#!/usr/bin/env python3
"""Pinned, isolated CPU Maxwell oracle; no new dependencies in Palace builds."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import dev
import mfem_bridge

BASE = dev.ROOT/'build/m2-oracle'
ENV = BASE/'venv'
SOURCE = dev.ROOT/'.cache/m2-sources/bempp-cl'
COMMIT = 'a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0'
REQUIREMENTS = dev.ROOT/'tools/experiments/bempp-requirements.txt'
CASE = dev.ROOT/'tools/experiments/bempp_sphere.py'
DIELECTRIC_CASE = dev.ROOT/'tools/experiments/bempp_dielectric.py'
COUPLING_CASE = dev.ROOT/'tools/experiments/bempp_coupling.py'
PAIRING_CASE = dev.ROOT/'tools/experiments/bempp_pairing.py'
ND2_CASE = dev.ROOT/'tools/experiments/mfem_nd2.py'
ND_COUPLING_CASE = dev.ROOT/'tools/experiments/bempp_nd2_coupling.py'
TRACE_CASE = dev.ROOT/'tools/experiments/bempp_trace_spaces.py'
TRANSMISSION_CASE = dev.ROOT/'tools/experiments/bempp_transmission.py'
ND_API = dev.ROOT/'tools/experiments/maxwell_nd.py'
FEM_API = dev.ROOT/'tools/experiments/maxwell_fem.py'
REFERENCE = dev.ROOT/'tools/maxwell_reference.py'
COMPRESSION = dev.ROOT/'tools/experiments/maxwell_hmatrix.py'
CUDA_SOURCE = dev.ROOT/'tools/experiments/maxwell_apply.cu'
CUDA_BUILD = BASE/'cuda'
CUDA_LIBRARY = CUDA_BUILD/'libmaxwell_apply.so'


def cuda_recipe():
    settings = dev.read(dev.SETTINGS)
    return dict(source_sha256=dev.sha(CUDA_SOURCE),architecture=settings['architecture'],
                builder_image_id=dev.image_id(settings['builder_image']),
                runtime_image_id=dev.image_id(settings['runtime_image']),
                flags=['-std=c++17','-O3','-Xcompiler=-fPIC','--cudart=shared'])


def verified_cuda():
    manifest = dev.read(CUDA_BUILD/'manifest.json')
    if manifest['recipe']!=cuda_recipe() or manifest['binary_sha256']!=dev.sha(CUDA_LIBRARY):
        raise ValueError('Native Maxwell apply stale; run build-cuda')
    return manifest


def build_cuda():
    CUDA_BUILD.mkdir(parents=True,exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (CUDA_BUILD/'manifest.json').exists() and CUDA_LIBRARY.exists():
            try: verified_cuda()
            except ValueError: pass
            else:
                print('Native Maxwell apply unchanged: cached library retained')
                return
        recipe = cuda_recipe()
        settings = dev.read(dev.SETTINGS)
        started = time.monotonic()
        name = dev.builder(settings)
        target = '/tmp/palace-maxwell-apply'
        try:
            with (CUDA_BUILD/'build.log').open('w') as log:
                def execute(argv):
                    remaining = 120-(time.monotonic()-started)
                    if remaining<=0: raise TimeoutError('Native CUDA build exceeded 120s budget')
                    dev.command(argv,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
                execute(['podman','exec',name,'ccache','/usr/local/cuda/bin/nvcc',
                             *recipe['flags'],'-arch=sm_'+settings['architecture'],'-c',
                             '/src/palace/'+str(CUDA_SOURCE.relative_to(dev.ROOT)),'-o',target+'.o'])
                execute(['podman','exec',name,'/usr/local/cuda/bin/nvcc','-shared','--cudart=shared',
                             target+'.o','-o',target+'.so'])
                execute(['podman','cp',name+':'+target+'.so',CUDA_LIBRARY])
            if cuda_recipe()!=recipe: raise ValueError('CUDA source changed during build')
            dev.write(CUDA_BUILD/'manifest.json',dict(recipe=recipe,binary_sha256=dev.sha(CUDA_LIBRARY),
                                                    build_seconds=time.monotonic()-started))
        finally:
            subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,check=True)
        print(json.dumps(verified_cuda(),indent=2))


def environment():
    code = ('import importlib.metadata as m,sys,json;'
            'print(json.dumps(dict(python=sys.version,base=sys.base_prefix,'
            'packages={n:m.version(n) for n in '+repr(['bempp-cl']+[line.split('==')[0] for line in REQUIREMENTS.read_text().splitlines() if line])+ '})))')
    return json.loads(dev.capture([ENV/'bin/python','-c',code]))


def package_hash():
    package = next((ENV/'lib').glob('python*/site-packages/bempp_cl'))
    value = hashlib.sha256()
    for p in sorted(package.rglob('*')):
        if p.is_file() and p.suffix in ['.py','.cl','.h','.npz']:
            value.update(str(p.relative_to(package)).encode()+b'\0'+bytes.fromhex(dev.sha(p)))
    return value.hexdigest()


def setup():
    if not SOURCE.exists():
        dev.command(['git','clone','https://github.com/bempp/bempp-cl.git',SOURCE],timeout=60)
        dev.command(['git','-C',SOURCE,'checkout','--detach',COMMIT])
    if dev.capture(['git','-C',SOURCE,'rev-parse','HEAD'])!=COMMIT or dev.capture(['git','-C',SOURCE,'status','--porcelain','--untracked-files=no']):
        raise ValueError('Expected clean pinned Bempp source; preserve existing checkout')
    BASE.mkdir(parents=True,exist_ok=True)
    if (BASE/'manifest.json').exists():
        try:
            verified()
        except ValueError:
            pass
        else:
            print('Oracle unchanged: pinned environment and JIT cache retained')
            return
    if not (ENV/'bin/python').exists():
        dev.command(['uv','venv','--python','3.12.15',ENV],timeout=60)
    dev.command(['uv','pip','install','--python',ENV/'bin/python','-r',REQUIREMENTS,SOURCE],timeout=120)
    info = environment()
    for row in REQUIREMENTS.read_text().splitlines():
        if row and info['packages'][row.split('==')[0]]!=row.split('==')[1]:
            raise ValueError('Unpinned dependency')
    manifest = dict(source_url='https://github.com/bempp/bempp-cl',source_commit=COMMIT,
                    requirements_sha256=dev.sha(REQUIREMENTS),environment=info,
                    python_binary_sha256=dev.sha((ENV/'bin/python').resolve()),
                    bempp_code_sha256=package_hash(),runtime_image_id=dev.image_id(dev.read(dev.SETTINGS)['runtime_image']))
    dev.write(BASE/'manifest.json',manifest)
    print(json.dumps(manifest,indent=2))


def verified():
    manifest = dev.read(BASE/'manifest.json')
    if (manifest['source_commit']!=COMMIT or manifest['requirements_sha256']!=dev.sha(REQUIREMENTS)
        or manifest['environment']!=environment() or manifest['bempp_code_sha256']!=package_hash()
        or manifest['python_binary_sha256']!=dev.sha((ENV/'bin/python').resolve())
        or manifest['runtime_image_id']!=dev.image_id(dev.read(dev.SETTINGS)['runtime_image'])):
        raise ValueError('Oracle environment stale/modified; run setup')
    return manifest


def python_mounts(env, base):
    """Preserve the venv's configured interpreter alias inside the container."""
    base = Path(base).resolve()
    config = dict(line.split(' = ', 1) for line in (env/'pyvenv.cfg').read_text().splitlines()
                  if ' = ' in line)
    home = Path(config['home']).parent
    if not home.is_absolute() or home.resolve()!=base or not (env/'bin/python').resolve().is_relative_to(base):
        raise ValueError('Venv interpreter and configured Python base disagree')
    mounts = [(env, env), (base, base)]
    if home!=base:
        mounts.append((base, home))
    return [arg for source,target in mounts for arg in ['-v',f'{source}:{target}:ro']]


