#!/usr/bin/env python3
"""Incremental local Palace builds and bounded medium fixtures; Python stdlib only."""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import signal
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build/sm120'
SETTINGS = ROOT / 'tools/runtime.json'
CASES = ['coax-tiny', 'coax-medium', 'tshaped-medium']
INTERRUPTED_SIGNAL = None


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def command(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def capture(args):
    return subprocess.check_output([str(x) for x in args], text=True).strip()


def combine_run_logs(output):
    """Preserve raw streams; concatenation has no cross-stream chronological order."""
    with (output / 'palace.log').open('wb') as combined:
        for stream in ['stdout', 'stderr']:
            combined.write(f'\n=== {stream} (separate capture; not global event order) ===\n'.encode())
            with (output / f'palace.{stream}.log').open('rb') as source:
                shutil.copyfileobj(source, combined)


def source_hash():
    """Hash compiler inputs, including uncommitted/new files, excluding data and docs."""
    paths = [ROOT / 'CMakeLists.txt']
    for directory in ['palace', 'cmake', 'tools/adapter']:
        paths.extend(p for p in (ROOT / directory).rglob('*') if p.is_file())
    value = hashlib.sha256()
    for path in sorted(paths):
        value.update(str(path.relative_to(ROOT)).encode() + b'\0')
        value.update(bytes.fromhex(sha(path)))
    return value.hexdigest()


def image_id(image):
    return capture(['podman', 'image', 'inspect', image, '--format', '{{.Id}}']).removeprefix('sha256:')


def container_name():
    return 'palace-dev-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:12]


def builder(settings):
    name = container_name()
    exists = subprocess.run(['podman', 'container', 'exists', name]).returncode == 0
    expected = image_id(settings['builder_image'])
    if exists:
        actual = read_output(['podman', 'inspect', name])[0]
        if actual['Image'].removeprefix('sha256:') != expected:
            raise ValueError('Builder image changed; preserve/export its cache before recreating it')
        mounts = {m['Destination']: m['Source'] for m in actual['Mounts']}
        if mounts.get('/src/palace') != str(ROOT):
            raise ValueError('Existing builder points at another source tree')
    else:
        cache = ROOT / '.cache/ccache'
        cache.mkdir(parents=True, exist_ok=True)
        command(['podman', 'create', '--name', name, '--network=none',
                 '--security-opt=label=disable', '-v', f'{ROOT}:/src/palace:ro',
                 '-v', f'{cache}:/cache/ccache', '-e', 'CCACHE_DIR=/cache/ccache',
                 '-e', 'CCACHE_BASEDIR=/src/palace', '-e', 'CCACHE_COMPILERCHECK=content',
                 '-e', 'CCACHE_MAXSIZE=20G', '--entrypoint', 'sleep', expected, 'infinity'],
                stdout=subprocess.DEVNULL)
    command(['podman', 'start', name], stdout=subprocess.DEVNULL)
    return name


def read_output(args):
    return json.loads(capture(args))


def build(jobs):
    settings = read(SETTINGS)
    BUILD.mkdir(parents=True, exist_ok=True)
    with (BUILD / 'build.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        name = builder(settings)
        started = time.monotonic()
        input_hash = source_hash()
        log_path = BUILD / 'build.log'
        try:
            with log_path.open('w') as log:
                # Reconfigure the solver only. Existing MFEM/libCEED/hypre stay installed.
                command(['podman', 'exec', name, 'cmake', '-S', '/src/palace/palace',
                         '-B', settings['build_dir'], '-DCMAKE_CXX_COMPILER_LAUNCHER=ccache',
                         '-DCMAKE_CUDA_COMPILER_LAUNCHER=ccache'], stdout=log,
                        stderr=subprocess.STDOUT, timeout=120)
                command(['podman', 'exec', name, 'cmake', '--build', settings['build_dir'],
                         '--parallel', jobs], stdout=log, stderr=subprocess.STDOUT, timeout=1800)
                native = BUILD / 'native'
                native.mkdir(exist_ok=True)
                adapter_sources = {p.name: sha(p) for p in (ROOT / 'tools/adapter').iterdir() if p.is_file()}
                previous = read(BUILD / 'manifest.json') if (BUILD / 'manifest.json').exists() else {}
                adapter = native / 'libcudss_fp32.so'
                if previous.get('adapter_sources') != adapter_sources or not adapter.exists() or previous.get('native', {}).get(adapter.name) != sha(adapter):
                    command(['podman', 'exec', name, '/usr/local/cuda/bin/nvcc', '-std=c++17',
                             '-arch=sm_' + settings['architecture'], '-shared', '-Xcompiler=-fPIC',
                             '/src/palace/tools/adapter/cudss_fp32.cu',
                             '/src/palace/tools/adapter/cuda_memory.cpp', '-I/opt/cudss/include',
                             '--cudart=shared', '-ldl', '-o', '/tmp/palace-adapter.so'],
                            stdout=log, stderr=subprocess.STDOUT, timeout=180)
                    command(['podman', 'cp', name + ':/tmp/palace-adapter.so', adapter], stdout=log)
                for filename in ['libpalace.so', 'palace-x86_64.bin']:
                    command(['podman', 'cp', f'{name}:{settings["build_dir"]}/{filename}', native / filename], stdout=log)
                stats = capture(['podman', 'exec', name, 'ccache', '--show-stats'])
            if input_hash != source_hash():
                raise ValueError('Compiler inputs changed during build; build again')
            manifest = dict(schema=1, source_sha256=input_hash,
                            git_revision=capture(['git', '-C', ROOT, 'rev-parse', 'HEAD']),
                            builder_image_id=image_id(settings['builder_image']),
                            runtime_base_id=image_id(settings['runtime_image']),
                            settings_sha256=sha(SETTINGS), adapter_sources=adapter_sources,
                            native={p.name: sha(p) for p in native.iterdir() if p.is_file()},
                            elapsed_seconds=round(time.monotonic() - started, 3),
                            ccache=stats, numerically_validated=False)
            write(BUILD / 'manifest.json', manifest)
            write(BUILD / f'history/{time.time_ns()}.json', manifest)
            print(json.dumps({'build_seconds': manifest['elapsed_seconds'], 'output': str(native), 'ccache': stats}, indent=2))
        finally:
            command(['podman', 'stop', '--time', '0', name], stdout=subprocess.DEVNULL)


def verified_build():
    manifest = read(BUILD / 'manifest.json')
    if manifest['source_sha256'] != source_hash() or manifest['settings_sha256'] != sha(SETTINGS):
        raise ValueError('Sources/settings changed: build first')
    for filename, expected in manifest['native'].items():
        if sha(BUILD / 'native' / filename) != expected:
            raise ValueError('Built binary changed: ' + filename)
    return manifest


def fixture(name):
    directory = ROOT / 'examples' / name
    info = read(directory / 'fixture.json')
    for relative in [info['mesh'], *info['archive_parts']]:
        if not (directory / relative).resolve().is_relative_to(directory.resolve()):
            raise ValueError('Fixture path escapes its directory')
    checksum = hashlib.sha256()
    for part in info['archive_parts']:
        with (directory / part).open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                checksum.update(block)
    if checksum.hexdigest() != info['archive_sha256']:
        raise ValueError('Corrupt fixture archive: ' + name)
    config = read(directory / 'config.json')
    if sha(directory / 'config.json') != info['config_sha256']:
        raise ValueError('Fixture config differs from its contract')
    expected = info['medium']
    linear = config['Solver']['Linear']
    if any(linear[k] != expected[k] for k in ['Tol', 'MaxIts', 'MaxSize']):
        raise ValueError('Fixture is not the frozen medium profile')
    if any(config['Solver'][k] != expected[k] for k in ['Order', 'PartialAssemblyOrder']):
        raise ValueError('Fixture changed FEM order or partial assembly')
    return directory, info, config


def prepare(name):
    directory, info, _ = fixture(name)
    mesh = directory / info['mesh']
    if mesh.exists():
        if sha(mesh) != info['mesh_sha256']:
            raise ValueError('Existing mesh differs from its fixture')
        return mesh
    mesh.parent.mkdir(parents=True, exist_ok=True)
    temporary = mesh.with_suffix('.unpacking')
    try:
        with temporary.open('wb') as output:
            proc = subprocess.Popen(['zstd', '-d', '-q', '-c'], stdin=subprocess.PIPE, stdout=output)
            try:
                for part in info['archive_parts']:
                    with (directory / part).open('rb') as stream:
                        shutil.copyfileobj(stream, proc.stdin)
                proc.stdin.close()
                if proc.wait(timeout=120):
                    raise ValueError('Fixture decompression failed')
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait()
        if sha(temporary) != info['mesh_sha256']:
            raise ValueError('Unpacked mesh checksum mismatch')
        temporary.replace(mesh)
    finally:
        temporary.unlink(missing_ok=True)
    return mesh


def available_memory():
    return int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                    if line.startswith('MemAvailable:'))) * 1024


