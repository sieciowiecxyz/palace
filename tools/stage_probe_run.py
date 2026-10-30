#!/usr/bin/env python3
"""Prepare/execute one bounded native diagnostic or full completion run; no RF qualification.

Uses pinned local Podman image, read-only native/mesh mounts and existing helpers.
`prepare` performs no container creation or simulation. Execution is explicit.
"""
from __future__ import annotations
import argparse
import csv
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import dev
from stage_operator_reference import compiler_inputs, source_hash
from stage_preprocess import check_diagnostic
from stage_full_check import check_full, expectations as full_expectations

IMAGE = '43ac46f6430cf44d7a2da0a618a0f5c67c6965cca2fde510f2a96116333e6d76'
GIB = 1024**3
# Exact reviewed GPU baseline flags; reject profiling/history or unknown additions.
GPU_BASELINE_KEYS = frozenset((
    'MFEM_MEMORY', 'LD_PRELOAD', 'PALACE_CUDA_MANAGED', 'PALACE_CUDSS_TRACK',
    'PALACE_LINE_BUFFERED_LOG', 'PALACE_SKIP_ESTIMATOR', 'PALACE_VERIFY_RESIDUAL',
    'PALACE_NATIVE_COMPLEX_COARSE', 'PALACE_HYPRE_DEVICE_POOL_MIB',
    'PALACE_MEMORY_MARKS', 'PALACE_RELEASE_GMRES_BASIS', 'PALACE_RELEASE_FINAL_SOLVER',
    'PALACE_GMRES_FP32_BASIS', 'PALACE_GMRES_FP32_DIRECT', 'PALACE_PORT_SETUP_AUDIT',
    'PALACE_REUSE_PORT_SETUP', 'PALACE_RELEASE_POSTPROCESS_ENERGY',
    'PALACE_DEFER_POSTPROCESSING',
))


