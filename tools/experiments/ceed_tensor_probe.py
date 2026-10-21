"""Cached isolated libCEED/MFEM basis vs cuBLAS FP64/FP32/TF32 action probe."""
import argparse
import fcntl
import math
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dev

BASE=dev.ROOT/'build/m6-ceed-tensor'
HERE=Path(__file__).resolve().parent
SOURCES=[HERE/'ceed_lt_probe.hpp',HERE/'ceed_tensor_probe.cpp',HERE/'ceed_tensor_probe.cu',dev.ROOT/'tools/adapter/ceed_compensated.cuh',dev.ROOT/'tools/adapter/ceed_fused.cuh']
PROGRAM=BASE/'ceed-tensor-probe'
FLAGS=['-std=c++17','-O2','-I/src/palace/palace','-I/opt/view/include',
       '-I/usr/local/cuda/include','-I/opt/cudss/include']
LINK=['-L/src/palace/build/sm120/native','-lpalace','-L/opt/view/lib','-lmfem','-lHYPRE','-lfmt','-lceed',
      '-L/usr/local/cuda/lib64','-lcublas','-lcublasLt','-lcudart',
      '-L/usr/local/cuda/lib64/stubs','-Wl,--no-as-needed','-lcuda','-Wl,--as-needed',
      '-Wl,-rpath,/native:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib:/usr/local/cuda/lib64']


def recipe():
    native=dev.verified_build()
    return dict(sources={p.name:dev.sha(p) for p in SOURCES},
        native=native['native'],builder_image_id=native['builder_image_id'],
        runtime_image_id=native['runtime_base_id'],architecture=dev.read(dev.SETTINGS)['architecture'],
        flags=FLAGS,link=LINK)


def verified():
    manifest=dev.read(BASE/'manifest.json')
    if manifest['recipe']!=recipe() or manifest['binary_sha256']!=dev.sha(PROGRAM):
        raise ValueError('CEED tensor probe stale; rebuild with cache')
    return manifest


