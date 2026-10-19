"""Bounded Maxwell T/K FMM-vs-dense action control; not a transmission solve."""
import argparse
import gc
import json
import os
from pathlib import Path
import resource
import time
import numpy as np
import bempp_cl.api as bem
import exafmm.helmholtz
import bempp_transmission as transmission


def scratch_usage(root='/scratch'):
    stats=os.statvfs(root)
    capacity=stats.f_blocks*stats.f_frsize
    used=(stats.f_blocks-stats.f_bfree)*stats.f_frsize
    if capacity-used<=4096:
        raise RuntimeError('RAM tmpfs exhausted; ExaFMM stream writes may be truncated')
    return used,capacity


def table_bytes(order,depth):
    """Pinned complex128 file layout: fmm.h::save_matrix/load_matrix, 8 children."""
    nsurf=6*(order-1)**2+2
    return 20*nsurf**2*(depth+1)*16+26*(2*(2*order)**3*8*8)*depth*8+8


def tree_receipts(order):
    from bempp_cl.api.fmm.fmm_assembler import _FMM_CACHE
    rows=[]
    for interface in _FMM_CACHE.values():
        path=Path(interface._fname).resolve()
        if not any(path.is_relative_to(root) for root in ['/scratch','/tmp']):raise ValueError('FMM temp path outside RAM')
        nodes=interface._tree.nodes
        depth=max(n.level for n in nodes)
        expected=table_bytes(order,depth)
        if path.stat().st_size!=expected:raise RuntimeError('ExaFMM RAM table size differs from pinned file layout')
        rows.append(dict(source_points=interface.number_of_source_points,target_points=interface.number_of_target_points,
            nodes=len(nodes),depth=depth,temporary_path=str(path),temporary_file_bytes=path.stat().st_size,expected_table_bytes=expected))
    return rows


