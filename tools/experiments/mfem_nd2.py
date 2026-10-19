"""ND2 global-space/face-transform oracle before Maxwell FEM-BEM coupling."""
import argparse
import json
from pathlib import Path
import resource
import time
import numpy as np
from scipy.sparse.linalg import spsolve
import maxwell_fem as fem
import maxwell_nd as nd


def run(level,output,epsilon=1.):
    if epsilon not in [1.,2.94]:raise ValueError('Analytic homogeneous probe supports epsilon1/2.94')
    k=np.sqrt(epsilon)
    started = time.monotonic()
    def stage(name):
        row = dict(stage=name,elapsed_s=time.monotonic()-started)
        print(json.dumps(row),flush=True)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
    stage('imports_complete')
    vertices,tetrahedra,faces = fem.mesh(level-1)
    with nd.GlobalND(vertices,tetrahedra,faces) as space:
        mass,curl = space.matrix(0),space.matrix(1)
        stage('mfem_global_nd2_assembly_complete')
        checks = nd.audit_basis(space,mass,curl)
        if max(checks[key] for key in checks if key!='nonidentity_face_transform_cells')>1e-11:
            raise ValueError('ND2 physical basis/orientation audit failed')
        if space.nonidentity==0: raise ValueError('Mesh did not exercise ND2 face transformations')
        stage('nd2_orientation_polynomial_quadrature_complete')
        operator = curl-epsilon*mass
        boundary = space.boundary()
        interior = np.setdiff1d(np.arange(space.ndofs),boundary)
        solution = space.project(2,k)
        projection_errors = nd.plane_field_errors(space,solution,k=k,order=6)
        rhs = -operator[interior][:,boundary]@solution[boundary]
        solve_start = time.monotonic()
        solution[interior] = spsolve(operator[interior][:,interior].astype(np.complex128),rhs)
        solve_seconds = time.monotonic()-solve_start
        raw = float(np.linalg.norm((operator@solution)[interior])/np.linalg.norm(rhs))
        coarse_quad = nd.plane_field_errors(space,solution,k=k,order=4)
        errors = nd.plane_field_errors(space,solution,k=k,order=6)
        quad = nd.plane_field_errors(space,solution,k=k,order=8)
        quad_delta = max(abs(errors[key]-quad[key]) for key in ['relative_E_L2','relative_H_L2'])
        coarse_delta = max(abs(errors[key]-coarse_quad[key]) for key in ['relative_E_L2','relative_H_L2'])
        sparse_bytes = sum(a.data.nbytes+a.indices.nbytes+a.indptr.nbytes for a in [mass,curl])
        # Preserve a cheap regression of the unchanged legacy ND1 API too.
        legacy = None
        if level==1:
            legacy = fem.assemble(vertices,tetrahedra,fem.MFEM())[-1]
        report = dict(scope='Actual global MFEM ND2 plane-wave Dirichlet reference; not FEM-BEM or antenna',
            level=level,epsilon_r=epsilon,wave_number=k,
            magnetic_normalization='curl(E)/(ik)=physical H/sqrt(epsilon), mu=k0=1; relative error unchanged',
            tetrahedra=len(tetrahedra),triangles=len(faces),fem_dofs=space.ndofs,
            local_dofs=space.local_dofs,boundary_dofs=len(boundary),interior_dofs=len(interior),
            mfem=dict(version=space.version,git=space.git),checks=checks,legacy_nd1_regression=legacy,
            projection_field_errors=projection_errors,dirichlet_field_errors=errors,
            raw_interior_rhs_relative=raw,field_quadrature6_vs8_delta=quad_delta,
            quadrature8_check_field_errors=quad,field_quadrature4_vs6_delta=coarse_delta,
            mass_curl_csr_bytes=sparse_bytes,solve_seconds=solve_seconds,
            elapsed_seconds=time.monotonic()-started,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            execution_passed=bool(raw<1e-10 and quad_delta<1e-6 and np.isfinite([errors['relative_E_L2'],errors['relative_H_L2']]).all()),
            analytic_target_passed=bool(errors['relative_E_L2']<0.01 and errors['relative_H_L2']<0.01),
            target=dict(E_L2=0.01,H_L2=0.01,raw=1e-10,orientation_polynomial=1e-11,quadrature_delta=1e-6,quadrature_pair=[6,8]),
            limitations=['Exact analytic boundary data on same bounded polyhedron, not an absorbing exterior reference',
                'ND2 interpolation of analytic boundary data; no BEM trace projection/BC mortar yet',
                'CPU sparse global assembly/LU; no GPU, port S/VSWR, dielectric transmission or antenna speedup'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--epsilon-r',type=float,choices=[1.,2.94],default=1.)
    args = parser.parse_args()
    run(args.level,args.output,args.epsilon_r)
