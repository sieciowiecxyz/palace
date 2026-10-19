"""Small RWG/SNC vs RWG/RBC interface audit; no Maxwell solve or promotion.

Compare Bempp weak matrices to independent physical triangle quadrature with
all barycentric DOF transforms. Test a representable constant E trace before
using the dual Gram matrix for a nonmatching ND2 mortar.
"""
import argparse
import json
from pathlib import Path
import resource
import time
import numpy as np
from scipy.linalg import solve, svdvals
from scipy.sparse import coo_matrix
import bempp_cl.api as bem
import maxwell_fem as fem


def quadrature(order=4):
    x,w = np.polynomial.legendre.leggauss(order)
    x,w = (x+1)/2,w/2
    points = np.array([(a,(1-a)*b) for a in x for b in x]).T
    weights = np.array([wa*wb*(1-a) for a,wa in zip(x,w) for wb in w])
    return points,weights


def local_values(space,triangle,points):
    return np.transpose(space.evaluate(triangle,points),(2,1,0))


def physical_gram(test,trial):
    if test.grid is not trial.grid:
        raise ValueError('Physical pairing requires the same barycentric grid')
    points = np.array([[1/6,2/3,1/6],[1/6,1/6,2/3]])
    rows,cols,values = [],[],[]
    for triangle in range(test.grid.number_of_elements):
        left,right = local_values(test,triangle,points),local_values(trial,triangle,points)
        area = test.grid.integration_elements[triangle]/2
        local = area*np.einsum('pic,pjc->ij',left,right)/3
        rows.extend(np.repeat(test.local2global[triangle],3))
        cols.extend(np.tile(trial.local2global[triangle],3))
        values.extend(local.ravel())
    local = coo_matrix((values,(rows,cols)),shape=(test.grid_dof_count,trial.grid_dof_count)).tocsr()
    return (test.dof_transformation.T@local@trial.dof_transformation).toarray()


def trace_load(test,field,order=4):
    points,weights = quadrature(order)
    local = np.zeros(test.grid_dof_count,dtype=np.complex128)
    for triangle in range(test.grid.number_of_elements):
        indices = test.grid.elements[:,triangle]
        vertices = test.grid.vertices[:,indices].T
        x = vertices[0]+points.T@(vertices[1:]-vertices[0])
        normal = test.grid.normals[triangle]*test.normal_multipliers[triangle]
        trace = np.cross(field(x),normal)
        rhs = test.grid.integration_elements[triangle]*np.einsum('p,pic,pc->i',weights,local_values(test,triangle,points),trace)
        np.add.at(local,test.local2global[triangle],rhs)
    return test.dof_transformation.T@local


def projection_error(space,coefficients,field,order=4):
    points,weights = quadrature(order)
    local = space.dof_transformation@coefficients
    numerator=denominator=0.
    for triangle in range(space.grid.number_of_elements):
        vertices = space.grid.vertices[:,space.grid.elements[:,triangle]].T
        x = vertices[0]+points.T@(vertices[1:]-vertices[0])
        normal = space.grid.normals[triangle]*space.normal_multipliers[triangle]
        exact = np.cross(field(x),normal)
        value = np.einsum('i,pic->pc',local[space.local2global[triangle]],local_values(space,triangle,points))
        jac = space.grid.integration_elements[triangle]
        numerator += jac*np.dot(weights,np.sum(abs(value-exact)**2,axis=1))
        denominator += jac*np.dot(weights,np.sum(abs(exact)**2,axis=1))
    return float(np.sqrt(numerator/denominator))


def spectrum(matrix,left_mass,right_mass):
    singular = svdvals(matrix)
    left_scale = np.sqrt(np.diag(left_mass))
    right_scale = np.sqrt(np.diag(right_mass))
    scaled = matrix/left_scale[:,None]/right_scale[None,:]
    normalized = svdvals(scaled)
    threshold = singular[0]*max(matrix.shape)*np.finfo(float).eps
    return dict(dimension=len(singular),numerical_rank=int(np.sum(singular>threshold)),
        rank_relative_threshold=float(threshold/singular[0]),sigma_max=float(singular[0]),
        sigma_min=float(singular[-1]),condition_2=float(singular[0]/singular[-1]),
        diagonal_mass_scaled_sigma_min=float(normalized[-1]),
        diagonal_mass_scaled_condition_2=float(normalized[0]/normalized[-1]))


