#!/usr/bin/env python3
"""Bounded cuDSS representation/mixed probes; no FEM dependency rebuild."""
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


def variant_paths(variant):
    if variant == 'reference':
        return OUTPUT, SOURCE
    if variant == 'mixed':
        return dev.ROOT/'build/mixed-coarse-probe', dev.ROOT/'tools/tests/mixed_coarse_probe.cu'
    raise ValueError('Unknown coarse probe variant')


def recipe(variant='reference'):
    build_dir, source = variant_paths(variant)
    settings = dev.read(dev.SETTINGS)
    return dict(source=dev.sha(source), script=dev.sha(__file__), variant=variant,
                support_source=dev.sha(SOURCE) if variant == 'mixed' else None,
                cuda_helpers=dev.sha(dev.ROOT/'palace/linalg/mixedcoarse.hpp') if variant == 'mixed' else None,
                architecture=settings['architecture'], builder=dev.image_id(settings['builder_image']),
                runtime=dev.image_id(settings['runtime_image']))

def build(variant='reference'):
    build_dir, source = variant_paths(variant)
    build_dir.mkdir(parents=True, exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = recipe(variant)
        manifest = build_dir/'manifest.json'
        binary = build_dir/'probe'
        previous = dev.read(manifest) if manifest.exists() else {}
        if (previous.get('recipe') == current and binary.exists()
                and previous.get('binary_sha256') == dev.sha(binary)):
            print('Probe unchanged: cached binary retained')
            return
        settings = dev.read(dev.SETTINGS)
        started = time.monotonic()
        name = dev.builder(settings)
        try:
            with (build_dir/'build.log').open('w') as log:
                dev.command(['podman', 'exec', name, '/usr/local/cuda/bin/nvcc', '-std=c++17',
                             '-arch=sm_'+settings['architecture'], '/src/palace/'+str(source.relative_to(dev.ROOT)),
                             '-I/opt/cudss/include', '-L/opt/cudss/lib', '-lcudss', '--cudart=shared',
                             '-o', '/tmp/palace-complex-coarse-probe'], stdout=log, stderr=subprocess.STDOUT,
                            timeout=120)
                dev.command(['podman', 'cp', name+':/tmp/palace-complex-coarse-probe', binary], stdout=log)
            if recipe(variant) != current:
                raise ValueError('Probe inputs changed during build')
            dev.write(manifest, dict(recipe=current, binary_sha256=dev.sha(binary),
                                     build_seconds=time.monotonic()-started))
        finally:
            subprocess.run(['podman', 'stop', '--time', '3', name], stdout=subprocess.DEVNULL, check=True)
        print(json.dumps(dev.read(manifest), indent=2))


def parse_probe(text, hybrid_mib=None):
    validate_hybrid_mib(hybrid_mib)
    rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
    if [r.get('mode') for r in rows] != ['native_complex_fp64', 'real_block_fp64']:
        raise ValueError('Missing or duplicated representation results')
    for row in rows:
        if (row.get('passed') is not True or row.get('nrhs') != 2 or row.get('updates') != 2
                or row.get('n') != 512 or row.get('cudss_live_after_destroy') != 0
                or row.get('dimension') != (512 if row['mode']=='native_complex_fp64' else 1024)):
            raise ValueError('Unexpected case coverage or cleanup')
        if row.get('hybrid_limit_bytes', 0) != (hybrid_mib or 0)*1024**2:
            raise ValueError('Requested memory mode/budget was not applied')
        if hybrid_mib is not None:
            for key in ['minimum_device_bytes', 'estimated_host_bytes']:
                value = row.get(key)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    raise ValueError('Missing or invalid hybrid memory query')
            if row['minimum_device_bytes'] > row['hybrid_limit_bytes']:
                raise ValueError('Hybrid minimum exceeds device budget')
        for key in ['relative_solution', 'relative_rhs_residual']:
            value = row.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1e-10:
                raise ValueError('Probe accuracy failed')
        for key in ['analysis_s', 'factor_s', 'solve_s', 'cudss_peak_bytes']:
            value = row.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid cost counter')
    return rows


def parse_mixed_probe(text):
    markers = [line for line in text.splitlines() if line.startswith('PALACE_MIXED_COARSE_HELPERS:')]
    if markers != ['PALACE_MIXED_COARSE_HELPERS: cases=4 passed=1']:
        raise ValueError('Missing or failed CUDA helper boundary/value coverage')
    rows = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
    expected = [(case, mode) for case in ['regular', 'ill_scaled']
                for mode in ['fp64', 'raw_fp32', 'scaled_refined_fp32']]
    if [(r.get('case'), r.get('mode')) for r in rows] != expected:
        raise ValueError('Mixed probe coverage differs from six frozen cases')
    for row in rows:
        refined = row['mode'] == 'scaled_refined_fp32'
        negative_control = row['case'] == 'ill_scaled' and row['mode'] == 'raw_fp32'
        if (row.get('n') != 512 or row.get('nrhs') != 2 or row.get('updates') != 2
                or row.get('corrections') != (2 if refined else 0)
                or row.get('factor_dtype') != ('complex_fp64' if row['mode'] == 'fp64' else 'complex_fp32')
                or row.get('residual_dtype') != 'complex_fp64'
                or row.get('correction_backend') != ('host_fp64' if row['mode']=='fp64' else 'cuda_fp64')
                or row.get('fault_rejected') is not True
                or row.get('cudss_live_after_destroy') != 0
                or not isinstance(row.get('passed'), bool)):
            raise ValueError('Mixed probe dtype/iteration/cleanup/fault coverage failed')
        for key in ['relative_solution', 'relative_rhs_residual', 'componentwise_backward_error',
                    'scale_min', 'scale_max', 'cudss_peak_bytes', 'analysis_s', 'factor_s',
                    'solve_s', 'correction_s']:
            value = row.get(key)
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or not math.isfinite(value) or value < 0):
                raise ValueError('Mixed probe nonfinite or invalid numeric result')
        tolerance = 1e-2 if row['mode'] == 'raw_fp32' else 1e-10
        passed_quality = all(row[k] <= tolerance for k in ['relative_solution', 'relative_rhs_residual', 'componentwise_backward_error'])
        if row['passed'] is not passed_quality or (not negative_control and not passed_quality):
            raise ValueError('Mixed probe original-equation quality failed')
        if not 0 < row['scale_min'] <= row['scale_max']:
            raise ValueError('Invalid scaling range')
        if refined and row['case'] == 'ill_scaled' and row['scale_max']/row['scale_min'] < 1e5:
            raise ValueError('Ill-scaled case was not equilibrated')
        if not refined and (row['scale_min'], row['scale_max']) != (1, 1):
            raise ValueError('Control case must not use equilibration')
    return rows


