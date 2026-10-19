"""Cached, isolated MFEM ND1/ND2 C API probes using the dependency image."""
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dev

SOURCE = dev.ROOT/'tools/experiments/mfem_bridge.cpp'
GLOBAL_SOURCE = dev.ROOT/'tools/experiments/mfem_global.cpp'
BASE = dev.ROOT/'build/m2-oracle/fem'
LIBRARY = BASE/'libmfem_bridge.so'


def recipe():
    settings = dev.read(dev.SETTINGS)
    return dict(source_sha256=dev.sha(SOURCE),global_source_sha256=dev.sha(GLOBAL_SOURCE),builder=dev.image_id(settings['builder_image']),
                runtime=dev.image_id(settings['runtime_image']),
                flags=['-std=c++17','-O2','-fPIC','-I/opt/view/include','-I/usr/local/cuda/include','-I/opt/cudss/include'])


def verified():
    manifest = dev.read(BASE/'manifest.json')
    if manifest['recipe']!=recipe() or manifest['binary_sha256']!=dev.sha(LIBRARY):
        raise ValueError('MFEM bridge stale; run tools/experiments/mfem_bridge.py build')
    return manifest


def build():
    BASE.mkdir(parents=True,exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if LIBRARY.exists() and (BASE/'manifest.json').exists():
            try: verified()
            except ValueError: pass
            else:
                print('MFEM bridge unchanged: cached library retained')
                return
        current = recipe()
        started = time.monotonic()
        name = dev.builder(dev.read(dev.SETTINGS))
        target = '/tmp/palace-mfem-bridge'
        try:
            with (BASE/'build.log').open('w') as log:
                def execute(argv):
                    remaining = 120-(time.monotonic()-started)
                    if remaining<=0: raise TimeoutError('MFEM bridge build exceeded 120s')
                    dev.command(argv,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
                execute(['podman','exec',name,'ccache','/opt/view/bin/mpicxx',*current['flags'],'-c',
                         '/src/palace/'+str(SOURCE.relative_to(dev.ROOT)),'-o',target+'.o'])
                execute(['podman','exec',name,'ccache','/opt/view/bin/mpicxx',*current['flags'],'-c',
                         '/src/palace/'+str(GLOBAL_SOURCE.relative_to(dev.ROOT)),'-o',target+'-global.o'])
                execute(['podman','exec',name,'/opt/view/bin/mpicxx','-shared',target+'.o',target+'-global.o',
                         '-L/opt/view/lib','-Wl,-rpath,/opt/view/lib','-lmfem','-o',target+'.so'])
                execute(['podman','cp',name+':'+target+'.so',LIBRARY])
            if recipe()!=current: raise ValueError('MFEM bridge source changed during build')
            dev.write(BASE/'manifest.json',dict(recipe=current,binary_sha256=dev.sha(LIBRARY),
                                              build_seconds=time.monotonic()-started))
        finally:
            subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,check=True)
        print(json.dumps(verified(),indent=2))


if __name__=='__main__':
    if sys.argv[1:] == ['build']: build()
    elif sys.argv[1:] == ['check']: print(json.dumps(verified(),indent=2))
    else: raise SystemExit('Usage: mfem_bridge.py build|check')
