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


def scratch_usage():
    stats=os.statvfs('/scratch')
    capacity=stats.f_blocks*stats.f_frsize
    used=(stats.f_blocks-stats.f_bfree)*stats.f_frsize
    if capacity-used<=4096:
        raise RuntimeError('RAM tmpfs exhausted; ExaFMM stream writes may be truncated')
    return used,capacity


def tree_receipts():
    from bempp_cl.api.fmm.fmm_assembler import _FMM_CACHE
    rows=[]
    for interface in _FMM_CACHE.values():
        path=Path(interface._fname).resolve()
        if not path.is_relative_to('/scratch'):raise ValueError('FMM temp path outside RAM')
        nodes=interface._tree.nodes
        rows.append(dict(source_points=interface.number_of_source_points,target_points=interface.number_of_target_points,
            nodes=len(nodes),depth=max(n.level for n in nodes),temporary_path=str(path),temporary_file_bytes=path.stat().st_size))
    return rows


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
        trees.extend(dict(wave_number=float(k),**receipt) for receipt in tree_receipts())
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
    parser.add_argument('--fmm-order',type=int,choices=[4,6,8],default=6)
    parser.add_argument('--fmm-ncrit',type=int,default=64)
    args=parser.parse_args();run(args.level,args.output,args.fmm_order,args.fmm_ncrit)
