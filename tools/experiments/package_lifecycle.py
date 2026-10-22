#!/usr/bin/env python3
"""Bounded deadline/SIGTERM checks of our own tiny packaged processes only."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dev


def check(bundle, output, mode, timeout_control=None):
    work = output/mode
    args = [sys.executable, str(bundle/'reproduce.py'), str(work), '--profile', 'memory',
            '--seconds', '1' if mode == 'deadline' else '60']
    started = time.monotonic(); sent = False
    with (output/f'{mode}.launcher.log').open('w') as log:
        process = subprocess.Popen(args, cwd='/tmp', stdout=log, stderr=subprocess.STDOUT)
        dev.write(output/f'{mode}.job.json', dict(pid=process.pid, argv=args))
        try:
            if mode == 'sigterm':
                # Only after target solver is live AND the runner cleanup scope is
                # active. Popen owns this PID; never select another process by name.
                while process.poll() is None and time.monotonic()-started < 30:
                    stdout = work/'palace.stdout.log'
                    if stdout.exists() and 'PALACE_NATIVE_COMPLEX_COARSE:' in stdout.read_text(errors='replace'):
                        process.send_signal(signal.SIGTERM); sent = True; break
                    time.sleep(.1)
            code = process.wait(timeout=35)
        except BaseException:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=45)  # Container itself retains its60s limit.
            raise
    result = dev.read(work/'result.json')
    metadata = dev.read(work/'command.json')
    command = metadata['argv']
    container = command[command.index('--name')+1]
    absent = subprocess.run(['podman', 'container', 'exists', container]).returncode == 1
    passed = code != 0 and result['complete'] is False and absent
    if mode == 'sigterm':
        passed = passed and sent and code == 130 and result.get('interrupted') is True and result.get('interrupted_signal') == 'SIGTERM'
    else:
        state = dev.read(work/'container-state.json')
        state = state.get('State', state)
        duration = (datetime.fromisoformat(state['FinishedAt'].replace('Z','+00:00'))
                    - datetime.fromisoformat(state['StartedAt'].replace('Z','+00:00'))).total_seconds()
        passed = passed and ('--timeout' in command and command[command.index('--timeout')+1] == '1')
        recognized = state['ExitCode'] in (137,143)
        if state['ExitCode'] == -1 and timeout_control is not None:
            witness = dev.read(timeout_control)
            a = witness['argv']
            recognized = (witness['podman_version'] == dev.capture(['podman','version','--format','{{.Client.Version}}'])
                          and witness['state']['ExitCode'] == -1 and witness['returncode'] == 255
                          and not witness['state']['OOMKilled'] and .5 <= witness['elapsed_seconds'] <= 10
                          and a[a.index('--timeout')+1] == '1' and a[a.index('--entrypoint')+1] == 'sleep'
                          and a[-1] == '30' and a[-2] == metadata['runtime_image'] and result['exit_code'] == 255)
        passed = passed and recognized and not state['OOMKilled'] and .5 <= duration <= 10
    receipt = dict(passed=bool(passed), mode=mode, exit_code=code, signal_sent=sent,
                   elapsed_seconds=time.monotonic()-started, result=result,
                   container=container, container_absent=absent,
                   timeout_control=str(timeout_control) if mode == 'deadline' and timeout_control else None,
                   scope='Expected interrupted execution, never a qualified RF result')
    dev.write(output/f'{mode}-check.json', receipt)
    if not passed:
        raise ValueError(f'{mode} cleanup/deadline check failed; see {output}')
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--timeout-control', type=Path, help='Independent same-image CPU sleep timeout witness for conmon -1/attach255 semantics')
    args = p.parse_args(); output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    results = [check(args.bundle.resolve(), output, mode, args.timeout_control) for mode in ['deadline', 'sigterm']]
    dev.write(output/'qualification.json', dict(passed=True, checks=results))
    print(json.dumps(results, indent=2))