def validate_output(work, config, returncode):
    log = (work / 'palace.log').read_text(errors='replace')
    target = work / config['Problem']['Output'] / 'port-S.csv'
    expected = [f for sample in config['Solver']['Driven']['Samples'] for f in sample['Freq']]
    iterations = [int(n) for n in re.findall(r'GMRES solver converged in (\d+) iterations', log)]
    excited = sum(bool(p.get('Excitation')) for p in config['Boundaries']['LumpedPort'])
    checks = [dict(absolute=float(a), relative_initial=float(r), threshold=float(t))
              for a, r, t in re.findall(
                  r'PALACE_KSP_CHECK:\s+absolute=([\deE+.-]+) relative_initial=([\deE+.-]+) threshold=([\deE+.-]+)', log)]
    # A failed recurrence may be followed by a reliable restart; the final checked
    # stopping norm must pass for each completed solve. Record every check.
    successful = sum(all(math.isfinite(v) for v in c.values()) and c['absolute'] <= c['threshold'] for c in checks)
    expected_solves = len(expected) * excited
    complete = (returncode == 0 and target.exists() and 'did not converge' not in log
                and len(iterations) == expected_solves and successful == expected_solves)
    frequencies = []
    if target.exists():
        with target.open() as stream:
            reader = csv.DictReader(stream, skipinitialspace=True)
            for row in reader:
                row = {k.strip().strip('"'): v for k, v in row.items()}
                frequencies.append(float(row['f (GHz)']))
        complete = complete and frequencies == expected
    return {'complete': complete, 'exit_code': returncode, 'frequencies_ghz': frequencies,
            'iterations': iterations, 'verified_stopping_norm_checks': checks,
            'expected_solves': expected_solves,
            'scope': 'Execution completeness only; RF/precision qualification is separate'}


