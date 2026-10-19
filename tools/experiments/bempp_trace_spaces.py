"""Compare dual and best-L2 RWG/BC traces, without Maxwell assembly or FEM solve."""
import argparse
import json
from pathlib import Path
import resource
import time
import numpy as np
from scipy.linalg import lu_factor,lu_solve
import bempp_cl.api as bem
import bempp_pairing as pairing
import maxwell_fem as fem


def fields():
    def constant(x):return np.tile([1.,0.,0.],(len(x),1))
    def electric(x):return constant(x)*np.exp(1j*x[:,2,None])
    def magnetic(x):return np.tile([0.,1.,0.],(len(x),1))*np.exp(1j*x[:,2,None])
    return dict(constant_x=constant,plane_e=electric,plane_h=magnetic)


def run(max_level,output):
    started=time.monotonic()
    def stage(name,**extra):
        row=dict(stage=name,elapsed_s=time.monotonic()-started,**extra)
        print(json.dumps(row),flush=True)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
    stage('imports_complete')
    rows=[]
    all_checks=True
    for level in range(1,max_level+1):
        vertices,tetrahedra,faces=fem.mesh(level-1)
        nodes=np.unique(faces.ravel())
        remap=np.full(len(vertices),-1,dtype=np.int64)
        remap[nodes]=np.arange(len(nodes))
        grid=bem.Grid(vertices[nodes].T,remap[faces].T.astype(np.uint32))
        rwg,snc=bem.function_space(grid,'RWG',0),bem.function_space(grid,'SNC',0)
        bc,rbc=bem.function_space(grid,'BC',0),bem.function_space(grid,'RBC',0)
        bary_rwg,bary_snc=rwg.barycentric_representation(),snc.barycentric_representation()
        params=bem.DefaultParameters()
        params.quadrature.regular=params.quadrature.singular=4
        results={}
        for label,trial,test in [('RWG_dual',rwg,rbc),('RWG_best_L2',rwg,bary_rwg),
                                 ('BC_dual',bc,bary_snc),('BC_best_L2',bc,bc)]:
            gram=bem.operators.boundary.sparse.identity(trial,trial,test,parameters=params).weak_form().A.toarray()
            if 'best_L2' in label:
                chol=np.linalg.cholesky(gram)
                if np.linalg.norm(chol@chol.T-gram)/np.linalg.norm(gram)>1e-12:
                    raise ValueError('Mass matrix is not numerically positive definite')
            factor=lu_factor(gram.astype(np.complex128))
            family={}
            for name,field in fields().items():
                rhs=pairing.trace_load(test,field,order=6)
                coefficients=lu_solve(factor,rhs)
                residual=float(np.linalg.norm(gram@coefficients-rhs)/np.linalg.norm(rhs))
                physical_trial=trial.barycentric_representation()
                error6=pairing.projection_error(physical_trial,coefficients,field,order=6)
                error4=pairing.projection_error(physical_trial,coefficients,field,order=4)
                family[name]=dict(surface_trace_L2=error6,weak_residual=residual,quadrature4_vs6_delta=abs(error4-error6))
                all_checks=all_checks and residual<1e-12 and abs(error4-error6)<1e-6 and np.isfinite(error6)
            results[label]=family
        if results['RWG_dual']['constant_x']['surface_trace_L2']>1e-12:
            raise ValueError('RWG dual projection does not reproduce constant trace')
        for family in ['RWG','BC']:
            for name in fields():
                if results[family+'_best_L2'][name]['surface_trace_L2']>results[family+'_dual'][name]['surface_trace_L2']+1e-9:
                    raise ValueError('Best-L2 projection is worse than dual projection')
        row=dict(level=level,triangles=len(faces),dofs=rwg.global_dof_count,projections=results)
        rows.append(row)
        stage('trace_projections_complete',level=level)
    report=dict(scope='RWG/BC dual vs best-L2 trace approximation; no Maxwell solve or antenna qualification',
        levels=rows,execution_passed=bool(all_checks),analytic_target_passed=False,
        elapsed_seconds=time.monotonic()-started,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        targets=dict(weak_residual=1e-12,quadrature_delta=1e-6,RWG_constant_trace=1e-12,best_L2_slack=1e-9),
        limitations=['Surface L2 approximation only, not H(div)^-1/2 stability or a coupled-field error bound',
            'BC need not reproduce a constant trace pointwise; its error is measured, not assigned a relaxed Maxwell threshold',
            'No FEM/BEM nonlocal assembly, transmission, ports or antenna RAM/speed comparison'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True,help='Maximum of a single-process surface hierarchy1..level')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.level,args.output)
