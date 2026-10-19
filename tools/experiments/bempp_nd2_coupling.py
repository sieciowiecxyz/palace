"""Small transparent Maxwell ND2/BC-RBC mortar with sparse FEM elimination.

No stabilization, dielectric transmission, ports, GPU or antenna promotion.
All working arrays stay in RAM; only the small boundary Schur is dense.
"""
import argparse
from itertools import combinations
import json
from pathlib import Path
import resource
import time
import numpy as np
from scipy.linalg import lu_factor, lu_solve, solve
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import norm as sparse_norm, splu, spsolve
import bempp_cl.api as bem
import bempp_pairing as pairing
import maxwell_fem as fem
import maxwell_nd as nd

K = 1.


class TransformedDense:
    """Pinned Bempp kernels in an untransformed local basis, then Qtest.T A Qtrial.

    The upstream dense assembler explicitly rejects BC/RBC transforms. Do not
    disable that check or edit installed sources: assemble the local space and
    apply both physical coefficient maps outside the kernel instead.
    """
    def __init__(self,domain,test,parameters):
        from bempp_cl.api.space.space import make_localised_space,return_compatible_representation
        self.domain,self.test=return_compatible_representation(domain,test)
        self.local_domain=make_localised_space(self.domain)
        self.local_test=make_localised_space(self.test)
        self.trial_map=self.domain.map_to_localised_space@self.domain.dof_transformation
        self.test_map=self.test.map_to_localised_space@self.test.dof_transformation
        self.parameters=parameters
        self.layout=None
        error=0.
        points=np.array([[.2,.6],[.3,.1]])
        for space,local,mapping in [(self.domain,self.local_domain,self.trial_map),(self.test,self.local_test,self.test_map)]:
            if local.requires_dof_transformation:raise ValueError('Local kernel space still requires a transform')
            coeff=np.sin(np.arange(space.global_dof_count)+.2)
            grid_coeff=space.dof_transformation@coeff
            local_coeff=mapping@coeff
            for triangle in space.support_elements:
                exact=np.einsum('i,pic->pc',grid_coeff[space.local2global[triangle]],pairing.local_values(space,triangle,points))
                value=np.einsum('i,pic->pc',local_coeff[local.local2global[triangle]],pairing.local_values(local,triangle,points))
                error=max(error,float(np.linalg.norm(value-exact)/max(np.linalg.norm(exact),1e-30)))
        self.pointwise_map_error=error
        if error>1e-12:raise ValueError('Local/global Bempp basis maps fail pointwise control')

    def assemble(self,descriptor,device_interface,precision,*args,**kwargs):
        from bempp_cl.core.dense_assembler import assemble_dense
        from bempp_cl.api.assembly.discrete_boundary_operator import DenseDiscreteBoundaryOperator
        local=assemble_dense(self.local_domain,self.local_test,self.parameters,descriptor,device_interface)
        reduced=np.asarray((self.test_map.T@local)@self.trial_map)
        self.layout=dict(local_shape=list(local.shape),local_bytes=local.nbytes,reduced_bytes=reduced.nbytes,
            pointwise_map_error=self.pointwise_map_error)
        return DenseDiscreteBoundaryOperator(reduced)


def weak_maxwell(kind,domain,range_space,test,parameters):
    assembler=TransformedDense(domain,test,parameters)
    factory=getattr(bem.operators.boundary.maxwell,kind)
    matrix=np.asarray(factory(domain,range_space,test,K,parameters=parameters,assembler=assembler,
                              device_interface='numba',precision='double').weak_form().A)
    return matrix,assembler.layout


