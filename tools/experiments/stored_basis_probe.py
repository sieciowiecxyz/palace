"""Cached one-TU probe linked to actual verified Palace vector methods."""
import argparse
import fcntl
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dev

BASE=dev.ROOT/'build/m3-stored-basis'
SOURCE=dev.ROOT/'tools/experiments/stored_basis_probe.cpp'
PROGRAM=BASE/'stored-basis-probe'
FLAGS=['-std=c++17','-O2','-I/src/palace/palace','-I/opt/view/include',
       '-I/usr/local/cuda/include','-I/opt/cudss/include']
LINK=['-L/src/palace/build/sm120/native','-lpalace','-L/opt/view/lib','-lmfem','-lHYPRE','-lfmt',
      '-L/usr/local/cuda/lib64/stubs','-Wl,--no-as-needed','-lcuda','-Wl,--as-needed',
      '-Wl,-rpath,/native:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib']


def recipe():
    native=dev.verified_build()
    return dict(source_sha256=dev.sha(SOURCE),palace_source_sha256=native['source_sha256'],
        native=native['native'],builder_image_id=native['builder_image_id'],runtime_image_id=native['runtime_base_id'],
        flags=FLAGS,link=LINK)


def verified():
    manifest=dev.read(BASE/'manifest.json')
    if manifest['recipe']!=recipe() or manifest['binary_sha256']!=dev.sha(PROGRAM):
        raise ValueError('Actual stored basis probe stale; rebuild with cache')
    return manifest


def build():
    dev.require_host_memory();BASE.mkdir(parents=True,exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if PROGRAM.exists() and (BASE/'manifest.json').exists():
            try:verified()
            except ValueError:pass
            else:print('Actual stored basis probe unchanged; caches retained');return
        current=recipe();started=time.monotonic();name=dev.builder(dev.read(dev.SETTINGS))
        target='/tmp/palace-stored-basis-probe'
        try:
            with (BASE/'build.log').open('w') as log:
                def execute(argv):
                    remaining=120-(time.monotonic()-started)
                    if remaining<=0:raise TimeoutError('Actual basis probe build exceeded120s')
                    dev.command(argv,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
                execute(['podman','exec',name,'ccache','/opt/view/bin/mpicxx',*FLAGS,
                    '-c','/src/palace/'+str(SOURCE.relative_to(dev.ROOT)),'-o',target+'.o'])
                execute(['podman','exec',name,'/opt/view/bin/mpicxx',target+'.o',*LINK,'-o',target])
                execute(['podman','cp',name+':'+target,PROGRAM])
            if recipe()!=current:raise ValueError('Actual probe source/native changed during build')
            dev.write(BASE/'manifest.json',dict(recipe=current,binary_sha256=dev.sha(PROGRAM),build_seconds=time.monotonic()-started))
        finally:subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print('Actual basis probe build complete; numerical qualification NOT RUN')


def run(output,device,seconds):
    if device not in ['cpu','cuda'] or not 30<=seconds<=120:raise ValueError('Probe requires cpu/cuda and30..120s')
    dev.require_host_memory();manifest=verified();settings=dev.read(dev.SETTINGS)
    gpu=None
    if device=='cuda':
        gpu=dev.capture(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.free','--format=csv,noheader,nounits'])
        if len(gpu.splitlines())!=1 or int(gpu.rsplit(',',1)[1].strip())<768:raise ValueError('Single GPU with >=768MiB free required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    name='palace-stored-basis-'+device+'-'+dev.sha(SOURCE)[:10]
    if subprocess.run(['podman','container','exists',name]).returncode==0:raise ValueError('Prior probe exists; inspect before retry')
    args=['podman','run','--name',name,'--network=none','--read-only','--timeout',str(seconds),
        '--ulimit','core=0:0','--stop-timeout','3','--memory','6g','--memory-swap','6g','--cpus','4',
        # GPU-built libCEED needs the real driver library even for CPU arithmetic.
        '--security-opt=label=disable','--device','nvidia.com/gpu=all',
        '--tmpfs','/tmp:rw,size=512m','--tmpfs','/scratch:rw,size=512m','-w','/scratch',
        '-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=1',
        '-e','LD_LIBRARY_PATH=/native:/opt/palace-cudss/lib:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib',
        '-v',f'{output}:/work','-v',f'{PROGRAM}:/native/stored-basis-probe:ro',
        '-v',f'{dev.BUILD/"native/libpalace.so"}:/native/libpalace.so:ro',
        '--entrypoint','/native/stored-basis-probe',settings['runtime_image'],device,'/work/case.json']
    dev.write(output/'command.json',dict(argv=args,manifest=manifest,device=device,gpu_before=gpu))
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
    dev.write(output/'result.json',dict(complete=complete,exit_code=code,elapsed_seconds=time.monotonic()-started))
    print('Actual stored basis probe terminal: '+('PASS' if complete else 'FAILED'))
    if not complete:raise ValueError('Probe failed; inspect bounded logs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['build','check','run']);parser.add_argument('output',nargs='?',type=Path)
    parser.add_argument('--device',choices=['cpu','cuda'],default='cuda');parser.add_argument('--seconds',type=int,default=60)
    args=parser.parse_args()
    if args.action=='build':build()
    elif args.action=='check':print('Actual Palace probe recipe/binary verified' if verified() else 'invalid')
    elif args.output is None:parser.error('run requires new output directory')
    else:run(args.output,args.device,args.seconds)