def build():
    dev.require_host_memory();BASE.mkdir(parents=True,exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if PROGRAM.exists() and (BASE/'manifest.json').exists():
            try:verified()
            except ValueError:pass
            else:print('CEED tensor probe unchanged; cache retained');return
        current=recipe();started=time.monotonic();settings=dev.read(dev.SETTINGS)
        name=dev.builder(settings);target='/tmp/palace-ceed-tensor-probe'
        try:
            with (BASE/'build.log').open('w') as log:
                def execute(argv):
                    remaining=120-(time.monotonic()-started)
                    if remaining<=0:raise TimeoutError('CEED probe build exceeded120s')
                    dev.command(argv,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
                execute(['podman','exec',name,'ccache','/opt/view/bin/mpicxx',*FLAGS,
                    '-c','/src/palace/tools/experiments/ceed_tensor_probe.cpp','-o',target+'.o'])
                execute(['podman','exec',name,'ccache','/usr/local/cuda/bin/nvcc','-std=c++17','-O2',
                    '-arch=sm_'+settings['architecture'],'-c','/src/palace/tools/experiments/ceed_tensor_probe.cu','-o',target+'-cuda.o'])
                execute(['podman','exec',name,'/opt/view/bin/mpicxx',target+'.o',target+'-cuda.o',*LINK,'-o',target])
                execute(['podman','cp',name+':'+target,PROGRAM])
            if recipe()!=current:raise ValueError('CEED probe source/native changed during build')
            dev.write(BASE/'manifest.json',dict(recipe=current,binary_sha256=dev.sha(PROGRAM),build_seconds=time.monotonic()-started))
        finally:
            subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print('CEED tensor probe built; numerical/performance qualification NOT RUN')


def validate_case(case):
    lt=case.get('lt',False)
    wmma=case.get('wmma',False)
    wmma_checks=case.get('wmma_checks',False)
    if not isinstance(wmma_checks,bool) or wmma_checks and (not wmma or case.get('suite')=='scale'):
        raise ValueError('Invalid WMMA control scope')
    if not isinstance(wmma,bool) or wmma and not (lt and case.get('fused')):raise ValueError('Missing WMMA comparators')
    compensated=case.get('compensated',False)
    if not isinstance(lt,bool) or lt and compensated:raise ValueError('Invalid Lt experiment scope')
    bits=case.get('compensated_bits',False)
    if bits and (not compensated or case.get('tiny_error_controls') is not True):
        raise ValueError('Missing compensated/tiny-error controls')
    if compensated and not case.get('fused'):raise ValueError('Missing fused comparator')
    suite=case.get('suite','screen')
    if suite not in ['screen','scale']:raise ValueError('Unknown basis suite')
    scale=suite=='scale'
    if case.get('complete') is not True or len(case.get('rows',[]))!=(42 if scale else 12 if lt else 96):
        raise ValueError('Missing basis action coverage')
    expected=set()
    for family in ([0] if scale or lt else range(4)):
        for q in ([14] if scale or lt else [6] if family==3 else [6,14]):
            for comp in ([1,2] if not (scale or lt) and family==0 and q==14 else [1]):
                for mode in [1,[8,4,2,8][family]]:
                    for elements in ([257,1023,4099,16383,65537,131071,1601320] if scale else [257,131071]):
                        for trans,add in [(False,False),(True,False),(True,True)]:
                            expected.add((family,q,comp,mode,elements,trans,add))
    seen=set()
    def accuracy(check,tolerance):
        if check.get('tolerance')!=tolerance:raise ValueError('Changed action tolerance')
        values=[check.get(k) for k in ['relative_l2','scaled_max']]
        if not all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 for v in values):
            raise ValueError('Invalid action error')
        if check.get('passed') is not all(v<=tolerance for v in values):
            raise ValueError('Action error flag disagrees with measured errors')
    def timing(check):
        for key in ['wall_ms','cuda_interval_ms']:
            values=check[key]
            if len(values)!=3 or not all(isinstance(v,(float,int)) and not isinstance(v,bool) and 0<v<120000 for v in values):
                raise ValueError('Invalid timing coverage')
            if check['median_'+key]!=sorted(values)[1]:raise ValueError('Invalid timing median')
    def linearity(check,tol,required=False):
        if not isinstance(check,dict) or check.get('alpha')!=1.23456789012345:
            raise ValueError('Missing independent basis linearity control')
        for key in ['homogeneity','superposition']:
            accuracy(check[key],tol)
            if required and check[key]['passed'] is not True:
                raise ValueError('Original/FP64 basis linearity control failed')
    def finite_range(items,tol,length,required=False):
        scales=[1e-300,1e-80,2.**-75,2.**-74,1e-30,1.,1e30,2.**100,2.**101,1e80,1e300]
        if not isinstance(items,list) or [item.get('scale') for item in items]!=scales:
            raise ValueError('Missing finite-range coverage')
        for item in items:
            count=item.get('nonfinite_outputs')
            if not isinstance(count,int) or isinstance(count,bool) or not 0<=count<=length or item.get('finite_output') is not (count==0):
                raise ValueError('Invalid finite-output accounting')
            if count:
                if item.get('accuracy') is not None or required:raise ValueError('Invalid nonfinite reference/result')
            else:
                accuracy(item['accuracy'],tol)
                if required and not item['accuracy']['passed']:raise ValueError('Independent original range control failed')
    for row in case['rows']:
        key=tuple(row[k] for k in ['family','Q','components','eval','elements','transpose','add'])
        if key in seen:raise ValueError('Duplicate action')
        seen.add(key)
        if key not in expected or row['P']!=[20,15,10,8][row['family']] or row['N']!=row['elements']*row['components']:
            raise ValueError('Unexpected basis action dimensions')
        if row['canaries_passed'] is not True:raise ValueError('Corrupted basis buffer')
        timing(row['original_timing'])
        if row['elements']==257:
            accuracy(row['original_vs_cpu'],1e-11)
            if row['original_vs_cpu']['passed'] is not True:
                raise ValueError('Original vs independent reference failed')
        if compensated and row['elements']==257 and not row['transpose']:
            linearity(row['original_linearity'],1e-11,True)
        if wmma_checks and row['elements']==257 and not row['transpose']:
            linearity(row['original_linearity'],1e-11,True)
            finite_range(row['original_range'],1e-11,row['N']*row['Q']*row['q_components'],True)
        if [m['precision'] for m in row['methods']]!=['FP64','FP32_pedantic','TF32_requested']+(['FP32_fused'] if case.get('fused') else [])+(['mixed_compensated'] if compensated and not row['transpose'] else [])+(['mixed_compensated_bits'] if bits and not row['transpose'] else [])+(['TF32_Lt'] if lt else [])+(['TF32_WMMA_fused'] if wmma and not row['transpose'] else []):
            raise ValueError('Missing precision comparison')
        for method in row['methods']:
            if method['precision']=='TF32_Lt':
                if method.get('workspace_limit_bytes')!=64*1024*1024 or len(method.get('plans',[]))!=row['q_components']:
                    raise ValueError('Invalid Lt workspace/plan coverage')
                expected_workspace=(row['N']*((row['Q']*row['q_components']+row['P']))+row['P']*row['Q']*row['q_components'])*4
                if method.get('extra_fp32_workspace_bytes')!=expected_workspace:
                    raise ValueError('Invalid Lt conversion workspace')
                plan_ms=method.get('plan_ms')
                if not isinstance(plan_ms,(float,int)) or not math.isfinite(plan_ms) or plan_ms<0:
                    raise ValueError('Invalid Lt setup time')
                supported=[]
                for plan in method['plans']:
                    candidates=plan['candidates'];count=plan['returned']
                    if not isinstance(count,int) or not 0<=count<=8 or len(candidates)!=count:
                        raise ValueError('Invalid Lt heuristic coverage')
                    masks=[plan['tensor_op_mask'],plan['tf32_input_mask']]
                    if any(not isinstance(v,int) or v<=0 for v in masks):raise ValueError('Invalid Lt implementation masks')
                    if len(plan['alignment_bytes'])!=4 or any(v not in [1,2,4,8,16,32,64,128,256] for v in plan['alignment_bytes']):
                        raise ValueError('Invalid Lt alignment constraints')
                    eligible=[]
                    for rank,item in enumerate(candidates):
                        flags=item['impl_flags'];workspace=item['workspace_bytes']
                        if item['rank']!=rank or not isinstance(flags,int) or flags<0 or not isinstance(workspace,int) or workspace<0:
                            raise ValueError('Invalid Lt candidate metadata')
                        usable=all(item[k]==0 for k in ['heuristic_state','check_status','check_state']) and workspace<=method['workspace_limit_bytes'] and all(flags&m for m in masks)
                        if item['eligible'] is not bool(usable):raise ValueError('Invalid Lt candidate eligibility')
                        if usable:eligible.append(item)
                    if plan['heuristic_status'] not in [0,15] or candidates and plan['heuristic_status']!=0:
                        raise ValueError('Failed Lt heuristic with candidates')
                    supported.append(bool(eligible))
                    if eligible:
                        first=eligible[0]
                        for key in ['rank','id','impl_flags','workspace_bytes']:
                            if plan['selected_'+key]!=first[key]:raise ValueError('Lt selection differs from checked first heuristic')
                if method.get('supported') is not all(supported):raise ValueError('Invalid Lt supported claim')
                if not method['supported']:
                    if 'accuracy' in method or 'timing' in method:raise ValueError('Unsupported Lt plan has fabricated execution')
                    continue
            tol={'FP64':1e-11,'FP32_pedantic':2e-6,'TF32_requested':2e-3,'TF32_Lt':2e-3,'TF32_WMMA_fused':2e-3,'FP32_fused':2e-6,'mixed_compensated':1e-11,'mixed_compensated_bits':1e-11}[method['precision']]
            if method['precision']=='TF32_WMMA_fused' and (method['extra_fp32_workspace_bytes']!=row['P']*row['Q']*row['q_components']*4 or method['shared_bytes_per_block']!=18432):
                raise ValueError('Invalid WMMA workspace')
            accuracy(method['accuracy'],tol)
            if row['elements']==257:
                accuracy(method['accuracy']['independent_cpu'],tol)
                if method['precision']=='FP64' and not method['accuracy']['independent_cpu']['passed']:
                    raise ValueError('FP64 library vs independent reference failed')
            if method['precision']=='FP64' and method['accuracy']['passed'] is not True:
                raise ValueError('FP64 library/layout control failed')
            timing(method['timing'])
            if compensated and row['elements']==257 and not row['transpose']:
                linearity(method['linearity'],tol,method['precision']=='FP64')
            if wmma_checks and row['elements']==257 and not row['transpose']:
                linearity(method['linearity'],1e-11 if method['precision']=='FP64' else 2e-6,method['precision']=='FP64')
                finite_range(method['range_stress'],tol,row['N']*row['Q']*row['q_components'],method['precision']=='FP64')
            if method['precision']=='FP32_fused' and method['extra_fp32_workspace_bytes']!=row['P']*row['Q']*row['q_components']*4:
                raise ValueError('Unexpected fused vector workspace')
            if method['precision'] in ['mixed_compensated','mixed_compensated_bits'] and method['extra_fp32_workspace_bytes']!=row['P']*row['Q']*row['q_components']*8:
                raise ValueError('Unexpected compensated vector workspace')
            if method['precision']=='mixed_compensated_bits' and row['elements']==257:
                stress=method.get('range_stress')
                scales=[1e-300,1e-80,2.**-75,2.**-74,1e-30,1.,1e30,2.**100,2.**101,1e80,1e300]
                if not isinstance(stress,list) or [s.get('scale') for s in stress]!=scales:
                    raise ValueError('Missing independent input-range coverage')
                for item in stress:accuracy(item['accuracy'],1e-11)
    if seen!=expected:raise ValueError('Incomplete basis action coverage')
    return True


def trace_summary(path):
    with sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro',uri=True) as db:
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'CUPTI_ACTIVITY_KIND_KERNEL','StringIds'}<=tables:raise ValueError('Missing CUDA kernel activity')
        columns={row[1] for row in db.execute('PRAGMA table_info(CUPTI_ACTIVITY_KIND_KERNEL)')}
        if not {'demangledName','mangledName','start','end'}<=columns:raise ValueError('Missing kernel symbols/times')
        rows=[dict(demangled=demangled,mangled=mangled,calls=calls,seconds=seconds) for demangled,mangled,calls,seconds in db.execute(
            'SELECT d.value,m.value,count(*),sum(k.end-k.start)*1e-9 FROM CUPTI_ACTIVITY_KIND_KERNEL k '
            'JOIN StringIds d ON d.id=k.demangledName JOIN StringIds m ON m.id=k.mangledName '
            'GROUP BY k.demangledName,k.mangledName ORDER BY 4 DESC')]
        if not rows or any(r['calls']<=0 or not math.isfinite(r['seconds']) or r['seconds']<=0 for r in rows):
            raise ValueError('Empty/invalid kernel trace')
        diagnostics={}
        for table in tables:
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',table):raise ValueError('Unexpected trace table name')
            if any(word in table.upper() for word in ['DIAGNOSTIC','ERROR','WARNING','DROPPED']):
                keys=[r[1] for r in db.execute('PRAGMA table_info('+table+')')]
                diagnostics[table]=[dict(zip(keys,row)) for row in db.execute('SELECT * FROM '+table)]
        levels={r['id']:r['name'] for r in diagnostics.get('ENUM_DIAGNOSTIC_SEVERITY_LEVEL',[])}
        issues=[]
        for table,records in diagnostics.items():
            if table.startswith('ENUM_'):continue
            for record in records:
                # Preserve every diagnostic; only schema-described Info/Verbose are benign.
                level=levels.get(record.get('severity'))
                text=str(record.get('text',record))
                lost=re.search(r'data.{0,20}lost|dropped.{0,15}events|not all.{0,20}events.{0,30}collected',text,re.I)
                if level not in ['Info','Verbose'] or lost:issues.append(dict(table=table,record=record))
        return dict(kernels=rows,diagnostics=diagnostics,diagnostic_issues=issues,
            scope='Executed kernel symbols only; no executed instruction counters or speedup claim. Profile includes all probe methods.')