def boundary_parents(space,grid):
    """Locate nested BEM triangles inside FEM boundary faces, independent of vertex IDs.

    A BEM triangle crossing a FEM face is rejected: it requires a true common
    intersection mesh, not evaluating one arbitrarily selected FEM cell.
    """
    owners={tuple(sorted(int(tet[i]) for i in face)):cell
            for cell,tet in enumerate(space.tetrahedra) for face in combinations(range(4),3)}
    faces=space.vertices[space.faces]
    first,second=faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]
    normals=np.cross(first,second)
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    aa=np.einsum('ij,ij->i',first,first)
    ab=np.einsum('ij,ij->i',first,second)
    bb=np.einsum('ij,ij->i',second,second)
    determinant=aa*bb-ab*ab
    cells,parents=[] ,[]
    for triangle in range(grid.number_of_elements):
        vertices=grid.vertices[:,grid.elements[:,triangle]].T
        displacement=vertices.mean(axis=0)-faces[:,0]
        a=np.einsum('ij,ij->i',displacement,first)
        b=np.einsum('ij,ij->i',displacement,second)
        u,v=(a*bb-b*ab)/determinant,(b*aa-a*ab)/determinant
        plane=np.abs(np.einsum('ij,ij->i',displacement,normals))
        candidates=np.flatnonzero((plane<1e-10)&(u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10))
        if len(candidates)!=1:raise ValueError('BEM triangle lacks a unique FEM boundary parent')
        parent=int(candidates[0])
        delta=vertices-faces[parent,0]
        da,db=delta@first[parent],delta@second[parent]
        u,v=(da*bb[parent]-db*ab[parent])/determinant[parent],(db*aa[parent]-da*ab[parent])/determinant[parent]
        if np.max(abs(delta@normals[parent]))>1e-10 or min(u.min(),v.min())<-1e-10 or (u+v).max()>1+1e-10:
            raise ValueError('BEM triangle crosses FEM faces; a common integration mesh is required')
        cells.append(owners[tuple(sorted(map(int,space.faces[parent])))])
        parents.append(parent)
    parents=np.asarray(parents,dtype=np.int64)
    return np.asarray(cells,dtype=np.int64),normals[parents],parents


def mortar(space,grid,bc,rbc):
    """Integrate B=<v,BC> and independently D=<RBC,v x n> on subtriangles."""
    points,weights = pairing.quadrature(4)
    cells,normals,_=boundary_parents(space,grid)
    rows,cols,bvalues,drows,dcols,dvalues = [],[],[],[],[],[]
    normal_error=coordinate_error=0.
    for triangle in range(bc.grid.number_of_elements):
        parent = triangle//6
        cell = cells[parent]
        vertices = space.vertices[space.tetrahedra[cell]]
        normal = normals[parent]
        child = bc.grid.vertices[:,bc.grid.elements[:,triangle]].T
        physical = child[0]+points.T@(child[1:]-child[0])
        inverse = np.linalg.inv(np.column_stack([np.ones(4),vertices]))
        lambdas = np.column_stack([np.ones(len(weights)),physical])@inverse
        coordinate_error=max(coordinate_error,float(np.max(abs(lambdas@vertices-physical))))
        normal_error=max(normal_error,float(np.linalg.norm(normal-bc.grid.normals[triangle]*bc.normal_multipliers[triangle])))
        indices,values,_ = space.basis(cell,lambdas[:,1:])
        bc_values = pairing.local_values(bc,triangle,points)
        rbc_values = pairing.local_values(rbc,triangle,points)
        jac = bc.grid.integration_elements[triangle]
        local_b = jac*np.einsum('p,pic,pjc->ij',weights,values,bc_values)
        local_d = jac*np.einsum('p,pic,pjc->ij',weights,rbc_values,np.cross(values,normal))
        rows.extend(np.repeat(indices,3))
        cols.extend(np.tile(bc.local2global[triangle],space.local_dofs))
        bvalues.extend(local_b.ravel())
        drows.extend(np.repeat(rbc.local2global[triangle],space.local_dofs))
        dcols.extend(np.tile(indices,3))
        dvalues.extend(local_d.ravel())
    bgrid=coo_matrix((bvalues,(rows,cols)),shape=(space.ndofs,bc.grid_dof_count)).tocsr()
    dgrid=coo_matrix((dvalues,(drows,dcols)),shape=(rbc.grid_dof_count,space.ndofs)).tocsr()
    b=(bgrid@bc.dof_transformation).tocsr()
    d=(rbc.dof_transformation.T@dgrid).tocsr()
    interior=np.setdiff1d(np.arange(space.ndofs),space.boundary())
    checks=dict(physical_adjoint_pairing=float(sparse_norm(d+b.T)/sparse_norm(b)),
        interior_tangential_pairing=float(sparse_norm(b[interior])/sparse_norm(b)),
        parent_child_normal_error=normal_error,physical_coordinate_error=coordinate_error)
    if max(checks.values())>1e-12: raise ValueError('ND2 BC/RBC mortar quadrature/normal/adjoint failed')
    return b,d,checks