def environment_hash(environment):
    return hashlib.sha256(json.dumps(environment,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def helper_hashes():
    return {'dev': dev.sha(Path(dev.__file__)),
            'stage_operator_reference': dev.sha(Path(compiler_inputs.__code__.co_filename)),
            'stage_preprocess': dev.sha(Path(check_diagnostic.__code__.co_filename)),
            'stage_full_check': dev.sha(Path(check_full.__code__.co_filename))}


def validate_policy(stage, seconds, memory_gib, threads, cpu, available, stage_trace=False):
    if stage not in ('preprocess', 'operators', 'full'):
        raise ValueError('Only preprocess/operators/full stages are permitted')
    maximum = 1800 if stage == 'full' else 300
    if type(seconds) is not int or type(memory_gib) is not int or not 1 <= seconds <= maximum or not 4 <= memory_gib <= 70:
        raise ValueError(f'Deadline must be 1..{maximum} s and memory budget 4..70 GiB')
    if stage == 'full' and (cpu or threads != 1 or stage_trace is not False):
        raise ValueError('Full runs require GPU, OMP1 and trace OFF')
    if type(threads) is not int or not 1 <= threads <= 8 or (cpu and threads != 1):
        raise ValueError('Threads must be 1..8; controlled CPU diagnostics require OMP1')
    if available < (memory_gib + 8) * GIB:
        raise ValueError('Host memory cannot cover cgroup budget plus 8 GiB reserve')


def inference_processes(proc_root=Path('/proc')):
    """Read-only check matching the local antenna inference guard's server names."""
    found = []
    for p in proc_root.iterdir():
        if not p.name.isdecimal():
            continue
        try:
            name = (p / 'comm').read_text().strip()
            args = (p / 'cmdline').read_bytes().split(b'\0')
            if (name in ('strata', 'llama-server', 'ollama') or name.startswith('vllm')
                    or any(x.rsplit(b'/', 1)[-1] == b'strata_server.py'
                           or x.startswith(b'vllm.entrypoints.')
                           or x == b'sglang.launch_server' for x in args)):
                found.append({'pid': int(p.name), 'name': name})
        except FileNotFoundError:
            pass  # Process exited during enumeration.
    return found


def no_inference():
    service = subprocess.run(['systemctl', '--user', 'show', 'localai-nvfp4.service',
                              '--property=ActiveState,SubState,MainPID'],
                             capture_output=True, text=True, check=True, timeout=5)
    state = dict(line.split('=', 1) for line in service.stdout.splitlines())
    if state != {'ActiveState': 'inactive', 'SubState': 'dead', 'MainPID': '0'}:
        raise ValueError('Strata service is not fully stopped')
    active = inference_processes()
    if active:
        raise ValueError(f'Inference server is active: {active}')
    return state


def capture(argv, timeout=15):
    return subprocess.check_output([str(x) for x in argv], text=True, timeout=timeout)


def cdi_identity(driver_path, spec=Path('/var/run/cdi/nvidia.yaml')):
    """Check the generated local CDI mount; do not bind over its symlink hook."""
    lines = spec.read_text().splitlines()
    if 'kind: nvidia.com/gpu' not in lines:
        raise ValueError('Expected NVIDIA GPU CDI specification')
    for i, line in enumerate(lines):
        if line.strip() != '- hostPath: '+str(driver_path):
            continue
        block = []
        for following in lines[i+1:]:
            if following.strip().startswith('- hostPath:'):
                break
            block.append(following.strip())
        if block and block[0] == 'containerPath: '+str(driver_path) and '- ro' in block:
            return {'path': str(spec), 'sha256': dev.sha(spec),
                    'host_driver_mount': str(driver_path), 'readonly': True}
    raise ValueError('Recorded host CUDA driver is not mounted read-only by CDI')


def identity(source, build, run, driver_record):
    manifest = dev.read(build / 'manifest.json')
    native = {n: dev.sha(build / 'native' / n) for n in dev.NATIVE_PATHS}
    if native != manifest['native']:
        raise ValueError('Native checksums differ from build manifest')
    compiler_sha = source_hash(compiler_inputs(source))
    if compiler_sha != manifest['source_sha256']:
        raise ValueError('Compiler inputs differ from native build manifest')
    if dev.sha(source / 'tools/runtime.json') != manifest['settings_sha256']:
        raise ValueError('Runtime settings differ from build manifest')
    if manifest['reference_runtime_image_id'] != IMAGE:
        raise ValueError('Build did not pin the selected reference image')
    config, command, fixture = (dev.read(run / n) for n in
                                ('config.json', 'command.json', 'fixture.json'))
    config_sha = dev.sha(run / 'config.json')
    if config_sha != command['actual_config_sha256']:
        raise ValueError('Actual run config changed')
    relative = Path(config['Model']['Mesh'])
    if relative.is_absolute() or '..' in relative.parts or str(relative) != fixture['mesh']:
        raise ValueError('Expected unchanged staged relative mesh path')
    mesh = run / relative
    if mesh.stat().st_size != fixture['mesh_bytes'] or dev.sha(mesh) != fixture['mesh_sha256']:
        raise ValueError('Mesh identity changed')
    output = Path(config.get('Problem', {}).get('Output', 'postpro'))
    if output.is_absolute() or '..' in output.parts or output == Path('.'):
        raise ValueError('Diagnostic output must be a nonempty relative subdirectory')
    driver = dev.read(driver_record)
    driver_path = Path(driver['path'])
    if driver_path.stat().st_size != driver['bytes'] or dev.sha(driver_path) != driver['sha256']:
        raise ValueError('Host CUDA driver differs from recorded identity')
    return dict(source_sha256=compiler_sha, native=native, manifest_sha256=dev.sha(build/'manifest.json'),
                config_sha256=config_sha, fixture_sha256=dev.sha(run/'fixture.json'),
                command_sha256=dev.sha(run/'command.json'),
                baseline_environment=command.get('environment', {}),
                baseline_environment_sha256=environment_hash(command.get('environment', {})),
                mesh_sha256=fixture['mesh_sha256'], mesh=str(mesh.resolve()),
                mesh_relative=str(relative), postpro=str(output), driver=driver,
                driver_record_sha256=dev.sha(driver_record), cdi=cdi_identity(driver_path)), config


FEATURE_VALUES = {'PALACE_PROBE_LOCATOR': frozenset(('gslib', 'mfem')),
                  'PALACE_SINGLE_RANK_DIRECT_MESH': frozenset(('0', '1'))}


def checked_features(features):
    if features is None:
        return {}
    if (not isinstance(features, dict) or any(key not in FEATURE_VALUES or
            not isinstance(value, str) or value not in FEATURE_VALUES[key]
            for key, value in features.items())):
        raise ValueError('Only reviewed prototype feature names/values are allowed')
    return dict(features)


def host_lock_path():
    # One user/host lock across all source checkouts; never put it in a worktree.
    runtime = Path('/run/user') / str(os.getuid())
    if not runtime.is_dir():
        runtime = Path.home() / '.cache/palace'
    return runtime / 'optimization-stages-host.lock'


def make_environment(stage, threads, cpu, baseline=None, stage_trace=False, features=None):
    if type(stage_trace) is not bool:
        raise ValueError('Stage trace must be an explicit boolean')
    if stage == 'full' and (cpu or threads != 1 or stage_trace):
        raise ValueError('Full runs require GPU, OMP1 and trace OFF')
    if cpu:
        # CPU tiny is an explicit controlled diagnostic, not the archived GPU profile.
        environment = {'PALACE_LINE_BUFFERED_LOG': '1', 'MFEM_MEMORY': 'host',
                       'LD_PRELOAD': '/opt/precision/libcudss_fp32.so',
                       'PALACE_CUDA_MANAGED': '1'}
    else:
        if (not isinstance(baseline, dict) or set(baseline) != GPU_BASELINE_KEYS
                or any(not isinstance(value,str) for value in baseline.values())):
            raise ValueError('GPU baseline environment keys/values differ from reviewed whitelist')
        if baseline['LD_PRELOAD'] != '/opt/precision/libcudss_fp32.so':
            raise ValueError('Unexpected baseline adapter preload')
        environment = dict(baseline)
    if stage != 'full':
        environment['PALACE_STAGE_STOP'] = stage
    environment.update(OMP_NUM_THREADS=str(threads),
                       OPENBLAS_NUM_THREADS='1',
                       LD_LIBRARY_PATH='/opt/palace-cudss/lib:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib')
    if stage_trace:
        environment['PALACE_STAGE_TRACE'] = '1'
    environment.update(checked_features(features))
    return environment


def create_argv(plan):
    observed = plan['identity']
    native = Path(plan['build']) / 'native'
    argv = ['podman', 'create', '--pull=never', '--name', plan['name'], '--network=none',
            '--timeout', str(plan['seconds']), '--stop-timeout', '2', '--ulimit', 'core=0:0',
            '--memory', f'{plan["memory_gib"]}g', '--memory-swap', f'{plan["memory_gib"]}g',
            '--cpus', str(2 if plan['cpu'] else 8), '--device', 'nvidia.com/gpu=all',
            '--security-opt=label=disable', '-v', f'{plan["output"]}:/work:rw',
            '-v', f'{observed["mesh"]}:/work/{observed["mesh_relative"]}:ro',
            '-w', '/work']
    for name_, destination in dev.NATIVE_PATHS.items():
        argv += ['-v', f'{native / name_}:{destination}:ro']
    environment = make_environment(plan['stage'],plan['threads'],plan['cpu'],plan['identity']['baseline_environment'],plan.get('stage_trace',False),plan.get('features',{}))
    for key, value in environment.items():
        if key != 'LD_PRELOAD':
            argv += ['-e', key+'='+value]
    # The adapter requires Palace/libCEED symbols. Scope it to Palace, not env.
    argv += ['--entrypoint', '/usr/bin/env', IMAGE,
             'LD_PRELOAD='+environment['LD_PRELOAD'],
             '/opt/palace-cudss/bin/palace-x86_64.bin', 'config.json']
    return argv


def prepare(source, build, run, output, driver_record, stage, seconds=120,
            memory_gib=8, threads=1, cpu=False, stage_trace=False, features=None):
    source, build, run, output, driver_record = (Path(p).resolve() for p in
                                               (source, build, run, output, driver_record))
    validate_policy(stage, seconds, memory_gib, threads, cpu, dev.available_memory(), stage_trace)
    features = checked_features(features)
    observed, config = identity(source, build, run, driver_record)
    image = json.loads(capture(['podman', 'image', 'inspect', IMAGE]))[0]
    if image['Id'].removeprefix('sha256:') != IMAGE:
        raise ValueError('Local image identity mismatch')
    # Keep exact numerical inputs; CPU tiny override is explicitly diagnostic.
    changes = {}
    if cpu:
        for key, value in [('Device', 'CPU'), ('Backend', '/cpu/self')]:
            changes['Solver.'+key] = {'before': config['Solver'].get(key), 'after': value}
            config['Solver'][key] = value
    name = 'palace-stage-' + hashlib.sha256(str(output).encode()).hexdigest()[:12]
    # Image environment contains no PALACE flags; do not inherit host process env.
    if any(value.startswith('PALACE_') for value in image.get('Config', {}).get('Env', [])):
        raise ValueError('Image carries unexpected inherited PALACE flags')
    plan = dict(schema=1, stage=stage, diagnostic_only=stage != 'full', rf_result=False, rf_qualified=False,
                source=str(source), build=str(build), input_run=str(run), output=str(output),
                driver_record=str(driver_record), identity=observed, name=name,
                image_id=IMAGE, host_lock=str(host_lock_path()), seconds=seconds, memory_gib=memory_gib, threads=threads,
                cpu=cpu, stage_trace=stage_trace, features=features, scope='Controlled diagnostic only; CPU override/thread and quota policy are explicit, not an E2E speedup benchmark',
                configuration_changes=changes, environment=make_environment(stage,threads,cpu,observed['baseline_environment'],stage_trace,features),
                image_config_sha256=hashlib.sha256(json.dumps(image['Config'],sort_keys=True).encode()).hexdigest(),
                runner_sha256=dev.sha(Path(__file__)), helper_sha256=helper_hashes(), prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if stage == 'full':
        backend = config.get('Solver', {}).get('Backend', '')
        # CUDA's default is /gpu/cuda/magma (main.cpp ConfigureCeedBackend).
        if config.get('Solver', {}).get('Device') != 'GPU' or (backend and not backend.startswith('/gpu/cuda/')):
            raise ValueError('Full run requires unchanged GPU/CUDA config')
        plan['full_expectations'] = full_expectations(config, run/observed['postpro'])
        plan['scope'] = 'Full completion/residual checks only; RF equivalence requires a separate matched comparison'
    plan['argv'] = create_argv(plan)
    output.mkdir(parents=True, exist_ok=False)
    if stage == 'full':
        with (output/'config.json').open('xb') as stream:
            stream.write((run/'config.json').read_bytes())
    else:
        with (output/'config.json').open('x') as stream:
            json.dump(config, stream, indent=2); stream.write('\n')
    plan['staged_config_sha256'] = dev.sha(output/'config.json')
    dev.write(output/'plan.json', plan)
    return plan


def execute(plan_path):
    plan_path = Path(plan_path).resolve(); plan = dev.read(plan_path)
    output = plan_path.parent
    if Path(plan['output']) != output or any((output/name).exists() for name in ('diagnostic-result.json', 'full-result.json')):
        raise ValueError('Wrong plan location or existing execution result; no automatic retry')
    validate_policy(plan['stage'], plan['seconds'], plan['memory_gib'], plan['threads'], plan['cpu'], dev.available_memory(), plan.get('stage_trace',False))
    if plan.get('diagnostic_only') != (plan['stage'] != 'full'):
        raise ValueError('Prepared execution stage classification changed')
    if plan['argv'] != create_argv(plan) or plan['environment'] != make_environment(plan['stage'],plan['threads'],plan['cpu'],plan['identity']['baseline_environment'],plan.get('stage_trace',False),plan.get('features',{})):
        raise ValueError('Prepared command/environment changed')
    if dev.sha(Path(__file__)) != plan['runner_sha256'] or helper_hashes() != plan['helper_sha256']:
        raise ValueError('Runner or helper changed since preparation')
    shared_lock = host_lock_path()
    if plan.get('host_lock') != str(shared_lock):
        raise ValueError('Prepared host lock changed')
    shared_lock.parent.mkdir(parents=True, exist_ok=True)
    with shared_lock.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _execute(plan, output)


def gpu_sample():
    columns=('timestamp','uuid','memory.used','utilization.gpu','power.draw','clocks.sm')
    try:
        query=subprocess.run(['nvidia-smi','--query-gpu='+','.join(columns),
                              '--format=csv,noheader,nounits'],capture_output=True,
                             text=True,timeout=2,check=False)
        if query.returncode:
            return {'devices': [], 'error': query.stderr.strip()}
        devices=[]
        for row in csv.reader(query.stdout.splitlines()):
            if len(row)!=len(columns):
                raise ValueError('Unexpected nvidia-smi column count')
            def number(value):
                try: return float(value.strip())
                except ValueError: return None
            devices.append(dict(timestamp=row[0].strip(),uuid=row[1].strip(),
                                memory_used_mib=number(row[2]),utilization_percent=number(row[3]),
                                power_w=number(row[4]),sm_clock_mhz=number(row[5])))
        return {'devices':devices,'scope':'sampled global GPU; not exclusive process residency'}
    except (OSError,subprocess.TimeoutExpired,ValueError) as error:
        return {'devices':[],'error':str(error)}


def terminal_container_proof(inspection, expected_id, expected_name):
    """Disappearing cgroup is completion only with this exact owned container's exit proof."""
    state = inspection.get('State', {})
    if (not expected_id or inspection.get('Id') != expected_id or
            inspection.get('Name', '').lstrip('/') != expected_name or
            state.get('Status') not in ('exited', 'stopped') or
            type(state.get('ExitCode')) is not int or state['ExitCode'] != 0 or
            state.get('OOMKilled') is not False or type(state.get('Pid')) is not int or state['Pid'] != 0 or
            state.get('Error') not in (None, '')):
        raise ValueError('Cgroup disappeared without authoritative owned-container exit0')
    started = utc_timestamp(state.get('StartedAt', ''))
    finished = utc_timestamp(state.get('FinishedAt', ''))
    if finished < started:
        raise ValueError('Terminal container finished before it started')
    return dict(container_id=expected_id, container_name=expected_name, state=state,
                scope='Terminal exit0 observed after cgroup disappeared; attach wait and normal checks still required')


def utc_timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Missing/invalid authoritative UTC timestamp')
    parsed = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.year <= 1:
        raise ValueError('Missing/invalid authoritative UTC timestamp')
    return parsed.timestamp()


def sample_cgroup(directory, container_name, container_id):
    try:
        memory = dev.cgroup_memory(directory)
        if directory and not memory:
            # dev's generic sampler suppresses OSError; distinguish disappearance from unknown data.
            for leaf in ('memory.current', 'memory.peak', 'memory.stat'):
                (directory/leaf).stat()
            raise ValueError('Unknown live cgroup memory sample')
        if directory and int((directory/'memory.swap.max').read_text()) != 0:
            raise ValueError('Cgroup swap was not disabled')
        return memory, None
    except FileNotFoundError:
        if directory is None:
            raise
        inspection = json.loads(capture(['podman', 'inspect', container_name]))[0]
        return {}, terminal_container_proof(inspection, container_id, container_name)


# Explicit root authorization for one recorded controller end-race; not a generic retry policy.
AUTHORIZED_CGROUP_RECOVERY = {
    'original_sha256': 'f543e23205ea0a64346d78c69483bd1dc9af9b3e473d570962d33bb88d3c0cd0',
    'plan_sha256': '019b40013e92435429c100c91a35d3a6c55ca28e3bbe92018ead80b62b2c3efe',
    'events_sha256': '7c500a3b86ad60990d5717ad0e4fb054b0563e74cb3627bbf0057f8ed4505b03',
    'events_proof_sha256': '05aa09468a434c88673622248aae12edd7f3154c68979d5799595540c6997689',
    'container_id': '04180b54a7b7c1fe1f2c7519be76e2cc6da220e092b739e878791cf5cb0d966f',
    'container_name': 'palace-stage-6b67ea4d21a6',
    'failed_runner_git': '252fa4f48',
    'failed_runner_sha256': '303ea41b9bfc463fc673ff30147c4b5bf63d1b78d1148b2d98128741cf083816',
}


def check_recovery_events(events, proof, original, plan, authorization):
    """Validate the recorded exact-CID history, never current/name-only runtime status."""
    cid, name = authorization['container_id'], authorization['container_name']
    start, end = utc_timestamp(original['started_utc']), utc_timestamp(original['finished_utc'])
    if (proof.get('command_exit_code') != 0 or proof.get('plan_container_name') != name or
            proof.get('since_utc') != original['started_utc'] or
            proof.get('events_count') != len(events) or not events or plan['name'] != name):
        raise ValueError('Recorded event query proof does not match failed execution')
    command = ['podman', 'events', '--stream=false', '--filter', 'container='+name,
               '--since', original['started_utc'], '--until', proof['until_utc'], '--format', 'json']
    if proof.get('command') != command or utc_timestamp(proof['until_utc']) < end:
        raise ValueError('Recorded event query window/command differs')
    times = []
    for event in events:
        if (event.get('ID') != cid or event.get('Name') != name or
                event.get('Type') != 'container' or type(event.get('timeNano')) is not int or
                event.get('Status') not in ('create', 'init', 'start', 'attach', 'died', 'cleanup', 'remove')):
            raise ValueError('Different CID/name or unapproved/ambiguous container event')
        stamp = event['timeNano']/1e9
        if not start <= stamp <= end:
            raise ValueError('Container event outside original controller execution window')
        times.append(stamp)
    if times != sorted(times):
        raise ValueError('Container event order is not monotonic')
    statuses = [event['Status'] for event in events]
    if (statuses.count('start') != 1 or statuses.count('died') != 1 or
            statuses.count('cleanup') != 1 or statuses.count('remove') != 1 or
            not statuses.index('start') < statuses.index('died') < statuses.index('cleanup') < statuses.index('remove')):
        raise ValueError('Missing authoritative start/died/before-cleanup history')
    died = events[statuses.index('died')]
    if type(died.get('ContainerExitCode')) is not int or died['ContainerExitCode'] != 0:
        raise ValueError('Recorded native exit was not integer0')
    if proof.get('native_died_events') != [died]:
        raise ValueError('Recorded query summary differs from raw died event')
    return dict(container_id=cid, container_name=name, native_exit_code=0,
                started_event=events[statuses.index('start')], died_event=died,
                died_before_cleanup=True)


def completion_recovery_evidence(run):
    """Offline checks only. No Podman mutation, service, solver or input/result rewrites."""
    run = Path(run).resolve()
    authorization = AUTHORIZED_CGROUP_RECOVERY
    files = {'original': run/'full-result.json', 'plan': run/'plan.json',
             'events': run/'monitor-race-podman-events.jsonl',
             'events_proof': run/'monitor-race-events-proof.json'}
    hashes = {name: dev.sha(path) for name, path in files.items()}
    if any(hashes[name] != authorization[name+'_sha256'] for name in files):
        raise ValueError('Recovery is not authorized for these original/plan/events hashes')
    original, plan, proof = (dev.read(files[name]) for name in ('original', 'plan', 'events_proof'))
    if (original.get('complete') is not False or original.get('solver_executed') is not False or
            original.get('diagnostic_only') is not False or original.get('own_container_removed') is not True or
            original.get('error') != "FileNotFoundError(2, 'No such file or directory')" or
            plan.get('stage') != 'full' or plan.get('stage_trace') is not False or plan.get('cpu') or
            plan.get('threads') != 1 or plan.get('runner_sha256') != authorization['failed_runner_sha256'] or
            original.get('features') != plan.get('features')):
        raise ValueError('Original failure is not the approved cgroup end-race')
    events = [json.loads(line) for line in files['events'].read_text().splitlines() if line.strip()]
    if (proof.get('events_sha256') != hashes['events'] or
            proof.get('original_full_result_sha256') != hashes['original'] or
            Path(proof.get('events_path', '')).resolve() != files['events']):
        raise ValueError('Recorded event proof binding differs')
    terminal = check_recovery_events(events, proof, original, plan, authorization)
    archived = capture(['git', '-C', str(Path(__file__).resolve().parents[1]), 'show',
                        authorization['failed_runner_git']+':tools/stage_probe_run.py'])
    archived_sha = hashlib.sha256(archived.encode()).hexdigest()
    if archived_sha != authorization['failed_runner_sha256']:
        raise ValueError('Archived failure-context runner source differs')
    observed, config = identity(*(Path(plan[key]) for key in ('source','build','input_run','driver_record')))
    if observed != plan['identity'] or dev.sha(run/'config.json') != plan['staged_config_sha256']:
        raise ValueError('Source/native/input identity after failure differs from original plan')
    if observed['config_sha256'] != plan['staged_config_sha256']:
        raise ValueError('Recovery requires byte-identical original full-run config')
    if full_expectations(config, Path(plan['input_run'])/observed['postpro']) != plan['full_expectations']:
        raise ValueError('Original completion expectations differ')
    full = check_full(run/observed['postpro'], run/'palace.stdout.log', run/'palace.stderr.log', plan['full_expectations'])
    artifacts = [run/'config.json', run/'palace.stdout.log', run/'palace.stderr.log',
                 run/observed['postpro']/'palace.json', run/observed['postpro']/'config_resolved.json']
    artifacts.extend(sorted((run/observed['postpro']).rglob('*.csv')))
    bindings = dict(file_sha256=hashes, identity_after=observed,
                    artifact_sha256={str(path.relative_to(run)): dev.sha(path) for path in artifacts},
                    archived_runner_git=authorization['failed_runner_git'], archived_runner_sha256=archived_sha)
    return dict(bindings=bindings, terminal=terminal, full=full,
                native_elapsed_seconds=dev.read(run/observed['postpro']/'palace.json')['ElapsedTime']['Durations']['Total'],
                original_controller_elapsed_seconds=original['elapsed_seconds'])


def recover_completion(run, write=False):
    run = Path(run).resolve()
    evidence = completion_recovery_evidence(run)
    record = dict(schema=1, complete=True, diagnostic_only=False, solver_executed=True,
                  recovered_controller_failure=True, original_failure_preserved=True, rf_qualified=False,
                  scope='Authorized offline native-completion recovery only; original controller result remains FAIL',
                  wall_time_scope='Recovered controller failure: native Palace elapsed valid; original wall is not a clean successful controller-wall sample',
                  created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  recovery_runner_sha256=dev.sha(Path(__file__)), **evidence)
    if write:
        with (run/'completion-recovery.json').open('x') as stream:
            json.dump(record, stream, indent=2, allow_nan=False); stream.write('\n')
    return record


def validate_completion_recovery(run):
    """Supplemental proof is useful only if all original evidence still replays exactly."""
    run = Path(run).resolve()
    saved = dev.read(run/'completion-recovery.json')
    if (saved.get('schema') != 1 or saved.get('complete') is not True or
            saved.get('diagnostic_only') is not False or saved.get('solver_executed') is not True or
            saved.get('recovered_controller_failure') is not True or
            saved.get('original_failure_preserved') is not True or saved.get('rf_qualified') is not False):
        raise ValueError('Invalid supplemental completion recovery classification')
    fresh = completion_recovery_evidence(run)
    if any(saved.get(key) != value for key,value in fresh.items()):
        raise ValueError('Supplemental recovery binding/evidence changed')
    return saved


def _execute(plan, output):
    result = dict(diagnostic_only=plan['stage'] != 'full', rf_result=False, rf_qualified=False, solver_executed=False, complete=False,
                  stage_trace=plan.get('stage_trace',False), features=plan.get('features',{}),
                  started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    created = False; process = None; cgroup = None
    started = time.monotonic()
    try:
        validate_policy(plan['stage'], plan['seconds'], plan['memory_gib'], plan['threads'],
                        plan['cpu'], dev.available_memory(), plan.get('stage_trace',False))
        result['inference_guard'] = no_inference()
        observed, _ = identity(*(Path(plan[k]) for k in ('source','build','input_run','driver_record')))
        if observed != plan['identity'] or dev.sha(output/'config.json') != plan['staged_config_sha256']:
            raise ValueError('Prepared inputs changed before execution')
        if plan['stage'] == 'full':
            expected = full_expectations(dev.read(output/'config.json'), Path(plan['input_run'])/observed['postpro'])
            if expected != plan.get('full_expectations'):
                raise ValueError('Full completion expectations changed since preparation')
        # No implicit pull: this exact local image must still exist.
        if capture(['podman','image','inspect',plan['image_id'],'--format','{{.Id}}']).strip().removeprefix('sha256:') != plan['image_id']:
            raise ValueError('Prepared image changed')
        capture(plan['argv']); created = True
        inspection = json.loads(capture(['podman','inspect',plan['name']]))[0]
        limits = inspection['HostConfig']
        if (inspection['Image'].removeprefix('sha256:') != IMAGE
                or limits['Memory'] != plan['memory_gib']*GIB
                or limits['MemorySwap'] != limits['Memory']):
            raise ValueError('Actual image or cgroup memory/swap limits differ')
        dev.write(output/'resource-policy.json',dict(memory_gib=plan['memory_gib'],swap_gib=0,
                  cpus=2 if plan['cpu'] else 8,core_bytes=0,network='none',
                  host_reserve_gib=8,host_guard_gib=6,deadline_s=plan['seconds'],
                  image=inspection['Image'],mounts=inspection['Mounts'],hostconfig=limits))
        with (output/'palace.stdout.log').open('x') as stdout, (output/'palace.stderr.log').open('x') as stderr, (output/'telemetry.jsonl').open('x') as telemetry:
            process = subprocess.Popen(['podman','start','--attach',plan['name']],stdout=stdout,stderr=stderr)
            solve_start = time.monotonic()
            while process.poll() is None:
                elapsed = time.monotonic()-solve_start
                free = dev.available_memory()
                if free < 6*GIB or elapsed > plan['seconds']+10:
                    raise TimeoutError('Host memory guard or diagnostic deadline')
                if cgroup is None:
                    state = json.loads(capture(['podman','inspect',plan['name']]))[0]['State']
                    if state.get('Pid'):
                        cgroup = dev.container_memory_path(state['Pid'])
                memory, terminal = sample_cgroup(cgroup, plan['name'], inspection.get('Id'))
                if terminal is not None:
                    result['monitor_terminal_state_proof'] = terminal
                    dev.write(output/'monitor-terminal-state.json', terminal)
                    break
                telemetry.write(json.dumps(dict(unix_s=time.time(),elapsed_s=elapsed,
                                                host_available_bytes=free,cgroup=memory,
                                                gpu=None if plan['cpu'] else gpu_sample()))+'\n');telemetry.flush()
                time.sleep(.5)
            result['exit_code'] = process.wait(timeout=5)
        state = json.loads(capture(['podman','inspect',plan['name']]))[0]['State']
        dev.write(output/'container-state.json',state)
        result['container_started'] = state.get('StartedAt') not in (None, '', '0001-01-01T00:00:00Z')
        result['palace_main_marker_seen'] = 'PALACE_LOG_BUFFERING: stdout=line' in (output/'palace.stderr.log').read_text()
        if result['exit_code'] != 0 or state.get('OOMKilled'):
            if not result['container_started']:
                raise ValueError('Container startup failed before native execution')
            if not result['palace_main_marker_seen']:
                raise ValueError('Entrypoint/loader failed before Palace main marker')
            raise ValueError('Native diagnostic failed or OOM')
        observed_after, _ = identity(*(Path(plan[k]) for k in ('source','build','input_run','driver_record')))
        if observed_after != observed:
            raise ValueError('Input/native identity changed during execution')
        if plan['stage'] == 'full':
            result['full'] = check_full(output/observed['postpro'],output/'palace.stdout.log',output/'palace.stderr.log',plan['full_expectations'])
            result['solver_executed'] = result['full']['solver_executed']
        else:
            result['diagnostic'] = check_diagnostic(output/observed['postpro'],output/'palace.stdout.log',plan['stage'])
        result['complete'] = True
    except BaseException as error:
        result['error'] = repr(error)
        raise
    finally:
        cleanup_error = None
        try:
            if created:
                subprocess.run(['podman','rm','--force',plan['name']],stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,timeout=8,check=True)
                if process is not None:
                    process.wait(timeout=8)
                result['own_container_removed'] = True
        except Exception as error:
            cleanup_error = error
            result.update(complete=False,cleanup_error=repr(error))
        finally:
            result['elapsed_seconds'] = time.monotonic()-started
            result['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            dev.write(output/('full-result.json' if plan['stage'] == 'full' else 'diagnostic-result.json'),result)
        if cleanup_error is not None and 'error' not in result:
            raise RuntimeError('Diagnostic cleanup failed') from cleanup_error
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('prepare')
    for key in ('source','build','run','output','driver-record'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--stage',choices=['preprocess','operators','full'],required=True)
    p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--memory-gib',type=int,default=8)
    p.add_argument('--threads',type=int,default=1)
    p.add_argument('--cpu',action='store_true')
    p.add_argument('--stage-trace',action='store_true',help='Opt-in inclusive host phase trace; does not change numerical config')
    p.add_argument('--probe-locator',choices=('gslib','mfem'),help='Explicit experimental locator; default leaves production choice unchanged')
    p.add_argument('--direct-mesh',choices=('0','1'),help='Explicit experimental rank-one mesh distribution')
    sub.add_parser('execute').add_argument('plan',type=Path)
    recovery = sub.add_parser('recover-completion', help='Offline approved cgroup end-race proof; default read-only preview')
    recovery.add_argument('--run', type=Path, required=True)
    recovery.add_argument('--write', action='store_true', help='Write a new exclusive supplemental completion-recovery.json; preserve original FAIL')
    args=parser.parse_args()
    if args.action == 'recover-completion':
        print(json.dumps(recover_completion(args.run, args.write), indent=2, allow_nan=False))
        return
    features = {}
    if args.action == 'prepare':
        if args.probe_locator is not None:
            features['PALACE_PROBE_LOCATOR'] = args.probe_locator
        if args.direct_mesh is not None:
            features['PALACE_SINGLE_RANK_DIRECT_MESH'] = args.direct_mesh
    result=execute(args.plan) if args.action=='execute' else prepare(args.source,args.build,args.run,args.output,args.driver_record,args.stage,args.seconds,args.memory_gib,args.threads,args.cpu,args.stage_trace,features)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
