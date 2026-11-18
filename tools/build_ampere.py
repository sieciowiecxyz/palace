#!/usr/bin/env python3
"""Build the frozen optimized M7 source for A100 without touching SM120 caches.

No GPU access, network, tests, publication or rental. Two CPUs, 6 GiB, no swap.
The retained SM80 dependency builder is required locally.
"""
from __future__ import annotations

import argparse
import difflib
import fcntl
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'artifacts/m7-sm120-bundle-r3-20261022'
BUILDER = 'sha256:38b0cdbcf7fd5861b90e1e90be091a45959e24216f001b0f98dd4143f2e53777'
RUNTIME = 'sha256:695d3dfc58c075f49d9e7e4206243bfb25b9b668a73be4ca1e57d95aed6088af'
CCACHE_IMAGE = 'sha256:296248155e55ca84f1e362d6a2926682f78c4f0290ab26158a265300244fb55d'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def run(args, log=None, timeout=1800):
    return subprocess.run(list(map(str, args)), check=True, text=True,
                          stdout=log, stderr=subprocess.STDOUT if log else None,
                          timeout=timeout)


def capture(args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/m7-sm80-a100-20261025')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with (output/'build.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        build(output)


def build(output):
    started = time.monotonic()
    bundle = output/'bundle'
    native = bundle/'build/sm80/native'
    native.mkdir(parents=True, exist_ok=True)
    original = json.loads((SOURCE/'build/sm120/manifest.json').read_text())
    source_files = {str(p.relative_to(SOURCE)): digest(p)
                    for tree in ('palace', 'cmake', 'tools/adapter')
                    for p in (SOURCE/tree).rglob('*') if p.is_file()}
    source_files['CMakeLists.txt'] = digest(SOURCE/'CMakeLists.txt')
    source_sha = hashlib.sha256()
    for name, checksum in sorted(source_files.items()):
        source_sha.update(name.encode() + b'\0' + bytes.fromhex(checksum))
    if source_sha.hexdigest() != original['source_sha256']:
        raise ValueError('Pinned source inputs differ from validated M7 manifest')
    committed_archive = subprocess.check_output(['git','-C',str(ROOT),'archive',
        original['git_revision'],'CMakeLists.txt','palace','cmake','tools/adapter'])
    committed = {}
    with tarfile.open(fileobj=io.BytesIO(committed_archive)) as files:
        for member in files:
            if member.isfile():
                committed[member.name] = files.extractfile(member).read()
    changed = []
    patch = []
    for relative in sorted(set(committed) | set(source_files)):
        before = committed.get(relative,b'')
        after = (SOURCE/relative).read_bytes() if relative in source_files else b''
        if before != after:
            changed.append(relative)
            patch.extend(difflib.unified_diff(before.decode().splitlines(keepends=True),
                after.decode().splitlines(keepends=True),fromfile='a/'+relative,tofile='b/'+relative))
    (output/'source-from-commit.patch').write_text(''.join(patch))
    for folder in ('palace', 'cmake', 'tools', 'examples'):
        shutil.copytree(SOURCE/folder, bundle/folder, dirs_exist_ok=True)
    # The exported M7 bundle omitted these configure/install inputs. Recover
    # their exact committed versions, not files from the changing working tree.
    archive = subprocess.check_output(['git', '-C', str(ROOT), 'archive',
                                      original['git_revision'], 'scripts', 'test/unit'])
    with tarfile.open(fileobj=io.BytesIO(archive)) as files:
        files.extractall(bundle, filter='data')
    supplemental = {str(p.relative_to(bundle)):digest(p)
                    for tree in ('scripts', 'test/unit')
                    for p in (bundle/tree).rglob('*') if p.is_file()}
    for name in ('CMakeLists.txt', 'LICENSE', 'NOTICE', 'THIRD-PARTY-LICENSES', 'THIRD-PARTY-NOTICES'):
        shutil.copy2(SOURCE/name, bundle/name)
    # Only launcher bookkeeping changes. Compiler inputs remain byte-identical.
    dev = bundle/'tools/dev.py'
    dev.write_text(dev.read_text().replace("BUILD = ROOT / 'build/sm120'", "BUILD = ROOT / 'build/sm80'")
        .replace("'libcudss_fp32.so': '/opt/precision/libcudss_fp32.so'}",
                 "'libcudss_fp32.so': '/opt/precision/libcudss_fp32.so',\n"
                 "                'libceed.so': '/opt/precision/libceed.so'}"))
    settings = json.loads((SOURCE/'tools/runtime.json').read_text())
    settings.update(profile='sm80-a100', architecture='80', builder_image=BUILDER,
                    builder_tag='localhost/palace:cudss-sm80-a100-builder', runtime_image=RUNTIME)
    settings.pop('qualified_image', None)
    write(bundle/'tools/runtime.json', settings)
    name = 'palace-m7-sm80-' + hashlib.sha256(str(output).encode()).hexdigest()[:12]
    cache = ROOT/'.cache/ccache-sm80'
    cache.mkdir(parents=True, exist_ok=True)
    created = subprocess.run(['podman', 'container', 'exists', name]).returncode != 0
    if created:
        run(['podman', 'create', '--name', name, '--network=none', '--memory=6g',
             '--memory-swap=6g', '--cpus=2', '--security-opt=label=disable',
             '-v', f'{bundle}:/src/palace:ro', '-v', f'{cache}:/cache/ccache',
             '-e', 'CCACHE_DIR=/cache/ccache', '-e', 'CCACHE_BASEDIR=/src/palace',
             '-e', 'CCACHE_COMPILERCHECK=content', '-e', 'CCACHE_MAXSIZE=20G',
             '--entrypoint', 'sleep', BUILDER, 'infinity'])
    run(['podman', 'start', name])
    write(output/'status.json', {'status':'building', 'container':name,
                                'source_sha256':source_sha.hexdigest(), 'gpu_tests':'NOT RUN'})
    try:
        # Offline ccache installation from our existing dependency-complete builder.
        # No apt, registry access, or changes to either original builder.
        ccache_holder = name + '-ccache'
        if subprocess.run(['podman', 'container', 'exists', ccache_holder]).returncode:
            run(['podman', 'create', '--name', ccache_holder, '--network=none',
                 '--entrypoint', '/bin/true', CCACHE_IMAGE])
        for source, target in (('/usr/bin/ccache', '/usr/local/bin/ccache'),
                               ('/lib/x86_64-linux-gnu/libhiredis.so.1.1.0', '/lib/x86_64-linux-gnu/libhiredis.so.1.1.0')):
            local = output/Path(source).name
            run(['podman', 'cp', f'{ccache_holder}:{source}', local])
            run(['podman', 'cp', local, f'{name}:{target}'])
        run(['podman', 'rm', ccache_holder])
        # Old SM80 libCEED used a host-native CPU target. Repair that one small
        # retained dependency with x86-64-v3; do not rebuild MFEM/HYPRE/MAGMA.
        repair = ROOT.parent.parent/'python/anteny/infra/palace/containers/rebuild_libceed.py'
        shutil.copy2(repair, output/'rebuild_libceed.py')
        run(['podman', 'cp', output/'rebuild_libceed.py', f'{name}:/tmp/rebuild_libceed.py'])
        if created or not (output/'libceed-repaired.json').exists():
            with (output/'libceed-build.log').open('w') as log:
                run(['podman', 'exec', name, 'bash', '-lc',
                     '. /opt/spack/share/spack/setup-env.sh; '
                     'spack -e /opt/palace-env-a100-sm80-cudss build-env libceed -- '
                     'spack -e /opt/palace-env-a100-sm80-cudss python /tmp/rebuild_libceed.py '
                     '/opt/palace-env-a100-sm80-cudss 2'], log)
            write(output/'libceed-repaired.json', {'script_sha256':digest(repair), 'cpu':'x86-64-v3'})
        configure = ['cmake', '-S', '/src/palace/palace', '-B', '/opt/palace-cudss-build',
                     '-DCMAKE_CUDA_ARCHITECTURES=80', '-DCMAKE_BUILD_TYPE=Release',
                     '-DCMAKE_INSTALL_PREFIX=/opt/palace-cudss',
                     '-DCMAKE_CXX_FLAGS=-march=x86-64-v3',
                     '-DCMAKE_CUDA_FLAGS=-Xcompiler=-march=x86-64-v3',
                     '-DCMAKE_CXX_COMPILER_LAUNCHER=ccache', '-DCMAKE_CUDA_COMPILER_LAUNCHER=ccache']
        if (output/'build.log').exists():
            shutil.copy2(output/'build.log', output/f'configure-prior-{time.time_ns()}.log')
        with (output/'build.log').open('w') as log:
            run(['podman', 'exec', name, *configure], log, 120)
            run(['podman', 'exec', name, 'cmake', '--build', '/opt/palace-cudss-build', '--parallel', '2'], log)
            run(['podman', 'exec', name, '/usr/local/cuda/bin/nvcc', '-std=c++17',
                 '-arch=sm_80', '-shared', '-Xcompiler=-fPIC,-march=x86-64-v3',
                 '/src/palace/tools/adapter/cudss_fp32.cu', '/src/palace/tools/adapter/cuda_memory.cpp',
                 '/src/palace/tools/adapter/pc_basis.cu', '/src/palace/tools/adapter/ceed_audit.cpp',
                 '-I/opt/cudss/include', '-I/opt/view/include', '--cudart=shared', '-ldl',
                 '-o', '/tmp/palace-adapter.so'], log, 300)
            run(['podman', 'exec', name, 'cmake', '--install', '/opt/palace-cudss-build'], log,120)
        for filename, directory in (('libpalace.so','lib'),('palace-x86_64.bin','bin')):
            # Install rewrites RPATH, so hash/export the bytes actually shipped.
            run(['podman', 'cp', f'{name}:/opt/palace-cudss/{directory}/{filename}', native/filename])
        run(['podman', 'cp', f'{name}:/tmp/palace-adapter.so', native/'libcudss_fp32.so'])
        # Bundle the repaired libCEED with the runtime, not the host CPU-specific one.
        libceed_real = capture(['podman','exec',name,'readlink','-f','/opt/view/lib/libceed.so'])
        run(['podman', 'cp', f'{name}:{libceed_real}', native/'libceed.so'])
        manifest = dict(original)
        manifest.update(source_sha256=source_sha.hexdigest(), builder_image_id=BUILDER.removeprefix('sha256:'),
                        runtime_base_id=RUNTIME.removeprefix('sha256:'),
                        settings_sha256=digest(bundle/'tools/runtime.json'),
                        native={p.name:digest(p) for p in native.iterdir() if p.is_file()},
                        elapsed_seconds=round(time.monotonic()-started,3),
                        ccache=capture(['podman','exec',name,'ccache','--show-stats']), numerically_validated=False)
        libceed_hash = manifest['native']['libceed.so']
        write(bundle/'build/sm80/manifest.json', manifest)
        context = output/'runtime-context'
        shutil.copytree(native, context/'native', dirs_exist_ok=True)
        (context/'install').mkdir(parents=True, exist_ok=True)
        run(['podman','cp',f'{name}:/opt/palace-cudss/.',context/'install'])
        write(context/'build-manifest.json', manifest)
        (context/'Containerfile').write_text('ARG BASE_IMAGE\nFROM ${BASE_IMAGE}\n'
            'COPY install/ /opt/palace-cudss/\n'
            'COPY native/libcudss_fp32.so /opt/precision/libcudss_fp32.so\n'
            'COPY native/libceed.so /opt/precision/libceed.so\n'
            'COPY build-manifest.json /opt/palace-local/build-manifest.json\n'
            'ENV LD_LIBRARY_PATH=/opt/palace-cudss/lib:/opt/precision:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib:/usr/local/cuda/lib64\n'
            'ENTRYPOINT ["/opt/palace-cudss/bin/palace-x86_64.bin"]\n')
        tag = 'localhost/palace:m7-sm80-a100-20261025'
        with (output/'runtime-build.log').open('w') as log:
            run(['podman','build','--pull=never','--network=none','--build-arg','BASE_IMAGE='+RUNTIME,
                 '-t',tag,'-f',context/'Containerfile',context], log, 180)
        image = capture(['podman','image','inspect',tag,'--format','{{.Id}}'])
        write(bundle/'build/sm80/runtime-image.json', {'tag':tag,'image_id':image,
              'build_manifest_sha256':digest(bundle/'build/sm80/manifest.json'),'numerically_validated':False})
        with (output/'static-audit.log').open('w') as log:
            for lib in ('/opt/palace-cudss-build/libpalace.so','/tmp/palace-adapter.so',
                        '/opt/view/lib/libmfem.so','/opt/view/lib/libHYPRE.so','/opt/view/lib/libmagma.so'):
                log.write('\n'+lib+'\n'); log.flush()
                run(['podman','exec',name,'/usr/local/cuda/bin/cuobjdump','--list-elf',lib],log,120)
            run(['podman','run','--rm','--network=none','--memory=6g','--memory-swap=6g','--cpus=2',
                 '--entrypoint','bash',image,'-lc',
                 'ldd /opt/palace-cudss/bin/palace-x86_64.bin; ldd /opt/precision/libcudss_fp32.so; '
                 'ldd /opt/precision/libceed.so'], log,60)
        static_log = (output/'static-audit.log').read_text()
        unexpected = [line for line in static_log.splitlines() if 'not found' in line
                      and not any(driver in line for driver in ('libcuda.so', 'libnvidia-'))]
        if unexpected:
            raise ValueError('Unresolved runtime dependencies: ' + '; '.join(unexpected))
        for lib in ('/opt/palace-cudss-build/libpalace.so','/tmp/palace-adapter.so',
                    '/opt/view/lib/libmfem.so','/opt/view/lib/libHYPRE.so','/opt/view/lib/libmagma.so'):
            listing = capture(['podman','exec',name,'/usr/local/cuda/bin/cuobjdump','--list-elf',lib])
            if 'sm_80.cubin' not in listing:
                raise ValueError('No SM80 cubin in '+lib)
        # Verify payload hashes and provenance without running the solver.
        runtime_paths = {'libpalace.so':'/opt/palace-cudss/lib/libpalace.so',
                         'palace-x86_64.bin':'/opt/palace-cudss/bin/palace-x86_64.bin',
                         'libcudss_fp32.so':'/opt/precision/libcudss_fp32.so',
                         'libceed.so':'/opt/precision/libceed.so'}
        for filename, inside in runtime_paths.items():
            checksum = capture(['podman','run','--rm','--network=none','--entrypoint',
                                'sha256sum',image,inside]).split()[0]
            if checksum != digest(native/filename):
                raise ValueError('Runtime bytes differ: '+filename)
        if json.loads(capture(['podman','run','--rm','--network=none','--entrypoint',
                               'cat',image,'/opt/palace-local/build-manifest.json'])) != manifest:
            raise ValueError('Runtime manifest differs')
        write(output/'provenance.json', {'source_bundle':str(SOURCE),'source_files':source_files,
              'supplemental_committed_inputs':supplemental,
              'source_changed_from_commit':changed,
              'source_patch_sha256':digest(output/'source-from-commit.patch'),
              'original_manifest':original,'configure_argv':configure,'architecture':'sm_80',
              'builder':BUILDER,'runtime_base':RUNTIME,'image':image,'libceed_sha256':libceed_hash,
              'ccache_image':CCACHE_IMAGE,'ccache_sha256':digest(output/'ccache'),
              'build_script_sha256':digest(__file__),'limits':{'cpus':2,'ram_gib':6,'swap':False},
              'qualification':'Build/static audit only. No A100 GPU execution or RF validation.'})
        write(output/'status.json', {'status':'built','image':image,'tag':tag,'container':name,
                                    'elapsed_seconds':round(time.monotonic()-started,3),'gpu_tests':'NOT RUN'})
        print(image)
    except Exception as error:
        write(output/'status.json', {'status':'failed','error':str(error),'container':name,'gpu_tests':'NOT RUN'})
        raise
    finally:
        run(['podman','stop','--time','0',name],timeout=30)


if __name__ == '__main__':
    main()