def schur_solve(a,b,d,gram,calderon,electric,rhs,k=1.,block=16):
    """Exact sparse FEM elimination, bounded RHS blocks; tiny dense crosscheck."""
    begin=time.monotonic()
    factor=splu(a.astype(np.complex128).tocsc())
    gram_factor=lu_factor(gram.astype(np.complex128))
    trace=lambda value:lu_solve(gram_factor,d@value)
    schur=np.array(electric,dtype=np.complex128,copy=True)
    for first in range(0,b.shape[1],block):
        last=min(first+block,b.shape[1])
        response=factor.solve(b[:,first:last].toarray().astype(np.complex128))
        schur[:,first:last] += 1j*k*(calderon@trace(response))
    magnetic=solve(schur,rhs,assume_a='gen')
    electric_fem=1j*k*factor.solve(np.asarray(b@magnetic))
    electric_trace=trace(electric_fem)
    residual_fem=a@electric_fem-1j*k*(b@magnetic)
    residual_boundary=calderon@electric_trace+electric@magnetic-rhs
    raw=float(np.sqrt(np.linalg.norm(residual_fem)**2+np.linalg.norm(residual_boundary)**2)/np.linalg.norm(rhs))
    dense_error=dense_bytes=None
    if a.shape[0]<=512:
        mapping=lu_solve(gram_factor,d.toarray().astype(np.complex128))
        full=np.block([[a.toarray(),-1j*k*b.toarray()],[calderon@mapping,electric]])
        full_solution=solve(full,np.concatenate([np.zeros(a.shape[0],complex),rhs]),assume_a='gen')
        dense_error=float(np.linalg.norm(np.concatenate([electric_fem,magnetic])-full_solution)/np.linalg.norm(full_solution))
        dense_bytes=full.nbytes
        if dense_error>1e-10: raise ValueError('Sparse Schur differs from tiny full coupled solve')
    return electric_fem,magnetic,electric_trace,dict(raw_block_rhs_relative=raw,
        dense_crosscheck_relative=dense_error,tiny_full_matrix_bytes=dense_bytes,
        schur_bytes=schur.nbytes,rhs_block_columns=block,max_fem_rhs_block_bytes=a.shape[0]*min(block,b.shape[1])*16,
        solve_seconds=time.monotonic()-begin)


def radiation(electric_space,magnetic_space,electric_trace,magnetic,params):
    z,wz=np.polynomial.legendre.leggauss(16)
    phi=np.arange(24)*2*np.pi/24
    sphere=np.asarray([(np.sqrt(1-m*m)*np.cos(p),np.sqrt(1-m*m)*np.sin(p),m) for m in z for p in phi])
    six=np.asarray([[1.,0.,0.],[-1.,0.,0.],[0.,1.,0.],[0.,-1.,0.],[0.,0.,1.],[0.,0.,-1.]])
    directions=np.vstack([sphere,six]).T.copy()
    weights=np.repeat(wz,24)*2*np.pi/24
    options=dict(parameters=params,device_interface='numba',precision='double')
    e_far=bem.operators.far_field.maxwell.electric_field(magnetic_space,directions,K,**options)
    h_far=bem.operators.far_field.maxwell.magnetic_field(electric_space,directions,K,**options)
    scattered=-(e_far*bem.GridFunction(magnetic_space,coefficients=magnetic))-(h_far*bem.GridFunction(electric_space,coefficients=electric_trace))
    scatter=float(np.sum(weights*np.sum(abs(scattered[:,:-6])**2,axis=0)))
    extinction=float(4*np.pi/K*scattered[0,-2].imag)
    return dict(spurious_far_field_max=float(np.max(np.linalg.norm(scattered,axis=0))),
        scattering_cross_section=scatter,optical_theorem_extinction=extinction,
        energy_error_incident_cross_section=abs(extinction-scatter)/np.pi)


