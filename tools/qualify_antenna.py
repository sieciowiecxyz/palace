#!/usr/bin/env python3
"""Recheck a cold single-frequency/two-port FP64 reference vs combined opt-ins.

Read-only artifacts, except an explicitly requested receipt. No execution or promotion.
"""
import argparse
import cmath
import csv
import hashlib
import json
import math
from pathlib import Path
import re

import dev


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(path):
    with Path(path).open() as stream:
        data=list(csv.reader(stream,skipinitialspace=True))
    require(len(data)>=2, 'CSV has no data')
    header=[s.strip() for s in data[0]]
    rows=[[float(s) for s in row] for row in data[1:]]
    require(all(len(row)==len(header) and all(math.isfinite(v) for v in row) for row in rows),
            'CSV width or finite-value check failed')
    return header,rows


def rf_metrics(sref, scand, eref, ecand, frequencies):
    require(sref[0]==scand[0] and len(sref[0])==9, 'S headers/2-port coverage differ')
    for i,port in enumerate(['1][1','2][1','1][2','2][2']):
        require(sref[0][2*i+1]==f'|S[{port}]| (dB)' and
                sref[0][2*i+2]==f'arg(S[{port}]) (deg.)', 'Unexpected S matrix order/units')
    require(eref[0]==ecand[0], 'Energy headers differ')
    require(all([r[0] for r in table[1]]==frequencies for table in [sref,scand,eref,ecand]),
            'CSV frequency coverage/order differs')
    ds=dv=dp=de=0.0
    for a,b in zip(sref[1],scand[1],strict=True):
        values=lambda row:[10**(row[i]/20)*cmath.exp(1j*math.radians(row[i+1])) for i in range(1,9,2)]
        x,y=values(a),values(b)
        ds=max(ds,max(abs(u-v) for u,v in zip(x,y,strict=True)))
        for k in [0,3]:
            require(abs(x[k])<1 and abs(y[k])<1, 'VSWR undefined/nonpassive reflection; use a separate antiresonance protocol')
            dv=max(dv,abs((1+abs(x[k]))/(1-abs(x[k]))-(1+abs(y[k]))/(1-abs(y[k]))))
        for cols in [(0,1),(2,3)]:
            dp=max(dp,abs(sum(abs(x[k])**2 for k in cols)-sum(abs(y[k])**2 for k in cols)))
    for a,b in zip(eref[1],ecand[1],strict=True):
        for x,y in zip(a[1:],b[1:],strict=True):
            require(x!=0 or y==0, 'Nonzero candidate energy in an exactly zero reference column')
            if x:de=max(de,abs(y-x)/abs(x))
    return dict(max_delta_S=ds,max_delta_vswr=dv,max_delta_power=dp,max_relative_energy=de,
                passed=ds<=1e-3 and dv<=.01 and dp<=1e-3 and de<=1e-3)