def run(output,seconds,scale=False,fused=False,compensated=False,lt=False,profile=False,wmma=False,wmma_checks=False):
    if wmma_checks and (not wmma or scale):raise ValueError('WMMA controls require screen WMMA')
    if wmma and not (lt and fused):raise ValueError('WMMA requires Lt/fused comparators')
    if lt and compensated:raise ValueError('Lt and compensated are separate experiments')
    if profile and not lt:raise ValueError('Trace requires isolated Lt experiment')
    if compensated and not fused:raise ValueError('Compensated screen requires --fused comparator')
    if not 30<=seconds<=120:raise ValueError('Probe requires30..120s deadline')
    dev.require_host_memory();manifest=verified();settings=dev.read(dev.SETTINGS)
    gpu=dev.capture(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.free','--format=csv,noheader,nounits'])
    if len(gpu.splitlines())!=1 or int(gpu.rsplit(',',1)[1].strip())<2048:
        raise ValueError('Single GPU with >=2048MiB free required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    name='palace-ceed-tensor-'+dev.sha(HERE/'ceed_tensor_probe.cpp')[:10]
    if subprocess.run(['podman','container','exists',name]).returncode==0:
        raise ValueError('Prior probe exists; inspect terminal state before retry')
    profiler=ram=None
    if profile:
        import nsight_window as profiler
        tool=profiler.verified_tool()
        if shutil.disk_usage('/dev/shm').free<1024**3:raise ValueError('Trace requires1GiB free RAM filesystem')
        ram=Path(tempfile.mkdtemp(prefix='palace-lt-trace-',dir='/dev/shm'));(ram/'tmp').mkdir()
        dev.write(output/'profile-input.json',dict(tool=tool,ram_directory=str(ram),capture='whole bounded probe',
            scope='Kernel instruction research; profiled timings must not be used as performance benchmark.'))
    args=['podman','run','--name',name,'--network=none','--read-only','--timeout',str(seconds),
        '--ulimit','core=0:0','--stop-timeout','3','--memory','6g','--memory-swap','6g','--cpus','4',
        '--security-opt=label=disable','--device','nvidia.com/gpu=all',
        '--tmpfs','/tmp:rw,size=512m','--tmpfs','/scratch:rw,size=512m','-w','/scratch',
        '--unsetenv','NVIDIA_TF32_OVERRIDE','-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=1',
        '-e','LD_LIBRARY_PATH=/native:/opt/palace-cudss/lib:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib:/usr/local/cuda/lib64',
        '-v',f'{output}:/work','-v',f'{PROGRAM}:/native/ceed-tensor-probe:ro',
        '-v',f'{dev.BUILD/"native/libpalace.so"}:/native/libpalace.so:ro']
    if profile:
        args.extend(['-v',f'{profiler.TOOL}:/profile-tools:ro','-v',f'{ram}:/profile',
            '-e','TMPDIR=/profile/tmp','--unsetenv','LD_PRELOAD','--entrypoint','/profile-tools/'+profiler.BINARY,
            settings['runtime_image'],'profile','--trace=cuda-sw','--sample=none','--cpuctxsw=none',
            '--cuda-trace-all-apis=true','--cuda-um-cpu-page-faults=false','--cuda-um-gpu-page-faults=false',
            '--capture-range=none','--kill=none','--wait=all','--export=sqlite','--output=/profile/window',
            '--force-overwrite=false','/native/ceed-tensor-probe','/work/case.json'])
    else:args.extend(['--entrypoint','/native/ceed-tensor-probe',settings['runtime_image'],'/work/case.json'])
    if scale:args.append('scale')
    if fused:args.append('fused')
    if compensated:args.append('compensated')
    if lt:args.append('lt')
    if wmma:args.append('wmma')
    if wmma_checks:args.append('wmma-checks')
    dev.write(output/'command.json',dict(argv=args,manifest=manifest,gpu_before=gpu,runner_sha256=dev.sha(Path(__file__))))
    started=time.monotonic();code=None
    try:
        with (output/'stdout.log').open('w') as stdout,(output/'stderr.log').open('w') as stderr:
            code=subprocess.run(args,stdout=stdout,stderr=stderr,timeout=seconds+15).returncode
    finally:
        if subprocess.run(['podman','container','exists',name]).returncode==0:
            subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            dev.write(output/'container-state.json',dev.read_output(['podman','inspect',name])[0]['State'])
            dev.command(['podman','rm',name],stdout=subprocess.DEVNULL)
        if ram is not None:
            report=dict(complete=False,files={})
            try:
                messages='\n'.join((output/name).read_text(errors='replace') for name in ['stdout.log','stderr.log'])
                loss=re.compile(r'data.{0,20}lost|dropped.{0,15}events|not all.{0,20}events.{0,30}collected|incompatibility.{0,30}driver|older version.{0,20}cupti|unsupported cuda|does not support cuda',re.I)
                report['warnings']=[line for line in messages.splitlines() if loss.search(line)]
                for suffix in ['sqlite','nsys-rep']:
                    source=ram/('window.'+suffix)
                    if not source.is_file() or not 0<source.stat().st_size<=64*1024**2:
                        raise ValueError('Trace missing or exceeds64MiB/result')
                    target=output/('profile.'+suffix);shutil.copy2(source,target)
                    report['files'][target.name]=dict(bytes=target.stat().st_size,sha256=dev.sha(target))
                report['summary']=trace_summary(output/'profile.sqlite')
                report['complete']=not report['warnings'] and not report['summary']['diagnostic_issues']
            except (ValueError,OSError,sqlite3.Error) as error:report['error']=str(error)
            finally:
                dev.write(output/'profile.json',report);shutil.rmtree(ram)
    state=dev.read(output/'container-state.json')
    complete=bool(code==0 and state['ExitCode']==0 and not state['OOMKilled'] and (output/'case.json').exists()
                  and (not profile or dev.read(output/'profile.json')['complete']))
    error=None
    if complete:
        try:validate_case(dev.read(output/'case.json'))
        except (ValueError,KeyError,TypeError) as e:complete=False;error=str(e)
    dev.write(output/'result.json',dict(complete=complete,exit_code=code,validation_error=error,
        elapsed_seconds=time.monotonic()-started,profiled=profile,
        scope='Execution/action-control only. Profiled timings are not benchmarks. Mixed precision numerical acceptance separate; no RF/TC/solver speedup qualification.'))
    print('CEED tensor probe terminal: '+('complete; inspect accuracy/timings' if complete else 'FAILED'))
    if not complete:raise ValueError('Probe incomplete; inspect bounded logs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['build','check','run']);parser.add_argument('output',nargs='?',type=Path)
    parser.add_argument('--scale',action='store_true',help='ND2/Q14 size ladder through actual N1601320, bounded GPU-resident action probe')
    parser.add_argument('--fused',action='store_true',help='Also screen fused FP32-register action without intermediate vector buffers')
    parser.add_argument('--compensated',action='store_true',help='Forward compensated mixed-register dot and small basis linearity controls; requires --fused')
    parser.add_argument('--lt',action='store_true',help='ND2/Q14 only: checked cuBLASLt TF32 tensor-op heuristic, <=64MiB workspace')
    parser.add_argument('--wmma',action='store_true',help='Forward-only P20/Q14/QC3 fused TF32 WMMA research, requires --lt --fused')
    parser.add_argument('--wmma-checks',action='store_true',help='Screen-only stationarity/range controls, retains negative mixed results')
    parser.add_argument('--profile-lt',action='store_true',help='Pinned Nsight CUDA activity in RAM; separate diagnostic, never a performance benchmark')
    parser.add_argument('--seconds',type=int,default=120);args=parser.parse_args()
    if args.action=='build':build()
    elif args.action=='check':print('CEED tensor probe verified' if verified() else 'invalid')
    elif args.output is None:parser.error('run requires new output directory')
    else:run(args.output,args.seconds,args.scale,args.fused,args.compensated,args.lt,args.profile_lt,args.wmma,args.wmma_checks)