def run(level,output,duality='electric',surface_level=None):
    if duality not in ['electric','magnetic']:raise ValueError('Unknown dual trace layout')
    surface_level=level if surface_level is None else surface_level
    if not level<=surface_level<=3:raise ValueError('Surface hierarchy must refine the FEM boundary, up to level3')
    started=time.monotonic()
    def stage(name):
        row=dict(stage=name,elapsed_s=time.monotonic()-started)
        print(json.dumps(row),flush=True)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
    stage('imports_complete')
    vertices,tetrahedra,faces=fem.mesh(level-1)
    with nd.GlobalND(vertices,tetrahedra,faces) as space:
        mass,curl=space.matrix(0),space.matrix(1)
        a=curl-K*K*mass
        surface_vertices,_,surface_faces=fem.mesh(surface_level-1)
        nodes=np.unique(surface_faces.ravel())
        remap=np.full(len(surface_vertices),-1,dtype=np.int64)
        remap[nodes]=np.arange(len(nodes))
        grid=bem.Grid(surface_vertices[nodes].T,remap[surface_faces].T.astype(np.uint32))
        rwg=bem.function_space(grid,'RWG',0)
        snc=bem.function_space(grid,'SNC',0)
        bc,rbc=bem.function_space(grid,'BC',0),bem.function_space(grid,'RBC',0)
        if duality=='electric':
            electric_space,magnetic_space,electric_test=rwg,bc,rbc
            magnetic_bary,test_bary=bc,rbc
        else:
            electric_space,magnetic_space,electric_test=bc,rwg,snc
            magnetic_bary,test_bary=rwg.barycentric_representation(),snc.barycentric_representation()
        params=bem.DefaultParameters()
        params.quadrature.regular=params.quadrature.singular=4
        gram=bem.operators.boundary.sparse.identity(electric_space,electric_space,electric_test,parameters=params).weak_form().A.toarray()
        b,d,mortar_checks=mortar(space,grid,magnetic_bary,test_bary)
        gram_factor=lu_factor(gram.astype(np.complex128))
        constant=lu_solve(gram_factor,d@space.project(0))
        linear=lu_solve(gram_factor,d@space.project(1))
        def exact_constant(x):return np.tile([1.,0.,0.],(len(x),1))
        def exact_linear(x):return x[:,[2,0,1]]
        constant_load=pairing.trace_load(test_bary,exact_constant,order=6)
        trace_checks=dict(constant_surface_L2=pairing.projection_error(electric_space.barycentric_representation(),constant,exact_constant),
            linear_surface_L2=pairing.projection_error(electric_space.barycentric_representation(),linear,exact_linear),
            constant_weak_relative=float(np.linalg.norm(gram@constant-constant_load)/np.linalg.norm(constant_load)),
            constant_exactly_representable=duality=='electric')
        if trace_checks['constant_weak_relative']>1e-12:raise ValueError('ND2 mortar does not preserve the exact constant weak trace')
        if duality=='electric' and trace_checks['constant_surface_L2']>1e-12:
            raise ValueError('RWG mortar does not reproduce the representable constant trace')
        stage('nd2_bc_mortar_validated')
        @bem.complex_callable
        def incident(x,n,index,result):
            value=np.exp(1j*K*x[2])
            result[0],result[1],result[2]=0.,-value*n[2],value*n[1]
        rhs=bem.GridFunction(electric_space,fun=incident,dual_space=electric_test,parameters=params).projections(electric_test)
        local_control=None
        if level==1:
            local_control={}
            for kind in ['electric_field','magnetic_field']:
                local_matrix,_=weak_maxwell(kind,rwg,rwg,snc,params)
                native=np.asarray(getattr(bem.operators.boundary.maxwell,kind)(rwg,rwg,snc,K,
                    parameters=params,assembler='dense',device_interface='numba',precision='double').weak_form().A)
                local_control[kind]=float(np.linalg.norm(local_matrix-native)/np.linalg.norm(native))
            if max(local_control.values())>1e-12:raise ValueError('Transformed kernel assembler disagrees with native RWG/SNC')
            stage('local_assembler_vs_native_maxwell_validated')
        electric,electric_layout=weak_maxwell('electric_field',magnetic_space,electric_space,electric_test,params)
        stage('electric_operator_assembled')
        magnetic_operator,magnetic_layout=weak_maxwell('magnetic_field',electric_space,electric_space,electric_test,params)
        calderon=gram/2+magnetic_operator
        stage('calderon_operator_assembled')
        solution,magnetic,electric_trace,solve_metrics=schur_solve(a,b,d,gram,calderon,electric,rhs,K)
        stage('sparse_fem_boundary_schur_solved')
        errors=nd.plane_field_errors(space,solution,order=6)
        quad=nd.plane_field_errors(space,solution,order=8)
        quad_delta=max(abs(errors[key]-quad[key]) for key in ['relative_E_L2','relative_H_L2'])
        reference=space.project(2)
        boundary=space.boundary()
        interior=np.setdiff1d(np.arange(space.ndofs),boundary)
        reference[interior]=spsolve(a[interior][:,interior].astype(np.complex128),-a[interior][:,boundary]@reference[boundary])
        reference_errors=nd.plane_field_errors(space,reference,order=6)
        difference=solution-reference
        delta_e=float(np.sqrt(max(0,np.vdot(difference,mass@difference).real)/errors['volume']))
        delta_h=float(np.sqrt(max(0,np.vdot(difference,curl@difference).real)/(K*K*errors['volume'])))
        stage('coupled_vs_analytic_and_dirichlet_fields_complete')
        far=radiation(electric_space,magnetic_space,electric_trace,magnetic,params)
        raw=solve_metrics['raw_block_rhs_relative']
        report=dict(scope='ND2/dual-trace single-Calderon-row transparent coupling; no antenna qualification',
            duality=duality,electric_trace_space='RWG' if duality=='electric' else 'BC',
            magnetic_trace_space='BC' if duality=='electric' else 'RWG',
            level=level,surface_level=surface_level,tetrahedra=len(space.tetrahedra),triangles=grid.number_of_elements,
            fem_boundary_triangles=len(space.faces),
            fem_dofs=space.ndofs,bem_dofs=magnetic_space.global_dof_count,mfem=dict(version=space.version,git=space.git),
            mortar_checks=mortar_checks,trace_checks=trace_checks,solve=solve_metrics,
            local_assembler_vs_native=local_control,
            local_assembly=dict(electric=electric_layout,magnetic=magnetic_layout),
            coupled_field_errors=errors,dirichlet_field_errors=reference_errors,
            coupled_minus_dirichlet_E_L2=delta_e,coupled_minus_dirichlet_H_L2=delta_h,
            field_quadrature6_vs8_delta=quad_delta,radiation=far,
            mass_curl_csr_bytes=sum(a.data.nbytes+a.indices.nbytes+a.indptr.nbytes for a in [mass,curl]),
            boundary_pairing_csr_bytes=sum(a.data.nbytes+a.indices.nbytes+a.indptr.nbytes for a in [b,d]),
            elapsed_seconds=time.monotonic()-started,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            execution_passed=bool(raw<1e-10 and quad_delta<1e-6 and np.isfinite(far['spurious_far_field_max'])),
            analytic_target_passed=bool(errors['relative_E_L2']<.01 and errors['relative_H_L2']<.01 and
                far['spurious_far_field_max']<.01 and far['energy_error_incident_cross_section']<1e-3),
            target=dict(E_L2=.01,H_L2=.01,far_field_absolute=.01,energy=1e-3,raw=1e-10,mortar=1e-12,quadrature=1e-6),
            limitations=['No stabilized coupling/interior-resonance qualification or dielectric FEM transmission',
                'Low-order RWG/BC traces differ from ND2 trace; projection errors are reported, not forced to zero',
                'Sparse FEM but dense small boundary operators/Schur; not scalable BEM assembly',
                'Exact Dirichlet comparator on same bounded domain, not a larger absorbing-air antenna reference',
                'CPU complex128 only; no ports/S/VSWR or antenna RAM/speed improvement claim'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--duality',choices=['electric','magnetic'],default='electric')
    parser.add_argument('--surface-level',type=int,choices=[1,2,3])
    args=parser.parse_args()
    run(args.level,args.output,args.duality,args.surface_level)
