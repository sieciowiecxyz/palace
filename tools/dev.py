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
                             '/src/palace/tools/adapter/cuda_memory.cpp',
                             '/src/palace/tools/adapter/pc_basis.cu',
                             '/src/palace/tools/adapter/ceed_audit.cpp', '-I/opt/cudss/include', '-I/opt/view/include',
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
                      initial_fields=False, linear_tol=None, cpu_reference=False,
                      complex_coarse=False, native_complex_coarse=False, preserve_coax_sweep=False,
                      coax_frequency=None):
    """Explicit runtime diagnostics; never change a frozen fixture on disk."""
    if preserve_coax_sweep not in [False,True,'fixture','n78']:
        raise ValueError('Unknown coax sweep preset')
    if coax_frequency is not None:
        samples=config['Solver']['Driven']['Samples']
        allowed=[value for sample in samples if sample.get('Type')=='Point' for value in sample.get('Freq',[])]
        if (name not in ['coax-tiny','coax-medium'] or not coax_fields or preserve_coax_sweep or
                isinstance(coax_frequency,bool) or coax_frequency not in allowed):
            raise ValueError('Select one existing coax fixture frequency with fields/L2; do not combine with sweep')
    if cpu_reference:
        config['Solver']['Device'] = 'CPU'
        config['Solver']['Backend'] = '/cpu/self'
    if native_complex_coarse:
        if cpu_reference or config['Solver']['Linear']['Type'] != 'cuDSS':
            raise ValueError('Native complex coarse requires GPU cuDSS')
    if complex_coarse or native_complex_coarse:
        config['Solver']['Linear'].update({'ComplexCoarseSolve': True, 'PCMatShifted': False})
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
        if not preserve_coax_sweep:
            config['Solver']['Driven']['Samples'] = [{'Type': 'Point', 'Freq': [3.55]}]
        elif preserve_coax_sweep=='n78':
            config['Solver']['Driven']['Samples'] = [{'Type': 'Point', 'Freq': [i/10 for i in range(33,40)]}]
        probes = []
        for fraction in [0.25, 0.5, 0.75]:
            z = fraction*geometry['length_mm']
            for radius in [0.22, 0.32]:
                for angle in [0.31, 1.37, 2.61]:
                    probes.append({'Index': len(probes)+1,
                                   'Center': [radius*math.cos(angle), radius*math.sin(angle), z]})
        config['Domains']['Postprocessing'] = {'Probe': probes}
        if coax_frequency is not None:
            config['Solver']['Driven']['Samples'] = [{'Type': 'Point', 'Freq': [coax_frequency]}]
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


def _verified_field_snapshot(directory, config, info, build, *, require_accuracy):
    directory = Path(directory).resolve()
    metadata = read(directory / 'fields.json')
    source_identity = field_identity(read(directory/'config.json'), read(directory/'fixture.json'),
                                     read(directory/'build-manifest.json'))
    if (metadata.get('identity') != field_identity(config, info, build) or
            metadata.get('identity') != source_identity or
            sha(directory/'config.json') != read(directory/'command.json')['actual_config_sha256'] or
            not metadata.get('complete') or not read(directory / 'result.json').get('complete') or
            (require_accuracy and read(directory/'result.json').get('field_accuracy_passed') is False)):
        raise ValueError('Field reference is incomplete or uses different physics/mesh/dependencies')
    if field_inventory(directory/'fields', expected_field_files(config)) != metadata['files']:
        raise ValueError('Field reference bytes changed')
    return directory


def verified_field_reference(directory, config, info, build):
    return _verified_field_snapshot(directory, config, info, build, require_accuracy=True)


def verified_initial_fields(directory, config, info, build):
    # A completed, byte-verified approximation may seed a stricter solve. It is
    # never accepted as an accuracy reference by this separate path.
    return _verified_field_snapshot(directory, config, info, build, require_accuracy=False)


def verified_partial_initial_fields(directory, config, info, build):
    source = read(Path(directory)/'config.json')
    files = expected_field_files(source)
    if not files or not files <= expected_field_files(config):
        raise ValueError('Partial seed excitations must be a nonempty subset of requested excitations')
    adjusted = json.loads(json.dumps(config))
    ports = {p['Index']:p for p in source['Boundaries']['LumpedPort']}
    if set(ports) != {p['Index'] for p in adjusted['Boundaries']['LumpedPort']}:
        raise ValueError('Partial seed requires identical physical ports')
    for p in adjusted['Boundaries']['LumpedPort']:
        p['Excitation'] = ports[p['Index']].get('Excitation',False)
    # Only excitation requests differ; all original strict physics/byte checks remain.
    return verified_initial_fields(directory, adjusted, info, build)


def verified_history_source(directory, config, info, build, frequencies):
    target=[f for sample in config['Solver']['Driven']['Samples'] for f in sample['Freq']]
    if (len(target)!=1 or not isinstance(frequencies,(list,tuple)) or len(frequencies)!=2
            or not all(isinstance(f,(int,float)) and not isinstance(f,bool) and math.isfinite(f) and f>0 for f in frequencies)
            or not frequencies[0]<frequencies[1]<target[0]):
        raise ValueError('History requires two distinct increasing source frequencies preceding one target')
    directory=Path(directory).resolve()
    source=read(directory/'config.json');source_info=read(directory/'fixture.json')
    # Verify the original, completed run and its full inventory. No fabricated result/view.
    verified_initial_fields(directory,source,source_info,build)
    samples=source['Solver']['Driven']['Samples']
    values=[f for sample in samples for f in sample.get('Freq',[])]
    if (any(sample.get('Type')!='Point' for sample in samples) or values!=sorted(set(values))
            or any(f not in values for f in frequencies)):
        raise ValueError('History frequencies must exist in an ordered point source sweep')
    source_ports={p['Index']:p for p in source['Boundaries']['LumpedPort']}
    requested={p['Excitation'] for p in config['Boundaries']['LumpedPort'] if p.get('Excitation')}
    available={p['Excitation'] for p in source_ports.values() if p.get('Excitation')}
    if (set(source_ports)!={p['Index'] for p in config['Boundaries']['LumpedPort']}
            or not requested or not requested<=available):
        raise ValueError('History requires identical physical ports and available excitations')
    adjusted=json.loads(json.dumps(config))
    adjusted['Solver']['Driven']['Samples']=samples
    for p in adjusted['Boundaries']['LumpedPort']:
        p['Excitation']=source_ports[p['Index']].get('Excitation',False)
    if field_identity(adjusted,info,build)!=field_identity(source,source_info,read(directory/'build-manifest.json')):
        raise ValueError('History uses different physics/mesh/dependencies beyond explicit frequency/excitation selection')
    metadata=read(directory/'fields.json')
    indices=[values.index(f) for f in frequencies]
    selected={f's{e}-f{i}-E.bin':metadata['files'][f's{e}-f{i}-E.bin'] for e in sorted(requested) for i in indices}
    return dict(source=str(directory),source_indices=indices,source_frequencies_ghz=list(frequencies),
                target_frequency_ghz=target[0],source_config_sha256=sha(directory/'config.json'),
                source_metadata_sha256=sha(directory/'fields.json'),selected_fields=selected,
                verified_input_bytes=sum(v['bytes'] for v in metadata['files'].values()),
                selected_input_bytes=sum(v['bytes'] for v in selected.values()),
                scope='Verified immutable history, starting approximation only; not an accuracy reference or completed target solve')


def field_restart_applied(log, config, initial_config=None):
    matches = re.findall(r'PALACE_FIELD_RESTART: excitation=(\d+) frequency_index=(\d+) norm_E=([\deE+.-]+)', log)
    expected = {(int(stem.split('-')[0][1:]), int(stem.split('-')[1][1:]))
                for stem in expected_field_files(initial_config or config) if stem.endswith('-E.bin')}
    target = {(int(stem.split('-')[0][1:]), int(stem.split('-')[1][1:]))
              for stem in expected_field_files(config) if stem.endswith('-E.bin')}
    zero = re.findall(r'PALACE_FIELD_RESTART_ZERO: excitation=(\d+) frequency_index=(\d+)',log)
    return (len(matches) == len(expected) and
            {(int(s), int(f)) for s, f, n in matches} == expected and
            len(zero)==len(target-expected) and {(int(s),int(f)) for s,f in zero}==target-expected and
            all(math.isfinite(float(n)) and float(n) >= 0 for s, f, n in matches))