def qualify(reference,candidate):
    paths=[Path(reference).resolve(),Path(candidate).resolve()]
    cfgs=[dev.read(p/'config.json') for p in paths]
    builds=[dev.read(p/'build-manifest.json') for p in paths]
    results=[dev.read(p/'result.json') for p in paths]
    require(cfgs[0]==cfgs[1] and builds[0]==builds[1], 'Reference/candidate must have identical config and native manifest')
    cfg=cfgs[0]
    frequencies=[f for s in cfg['Solver']['Driven']['Samples'] for f in s['Freq']]
    require(len(frequencies)==1 and cfg['Solver']['Driven'].get('AdaptiveTol',0)==0,
            'This qualification protocol is single-frequency/uniform')
    require(sorted(p['Index'] for p in cfg['Boundaries']['LumpedPort'])==[1,2] and
            sorted(p['Excitation'] for p in cfg['Boundaries']['LumpedPort'])==[1,2], 'Require both physical ports/excitations1/2')
    require(all(r.get('complete') and r.get('exit_code')==0 for r in results), 'Incomplete reference or candidate')
    logs=[(p/'palace.log').read_text() for p in paths]
    envs=[dev.read(p/'command.json')['environment'] for p in paths]
    require(not any(k in envs[0] for k in ['PALACE_GMRES_FP32_BASIS','PALACE_GMRES_FP32_DIRECT',
            'PALACE_NATIVE_COARSE_FP32','PALACE_REUSE_PORT_SETUP']), 'Reference is not fullFP64/fresh setup')
    require(all(envs[1].get(k)=='1' for k in ['PALACE_GMRES_FP32_BASIS','PALACE_GMRES_FP32_DIRECT',
            'PALACE_NATIVE_COARSE_FP32','PALACE_REUSE_PORT_SETUP']), 'Combined candidate flags differ')
    forbidden=['PALACE_SWEEP_PREDICTOR','PALACE_PROM_VALIDATE','PALACE_INITIAL_FIELDS','PALACE_HISTORY_FIELDS',
               'PALACE_GMRES_FP64_DISK_BASIS','PALACE_GMRES_FP32_DISK_BASIS','PALACE_CUDSS_FP32']
    require(not any(k in env for env in envs for k in forbidden), 'Cold/in-memory protocol violated')
    require(dev.native_complex_coarse_applied(logs[0],2,'complex_fp64') and
            dev.native_complex_coarse_applied(logs[1],1,'complex_fp32') and
            dev.native_mixed_applied(logs[1],1,2), 'Native precision/count/residual audit failed')
    raws=[]
    for i,(p,c) in enumerate(zip(paths,cfgs)):
        dev.verified_field_reference(p,c,dev.read(p/'fixture.json'),builds[0])
        require(dev.validate_output(p,c,0)['complete'], 'Recomputed execution checks failed')
        require(dev.port_setup_audit(logs[i],c,bool(i))['passed'], 'Setup/reuse audit failed')
        require(not dev.read(p/'container-state.json')['OOMKilled'], 'OOM is not a valid result')
        raw=[float(v) for v in re.findall(r'PALACE_TRUE_RESIDUAL: norm_Ax_minus_b=[\deE+.-]+ norm_b=[\deE+.-]+ relative=([\deE+.-]+)',logs[i])]
        require(len(raw)==2 and all(math.isfinite(v) and 0<=v<=1e-6 for v in raw), 'Original raw residual gate failed')
        raws.append(raw)
        require(all(math.isfinite(results[i][k]) and results[i][k]>0 for k in ['end_to_end_seconds','cgroup_memory_peak_bytes']),
                'Missing cost measurement')
    fields=dev.field_comparisons(paths[1],cfg)
    post=[p/cfg['Problem']['Output'] for p in paths]
    metrics=rf_metrics(*(read_csv(p/'port-S.csv') for p in post),
                       *(read_csv(p/'domain-E.csv') for p in post),frequencies)
    normalized=json.loads(json.dumps(cfg))
    for sample in normalized['Solver']['Driven']['Samples']:sample['Freq']=[0]
    normalized['Model']['Mesh']=dev.read(paths[0]/'fixture.json')['mesh_sha256']
    case_id=hashlib.sha256(json.dumps(normalized,sort_keys=True).encode()).hexdigest()
    return dict(passed=metrics['passed'] and fields['passed'],frequency_ghz=frequencies[0],raw=raws,fields=fields,
                metrics=metrics,reference=results[0],candidate=results[1],
                time_saving_percent=100*(1-results[1]['end_to_end_seconds']/results[0]['end_to_end_seconds']),
                cgroup_saving_percent=100*(1-results[1]['cgroup_memory_peak_bytes']/results[0]['cgroup_memory_peak_bytes']),
                input_paths=[str(p) for p in paths],source_sha256=builds[0]['source_sha256'],
                build_manifest_sha256=hashlib.sha256(json.dumps(builds[0],sort_keys=True).encode()).hexdigest(),
                case_without_frequency_sha256=case_id,
                analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                written_artifact_bytes=[sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) for p in paths],
                scope='Cold single-f/bothports samebuild/config/mesh; combined flags vsfullFP64. Onepair, notmedian/physical/fullband/monolithicsweep/generalization. All per-chunk setup/IO included.')


