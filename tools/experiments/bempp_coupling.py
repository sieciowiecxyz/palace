"""Small real Maxwell FEM-BEM coupling, CPU MFEM ND1 and Bempp RWG/SNC.

Transparent material eps=mu=1 and analytic incident plane wave. This validates
the interface, not ND2 antenna accuracy, stability at resonances, or GPU speed.
"""
import argparse
from itertools import combinations
import json
from pathlib import Path
import resource
import time
import numpy as np
from scipy.linalg import solve
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import bempp_cl.api as bem
import maxwell_fem as fem

K = 1.0


def trace_and_pairing(vertices,tetrahedra,faces,grid,rwg,edges,dofs,signs,edge_map):
    boundary_nodes = np.unique(faces.ravel())
    owners = {tuple(sorted(int(tet[i]) for i in face)):e
              for e,tet in enumerate(tetrahedra) for face in combinations(range(4),3)}
    coords = np.array([[1/6,2/3,1/6],[1/6,1/6,2/3]])
    bary = np.vstack([1-coords.sum(axis=0),coords]).T
    mapping = {}
    pair_rows,pair_cols,pair_values = [],[],[]
    max_trace_error=max_scale_error=0.0
    for triangle in range(grid.number_of_elements):
        global_vertices = boundary_nodes[grid.elements[:,triangle]]
        points = vertices[global_vertices]
        cell = owners[tuple(sorted(global_vertices))]
        tet = tetrahedra[cell]
        inverse = np.linalg.inv(np.column_stack([np.ones(4),vertices[tet]]))
        lambdas = np.column_stack([np.ones(3),bary@points])@inverse
        physical = fem.basis(lambdas,inverse[1:,:].T)*signs[cell][None,:,None]
        normal = np.cross(points[1]-points[0],points[2]-points[0])
        jacobian = np.linalg.norm(normal)
        normal /= jacobian
        trace = np.cross(physical,normal)
        boundary = np.transpose(rwg.evaluate(triangle,coords),(2,1,0))
        for local,(a,b) in enumerate([(0,1),(0,2),(1,2)]):
            key = tuple(sorted((int(global_vertices[a]),int(global_vertices[b]))))
            edge = edge_map[key]
            local_edge = int(np.flatnonzero(dofs[cell]==edge)[0])
            index = int(rwg.local2global[triangle,local])
            value,target = trace[:,local_edge,:],boundary[:,local,:]
            scale = float(np.vdot(target,value).real/np.vdot(target,target).real)
            length = np.linalg.norm(vertices[key[1]]-vertices[key[0]])
            max_scale_error = max(max_scale_error,abs(abs(scale)*length-1))
            max_trace_error = max(max_trace_error,float(np.linalg.norm(value-scale*target)/np.linalg.norm(value)))
            if index in mapping:
                old_edge,old_scale = mapping[index]
                if old_edge!=edge or abs(old_scale-scale)>1e-12:
                    raise ValueError('Trace differs across adjacent boundary faces')
            mapping[index] = edge,scale
            for row,global_edge in enumerate(dofs[cell]):
                pair_rows.append(global_edge)
                pair_cols.append(index)
                pair_values.append(jacobian*np.sum(physical[:,row,:]*target)/6)
    if len(mapping)!=rwg.global_dof_count or max(max_scale_error,max_trace_error)>1e-12:
        raise ValueError('Rotated MFEM trace/RWG scaling failed')
    ordered = [mapping[i] for i in range(rwg.global_dof_count)]
    trace_map = coo_matrix(([s for e,s in ordered],(np.arange(len(ordered)),[e for e,s in ordered])),
                           shape=(len(ordered),len(edges))).tocsr()
    pairing = coo_matrix((pair_values,(pair_rows,pair_cols)),shape=(len(edges),len(ordered))).tocsr()
    return trace_map,pairing,dict(max_pointwise_trace_error=max_trace_error,max_edge_length_scaling_error=max_scale_error)


