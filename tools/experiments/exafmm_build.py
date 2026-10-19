"""Cached optional ExaFMM oracle addon; never rebuild Palace or modify its venv."""
import fcntl
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dev

BASE=dev.ROOT/'build/m2-oracle/exafmm'
SOURCE=dev.ROOT/'.cache/m2-sources/exafmm-t'
COMMIT='78b7d56f988b3843ba502faf4ac60b0c013aa206'
HEADERS=dev.ROOT/'.cache/m2-build-deps/pybind11-2.13.6'
ENV=dev.ROOT/'build/m2-oracle/venv'
BASE_IMAGE='docker.io/library/ubuntu@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac'
LIBS=['libfftw3.so.3','libfftw3f.so.3','libopenblas.so.0','libgfortran.so.5','libgomp.so.1','libquadmath.so.0']
PROVISION='''export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends g++ ccache libfftw3-dev libopenblas-pthread-dev
dpkg-query -W g++ gcc libfftw3-dev libopenblas-pthread-dev > /exafmm-build-packages.txt
'''
FLAGS=['-std=c++14','-O2','-fPIC','-fopenmp','-march=x86-64-v3']
LINK_FLAGS=['-shared','-fopenmp','-Wl,-rpath,$ORIGIN/lib','-lfftw3f','-lfftw3','-lopenblas']


def cleanup(name,state_path):
    if subprocess.run(['podman','container','exists',name]).returncode==0:
        subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        dev.write(state_path,dev.read_output(['podman','inspect',name])[0]['State'])
        dev.command(['podman','rm',name],stdout=subprocess.DEVNULL)


def tree_hash(path):
    digest=hashlib.sha256()
    for p in sorted(path.rglob('*')):
        if p.is_file():digest.update(str(p.relative_to(path)).encode()+b'\0'+bytes.fromhex(dev.sha(p)))
    return digest.hexdigest()


def python_info():
    return json.loads(dev.capture([ENV/'bin/python','-c',
        'import sys,sysconfig,json;print(json.dumps(dict(base=sys.base_prefix,version=sys.version,include=sysconfig.get_path("include"),suffix=sysconfig.get_config_var("EXT_SUFFIX"))))']))


def image_name():
    key=hashlib.sha256((BASE_IMAGE+PROVISION).encode()).hexdigest()[:16]
    return 'localhost/palace-exafmm-builder:'+key


def ensure_source_headers():
    if not SOURCE.exists():
        dev.command(['git','clone','--depth','1','--branch','v0.1.1','https://github.com/exafmm/exafmm-t.git',SOURCE],timeout=60)
    if dev.capture(['git','-C',SOURCE,'rev-parse','HEAD'])!=COMMIT or dev.capture(['git','-C',SOURCE,'status','--porcelain','--untracked-files=no']):
        raise ValueError('Expected clean pinned ExaFMM source; preserve checkout')
    marker=HEADERS/'pybind11-2.13.6.dist-info/METADATA'
    if not marker.exists():dev.command(['uv','pip','install','--python',ENV/'bin/python','--target',HEADERS,'--no-deps','pybind11==2.13.6'],timeout=60)
    if 'Version: 2.13.6\n' not in marker.read_text():raise ValueError('Expected pinned private pybind11 headers')


def ensure_image():
    tag=image_name()
    if subprocess.run(['podman','image','exists',tag]).returncode==0:return dev.image_id(tag)
    if subprocess.run(['podman','image','exists',BASE_IMAGE]).returncode:dev.command(['podman','pull','--quiet',BASE_IMAGE],timeout=60)
    name='palace-exafmm-image-'+tag.rsplit(':',1)[1]
    if subprocess.run(['podman','container','exists',name]).returncode==0:raise ValueError('Previous addon provision container exists; inspect it, no automatic retry')
    try:
        with (BASE/'image.log').open('w') as log:
            dev.command(['podman','run','--name',name,'--network=host','--timeout','180','--memory','6g','--memory-swap','6g',
                '--cpus','4','--security-opt=label=disable','--tmpfs','/tmp:rw,size=512m','--entrypoint','/bin/sh',BASE_IMAGE,'-eu','-c',PROVISION],stdout=log,stderr=subprocess.STDOUT,timeout=195)
        state=dev.read_output(['podman','inspect',name])[0]['State'];dev.write(BASE/'image-state.json',state)
        if state['Running'] or state['OOMKilled'] or state['ExitCode']!=0:raise ValueError('Addon image provisioning failed')
        dev.command(['podman','commit',name,tag],stdout=subprocess.DEVNULL,timeout=30)
    finally:
        cleanup(name,BASE/'image-state.json')
    return dev.image_id(tag)


