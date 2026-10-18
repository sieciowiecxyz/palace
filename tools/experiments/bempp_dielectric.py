"""CPU PMCHWT dielectric-sphere oracle; no FEM interface or antenna qualification.

Scaled multitrace conventions follow pinned Bempp maxwell_dielectric.py:
(Ainterior + Aexterior)[E x n, H x n] = [Einc x n, Hinc x n].
"""
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

EPSILON = 2.94
K = 1.0


def run(level,output,volume_preserving=False):
    started = time.monotonic()
    def stage(name):
        row = dict(stage=name,elapsed_s=time.monotonic()-started)
        print(json.dumps(row),flush=True)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
    stage('imports_complete')
    bessel_error = 0.0
    for x in [0.1,1.0,2.5]:
        a,b = reference.dielectric_coefficients(x,EPSILON)
        m = np.sqrt(EPSILON)
        for n,(an,bn) in enumerate(zip(a,b),1):
            psi,dp = x*spherical_jn(n,x),spherical_jn(n,x)+x*spherical_jn(n,x,True)
            xi = x*(spherical_jn(n,x)+1j*spherical_yn(n,x))
            dxi = dp+1j*(spherical_yn(n,x)+x*spherical_yn(n,x,True))
            inner,di = m*x*spherical_jn(n,m*x),spherical_jn(n,m*x)+m*x*spherical_jn(n,m*x,True)
            bessel_error = max(bessel_error,abs(an-(m*inner*dp-psi*di)/(m*inner*dxi-xi*di)),
                               abs(bn-(inner*dp-m*psi*di)/(inner*dxi-m*xi*di)))
    if bessel_error>1e-13: raise ValueError('Independent dielectric Bessel check failed')
    vertices,faces = reference.icosphere(level,volume_preserving=volume_preserving)
    grid = bem.Grid(np.asarray(vertices).T,np.asarray(faces,dtype=np.uint32).T)
    rwg,snc = bem.function_space(grid,'RWG',0),bem.function_space(grid,'SNC',0)
    params = bem.DefaultParameters()
    params.quadrature.regular = params.quadrature.singular = 4
    stage('grid_spaces_complete')

    @bem.complex_callable
    def electric_trace(x,n,index,result):
        value = np.exp(1j*K*x[2])
        result[0],result[1],result[2] = 0.0,-value*n[2],value*n[1]

    @bem.complex_callable
    def magnetic_trace(x,n,index,result):
        value = np.exp(1j*K*x[2])
        result[0],result[1],result[2] = value*n[2],0.0,-value*n[0]

    rhs = np.concatenate([bem.GridFunction(rwg,fun=f,dual_space=snc,parameters=params).projections(snc)
                           for f in [electric_trace,magnetic_trace]])
    stage('incident_projection_complete')
    def operators(wavenumber):
        options = dict(parameters=params,assembler='dense',device_interface='numba',precision='double')
        e = bem.operators.boundary.maxwell.electric_field(rwg,rwg,snc,wavenumber,**options).weak_form().A
        h = bem.operators.boundary.maxwell.magnetic_field(rwg,rwg,snc,wavenumber,**options).weak_form().A
        return np.asarray(e),np.asarray(h)
    e_ext,h_ext = operators(K)
    stage('exterior_assembly_complete')
    rho = np.sqrt(EPSILON)
    e_int,h_int = operators(K*rho)
    stage('interior_assembly_complete')
    diagonal = h_ext+h_int
    matrix = np.block([[diagonal,e_ext+e_int/rho],[-e_ext-rho*e_int,diagonal]])
    assembled = time.monotonic()
    stage('pmchwt_assembly_complete')
    coefficients = solve(matrix,rhs,assume_a='gen')
    residual = float(np.linalg.norm(matrix@coefficients-rhs)/np.linalg.norm(rhs))
    solve_seconds = time.monotonic()-assembled
    count = rwg.global_dof_count
    electric = bem.GridFunction(rwg,coefficients=coefficients[:count])
    magnetic = bem.GridFunction(rwg,coefficients=coefficients[count:])
    stage('cpu_lu_complete')
    u,wu = np.polynomial.legendre.leggauss(16)
    azimuth = np.arange(24)*2*np.pi/24
    directions = np.asarray([(np.sqrt(1-z*z)*np.cos(p),np.sqrt(1-z*z)*np.sin(p),z) for z in u for p in azimuth])
    weights = np.repeat(wu,24)*2*np.pi/24
    points = np.vstack([directions,[[0,0,1],[0,0,-1]]]).T.copy()
    options = dict(parameters=params,device_interface='numba',precision='double')
    e_far = bem.operators.far_field.maxwell.electric_field(rwg,points,K,**options)
    h_far = bem.operators.far_field.maxwell.magnetic_field(rwg,points,K,**options)
    field = -(e_far*magnetic)-(h_far*electric)
    exact = np.asarray(reference.far_field(points.T.tolist(),k=K,epsilon_r=EPSILON)).T
    scatter = float(np.sum(weights*np.sum(abs(field[:,:-2])**2,axis=0)))
    scatter_exact,extinction_exact = reference.cross_sections(epsilon_r=EPSILON)
    extinction = float(4*np.pi/K*field[0,-2].imag)
    field_error = float(np.sqrt(np.sum(weights*np.sum(abs(field[:,:-2]-exact[:,:-2])**2,axis=0))/
                               np.sum(weights*np.sum(abs(exact[:,:-2])**2,axis=0))))
    energy_error,scatter_error = abs(extinction-scatter)/scatter,abs(scatter-scatter_exact)/scatter_exact
    report = dict(scope='Dielectric sphere PMCHWT Maxwell BEM oracle; no FEM interface or antenna',
                  level=level,triangles=len(faces),dofs=2*count,ka=K,epsilon_r=EPSILON,mu_r=1.0,
                  geometry=dict(target_sphere_radius=1.0,volume_preserving=volume_preserving,
                                vertex_radius=float(np.linalg.norm(vertices[0])),
                                mesh_volume=reference.signed_volume(vertices,faces),
                                rule='Scale by (exact sphere volume / original mesh volume)^(1/3); no field fit'),
                  time_convention='exp(-iwt), outgoing exp(+ikr), Einc=xhat exp(+ikz)',
                  backend='CPU numba dense complex128, all-RWG/SNC scaled multitrace',
                  quadrature_regular=4,quadrature_singular=4,matrix_bytes=matrix.nbytes,
                  max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                  raw_rhs_relative=residual,independent_bessel_error=bessel_error,
                  relative_complex_far_field_L2=field_error,scattering_cross_section=scatter,
                  scattering_cross_section_exact=scatter_exact,extinction=extinction,extinction_exact=extinction_exact,
                  relative_scattering_error=scatter_error,relative_lossless_energy_error=energy_error,
                  solve_seconds=solve_seconds,elapsed_seconds=time.monotonic()-started,
                  execution_passed=bool(np.isfinite(field_error) and residual<=1e-10),
                  analytic_target_passed=bool(field_error<=0.01 and scatter_error<=0.01 and energy_error<=0.01),
                  target=dict(complex_field=0.01,scattering=0.01,energy=0.01,raw_residual=1e-10),
                  limitations=['Piecewise-flat sphere; mesh convergence required; no phase/amplitude fitting',
                               'CPU dense only; not a hybrid FEM-BEM interface or antenna port validation'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--volume-preserving',action='store_true')
    args = parser.parse_args()
    run(args.level,args.output,args.volume_preserving)
