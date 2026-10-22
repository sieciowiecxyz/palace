"""Cached CPU ROI replay; reads existing fields, never assembles or solves a system."""
import argparse
import fcntl
import json
import math
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dev
import qualify_antenna as q
import stored_basis_probe as probe

BASE=dev.ROOT/'build/m7-field-roi'
SOURCE=Path(__file__).with_suffix('.cpp')
PROGRAM=BASE/'field-roi'
FLAGS=[*probe.FLAGS,'-DPALACE_WITH_SLEPC']
ROIS=('PCB','feed-PTFE','slot-sector-PP','slot-sector-PN','slot-sector-NP','slot-sector-NN')


def assess(entries,frequencies):
    """Require complete spatial/port/field/quadrature coverage, never a partial PASS."""
    if not frequencies or frequencies!=sorted(set(frequencies)) or not all(math.isfinite(f) and f>0 for f in frequencies):
        raise ValueError('Require distinct increasing positive frequencies')
    def key(r):return (r['frequency_ghz'],r['port'],r['field'],r['quadrature'],r['roi'])
    expected={(f,p,v,k,r) for f in frequencies for p in (1,2) for v in ('E','B')
              for k in (4,6) for r in ROIS}
    if len(entries)!=len(expected) or {key(r) for r in entries}!=expected:
        raise ValueError('Incomplete or duplicated ROI coverage')
    phase_limit=math.degrees(math.asin(.01))
    for r in entries:
        values=[r[k] for k in ('relative_complex_L2','phase_rms_degrees',
                              'phase_undefined_reference_fraction','reference_norm_squared')]
        if not all(math.isfinite(v) and v>=0 for v in values) or r['reference_norm_squared']<=0 or r['points']<=0:
            raise ValueError('Invalid/empty/nonfinite ROI')
        if r['relative_complex_L2']>.01 or r['phase_rms_degrees']>phase_limit or r['phase_undefined_reference_fraction']>1e-6:
            raise ValueError('Spatial complex L2/phase gate failed')
    rows={key(r):r for r in entries}
    differences=[abs(r['relative_complex_L2']-rows[(f,p,v,6,roi)]['relative_complex_L2'])
                 for (f,p,v,k,roi),r in rows.items() if k==4]
    if max(differences)>5e-4:raise ValueError('ROI quadrature stability failed')
    return dict(passed=True,frequencies_ghz=frequencies,rows=len(entries),
                max_complex_L2=max(r['relative_complex_L2'] for r in entries),
                max_phase_rms_degrees=max(r['phase_rms_degrees'] for r in entries),
                max_undefined_phase_fraction=max(r['phase_undefined_reference_fraction'] for r in entries),
                max_quadrature_L2_delta=max(differences),phase_limit_degrees=phase_limit)


def recipe():
    m=dev.verified_build()
    return dict(source_sha256=dev.sha(SOURCE),native=m['native'],palace_source_sha256=m['source_sha256'],
                builder=m['builder_image_id'],runtime=m['runtime_base_id'],flags=FLAGS,link=probe.LINK)


def verified():
    m=dev.read(BASE/'manifest.json')
    if m['recipe']!=recipe() or m['binary_sha256']!=dev.sha(PROGRAM):
        raise ValueError('Stale ROI helper; build with preserved cache')
    return m


