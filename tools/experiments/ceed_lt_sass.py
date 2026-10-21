"""Read-only executed-symbol/SASS audit of the exact pinned runtime cuBLASLt.

No GPU work or counters. Temporary library copy is in RAM, never SSD.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dev
from ceed_tensor_probe import trace_summary


def run(trace,output,library_name='cublasLt'):
    trace=Path(trace).resolve();output=Path(output).resolve()
    command=dev.read(trace/'command.json');profile=dev.read(trace/'root-reanalysis.json')
    if not profile['complete'] or profile['source_profile_sha256']!=dev.sha(trace/'profile.sqlite'):
        raise ValueError('Require verified actual kernel capture, not unexecuted symbols')
    summary=trace_summary(trace/'profile.sqlite')
    if summary['diagnostic_issues']:raise ValueError('Trace contains diagnostic issues')
    runtime=dev.read(dev.SETTINGS)['runtime_image']
    if runtime not in command['argv'] or command['manifest']['recipe']['runtime_image_id'].removeprefix('sha256:')!=runtime.removeprefix('sha256:'):
        raise ValueError('Runtime identity differs from trace')
    symbols=[k for k in summary['kernels'] if 'tensorop_s1688gemm_128x256_16x3_' in k['demangled']]
    if len(symbols)!=2 or any(k['calls']<=0 for k in symbols):raise ValueError('Expected two actually launched target symbols')
    tool=Path('/opt/cuda/bin/cuobjdump').resolve()
    if not tool.is_file() or shutil.disk_usage('/dev/shm').free<4*1024**3:
        raise ValueError('Require cuobjdump and4GiB free RAM filesystem')
    output.mkdir(parents=True,exist_ok=False)
    report=dict(complete=False,runtime_image=runtime,trace_profile_sha256=dev.sha(trace/'profile.sqlite'),
        tool=str(tool),tool_sha256=dev.sha(tool),tool_version=dev.capture([str(tool),'--version']),
        scope='Actually launched kernel symbols plus static instruction implementation; not executed instruction counters or whole-solver speedup.',rows=[])
    name='palace-lt-static-'+dev.sha(trace/'profile.sqlite')[:12]
    if subprocess.run(['podman','container','exists',name]).returncode==0:raise ValueError('Audit container already exists')
    try:
        with tempfile.TemporaryDirectory(prefix='palace-lt-sass-',dir='/dev/shm') as temporary:
            dev.command(['podman','create','--name',name,'--network=none','--read-only','--entrypoint','/bin/true',runtime],stdout=subprocess.DEVNULL,timeout=30)
            source='/usr/local/cuda-12.9/targets/x86_64-linux/lib/lib'+library_name+'.so.12.9.1.4'
            library=Path(temporary)/('lib'+library_name+'.so')
            dev.command(['podman','cp',name+':'+source,str(library)],timeout=45)
            report.update(library_path=source,library_bytes=library.stat().st_size,library_sha256=dev.sha(library))
            for index,kernel in enumerate(symbols):
                target=output/f'kernel-{index}.sass';stderr=output/f'kernel-{index}.stderr'
                argv=['prlimit','--as=8589934592','--cpu=50','--fsize=16777216','--',str(tool),
                    '--gpu-architecture','sm_120','--function',kernel['mangled'],'--dump-sass',str(library)]
                with target.open('w') as out,stderr.open('w') as err:
                    result=subprocess.run(argv,stdout=out,stderr=err,timeout=60)
                text=target.read_text()
                instructions=[line.strip() for line in text.splitlines() if re.search(r'\b(?:HMMA|DMMA|IMMA|MMA)[.\s]',line)]
                row=dict(kernel,argv=argv,exit_code=result.returncode,sass_file=target.name,
                    sass_sha256=dev.sha(target),sass_bytes=target.stat().st_size,
                    tensor_instruction_lines=instructions,
                    matched_exact_symbol=('Function : '+kernel['mangled']) in text)
                report['rows'].append(row)
            report['complete']=all(r['exit_code']==0 and r['matched_exact_symbol'] and r['tensor_instruction_lines'] for r in report['rows'])
    finally:
        if subprocess.run(['podman','container','exists',name]).returncode==0:
            dev.command(['podman','rm',name],stdout=subprocess.DEVNULL,timeout=15)
        dev.write(output/'result.json',report)
    print(json.dumps({k:report[k] for k in ['complete','scope']}))
    if not report['complete']:raise ValueError('No exact SM120 tensor instruction evidence; inspect saved output')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--library',choices=['cublasLt','cublas'],default='cublasLt')
    args=parser.parse_args();run(args.trace,args.output,args.library)
