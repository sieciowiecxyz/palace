"""Bounded dielectric FEM-BEM screening against independent same-polyhedron PMCHWT.

Centroid probes are not a full-volume field norm. This diagnostic cannot alone
qualify M2 or the antenna; transparent epsilon=1 also checks analytic signs.
"""
import argparse
import json
from pathlib import Path
import resource
import time
import numpy as np
from scipy.linalg import solve
import bempp_cl.api as bem
import bempp_nd2_coupling as coupled


def surface_mesh(level):
    if level not in [1,2,3,4]:raise ValueError('Surface level must be1..4')
    vertices,_,faces=coupled.fem.mesh(min(level-1,2))
    nodes=np.unique(faces.ravel())
    inverse=np.full(len(vertices),-1,dtype=np.int64)
    inverse[nodes]=np.arange(len(nodes))
    vertices,faces=vertices[nodes],inverse[faces]
    if level==4:
        # Planar refinement: never project vertices onto a sphere.
        vertices=list(vertices)
        midpoints,children={},[]
        def midpoint(a,b):
            key=tuple(sorted((int(a),int(b))))
            if key not in midpoints:
                midpoints[key]=len(vertices)
                vertices.append((vertices[a]+vertices[b])/2)
            return midpoints[key]
        for a,b,c in faces:
            ab,bc,ca=midpoint(a,b),midpoint(b,c),midpoint(c,a)
            children.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
        vertices,faces=np.asarray(vertices),np.asarray(children)
    return vertices,faces


def surface(level):
    vertices,faces=surface_mesh(level)
    return bem.Grid(vertices.T,faces.T.astype(np.uint32))


def incident(points):
    electric=np.zeros((len(points),3),complex)
    magnetic=np.zeros_like(electric)
    electric[:,0]=magnetic[:,1]=np.exp(1j*points[:,2])
    return electric,magnetic


def relative(actual,reference,weights=None):
    weights=np.ones(len(actual)) if weights is None else weights
    return float(np.sqrt(np.dot(weights,np.sum(abs(actual-reference)**2,axis=1))/
                         np.dot(weights,np.sum(abs(reference)**2,axis=1))))


def projections(space,test,params):
    @bem.complex_callable
    def e_trace(x,n,index,result):
        value=np.exp(1j*x[2])
        result[0],result[1],result[2]=0.,-value*n[2],value*n[1]
    @bem.complex_callable
    def h_trace(x,n,index,result):
        value=np.exp(1j*x[2])
        result[0],result[1],result[2]=value*n[2],0.,-value*n[0]
    return [bem.GridFunction(space,fun=f,dual_space=test,parameters=params).projections(test)
            for f in [e_trace,h_trace]]


def pmchwt(grid,epsilon,params):
    """Independent all-surface transmission solve, no FEM mortar or Schur."""
    rwg,snc=bem.function_space(grid,'RWG',0),bem.function_space(grid,'SNC',0)
    options=dict(parameters=params,assembler='dense',device_interface='numba',precision='double')
    def operators(k):
        return [np.asarray(getattr(bem.operators.boundary.maxwell,name)(rwg,rwg,snc,k,**options).weak_form().A)
                for name in ['electric_field','magnetic_field']]
    rho=np.sqrt(epsilon)
    te,ke=operators(1.)
    ti,ki=(te,ke) if epsilon==1. else operators(rho)
    matrix=np.block([[ke+ki,te+ti/rho],[-te-rho*ti,ke+ki]])
    rhs=np.concatenate(projections(rwg,snc,params))
    coeff=solve(matrix,rhs,assume_a='gen')
    raw=float(np.linalg.norm(matrix@coeff-rhs)/np.linalg.norm(rhs))
    count=rwg.global_dof_count
    return rwg,coeff[:count],coeff[count:],dict(dofs=2*count,matrix_bytes=matrix.nbytes,raw=raw)