def relative(left,right):
    return float(np.linalg.norm(left-right)/np.linalg.norm(right))


def run(level,output):
    started = time.monotonic()
    def stage(name):
        row = dict(stage=name,elapsed_s=time.monotonic()-started)
        print(json.dumps(row),flush=True)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
    stage('imports_complete')
    vertices,tetrahedra,faces = fem.mesh(level-1)
    nodes = np.unique(faces.ravel())
    remap = np.full(len(vertices),-1,dtype=np.int64)
    remap[nodes] = np.arange(len(nodes))
    grid = bem.Grid(vertices[nodes].T,remap[faces].T.astype(np.uint32))
    rwg,snc = bem.function_space(grid,'RWG',0),bem.function_space(grid,'SNC',0)
    bc,rbc = bem.function_space(grid,'BC',0),bem.function_space(grid,'RBC',0)
    bary_rwg,bary_snc = rwg.barycentric_representation(),snc.barycentric_representation()
    params = bem.DefaultParameters()
    params.quadrature.regular = params.quadrature.singular = 4
    def weak(domain,test):
        return bem.operators.boundary.sparse.identity(domain,domain,test,parameters=params).weak_form().A.toarray()
    primal,dual = weak(rwg,snc),weak(rwg,rbc)
    reverse = weak(bc,snc)
    rwg_mass,bc_mass = weak(rwg,rwg),weak(bc,bc)
    stage('bempp_gram_complete')
    direct_primal = physical_gram(bary_snc,bary_rwg)
    direct_dual = physical_gram(rbc,bary_rwg)
    direct_reverse = physical_gram(bary_snc,bc)
    checks = dict(primal_physical_quadrature=relative(primal,direct_primal),
        dual_physical_quadrature=relative(dual,direct_dual),
        reverse_physical_quadrature=relative(reverse,direct_reverse),
        primal_skew_symmetry=float(np.linalg.norm(primal+primal.T)/np.linalg.norm(primal)),
        dual_reverse_adjoint=relative(dual,-reverse.T))
    specs = dict(primal=spectrum(primal,rwg_mass,rwg_mass),dual=spectrum(dual,bc_mass,rwg_mass))
    def constant(x): return np.tile([1.,0.,0.],(len(x),1))
    def plane(x): return constant(x)*np.exp(1j*x[:,2,None])
    projections = {}
    for name,field in [('constant',constant),('plane',plane)]:
        rhs = trace_load(rbc,field)
        coefficients = solve(dual.astype(np.complex128),rhs)
        projections[name] = dict(weak_relative_residual=relative(dual@coefficients,rhs),
            relative_surface_trace_L2=projection_error(bary_rwg,coefficients,field))
    stage('physical_pairing_projection_complete')
    passed = bool(max(checks.values())<1e-12 and specs['dual']['numerical_rank']==rwg.global_dof_count
        and specs['dual']['diagonal_mass_scaled_condition_2']<100
        and projections['constant']['relative_surface_trace_L2']<1e-12
        and max(p['weak_relative_residual'] for p in projections.values())<1e-12)
    report = dict(scope='RWG/SNC and RWG/RBC Gram audit; no ND2/Maxwell solve or antenna qualification',
        level=level,triangles=len(faces),barycentric_triangles=bc.grid.number_of_elements,
        boundary_dofs=rwg.global_dof_count,checks=checks,spectra=specs,projections=projections,
        execution_passed=passed,interface_target_passed=passed,analytic_target_passed=False,
        elapsed_seconds=time.monotonic()-started,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        limits=dict(pairing=1e-12,constant_trace=1e-12,diagonal_mass_scaled_condition_max=100),
        limitations=['ND1 representable constant trace only; plane-wave trace is not exactly RWG0',
            'Small closed quasiuniform polyhedron, not an inf-sup proof on graded antenna meshes',
            'No ND2 trace, stabilized coupling, GPU or antenna memory/speed qualification'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    run(args.level,args.output)
