#!/usr/bin/env python3
"""Build one pinned libCEED Q-workspace object and reuse the other cached objects."""
import fcntl
import hashlib
import shlex
import subprocess
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dev

SOURCE = '/tmp/root/spack-stage/spack-stage-libceed-develop-2afuek6b57ch2y3u3apevwyaitn3ap35/spack-src'
REVISION = 'cbd49027b0ae891f0c8efd9d9cf05bc82385a388'
SOURCE_SHA = 'd5349256bd72bb8c077ad4e4f3d907f099100434baf9383f115f5d15eda4b18b'
OUTPUT = dev.ROOT / 'build/ceed-qpool'
HERE = Path(__file__).resolve().parent


def generate(original):
    if hashlib.sha256(original.encode()).hexdigest() != SOURCE_SHA:
        raise ValueError('Pinned libCEED source changed; refuse ABI-dependent prototype')
    start = original.index('static int CeedOperatorApplyAdd_Cuda(')
    end = original.index('// Create operator AtPoints', start)  # Contains other functions too.
    setup = '  // Work vector\n  CeedCallBackend(CeedGetWorkVector(ceed, impl->max_active_e_vec_len, &active_e_vec));'
    index = original.index(setup, start, end)
    borrow = '''  // Bounded, in-memory prototype. Conservatively synchronize every stream;
  // this is a memory/correctness experiment, not a claimed speed optimization.
  if (atomic_flag_test_and_set(&palace_pool_in_use))
    return CeedError(ceed, CEED_ERROR_BACKEND, "Q-pool does not support overlapping applications");
  CeedCallCuda(ceed, cudaDeviceSynchronize());
  CeedVector saved_q_in[CEED_FIELD_MAX] = {0}, saved_q_out[CEED_FIELD_MAX] = {0};
  CeedCallBackend(PalaceQPoolBorrow(ceed, op_input_fields, qf_input_fields,
                                   num_input_fields, impl->q_vecs_in, saved_q_in));
  CeedCallBackend(PalaceQPoolBorrow(ceed, op_output_fields, qf_output_fields,
                                   num_output_fields, impl->q_vecs_out, saved_q_out));
  atomic_fetch_add(&palace_pool_calls, 1);

'''
    original = original[:index] + borrow + original[index:]
    marker = '  // Return work vector\n  CeedCallBackend(CeedRestoreWorkVector(ceed, &active_e_vec));'
    index = original.index(marker, start)
    restore = '''  // Finish asynchronous CUDA/MAGMA users before returning shared storage.
  CeedCallCuda(ceed, cudaDeviceSynchronize());
  CeedCallBackend(PalaceQPoolReturn(ceed, num_input_fields, impl->q_vecs_in, saved_q_in));
  CeedCallBackend(PalaceQPoolReturn(ceed, num_output_fields, impl->q_vecs_out, saved_q_out));
  atomic_flag_clear(&palace_pool_in_use);

'''
    original = original[:index] + restore + original[index:]
    include = '#include "ceed-cuda-ref.h"'
    if original.count(include) != 1:
        raise ValueError('Pinned include site changed')
    original = original.replace(include, include + '\n' + (HERE/'ceed_qpool.h').read_text())
    return original