def build():
    dev.require_host_memory(); BASE.mkdir(parents=True,exist_ok=True)
    with (dev.BUILD/'build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if PROGRAM.exists():
            try: verified()
            except (ValueError,FileNotFoundError): pass
            else: print('ROI helper cached; no compilation'); return
        r=recipe(); started=time.monotonic(); name=dev.builder(dev.read(dev.SETTINGS))
        target='/tmp/palace-field-roi'
        try:
            with (BASE/'build.log').open('w') as log:
                for args in [
                    ['ccache','/opt/view/bin/mpicxx',*FLAGS,'-c','/src/palace/'+str(SOURCE.relative_to(dev.ROOT)),'-o',target+'.o'],
                    ['/opt/view/bin/mpicxx',target+'.o',*probe.LINK,'-o',target]]:
                    dev.command(['podman','exec',name,*args],stdout=log,stderr=subprocess.STDOUT,
                                timeout=max(1,120-(time.monotonic()-started)))
                dev.command(['podman','cp',name+':'+target,PROGRAM],stdout=log,timeout=10)
            if recipe()!=r: raise ValueError('Source/native changed during helper build')
            dev.write(BASE/'manifest.json',dict(recipe=r,binary_sha256=dev.sha(PROGRAM),build_seconds=time.monotonic()-started))
        finally:
            subprocess.run(['podman','stop','--time','3',name],stdout=subprocess.DEVNULL,check=True)


def run(reference,candidate,output,mode,part='all',pairs=None):
    reference=Path(reference).resolve(); candidate=Path(candidate).resolve(); output=Path(output).resolve()
    if any(not p.is_relative_to(dev.ROOT) for p in (reference,candidate,output)):
        raise ValueError('Replay paths must be inside the read-only repository mount')
    if mode not in ('coax','antenna'): raise ValueError('Explicit coax/antenna mode required')
    if part not in ('all','1E','1B','2E','2B'): raise ValueError('Invalid replay part')
    if mode=='antenna' and part=='all' and pairs is None:
        raise ValueError('Whole antenna replay needs batch --count1/900s or explicit bounded --part')
    if pairs is not None:
        if mode!='antenna' or part!='all' or len(pairs)!=1:
            raise ValueError('Only one antenna pair per complete900s replay is qualified')
        if any(not Path(p[k]).resolve().is_relative_to(dev.ROOT) for p in pairs for k in ('reference','candidate')):
            raise ValueError('All batch inputs must be inside read-only repository')
        if Path(pairs[0]['reference']).resolve()!=reference or Path(pairs[0]['candidate']).resolve()!=candidate:
            raise ValueError('Mesh source must equal the first replay pair')
    dev.require_host_memory(); m=verified()
    case=dict(reference=str(reference),candidate=str(candidate),mode=mode,part=part,output='/work/fields.json')
    seconds=180
    if pairs is not None:
        receipts=[q.qualify(p['reference'],p['candidate'],3) for p in pairs]
        qualification=q.summarize(receipts,sorted(p['frequency_ghz'] for p in pairs))
        case['pairs']=pairs; seconds=900
    else:qualification=q.qualify(reference,candidate,3)
    if not qualification['passed']: raise ValueError('Original whole-field qualification failed')
    output.mkdir(parents=True,exist_ok=False)
    dev.write(output/'case.json',case)
    name='palace-roi-'+dev.sha(output/'case.json')[:12]
    if subprocess.run(['podman','container','exists',name]).returncode!=1: raise ValueError('Container already exists')
    args=['podman','run','--name',name,'--network=none','--read-only','--timeout',str(seconds),
          '--ulimit','core=0:0','--stop-timeout','3','--memory','12g','--memory-swap','12g','--cpus','4',
          '--security-opt=label=disable','--device','nvidia.com/gpu=all',
          '--tmpfs','/tmp:rw,size=256m','-w',str(reference),'-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=1',
          '-e','LD_LIBRARY_PATH=/native:/opt/palace-cudss/lib:/opt/view/lib:/opt/view/lib64:/opt/cudss/lib',
          '-v',f'{dev.ROOT}:{dev.ROOT}:ro','-v',f'{output}:/work',
          '-v',f'{PROGRAM}:/native/field-roi:ro','-v',f'{dev.BUILD/"native/libpalace.so"}:/native/libpalace.so:ro',
          '--entrypoint','/native/field-roi',dev.read(dev.SETTINGS)['runtime_image'],'/work/case.json']
    dev.write(output/'command.json',dict(argv=args,helper_manifest=m,original_qualification=qualification,
                                      scope='CPU postprocessing only; GPU driver exposed for linking, no solve'))
    started=time.monotonic(); code=None
    try:
        with (output/'stdout.log').open('w') as out,(output/'stderr.log').open('w') as err:
            code=subprocess.run(args,stdout=out,stderr=err,timeout=seconds+15).returncode
        state=dev.read_output(['podman','inspect',name])[0]['State']
        dev.write(output/'container-state.json',state)
    finally:
        subprocess.run(['podman','rm','--force',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        dev.write(output/'result.json',dict(exit_code=code,complete=code==0,elapsed_seconds=time.monotonic()-started))
    if code!=0: raise ValueError('ROI replay failed; preserved logs, no automatic retry')
    print(json.dumps(dict(complete=True,output=str(output),seconds=time.monotonic()-started)))


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('build')
    r=sub.add_parser('run'); r.add_argument('reference'); r.add_argument('candidate'); r.add_argument('output')
    r.add_argument('--mode',choices=['coax','antenna'],required=True)
    r.add_argument('--part',choices=['all','1E','1B','2E','2B'],default='all')
    b=sub.add_parser('batch');b.add_argument('receipts',type=Path);b.add_argument('output')
    b.add_argument('--start',type=int,required=True);b.add_argument('--count',type=int,choices=[1],default=1)
    a=sub.add_parser('assess',help='Separate row coverage/quality check; execution completeness and RF provenance must also be audited')
    a.add_argument('fields',type=Path);a.add_argument('--frequencies',type=float,nargs='+',required=True)
    a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.action=='build': build()
    elif args.action=='run': run(args.reference,args.candidate,args.output,args.mode,args.part)
    elif args.action=='assess':
        if args.output.exists(): raise ValueError('Assessment output already exists')
        result=assess(dev.read(args.fields)['entries'],args.frequencies)
        result.update(input_sha256=dev.sha(args.fields),scope='Row quality and coverage only; not original RF execution/provenance or physics validation')
        dev.write(args.output,result);print(json.dumps(result))
    else:
        if args.start<0: p.error('Require start>=0')
        rows=dev.read(args.receipts)['receipts'][args.start:args.start+args.count]
        if len(rows)!=args.count: p.error('Requested batch is missing receipts')
        pairs=[dict(reference=r['input_paths'][0],candidate=r['input_paths'][1],frequency_ghz=r['frequency_ghz']) for r in rows]
        run(pairs[0]['reference'],pairs[0]['candidate'],args.output,'antenna',pairs=pairs)


if __name__=='__main__':
    dev.install_signal_handlers()
    try:main()
    except KeyboardInterrupt:sys.exit(130)