def run(level,output):
    started = time.monotonic()
    def stage(name):
        row = dict(stage=name,elapsed_s=time.monotonic()-started)
        print(json.dumps(row),flush=True)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
    stage('imports_complete')
    vertices,tetrahedra,faces = fem.mesh(level-1)
    bridge = fem.MFEM()
    mass,curl,edges,dofs,signs,edge_map,metadata = fem.assemble(vertices,tetrahedra,bridge)
    volume_operator = curl-K*K*mass
    stage('mfem_volume_assembly_complete')
    boundary_nodes = np.unique(faces.ravel())
    remap = np.full(len(vertices),-1,dtype=np.int64)
    remap[boundary_nodes] = np.arange(len(boundary_nodes))
    grid = bem.Grid(vertices[boundary_nodes].T,remap[faces].T.astype(np.uint32))
    rwg,snc = bem.function_space(grid,'RWG',0),bem.function_space(grid,'SNC',0)
    params = bem.DefaultParameters()
    params.quadrature.regular = params.quadrature.singular = 4
    trace_map,direct_pairing,trace_metrics = trace_and_pairing(vertices,tetrahedra,faces,grid,rwg,edges,dofs,signs,edge_map)
    gram = bem.operators.boundary.sparse.identity(rwg,rwg,snc,parameters=params).weak_form().A.toarray()
    pairing = trace_map.T@gram
    pair_error = float(np.linalg.norm(pairing-direct_pairing.toarray())/np.linalg.norm(pairing))
    if pair_error>1e-12: raise ValueError('FEM boundary weak pairing/rotation disagrees with Bempp SNC Gram')
    stage('trace_pairing_complete')

    @bem.complex_callable
    def incident(x,n,index,result):
        value = np.exp(1j*K*x[2])
        result[0],result[1],result[2] = 0.,-value*n[2],value*n[1]

    rhs_trace = bem.GridFunction(rwg,fun=incident,dual_space=snc,parameters=params).projections(snc)
    options = dict(parameters=params,assembler='dense',device_interface='numba',precision='double')
    electric = np.asarray(bem.operators.boundary.maxwell.electric_field(rwg,rwg,snc,K,**options).weak_form().A)
    magnetic = np.asarray(bem.operators.boundary.maxwell.magnetic_field(rwg,rwg,snc,K,**options).weak_form().A)
    # Green: a(E,v)-ik <H x n, v_t>=0. Outgoing Calderon row:
    # (1/2 G + M) (E x n) + T (H x n) = Einc x n.
    calderon = gram/2+magnetic
    matrix = np.block([[volume_operator.toarray(),-1j*K*pairing],
                       [calderon@trace_map,electric]])
    rhs = np.concatenate([np.zeros(len(edges),dtype=complex),rhs_trace])
    stage('coupled_assembly_complete')
    begin = time.monotonic()
    coefficients = solve(matrix,rhs,assume_a='gen')
    raw = float(np.linalg.norm(matrix@coefficients-rhs)/np.linalg.norm(rhs))
    solve_seconds = time.monotonic()-begin
    solution,magnetic_trace = coefficients[:len(edges)],coefficients[len(edges):]
    stage('coupled_solve_complete')
    incident_e,incident_h = fem.plane_coefficients(vertices,edges,K)
    boundary = np.unique(trace_map.indices)
    interior = np.setdiff1d(np.arange(len(edges)),boundary)
    dirichlet = incident_e.copy()
    if len(interior):
        dirichlet[interior] = spsolve(volume_operator[interior][:,interior],
                                     -volume_operator[interior][:,boundary]@dirichlet[boundary])
    errors = fem.plane_field_errors(vertices,tetrahedra,dofs,signs,solution,K)
    reference_errors = fem.plane_field_errors(vertices,tetrahedra,dofs,signs,dirichlet,K)
    quad_check = fem.plane_field_errors(vertices,tetrahedra,dofs,signs,solution,K,order=6)
    quad_delta = max(abs(errors[key]-quad_check[key]) for key in ['relative_E_L2','relative_H_L2'])
    difference = solution-dirichlet
    delta_e = float(np.sqrt(max(0,np.vdot(difference,mass@difference).real)/errors['volume']))
    delta_h = float(np.sqrt(max(0,np.vdot(difference,curl@difference).real)/(K*K*errors['volume'])))
    electric_trace = trace_map@solution
    opposite_rhs = (trace_map@incident_h)
    # This second Calderon row is a diagnostic, not the enforced solve residual.
    second_residual = -electric@electric_trace+calderon@magnetic_trace-gram@opposite_rhs
    second_relative = float(np.linalg.norm(second_residual)/max(np.linalg.norm(gram@opposite_rhs),1e-30))
    @bem.complex_callable
    def incident_h(x,n,index,result):
        value = np.exp(1j*K*x[2])
        result[0],result[1],result[2] = value*n[2],0.,-value*n[0]
    exact_h_rhs = bem.GridFunction(rwg,fun=incident_h,dual_space=snc,parameters=params).projections(snc)
    second_exact = float(np.linalg.norm(-electric@electric_trace+calderon@magnetic_trace-exact_h_rhs)/np.linalg.norm(exact_h_rhs))
    directions = np.array([[1.,0.,0.],[-1.,0.,0.],[0.,1.,0.],[0.,-1.,0.],[0.,0.,1.],[0.,0.,-1.]])
    z,wz = np.polynomial.legendre.leggauss(16)
    phi = np.arange(24)*2*np.pi/24
    sphere = np.asarray([(np.sqrt(1-m*m)*np.cos(p),np.sqrt(1-m*m)*np.sin(p),m) for m in z for p in phi])
    weights = np.repeat(wz,24)*2*np.pi/24
    all_directions = np.vstack([sphere,directions])
    e_far = bem.operators.far_field.maxwell.electric_field(rwg,all_directions.T.copy(),K,parameters=params,device_interface='numba',precision='double')
    h_far = bem.operators.far_field.maxwell.magnetic_field(rwg,all_directions.T.copy(),K,parameters=params,device_interface='numba',precision='double')
    scattered = -(e_far*bem.GridFunction(rwg,coefficients=magnetic_trace))-(h_far*bem.GridFunction(rwg,coefficients=electric_trace))
    far_max = float(np.max(np.linalg.norm(scattered,axis=0)))
    far_six = float(np.max(np.linalg.norm(scattered[:,-6:],axis=0)))
    scatter = float(np.sum(weights*np.sum(abs(scattered[:,:-6])**2,axis=0)))
    extinction = float(4*np.pi/K*scattered[0,-2].imag)
    energy_error = abs(extinction-scatter)/np.pi
    report = dict(scope='Actual MFEM ND1/Bempp Maxwell coupling; transparent plane wave, not ND2 antenna',
        level=level,refinement=level-1,ka=K,epsilon_r=1.,mu_r=1.,tetrahedra=len(tetrahedra),triangles=len(faces),
        fem_dofs=len(edges),bem_dofs=rwg.global_dof_count,matrix_bytes=matrix.nbytes,
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,backend='CPU dense coupled solve; MFEM local integrators',
        mfem=metadata,trace=trace_metrics,boundary_pairing_error=pair_error,
        raw_rhs_relative=raw,coupled_field_errors=errors,dirichlet_fem_field_errors=reference_errors,
        coupled_minus_dirichlet_E_L2=delta_e,coupled_minus_dirichlet_H_L2=delta_h,
        field_quadrature4_vs6_delta=quad_delta,second_calderon_diagnostic_relative=second_relative,
        second_calderon_exact_weak_rhs_relative=second_exact,
        spurious_far_field_max_six_directions=far_six,spurious_far_field_max_384_plus_six_directions=far_max,
        spurious_scattering_cross_section=scatter,optical_theorem_extinction=extinction,
        relative_energy_error_incident_cross_section=energy_error,solve_seconds=solve_seconds,
        elapsed_seconds=time.monotonic()-started,execution_passed=bool(raw<1e-10 and np.isfinite(far_max)),
        analytic_target_passed=bool(errors['relative_E_L2']<0.01 and errors['relative_H_L2']<0.01 and far_max<0.01 and quad_delta<1e-6 and energy_error<1e-3),
        target=dict(E_L2=0.01,H_L2=0.01,far_field_absolute=0.01,raw=1e-10,trace_pairing=1e-12,quadrature_delta=1e-6,energy=1e-3),
        limitations=['ND1 validation probe only; production antenna ND2/medium unchanged',
                     'CPU dense prototype, no GPU/compression/ports or antenna speed claim',
                     'Comparator uses exact Dirichlet data on same bounded FEM domain, not a larger absorbing air domain',
                     'Nonsymmetric single-row coupling not qualified near interior resonances; no dielectric FEM transmission yet'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    run(args.level,args.output)
