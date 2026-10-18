"""Small CPU Maxwell EFIE oracle; matrices stay in RAM, no geometry simplification in Palace."""
import argparse
import json
from pathlib import Path
import resource
import time
import numpy as np
from scipy.linalg import solve
from scipy.special import spherical_jn,spherical_yn
import bempp_cl.api as bem
import maxwell_reference as reference

K = 1.0


def run(level,output,compression=False,native=False,eta=2.0):
    started = time.monotonic()
    def stage(name):
        row = dict(stage=name,elapsed_s=time.monotonic()-started)
        print(json.dumps(row),flush=True)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
    stage('imports_complete')
    # Independently check the stdlib Mie series using SciPy's special functions.
    coefficient_error = 0.0
    for x in [0.1,1.0,2.5]:
        a,b = reference.coefficients(x)
        for n,(an,bn) in enumerate(zip(a,b),1):
            j,y = spherical_jn(n,x),spherical_yn(n,x)
            dj,dy = spherical_jn(n,x,True),spherical_yn(n,x,True)
            coefficient_error = max(coefficient_error,abs(an-(j+x*dj)/(j+x*dj+1j*(y+x*dy))),abs(bn-j/(j+1j*y)))
    if coefficient_error>1e-13: raise ValueError('Independent Bessel coefficient check failed')
    vertices,faces = reference.icosphere(level)
    grid = bem.Grid(np.asarray(vertices).T,np.asarray(faces,dtype=np.uint32).T)
    rwg = bem.function_space(grid,'RWG',0)
    snc = bem.function_space(grid,'SNC',0)
    params = bem.DefaultParameters()
    params.quadrature.regular = params.quadrature.singular = 4
    stage('grid_spaces_complete')

    @bem.complex_callable
    def trace(x,n,index,result):
        value = np.exp(1j*K*x[2])
        result[0] = 0.0
        result[1] = -value*n[2]
        result[2] = value*n[1]

    incident = bem.GridFunction(rwg,fun=trace,dual_space=snc,parameters=params)
    rhs = incident.projections(snc)
    stage('incident_projection_complete')
    op = bem.operators.boundary.maxwell.electric_field(rwg,rwg,snc,K,parameters=params,
                                                     assembler='dense',device_interface='numba',precision='double')
    matrix = np.asarray(op.weak_form().A)
    assembly_finished = time.monotonic()
    stage('dense_maxwell_assembly_complete')
    coefficients = solve(matrix,rhs,assume_a='gen')
    residual = np.linalg.norm(matrix@coefficients-rhs)/np.linalg.norm(rhs)
    solve_seconds = time.monotonic()-assembly_finished
    solution = bem.GridFunction(rwg,coefficients=coefficients)
    stage('cpu_lu_complete')
    compressed = candidate = None
    if compression:
        from maxwell_hmatrix import probe,support_boxes
        stage('compression_begin')
        compressed,candidate = probe(matrix,support_boxes(grid,rwg),rhs,coefficients,native=native,eta=eta)
        (output/'compression.json').write_text(json.dumps(compressed,indent=2)+'\n')
        stage('compression_cuda_complete')
    u,wu = np.polynomial.legendre.leggauss(16)
    azimuth = np.arange(24)*2*np.pi/24
    directions = np.asarray([(np.sqrt(1-z*z)*np.cos(p),np.sqrt(1-z*z)*np.sin(p),z) for z in u for p in azimuth])
    weights = np.repeat(wu,24)*2*np.pi/24
    points = np.vstack([directions,[[0,0,1],[0,0,-1]]]).T.copy()
    far_op = bem.operators.far_field.maxwell.electric_field(rwg,points,K,parameters=params,
                                                          device_interface='numba',precision='double')
    field = -(far_op*solution)
    exact = np.asarray(reference.far_field(points.T.tolist(),k=K)).T
    scatter = float(np.sum(weights*np.sum(abs(field[:,:-2])**2,axis=0)))
    scatter_exact,extinction_exact = reference.cross_sections()
    extinction = float(4*np.pi/K*field[0,-2].imag)
    field_error = float(np.sqrt(np.sum(weights*np.sum(abs(field[:,:-2]-exact[:,:-2])**2,axis=0))/
                               np.sum(weights*np.sum(abs(exact[:,:-2])**2,axis=0))))
    energy_error = abs(extinction-scatter)/scatter
    scatter_error = abs(scatter-scatter_exact)/scatter_exact
    if compressed is not None:
        candidate_field = -(far_op*bem.GridFunction(rwg,coefficients=candidate))
        compressed['relative_far_field_difference'] = float(np.linalg.norm(candidate_field-field)/np.linalg.norm(field))
        candidate_error = float(np.sqrt(np.sum(weights*np.sum(abs(candidate_field[:,:-2]-exact[:,:-2])**2,axis=0))/
                                       np.sum(weights*np.sum(abs(exact[:,:-2])**2,axis=0))))
        compressed['relative_complex_far_field_L2'] = candidate_error
        compressed['frozen_targets']['far_field_difference'] = 1e-4
        compressed['quality_passed'] = bool(compressed['quality_passed'] and compressed['relative_far_field_difference']<1e-4)
        (output/'compression.json').write_text(json.dumps(compressed,indent=2)+'\n')
    report = dict(scope='PEC sphere Maxwell BEM oracle; no Palace port/antenna qualification',
                  level=level,triangles=len(faces),dofs=rwg.global_dof_count,ka=1.0,
                  time_convention='exp(-iwt), outgoing exp(+ikr), Einc=xhat exp(+ikz)',
                  backend='CPU numba dense complex128',quadrature_regular=4,quadrature_singular=4,
                  matrix_bytes=matrix.nbytes,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                  raw_rhs_relative=float(residual),independent_bessel_error=coefficient_error,
                  relative_complex_far_field_L2=field_error,scattering_cross_section=scatter,
                  scattering_cross_section_exact=scatter_exact,extinction=extinction,extinction_exact=extinction_exact,
                  relative_scattering_error=scatter_error,relative_lossless_energy_error=energy_error,
                  solve_seconds=solve_seconds,elapsed_seconds=time.monotonic()-started,
                  execution_passed=bool(np.isfinite(field_error) and residual<=1e-10),
                  analytic_target_passed=bool(field_error<=0.01 and scatter_error<=0.01 and energy_error<=0.01),
                  target=dict(complex_field=0.01,scattering=0.01,energy=0.01,raw_residual=1e-10),
                  limitations=['Piecewise-flat approximation of smooth sphere; mesh convergence required',
                               'No fitting of phase or amplitude to the analytic field',
                               'No dielectric or FEM-BEM interface yet; no production promotion'])
    if compressed is not None: report['compression'] = compressed
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--compression',action='store_true')
    parser.add_argument('--native-apply',action='store_true')
    parser.add_argument('--compression-eta',type=float,default=2.0)
    args = parser.parse_args()
    if args.native_apply and not args.compression: parser.error('--native-apply requires --compression')
    run(args.level,args.output,args.compression,args.native_apply,args.compression_eta)
