"""Cached CUDA shared-header probe. Does not rebuild Palace or dependencies."""
import argparse
import fcntl
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dev

BASE=dev.ROOT/'build/m3-basis'
SOURCE=dev.ROOT/'tools/experiments/mixed_basis.cu'
HEADER=dev.ROOT/'palace/linalg/mixedbasis.hpp'
WORKER=dev.ROOT/'tools/experiments/mixed_basis_worker.py'
LIBRARY=BASE/'libmixed_basis.so'
FLAGS=['-std=c++17','-O3','-Xcompiler=-fPIC','--cudart=shared','-I/src/palace/palace']


def recipe():
    settings=dev.read(dev.SETTINGS)
    return dict(source_sha256=dev.sha(SOURCE),header_sha256=dev.sha(HEADER),flags=FLAGS,
        architecture=settings['architecture'],builder_image_id=dev.image_id(settings['builder_image']),
        runtime_image_id=dev.image_id(settings['runtime_image']))


def verified():
    manifest=dev.read(BASE/'manifest.json')
    if manifest['recipe']!=recipe() or manifest['binary_sha256']!=dev.sha(LIBRARY):
        raise ValueError('Mixed basis probe stale; rebuild with cache')
    return manifest


def cleanup(name,state_path):
    if subprocess.run(['podman','container','exists',name]).returncode==0:
        subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        dev.write(state_path,dev.read_output(['podman','inspect',name])[0]['State'])
        dev.command(['podman','rm',name],stdout=subprocess.DEVNULL)


def build():
    dev.require_host_memory()
    BASE.mkdir(parents=True,exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if LIBRARY.exists() and (BASE/'manifest.json').exists():
            try:verified()
            except ValueError:pass
            else:print('Mixed basis CUDA probe unchanged: cache retained');return
        current=recipe();started=time.monotonic()
        settings=dev.read(dev.SETTINGS);name=dev.builder(settings)
        target='/tmp/palace-mixed-basis'
        try:
            with (BASE/'build.log').open('w') as log:
                def execute(argv):
                    remaining=120-(time.monotonic()-started)
                    if remaining<=0:raise TimeoutError('Mixed basis addon build exceeded120s')
                    dev.command(argv,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
                execute(['podman','exec',name,'ccache','/usr/local/cuda/bin/nvcc',*FLAGS,
                    '-arch=sm_'+settings['architecture'],'-c','/src/palace/'+str(SOURCE.relative_to(dev.ROOT)),
                    '-o',target+'.o'])
                execute(['podman','exec',name,'/usr/local/cuda/bin/nvcc','-shared','--cudart=shared',target+'.o','-o',target+'.so'])
                execute(['podman','cp',name+':'+target+'.so',LIBRARY])
            if current!=recipe():raise ValueError('Probe source changed during build')
            dev.write(BASE/'manifest.json',dict(recipe=current,binary_sha256=dev.sha(LIBRARY),build_seconds=time.monotonic()-started))
        finally:subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print('Mixed basis CUDA addon build complete; numerical qualification NOT RUN')


def run(output,seconds):
    if not 30<=seconds<=120:raise ValueError('Probe requires30..120s deadline')
    import bempp_oracle
    dev.require_host_memory();manifest=verified();environment=bempp_oracle.verified()
    settings=dev.read(dev.SETTINGS)
    gpu=dev.capture(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.free','--format=csv,noheader,nounits'])
    if len(gpu.splitlines())!=1 or int(gpu.rsplit(',',1)[1].strip())<768:raise ValueError('Single GPU with >=768MiB free required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    name='palace-mixed-basis-'+dev.sha(WORKER)[:10]
    if subprocess.run(['podman','container','exists',name]).returncode==0:raise ValueError('Prior probe exists; inspect terminal state, no retry')
    base_python=Path(environment['environment']['base'])
    args=['podman','run','--name',name,'--network=none','--read-only','--timeout',str(seconds),
        '--ulimit','core=0:0','--stop-timeout','3','--memory','6g','--memory-swap','6g','--cpus','4',
        '--security-opt=label=disable','--device','nvidia.com/gpu=all',
        '--tmpfs','/tmp:rw,size=512m','--tmpfs','/scratch:rw,size=512m','-w','/scratch',
        *bempp_oracle.python_mounts(bempp_oracle.ENV,base_python),
        '-v',f'{output}:/work','-v',f'{WORKER}:/scripts/case.py:ro','-v',f'{LIBRARY}:/native/libmixed_basis.so:ro',
        '--entrypoint',str(bempp_oracle.ENV/'bin/python'),settings['runtime_image'],'-u','/scripts/case.py']
    dev.write(output/'command.json',dict(argv=args,manifest=manifest,worker_sha256=dev.sha(WORKER),gpu_before=gpu,environment=environment))
    started=time.monotonic();code=None
    try:
        with (output/'stdout.log').open('w') as stdout,(output/'stderr.log').open('w') as stderr:
            code=subprocess.run(args,stdout=stdout,stderr=stderr,timeout=seconds+15).returncode
    finally:cleanup(name,output/'container-state.json')
    state=dev.read(output/'container-state.json')
    complete=bool(code==0 and state['ExitCode']==0 and not state['OOMKilled'] and (output/'case.json').exists())
    dev.write(output/'result.json',dict(complete=complete,exit_code=code,elapsed_seconds=time.monotonic()-started))
    print('Mixed basis probe terminal: '+('execution complete; inspect numerical gates' if complete else 'FAILED'))
    if not complete:raise ValueError('Probe incomplete; inspect bounded logs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['build','check','run']);parser.add_argument('output',nargs='?',type=Path)
    parser.add_argument('--seconds',type=int,default=60);args=parser.parse_args()
    if args.action=='build':build()
    elif args.action=='check':print('Mixed basis recipe/binary verified' if verified() else 'invalid')
    elif args.output is None:parser.error('run requires new output directory')
    else:run(args.output,args.seconds)