def solve_control(level,output,order,ncrit,preconditioner='none'):
    """Small actual FMM GMRES PMCHWT; dense is only the independent oracle."""
    from scipy.linalg import solve
    from scipy.sparse import bmat
    from scipy.sparse.linalg import LinearOperator,gmres,spilu
    from bempp_cl.api.fmm import exafmm as interface_api
    from bempp_cl.api.fmm.fmm_assembler import clear_fmm_cache
    if level!=2 or order not in [8,9] or ncrit!=32:raise ValueError('Solve pilot fixed to B2/p8..9/ncrit32')
    if preconditioner not in ['none','near-ilu']:raise ValueError('Unknown pilot preconditioner')
    begin=time.monotonic()
    mounts=[line.split() for line in Path('/proc/mounts').read_text().splitlines()]
    for root in ['/scratch','/tmp']:
        if not any(v[1]==root and v[2]=='tmpfs' for v in mounts):raise ValueError('Both wave tables require capped RAM tmpfs')
        used,capacity=scratch_usage(root)
        if table_bytes(order,2)+4096>capacity-used:raise ValueError('Predicted B2 table exceeds RAM tmpfs budget')
    if Path.cwd()!=Path('/scratch') or not Path(exafmm.__file__).resolve().is_relative_to('/exafmm'):
        raise ValueError('Expected guarded runtime/private addon')
    params=bem.GLOBAL_PARAMETERS
    params.quadrature.regular=params.quadrature.singular=4
    params.fmm.expansion_order=order;params.fmm.ncrit=ncrit
    params.fmm.dense_evaluation=False;params.fmm.debug=False
    grid=transmission.surface(level)
    rwg,snc=bem.function_space(grid,'RWG',0),bem.function_space(grid,'SNC',0)
    rho=np.sqrt(2.94);count=rwg.global_dof_count
    dense_operators=[];fmm_operators=[];near_operators=[];setup=[];scratch_peaks={};trees=[]
    clear_fmm_cache()
    for k,root in [(1.,'/scratch'),(rho,'/tmp')]:
        directory=Path(root)/'.exafmm';directory.mkdir(exist_ok=True)
        interface_api.FMM_TMP_DIR=str(directory)
        dense_pair=[];fmm_pair=[];near_pair=[]
        for name in ['electric_field','magnetic_field']:
            factory=getattr(bem.operators.boundary.maxwell,name)
            options=dict(parameters=params,device_interface='numba',precision='double')
            start=time.monotonic()
            dense_pair.append(np.asarray(factory(rwg,rwg,snc,k,assembler='dense',**options).weak_form().A))
            dense_seconds=time.monotonic()-start;start=time.monotonic()
            boundary=factory(rwg,rwg,snc,k,assembler='fmm',**options)
            fmm_pair.append(boundary.weak_form())
            if preconditioner=='near-ilu':near_pair.append(boundary.descriptor.singular_part.weak_form().to_sparse().tocsc())
            used,capacity=scratch_usage(root);scratch_peaks[root]=dict(used_bytes=used,capacity_bytes=capacity)
            setup.append(dict(wave_number=float(k),kernel=name,dense_seconds=dense_seconds,fmm_seconds=time.monotonic()-start))
        dense_operators.append(dense_pair);fmm_operators.append(fmm_pair);near_operators.append(near_pair)
        (output/'progress.json').write_text(json.dumps(dict(stage='wave_setup',wave_number=float(k),elapsed_s=time.monotonic()-begin))+'\n')
    trees=tree_receipts(order)
    te,ke=dense_operators[0];ti,ki=dense_operators[1]
    matrix=np.block([[ke+ki,te+ti/rho],[-te-rho*ti,ke+ki]])
    rhs=np.concatenate(transmission.projections(rwg,snc,params))
    start=time.monotonic();reference=solve(matrix,rhs,assume_a='gen');dense_solve_seconds=time.monotonic()-start
    dense_raw=float(np.linalg.norm(matrix@reference-rhs)/np.linalg.norm(rhs))
    preconditioner_report=dict(kind=preconditioner,source='No preconditioner')
    inverse=None
    if preconditioner=='near-ilu':
        start=time.monotonic()
        nte,nke=near_operators[0];nti,nki=near_operators[1]
        near_matrix=bmat([[nke+nki,nte+nti/rho],[-nte-rho*nti,nke+nki]],format='csc')
        factor=spilu(near_matrix,drop_tol=1e-3,fill_factor=5.)
        inverse=LinearOperator(matrix.shape,matvec=factor.solve,dtype=np.complex128)
        def sparse_bytes(value):return value.data.nbytes+value.indices.nbytes+value.indptr.nbytes
        preconditioner_report=dict(kind=preconditioner,source='Exact adjacent-panel singular_part, no dense oracle entries',
            nnz=near_matrix.nnz,matrix_bytes=sparse_bytes(near_matrix),factor_nnz=factor.L.nnz+factor.U.nnz,
            factor_matrix_bytes=sparse_bytes(factor.L)+sparse_bytes(factor.U),drop_tol=1e-3,fill_factor=5.,
            setup_seconds=time.monotonic()-start)
    matvec_calls=0;matvec_seconds=0.
    def action(x):
        nonlocal matvec_calls,matvec_seconds
        start=time.monotonic();t,h=x[:count],x[count:]
        te,ke=fmm_operators[0];ti,ki=fmm_operators[1]
        result=np.concatenate((ke@t+ki@t+te@h+(ti@h)/rho,-te@t-rho*(ti@t)+ke@h+ki@h))
        matvec_calls+=1;matvec_seconds+=time.monotonic()-start
        return result
    operator=LinearOperator(matrix.shape,matvec=action,dtype=np.complex128)
    history=[]
    def callback(value):
        history.append(float(value))
        (output/'progress.json').write_text(json.dumps(dict(stage='gmres',iteration=len(history),relative_estimate=float(value),elapsed_s=time.monotonic()-begin))+'\n')
    start=time.monotonic()
    coeff,info=gmres(operator,rhs,M=inverse,rtol=1e-10,atol=0.,restart=32,maxiter=1,callback=callback,callback_type='pr_norm')
    fmm_solve_seconds=time.monotonic()-start
    fmm_raw=float(np.linalg.norm(action(coeff)-rhs)/np.linalg.norm(rhs))
    independent_raw=float(np.linalg.norm(matrix@coeff-rhs)/np.linalg.norm(rhs))
    solution_error=float(np.linalg.norm(coeff-reference)/np.linalg.norm(reference))
    np.savez(output/'pmchwt-solution.npz',fmm_solution=coeff,dense_solution=reference,rhs=rhs)
    finite=bool(np.isfinite(coeff).all() and np.isfinite([dense_raw,fmm_raw,independent_raw,solution_error]).all())
    passed=bool(finite and info==0 and dense_raw<1e-9 and fmm_raw<1e-9 and independent_raw<1e-9 and solution_error<1e-6)
    for root in ['/scratch','/tmp']:scratch_usage(root)
    fmm_operators.clear();del operator;clear_fmm_cache();gc.collect()
    for root in ['/scratch','/tmp']:
        interface_api.FMM_TMP_DIR=str(Path(root)/'.exafmm');interface_api.cleanup_fmm_tmp()
    report=dict(scope=solve_control.__doc__,level=level,epsilon_r=2.94,expansion_order=order,ncrit=ncrit,
        dofs=2*count,execution_passed=finite,solve_control_passed=passed,analytic_target_passed=False,
        dense_fallback=False,storage_precision='complex128',arithmetic_precision='FP64/complex128',
        residual_precision='FP64/complex128',dense_matrix_bytes=matrix.nbytes,dense_raw=dense_raw,
        fmm_raw=fmm_raw,independent_raw=independent_raw,solution_relative_error=solution_error,
        gmres_info=int(info),gmres_iterations=len(history),gmres_history=history,restart=32,max_cycles=1,
        gmres_callback_norm='Left-preconditioned residual estimate / norm(rhs)',preconditioner=preconditioner_report,
        target=dict(raw=1e-9,solution_relative=1e-6,gmres_rtol=1e-10),
        setup=setup,dense_solve_seconds=dense_solve_seconds,fmm_solve_seconds=fmm_solve_seconds,
        matvec_calls=matvec_calls,matvec_seconds=matvec_seconds,trees=trees,scratch_peaks=scratch_peaks,
        scratch_final_used_bytes={root:scratch_usage(root)[0] for root in ['/scratch','/tmp']},
        elapsed_seconds=time.monotonic()-begin,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        limitations=['Small CPU PMCHWT, not antenna or physical field convergence',
                    'Dense oracle retained; RSS is not FMM-only memory',
                    'Two existing 512MiB RAM tmpfs mounts retain one wave table each; no rebuilt tree per iteration',
                    'GMRES bounded to one 32-step cycle; nonconvergence is a failure, not a changed tolerance'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


def run(level,output,order=6,ncrit=64):
    if level not in [2,3] or order not in [4,6,8] or not 16<=ncrit<=128:raise ValueError('Bounded FMM control options')
    begin=time.monotonic()
    def stage(name,**extra):
        row=dict(stage=name,elapsed_s=time.monotonic()-begin,**extra)
        (output/'progress.json').write_text(json.dumps(row)+'\n');print(json.dumps(row),flush=True)
    # ExaFMM uses cwd/.exafmm/*.tmp; require RAM rather than a disk fallback.
    mounts=[line.split() for line in Path('/proc/mounts').read_text().splitlines()]
    if Path.cwd()!=Path('/scratch') or not any(v[1]=='/scratch' and v[2]=='tmpfs' for v in mounts):raise ValueError('FMM working directory must be capped tmpfs')
    if not Path(exafmm.__file__).resolve().is_relative_to('/exafmm'):
        raise ValueError('Expected private pinned addon')
    params=bem.GLOBAL_PARAMETERS
    params.quadrature.regular=params.quadrature.singular=4
    params.fmm.expansion_order=order;params.fmm.ncrit=ncrit
    params.fmm.dense_evaluation=False;params.fmm.debug=False
    grid=transmission.surface(level)
    rwg,snc=bem.function_space(grid,'RWG',0),bem.function_space(grid,'SNC',0)
    rng=np.random.default_rng(4137)
    vectors=rng.standard_normal((3,rwg.global_dof_count))+1j*rng.standard_normal((3,rwg.global_dof_count))
    rows=[];trees=[];peak_scratch_used=0
    stage('import_and_spaces_complete',dofs=rwg.global_dof_count)
    for k in [1.,np.sqrt(2.94)]:
        for name in ['electric_field','magnetic_field']:
            factory=getattr(bem.operators.boundary.maxwell,name)
            before=time.monotonic()
            dense=np.asarray(factory(rwg,rwg,snc,k,parameters=params,assembler='dense',device_interface='numba',precision='double').weak_form().A)
            dense_setup=time.monotonic()-before
            before=time.monotonic()
            fmm=factory(rwg,rwg,snc,k,parameters=params,assembler='fmm',device_interface='numba',precision='double').weak_form()
            fmm_setup=time.monotonic()-before
            used,capacity=scratch_usage()
            peak_scratch_used=max(peak_scratch_used,used)
            errors=[];times=[]
            for x in vectors:
                before=time.monotonic();value=fmm@x;times.append(time.monotonic()-before)
                exact=dense@x
                if value.shape!=exact.shape:raise ValueError('FMM action shape differs from dense')
                errors.append(float(np.linalg.norm(value-exact)/np.linalg.norm(exact)))
            row=dict(wave_number=float(k),kernel=name,dense_setup_seconds=dense_setup,fmm_setup_seconds=fmm_setup,
                dense_matrix_bytes=dense.nbytes,action_relative_errors=errors,fmm_apply_seconds=times,
                dtype=str(value.dtype),shape=list(fmm.shape))
            if not np.isfinite(errors).all():raise ValueError('Nonfinite FMM actions')
            rows.append(row);stage('operator_complete',wave_number=float(k),kernel=name,error=max(errors))
        trees.extend(dict(wave_number=float(k),**receipt) for receipt in tree_receipts(order))
        # Each wave is an independent control: retain only its scalar receipt.
        del fmm
        from bempp_cl.api.fmm.fmm_assembler import clear_fmm_cache
        from bempp_cl.api.fmm.exafmm import cleanup_fmm_tmp
        clear_fmm_cache();cleanup_fmm_tmp();gc.collect()
    loaded=[line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines() if '/exafmm/lib/' in line]
    private_blas=any(Path(p).name=='libopenblas.so.0' for p in loaded)
    private_fftw=any(Path(p).name=='libfftw3.so.3' for p in loaded)
    if not private_blas or not private_fftw:raise ValueError('Expected pinned private BLAS/FFTW')
    passed=bool(trees and min(t['depth'] for t in trees)>=2 and max(max(r['action_relative_errors']) for r in rows)<1e-6)
    used,capacity=scratch_usage()
    report=dict(scope=__doc__,level=level,expansion_order=order,ncrit=ncrit,dofs=rwg.global_dof_count,
        scratch_used_bytes=used,scratch_capacity_bytes=capacity,scratch_peak_observed_bytes=peak_scratch_used,
        cache_policy='Sequential independent waves; release tree and RAM temp after each wave',
        rows=rows,trees=trees,dense_fallback=False,private_loaded_libraries=sorted(set(loaded)),
        execution_passed=True,operator_control_passed=passed,analytic_target_passed=False,target=dict(action_relative=1e-6,min_tree_depth=2),
        elapsed_seconds=time.monotonic()-begin,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        limitations=['Small operator actions only, not PMCHWT solution or higher-mesh field convergence',
                     'Shared-process RSS includes dense oracle and both FMM trees; not an FMM-only peak',
                     'CPU backend; no CUDA, antenna S/VSWR or performance promotion'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[2,3],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fmm-order',type=int,choices=[4,6,8,9],default=6)
    parser.add_argument('--fmm-ncrit',type=int,default=64)
    parser.add_argument('--solve',action='store_true')
    parser.add_argument('--fmm-preconditioner',choices=['none','near-ilu'],default='none')
    args=parser.parse_args()
    if args.solve:solve_control(args.level,args.output,args.fmm_order,args.fmm_ncrit,args.fmm_preconditioner)
    else:
        if args.fmm_preconditioner!='none':parser.error('Preconditioner applies only to solve')
        run(args.level,args.output,args.fmm_order,args.fmm_ncrit)