def cpu_reference_applied(log):
    devices = re.findall(r'^Device configuration: ([^\n]+)', log, re.MULTILINE)
    backends = re.findall(r'^libCEED backend: ([^\n]+)', log, re.MULTILINE)
    actual = {v.strip() for v in devices[0].split(',')} if len(devices) == 1 else set()
    return (bool(actual) and 'cpu' in actual and actual <= {'cpu', 'omp'}
            and len(backends) == 1 and backends[0].startswith('/cpu/')
            and log.count('CUDSS_HYBRID_EXECUTE: enabled=1\n') == 1
            and log.count('PALACE_CUDSS_SERIAL_RHS: enabled=1\n') == 1)


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


def memory_phase_report(log, solves, fields=False, release=False, release_final=False,frequency_releases=0,predictor_checks=0):
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
    if release_final:
        required.update({'linear_workspace_release.begin': 1, 'linear_workspace_release.end': 1})
    if frequency_releases:
        required.update({'frequency_workspace_release.begin': frequency_releases,
                         'frequency_workspace_release.end': frequency_releases})
    if predictor_checks:
        required.update({'sweep_predictor.begin': predictor_checks, 'sweep_predictor.end': predictor_checks})
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


def native_complex_coarse_applied(log, solves, dtype='complex_fp64'):
    markers = re.findall(r'PALACE_NATIVE_COMPLEX_COARSE: dimension=(\d+) nnz=(\d+) dtype=(\w+) matrix=general', log)
    return (solves > 0 and dtype in ['complex_fp64', 'complex_fp32'] and len(markers) == solves
            and all(int(n) > 0 and int(nnz) > 0 and actual == dtype for n, nnz, actual in markers))


def native_coarse_builds(solves, reuse, profile, frequencies=1):
    # The controlled profiling stop occurs inside the FIRST solve, even if the
    # input requests more frequencies/ports. Full-run coverage is unchanged.
    return 1 if profile else frequencies if reuse else solves


def validate_native_mixed(enabled, native, hybrid, cpu, profile, ams):
    # A bounded profile is allowed, but remains incomplete as an RF solve.
    if enabled and (not native or hybrid is not None or cpu or ams is not None):
        raise ValueError('Native mixed requires native complex coarse without hybrid/CPU/AMS')


def native_mixed_applied(log, builds):
    summaries = re.findall(r'PALACE_NATIVE_MIXED_COARSE: solves=(\d+) corrections=2 max_relative_residual=(\S+) backend=cuda_fp64', log)
    scales = re.findall(r'PALACE_NATIVE_MIXED_SCALE: min=(\S+) max=(\S+) corrections=2 original=complex_fp64', log)
    if (builds < 1 or len(summaries) != builds or len(scales) != builds
            or log.count('PALACE_NATIVE_MIXED_COARSE:') != builds
            or log.count('PALACE_NATIVE_MIXED_SCALE:') != builds):
        return False
    try:
        valid = (all(int(n) > 0 and math.isfinite(float(r)) and 0 <= float(r) <= 1e-3 for n, r in summaries)
                 and all(0 < float(lo) <= float(hi) and math.isfinite(float(hi)) for lo, hi in scales))
    except ValueError:
        return False
    cleanup = re.findall(r'CUDSS_MEMORY: precision=(\w+) managed=(\d+) peak_bytes=(\d+) live_bytes=(\d+) allocations=(\d+)', log)
    return (valid and len(cleanup) == 1 and cleanup[0][0:2] == ('fp32', '1')
            and int(cleanup[0][2]) > 0 and int(cleanup[0][3]) == 0 and int(cleanup[0][4]) > 0)


def basis_prefetch_applied(log, solves):
    markers = re.findall(r'PALACE_BASIS_PREFETCH: managed=true stream=0 calls=(\d+) requested_bytes=(\d+)', log)
    return solves > 0 and len(markers) == solves and all(int(c) > 0 and int(b) >= 4*int(c) for c, b in markers)


def point_sweep_config(config, frequencies):
    if (not isinstance(frequencies,(list,tuple)) or len(frequencies)<1
            or not all(isinstance(f,(int,float)) and not isinstance(f,bool) and math.isfinite(f) and f>0 for f in frequencies)
            or list(frequencies)!=sorted(set(frequencies))):
        raise ValueError('Frequency override requires sorted distinct positive finite GHz values')
    driven=config['Solver']['Driven']
    if (driven.get('AdaptiveTol',0)>0 or driven.get('Restart',1)!=1
            or config.get('Model',{}).get('Refinement',{}).get('MaxIts',0)!=0):
        raise ValueError('Frequency override requires a fixed mesh, uniform sweep and first solve')
    config=json.loads(json.dumps(config))
    config['Solver']['Driven']['Samples']=[{'Type':'Point','Freq':list(frequencies)}]
    return config


def port_batch_config(config, both_ports=False, reuse=False, excitation=None, frequency_batch=False):
    config = json.loads(json.dumps(config))
    ports = config['Boundaries']['LumpedPort']
    if excitation is not None:
        if both_ports or isinstance(excitation,bool) or not isinstance(excitation,int) or excitation not in {p['Index'] for p in ports}:
            raise ValueError('Single excitation must select one existing port, without both-ports')
        for p in ports:
            p['Excitation'] = excitation if p['Index']==excitation else False
    if both_ports:
        if len(ports) != 2 or len({p['Index'] for p in ports}) != 2:
            raise ValueError('Both ports requires exactly two distinct lumped ports')
        for p in ports:
            p['Excitation'] = p['Index']
    if reuse or frequency_batch:
        samples = config['Solver']['Driven']['Samples']
        excitations = {p.get('Excitation') for p in ports if p.get('Excitation')}
        frequencies=[f for s in samples for f in s.get('Freq',[])]
        if (not samples or any(s.get('Type')!='Point' for s in samples) or not frequencies
                or not all(isinstance(f,(int,float)) and not isinstance(f,bool) and math.isfinite(f) and f>0 for f in frequencies)
                or frequencies!=sorted(set(frequencies)) or (frequency_batch and len(frequencies)<2)
                or (len(frequencies)>1 and len(excitations)!=2)
                or len(excitations) < 2 or any(isinstance(e,bool) or not isinstance(e,int) or e <= 0 for e in excitations)
                or config['Boundaries'].get('WavePort') or config['Boundaries'].get('FloquetPort')
                or config['Solver']['Driven'].get('AdaptiveTol',0)>0
                or (len(frequencies)>1 and (config['Solver']['Driven'].get('Save') or any(s.get('Save') for s in samples)))
                or config.get('Model',{}).get('Refinement',{}).get('MaxIts',0) != 0
                or config['Solver']['Driven'].get('Restart',1) != 1):
            raise ValueError('Port setup reuse/batching requires sorted distinct point frequencies, fixed mesh, distinct lumped excitations, no wave/Floquet ports and first solve; sweeps require two excitations')
    return config