def coax_geometry(name):
    if name not in ['coax-tiny', 'coax-medium']:
        raise ValueError('TEM diagnostics require a verified coax fixture')
    directory = ROOT / 'examples' / name
    audit = read(directory / 'mesh-audit.json')
    geometry = audit['geometry']
    digest = hashlib.sha256(json.dumps(geometry, sort_keys=True).encode()).hexdigest()
    if (digest != audit['source_model_sha256'] or
            audit['mesh_sha256'] != read(directory / 'fixture.json')['mesh_sha256']):
        raise ValueError('Coax geometry manifest does not match its fixture')
    return geometry


def diagnostic_config(name, config, coax_fields=False, pc_side=None, krylov_size=None,
                      initial_fields=False, linear_tol=None):
    """Explicit runtime diagnostics; never change a frozen fixture on disk."""
    if linear_tol is not None:
        if (isinstance(linear_tol, bool) or not isinstance(linear_tol, (int, float))
                or not math.isfinite(linear_tol)
                or not 1e-14 <= linear_tol <= config['Solver']['Linear']['Tol']):
            raise ValueError('Diagnostic tolerance must be finite, at least 1e-14, and no weaker than fixture')
        config['Solver']['Linear']['Tol'] = linear_tol
    if krylov_size is not None:
        if (isinstance(krylov_size, bool) or not isinstance(krylov_size, int)
                or not 1 <= krylov_size <= 240):
            raise ValueError('Diagnostic Krylov size must be 1..240')
        if config['Solver']['Linear']['KSPType'] != 'GMRES':
            raise ValueError('Diagnostic Krylov size requires GMRES')
        config['Solver']['Linear']['MaxSize'] = krylov_size
    if initial_fields:
        config['Solver']['Linear']['InitialGuess'] = True
    if coax_fields:
        geometry = coax_geometry(name)
        config['Solver']['Driven']['Samples'] = [{'Type': 'Point', 'Freq': [3.55]}]
        probes = []
        for fraction in [0.25, 0.5, 0.75]:
            z = fraction*geometry['length_mm']
            for radius in [0.22, 0.32]:
                for angle in [0.31, 1.37, 2.61]:
                    probes.append({'Index': len(probes)+1,
                                   'Center': [radius*math.cos(angle), radius*math.sin(angle), z]})
        config['Domains']['Postprocessing'] = {'Probe': probes}
    if pc_side:
        config['Solver']['Linear']['PCSide'] = pc_side.title()
    return config


def field_identity(config, info, build):
    """Field ordering/physics identity; permit explicit solver/backend comparisons."""
    physics = json.loads(json.dumps(config))
    physics['Problem'].pop('Output', None)
    physics['Problem'].pop('Verbose', None)
    physics['Model']['Mesh'] = info['mesh_sha256']
    physics['Domains'].pop('Postprocessing', None)
    physics['Boundaries'].pop('Postprocessing', None)
    for key in ['Linear', 'Device', 'Backend']:
        physics['Solver'].pop(key, None)
    physics['Solver']['Driven'].pop('Save', None)
    identity = {'physics': physics, 'runtime_base_id': build['runtime_base_id'],
                'builder_image_id': build['builder_image_id'], 'format': 'PALF64V1-le-single-rank'}
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def expected_field_files(config):
    excitations = set()
    for port in config['Boundaries']['LumpedPort']:
        value = port.get('Excitation')
        if value:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError('Field snapshots require explicit integer excitations')
            excitations.add(value)
    count = sum(len(s['Freq']) for s in config['Solver']['Driven']['Samples'])
    return {f's{excitation}-f{frequency}-{field}.bin'
            for excitation in excitations for frequency in range(count) for field in ['E', 'B']}


def field_inventory(directory, expected):
    if {p.name for p in directory.iterdir()} != expected:
        raise ValueError('Missing or unexpected field snapshot files')
    result = {}
    for filename in sorted(expected):
        path = directory / filename
        if not path.is_file() or path.is_symlink():
            raise ValueError('Field snapshot must be a regular file')
        with path.open('rb') as stream:
            header = stream.read(16)
        if len(header) != 16:
            raise ValueError('Truncated field snapshot')
        magic, size = struct.unpack('<8sQ', header)
        if magic != b'PALF64V1' or size == 0 or path.stat().st_size != 16 + 16*size:
            raise ValueError('Invalid field snapshot format/size')
        result[filename] = {'sha256': sha(path), 'dofs': size, 'bytes': path.stat().st_size}
    return result