def run(output,level,seconds,compression=False,native=False,eta=2.0,physics='pec',volume_preserving=False,duality='electric',surface_level=None,epsilon_r=None,reference_only=False):
    if level not in [1,2,3] or not 30<=seconds<=180:
        raise ValueError('Oracle requires level1..3, limit30..180s')
    if not 1<=eta<=4: raise ValueError('Compression eta must be in [1,4]')
    if physics not in ['pec','dielectric','coupling','pairing','nd2','nd2-coupling','traces','transmission'] or (physics!='pec' and (compression or native)):
        raise ValueError('Only PEC supports the optional CUDA compression probe')
    if volume_preserving and physics!='dielectric': raise ValueError('Volume rule is an explicit dielectric mesh variant')
    if duality not in ['electric','magnetic'] or (duality!='electric' and physics!='nd2-coupling'):
        raise ValueError('Magnetic duality applies only to the ND2 coupling probe')
    maximum_surface=4 if physics=='transmission' and reference_only else 3
    if surface_level is not None and (physics not in ['nd2-coupling','transmission'] or not level<=surface_level<=maximum_surface):
        raise ValueError('Independent surface hierarchy must refine the ND2 coupling boundary')
    if epsilon_r is not None and (physics!='transmission' or epsilon_r not in [1.,2.94]):
        raise ValueError('Explicit epsilon applies only to the transmission screening case')
    if physics=='transmission' and (level if surface_level is None else surface_level)<2:
        raise ValueError('Transmission requires BEM level2 or3 for a reference hierarchy')
    if reference_only and (physics!='transmission' or epsilon_r not in [1.,2.94]):
        raise ValueError('Reference-only calibration requires explicit transmission epsilon1/2.94')
    source = {'pec':CASE,'dielectric':DIELECTRIC_CASE,'coupling':COUPLING_CASE,'pairing':PAIRING_CASE,
              'nd2':ND2_CASE,'nd2-coupling':ND_COUPLING_CASE,'traces':TRACE_CASE,'transmission':TRANSMISSION_CASE}[physics]
    dev.require_host_memory()
    manifest = verified()
    if native and not compression: raise ValueError('--native-apply requires --compression')
    cuda = verified_cuda() if native else None
    bridge = mfem_bridge.verified() if physics in ['coupling','nd2','nd2-coupling','transmission'] else None
    output = Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    (BASE/'jit-cache').mkdir(exist_ok=True)
    settings = dev.read(dev.SETTINGS)
    name = 'palace-bempp-'+hashlib.sha256(str(output).encode()).hexdigest()[:12]
    base_python = manifest['environment']['base']
    args = ['podman','run','--name',name,'--network=none','--read-only','--timeout',str(seconds),
            '--ulimit','core=0:0','--stop-timeout','3','--memory','6g','--memory-swap','6g','--cpus','4',
            '--security-opt=label=disable','--unsetenv','LD_PRELOAD',
            '--tmpfs','/tmp:rw,size=512m','--tmpfs','/scratch:rw,size=512m','-w','/scratch',
            '-e','NUMBA_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=1','-e','OMP_NUM_THREADS=2',
            '-e','NUMBA_CACHE_DIR=/jit-cache','-e','PYTHONDONTWRITEBYTECODE=1',
            '-e','PYTHONPATH=/scripts',
            *python_mounts(ENV,base_python),
            '-v',f'{BASE/"jit-cache"}:/jit-cache','-v',f'{output}:/work',
            '-v',f'{source}:/scripts/case.py:ro','-v',f'{REFERENCE}:/scripts/maxwell_reference.py:ro',
            '-v',f'{COMPRESSION}:/scripts/maxwell_hmatrix.py:ro',
            *(['--device','nvidia.com/gpu=all'] if compression else []),
            *(['-v',f'{CUDA_LIBRARY}:/native/libmaxwell_apply.so:ro'] if native else []),
            *(['-v',f'{mfem_bridge.LIBRARY}:/native/libmfem_bridge.so:ro'] if bridge else []),
            *(['-v',f'{FEM_API}:/scripts/maxwell_fem.py:ro'] if physics in ['coupling','pairing','nd2','nd2-coupling','traces','transmission'] else []),
            *(['-v',f'{ND_API}:/scripts/maxwell_nd.py:ro'] if physics in ['nd2','nd2-coupling','transmission'] else []),
            *(['-v',f'{PAIRING_CASE}:/scripts/bempp_pairing.py:ro'] if physics in ['nd2-coupling','traces','transmission'] else []),
            *(['-v',f'{ND_COUPLING_CASE}:/scripts/bempp_nd2_coupling.py:ro'] if physics=='transmission' else []),
            '--entrypoint',str(ENV/'bin/python'),settings['runtime_image'],
            '-u','/scripts/case.py','--level',str(level),'--output','/work',
            *(['--compression'] if compression else []),*(['--native-apply'] if native else []),
            *(['--compression-eta',str(eta)] if physics=='pec' else []),
            *(['--duality',duality] if physics=='nd2-coupling' else []),
            *(['--surface-level',str(surface_level)] if surface_level is not None else []),
            *(['--epsilon-r',str(2.94 if epsilon_r is None else epsilon_r)] if physics=='transmission' else []),
            *(['--reference-only'] if reference_only else []),
            *(['--volume-preserving'] if volume_preserving else [])]
    dev.write(output/'command.json',dict(argv=args,environment=manifest,
                                      physics=physics,duality=duality if physics=='nd2-coupling' else None,
                                      surface_level=(level if surface_level is None else surface_level) if physics in ['nd2-coupling','transmission'] else None,
                                      epsilon_r=(2.94 if epsilon_r is None else epsilon_r) if physics=='transmission' else None,
                                      reference_only=reference_only,
                                      coupling_api_sha256=dev.sha(ND_COUPLING_CASE) if physics=='transmission' else None,
                                      case_sha256=dev.sha(source),reference_sha256=dev.sha(REFERENCE),
                                      compression_sha256=dev.sha(COMPRESSION),
                                      native_cuda=cuda,
                                      mfem_bridge=bridge,fem_api_sha256=dev.sha(FEM_API) if physics in ['coupling','pairing','nd2','nd2-coupling','traces','transmission'] else None,
                                      nd_api_sha256=dev.sha(ND_API) if physics in ['nd2','nd2-coupling','transmission'] else None,
                                      pairing_api_sha256=dev.sha(PAIRING_CASE) if physics in ['nd2-coupling','traces','transmission'] else None,
                                      scope='CPU Maxwell oracle, optional CUDA compressed apply; no antenna promotion'))
    started = time.monotonic()
    result = dict(complete=False,analytic_target_passed=False,level=level)
    try:
        with (output/'stdout.log').open('w') as stdout,(output/'stderr.log').open('w') as stderr:
            process = subprocess.run(args,stdout=stdout,stderr=stderr,timeout=seconds+15)
        state = dev.read_output(['podman','inspect',name])[0]['State']
        dev.write(output/'container-state.json',state)
        result['exit_code'] = process.returncode
        if process.returncode or state['OOMKilled']:
            raise ValueError('Oracle execution failed; inspect stage/log, no automatic retry')
        case = dev.read(output/'case.json')
        result.update(complete=case['execution_passed'],analytic_target_passed=case['analytic_target_passed'])
        if compression:
            result['compression_target_passed'] = case['compression']['quality_passed']
    finally:
        subprocess.run(['podman','rm','--force',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        result['elapsed_seconds'] = time.monotonic()-started
        result['scope'] = 'Execution vs analytic target are separate; no production qualification'
        dev.write(output/'result.json',result)
    print(json.dumps(result,indent=2))
    if not result['complete']: raise ValueError('CPU Maxwell oracle incomplete')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['setup','check','run','build-cuda'])
    parser.add_argument('output',type=Path,nargs='?')
    parser.add_argument('--level',type=int,default=1)
    parser.add_argument('--seconds',type=int,default=120)
    parser.add_argument('--compression',action='store_true',help='Probe exact-near/low-rank far Maxwell and CUDA apply')
    parser.add_argument('--native-apply',action='store_true',help='Compare a cached two-kernel FP64 CUDA apply')
    parser.add_argument('--compression-eta',type=float,default=2.0,help='Geometric admissibility only; fixed SVD/quality gates')
    parser.add_argument('--physics',choices=['pec','dielectric','coupling','pairing','nd2','nd2-coupling','traces','transmission'],default='pec')
    parser.add_argument('--volume-preserving',action='store_true',help='Explicit dielectric sphere geometry variant, no field fit')
    parser.add_argument('--duality',choices=['electric','magnetic'],default='electric')
    parser.add_argument('--surface-level',type=int,choices=[1,2,3,4])
    parser.add_argument('--epsilon-r',type=float,choices=[1.,2.94])
    parser.add_argument('--reference-only',action='store_true')
    args = parser.parse_args()
    if args.action=='setup': setup()
    elif args.action=='build-cuda': build_cuda()
    elif args.action=='check': print(json.dumps(verified(),indent=2))
    elif args.output is None: parser.error('run requires new output directory')
    else: run(args.output,args.level,args.seconds,args.compression,args.native_apply,args.compression_eta,args.physics,args.volume_preserving,args.duality,args.surface_level,args.epsilon_r,args.reference_only)