def port_setup_audit(log, config, reuse=False, frequency_batch=False):
    excitations = sorted({int(p['Excitation']) for p in config['Boundaries']['LumpedPort'] if p.get('Excitation')})
    frequencies = sum(len(s['Freq']) for s in config['Solver']['Driven']['Samples'])
    frequency_major=(reuse or frequency_batch) and frequencies>1
    order=[(i,e,f) for i,e in enumerate(excitations) for f in range(frequencies)]
    if frequency_major:order.sort(key=lambda x:x[2])
    expected = [('reuse' if reuse and i else 'build', str(e), str(f)) for i,e,f in order]
    markers = re.findall(r'PALACE_PORT_SETUP: action=(build|reuse) excitation=(\d+) frequency_index=(\d+)',log)
    hashes = re.findall(r'PALACE_COARSE_CSR: algorithm=fnv1a64 structure=([0-9a-f]{16}) values=([0-9a-f]{16})',log)
    phases = re.findall(r'PALACE_COARSE_SETUP: analysis_s=([\deE+.-]+) factor_s=([\deE+.-]+)',log)
    builds = sum(a=='build' for a,_,_ in expected)
    passed = (builds > 0 and markers == expected and len(hashes)==builds and len(phases)==builds
              and all(math.isfinite(float(t)) and float(t)>=0 for pair in phases for t in pair))
    history=None
    if frequency_major:
        seeds=re.findall(r'PALACE_SWEEP_SEED: action=(zero|restore|store|release) excitation=(\d+) frequency_index=(\d+)',log)
        expected_seeds=[(action,str(e),str(f)) for _,e,f in order for action in
                        [('zero' if f==0 else 'restore'),('store' if f+1<frequencies else 'release')]] if config['Solver']['Linear'].get('InitialGuess',True) else []
        sizes=[int(b) for b in re.findall(r'PALACE_SWEEP_SEED: action=store excitation=\d+ frequency_index=\d+ logical_bytes=(\d+)',log)]
        history_passed=seeds==expected_seeds and ((len(sizes)==len(excitations)*(frequencies-1) and min(sizes)>0 and len(set(sizes))==1) if expected_seeds else not sizes)
        history=dict(passed=history_passed,markers=seeds,logical_history_capacity_bytes=len(excitations)*sizes[0] if sizes else 0,
                     scope='Per-port previous solution buffers; logical capacity, not physical VRAM peak')
        passed=passed and history_passed
    return dict(passed=passed, expected_builds=builds, markers=markers,history=history,
                csr_fingerprints=hashes, setup_seconds=[dict(analysis=float(a),factor=float(f)) for a,f in phases])


def validate_ams(cycles, *incompatible):
    if cycles is not None and (not isinstance(cycles, int) or isinstance(cycles, bool)
            or not 1 <= cycles <= 4 or any(v is not None and v is not False for v in incompatible)):
        raise ValueError('AMS requires fixed integer cycles 1..4, GPU and no native/complex coarse, hybrid, Q-pool or setup reuse/audit')


def ams_config(config, cycles):
    validate_ams(cycles)
    if cycles is None:
        raise ValueError('Explicit AMS cycles required')
    config = json.loads(json.dumps(config))
    config['Solver']['Linear'].update(Type='AMS', PCMatReal=True, PCMatShifted=True,
        ComplexCoarseSolve=False, AMSMaxIts=cycles, AMSSingularOperator=False,
        AMGAggressiveCoarsening=False, MGCycleIts=1)
    return config


def ams_applied(log, cycles, solves):
    configs = re.findall(r'PALACE_AMS_GPU_CONFIG: cycles=(\d+) tolerance=0 memory_device=1 execution_device=1', log)
    operators = re.findall(r'PALACE_AMS_OPERATOR: dimension=(\d+) cycle_type=(\d+)', log)
    return (solves > 0 and configs == [str(cycles)]*solves and len(operators) == solves
            and all(int(dim) > 0 and int(cycle) in [1, 14] for dim, cycle in operators)
            and 'PALACE_NATIVE_COMPLEX_COARSE:' not in log and 'CUDSS_MEMORY:' not in log)


def validate_native_hybrid(mib, native, cpu, profile):
    if mib is None:
        return
    if (not isinstance(mib, int) or isinstance(mib, bool) or not 256 <= mib <= 16384
            or not native or cpu or profile):
        raise ValueError('Native hybrid requires integer MiB 256..16384, native complex FP64 coarse and no CPU/profile mode')


def native_hybrid_applied(log, mib, builds):
    matches = re.findall(r'PALACE_NATIVE_HYBRID: limit_bytes=(\d+) minimum_device_bytes=(\d+) estimated_host_bytes=(\d+)', log)
    if builds < 1 or len(matches) != builds:
        return False
    return all(int(limit) == mib*1024**2 and 0 <= int(minimum) <= int(limit)
               for limit, minimum, host in matches) and bool(re.search(
                   r'CUDSS_MEMORY: precision=fp64 managed=0 peak_bytes=\d+ live_bytes=0 allocations=\d+', log))


def validate_deferred_postprocessing(config, release_final_solver,frequency_major=False,release_energy=False):
    boundaries = config['Boundaries']
    excitations = {int(p['Excitation']) for p in boundaries['LumpedPort'] if p.get('Excitation')}
    driven = config['Solver']['Driven']
    if (not release_final_solver or len(excitations) != 2
            or (sum(len(s['Freq']) for s in driven['Samples']) != 1 and not (frequency_major and release_energy))
            or driven.get('Restart', 1) != 1 or driven.get('Save')
            or config.get('Model', {}).get('Refinement', {}).get('MaxIts', 0) != 0
            or boundaries.get('WavePort') or boundaries.get('FloquetPort')):
        raise ValueError('Deferred postprocessing requires two lumped excitations, fixed mesh/final solver release without visualization/wave/Floquet ports; multiple frequencies require frequency-major batching and energy release')


def deferred_postprocessing_applied(log, config,frequency_major=False):
    excitations = sorted({int(p['Excitation']) for p in config['Boundaries']['LumpedPort'] if p.get('Excitation')})
    if len(excitations) != 2:
        return False
    matches = list(re.finditer(r'PALACE_DEFERRED_POSTPROCESS: action=(store|measure) excitation=(\d+) frequency_index=(\d+)', log))
    frequencies=sum(len(s['Freq']) for s in config['Solver']['Driven']['Samples'])
    if frequencies>1 and not frequency_major:return False
    expected=[(a,str(e),str(f)) for f in range(frequencies) for a,e in ([('store',excitations[0])]+[('measure',e) for e in excitations])]
    if [m.groups() for m in matches]!=expected:return False
    if frequency_major and frequencies>1:
        releases=list(re.finditer(r'PALACE_FREQUENCY_SOLVER_RELEASED: frequency_index=(\d+) solves_so_far=(\d+) iterations_so_far=(\d+)',log))
        iterations=[int(n) for n in re.findall(r'GMRES solver converged in (\d+) iterations',log)]
        if len(releases)!=frequencies or len(iterations)!=2*frequencies:return False
        for f,r in enumerate(releases):
            group=matches[f*3:f*3+3]
            if (r.groups()!=(str(f),str(2*(f+1)),str(sum(iterations[:2*(f+1)])))
                    or not group[0].start()<r.start()<group[1].start()<group[2].start()
                    or (f+1<frequencies and group[2].start()>=matches[(f+1)*3].start())):return False
        return (log.count('PALACE_FINAL_SOLVER_RELEASED: enabled=1')==1
                and releases[-1].start()<log.find('PALACE_FINAL_SOLVER_RELEASED: enabled=1')<matches[-2].start())
    released = log.find('PALACE_FINAL_SOLVER_RELEASED: enabled=1')
    return (len(excitations) == 2 and [m.groups() for m in matches] == expected
            and matches[0].start() < released < matches[1].start())


def sweep_predictor_mode(value):
    if value is False:return False
    if value is True:return 'linear'
    if isinstance(value,str) and value in ['linear','projected']:return value
    raise ValueError('Unknown sweep predictor mode')


def validate_sweep_predictor(config, frequency_major, initial_fields=None, history=False):
    frequencies=[f for s in config['Solver']['Driven']['Samples'] for f in s['Freq']]
    history_valid=history and len(frequencies)==1 and not frequency_major
    driven=config['Solver']['Driven'];boundaries=config['Boundaries']
    if ((not history_valid and (not frequency_major or len(frequencies)<3)) or initial_fields
            or not config['Solver']['Linear'].get('InitialGuess',True)
            or driven.get('AdaptiveTol',0)>0 or driven.get('Restart',1)!=1 or driven.get('Save')
            or any(sample.get('Save') for sample in driven['Samples'])
            or config.get('Model',{}).get('Refinement',{}).get('MaxIts',0)!=0
            or boundaries.get('WavePort') or boundaries.get('FloquetPort')):
        raise ValueError('Sweep predictor requires >=3 batch frequencies or explicit single-frequency history, InitialGuess and fixed uniform lumped solve without external seed/viz')


