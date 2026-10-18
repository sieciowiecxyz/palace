#!/usr/bin/env python3
"""Pinned Nsight CLI and bounded in-RAM trace analysis; no solver data offload."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT/'build/nsight-2026.5.1'
URL = 'https://developer.nvidia.com/downloads/assets/tools/secure/nsight-systems/2026_5/nsightsystems-linux-cli-public-2026.5.1.161-3889610.deb'
DIGEST = '61829db6392e5c293ada1319df86a97c3356bc810335a1975cb551fcfe3eca08'
BINARY = 'opt/nvidia/nsight-systems-cli/2026.5.1/target-linux-x64/nsys'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verified_tool():
    metadata = json.loads((TOOL/'manifest.json').read_text())
    if (metadata['download_sha256'] != DIGEST or metadata['binary'] != BINARY or
            metadata['binary_sha256'] != sha(TOOL/BINARY)):
        raise ValueError('Profiler tool manifest mismatch; run tools/nsight_window.py setup')
    return metadata


def setup():
    if (TOOL/'manifest.json').exists():
        verified_tool()
        print('Nsight CLI unchanged: cached tool retained')
        return
    TOOL.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='palace-nsys-install-', dir='/dev/shm') as temporary:
        archive = Path(temporary)/'tool.deb'
        started, total = time.monotonic(), 0
        with urllib.request.urlopen(URL, timeout=30) as source, archive.open('wb') as target:
            while chunk := source.read(1024*1024):
                total += len(chunk)
                if total > 250*1024**2 or time.monotonic()-started > 90:
                    raise ValueError('Profiler download budget exceeded')
                target.write(chunk)
        if sha(archive) != DIGEST:
            raise ValueError('Profiler download SHA mismatch')
        # Extract data only; never execute package install scripts or change the OS.
        pack = subprocess.Popen(['ar', 'p', str(archive), 'data.tar.gz'], stdout=subprocess.PIPE)
        try:
            subprocess.run(['tar', '-xzf', '-', '-C', str(TOOL)], stdin=pack.stdout, check=True)
        finally:
            pack.stdout.close()
            code = pack.wait()
        if code:
            raise ValueError('Profiler package extraction failed')
        metadata = dict(version='2026.5.1.161', url=URL, download_bytes=total,
                        download_sha256=DIGEST, binary=BINARY, binary_sha256=sha(TOOL/BINARY))
        (TOOL/'manifest.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(verified_tool(), indent=2))


def parse_window(value):
    if not isinstance(value, str) or not re.fullmatch(r'(0|[1-9]\d*):([1-9]\d*)', value):
        raise ValueError('Profile window requires FIRST:COUNT (FIRST=0..32, COUNT=1..8)')
    first, count = map(int, value.split(':'))
    if not 0 <= first <= 32 or not 1 <= count <= 8:
        raise ValueError('Profile window requires FIRST=0..32 and COUNT=1..8')
    return first, count


def prepare(value, output):
    first, count = parse_window(value)
    metadata = verified_tool()
    ram = Path(tempfile.mkdtemp(prefix='palace-nsys-', dir='/dev/shm'))
    (ram/'tmp').mkdir()
    info = dict(first=first, count=count, ram_directory=str(ram), tool=metadata,
                scope='Intentional partial profiling window; never an RF/accuracy run')
    (output/'profile-input.json').write_text(json.dumps(info, indent=2)+'\n')
    return info


def arguments(profile):
    return ['profile', '--trace=cuda-sw,nvtx', '--sample=none', '--cpuctxsw=none',
            '--cuda-um-cpu-page-faults=false', '--cuda-um-gpu-page-faults=false',
            '--kill=none', '--wait=all',
            '--export=sqlite', '--output=/profile/window', '--force-overwrite=false']


def target_pid(root, proc=Path('/proc')):
    """Only inspect this container's process subtree, never unrelated user apps."""
    pending, seen = [root], set()
    while pending and len(seen) < 128:
        pid = pending.pop()
        if pid in seen: continue
        seen.add(pid)
        try:
            command = (proc/str(pid)/'cmdline').read_bytes().split(b'\0', 1)[0]
            executable = proc/str(pid)/'exe'
            if (Path(command.decode()).name == 'palace-x86_64.bin' or
                    (executable.is_symlink() and executable.readlink().name == 'palace-x86_64.bin')):
                return pid
            for children in (proc/str(pid)/'task').glob('*/children'):
                pending += [int(x) for x in children.read_text().split()]
        except (OSError, UnicodeError, ValueError):
            continue
    return None


