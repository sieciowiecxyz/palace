#!/usr/bin/env python3
"""Interrupt our own runner after real container creation, before create returns.

A private PATH shim delays only the return from successful `podman create`.
The solver never starts. No system PATH, image, application or permission changes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dev


def run(output):
    output = output.resolve(); output.mkdir(parents=True, exist_ok=False)
    real = shutil.which('podman'); work = output/'run'
    name = 'palace-run-'+hashlib.sha256(str(work).encode()).hexdigest()[:12]
    if subprocess.run([real, 'container', 'exists', name]).returncode != 1:
        raise ValueError('Refuse to use a pre-existing container name')
    marker = output/'created-probe.json'; shimdir = output/'shim'; shimdir.mkdir()
    shim = shimdir/'podman'
    shim.write_text(f'''#!{sys.executable}
import json,os,subprocess,sys,time
from pathlib import Path
real={real!r}
if len(sys.argv)>1 and sys.argv[1]=='create':
    result=subprocess.run([real,*sys.argv[1:]])
    if result.returncode==0:
        Path({str(marker)!r}).write_text(json.dumps(dict(pid=os.getpid(),monotonic=time.monotonic(),birth=Path('/proc/self/stat').read_text().split()[21])))
        time.sleep(3)
    sys.exit(result.returncode)
os.execv(real,[real,*sys.argv[1:]])
''')
    shim.chmod(0o700)
    env = dict(os.environ, PATH=str(shimdir)+os.pathsep+os.environ['PATH'])
    args = [sys.executable, str(dev.ROOT/'tools/dev.py'), 'run', 'coax-tiny', str(work),
            '--seconds', '60', '--basis', 'fp64']
    started = time.monotonic()
    with (output/'launcher.log').open('w') as log:
        process = subprocess.Popen(args, cwd=dev.ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        dev.write(output/'job.json', dict(pid=process.pid, argv=args))
        try:
            while not marker.exists() and process.poll() is None and time.monotonic()-started < 20:
                time.sleep(.02)
            if not marker.exists() or process.poll() is not None:
                raise ValueError('Did not reach live container-create probe')
            probe = dev.read(marker)
            before = dev.read_output([real, 'inspect', name])[0]['State']
            if before['Status'] != 'created' or before['Running'] or before['Pid']:
                raise ValueError('Probe failed to isolate pre-start phase')
            process.send_signal(signal.SIGTERM)
            code = process.wait(timeout=20)
            removed_by_runner = subprocess.run([real, 'container', 'exists', name]).returncode == 1
        except BaseException:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM); process.wait(timeout=20)
            raise
        finally:
            # The private shim has a bounded3s delay, no subsequent create/action.
            if marker.exists():
                probe = dev.read(marker)
                time.sleep(max(0, 3.2-(time.monotonic()-probe['monotonic'])))
            subprocess.run([real, 'rm', '--force', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = dev.read(work/'result.json')
    absent = subprocess.run([real, 'container', 'exists', name]).returncode == 1
    passed = (code == 130 and not result['complete'] and result['interrupted']
              and result.get('interrupted_signal') == 'SIGTERM' and result.get('launch_phase') == 'creating'
              and removed_by_runner and absent and not (work/'palace.stdout.log').exists())
    receipt = dict(passed=bool(passed), runner_exit_code=code, result=result,
                   before_signal=before, removed_by_runner_before_harness_cleanup=removed_by_runner,
                   container_absent=absent,
                   elapsed_seconds=time.monotonic()-started,
                   scope='Own controlled pre-start SIGTERM; real container created but solver never started')
    dev.write(output/'qualification.json', receipt)
    if not passed:
        raise ValueError('Pre-start SIGTERM/cleanup check failed')
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(run(args.output), indent=2))