def sweep_predictor_audit(log, config, mode='linear', history=None):
    mode=sweep_predictor_mode(mode)
    frequencies=[f for s in config['Solver']['Driven']['Samples'] for f in s['Freq']]
    excitations=sorted({int(p['Excitation']) for p in config['Boundaries']['LumpedPort'] if p.get('Excitation')})
    matches=list(re.finditer(r'PALACE_SWEEP_PREDICTOR: action=(accept|fallback) excitation=(\d+) frequency_index=(\d+) ratio=([\deE+.-]+) baseline_residual=([\deE+.-]+) candidate_residual=([\deE+.-]+)',log))
    expected=[(e,f) for f in ([0] if history else range(2,len(frequencies))) for e in excitations]
    passed=((bool(excitations) and len(frequencies)==1 if history else len(excitations)==2 and len(frequencies)>=3) and len(matches)==len(expected)
            and log.count('PALACE_SWEEP_PREDICTOR:')==len(expected))
    checks=[]
    for m,(e,f) in zip(matches,expected):
        action,port,index,ratio,baseline,predicted=m.groups()
        ratio,baseline,predicted=map(float,[ratio,baseline,predicted])
        source=history['source_frequencies_ghz'] if history else frequencies[f-2:f]
        target=(frequencies[f]-source[1])/(source[1]-source[0])
        valid=(port==str(e) and index==str(f) and all(math.isfinite(x) for x in [ratio,baseline,predicted])
               and ratio>0 and baseline>=0 and predicted>=0 and math.isclose(ratio,target,rel_tol=1e-10)
               and (predicted<baseline if action=='accept' else predicted>=baseline))
        checks.append(dict(excitation=e,frequency_index=f,action=action,ratio=ratio,
                           baseline_residual=baseline,candidate_residual=predicted,passed=valid))
        passed=passed and valid
    sizes=[]
    if history:
        seeds=list(re.finditer(r'PALACE_HISTORY_SEED: excitation=(\d+) frequency_index=0 source_indices=(\d+),(\d+) source_frequencies=([\deE+.-]+),([\deE+.-]+) logical_bytes_per_field=(\d+)',log))
        releases=list(re.finditer(r'PALACE_HISTORY_RELEASE: excitation=(\d+) frequency_index=0',log))
        passed=passed and len(seeds)==len(excitations) and len(releases)==len(excitations)
        passed=passed and log.count('PALACE_HISTORY_SEED:')==len(excitations) and log.count('PALACE_HISTORY_RELEASE:')==len(excitations)
        for seed,release,selection,e in zip(seeds,releases,matches,excitations):
            port,i,j,fi,fj,size=seed.groups();size=int(size);sizes.append(size)
            passed=passed and (port==str(e) and release[1]==str(e) and [int(i),int(j)]==history['source_indices']
                and [float(fi),float(fj)]==history['source_frequencies_ghz'] and size>0
                and seed.start()<selection.start()<release.start()
                and 'GMRES solver converged in' in log[selection.end():release.start()])
        passed=passed and bool(sizes) and len(set(sizes))==1
        passed=passed and all(a.start()<b.start() for a,b in zip(releases,seeds[1:]))
    else:
        older=list(re.finditer(r'PALACE_SWEEP_OLDER: action=(store|release) excitation=(\d+) frequency_index=(\d+)(?: logical_bytes=(\d+))?',log))
        expected_older=[('store' if f+1<len(frequencies) else 'release',str(e),str(f))
                        for f in range(1,len(frequencies)) for e in excitations]
        passed=passed and [m.groups()[:3] for m in older]==expected_older and log.count('PALACE_SWEEP_OLDER:')==len(expected_older)
        sizes=[int(m[4]) for m in older if m[1]=='store' and m[4] is not None]
        normal_sizes=[int(b) for b in re.findall(r'PALACE_SWEEP_SEED: action=store excitation=\d+ frequency_index=\d+ logical_bytes=(\d+)',log)]
        passed=passed and len(sizes)==len(excitations)*(len(frequencies)-2) and bool(sizes) and min(sizes)>0 and len(set(sizes+normal_sizes))==1
        # Every prediction follows this port's prior older store and current restore,
        # and precedes its converged solve/current store or release.
        for m,check in zip(matches,checks):
            e,f=check['excitation'],check['frequency_index']
            before=f'PALACE_SWEEP_SEED: action=restore excitation={e} frequency_index={f}'
            after=f'PALACE_SWEEP_SEED: action={"store" if f+1<len(frequencies) else "release"} excitation={e} frequency_index={f}'
            previous=f'PALACE_SWEEP_OLDER: action=store excitation={e} frequency_index={f-1}'
            start,end=log.find(before),log.find(after)
            passed=passed and 0<=log.find(previous)<start<m.start()<end and 'GMRES solver converged in' in log[m.end():end]
    projections=list(re.finditer(r'PALACE_SWEEP_PROJECTION: excitation=(\d+) frequency_index=(\d+) image_norm=([\deE+.-]+) dot_real=([\deE+.-]+) dot_imag=([\deE+.-]+) alpha_real=([\deE+.-]+) alpha_imag=([\deE+.-]+) usable=([01]) operator_applies=([23])',log))
    expected_projection=len(expected) if mode=='projected' else 0
    passed=passed and len(projections)==expected_projection and log.count('PALACE_SWEEP_PROJECTION:')==expected_projection
    projection_checks=[]
    for m,check,selection in zip(projections,checks,matches):
        port,index,norm,dr,di,ar,ai,usable,applies=m.groups()
        norm,dr,di,ar,ai=map(float,[norm,dr,di,ar,ai]);dot=complex(dr,di);alpha=complex(ar,ai)
        target=dot/norm if norm>0 else None
        normalizable=norm>0 and math.isfinite(norm) and math.isfinite(1.0/norm)
        expected_usable=(normalizable and target is not None and math.isfinite(target.real)
                         and math.isfinite(target.imag) and abs(target)<=1e6)
        valid=(port==str(check['excitation']) and index==str(check['frequency_index'])
               and all(math.isfinite(x) for x in [norm,dr,di,ar,ai]) and norm>=0
               and bool(int(usable))==bool(expected_usable) and int(applies)==(3 if expected_usable else 2)
               and m.start()<selection.start())
        if history and len(seeds)>len(projection_checks):valid=valid and seeds[len(projection_checks)].start()<m.start()
        if expected_usable:valid=valid and abs(alpha-target)<=1e-12*max(1,abs(target))
        else:valid=valid and alpha==0 and check['action']=='fallback' and check['baseline_residual']==check['candidate_residual']
        projection_checks.append(dict(excitation=int(port),frequency_index=int(index),image_norm=norm,
            dot_real=dr,dot_imag=di,alpha_real=ar,alpha_imag=ai,usable=bool(int(usable)),operator_applies=int(applies),passed=bool(valid)))
        passed=passed and valid
    return dict(mode=mode,projection_checks=projection_checks,passed=bool(passed),checks=checks,accepted=sum(c['action']=='accept' for c in checks),
                fallback=sum(c['action']=='fallback' for c in checks),
                logical_older_capacity_bytes=(1 if history else len(excitations))*sizes[0] if sizes else 0,
                history_replay=history is not None,
                scope='Initial-guess selection only; linear two original A applies, projected up to three and two temporary vectors. Not field/PROM/physical residency qualification')


def postprocess_energy_release_applied(log, config,frequency_major=False):
    excitations = sorted({int(p['Excitation']) for p in config['Boundaries']['LumpedPort'] if p.get('Excitation')})
    frequencies = sum(len(s['Freq']) for s in config['Solver']['Driven']['Samples'])
    order = [(str(e),str(f)) for e in excitations for f in range(frequencies)]
    if frequency_major:order.sort(key=lambda x:int(x[1]))
    released = re.findall(r'PALACE_POSTPROCESS_ENERGY_RELEASED: excitation=(\d+) frequency_index=(\d+)',log)
    rebuilt = re.findall(r'PALACE_POSTPROCESS_ENERGY_REBUILT: excitation=(\d+) frequency_index=(\d+)',log)
    return len(order)>1 and released==order[:-1] and rebuilt==order[1:]


