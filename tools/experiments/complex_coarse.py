#!/usr/bin/env python3
"""Bounded FP64 cuDSS representation probe; no FEM changes or dependency rebuild."""
import argparse
import fcntl
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dev

OUTPUT = dev.ROOT/'build/complex-coarse-probe'
SOURCE = dev.ROOT/'tools/tests/complex_coarse_probe.cu'


def recipe():
    settings = dev.read(dev.SETTINGS)
    return dict(source=dev.sha(SOURCE), script=dev.sha(__file__),
                architecture=settings['architecture'], builder=dev.image_id(settings['builder_image']),
                runtime=dev.image_id(settings['runtime_image']))


def build():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = recipe()
        manifest = OUTPUT/'manifest.json'
        binary = OUTPUT/'probe'
        previous = dev.read(manifest) if manifest.exists() else {}
        if (previous.get('recipe') == current and binary.exists()
                and previous.get('binary_sha256') == dev.sha(binary)):
            print('Probe unchanged: cached binary retained')
            return
        settings = dev.read(dev.SETTINGS)
        started = time.monotonic()
        name = dev.builder(settings)
        try:
            with (OUTPUT/'build.log').open('w') as log:
                dev.command(['podman', 'exec', name, '/usr/local/cuda/bin/nvcc', '-std=c++17',
                             '-arch=sm_'+settings['architecture'], '/src/palace/'+str(SOURCE.relative_to(dev.ROOT)),
                             '-I/opt/cudss/include', '-L/opt/cudss/lib', '-lcudss', '--cudart=shared',
                             '-o', '/tmp/palace-complex-coarse-probe'], stdout=log, stderr=subprocess.STDOUT,
                            timeout=120)
                dev.command(['podman', 'cp', name+':/tmp/palace-complex-coarse-probe', binary], stdout=log)
            if recipe() != current:
                raise ValueError('Probe inputs changed during build')
            dev.write(manifest, dict(recipe=current, binary_sha256=dev.sha(binary),
                                     build_seconds=time.monotonic()-started))
        finally:
            subprocess.run(['podman', 'stop', '--time', '3', name], stdout=subprocess.DEVNULL, check=True)
        print(json.dumps(dev.read(manifest), indent=2))


def parse_probe(text):
    rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
    if [r.get('mode') for r in rows] != ['native_complex_fp64', 'real_block_fp64']:
        raise ValueError('Missing or duplicated representation results')
    for row in rows:
        if (row.get('passed') is not True or row.get('nrhs') != 2 or row.get('updates') != 2
                or row.get('n') != 512 or row.get('cudss_live_after_destroy') != 0
                or row.get('dimension') != (512 if row['mode']=='native_complex_fp64' else 1024)):
            raise ValueError('Unexpected case coverage or cleanup')
        for key in ['relative_solution', 'relative_rhs_residual']:
            value = row.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1e-10:
                raise ValueError('Probe accuracy failed')
        for key in ['analysis_s', 'factor_s', 'solve_s', 'cudss_peak_bytes']:
            value = row.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid cost counter')
    return rows


def run(output):
    dev.require_host_memory()
    manifest = dev.read(OUTPUT/'manifest.json')
    if manifest['recipe'] != recipe() or manifest['binary_sha256'] != dev.sha(OUTPUT/'probe'):
        raise ValueError('Probe stale; build before running')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    settings = dev.read(dev.SETTINGS)
    name = 'palace-probe-'+hashlib.sha256(str(output).encode()).hexdigest()[:12]
    args = ['podman', 'run', '--name', name, '--network=none', '--timeout', '60',
            '--ulimit', 'core=0:0',
            '--stop-timeout', '3', '--memory', '2g', '--memory-swap', '2g', '--cpus', '2',
            '--device', 'nvidia.com/gpu=all', '--security-opt=label=disable', '--unsetenv', 'LD_PRELOAD',
            '-v', f'{OUTPUT / "probe"}:/probe:ro', '--entrypoint', '/probe', settings['runtime_image']]
    dev.write(output/'command.json', {'argv': args, 'build': manifest})
    started = time.monotonic()
    result = {'complete': False, 'scope': 'Manufactured API/filter only; not antenna accuracy or speedup'}
    try:
        with (output/'stdout.log').open('w') as stdout, (output/'stderr.log').open('w') as stderr:
            process = subprocess.run(args, stdout=stdout, stderr=stderr, timeout=75)
        result['exit_code'] = process.returncode
        state = dev.read_output(['podman', 'inspect', name])[0]['State']
        dev.write(output/'container-state.json', state)
        if process.returncode or state['OOMKilled']:
            raise ValueError('Probe execution failed')
        result['cases'] = parse_probe((output/'stdout.log').read_text())
        result['complete'] = True
    finally:
        subprocess.run(['podman', 'rm', '--force', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result['elapsed_seconds'] = time.monotonic()-started
        dev.write(output/'result.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'run'])
    parser.add_argument('output', type=Path, nargs='?')
    args = parser.parse_args()
    if args.action == 'build':
        build()
    elif args.output is None:
        parser.error('run requires a new artifact directory')
    else:
        run(args.output)