def _build():
    settings = dev.read(dev.SETTINGS)
    native = dev.verified_build()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    library = OUTPUT/'libceed_qpool.so'
    recipe = {p.name: dev.sha(p) for p in HERE.glob('ceed_qpool*') if p.is_file()}
    previous = dev.read(OUTPUT/'manifest.json') if (OUTPUT/'manifest.json').exists() else {}
    if (previous.get('recipe') == recipe and previous.get('builder') == native['builder_image_id']
            and previous.get('runtime') == native['runtime_base_id']
            and library.exists() and previous.get('library_sha256') == dev.sha(library)
            and (OUTPUT/'probe').exists() and previous.get('probe_sha256') == dev.sha(OUTPUT/'probe')):
        print('Q-pool prototype unchanged: cached library retained')
        return
    started = time.monotonic()
    name = dev.builder(settings)
    try:
        revision = dev.capture(['podman', 'exec', name, 'git', '-C', SOURCE, 'rev-parse', 'HEAD'])
        if revision != REVISION:
            raise ValueError('Wrong libCEED source revision')
        source = dev.capture(['podman', 'exec', name, 'cat', SOURCE+'/backends/cuda-ref/ceed-cuda-ref-operator.c']) + '\n'
        generated = OUTPUT/'operator.c'
        generated.write_text(generate(source))
        work = '/opt/palace-ceed-qpool'
        exists = subprocess.run(['podman', 'exec', name, 'test', '-d', work]).returncode == 0
        if not exists:
            dev.command(['podman', 'exec', name, 'cp', '-a', SOURCE, work])
        # Only the one modified host C object is recompiled. Reuse every other
        # cached dependency object and the exact original link command.
        log = dev.capture(['podman', 'exec', name, 'cat', str(Path(SOURCE).parent/'spack-build-out.txt')])
        compile_line = next(line for line in log.splitlines()
                            if ' -c -o build/backends/cuda-ref/ceed-cuda-ref-operator.o ' in line)
        link_line = next(line for line in log.splitlines()
                         if ' -shared ' in line and ' -o build/libceed.so ' in line)
        compile_argv = shlex.split(compile_line)
        compile_argv = [arg.replace(SOURCE, work) for arg in compile_argv]
        # Spack wrappers are not needed to recompile a C-only backend file.
        compile_argv[0:1] = ['ccache', 'cc']
        compile_argv += ['-I/usr/local/cuda/include']
        link_argv = shlex.split(link_line)
        link_argv[0] = 'c++'
        dev.command(['podman', 'cp', generated, name+':'+work+'/backends/cuda-ref/ceed-cuda-ref-operator.c'])
        with (OUTPUT/'build.log').open('w') as build_log:
            for args in [compile_argv, link_argv]:
                dev.command(['podman', 'exec', '-w', work, name, *args], stdout=build_log,
                            stderr=subprocess.STDOUT, timeout=120)
        dev.command(['podman', 'cp', name+':'+work+'/build/libceed.so', library])
        probe_args = ['ccache', 'cc', '-std=c11', '-O2', '-I/opt/view/include',
                      '/src/palace/tools/experiments/ceed_qpool_probe.c',
                      '-L/opt/view/lib', '-lceed', '-lm', '-L/usr/local/cuda/lib64/stubs', '-lcuda',
                      '-Wl,-rpath,/opt/view/lib', '-o', '/tmp/palace-qpool-probe']
        with (OUTPUT/'probe-build.log').open('w') as probe_log:
            dev.command(['podman', 'exec', name, *probe_args], stdout=probe_log,
                        stderr=subprocess.STDOUT, timeout=60)
        dev.command(['podman', 'cp', name+':/tmp/palace-qpool-probe', OUTPUT/'probe'])
        runtime_path = dev.capture(['podman', 'exec', name, 'readlink', '-f', '/opt/view/lib/libceed.so'])
        dev.write(OUTPUT/'manifest.json', {'schema': 1, 'recipe': recipe, 'source_revision': revision,
                  'source_sha256': SOURCE_SHA, 'generated_sha256': dev.sha(generated),
                  'library_sha256': dev.sha(library), 'probe_sha256': dev.sha(OUTPUT/'probe'), 'builder': native['builder_image_id'],
                  'runtime': native['runtime_base_id'], 'compile_argv': compile_argv,
                  'link_argv': link_argv, 'runtime_library_path': runtime_path,
                  'seconds': time.monotonic()-started, 'qualified': False,
                  'scope': 'Experimental active-Q pool, conservative device synchronization; no disk working storage'})
        print(f'Q-pool prototype built in {time.monotonic()-started:.2f}s')
    finally:
        subprocess.run(['podman', 'stop', '--time', '3', name], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)


def build():
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _build()


if __name__ == '__main__':
    build()