def run(name, output, seconds, basis='fp32', coax_fields=False, pc_side=None, coax_l2=False,
        save_fields=False, field_reference=None, allocation_trace=False, ceed_qpool=False, hypre_pool_mib=None, memory_marks=False, release_gmres_basis=False,
        initial_fields=None, krylov_size=None, linear_tol=None, cpu_reference=False,
        phase_trace=False, complex_coarse=False, release_final_solver=False, native_complex_coarse=False,
        nsys_window=None, direct_basis=False, coax_sweep=False, coax_frequency=None, basis_prefetch=False,
        setup_audit=False, port_setup_reuse=False, both_ports=False, partial_initial_fields=False, excitation=None,
        release_postprocess_energy=False, defer_postprocessing=False, cudss_hybrid_mib=None, ams_cycles=None,
        native_coarse_fp32=False, basis_audit=False, pc_basis_fp32_forward=False, pc_basis_compensated_forward=False, frequency_port_batch=False, frequencies=None, sweep_predictor=False, initial_history=None, history_frequencies=None):
    invocation_started=time.monotonic()
    sweep_predictor=sweep_predictor_mode(sweep_predictor)
    if bool(initial_history)!=(history_frequencies is not None):
        raise ValueError('History source and two source frequencies must be specified together')
    if initial_history and (not sweep_predictor or initial_fields or frequency_port_batch or cpu_reference or nsys_window is not None):
        raise ValueError('History replay requires predictor and one target frequency, without other seeds/batch/CPU/profiler')
    if sweep_predictor and (not (port_setup_reuse or frequency_port_batch or initial_history) or initial_fields
            or not native_complex_coarse or cpu_reference or nsys_window is not None):
        raise ValueError('Sweep predictor requires native CUDA coarse and frequency batching/reuse, without external seed or partial profiler')
    if pc_basis_fp32_forward and pc_basis_compensated_forward:
        raise ValueError('Choose exactly one experimental PC basis arithmetic')
    pc_basis_mixed=pc_basis_fp32_forward or pc_basis_compensated_forward
    if pc_basis_mixed and (not native_complex_coarse or not release_final_solver or pc_side!='right'
            or cpu_reference or nsys_window is not None or ceed_qpool or ams_cycles is not None or cudss_hybrid_mib is not None):
        raise ValueError('Mixed PC basis requires native coarse/right/release-final-solver without CPU/profiler/Qpool/AMS/hybrid')
    validate_native_mixed(native_coarse_fp32, native_complex_coarse, cudss_hybrid_mib,
                          cpu_reference, nsys_window, ams_cycles)
    validate_ams(ams_cycles, native_complex_coarse, complex_coarse, cpu_reference, cudss_hybrid_mib,
                 ceed_qpool, setup_audit, port_setup_reuse)
    if direct_basis and basis != 'fp32':
        raise ValueError('Direct basis requires FP32 storage')
    if basis_prefetch and (basis != 'fp32' or not direct_basis or cpu_reference):
        raise ValueError('Basis prefetch requires direct FP32 CUDA')
    if (setup_audit or port_setup_reuse or frequency_port_batch) and (not native_complex_coarse or nsys_window is not None):
        raise ValueError('Port setup audit/reuse requires native complex coarse without partial profiler')
    if partial_initial_fields and not initial_fields:
        raise ValueError('Partial initial fields requires an explicit verified source')
    if coax_sweep and (name not in ['coax-tiny','coax-medium'] or not (coax_fields or coax_l2)):
        raise ValueError('Coax sweep requires coax fields/L2 on a coax fixture')
    if coax_frequency is not None and (name not in ['coax-tiny','coax-medium'] or not (coax_fields or coax_l2) or coax_sweep):
        raise ValueError('Coax frequency requires coax fields/L2 and no simultaneous sweep')
    if frequencies is not None and (coax_sweep or coax_frequency is not None):
        raise ValueError('Frequency override conflicts with coax sweep/frequency presets')
    profiler = profile = None
    if nsys_window is not None:
        if (basis != 'fp64' and not (basis == 'fp32' and direct_basis)) or cpu_reference or ceed_qpool or save_fields or field_reference or coax_l2:
            raise ValueError('Profiling requires FP64 or direct FP32 CUDA and no output/reference field qualification')
        import nsight_window as profiler
        profiler.parse_window(nsys_window)
        profiler.verified_tool()
        phase_trace = True
    if basis not in ['fp32', 'fp64']:
        raise ValueError('Working data must remain in RAM/VRAM; disk basis was removed')
    validate_native_hybrid(cudss_hybrid_mib, native_complex_coarse, cpu_reference, nsys_window)
    if native_complex_coarse and ((basis != 'fp64' and not (basis == 'fp32' and direct_basis)) or cpu_reference or ceed_qpool):
        raise ValueError('Native complex coarse requires FP64 or explicit direct FP32 basis, without CPU or Q-pool')
    if cpu_reference and (ceed_qpool or basis != 'fp64' or complex_coarse):
        raise ValueError('CPU reference requires FP64 basis without GPU Q-pool or complex-coarse profile')
    if hypre_pool_mib is not None and (not isinstance(hypre_pool_mib, int) or isinstance(hypre_pool_mib, bool)
                                       or not 16 <= hypre_pool_mib <= 4096):
        raise ValueError('HYPRE pool must be an integer from 16 to 4096 MiB')
    require_host_memory()
    manifest = verified_build()
    qpool = verified_qpool(manifest) if ceed_qpool else None
    directory, info, config = fixture(name)
    config = diagnostic_config(name, config, coax_fields or coax_l2, pc_side, krylov_size,
                               bool(initial_fields), linear_tol, cpu_reference, complex_coarse,
                               native_complex_coarse, coax_sweep, coax_frequency)
    if ams_cycles is not None:
        config = ams_config(config, ams_cycles)
    if frequencies is not None:
        config = point_sweep_config(config, frequencies)
    config = port_batch_config(config, both_ports, port_setup_reuse, excitation, frequency_port_batch)
    frequency_count=sum(len(s['Freq']) for s in config['Solver']['Driven']['Samples'])
    frequency_major=(port_setup_reuse or frequency_port_batch) and frequency_count>1
    if sweep_predictor:
        validate_sweep_predictor(config,frequency_major,initial_fields,bool(initial_history))
    if frequency_major and initial_fields:
        raise ValueError('Frequency-major batching uses per-port RAM/VRAM history, not external field seeds')
    if release_postprocess_energy and (len(expected_field_files(config)) < 4 or config['Solver']['Driven'].get('Save')
            or config.get('Model',{}).get('Refinement',{}).get('MaxIts',0) != 0):
        raise ValueError('Energy release requires multiple solves, fixed mesh and no visualization saves')
    if defer_postprocessing:
        validate_deferred_postprocessing(config, release_final_solver,frequency_major,release_postprocess_energy)
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
                   (verified_partial_initial_fields if partial_initial_fields else verified_initial_fields)(initial_fields, config, info, manifest))
    history = verified_history_source(initial_history,config,info,manifest,history_frequencies) if initial_history else None
    mesh = prepare(name)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / info['mesh']).parent.mkdir(parents=True, exist_ok=True)
    # Each run owns its input snapshot; never reuse previous postprocessing output.
    shutil.copy2(mesh, output / info['mesh'])
    write(output / 'config.json', config)
    write(output / 'build-manifest.json', manifest)
    write(output / 'fixture.json', info)
    if history:write(output/'history-source.json',history)
    if name in ['coax-tiny', 'coax-medium']:
        write(output / 'geometry.json', coax_geometry(name))
    settings = read(SETTINGS)
    container = 'palace-run-' + hashlib.sha256(str(output).encode()).hexdigest()[:12]
    flags = {'MFEM_MEMORY': 'cuda', 'LD_PRELOAD': '/opt/precision/libcudss_fp32.so',
             'PALACE_CUDA_MANAGED': '1', 'PALACE_CUDSS_TRACK': '1',
             'PALACE_LINE_BUFFERED_LOG': '1',
             'PALACE_SKIP_ESTIMATOR': '1', 'PALACE_VERIFY_RESIDUAL': '1'}
    if cpu_reference:
        flags.update({'MFEM_MEMORY': 'host', 'PALACE_CUDSS_HYBRID_EXECUTE': '1',
                      'OMP_NUM_THREADS': '8', 'OPENBLAS_NUM_THREADS': '1'})
    if native_complex_coarse:
        flags['PALACE_NATIVE_COMPLEX_COARSE'] = '1'
    if native_coarse_fp32:
        flags['PALACE_NATIVE_COARSE_FP32'] = '1'
    if basis_audit:
        flags['PALACE_CEED_BASIS_AUDIT'] = '1'
    if pc_basis_fp32_forward:
        flags['PALACE_PC_BASIS_FP32_FORWARD'] = '1'
    if pc_basis_compensated_forward:
        flags['PALACE_PC_BASIS_COMPENSATED_FORWARD'] = '1'
    if cudss_hybrid_mib is not None:
        flags['PALACE_CUDSS_HYBRID_MIB'] = str(cudss_hybrid_mib)
    if ams_cycles is not None:
        flags['PALACE_AMS_FIXED_GPU'] = '1'
    if phase_trace:
        flags['PALACE_PHASE_TRACE'] = '1'
    if hypre_pool_mib is not None:
        flags['PALACE_HYPRE_DEVICE_POOL_MIB'] = str(hypre_pool_mib)
    if memory_marks:
        flags['PALACE_MEMORY_MARKS'] = '1'
    if release_gmres_basis:
        flags['PALACE_RELEASE_GMRES_BASIS'] = '1'
    if release_final_solver:
        flags['PALACE_RELEASE_FINAL_SOLVER'] = '1'
    if basis == 'fp32':
        flags['PALACE_GMRES_FP32_BASIS'] = '1'
    if direct_basis:
        flags['PALACE_GMRES_FP32_DIRECT'] = '1'
    if basis_prefetch:
        flags['PALACE_GMRES_BASIS_PREFETCH'] = '1'
    if setup_audit or port_setup_reuse or frequency_port_batch:
        flags['PALACE_PORT_SETUP_AUDIT'] = '1'
    if sweep_predictor:
        flags['PALACE_SWEEP_PREDICTOR'] = sweep_predictor
    if frequency_port_batch:
        flags['PALACE_FREQUENCY_PORT_BATCH'] = '1'
    if port_setup_reuse:
        flags['PALACE_REUSE_PORT_SETUP'] = '1'
    if release_postprocess_energy:
        flags['PALACE_RELEASE_POSTPROCESS_ENERGY'] = '1'
    if defer_postprocessing:
        flags['PALACE_DEFER_POSTPROCESSING'] = '1'
    if allocation_trace:
        flags['PALACE_CUDA_ALLOC_TRACE'] = '1'
    if coax_l2:
        flags['PALACE_COAX_TEM_DIAGNOSTIC'] = '1'
        flags['PALACE_COAX_TEM_LENGTH_M'] = str(coax_geometry(name)['length_mm']*1e-3)
    if save_fields:
        flags['PALACE_SAVE_FIELDS'] = '/work/fields'
    if reference:
        flags['PALACE_REFERENCE_FIELDS'] = '/reference-fields'
    if history:
        flags['PALACE_HISTORY_FIELDS']='/history-fields'
        flags['PALACE_HISTORY_INDICES']=','.join(map(str,history['source_indices']))
        flags['PALACE_HISTORY_FREQUENCIES']=','.join(map(str,history['source_frequencies_ghz']))
    if initial:
        flags['PALACE_INITIAL_FIELDS'] = '/initial-fields'
        if partial_initial_fields:
            excitations = sorted({p['Excitation'] for p in read(initial/'config.json')['Boundaries']['LumpedPort'] if p.get('Excitation')})
            flags['PALACE_INITIAL_FIELDS_EXCITATIONS'] = ','+','.join(map(str,excitations))+','
    if profiler:
        profile = profiler.prepare(nsys_window, output)
        flags['PALACE_KRYLOV_PROFILE'] = nsys_window
        flags['PALACE_PROFILE_CAPTURE_RANGE'] = '1'
    args = ['podman', 'create', '--name', container, '--network=none', '--timeout', str(seconds),
            '--ulimit', 'core=0:0',
            '--stop-timeout', '3', '--memory', '60g', '--memory-swap', '60g',
            '--cpus', '8', '--device', 'nvidia.com/gpu=all', '--security-opt=label=disable',
            '--unsetenv', 'PALACE_GMRES_FP32_BASIS', '--unsetenv', 'PALACE_GMRES_FP64_DISK_BASIS',
            '--unsetenv', 'PALACE_GMRES_FP32_DIRECT',
            '--unsetenv', 'PALACE_GMRES_BASIS_PREFETCH',
            '--unsetenv', 'PALACE_PORT_SETUP_AUDIT', '--unsetenv', 'PALACE_REUSE_PORT_SETUP',
            '--unsetenv', 'PALACE_SWEEP_PREDICTOR', '--unsetenv', 'PALACE_FREQUENCY_PORT_BATCH',
            '--unsetenv', 'PALACE_RELEASE_POSTPROCESS_ENERGY',
            '--unsetenv', 'PALACE_DEFER_POSTPROCESSING',
            '--unsetenv', 'PALACE_GMRES_FP32_DISK_BASIS', '--unsetenv', 'PALACE_CUDA_ALLOC_TRACE',
            '--unsetenv', 'PALACE_HYPRE_DEVICE_POOL_MIB',
            '--unsetenv', 'PALACE_MEMORY_MARKS', '--unsetenv', 'PALACE_RELEASE_GMRES_BASIS',
            '--unsetenv', 'PALACE_RELEASE_FINAL_SOLVER',
            '--unsetenv', 'PALACE_LINE_BUFFERED_LOG',
            '--unsetenv', 'PALACE_CUDSS_HYBRID_EXECUTE', '--unsetenv', 'PALACE_CUDSS_HYBRID_MIB',
            '--unsetenv', 'PALACE_AMS_FIXED_GPU',
            '--unsetenv', 'PALACE_NATIVE_COMPLEX_COARSE', '--unsetenv', 'PALACE_CUDSS_FP32',
            '--unsetenv', 'PALACE_NATIVE_COARSE_FP32',
            '--unsetenv', 'PALACE_CEED_BASIS_AUDIT',
            '--unsetenv', 'PALACE_PC_BASIS_FP32_FORWARD',
            '--unsetenv', 'PALACE_PC_BASIS_COMPENSATED_FORWARD',
            '--unsetenv', 'PALACE_PHASE_TRACE',
            '--unsetenv', 'PALACE_KRYLOV_PROFILE',
            '--unsetenv', 'PALACE_PROFILE_CAPTURE_RANGE',
            '--unsetenv', 'PALACE_COAX_TEM_DIAGNOSTIC',
            '--unsetenv', 'PALACE_COAX_TEM_LENGTH_M',
            '--unsetenv', 'PALACE_SAVE_FIELDS', '--unsetenv', 'PALACE_REFERENCE_FIELDS',
            '--unsetenv', 'PALACE_HISTORY_FIELDS', '--unsetenv', 'PALACE_HISTORY_INDICES',
            '--unsetenv', 'PALACE_HISTORY_FREQUENCIES',
            '--unsetenv', 'PALACE_INITIAL_FIELDS',
            '--unsetenv', 'PALACE_INITIAL_FIELDS_EXCITATIONS',
            '-v', f'{output}:/work', '-v', f'{BUILD / "native/libpalace.so"}:/opt/palace-cudss/lib/libpalace.so:ro',
            '-v', f'{BUILD / "native/palace-x86_64.bin"}:/opt/palace-cudss/bin/palace-x86_64.bin:ro',
            '-v', f'{BUILD / "native/libcudss_fp32.so"}:/opt/precision/libcudss_fp32.so:ro', '-w', '/work']
    if qpool:
        location, metadata = qpool
        args.extend(['-v', f'{location / "libceed_qpool.so"}:{metadata["runtime_library_path"]}:ro'])
        write(output/'ceed-qpool-manifest.json', metadata)
    if history:
        args.extend(['-v',f"{Path(history['source'])/'fields'}:/history-fields:ro"])
    if reference:
        args.extend(['-v', f'{reference / "fields"}:/reference-fields:ro'])
    if initial:
        args.extend(['-v', f'{initial / "fields"}:/initial-fields:ro'])
    if profile:
        args.extend(['-v', f'{profiler.TOOL}:/profile-tools:ro',
                     '-v', f'{profile["ram_directory"]}:/profile',
                     '--tmpfs', '/tmp:rw,size=256m', '-e', 'TMPDIR=/profile/tmp'])
    for key, value in flags.items():
        if profile and key == 'LD_PRELOAD': continue  # Inject target only, not collector.
        args.extend(['-e', f'{key}={value}'])
    target = '/opt/palace-cudss/bin/palace-x86_64.bin'
    if profile:
        args.extend(['--unsetenv', 'LD_PRELOAD', '--entrypoint', '/profile-tools/'+profiler.BINARY,
                     settings['runtime_image'], *profiler.arguments(profile),
                     '--env-var=LD_PRELOAD='+flags['LD_PRELOAD'], target, 'config.json'])
    else:
        args.extend(['--entrypoint', target, settings['runtime_image'], 'config.json'])
    try:
        command(args, stdout=subprocess.DEVNULL)
    except BaseException:
        if profile: shutil.rmtree(profile['ram_directory'])
        raise
    write(output / 'command.json', {'argv': args, 'environment': flags,
                                   'diagnostic': {'coax_fields': coax_fields or coax_l2,
                                                  'pc_side': pc_side, 'coax_l2': coax_l2,
                                                  'allocation_trace': allocation_trace, 'ceed_qpool': ceed_qpool,
                                                  'hypre_pool_mib': hypre_pool_mib, 'memory_marks': memory_marks,
                                                  'release_gmres_basis': release_gmres_basis,
                                                  'release_final_solver': release_final_solver},
                                   'native_complex_coarse': native_complex_coarse,
                                   'native_coarse_fp32': native_coarse_fp32,
                                   'basis_audit': basis_audit,
                                   'pc_basis_fp32_forward': pc_basis_fp32_forward,
                                   'pc_basis_compensated_forward': pc_basis_compensated_forward,
                                   'frequency_major_reuse': frequency_major and port_setup_reuse,
                                   'frequency_major_batch': frequency_major,
                                   'frequency_override_ghz': frequencies,
                                   'sweep_predictor': sweep_predictor,
                                   'history_source': history,
                                   'nsys_window': nsys_window,
                                   'cpu_reference': cpu_reference,
                                   'phase_trace': phase_trace,
                                   'initial_fields': str(initial) if initial else None,
                                   'initial_fields_metadata_sha256': sha(initial/'fields.json') if initial else None,
                                   'initial_fields_source_accuracy_passed': read(initial/'result.json').get('field_accuracy_passed') if initial else None,
                                   'initial_fields_scope': 'Starting approximation only; not an accuracy reference' if initial else None,
                                   'actual_config_sha256': sha(output / 'config.json')})
    started = time.monotonic()
    status = {'complete': False, 'interrupted': True, 'preparation_seconds':started-invocation_started}
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
                process_pid = (profiler.target_pid(pid) if profile else pid)
                process_memory = process_gpu_memory(process_pid or 0)
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
                                            'container_memory': memory, 'gpu_process_pid': process_pid or None,
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
        if profile:
            measured = profiler.collect(profile, output)
            status['profile_complete'] = (measured['complete'] and returncode == 0 and
                                          not inspected['State'].get('OOMKilled', False) and
                                          not status.get('host_guard_or_deadline', False))
            status['complete'] = False  # Deliberately partial; never an RF qualification.
            status['scope'] = profile['scope']
        if native_complex_coarse:
            status['native_complex_coarse_applied'] = native_complex_coarse_applied(
                (output/'palace.log').read_text(), native_coarse_builds(status['expected_solves'], port_setup_reuse, profile,frequency_count),
                'complex_fp32' if native_coarse_fp32 else 'complex_fp64')
            status['complete'] = status['complete'] and status['native_complex_coarse_applied']
            if profile:
                status['profile_complete'] = status['profile_complete'] and status['native_complex_coarse_applied']
        if native_coarse_fp32:
            status['native_mixed_applied'] = native_mixed_applied(
                (output/'palace.log').read_text(), native_coarse_builds(status['expected_solves'], port_setup_reuse, profile,frequency_count))
            status['complete'] = status['complete'] and status['native_mixed_applied']
            if profile:
                status['profile_complete'] = status['profile_complete'] and status['native_mixed_applied']
        if basis_audit:
            import ceed_basis_audit
            try:
                audit = ceed_basis_audit.analyze((output/'palace.log').read_text())
            except (ValueError, TypeError, KeyError) as error:
                audit = dict(passed=False,error=str(error),scope='Basis metadata audit failed; no dimension qualification')
            write(output/'basis-audit.json',audit)
            status['basis_audit_passed'] = audit['passed']
            status['complete'] = status['complete'] and audit['passed']
            if profile:
                status['profile_complete'] = status['profile_complete'] and audit['passed']
        if pc_basis_mixed:
            import pc_basis_audit
            try:
                audit = pc_basis_audit.analyze((output/'palace.log').read_text(),
                    'compensated_bits' if pc_basis_compensated_forward else 'fp32_fused')
            except (ValueError,TypeError,KeyError) as error:
                audit = dict(passed=False,error=str(error))
            write(output/'pc-basis-audit.json',audit)
            status['pc_basis_compensated_forward_passed' if pc_basis_compensated_forward else 'pc_basis_fp32_forward_passed'] = audit['passed']
            status['complete'] = status['complete'] and audit['passed']
        if setup_audit or port_setup_reuse or frequency_port_batch:
            audit = port_setup_audit((output/'palace.log').read_text(), config, port_setup_reuse, frequency_port_batch)
            write(output/'port-setup-audit.json',audit)
            status['port_setup_audit_passed'] = audit['passed']
            status['complete'] = status['complete'] and audit['passed']
        if ams_cycles is not None:
            status['ams_fixed_gpu_config_applied'] = ams_applied(
                (output/'palace.log').read_text(), ams_cycles, status['expected_solves'])
            if not profile:
                status['complete'] = status['complete'] and status['ams_fixed_gpu_config_applied']
        if cudss_hybrid_mib is not None:
            expected_builds = frequency_count if port_setup_reuse else status['expected_solves']
            status['native_hybrid_applied'] = native_hybrid_applied(
                (output/'palace.log').read_text(), cudss_hybrid_mib, expected_builds)
            status['complete'] = status['complete'] and status['native_hybrid_applied']
        if defer_postprocessing:
            status['deferred_postprocessing_applied'] = deferred_postprocessing_applied(
                (output/'palace.log').read_text(), config,frequency_major)
            try: counters=read(output/config['Problem']['Output']/'palace.json').get('LinearSolver',{})
            except (OSError,ValueError): counters={}
            status['solver_metadata_counts_passed']=(counters.get('TotalSolves')==status['expected_solves']
                and counters.get('TotalIts')==sum(status['iterations']))
            status['complete'] = status['complete'] and status['solver_metadata_counts_passed']
            status['complete'] = status['complete'] and status['deferred_postprocessing_applied']
        if sweep_predictor:
            prediction=sweep_predictor_audit((output/'palace.log').read_text(),config,sweep_predictor,history)
            write(output/'sweep-predictor-audit.json',prediction)
            status['sweep_predictor_passed']=prediction['passed']
            status['complete']=status['complete'] and prediction['passed']
        if release_postprocess_energy:
            status['postprocess_energy_release_applied'] = postprocess_energy_release_applied((output/'palace.log').read_text(),config,frequency_major)
            status['complete'] = status['complete'] and status['postprocess_energy_release_applied']
        if basis_prefetch and not profile:
            status['basis_prefetch_applied'] = basis_prefetch_applied(
                (output/'palace.log').read_text(), status['expected_solves'])
            status['complete'] = status['complete'] and status['basis_prefetch_applied']
        if cpu_reference:
            status['cpu_reference_applied'] = cpu_reference_applied((output/'palace.log').read_text())
            status['complete'] = status['complete'] and status['cpu_reference_applied']
        status['line_buffered_log_applied'] = ((output/'palace.stderr.log').read_text()
                                              .count('PALACE_LOG_BUFFERING: stdout=line\n') == 1)
        status['complete'] = status['complete'] and status['line_buffered_log_applied']
        if initial:
            status['field_restart_applied'] = field_restart_applied((output/'palace.log').read_text(), config,
                read(initial/'config.json') if partial_initial_fields else None)
            status['complete'] = status['complete'] and status['field_restart_applied']
        if memory_marks:
            phases = memory_phase_report((output/'palace.log').read_text(), status['expected_solves'],
                                         bool(save_fields or reference), release_gmres_basis,
                                         release_final_solver,frequency_count if frequency_major and defer_postprocessing else 0,
                                         (status['expected_solves'] if history else 2*(frequency_count-2)) if sweep_predictor else 0)
            write(output/'memory-phases.json', phases)
            status['memory_marks_passed'] = phases['complete']
            status['complete'] = status['complete'] and phases['complete']
        if release_final_solver:
            status['final_solver_released'] = ((output/'palace.log').read_text()
                                               .count('PALACE_FINAL_SOLVER_RELEASED: enabled=1\n') == 1)
            status['complete'] = status['complete'] and status['final_solver_released']
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
        if profile:
            # collect() normally cleans up; also cover interrupted/failed launches.
            shutil.rmtree(profile['ram_directory'], ignore_errors=True)
        if not (output/'palace.log').exists() and (output/'palace.stderr.log').exists():
            combine_run_logs(output)
        finished=time.monotonic()
        status['elapsed_seconds'] = finished - started
        status['end_to_end_seconds'] = finished - invocation_started
        if INTERRUPTED_SIGNAL is not None:
            status['interrupted_signal'] = INTERRUPTED_SIGNAL
        write(output / 'result.json', status)
    print(json.dumps(status, indent=2))
    if not status['complete'] and not status.get('profile_complete'):
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
    r.add_argument('--direct-basis', action='store_true', help='Experimental direct FP32 basis dot/axpy with FP64 arithmetic; requires --basis fp32')
    r.add_argument('--basis-prefetch', action='store_true', help='Experimental managed basis prefetch before Dot on CUDA stream 0; requires --direct-basis')
    r.add_argument('--setup-audit', action='store_true', help='Log driver setup counts and native coarse CSR fingerprints/analysis/factor times')
    r.add_argument('--port-setup-reuse', action='store_true', help='Opt-in lumped-port setup reuse at equal frequency; multi-frequency two-port batches use per-port RAM/VRAM history and frequency-major order; includes setup audit')
    r.add_argument('--both-ports', action='store_true', help='Excite both existing lumped ports separately, preserving geometry and terminations')
    r.add_argument('--excitation', type=int, help='Solve only one existing lumped port index, preserving physical terminations')
    r.add_argument('--partial-initial-fields', action='store_true', help='Allow verified initial snapshot for a subset of requested excitations; others start at zero')
    r.add_argument('--ams-cycles', type=int, help='Experimental fixed 1..4 AMS coarse cycles on a real shifted positive auxiliary PC; physical A unchanged')
    r.add_argument('--cudss-hybrid-mib', type=int, help='Experimental native FP64 cuDSS host/device memory budget; query actual minimum before factorization')
    r.add_argument('--defer-postprocessing', action='store_true', help='Opt-in cache first E field in RAM/VRAM and measure both ports after final solver release')
    r.add_argument('--release-postprocess-energy', action='store_true', help='Opt-in free energy operators between solves and rebuild before measurements; no visualization writes')
    r.add_argument('--coax-sweep',nargs='?',const='fixture',default=False,choices=['fixture','n78'],help='Keep fixture frequencies or explicitly select n78 preset 3.3..3.9GHz/0.1GHz with coax field diagnostics')
    r.add_argument('--initial-history',help='Completed verified source run; immutable earlier fields for a single target-frequency predictor replay, not an accuracy reference')
    r.add_argument('--history-frequencies',nargs=2,type=float,help='Two increasing source GHz frequencies preceding the single target')
    r.add_argument('--sweep-predictor',nargs='?',const='linear',default=False,choices=['linear','projected'],help='Experimental two-history initial guess: linear extrapolation or complex residual projection; original FP64 residual gate')
    r.add_argument('--frequency-port-batch', action='store_true', help='Two-port frequency-major schedule with per-port history, independent of optional setup reuse')
    r.add_argument('--frequencies',nargs='+',type=float,help='Explicit sorted GHz point sweep; preserves frozen fixture mesh/materials/Tol, conflicts with coax presets')
    r.add_argument('--coax-frequency', type=float, help='Run one existing coax fixture frequency with fields/L2; both ports and medium mesh unchanged')
    r.add_argument('--release-final-solver', action='store_true', help='Release final fixed-mesh solver and system operators before postprocessing')
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
    r.add_argument('--initial-fields', type=Path, help='Byte-verified completed same-mesh snapshot as initial approximation only; accuracy not implied')
    r.add_argument('--krylov-size', type=int, help='Explicit diagnostic GMRES restart size, 1..240; leaves medium mesh/tolerance unchanged')
    r.add_argument('--linear-tol', type=float, help='Stricter reference tolerance, 1e-14 up to fixture Tol; leaves spatial medium unchanged')
    r.add_argument('--cpu-reference', action='store_true', help='Experimental FP64 host FEM/GMRES with cuDSS hybrid execute; not the CUDA baseline')
    r.add_argument('--phase-trace', action='store_true', help='Diagnostic host BlockTimer/NVTX scopes, including nested preconditioner phases')
    r.add_argument('--complex-coarse', action='store_true', help='Diagnostic exact complex coarse solve; GPU profile only, unshifted preconditioner')
    r.add_argument('--native-complex-coarse', action='store_true', help='Experimental rank1 complex cuDSS coarse, FP64 default, without real 2N block; implies --complex-coarse')
    r.add_argument('--native-coarse-fp32', action='store_true', help='Opt-in scaled complex FP32 LU with two original-FP64 CUDA corrections; requires native coarse, no hybrid/AMS')
    r.add_argument('--basis-audit', action='store_true', help='Opt-in host metadata audit of actual libCEED basis dimensions/calls; no vector copies or GPU synchronization')
    pc_basis=r.add_mutually_exclusive_group()
    pc_basis.add_argument('--pc-basis-fp32-forward',action='store_true',help='Experimental PC-only non-tensor forward basis FP32 registers; outer A/residual and transpose stay FP64')
    pc_basis.add_argument('--pc-basis-compensated-forward',action='store_true',help='Experimental PC-only P20/Q14/QC3 forward compensated hi/lo registers with guarded bit splitting; outer A/residual and transpose stay FP64')
    r.add_argument('--nsys-window', metavar='FIRST:COUNT', help='Partial CUDA trace with calibrated host phases; FIRST=0..32, COUNT=2..8; no RF qualification')
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
            args.initial_fields, args.krylov_size, args.linear_tol, args.cpu_reference, args.phase_trace,
            args.complex_coarse, args.release_final_solver, args.native_complex_coarse, args.nsys_window, args.direct_basis, args.coax_sweep, args.coax_frequency, args.basis_prefetch,
            args.setup_audit, args.port_setup_reuse, args.both_ports, args.partial_initial_fields, args.excitation,
            args.release_postprocess_energy, args.defer_postprocessing, args.cudss_hybrid_mib, args.ams_cycles,
            args.native_coarse_fp32, args.basis_audit,args.pc_basis_fp32_forward,args.pc_basis_compensated_forward,args.frequency_port_batch,args.frequencies,args.sweep_predictor,args.initial_history,args.history_frequencies)
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