def recipe():
    if dev.capture(['git','-C',SOURCE,'rev-parse','HEAD'])!=COMMIT or dev.capture(['git','-C',SOURCE,'status','--porcelain','--untracked-files=no']):raise ValueError('ExaFMM source drift')
    info=python_info()
    return dict(commit=COMMIT,source_sha256=tree_hash(SOURCE/'include'),binding_sha256=dev.sha(SOURCE/'python/exafmm.cpp'),
        pybind_headers_sha256=tree_hash(HEADERS/'pybind11/include'),python=info,flags=FLAGS,link_flags=LINK_FLAGS,libraries=LIBS,
        python_binary_sha256=dev.sha((ENV/'bin/python').resolve()),python_headers_sha256=tree_hash(Path(info['include'])),
        builder_image_id=dev.image_id(image_name()),runtime_image_id=dev.image_id(dev.read(dev.SETTINGS)['runtime_image']))


def verified():
    manifest=dev.read(BASE/'manifest.json')
    if manifest['recipe']!=recipe():raise ValueError('ExaFMM addon recipe changed; build with cache')
    for name,sha in manifest['files_sha256'].items():
        if dev.sha(BASE/name)!=sha:raise ValueError('ExaFMM addon artifact changed')
    return manifest


def build():
    BASE.mkdir(parents=True,exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ensure_source_headers()
        from bempp_oracle import verified as verify_oracle,python_mounts
        verify_oracle()
        if (BASE/'manifest.json').exists():
            try:verified()
            except (ValueError,FileNotFoundError):pass
            else:print('ExaFMM unchanged: binary/image/header/ccache retained');return
        started=time.monotonic();image=ensure_image();current=recipe();info=current['python']
        suffix='exafmm'+info['suffix'];candidate=BASE/'candidate';(candidate/'lib').mkdir(parents=True,exist_ok=True)
        cache=dev.ROOT/'.cache/ccache';cache.mkdir(parents=True,exist_ok=True)
        compile_argv=['/usr/bin/ccache','/usr/bin/g++',*FLAGS,'-I'+info['include'],'-I/pybind/pybind11/include','-I/exafmm-src/include',
            '-c','/exafmm-src/python/exafmm.cpp','-o','/out/exafmm.o']
        link_argv=['/usr/bin/g++','/out/exafmm.o','-o','/out/'+suffix,*LINK_FLAGS]
        script=shlex.join(compile_argv)+'\n'+shlex.join(link_argv)+'\n'+'\n'.join('cp -L /usr/lib/x86_64-linux-gnu/'+name+' /out/lib/'+name for name in LIBS)+'''
cp /exafmm-build-packages.txt /out/packages.txt
cp -L /usr/share/doc/libfftw3-double3/copyright /out/LICENSE.fftw
cp -L /usr/share/doc/libopenblas0-pthread/copyright /out/LICENSE.openblas
ldd /out/exafmm*.so > /out/ldd.txt
'''
        name='palace-exafmm-compile'
        if subprocess.run(['podman','container','exists',name]).returncode==0:raise ValueError('Previous compile container exists; inspect before retry')
        try:
            with (BASE/'build.log').open('w') as log:
                dev.command(['podman','run','--name',name,'--network=none','--read-only','--timeout','120','--memory','6g','--memory-swap','6g','--cpus','4',
                    '--security-opt=label=disable','--tmpfs','/tmp:rw,size=1g','-e','TMPDIR=/tmp','-e','CCACHE_DIR=/ccache',
                    '-v',f'{cache}:/ccache','-v',f'{SOURCE}:/exafmm-src:ro','-v',f'{HEADERS}:/pybind:ro','-v',f'{candidate}:/out',
                    *python_mounts(ENV,Path(info['base'])),'--entrypoint','/bin/sh',image,'-eu','-c',script],stdout=log,stderr=subprocess.STDOUT,timeout=135)
            state=dev.read_output(['podman','inspect',name])[0]['State'];dev.write(BASE/'compile-state.json',state)
            if state['Running'] or state['OOMKilled'] or state['ExitCode']!=0:raise ValueError('Addon compile failed')
        finally:
            cleanup(name,BASE/'compile-state.json')
        if current!=recipe():raise ValueError('Build inputs changed during compile')
        names=[suffix,*['lib/'+name for name in LIBS],'packages.txt','LICENSE.exafmm','LICENSE.fftw','LICENSE.openblas']
        shutil.copy2(SOURCE/'LICENSE',candidate/'LICENSE.exafmm')
        for name in [*names,'ldd.txt']:
            target=BASE/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(candidate/name,target)
        dev.write(BASE/'manifest.json',dict(recipe=current,files_sha256={p:dev.sha(BASE/p) for p in names},build_seconds=time.monotonic()-started))
        print(json.dumps(dict(build_seconds=time.monotonic()-started,binary=suffix,binary_sha256=dev.sha(BASE/suffix),scope='Built only; runtime/import/numerics NOT RUN')))


if __name__=='__main__':
    if sys.argv[1:]==['build']:build()
    elif sys.argv[1:]==['check']:print(json.dumps(verified(),indent=2))
    else:raise SystemExit('Usage: exafmm_build.py build|check')
