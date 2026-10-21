#!/usr/bin/env python3
"""Bounded existing-PROM assessment; full original residual and held-out fields.

Research only. Does not alter the normal uniform runner or qualify an antenna.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dev


def probe_config(source, samples, hdm_tol=None):
    if type(samples) is not int or samples not in (2, 3, 4):
        raise ValueError('PROM probe samples must be integer 2, 3 or 4 per port')
    driven = source['Solver']['Driven']
    frequencies = [f for s in driven['Samples'] for f in s.get('Freq', [])]
    if (any(s.get('Type') != 'Point' or s.get('AddToPROM') or s.get('Save') for s in driven['Samples'])
            or driven.get('Save') or driven.get('Restart', 1) != 1
            or driven.get('AdaptiveTol', 0) != 0 or len(frequencies) <= samples
            or not all(math.isfinite(f) and f > 0 for f in frequencies)
            or frequencies != sorted(set(frequencies))
            or source.get('Model', {}).get('Refinement', {}).get('MaxIts', 0) != 0
            or source['Boundaries'].get('WavePort') or source['Boundaries'].get('FloquetPort')):
        raise ValueError('PROM probe requires a completed uniform fixed-mesh point sweep with held-out frequencies')
    out = json.loads(json.dumps(source))
    out['Solver']['Driven'].update(AdaptiveTol=0.01, AdaptiveMaxSamples=samples)
    if hdm_tol is not None:
        if (isinstance(hdm_tol, bool) or not isinstance(hdm_tol, (float,int)) or not math.isfinite(hdm_tol)
                or not 1e-10 <= hdm_tol <= min(source['Solver']['Linear']['Tol'],1e-6)):
            raise ValueError('HDM tolerance can only tighten the source tolerance, within 1e-10..1e-6')
        out['Solver']['Linear']['Tol']=hdm_tol
    return out


def audit(log, config, samples):
    frequencies = [f for s in config['Solver']['Driven']['Samples'] for f in s['Freq']]
    excitations = {int(p['Excitation']) for p in config['Boundaries']['LumpedPort'] if p.get('Excitation')}
    offline = re.findall(r'PALACE_PROM_SAMPLE: excitation=(\d+) frequency_ghz=(\S+)', log)
    rows = re.findall(r'PALACE_PROM_RAW: excitation=(\d+) frequency_index=(\d+) training=(\d+) dimension=(\d+) relative=(\S+)', log)
    expected = {(e, i) for e in excitations for i in range(len(frequencies))}
    if (len(rows) != len(expected) or {(int(e), int(i)) for e, i, t, d, r in rows} != expected
            or log.count('PALACE_PROM_RAW:') != len(rows)
            or log.count('PALACE_PROM_SAMPLE:') != len(offline)):
        raise ValueError('PROM online coverage is incomplete or duplicated')
    points = {e: [] for e in excitations}
    for e, f in offline:
        e, f = int(e), float(f)
        if (e not in points or not math.isfinite(f) or
                f < frequencies[0]*(1-1e-12) or f > frequencies[-1]*(1+1e-12) or f in points[e]):
            raise ValueError('Invalid offline sample')
        points[e].append(f)
    if any(not 2 <= len(v) <= samples or not all(any(math.isclose(f, q, rel_tol=1e-12) for q in v)
                                               for f in [frequencies[0], frequencies[-1]]) for v in points.values()):
        raise ValueError('Offline sample count/endpoints differ')
    parsed = []
    for e, i, training, dim, raw in rows:
        e, i, training, dim, raw = int(e), int(i), int(training), int(dim), float(raw)
        known = any(math.isclose(frequencies[i], f, rel_tol=1e-12) for f in points[e])
        if training not in (0, 1) or bool(training) != known or not 1 <= dim <= 2*len(offline) or not math.isfinite(raw) or raw < 0:
            raise ValueError('Invalid original residual, training flag or reduced dimension')
        parsed.append(dict(excitation=e, frequency_index=i, training=known, dimension=dim, relative=raw))
    if any(not any(r['excitation'] == e and not r['training'] for r in parsed) for e in excitations):
        raise ValueError('No genuinely held-out frequency for an excitation')
    raw_offline = [float(x) for x in re.findall(r'PALACE_TRUE_RESIDUAL: norm_Ax_minus_b=[\deE+.-]+ norm_b=[\deE+.-]+ relative=([\deE+.-]+)', log)]
    if len(raw_offline) != len(offline) or not all(math.isfinite(x) and 0 <= x <= 1e-6 for x in raw_offline):
        raise ValueError('Offline full solves failed original residual gate')
    return dict(execution_complete=True, original_residual_passed=all(r['relative'] <= 1e-6 for r in parsed),
                raw_limit=1e-6, online=parsed, offline=points, offline_raw=raw_offline,
                held_out=sum(not r['training'] for r in parsed))


def run(reference, output, samples=2, seconds=60, hdm_tol=None):
    invocation = time.monotonic()
    if type(seconds) is not int or not 15 <= seconds <= 300:
        raise ValueError('PROM probe deadline must be 15..300 seconds')
    dev.require_host_memory()
    build = dev.verified_build()
    reference = Path(reference).resolve()
    source, info = dev.read(reference/'config.json'), dev.read(reference/'fixture.json')
    if info['name'] not in ('coax-tiny', 'coax-medium'):
        raise ValueError('This bounded first filter supports coax fixtures only; antenna NOT qualified')
    config = probe_config(source, samples, hdm_tol)
    dev.verified_field_reference(reference, source, info, build)
    mesh = dev.prepare(info['name'])
    if dev.sha(mesh) != info['mesh_sha256']:
        raise ValueError('Reference mesh differs from the local fixture')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/info['mesh']).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mesh, output/info['mesh'])
    for name, value in [('config.json', config), ('build-manifest.json', build), ('fixture.json', info)]:
        dev.write(output/name, value)
    shutil.copy2(reference/'geometry.json', output/'geometry.json')
    settings = dev.read(dev.SETTINGS)
    name = 'palace-prom-'+hashlib.sha256(str(output).encode()).hexdigest()[:12]
    flags = dict(MFEM_MEMORY='cuda', LD_PRELOAD='/opt/precision/libcudss_fp32.so',
                 PALACE_CUDA_MANAGED='1', PALACE_CUDSS_TRACK='1', PALACE_LINE_BUFFERED_LOG='1',
                 PALACE_VERIFY_RESIDUAL='1', PALACE_SKIP_ESTIMATOR='1', PALACE_NATIVE_COMPLEX_COARSE='1',
                 PALACE_GMRES_FP32_BASIS='1', PALACE_GMRES_FP32_DIRECT='1', PALACE_HYPRE_DEVICE_POOL_MIB='256',
                 PALACE_PROM_VALIDATE='1', PALACE_SAVE_FIELDS='/work/fields', PALACE_REFERENCE_FIELDS='/reference-fields')
    args = ['podman', 'create', '--name', name, '--network=none', '--timeout', str(seconds),
            '--ulimit', 'core=0:0', '--stop-timeout', '3', '--memory', '60g', '--memory-swap', '60g',
            '--cpus', '8', '--device', 'nvidia.com/gpu=all', '--security-opt=label=disable', '-w', '/work']
    # Inherit no experimental PALACE/image memory policy. Explicit flags below are the entire probe policy.
    image_env = dev.read_output(['podman', 'image', 'inspect', settings['runtime_image']])[0]['Config'].get('Env', [])
    for key in sorted({v.split('=', 1)[0] for v in image_env if v.startswith(('PALACE_', 'MFEM_', 'HYPRE_', 'LD_PRELOAD='))}):
        args += ['--unsetenv', key]
    for key, value in flags.items(): args += ['-e', key+'='+value]
    args += ['-v', f'{output}:/work', '-v', f'{reference/"fields"}:/reference-fields:ro']
    for src, dst in [('libpalace.so', '/opt/palace-cudss/lib/libpalace.so'),
                     ('palace-x86_64.bin', '/opt/palace-cudss/bin/palace-x86_64.bin'),
                     ('libcudss_fp32.so', '/opt/precision/libcudss_fp32.so')]:
        args += ['-v', f'{dev.BUILD/"native"/src}:{dst}:ro']
    args += ['--entrypoint', '/opt/palace-cudss/bin/palace-x86_64.bin', settings['runtime_image'], 'config.json']
    dev.write(output/'command.json', dict(argv=args, environment=flags, actual_config_sha256=dev.sha(output/'config.json'),
                                         reference=str(reference), reference_config_sha256=dev.sha(reference/'config.json'),
                                         reference_inventory_sha256=dev.sha(reference/'fields.json'), samples_per_port=samples,
                                         hdm_tolerance=config['Solver']['Linear']['Tol']))
    result = dict(complete=False, execution_complete=False, scope='Existing PROM coax filter; no fallback or antenna qualification')
    started = time.monotonic()
    result['preparation_seconds'] = started-invocation
    try:
        dev.command(args, stdout=subprocess.DEVNULL)
        with (output/'palace.stdout.log').open('w') as out, (output/'palace.stderr.log').open('w') as err, (output/'telemetry.jsonl').open('w') as telemetry:
            proc = subprocess.Popen(['podman', 'start', '--attach', name], stdout=out, stderr=err)
            low = 0
            while proc.poll() is None:
                state = dev.read_output(['podman', 'inspect', name])[0]['State']
                try:
                    memory = dev.cgroup_memory(dev.container_memory_path(state['Pid'])) if state.get('Pid') else {}
                except OSError:
                    memory = {}  # Process exit may race one telemetry sample; inspect final state below.
                result['cgroup_memory_peak_bytes'] = max(result.get('cgroup_memory_peak_bytes', 0), memory.get('peak_bytes', 0))
                free = dev.available_memory()
                low = low+1 if free < 6*1024**3 else 0
                telemetry.write(json.dumps(dict(seconds=time.monotonic()-started, host_available_bytes=free, cgroup=memory))+'\n')
                telemetry.flush()
                if low >= 2 or time.monotonic()-started > seconds+10:
                    result['host_guard_or_deadline'] = True
                    dev.command(['podman', 'stop', '--time', '3', name], stdout=subprocess.DEVNULL)
                    break
                time.sleep(1)
            result['exit_code'] = proc.wait(timeout=15)
        state = dev.read_output(['podman', 'inspect', name])[0]['State']
        dev.write(output/'container-state.json', state)
        dev.combine_run_logs(output)
        if result['exit_code'] or state.get('OOMKilled') or result.get('host_guard_or_deadline'):
            raise ValueError('PROM process failed/deadline/OOM/host guard')
        log = (output/'palace.log').read_text()
        checks = audit(log, config, samples)
        fields = dev.field_comparisons(output, config)
        dev.write(output/'field-comparison.json', fields)
        result.update(checks)
        result['field_accuracy_passed'] = fields['passed']
        result['native_coarse_applied'] = dev.native_complex_coarse_applied(log, len(checks['offline_raw']), 'complex_fp64')
        dev.field_inventory(output/'fields', dev.expected_field_files(config))
        result['complete'] = checks['original_residual_passed'] and fields['passed'] and result['native_coarse_applied']
        dev.write(output/'prom-audit.json', checks)
    except (ValueError, subprocess.SubprocessError, OSError) as error:
        result['error'] = str(error)
    finally:
        subprocess.run(['podman', 'rm', '--force', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if 'proc' in locals() and proc.poll() is None: proc.wait(timeout=15)
        if not (output/'palace.log').exists() and (output/'palace.stdout.log').exists(): dev.combine_run_logs(output)
        result['elapsed_seconds'] = time.monotonic()-started
        result['end_to_end_seconds'] = time.monotonic()-invocation
        dev.write(output/'result.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--samples-per-port', type=int, choices=[2,3,4], default=2)
    parser.add_argument('--seconds', type=int, default=60)
    parser.add_argument('--hdm-tol',type=float,help='Explicit tighter offline solver tolerance; original online raw gate stays 1e-6')
    options = parser.parse_args()
    run(options.reference, options.output, options.samples_per_port, options.seconds, options.hdm_tol)