def summarize(receipts,expected):
    require(expected and expected==sorted(set(expected)), 'Expected frequencies must be distinct/increasing')
    receipts=sorted(receipts,key=lambda r:r['frequency_ghz'])
    require([r['frequency_ghz'] for r in receipts]==expected, 'Summary frequency coverage/duplicates differ')
    require(all(r['passed'] and r['metrics']['passed'] and r['fields']['passed'] for r in receipts),
            'Summary contains an unqualified case')
    require(len({r['source_sha256'] for r in receipts})==1 and
            len({r['build_manifest_sha256'] for r in receipts})==1 and
            len({r['case_without_frequency_sha256'] for r in receipts})==1,
            'Summary changes build, mesh or configuration beyond frequency')
    for r in receipts:
        require(all(math.isfinite(r[mode][key]) and r[mode][key]>0 for mode in ['reference','candidate']
                    for key in ['end_to_end_seconds','cgroup_memory_peak_bytes']), 'Invalid summary cost')
    reference=sum(r['reference']['end_to_end_seconds'] for r in receipts)
    candidate=sum(r['candidate']['end_to_end_seconds'] for r in receipts)
    refmem=max(r['reference']['cgroup_memory_peak_bytes'] for r in receipts)
    candmem=max(r['candidate']['cgroup_memory_peak_bytes'] for r in receipts)
    return dict(passed=True,frequencies_ghz=expected,reference_end_to_end_seconds=reference,
                candidate_end_to_end_seconds=candidate,time_saving_percent=100*(1-candidate/reference),
                speed_ratio=reference/candidate,reference_max_cgroup_bytes=refmem,candidate_max_cgroup_bytes=candmem,
                max_cgroup_saving_percent=100*(1-candmem/refmem),
                maxima={k:max(r['metrics'][k] for r in receipts) for k in
                        ['max_delta_S','max_delta_vswr','max_relative_energy','max_delta_power']},
                max_relative_E=max(e['relative_E'] for r in receipts for e in r['fields']['entries']),
                max_relative_B=max(e['relative_B'] for r in receipts for e in r['fields']['entries']),
                total_field_rows=sum(len(r['fields']['entries']) for r in receipts),
                reference_total_iterations=sum(sum(r['reference']['iterations']) for r in receipts),
                candidate_total_iterations=sum(sum(r['candidate']['iterations']) for r in receipts),
                written_artifact_bytes=sum(sum(r['written_artifact_bytes']) for r in receipts),receipts=receipts,
                scope='Sum of independent cold single-f job pairs/bothports, all repeatedsetup/IO/cleanup included. Notmonolithicsweep, median/fullband/newgeometry/physicalmeasurement/TC proof. Peakcgroup ismax, notsum orphysicalVRAM.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path,nargs='?')
    parser.add_argument('candidate',type=Path,nargs='?')
    parser.add_argument('--summary',type=Path,nargs='+',help='Recheck original pairs named by these receipts, then aggregate; no trust in cached passed flags')
    parser.add_argument('--expected-frequencies',type=float,nargs='+',help='Explicit required coverage for --summary')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.summary:
        if args.reference or args.candidate or not args.expected_frequencies:
            parser.error('--summary requires --expected-frequencies and no pair positional arguments')
        receipt=summarize([qualify(*dev.read(p)['input_paths']) for p in args.summary],args.expected_frequencies)
    else:
        if not args.reference or not args.candidate or args.expected_frequencies:
            parser.error('Specify reference and candidate, or --summary with expected frequencies')
        receipt=qualify(args.reference,args.candidate)
    dev.write(args.output,receipt)
    keys=(['passed','frequencies_ghz','reference_end_to_end_seconds','candidate_end_to_end_seconds',
           'time_saving_percent','max_cgroup_saving_percent','maxima','total_field_rows'] if args.summary else
          ['passed','frequency_ghz','metrics','time_saving_percent','cgroup_saving_percent'])
    print(json.dumps({k:receipt[k] for k in keys},indent=2))
    raise SystemExit(0 if receipt['passed'] else 1)
