#!/usr/bin/env python3
"""Prepare/execute one bounded M0 native diagnostic; never claim an RF result.

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
from pathlib import Path
import subprocess
import time

import dev
from stage_operator_reference import compiler_inputs, source_hash
from stage_preprocess import check_diagnostic

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
            'stage_preprocess': dev.sha(Path(check_diagnostic.__code__.co_filename))}


def validate_policy(stage, seconds, memory_gib, threads, cpu, available):
    if stage not in ('preprocess', 'operators'):
        raise ValueError('Only diagnostic stages preprocess/operators are permitted')
    if type(seconds) is not int or type(memory_gib) is not int or not 1 <= seconds <= 300 or not 4 <= memory_gib <= 70:
        raise ValueError('Deadline must be 1..300 s and memory budget 4..70 GiB')
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


def make_environment(stage, threads, cpu, baseline=None):
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
    environment.update(PALACE_STAGE_STOP=stage, OMP_NUM_THREADS=str(threads),
                       OPENBLAS_NUM_THREADS='1',
                       LD_LIBRARY_PATH='/opt/palace-cudss/lib:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib')
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
    environment = make_environment(plan['stage'],plan['threads'],plan['cpu'],plan['identity']['baseline_environment'])
    for key, value in environment.items():
        if key != 'LD_PRELOAD':
            argv += ['-e', key+'='+value]
    # The adapter requires Palace/libCEED symbols. Scope it to Palace, not env.
    argv += ['--entrypoint', '/usr/bin/env', IMAGE,
             'LD_PRELOAD='+environment['LD_PRELOAD'],
             '/opt/palace-cudss/bin/palace-x86_64.bin', 'config.json']
    return argv


def prepare(source, build, run, output, driver_record, stage, seconds=120,
            memory_gib=8, threads=1, cpu=False):
    source, build, run, output, driver_record = (Path(p).resolve() for p in
                                               (source, build, run, output, driver_record))
    validate_policy(stage, seconds, memory_gib, threads, cpu, dev.available_memory())
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
    plan = dict(schema=1, stage=stage, diagnostic_only=True, rf_result=False,
                source=str(source), build=str(build), input_run=str(run), output=str(output),
                driver_record=str(driver_record), identity=observed, name=name,
                image_id=IMAGE, seconds=seconds, memory_gib=memory_gib, threads=threads,
                cpu=cpu, scope='Controlled diagnostic only; CPU override/thread and quota policy are explicit, not an E2E speedup benchmark',
                configuration_changes=changes, environment=make_environment(stage,threads,cpu,observed['baseline_environment']),
                image_config_sha256=hashlib.sha256(json.dumps(image['Config'],sort_keys=True).encode()).hexdigest(),
                runner_sha256=dev.sha(Path(__file__)), helper_sha256=helper_hashes(), prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    plan['argv'] = create_argv(plan)
    output.mkdir(parents=True, exist_ok=False)
    with (output/'config.json').open('x') as stream:
        json.dump(config, stream, indent=2); stream.write('\n')
    plan['staged_config_sha256'] = dev.sha(output/'config.json')
    dev.write(output/'plan.json', plan)
    return plan


def execute(plan_path):
    plan_path = Path(plan_path).resolve(); plan = dev.read(plan_path)
    output = plan_path.parent
    if Path(plan['output']) != output or (output/'diagnostic-result.json').exists():
        raise ValueError('Wrong plan location or existing execution result; no automatic retry')
    if plan['argv'] != create_argv(plan) or plan['environment'] != make_environment(plan['stage'],plan['threads'],plan['cpu'],plan['identity']['baseline_environment']):
        raise ValueError('Prepared command/environment changed')
    if dev.sha(Path(__file__)) != plan['runner_sha256'] or helper_hashes() != plan['helper_sha256']:
        raise ValueError('Runner or helper changed since preparation')
    with (Path(plan['source'])/'build/optimization-stages-host.lock').open('a') as lock:
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


def _execute(plan, output):
    result = dict(diagnostic_only=True, rf_result=False, complete=False,
                  started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    created = False; process = None; cgroup = None
    started = time.monotonic()
    try:
        validate_policy(plan['stage'], plan['seconds'], plan['memory_gib'], plan['threads'],
                        plan['cpu'], dev.available_memory())
        result['inference_guard'] = no_inference()
        observed, _ = identity(*(Path(plan[k]) for k in ('source','build','input_run','driver_record')))
        if observed != plan['identity'] or dev.sha(output/'config.json') != plan['staged_config_sha256']:
            raise ValueError('Prepared inputs changed before execution')
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
                memory = dev.cgroup_memory(cgroup)
                if cgroup and int((cgroup/'memory.swap.max').read_text()) != 0:
                    raise ValueError('Cgroup swap was not disabled')
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
            dev.write(output/'diagnostic-result.json',result)
        if cleanup_error is not None and 'error' not in result:
            raise RuntimeError('Diagnostic cleanup failed') from cleanup_error
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('prepare')
    for key in ('source','build','run','output','driver-record'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--stage',choices=['preprocess','operators'],required=True)
    p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--memory-gib',type=int,default=8)
    p.add_argument('--threads',type=int,default=1)
    p.add_argument('--cpu',action='store_true')
    sub.add_parser('execute').add_argument('plan',type=Path)
    args=parser.parse_args()
    result=execute(args.plan) if args.action=='execute' else prepare(args.source,args.build,args.run,args.output,args.driver_record,args.stage,args.seconds,args.memory_gib,args.threads,args.cpu)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
