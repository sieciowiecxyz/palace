"""Cached isolated libCEED/MFEM basis vs cuBLAS FP64/FP32/TF32 action probe."""
import argparse
import fcntl
import math
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dev

BASE=dev.ROOT/'build/m6-ceed-tensor'
HERE=Path(__file__).resolve().parent
SOURCES=[HERE/'ceed_tensor_probe.cpp',HERE/'ceed_tensor_probe.cu',dev.ROOT/'tools/adapter/ceed_fused.cuh']
PROGRAM=BASE/'ceed-tensor-probe'
FLAGS=['-std=c++17','-O2','-I/src/palace/palace','-I/opt/view/include',
       '-I/usr/local/cuda/include','-I/opt/cudss/include']
LINK=['-L/src/palace/build/sm120/native','-lpalace','-L/opt/view/lib','-lmfem','-lHYPRE','-lfmt','-lceed',
      '-L/usr/local/cuda/lib64','-lcublas','-lcudart',
      '-L/usr/local/cuda/lib64/stubs','-Wl,--no-as-needed','-lcuda','-Wl,--as-needed',
      '-Wl,-rpath,/native:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib:/usr/local/cuda/lib64']


def recipe():
    native=dev.verified_build()
    return dict(sources={p.name:dev.sha(p) for p in SOURCES},
        native=native['native'],builder_image_id=native['builder_image_id'],
        runtime_image_id=native['runtime_base_id'],architecture=dev.read(dev.SETTINGS)['architecture'],
        flags=FLAGS,link=LINK)


def verified():
    manifest=dev.read(BASE/'manifest.json')
    if manifest['recipe']!=recipe() or manifest['binary_sha256']!=dev.sha(PROGRAM):
        raise ValueError('CEED tensor probe stale; rebuild with cache')
    return manifest