def verified_field_reference(directory, config, info, build):
    directory = Path(directory).resolve()
    metadata = read(directory / 'fields.json')
    source_identity = field_identity(read(directory/'config.json'), read(directory/'fixture.json'),
                                     read(directory/'build-manifest.json'))
    if (metadata.get('identity') != field_identity(config, info, build) or
            metadata.get('identity') != source_identity or
            sha(directory/'config.json') != read(directory/'command.json')['actual_config_sha256'] or
            not metadata.get('complete') or not read(directory / 'result.json').get('complete') or
            read(directory/'result.json').get('field_accuracy_passed') is False):
        raise ValueError('Field reference is incomplete or uses different physics/mesh/dependencies')
    if field_inventory(directory/'fields', expected_field_files(config)) != metadata['files']:
        raise ValueError('Field reference bytes changed')
    return directory


def field_restart_applied(log, config):
    matches = re.findall(r'PALACE_FIELD_RESTART: excitation=(\d+) frequency_index=(\d+) norm_E=([\deE+.-]+)', log)
    expected = {(int(stem.split('-')[0][1:]), int(stem.split('-')[1][1:]))
                for stem in expected_field_files(config) if stem.endswith('-E.bin')}
    return (len(matches) == len(expected) and
            {(int(s), int(f)) for s, f, n in matches} == expected and
            all(math.isfinite(float(n)) and float(n) >= 0 for s, f, n in matches))


def field_comparisons(work, config):
    entries = [dict(excitation=int(e), frequency_index=int(f), region=int(r),
                    relative_E=float(a), relative_B=float(b))
               for e, f, r, a, b in re.findall(
                   r'PALACE_FIELD_COMPARE: excitation=(\d+) frequency_index=(\d+) region=(-?\d+) '
                   r'relative_E=(\S+) relative_B=(\S+)', (work/'palace.log').read_text())]
    expected_files = expected_field_files(config)
    solves = {(int(re.match(r's(\d+)-f(\d+)-', name)[1]),
               int(re.match(r's(\d+)-f(\d+)-', name)[2])) for name in expected_files}
    regions = [-1] + [d['Index'] for d in config['Domains'].get('Postprocessing', {}).get('Energy', [])]
    expected = {(e, f, r) for e, f in solves for r in regions}
    coverage = {(v['excitation'], v['frequency_index'], v['region']) for v in entries}
    complete = coverage == expected and len(entries) == len(expected)
    passed = complete and all(math.isfinite(v[k]) and 0.0 <= v[k] <= 0.01
                              for v in entries for k in ['relative_E', 'relative_B'])
    return {'complete': complete, 'passed': passed, 'tolerance': 0.01, 'entries': entries,
            'norm': 'sqrt(error energy/reference energy), epsilon/mu weighted, same mesh; no phase fitting'}


def container_memory_path(pid):
    """Resolve cgroup v2 host path from the running container's host PID."""
    for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines():
        if line.startswith('0::'):
            relative = Path(line[3:].lstrip('/'))
            if '..' in relative.parts:
                raise ValueError('Unexpected cgroup path')
            return Path('/sys/fs/cgroup') / relative
    return None


def cgroup_memory(directory):
    if directory is None:
        return {}
    try:
        values = {'current_bytes': int((directory/'memory.current').read_text()),
                  'peak_bytes': int((directory/'memory.peak').read_text())}
        stats = dict(line.split() for line in (directory/'memory.stat').read_text().splitlines())
        values.update({key + '_bytes': int(stats[key]) for key in ['anon', 'file', 'shmem'] if key in stats})
        return values
    except (OSError, ValueError):
        return {}  # A container can start/exit between samples; absence is not completion.


def process_gpu_memory(pid):
    """Reported compute-context VRAM for the direct single-rank entrypoint PID."""
    if not pid:
        return None
    try:
        query = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,used_gpu_memory',
                                '--format=csv,noheader,nounits'],
                               capture_output=True, text=True, timeout=5)
        if query.returncode:
            return None
        total, found = 0, False
        for row in csv.reader(query.stdout.splitlines()):
            if len(row) != 2 or row[0].strip() != str(pid):
                continue
            try:
                total += int(row[1].strip()) * 1024**2  # nvidia-smi memory values are MiB.
                found = True
            except ValueError:
                return None  # Unsupported/MIG/unavailable is not zero usage.
        return total if found else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def memory_phase_report(log, solves, fields=False, release=False):
    events, errors = [], []
    decoder = json.JSONDecoder()
    for line in log.splitlines():
        marker = 'PALACE_MEMORY_PHASE '
        if marker not in line:
            continue
        try:
            event, _ = decoder.raw_decode(line[line.index(marker)+len(marker):])
            for key in ['managed_live_bytes', 'managed_interval_peak_bytes',
                        'managed_process_peak_bytes', 'cudss_live_bytes']:
                if not isinstance(event[key], int) or event[key] < 0:
                    raise ValueError('Invalid memory counter')
            if (event['managed_live_bytes'] > event['managed_interval_peak_bytes'] or
                    event['managed_interval_peak_bytes'] > event['managed_process_peak_bytes']):
                raise ValueError('Memory high-water ordering invalid')
            if (not all(math.isfinite(event[k]) and event[k] >= 0 for k in ['t_s', 'elapsed_s'])
                    or not isinstance(event['from'], str) or not isinstance(event['to'], str)):
                raise ValueError('Invalid phase label/time')
            if events and (event['t_s'] < events[-1]['t_s'] or event['from'] != events[-1]['to']):
                raise ValueError('Broken phase order')
            events.append(event)
        except (ValueError, KeyError, TypeError) as error:
            errors.append(str(error))
    required = {key: solves for key in ['preconditioner.begin', 'preconditioner.end',
                'gmres.begin', 'gmres.end', 'postprocess.begin', 'postprocess.end']}
    required.update({'setup.begin': 1, 'setup.end': 1, 'operators.begin': 1, 'driven.end': 1})
    if fields:
        required.update({'field_diagnostics.begin': solves, 'field_diagnostics.end': solves})
    if release:
        required.update({'gmres.basis_release.begin': solves, 'gmres.basis_release.end': solves})
    coverage = {label: sum(e['to'] == label for e in events) for label in required}
    complete = not errors and coverage == required
    return dict(complete=complete, events=events, required=required, coverage=coverage, errors=errors,
                scope='Allocation lifetimes and host monotonic intervals; no GPU synchronization; peaks are not additive')