def validate_hybrid_mib(value):
    if value is not None and (not isinstance(value, int) or isinstance(value, bool) or not 256 <= value <= 16384):
        raise ValueError('Hybrid MiB must be an integer from 256 to 16384')


def run(output, hybrid_mib=None, variant='reference'):
    build_dir, source = variant_paths(variant)
    if variant == 'mixed' and hybrid_mib is not None:
        raise ValueError('Mixed probe does not combine hybrid memory')
    validate_hybrid_mib(hybrid_mib)
    dev.require_host_memory()
    manifest = dev.read(build_dir/'manifest.json')
    if manifest['recipe'] != recipe(variant) or manifest['binary_sha256'] != dev.sha(build_dir/'probe'):
        raise ValueError('Probe stale; build before running')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    settings = dev.read(dev.SETTINGS)
    name = 'palace-probe-'+hashlib.sha256(str(output).encode()).hexdigest()[:12]
    args = ['podman', 'run', '--name', name, '--network=none', '--timeout', '60',
            '--ulimit', 'core=0:0',
            '--stop-timeout', '3', '--memory', '2g', '--memory-swap', '2g', '--cpus', '2',
            '--device', 'nvidia.com/gpu=all', '--security-opt=label=disable', '--unsetenv', 'LD_PRELOAD',
            '-v', f'{build_dir / "probe"}:/probe:ro', '--entrypoint', '/probe', settings['runtime_image']]
    # Isolated runtime: never inherit a memory policy from the container image.
    environment = ['--unsetenv', 'PALACE_PROBE_HYBRID_MIB']
    if hybrid_mib is not None:
        environment += ['-e', 'PALACE_PROBE_HYBRID_MIB='+str(hybrid_mib)]
    args[2:2] = environment
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
        result['cases'] = (parse_mixed_probe((output/'stdout.log').read_text()) if variant == 'mixed'
                           else parse_probe((output/'stdout.log').read_text(), hybrid_mib))
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
    parser.add_argument('--hybrid-mib', type=int, help='Explicit cuDSS hybrid device budget; inputs remain managed, factor device allocations are not UVM')
    parser.add_argument('--variant', choices=['reference', 'mixed'], default='reference')
    args = parser.parse_args()
    if args.action == 'build':
        build(args.variant)
    elif args.output is None:
        parser.error('run requires a new artifact directory')
    else:
        run(args.output, args.hybrid_mib, args.variant)