def build():
    dev.require_host_memory();BASE.mkdir(parents=True,exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if PROGRAM.exists() and (BASE/'manifest.json').exists():
            try:verified()
            except ValueError:pass
            else:print('CEED tensor probe unchanged; cache retained');return
        current=recipe();started=time.monotonic();settings=dev.read(dev.SETTINGS)
        name=dev.builder(settings);target='/tmp/palace-ceed-tensor-probe'
        try:
            with (BASE/'build.log').open('w') as log:
                def execute(argv):
                    remaining=120-(time.monotonic()-started)
                    if remaining<=0:raise TimeoutError('CEED probe build exceeded120s')
                    dev.command(argv,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
                execute(['podman','exec',name,'ccache','/opt/view/bin/mpicxx',*FLAGS,
                    '-c','/src/palace/tools/experiments/ceed_tensor_probe.cpp','-o',target+'.o'])
                execute(['podman','exec',name,'ccache','/usr/local/cuda/bin/nvcc','-std=c++17','-O2',
                    '-arch=sm_'+settings['architecture'],'-c','/src/palace/tools/experiments/ceed_tensor_probe.cu','-o',target+'-cuda.o'])
                execute(['podman','exec',name,'/opt/view/bin/mpicxx',target+'.o',target+'-cuda.o',*LINK,'-o',target])
                execute(['podman','cp',name+':'+target,PROGRAM])
            if recipe()!=current:raise ValueError('CEED probe source/native changed during build')
            dev.write(BASE/'manifest.json',dict(recipe=current,binary_sha256=dev.sha(PROGRAM),build_seconds=time.monotonic()-started))
        finally:
            subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print('CEED tensor probe built; numerical/performance qualification NOT RUN')


def validate_case(case):
    suite=case.get('suite','screen')
    if suite not in ['screen','scale']:raise ValueError('Unknown basis suite')
    scale=suite=='scale'
    if case.get('complete') is not True or len(case.get('rows',[]))!=(42 if scale else 96):
        raise ValueError('Missing basis action coverage')
    expected=set()
    for family in ([0] if scale else range(4)):
        for q in ([14] if scale else [6] if family==3 else [6,14]):
            for comp in ([1,2] if not scale and family==0 and q==14 else [1]):
                for mode in [1,[8,4,2,8][family]]:
                    for elements in ([257,1023,4099,16383,65537,131071,1601320] if scale else [257,131071]):
                        for trans,add in [(False,False),(True,False),(True,True)]:
                            expected.add((family,q,comp,mode,elements,trans,add))
    seen=set()
    def accuracy(check,tolerance):
        if check.get('tolerance')!=tolerance:raise ValueError('Changed action tolerance')
        values=[check.get(k) for k in ['relative_l2','scaled_max']]
        if not all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 for v in values):
            raise ValueError('Invalid action error')
        if check.get('passed') is not all(v<=tolerance for v in values):
            raise ValueError('Action error flag disagrees with measured errors')
    def timing(check):
        for key in ['wall_ms','cuda_interval_ms']:
            values=check[key]
            if len(values)!=3 or not all(isinstance(v,(float,int)) and not isinstance(v,bool) and 0<v<120000 for v in values):
                raise ValueError('Invalid timing coverage')
            if check['median_'+key]!=sorted(values)[1]:raise ValueError('Invalid timing median')
    for row in case['rows']:
        key=tuple(row[k] for k in ['family','Q','components','eval','elements','transpose','add'])
        if key in seen:raise ValueError('Duplicate action')
        seen.add(key)
        if key not in expected or row['P']!=[20,15,10,8][row['family']] or row['N']!=row['elements']*row['components']:
            raise ValueError('Unexpected basis action dimensions')
        if row['canaries_passed'] is not True:raise ValueError('Corrupted basis buffer')
        timing(row['original_timing'])
        if row['elements']==257:
            accuracy(row['original_vs_cpu'],1e-11)
            if row['original_vs_cpu']['passed'] is not True:
                raise ValueError('Original vs independent reference failed')
        if [m['precision'] for m in row['methods']]!=['FP64','FP32_pedantic','TF32_requested']+(['FP32_fused'] if case.get('fused') else []):
            raise ValueError('Missing precision comparison')
        for method in row['methods']:
            tol={'FP64':1e-11,'FP32_pedantic':2e-6,'TF32_requested':2e-3,'FP32_fused':2e-6}[method['precision']]
            accuracy(method['accuracy'],tol)
            if row['elements']==257:
                accuracy(method['accuracy']['independent_cpu'],tol)
                if method['precision']=='FP64' and not method['accuracy']['independent_cpu']['passed']:
                    raise ValueError('FP64 library vs independent reference failed')
            if method['precision']=='FP64' and method['accuracy']['passed'] is not True:
                raise ValueError('FP64 library/layout control failed')
            timing(method['timing'])
            if method['precision']=='FP32_fused' and method['extra_fp32_workspace_bytes']!=row['P']*row['Q']*row['q_components']*4:
                raise ValueError('Unexpected fused vector workspace')
    if seen!=expected:raise ValueError('Incomplete basis action coverage')
    return True


def run(output,seconds,scale=False,fused=False):
    if not 30<=seconds<=120:raise ValueError('Probe requires30..120s deadline')
    dev.require_host_memory();manifest=verified();settings=dev.read(dev.SETTINGS)
    gpu=dev.capture(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.free','--format=csv,noheader,nounits'])
    if len(gpu.splitlines())!=1 or int(gpu.rsplit(',',1)[1].strip())<2048:
        raise ValueError('Single GPU with >=2048MiB free required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    name='palace-ceed-tensor-'+dev.sha(SOURCES[0])[:10]
    if subprocess.run(['podman','container','exists',name]).returncode==0:
        raise ValueError('Prior probe exists; inspect terminal state before retry')
    args=['podman','run','--name',name,'--network=none','--read-only','--timeout',str(seconds),
        '--ulimit','core=0:0','--stop-timeout','3','--memory','6g','--memory-swap','6g','--cpus','4',
        '--security-opt=label=disable','--device','nvidia.com/gpu=all',
        '--tmpfs','/tmp:rw,size=512m','--tmpfs','/scratch:rw,size=512m','-w','/scratch',
        '--unsetenv','NVIDIA_TF32_OVERRIDE','-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=1',
        '-e','LD_LIBRARY_PATH=/native:/opt/palace-cudss/lib:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib:/usr/local/cuda/lib64',
        '-v',f'{output}:/work','-v',f'{PROGRAM}:/native/ceed-tensor-probe:ro',
        '-v',f'{dev.BUILD/"native/libpalace.so"}:/native/libpalace.so:ro',
        '--entrypoint','/native/ceed-tensor-probe',settings['runtime_image'],'/work/case.json']
    if scale:args.append('scale')
    if fused:args.append('fused')
    dev.write(output/'command.json',dict(argv=args,manifest=manifest,gpu_before=gpu,runner_sha256=dev.sha(Path(__file__))))
    started=time.monotonic();code=None
    try:
        with (output/'stdout.log').open('w') as stdout,(output/'stderr.log').open('w') as stderr:
            code=subprocess.run(args,stdout=stdout,stderr=stderr,timeout=seconds+15).returncode
    finally:
        if subprocess.run(['podman','container','exists',name]).returncode==0:
            subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            dev.write(output/'container-state.json',dev.read_output(['podman','inspect',name])[0]['State'])
            dev.command(['podman','rm',name],stdout=subprocess.DEVNULL)
    state=dev.read(output/'container-state.json')
    complete=bool(code==0 and state['ExitCode']==0 and not state['OOMKilled'] and (output/'case.json').exists())
    error=None
    if complete:
        try:validate_case(dev.read(output/'case.json'))
        except (ValueError,KeyError,TypeError) as e:complete=False;error=str(e)
    dev.write(output/'result.json',dict(complete=complete,exit_code=code,validation_error=error,
        elapsed_seconds=time.monotonic()-started,scope='Execution/action-control only. Mixed precision numerical acceptance separate; no RF/TC/solver speedup qualification.'))
    print('CEED tensor probe terminal: '+('complete; inspect accuracy/timings' if complete else 'FAILED'))
    if not complete:raise ValueError('Probe incomplete; inspect bounded logs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['build','check','run']);parser.add_argument('output',nargs='?',type=Path)
    parser.add_argument('--scale',action='store_true',help='ND2/Q14 size ladder through actual N1601320, bounded GPU-resident action probe')
    parser.add_argument('--fused',action='store_true',help='Also screen fused FP32-register action without intermediate vector buffers')
    parser.add_argument('--seconds',type=int,default=120);args=parser.parse_args()
    if args.action=='build':build()
    elif args.action=='check':print('CEED tensor probe verified' if verified() else 'invalid')
    elif args.output is None:parser.error('run requires new output directory')
    else:run(args.output,args.seconds,args.scale,args.fused)