def require_host_memory():
    free = available_memory()
    if free < 6 * 1024**3:
        raise ValueError(f'Host RAM below 6 GiB guard ({free / 1024**3:.2f} GiB available); GPU run not started')
    return free


def verified_qpool(native):
    directory = ROOT/'build/ceed-qpool'
    metadata = read(directory/'manifest.json')
    recipe = {p.name: sha(p) for p in (ROOT/'tools/experiments').glob('ceed_qpool*') if p.is_file()}
    if (metadata.get('recipe') != recipe or metadata.get('builder') != native['builder_image_id']
            or metadata.get('runtime') != native['runtime_base_id']
            or sha(directory/'libceed_qpool.so') != metadata.get('library_sha256')):
        raise ValueError('Q-pool prototype stale/tampered; build tools/experiments/ceed_qpool.py')
    destination = metadata.get('runtime_library_path', '')
    if not destination.startswith('/opt/software/') or not destination.endswith('/lib/libceed.so'):
        raise ValueError('Unexpected libCEED runtime path')
    return directory, metadata


def run(name, output, seconds, basis='fp32', coax_fields=False, pc_side=None, coax_l2=False,
        save_fields=False, field_reference=None, allocation_trace=False, ceed_qpool=False, hypre_pool_mib=None, memory_marks=False, release_gmres_basis=False,
        initial_fields=None, krylov_size=None, linear_tol=None):
    if basis not in ['fp32', 'fp64']:
        raise ValueError('Working data must remain in RAM/VRAM; disk basis was removed')
    if hypre_pool_mib is not None and (not isinstance(hypre_pool_mib, int) or isinstance(hypre_pool_mib, bool)
                                       or not 16 <= hypre_pool_mib <= 4096):
        raise ValueError('HYPRE pool must be an integer from 16 to 4096 MiB')
    require_host_memory()
    manifest = verified_build()
    qpool = verified_qpool(manifest) if ceed_qpool else None
    directory, info, config = fixture(name)
    config = diagnostic_config(name, config, coax_fields or coax_l2, pc_side, krylov_size,
                               bool(initial_fields), linear_tol)
    if release_gmres_basis and config['Solver']['Linear']['KSPType'] != 'GMRES':
        raise ValueError('Basis release is qualified only for GMRES')
    # Include the cable dielectric as a separate region for antenna field qualification.
    if save_fields or field_reference:
        regions = config['Domains'].setdefault('Postprocessing', {}).setdefault('Energy', [])
        region = 3 if name == 'tshaped-medium' else 1
        if not any(r['Index'] == region for r in regions):
            regions.append({'Index': region, 'Attributes': [region]})
    reference = (verified_field_reference(field_reference, config, info, manifest)
                 if field_reference else None)
    initial = None
    if initial_fields:
        initial = (reference if Path(initial_fields).resolve() == reference else
                   verified_field_reference(initial_fields, config, info, manifest))
    mesh = prepare(name)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / info['mesh']).parent.mkdir(parents=True, exist_ok=True)
    # Each run owns its input snapshot; never reuse previous postprocessing output.
    shutil.copy2(mesh, output / info['mesh'])
    write(output / 'config.json', config)
    write(output / 'build-manifest.json', manifest)
    write(output / 'fixture.json', info)
    if name in ['coax-tiny', 'coax-medium']:
        write(output / 'geometry.json', coax_geometry(name))
    settings = read(SETTINGS)
    container = 'palace-run-' + hashlib.sha256(str(output).encode()).hexdigest()[:12]
    flags = {'MFEM_MEMORY': 'cuda', 'LD_PRELOAD': '/opt/precision/libcudss_fp32.so',
             'PALACE_CUDA_MANAGED': '1', 'PALACE_CUDSS_TRACK': '1',
             'PALACE_LINE_BUFFERED_LOG': '1',
             'PALACE_SKIP_ESTIMATOR': '1', 'PALACE_VERIFY_RESIDUAL': '1'}
    if hypre_pool_mib is not None:
        flags['PALACE_HYPRE_DEVICE_POOL_MIB'] = str(hypre_pool_mib)
    if memory_marks:
        flags['PALACE_MEMORY_MARKS'] = '1'
    if release_gmres_basis:
        flags['PALACE_RELEASE_GMRES_BASIS'] = '1'
    if basis == 'fp32':
        flags['PALACE_GMRES_FP32_BASIS'] = '1'
    if allocation_trace:
        flags['PALACE_CUDA_ALLOC_TRACE'] = '1'
    if coax_l2:
        flags['PALACE_COAX_TEM_DIAGNOSTIC'] = '1'
        flags['PALACE_COAX_TEM_LENGTH_M'] = str(coax_geometry(name)['length_mm']*1e-3)
    if save_fields:
        flags['PALACE_SAVE_FIELDS'] = '/work/fields'
    if reference:
        flags['PALACE_REFERENCE_FIELDS'] = '/reference-fields'
    if initial:
        flags['PALACE_INITIAL_FIELDS'] = '/initial-fields'
    args = ['podman', 'create', '--name', container, '--network=none', '--timeout', str(seconds),
            '--stop-timeout', '3', '--memory', '60g', '--memory-swap', '60g',
            '--cpus', '8', '--device', 'nvidia.com/gpu=all', '--security-opt=label=disable',
            '--unsetenv', 'PALACE_GMRES_FP32_BASIS', '--unsetenv', 'PALACE_GMRES_FP64_DISK_BASIS',
            '--unsetenv', 'PALACE_GMRES_FP32_DISK_BASIS', '--unsetenv', 'PALACE_CUDA_ALLOC_TRACE',
            '--unsetenv', 'PALACE_HYPRE_DEVICE_POOL_MIB',
            '--unsetenv', 'PALACE_MEMORY_MARKS', '--unsetenv', 'PALACE_RELEASE_GMRES_BASIS',
            '--unsetenv', 'PALACE_LINE_BUFFERED_LOG',
            '--unsetenv', 'PALACE_COAX_TEM_DIAGNOSTIC',
            '--unsetenv', 'PALACE_COAX_TEM_LENGTH_M',
            '--unsetenv', 'PALACE_SAVE_FIELDS', '--unsetenv', 'PALACE_REFERENCE_FIELDS',
            '--unsetenv', 'PALACE_INITIAL_FIELDS',
            '-v', f'{output}:/work', '-v', f'{BUILD / "native/libpalace.so"}:/opt/palace-cudss/lib/libpalace.so:ro',
            '-v', f'{BUILD / "native/palace-x86_64.bin"}:/opt/palace-cudss/bin/palace-x86_64.bin:ro',
            '-v', f'{BUILD / "native/libcudss_fp32.so"}:/opt/precision/libcudss_fp32.so:ro', '-w', '/work']
    if qpool:
        location, metadata = qpool
        args.extend(['-v', f'{location / "libceed_qpool.so"}:{metadata["runtime_library_path"]}:ro'])
        write(output/'ceed-qpool-manifest.json', metadata)
    if reference:
        args.extend(['-v', f'{reference / "fields"}:/reference-fields:ro'])
    if initial:
        args.extend(['-v', f'{initial / "fields"}:/initial-fields:ro'])
    for key, value in flags.items():
        args.extend(['-e', f'{key}={value}'])
    args.extend(['--entrypoint', '/opt/palace-cudss/bin/palace-x86_64.bin', settings['runtime_image'], 'config.json'])
    command(args, stdout=subprocess.DEVNULL)
    write(output / 'command.json', {'argv': args, 'environment': flags,
                                   'diagnostic': {'coax_fields': coax_fields or coax_l2,
                                                  'pc_side': pc_side, 'coax_l2': coax_l2,
                                                  'allocation_trace': allocation_trace, 'ceed_qpool': ceed_qpool,
                                                  'hypre_pool_mib': hypre_pool_mib, 'memory_marks': memory_marks,
                                                  'release_gmres_basis': release_gmres_basis},
                                   'initial_fields': str(initial) if initial else None,
                                   'initial_fields_metadata_sha256': sha(initial/'fields.json') if initial else None,
                                   'actual_config_sha256': sha(output / 'config.json')})
    started = time.monotonic()
    status = {'complete': False, 'interrupted': True}
    try:
        with (output / 'palace.stdout.log').open('w') as log, \
             (output / 'palace.stderr.log').open('w') as errors, \
             (output / 'telemetry.jsonl').open('w') as telemetry:
            proc = subprocess.Popen(['podman', 'start', '--attach', container], stdout=log, stderr=errors)
            low_memory = 0
            memory_path = None
            pid = 0
            while proc.poll() is None:
                if memory_path is None:
                    inspected = read_output(['podman', 'inspect', container])[0]
                    pid = inspected['State'].get('Pid', 0)
                    if pid:
                        try:
                            memory_path = container_memory_path(pid)
                        except OSError:
                            pass
                process_memory = process_gpu_memory(pid)
                if process_memory is not None:
                    status['gpu_process_memory_peak_bytes'] = max(status.get('gpu_process_memory_peak_bytes', 0), process_memory)
                memory = cgroup_memory(memory_path)
                if memory:
                    status['cgroup_memory_peak_bytes'] = max(status.get('cgroup_memory_peak_bytes', 0), memory['peak_bytes'])
                free = available_memory()
                low_memory = low_memory + 1 if free < 6 * 1024**3 else 0
                gpu = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
                                     capture_output=True, text=True, timeout=5)
                telemetry.write(json.dumps({'seconds': time.monotonic() - started,
                                            'host_available_bytes': free, 'gpu': gpu.stdout.strip(),
                                            'container_memory': memory, 'gpu_process_pid': pid or None,
                                            'gpu_process_memory_bytes': process_memory}) + '\n')
                telemetry.flush()
                if low_memory >= 2 or time.monotonic() - started > seconds + 10:
                    status['host_guard_or_deadline'] = True
                    status['stop_reason'] = 'host_memory_guard' if low_memory >= 2 else 'runner_deadline'
                    command(['podman', 'stop', '--time', '3', container], stdout=subprocess.DEVNULL)
                    break
                time.sleep(1)
            returncode = proc.wait(timeout=15)
        combine_run_logs(output)
        inspected = read_output(['podman', 'inspect', container])[0]
        write(output / 'container-state.json', inspected['State'])
        status.update(validate_output(output, config, returncode))
        status['line_buffered_log_applied'] = ((output/'palace.stderr.log').read_text()
                                              .count('PALACE_LOG_BUFFERING: stdout=line\n') == 1)
        status['complete'] = status['complete'] and status['line_buffered_log_applied']
        if initial:
            status['field_restart_applied'] = field_restart_applied((output/'palace.log').read_text(), config)
            status['complete'] = status['complete'] and status['field_restart_applied']
        if memory_marks:
            phases = memory_phase_report((output/'palace.log').read_text(), status['expected_solves'],
                                         bool(save_fields or reference), release_gmres_basis)
            write(output/'memory-phases.json', phases)
            status['memory_marks_passed'] = phases['complete']
            status['complete'] = status['complete'] and phases['complete']
        if release_gmres_basis:
            releases = re.findall(r'PALACE_GMRES_BASIS_RELEASED: vectors=(\d+) logical_fp64_bytes=(\d+)',
                                  (output/'palace.log').read_text())
            status['gmres_basis_released'] = len(releases) == status['expected_solves'] and all(int(n) > 0 for n, b in releases)
            status['complete'] = status['complete'] and status['gmres_basis_released']
        if hypre_pool_mib is not None:
            logged = re.findall(r'PALACE_HYPRE_POOL: initial_device_bytes=(\d+)',
                                (output/'palace.log').read_text())
            status['hypre_pool_applied'] = logged == [str(hypre_pool_mib * 1024**2)]
            status['complete'] = status['complete'] and status['hypre_pool_applied']
        if qpool:
            checks = re.findall(r'PALACE_CEED_QPOOL: calls=(\d+) borrowed_vectors=(\d+)',
                                (output/'palace.log').read_text())
            status['qpool_executed'] = bool(checks) and all(int(a) > 0 and int(b) > 0 for a, b in checks)
            status['complete'] = status['complete'] and status['qpool_executed']
        if status.get('host_guard_or_deadline'):
            status['complete'] = False
        status['interrupted'] = False
        if status['complete'] and save_fields:
            write(output/'fields.json', {'schema': 1, 'identity': field_identity(config, info, manifest),
                                         'complete': True, 'files': field_inventory(output/'fields', expected_field_files(config))})
        if reference:
            comparison = field_comparisons(output, config)
            write(output/'field-comparison.json', comparison)
            status['field_accuracy_passed'] = comparison['passed']
            status['complete'] = status['complete'] and comparison['complete']
    finally:
        subprocess.run(['podman', 'rm', '--force', container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if 'proc' in locals() and proc.poll() is None:
            proc.wait(timeout=15)
        if not (output/'palace.log').exists() and (output/'palace.stderr.log').exists():
            combine_run_logs(output)
        status['elapsed_seconds'] = time.monotonic() - started
        if INTERRUPTED_SIGNAL is not None:
            status['interrupted_signal'] = INTERRUPTED_SIGNAL
        write(output / 'result.json', status)
    print(json.dumps(status, indent=2))
    if not status['complete']:
        raise ValueError('Run incomplete; see ' + str(output / 'palace.log'))
    if status.get('field_accuracy_passed') is False:
        raise ValueError('Field accuracy failed; see ' + str(output/'field-comparison.json'))


def package(tag):
    manifest = verified_build()
    settings = read(SETTINGS)
    context = BUILD / 'package'
    context.mkdir(exist_ok=True)
    shutil.copytree(BUILD / 'native', context / 'native', dirs_exist_ok=True)
    shutil.copy2(ROOT / 'tools/containers/Containerfile.runtime', context / 'Containerfile')
    write(context / 'build-manifest.json', manifest)
    command(['podman', 'build', '--pull=never', '--network=none', '--build-arg',
             'BASE_IMAGE=' + settings['runtime_image'], '-t', tag, context])
    write(BUILD / 'runtime-image.json', {'tag': tag, 'image_id': image_id(tag),
                                       'build_manifest_sha256': sha(BUILD / 'manifest.json'),
                                       'numerically_validated': False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    b = sub.add_parser('build'); b.add_argument('--jobs', type=int, default=8)
    p = sub.add_parser('prepare'); p.add_argument('case', choices=CASES)
    r = sub.add_parser('run'); r.add_argument('case', choices=CASES)
    r.add_argument('output', type=Path); r.add_argument('--seconds', type=int, default=1800)
    r.add_argument('--memory-marks', action='store_true', help='Optional allocation phase markers; no device synchronization')
    r.add_argument('--release-gmres-basis', action='store_true', help='Discard cached GMRES vectors after reconstruction, before postprocessing')
    r.add_argument('--hypre-pool-mib', type=int, help='Experimental initial Umpire device reservation, 16..4096 MiB; not a hard cap')
    r.add_argument('--ceed-qpool', action='store_true', help='Unqualified in-memory libCEED workspace prototype; requires separate cached build')
    r.add_argument('--allocation-trace', action='store_true', help='Trace large UVM allocations and caller stacks; diagnostic only')
    r.add_argument('--basis', choices=['fp32', 'fp64'], default='fp32',
                   help='GMRES basis storage only; FP64 operators/factors unchanged')
    r.add_argument('--coax-fields', action='store_true', help='Diagnostic coax: 3.55 GHz, 18 field probes')
    r.add_argument('--coax-l2', action='store_true', help='Expensive opt-in volume L2 check for the TEM coax')
    r.add_argument('--pc-side', choices=['left', 'right'], help='Explicit diagnostic preconditioning side')
    r.add_argument('--save-fields', action='store_true', help='Save FP64 same-mesh field snapshots')
    r.add_argument('--field-reference', type=Path, help='Completed run with verified field snapshots')
    r.add_argument('--initial-fields', type=Path, help='Verified same-mesh snapshot input, read once per solve as initial E')
    r.add_argument('--krylov-size', type=int, help='Explicit diagnostic GMRES restart size, 1..240; leaves medium mesh/tolerance unchanged')
    r.add_argument('--linear-tol', type=float, help='Stricter reference tolerance, 1e-14 up to fixture Tol; leaves spatial medium unchanged')
    r.add_argument('--background', action='store_true', help='Detach bounded run from the calling tool session')
    p = sub.add_parser('package'); p.add_argument('--tag', default='localhost/palace:local-sm120')
    sub.add_parser('status')
    args = parser.parse_args()
    if args.action == 'build':
        if not 1 <= args.jobs <= 24: parser.error('--jobs must be 1..24')
        build(args.jobs)
    elif args.action == 'prepare': print(prepare(args.case))
    elif args.action == 'run':
        if not 1 <= args.seconds <= 1800: parser.error('--seconds must be 1..1800')
        if args.background:
            output = args.output.resolve()
            metadata = output.parent/(output.name+'.job.json')
            if output.exists() or metadata.exists():
                raise ValueError('Background output/job already exists')
            metadata.parent.mkdir(parents=True, exist_ok=True)
            logfile = output.parent/(output.name+'.launcher.log')
            argv = [sys.executable, str(Path(__file__).resolve()),
                    *(arg for arg in sys.argv[1:] if arg != '--background')]
            with logfile.open('x') as log:
                process = subprocess.Popen(argv, cwd=ROOT, stdin=subprocess.DEVNULL,
                                           stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True)
            proc = Path(f'/proc/{process.pid}/stat')
            # Read after the final ')' because the comm field may contain spaces.
            try:
                birth = proc.read_text().rsplit(')', 1)[1].split()[19]
            except FileNotFoundError:
                birth = None  # Early failure is diagnosed from launcher log, never called live.
            job = {'pid': process.pid, 'start_ticks': birth, 'argv': argv, 'cwd': str(ROOT),
                   'output': str(output), 'log': str(logfile), 'result': str(output/'result.json')}
            write(metadata, job)
            print(json.dumps({'job': str(metadata), **job}, indent=2))
            return
        run(args.case, args.output, args.seconds, args.basis, args.coax_fields, args.pc_side,
            args.coax_l2, args.save_fields, args.field_reference, args.allocation_trace, args.ceed_qpool, args.hypre_pool_mib, args.memory_marks, args.release_gmres_basis,
            args.initial_fields, args.krylov_size, args.linear_tol)
    elif args.action == 'package': package(args.tag)
    else:
        print(json.dumps({'builder': container_name(), 'build': str(BUILD),
                          'manifest': read(BUILD / 'manifest.json') if (BUILD / 'manifest.json').exists() else None}, indent=2))


if __name__ == '__main__':
    def interrupted(_signum, _frame):
        global INTERRUPTED_SIGNAL
        INTERRUPTED_SIGNAL = signal.Signals(_signum).name
        print('PALACE_RUNNER_SIGNAL: ' + INTERRUPTED_SIGNAL, file=sys.stderr, flush=True)
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except (ValueError, FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, BlockingIOError) as error:
        sys.exit(str(error))