def sqlite_summary(path):
    with sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro', uri=True) as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {'CUPTI_ACTIVITY_KIND_KERNEL', 'CUPTI_ACTIVITY_KIND_RUNTIME', 'NVTX_EVENTS', 'StringIds'}
        if not required <= tables:
            raise ValueError('Profiler schema missing CUDA/runtime/NVTX records')
        out = dict(tables=sorted(tables), scope='Totals cover entire bounded process; phase attribution selects Krylov sample by CPU launch thread/time. GPU sums may overlap.')
        out['kernel_count'], out['kernel_sum_seconds'] = db.execute(
            'SELECT count(*),coalesce(sum(end-start),0)*1e-9 FROM CUPTI_ACTIVITY_KIND_KERNEL').fetchone()
        out['top_kernels'] = [dict(name=n, calls=c, seconds=s) for n,c,s in db.execute(
            'SELECT s.value,count(*),sum(k.end-k.start)*1e-9 FROM CUPTI_ACTIVITY_KIND_KERNEL k '
            'JOIN StringIds s ON s.id=k.demangledName GROUP BY k.demangledName ORDER BY 3 DESC LIMIT 20')]
        ranges = [(a,b,tid,n.strip()) for a,b,tid,n in db.execute(
            'SELECT n.start,n.end,n.globalTid,coalesce(n.text,s.value) FROM NVTX_EVENTS n '
            'LEFT JOIN StringIds s ON s.id=n.textId WHERE n.end IS NOT NULL AND n.end>=n.start') if n]
        windows = [r for r in ranges if r[3]=='Krylov sample']
        selected = [r for r in ranges if any(w[2]==r[2] and w[0]<=r[0] and r[1]<=w[1] for w in windows)]
        out['window_count'] = len(windows)
        out['nvtx_ranges'] = [dict(name=n, calls=sum(r[3]==n for r in selected),
                                  inclusive_seconds=sum((r[1]-r[0])*1e-9 for r in selected if r[3]==n))
                              for n in sorted({r[3] for r in selected})]
        # Nsight serialized process bits occupy globalTid/globalPid above the low 24 bits.
        launches = {(c,tid//16777216):(t,tid) for c,tid,t in db.execute(
            'SELECT correlationId,globalTid,start FROM CUPTI_ACTIVITY_KIND_RUNTIME')}
        phases = defaultdict(lambda: dict(calls=0, seconds=0.0))
        for corr,pid,duration in db.execute('SELECT correlationId,globalPid,end-start FROM CUPTI_ACTIVITY_KIND_KERNEL'):
            launch = launches.get((corr,pid//16777216))
            name = 'unmatched CUDA launch'
            if launch:
                t,tid = launch
                enclosing = [r for r in selected if r[2]==tid and r[0]<=t<=r[1]]
                name = min(enclosing,key=lambda r:r[1]-r[0])[3] if enclosing else 'outside NVTX ranges'
            phases[name]['calls'] += 1
            phases[name]['seconds'] += duration*1e-9
        out['kernel_seconds_by_launch_phase'] = dict(phases)
        out['copies'] = []
        if 'CUPTI_ACTIVITY_KIND_MEMCPY' in tables:
            columns = {r[1] for r in db.execute('PRAGMA table_info(CUPTI_ACTIVITY_KIND_MEMCPY)')}
            keys = ['copyKind'] + [x for x in ['srcKind','dstKind','migrationCause'] if x in columns]
            query = 'SELECT '+','.join(keys)+',count(*),sum(bytes),sum(end-start)*1e-9 FROM CUPTI_ACTIVITY_KIND_MEMCPY GROUP BY '+','.join(keys)
            out['copies'] = [dict(zip(keys+['calls','bytes','seconds'],row)) for row in db.execute(query)]
        # Preserve relevant labels, never guess numeric enum values for UVM.
        out['cuda_enums'] = {t: [dict(zip([r[1] for r in db.execute('PRAGMA table_info('+t+')')],row))
                                for row in db.execute('SELECT * FROM '+t)]
                             for t in ['ENUM_CUDA_MEM_KIND','ENUM_CUDA_MEMCPY_OPER','ENUM_CUDA_UNIF_MEM_MIGRATION'] if t in tables}
        out['diagnostic_tables'] = [t for t in sorted(tables) if any(k in t.upper() for k in ['DIAGNOSTIC','ERROR','WARNING','DROPPED'])]
        out['diagnostics'] = {t: [dict(zip([c[1] for c in db.execute('PRAGMA table_info('+t+')')],row)) for row in db.execute('SELECT * FROM '+t)]
                              for t in out['diagnostic_tables']}
        if out['kernel_count'] == 0 or not math.isfinite(out['kernel_sum_seconds']):
            raise ValueError('Empty/invalid kernel capture')
        return out


def collect(profile, output):
    ram = Path(profile['ram_directory'])
    report = dict(complete=False, scope=profile['scope'])
    try:
        text = (output/'palace.log').read_text(errors='replace')
        first,count = profile['first'],profile['count']
        report['window_markers_passed'] = all(text.count(f'PALACE_PROFILE_WINDOW: {event} first={first} count={count}')==1 for event in ['begin','end'])
        report['clean_stop_passed'] = text.count('PALACE_PROFILE_STOP: clean diagnostic stop; no RF qualification') == 1
        loss = re.compile(r'data.{0,20}lost|dropped.{0,15}events|not all.{0,20}events.{0,30}collected|incompatibility.{0,30}driver|older version.{0,20}cupti|unsupported cuda|does not support cuda', re.I)
        report['collector_warnings'] = [line for line in text.splitlines() if loss.search(line)]
        report['files'] = {p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in ram.glob('window.*') if p.is_file()}
        native = ram/'window.nsys-rep'
        if native.exists() and native.stat().st_size <= 64*1024**2:
            shutil.copy2(native, output/'profile.nsys-rep')  # Ordinary final diagnostic result.
        sql = ram/'window.sqlite'
        if sql.exists(): report['summary'] = sqlite_summary(sql)
        for rows in report.get('summary',{}).get('diagnostics',{}).values():
            for row in rows:
                report['collector_warnings'] += [v for v in row.values() if isinstance(v,str) and loss.search(v)]
                if isinstance(row.get('severity'),int) and row['severity'] >= 2:
                    report['collector_warnings'].append(str(row.get('text',row)))
        report['collector_warnings'] = sorted(set(report['collector_warnings']))
        calls = {r['name']:r['calls'] for r in report.get('summary',{}).get('nvtx_ranges',[])}
        report['iteration_coverage_passed'] = (report.get('summary',{}).get('window_count')==1 and calls.get('Preconditioner')==count and calls.get('Krylov orthogonalization')==count)
        report['complete'] = bool(report['window_markers_passed'] and report['clean_stop_passed'] and not report['collector_warnings']
                                  and report['iteration_coverage_passed'] and 'summary' in report)
        return report
    finally:
        (output/'profile-summary.json').write_text(json.dumps(report,indent=2)+'\n')
        shutil.rmtree(ram)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup','check'])
    args = parser.parse_args()
    if args.action=='setup': setup()
    else: print(json.dumps(verified_tool(), indent=2))