def interior(space,t,h,points,epsilon,params):
    """exp(-iwt): E=K*t+T*h/rho, H=K*h-rho*T*t, rho=sqrt(epsilon)."""
    opts=dict(parameters=params,device_interface='numba',precision='double')
    t,h=bem.GridFunction(space,coefficients=t),bem.GridFunction(space,coefficients=h)
    electric=bem.operators.potential.maxwell.electric_field(space,points.T.copy(),np.sqrt(epsilon),**opts)
    magnetic=bem.operators.potential.maxwell.magnetic_field(space,points.T.copy(),np.sqrt(epsilon),**opts)
    return ((magnetic*t)+(electric*h)/np.sqrt(epsilon)).T,((magnetic*h)-np.sqrt(epsilon)*(electric*t)).T


def far_field(e_space,h_space,t,h,params):
    z,w=np.polynomial.legendre.leggauss(16)
    phi=np.arange(24)*2*np.pi/24
    directions=np.asarray([(np.sqrt(1-a*a)*np.cos(p),np.sqrt(1-a*a)*np.sin(p),a) for a in z for p in phi]+[(0.,0.,1.)])
    weights=np.repeat(w,24)*2*np.pi/24
    opts=dict(parameters=params,device_interface='numba',precision='double')
    electric=bem.operators.far_field.maxwell.electric_field(h_space,directions.T.copy(),1.,**opts)
    magnetic=bem.operators.far_field.maxwell.magnetic_field(e_space,directions.T.copy(),1.,**opts)
    field=(-(electric*bem.GridFunction(h_space,coefficients=h))-
           (magnetic*bem.GridFunction(e_space,coefficients=t))).T
    scatter=float(np.dot(weights,np.sum(abs(field[:-1])**2,axis=1)))
    extinction=float(4*np.pi*field[-1,0].imag)
    return field,dict(scattering=scatter,extinction=extinction,energy_error_over_pi=abs(scatter-extinction)/np.pi)


