"""Volume-quadrature replay of saved FEM-BEM and independent PMCHWT solutions.

No factorization or BEM assembly. The existing MFEM handle builds its small
serial mass/curl forms when creating the space; their matrices are not exported.
Working arrays remain in RAM; reference potentials are evaluated in chunks.
"""
import argparse
from itertools import permutations
import json
from pathlib import Path
import resource
import time
import numpy as np
import bempp_transmission as transmission


def tetra_rule(degree):
    """Positive symmetric MFEM v4.9 tetrahedron rules; weights sum to1/6.

    Data: mfem/mfem v4.9 fem/intrules.cpp, TetrahedronIntegrationRule cases2/5.
    All barycentric monomials through the stated degree are unit-checked.
    """
    orbits=[]
    if degree==2:
        a=.58541019662496845446
        orbits=[([a,*([(1-a)/3]*3)],1/24)]
    elif degree==5:
        a=.045503704125649649492
        b=.092735250310891226402
        c=.067342242210098170608
        orbits=[([a,a,.5-a,.5-a],.0070910034628469110730),
                ([1-3*b,b,b,b],.012248840519393658257),
                ([c,*([(1-c)/3]*3)],.018781320953002641800)]
    else:raise ValueError('Volume degree must be2 or5')
    points,weights=[],[]
    for coordinates,weight in orbits:
        orbit=sorted(set(permutations(coordinates)))
        points.extend(orbit)
        weights.extend([weight]*len(orbit))
    return np.asarray(points),np.asarray(weights)


def evaluate_reference(directory,level,points,order,stage,chunk=128):
    """Reconstruct a saved RWG current; never build a boundary matrix."""
    import bempp_cl.api as bem
    with np.load(directory/f'pmchwt-level{level}.npz',allow_pickle=False) as data:
        t,h,epsilon=data['electric_trace'],data['magnetic_trace'],float(data['epsilon_r'])
        if int(data['level'])!=level:raise ValueError('Reference NPZ level mismatch')
    space=bem.function_space(transmission.surface(level),'RWG',0)
    if t.shape!=h.shape or t.shape!=(space.global_dof_count,) or not np.isfinite(t).all() or not np.isfinite(h).all():
        raise ValueError('Reference current layout or values invalid')
    params=bem.DefaultParameters()
    params.quadrature.regular=order
    fields_e,fields_h=[],[]
    for first in range(0,len(points),chunk):
        e,magnetic=transmission.interior(space,t,h,points[first:first+chunk],epsilon,params)
        fields_e.append(e)
        fields_h.append(magnetic)
        stage(f'potential_B{level}_q{order}',done=min(first+chunk,len(points)),total=len(points))
    return np.concatenate(fields_e),np.concatenate(fields_h)


def run(level,output,candidate,reference,degree):
    started=time.monotonic()
    def stage(name,**extra):
        row=dict(stage=name,elapsed_s=time.monotonic()-started,**extra)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True)
    nodes,quadrature_weights=tetra_rule(degree)
    with np.load(candidate/'coupled-solution.npz',allow_pickle=False) as data:
        u=data['electric_fem']
        epsilon=float(data['epsilon_r'])
        if int(data['level'])!=level:raise ValueError('Candidate level mismatch')
    ref_case=json.loads((reference/'case.json').read_text())
    fine_level=ref_case['surface_level']
    if ref_case['epsilon_r']!=epsilon or fine_level not in [3,4]:raise ValueError('Reference physics mismatch')
    coupled=transmission.coupled
    vertices,tets,faces=coupled.fem.mesh(level-1)
    points,weights,e_values,h_values=[],[],[],[]
    with coupled.nd.GlobalND(vertices,tets,faces) as space:
        if u.shape!=(space.ndofs,) or not np.isfinite(u).all():raise ValueError('Invalid saved ND2 vector')
        for cell,tet in enumerate(tets):
            cell_vertices=vertices[tet]
            jacobian=np.linalg.det((cell_vertices[1:]-cell_vertices[0]).T)
            indices,values,curls=space.basis(cell,nodes[:,1:])
            points.append(nodes@cell_vertices)
            weights.append(jacobian*quadrature_weights)
            e_values.append(np.einsum('i,pic->pc',u[indices],values))
            h_values.append(np.einsum('i,pic->pc',u[indices],curls)/1j)
        fem_dofs=space.ndofs
    points,weights,e_values,h_values=map(np.concatenate,[points,weights,e_values,h_values])
    if not (weights>0).all() or abs(weights.sum()-4*np.pi/3)>1e-12:
        raise ValueError('Volume quadrature does not cover the expected positive-volume domain')
    stage('saved_fem_fields_evaluated',points=len(points))
    coarse_e,coarse_h=evaluate_reference(reference,fine_level-1,points,12,stage)
    fine_e,fine_h=evaluate_reference(reference,fine_level,points,12,stage)
    accurate_e,accurate_h=evaluate_reference(reference,fine_level,points,16,stage)
    rel=lambda a,b:transmission.relative(a,b,weights)
    errors=dict(E=rel(e_values,accurate_e),H=rel(h_values,accurate_h))
    convergence=dict(E=rel(coarse_e,fine_e),H=rel(coarse_h,fine_h))
    potential=dict(E=rel(fine_e,accurate_e),H=rel(fine_h,accurate_h))
    finite=bool(all(np.isfinite(a).all() for a in [e_values,h_values,coarse_e,coarse_h,fine_e,fine_h,accurate_e,accurate_h]))
    report=dict(scope=__doc__,level=level,volume_degree=degree,points=len(points),epsilon_r=epsilon,
                volume=float(weights.sum()),fem_dofs=fem_dofs,reference_surface_level=fine_level,
                relative_volume_E_H=errors,reference_refinement=convergence,potential_q12_vs16=potential,
                execution_passed=finite,analytic_target_passed=False,
                quality_screening_passed=bool(finite and max(errors.values())<.01 and max(convergence.values())<.003 and max(potential.values())<1e-6),
                target=dict(volume_field=.01,reference_change=.003,potential_quadrature=1e-6),
                elapsed_seconds=time.monotonic()-started,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                limitations=['Volume quadrature estimates: degree2/5 agreement must be checked separately',
                             'No port, resonance, antenna GPU, time or memory qualification',
                             'No new BEM assembly/solve; existing MFEM space creation assembles small serial forms'])
    np.savez(output/'volume-fields.npz',points=points,weights=weights,coupled_E=e_values,coupled_H=h_values,
             reference_E=accurate_e,reference_H=accurate_h,coarse_E=coarse_e,coarse_H=coarse_h,
             reference_q12_E=fine_e,reference_q12_H=fine_h)
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    parser.add_argument('--volume-degree',type=int,choices=[2,5],required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.level,args.output,args.candidate,args.reference,args.volume_degree)