def reference_check(level,output,epsilon=1.,surface_level=3):
    """Isolate PMCHWT mesh vs potential quadrature without any FEM solve."""
    surface_level=level if surface_level is None else surface_level
    if epsilon not in [1.,2.94] or level not in [1,2,3] or surface_level not in [2,3,4]:
        raise ValueError('Reference-only requires epsilon1/2.94, sampling1..3 and BEM2..4')
    begin=time.monotonic()
    vertices,tets,_=coupled.fem.mesh(level-1)
    points=vertices[tets].mean(axis=1)
    weights=np.linalg.det(np.transpose(vertices[tets][:,1:]-vertices[tets][:,:1],(0,2,1)))/6
    exact_e,exact_h=incident(points)
    params=bem.DefaultParameters()
    params.quadrature.regular=params.quadrature.singular=4
    rows,previous=[],None
    orders=[4,8] if epsilon==1. else [8,12]
    for ref_level in [surface_level-1,surface_level]:
        space,t,h,metrics=pmchwt(surface(ref_level),epsilon,params)
        np.savez(output/f'pmchwt-level{ref_level}.npz',electric_trace=t,magnetic_trace=h,
                 points=points,weights=weights,epsilon_r=epsilon,level=ref_level)
        values=[]
        for order in orders:
            # Change only regular potential quadrature after the solved currents.
            potential_params=bem.DefaultParameters()
            potential_params.quadrature.regular=order
            before=time.monotonic()
            e,magnetic=interior(space,t,h,points,epsilon,potential_params)
            values.append((e,magnetic))
            np.savez(output/f'fields-level{ref_level}-q{order}.npz',points=points,weights=weights,electric=e,magnetic=magnetic)
            metrics[f'potential_q{order}']=dict(E_probes=relative(e,exact_e,weights) if epsilon==1. else None,
                                               H_probes=relative(magnetic,exact_h,weights) if epsilon==1. else None,
                                               seconds=time.monotonic()-before)
        metrics.update(level=ref_level,potential_orders=orders,potential_quadrature_delta=dict(
            E_probes=relative(values[0][0],values[1][0],weights),H_probes=relative(values[0][1],values[1][1],weights)))
        if previous is not None:
            convergence=dict(E_probes=relative(previous[0],values[-1][0],weights),H_probes=relative(previous[1],values[-1][1],weights))
        previous=values[-1]
        rows.append(metrics)
        print(json.dumps(dict(stage=f'reference_level{ref_level}_complete',elapsed_s=time.monotonic()-begin)),flush=True)
    report=dict(scope='Same-polyhedron PMCHWT reference calibration, no FEM solve or antenna qualification',
                level=level,surface_level=surface_level,epsilon_r=epsilon,probe_count=len(points),rows=rows,
                reference_convergence=convergence,
                execution_passed=bool(all(r['raw']<1e-10 for r in rows)),analytic_target_passed=False,
                elapsed_seconds=time.monotonic()-begin,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                limitations=['Centroid sampling only; no full-volume L2 or dielectric transmission qualification',
                             'Analytic error and quadrature deltas are reported separately, not fitted'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


def run(level,output,epsilon=2.94,surface_level=None):
    surface_level=level if surface_level is None else surface_level
    if level not in [1,2,3] or not max(2,level)<=surface_level<=3 or epsilon not in [1.,2.94]:
        raise ValueError('Use FEM1..3, nested BEM2..3 and epsilon1 or2.94')
    begin=time.monotonic()
    def stage(name):
        row=dict(stage=name,elapsed_s=time.monotonic()-begin)
        print(json.dumps(row),flush=True)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
    stage('imports_complete')
    vertices,tets,faces=coupled.fem.mesh(level-1)
    params=bem.DefaultParameters()
    params.quadrature.regular=params.quadrature.singular=4
    grid=surface(surface_level)
    with coupled.nd.GlobalND(vertices,tets,faces) as volume:
        mass,curl=volume.matrix(0),volume.matrix(1)
        rwg,snc=bem.function_space(grid,'RWG',0),bem.function_space(grid,'SNC',0)
        bc=bem.function_space(grid,'BC',0)
        gram=bem.operators.boundary.sparse.identity(bc,bc,snc,parameters=params).weak_form().A.toarray()
        b,d,mortar=coupled.mortar(volume,grid,rwg.barycentric_representation(),snc.barycentric_representation())
        if max(mortar.values())>1e-12:raise ValueError('Dielectric mortar failed')
        stage('mortar_complete')
        electric,e_layout=coupled.weak_maxwell('electric_field',rwg,bc,snc,params)
        magnetic,k_layout=coupled.weak_maxwell('magnetic_field',bc,bc,snc,params)
        rhs=projections(bc,snc,params)[0]
        u,h,t,solve_metrics=coupled.schur_solve(curl-epsilon*mass,b,d,gram,gram/2+magnetic,electric,rhs)
        np.savez(output/'coupled-solution.npz',electric_fem=u,electric_trace=t,magnetic_trace=h,
                 level=level,surface_level=surface_level,epsilon_r=epsilon)
        stage('coupled_solve_complete')
        # One weighted centroid per tetrahedron is a screening diagnostic, not L2.
        points=vertices[tets].mean(axis=1)
        weights=np.linalg.det(np.transpose(vertices[tets][:,1:]-vertices[tets][:,:1],(0,2,1)))/6
        fields_e,fields_h=[],[]
        for cell in range(len(tets)):
            indices,values,curls=volume.basis(cell,np.array([[.25,.25,.25]]))
            fields_e.append(np.einsum('i,pic->pc',u[indices],values)[0])
            fields_h.append(np.einsum('i,pic->pc',u[indices],curls)[0]/1j)
        fields_e,fields_h=np.asarray(fields_e),np.asarray(fields_h)
        far,energy=far_field(bc,rwg,t,h,params)
        references=[]
        fine_e=fine_h=fine_far=None
        for ref_level in [surface_level-1,surface_level]:
            ref_space,ref_t,ref_h,metrics=pmchwt(surface(ref_level),epsilon,params)
            np.savez(output/f'pmchwt-level{ref_level}.npz',electric_trace=ref_t,magnetic_trace=ref_h,
                     points=points,weights=weights,epsilon_r=epsilon,level=ref_level)
            potential_params=bem.DefaultParameters()
            potential_params.quadrature.regular=8
            e,h_ref=interior(ref_space,ref_t,ref_h,points,epsilon,potential_params)
            ref_far,ref_energy=far_field(ref_space,ref_space,ref_t,ref_h,params)
            metrics.update(level=ref_level,energy=ref_energy,potential_quadrature=8)
            references.append(metrics)
            if fine_e is not None:
                convergence=dict(E_probes=relative(fine_e,e,weights),H_probes=relative(fine_h,h_ref,weights),
                                 far_relative=relative(fine_far,ref_far) if epsilon!=1. else None,
                                 far_absolute=float(np.max(np.linalg.norm(fine_far-ref_far,axis=1))))
            fine_e,fine_h,fine_far=e,h_ref,ref_far
            stage(f'pmchwt_reference_level{ref_level}_complete')
        errors=dict(E_weighted_probes=relative(fields_e,fine_e,weights),H_weighted_probes=relative(fields_h,fine_h,weights),
                    far_relative=relative(far,fine_far) if epsilon!=1. else None,
                    far_absolute=float(np.max(np.linalg.norm(far-fine_far,axis=1))))
        analytic=None
        if epsilon==1.:
            exact_e,exact_h=incident(points)
            analytic=dict(coupled_E=relative(fields_e,exact_e,weights),coupled_H=relative(fields_h,exact_h,weights),
                          reference_E=relative(fine_e,exact_e,weights),reference_H=relative(fine_h,exact_h,weights))
        execution=bool(solve_metrics['raw_block_rhs_relative']<1e-10 and all(r['raw']<1e-10 for r in references)
                       and np.isfinite(fields_e).all() and np.isfinite(fine_e).all())
        report=dict(scope=__doc__,epsilon_r=epsilon,level=level,surface_level=surface_level,
                    fem_dofs=volume.ndofs,bem_dofs=rwg.global_dof_count,probe_count=len(points),
                    mortar=mortar,solve=solve_metrics,local_assembly=dict(electric=e_layout,magnetic=k_layout),
                    reference_hierarchy=references,reference_convergence=convergence,comparison=errors,
                    coupled_energy=energy,analytic_transparent_probes=analytic,
                    execution_passed=execution,analytic_target_passed=False,
                    screening_passed=bool(execution and max(errors['E_weighted_probes'],errors['H_weighted_probes'])<.01
                         and max(convergence['E_probes'],convergence['H_probes'])<.003
                         and energy['energy_error_over_pi']<1e-3
                         and (errors['far_relative']<.01 if epsilon!=1. else max(analytic.values())<.01)),
                    target=dict(probe_error=.01,reference_change=.003,far_relative=.01,energy_over_pi=1e-3,raw=1e-10),
                    elapsed_seconds=time.monotonic()-begin,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                    limitations=['Centroid probes are not full-volume L2 or boundary field accuracy',
                                 'Reference convergence and potential quadrature require further qualification',
                                 'Shared Bempp kernels but independent PMCHWT system; no antenna promotion'])
        np.savez(output/'probes.npz',points=points,weights=weights,coupled_E=fields_e,coupled_H=fields_h,
                 reference_E=fine_e,reference_H=fine_h,coupled_far=far,reference_far=fine_far)
        (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    parser.add_argument('--surface-level',type=int,choices=[2,3,4])
    parser.add_argument('--epsilon-r',type=float,choices=[1.,2.94],default=2.94)
    parser.add_argument('--reference-only',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.reference_only:reference_check(args.level,args.output,args.epsilon_r,args.surface_level)
    else:run(args.level,args.output,args.epsilon_r,args.surface_level)
