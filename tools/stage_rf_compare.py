#!/usr/bin/env python3
"""Read-only medium A/B RF gates. Completion, one-pair RF agreement and speed statistics differ."""
import argparse
import cmath
from collections import Counter
import csv
import difflib
import hashlib
import json
import math
from pathlib import Path
import re

from stage_full_check import expectations, check_full
from stage_operator_reference import compiler_inputs, source_hash

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT/'artifacts/m7-sm120-bundle-r3-20261022'
LEGACY_SOURCE = 'a6ec732f11cc7fe920365ba2aae354b68fe97e81f732d5afd4659ed5187c3338'
FROZEN_MANIFEST_SHA = 'dc8fa9d99d62138ca547b38278565adf24338784daa8a543e386aec16889ff1d'
FEATURE_VALUES = {'PALACE_PROBE_LOCATOR': {'gslib','mfem'},
                  'PALACE_SINGLE_RANK_DIRECT_MESH': {'0','1'}}
Z0 = 376.730313668  # Preserved legacy diagnostic constant, not fitted to flux.
FIELD_REL = 1e-5
FIELD_ABS = 1e-12  # L2 absolute gate for near-zero reference; in each CSV field's units.
UNIT_FILES = ('palace/utils/units.hpp', 'palace/utils/iodata.cpp',
              'palace/utils/constants.hpp', 'palace/utils/configfile.cpp',
              'palace/models/postoperatorcsv.cpp', 'palace/models/surfacepostoperator.cpp',
              'palace/models/domainpostoperator.cpp', 'palace/models/materialoperator.cpp',
              'palace/fem/output_functionals.cpp', 'palace/fem/output_functionals.hpp')
TAIL_ANCHOR = 'auto PostOperator<solver_t>::InitializeParaviewDataCollection(int ex_idx)'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def source_proof(source, frozen=FROZEN):
    """Do not invoke/patch the source-pinned legacy analyzer: establish a new explicit proof."""
    source, frozen = Path(source), Path(frozen)
    proof = dict(passed=False, source=str(source), frozen=str(frozen), files={},
                 legacy_source=LEGACY_SOURCE, legacy_analyzer_guard_preserved=True)
    try:
        manifest = read(frozen/'bundle-manifest.json')
        proof['frozen_compiler_source_sha256'] = source_hash(compiler_inputs(frozen))
        if proof['frozen_compiler_source_sha256'] != LEGACY_SOURCE:
            raise ValueError('Frozen compiler tree differs from legacy source pin')
        proof['bundle_manifest_sha256'] = sha(frozen/'bundle-manifest.json')
        if proof['bundle_manifest_sha256'] != FROZEN_MANIFEST_SHA:
            raise ValueError('Frozen manifest differs from independently pinned bundle')
        if manifest['source_sha256'] != LEGACY_SOURCE:
            raise ValueError('Frozen bundle is not the legacy source pin')
        paths = set(UNIT_FILES)
        # Surface QFunction headers and their relative quoted dependencies are also pinned.
        queue = ['palace/fem/qfunctions/32/surf_32_qf.h', 'palace/fem/qfunctions/21/surf_21_qf.h']
        while queue:
            name = queue.pop()
            if name in paths:
                continue
            paths.add(name)
            text = (frozen/name).read_text()
            for include in re.findall(r'^#include "([^"]+)"', text, re.MULTILINE):
                candidate = (Path(name).parent/include)
                resolved = (frozen/candidate).resolve().relative_to(frozen.resolve())
                queue.append(str(resolved))
        for name in sorted(paths):
            old, new = sha(frozen/name), sha(source/name)
            passed = old == manifest['files'].get(name) and old == new
            proof['files'][name] = dict(frozen_sha256=old, actual_sha256=new, equal=passed)
            if not passed:
                raise ValueError('Unit/normalization source differs: '+name)
        name = 'palace/models/postoperator.cpp'
        old, new = (frozen/name).read_text(), (source/name).read_text()
        if sha(frozen/name) != manifest['files'][name]:
            raise ValueError('Frozen PostOperator hash differs from manifest')
        old_tail, new_tail = old[old.index(TAIL_ANCHOR):], new[new.index(TAIL_ANCHOR):]
        equal = old_tail == new_tail
        proof['measurement_tail'] = dict(anchor=TAIL_ANCHOR, equal=equal,
                frozen_sha256=hashlib.sha256(old_tail.encode()).hexdigest(),
                actual_sha256=hashlib.sha256(new_tail.encode()).hexdigest(),
                whole_file_diff='\n'.join(difflib.unified_diff(old.splitlines(), new.splitlines(), n=1)))
        if not equal:
            raise ValueError('PostOperator measurement/output function bodies changed')
        proof.update(passed=True, correction='physical rE = raw CSV * Z0/(L0*Lc); RMS intensity=|rE|^2/Z0',
                     derivation='CSV applies inverse FIELD_E; physical far field includes LENGTH. Hc^2=1/(Z0*Lc_m^2), hence ratio=(Hc*Z0)^2*Lc_m=Z0/Lc_m.',
                     native_Z0=1.25663706127e-6*299792458,
                     legacy_Z0=Z0, legacy_Z0_relative_difference=Z0/(1.25663706127e-6*299792458)-1)
    except (OSError, ValueError, KeyError) as error:
        proof['error'] = str(error)
    return proof


def table(path):
    with Path(path).open(newline='') as stream:
        rows = csv.reader(stream)
        header = [x.strip() for x in next(rows)]
        if len(set(header)) != len(header):
            raise ValueError('Duplicate CSV column')
        values = [[float(x) for x in row] for row in rows if any(x.strip() for x in row)]
    if not values or any(len(row) != len(header) or not all(math.isfinite(x) for x in row)
                         for row in values):
        raise ValueError('Empty, incomplete or nonfinite CSV: '+str(path))
    return header, values


def vector_delta(a, b):
    if len(a) != len(b) or not a:
        raise ValueError('Complex field layouts differ')
    norm = math.sqrt(math.fsum(abs(x)**2 for x in a))
    error = math.sqrt(math.fsum(abs(y-x)**2 for x,y in zip(a,b)))
    absolute = norm <= FIELD_ABS
    floor = max(FIELD_ABS, norm/math.sqrt(len(a))*1e-8)
    phases = [abs(cmath.phase(y/x)) for x,y in zip(a,b) if abs(x)>floor and abs(y)>floor]
    return dict(passed=error<=FIELD_ABS if absolute else error/norm<=FIELD_REL,
                reference_l2=norm, error_l2=error, relative_l2=None if absolute else error/norm,
                max_abs_error=max(abs(y-x) for x,y in zip(a,b)),
                criterion='absolute_l2' if absolute else 'relative_l2', absolute_limit=FIELD_ABS,
                relative_limit=FIELD_REL, phase_floor=floor, phase_samples=len(phases),
                phase_excluded=len(a)-len(phases), max_phase_error_rad=max(phases,default=None))


def sphere(n):
    if type(n) is not int or n < 2:
        raise ValueError('Native sphere requires NSample>=2')
    points=[(0.,0.),(180.,0.)]
    if n == 2:
        return points
    remaining=n-2; nr=int(math.sqrt(remaining))
    sine=[math.sqrt(1-(1-2*i/(nr+1))**2) for i in range(1,nr+1)]
    counts=[int(remaining*s/sum(sine)+.5) for s in sine[:-1]]
    counts.append(remaining-sum(counts))
    for i,count in enumerate(counts,1):
        theta=90. if i==(nr+1)//2 else math.degrees(math.acos(1-2*i/(nr+1)))
        for j in range(count):
            phi=0. if j==0 else 180. if j==count//2 else 360.*j/count
            points.append((theta,phi))
    if len(points)!=n:
        raise ValueError('Wrong native sphere size')
    return points


def angle_key(theta,phi):
    return round(theta,6), 0. if abs(theta)<1e-5 or abs(theta-180)<1e-5 else round(phi%360,6)


def sphere_power(angles, vectors, n):
    lookup={angle_key(*angle):i for i,angle in enumerate(angles)}
    if len(lookup)!=len(angles):
        raise ValueError('Duplicate far-field direction')
    ids=[lookup[angle_key(*point)] for point in sphere(n)]
    native=[angles[i] for i in ids]
    rings=sorted({angle[0] for angle in native}); counts=Counter(angle[0] for angle in native)
    edges=[0]+[(a+b)/2 for a,b in zip(rings,rings[1:])]+[180]
    weights={t:2*math.pi*(math.cos(math.radians(edges[i]))-math.cos(math.radians(edges[i+1])))/counts[t]
             for i,t in enumerate(rings)}
    area=math.fsum(weights[t] for t,p in native)
    if abs(area-4*math.pi)>1e-10:
        raise ValueError('Native weights do not cover4pi')
    power=math.fsum(math.fsum(abs(x)**2 for x in vectors[idx])/Z0*weights[angles[idx][0]] for idx in ids)
    return dict(power_w=power, integrated_directions=len(ids), supplied_directions=len(angles), solid_angle=area)


def load_run(path, legacy=False, frozen=FROZEN):
    path=Path(path).resolve(); config=read(path/'config.json'); post=path/config['Problem']['Output']
    if legacy:
        manifest=read(path/'build-manifest.json')
        if manifest['source_sha256']!=LEGACY_SOURCE:
            raise ValueError('Legacy diagnostic must retain the exact legacy source pin')
        source=Path(frozen); plan=None
    else:
        plan=read(path/'plan.json'); source=Path(plan['source'])
        result=read(path/'full-result.json')
        if (not math.isfinite(result.get('full',{}).get('max_raw_relative_rhs',math.inf)) or
                not result.get('complete') or result.get('diagnostic_only') is not False or
                result.get('solver_executed') is not True or result.get('exit_code')!=0 or
                result.get('full',{}).get('max_raw_relative_rhs',math.inf)>1e-6):
            raise ValueError('Actual full-result is missing or incomplete')
        if sha(path/'config.json')!=plan['staged_config_sha256']:
            raise ValueError('Staged config changed after execution')
        if sha(plan['identity']['mesh'])!=plan['identity']['mesh_sha256']:
            raise ValueError('Raw mesh changed after execution')
        manifest=read(Path(plan['build'])/'manifest.json')
        if manifest['source_sha256']!=plan['identity']['source_sha256'] or manifest['native']!=plan['identity']['native']:
            raise ValueError('Build/source metadata differs from execution plan')
        if any(sha(Path(plan['build'])/'native'/name)!=value for name,value in plan['identity']['native'].items()):
            raise ValueError('Pinned native files changed after execution')
    observed_source_sha=source_hash(compiler_inputs(source))
    if observed_source_sha!=manifest['source_sha256']:
        raise ValueError('Current compiler source tree differs from actual executed build')
    expected=plan['full_expectations'] if plan else expectations(config,post)
    completion=check_full(post,path/'palace.stdout.log',path/'palace.stderr.log',expected)
    if plan and any(result['full'].get(k)!=completion[k] for k in
                    ('total_solves','total_iterations','max_raw_relative_rhs')):
        raise ValueError('Stored full-result differs from actual completion/residual replay')
    tables={p.name:table(p) for p in post.glob('*.csv')}
    proof=source_proof(source,frozen)
    fingerprint=dict(path=str(path),source=str(source),source_sha256=manifest['source_sha256'],
                     observed_compiler_source_sha256=observed_source_sha, native=manifest['native'],plan_sha256=sha(path/'plan.json') if plan else None,
                     config_sha256=sha(path/'config.json'), mesh_sha256=plan['identity']['mesh_sha256'] if plan else read(path/'fixture.json')['mesh_sha256'],
                     metadata_sha256=sha(post/'palace.json'), csv_sha256={p.name:sha(p) for p in post.glob('*.csv')},
                     stdout_sha256=sha(path/'palace.stdout.log'),stderr_sha256=sha(path/'palace.stderr.log'),
                     full_result_sha256=sha(path/'full-result.json') if not legacy else None)
    return dict(path=path,config=config,plan=plan,tables=tables,completion=completion,
                source_proof=proof,fingerprint=fingerprint)


def complex_columns(header, row, pattern):
    found={}
    for i,name in enumerate(header):
        match=pattern.fullmatch(name)
        if match:
            part,*key=match.groups();found.setdefault(tuple(key),{})[part]=row[i]
    if not found or any(set(x)!={'Re','Im'} for x in found.values()):
        raise ValueError('Incomplete complex columns')
    return {key:complex(value['Re'],value['Im']) for key,value in found.items()}


def wide_rows(data):
    header,rows=data
    if len({row[0] for row in rows})!=len(rows):
        raise ValueError('Duplicate wide-table frequency')
    return header,{row[0]:row for row in rows}


def scattering(data):
    header,rows=wide_rows(data);out={}
    for f,row in rows.items():
        values={}
        for dst in (1,2):
            for src in (1,2):
                db=row[header.index(f'|S[{dst}][{src}]| (dB)')]
                angle=row[header.index(f'arg(S[{dst}][{src}]) (deg.)')]
                values[dst,src]=10**(db/20)*cmath.exp(1j*math.radians(angle))
        out[f]=values
    return out


def power_gates(run,samples):
    if not run['source_proof']['passed']:
        return dict(status='NOT_RUN',passed=False,reason='Unit/source equivalence not proved')
    cfg=run['config']; tables=run['tables']
    if (any(m.get('Conductivity',0) for m in cfg['Domains']['Materials']) or
            any(cfg['Boundaries'].get(key) for key in ('Conductivity','Impedance','RationalImpedance'))):
        return dict(status='NOT_RUN',passed=False,reason='Additional conductor/impedance losses are not covered by this dielectric-only power balance')
    eh,energy=wide_rows(tables['domain-E.csv']); fh,flux=wide_rows(tables['surface-F.csv'])
    vh,voltage=wide_rows(tables['port-V.csv'])
    index_to_tan={}
    materials={attr:float(m.get('LossTan',0)) for m in cfg['Domains']['Materials'] for attr in m['Attributes']}
    covered=set()
    for item in cfg['Domains']['Postprocessing'].get('Energy',[]):
        tans={materials[attr] for attr in item['Attributes']}
        if len(tans)!=1 or covered.intersection(item['Attributes']):
            raise ValueError('Energy groups cannot uniquely resolve dielectric losses')
        index_to_tan[item['Index']]=tans.pop();covered.update(item['Attributes'])
    if any(tan>0 and attr not in covered for attr,tan in materials.items()):
        raise ValueError('Missing lossy material energy group')
    fluxes=[x for x in cfg['Boundaries']['Postprocessing']['SurfaceFlux'] if x['Type']=='Power']
    if len(fluxes)!=1:
        raise ValueError('Need exactly one outer power flux')
    rows=[]
    for f,s in samples.items():
        for port in (1,2):
            pcfg=next(p for p in cfg['Boundaries']['LumpedPort'] if p['Index']==port and p['Excitation']==port)
            vinc=voltage[f][vh.index(f'V_inc[{port}][{port}] (V)')]
            incident=vinc*vinc/pcfg['R']
            if not math.isclose(incident,1.,rel_tol=1e-9,abs_tol=1e-12):
                raise ValueError('Power check requires source-proven1W incident normalization')
            accepted=1-sum(abs(s[dst,port])**2 for dst in (1,2))
            loss=4*math.pi*f*1e9*math.fsum(tan*energy[f][eh.index(f'E_elec[{idx}][{port}] (J)')]
                                            for idx,tan in index_to_tan.items())
            outgoing=flux[f][fh.index(f'Φ_pow[{fluxes[0]["Index"]}][{port}] (W)')]
            residual=accepted-outgoing-loss
            rows.append(dict(frequency_ghz=f,port=port,incident_w=incident,accepted_w=accepted,
                             dielectric_loss_w=loss,outer_flux_w=outgoing,residual_w=residual,
                             passed=abs(residual)<=.02))
    return dict(status='RUN',passed=all(row['passed'] for row in rows),absolute_limit_w=.02,
                formula='1-|Spp|²-|Sother,p|² - outerFluxW - 4*pi*fHz*sum(LossTan*E_elec_J)',
                normalization='Source-proven1W RMS incident; current model PEC conductors and dielectric LossTan losses',rows=rows)


def farfields(run):
    header,rows=run['tables']['farfield-rE.csv']; result={}
    if header[1:4]!=['exc','theta (deg.)','phi (deg.)'] or len(header)!=10:
        raise ValueError('Unexpected farfield layout')
    for row in rows:
        key=row[0],int(row[1]);item=result.setdefault(key,dict(angles=[],values=[]))
        item['angles'].append(tuple(row[2:4]));item['values'].extend(complex(row[k],row[k+1]) for k in (4,6,8))
    return result


def compare_runs(reference,candidate,legacy_reference=False,frozen=FROZEN):
    a=load_run(reference,legacy_reference,frozen);b=load_run(candidate,False,frozen)
    if a['config']!=b['config'] or a['fingerprint']['config_sha256']!=b['fingerprint']['config_sha256'] or a['fingerprint']['mesh_sha256']!=b['fingerprint']['mesh_sha256']:
        raise ValueError('RF A/B requires exactly unchanged config and mesh')
    feature_changes={}
    if not legacy_reference:
        for run in (a,b):
            plan=run['plan'];features=plan.get('features',{})
            if plan['stage']!='full' or plan['cpu'] or plan['threads']!=1 or plan['stage_trace']:
                raise ValueError('Matched RF pair requires full GPU/OMP1/traceOFF')
            if any(k not in FEATURE_VALUES or v not in FEATURE_VALUES[k] for k,v in features.items()):
                raise ValueError('Unreviewed feature in RF pair')
            if any(plan['environment'].get(k)!=v for k,v in features.items()) or 'PALACE_STAGE_STOP' in plan['environment']:
                raise ValueError('Feature/stage environment differs from recorded policy')
        fa,fb=a['plan'].get('features',{}),b['plan'].get('features',{})
        feature_changes={k:dict(reference=fa.get(k),candidate=fb.get(k)) for k in set(fa)|set(fb) if fa.get(k)!=fb.get(k)}
        if len(feature_changes)>1:
            raise ValueError('M3 compares one prototype flag at a time')
        if {k:v for k,v in a['plan']['environment'].items() if k not in FEATURE_VALUES}!={k:v for k,v in b['plan']['environment'].items() if k not in FEATURE_VALUES}:
            raise ValueError('Uncontrolled execution environment difference')
        for key in ('identity','build','source','image_id','seconds','memory_gib','threads','cpu',
                    'stage_trace','staged_config_sha256','runner_sha256','helper_sha256','full_expectations'):
            if a['plan'][key]!=b['plan'][key]:
                raise ValueError('Matched A/B plan differs: '+key)
    if set(a['tables'])!=set(b['tables']):
        raise ValueError('CSV file sets differ')
    csv_deltas={}
    auxiliary=[]
    for name,(ah,ar) in a['tables'].items():
        bh,br=b['tables'][name]
        if ah!=bh or len(ar)!=len(br) or any(x[0]!=y[0] for x,y in zip(ar,br)):
            raise ValueError('CSV header/row/frequency layouts differ: '+name)
        csv_deltas[name]=dict(rows=len(ar),columns=len(ah),all_finite=True,
                             max_numeric_abs_delta=max(abs(x-y) for ra,rb in zip(ar,br) for x,y in zip(ra,rb)))
        # Complex S/probes/FF have dedicated gates below. Do not silently ignore other tables.
        if name not in ('port-S.csv','probe-E.csv','probe-B.csv','farfield-rE.csv'):
            columns=[dict(column=ah[i],**vector_delta([row[i] for row in ar],[row[i] for row in br]))
                     for i in range(1,len(ah))]
            auxiliary.append(dict(file=name,passed=all(x['passed'] for x in columns),
                                  checked_columns=len(columns),
                                  worst_relative_l2=max((x['relative_l2'] for x in columns if x['relative_l2'] is not None),default=None),
                                  failed_columns=[x for x in columns if not x['passed']]))
    sa,sb=scattering(a['tables']['port-S.csv']),scattering(b['tables']['port-S.csv'])
    srows=[]
    for f in sa:
        for port in (1,2):
            worst=max(abs(sb[f][dst,port]-sa[f][dst,port]) for dst in (1,2))
            va=[]
            for sample in (sa,sb):
                rho=abs(sample[f][port,port])
                if rho>=1:raise ValueError('Nonpassive reflection prevents finite VSWR')
                va.append((1+rho)/(1-rho))
            delta=abs(va[1]-va[0])
            srows.append(dict(frequency_ghz=f,port=port,max_delta_complex_S=worst,
                              reference_vswr=va[0],candidate_vswr=va[1],delta_vswr=delta,
                              passed=worst<=1e-5 and delta<=.001))
    probes=[]
    for field in ('E','B'):
        ah,ar=wide_rows(a['tables'][f'probe-{field}.csv']);bh,br=wide_rows(b['tables'][f'probe-{field}.csv'])
        pattern=re.compile(r'(Re|Im)\{'+field+r'_([xyz])\[(\d+)\]\[(\d+)\]\} \(.+\)')
        for f in ar:
            za=complex_columns(ah,ar[f],pattern);zb=complex_columns(bh,br[f],pattern)
            if za.keys()!=zb.keys():raise ValueError('Probe grids differ')
            for port in (1,2):
                keys=sorted(key for key in za if int(key[-1])==port)
                delta=vector_delta([za[k] for k in keys],[zb[k] for k in keys])
                probes.append(dict(field=field,port=port,frequency_ghz=f,complex_components=len(keys),
                                   units='V/m' if field=='E' else 'Wb/m²',**delta))
    fa,fb=farfields(a),farfields(b);ffrows=[];ffpower=[]
    if fa.keys()!=fb.keys():raise ValueError('Farfield frequency/port grids differ')
    for key in fa:
        x,y=fa[key],fb[key]
        if x['angles']!=y['angles']:raise ValueError('Farfield angle grids differ')
        if not all(run['source_proof']['passed'] for run in (a,b)):
            ffrows.append(dict(frequency_ghz=key[0],port=key[1],status='NOT_RUN',passed=False,reason='Unit/source equivalence not proved'))
            continue
        scale=Z0/(a['config']['Model']['L0']*a['config']['Model']['Lc'])
        ffrows.append(dict(frequency_ghz=key[0],port=key[1],status='RUN',field_units='V',
                           angles=len(x['angles']),complex_components=len(x['values']),
                           weighting='Unweighted all reported complex Cartesian field components',
                           **vector_delta([z*scale for z in x['values']],[z*scale for z in y['values']])))
    for run,fields,label in ((a,fa,'reference'),(b,fb,'candidate')):
        if not run['source_proof']['passed']:
            ffpower.append(dict(run=label,status='NOT_RUN',passed=False,reason='Unit/source equivalence not proved'));continue
        scale=Z0/(run['config']['Model']['L0']*run['config']['Model']['Lc'])
        fh,flux=wide_rows(run['tables']['surface-F.csv'])
        flux_index=next(x['Index'] for x in run['config']['Boundaries']['Postprocessing']['SurfaceFlux'] if x['Type']=='Power')
        n=run['config']['Boundaries']['Postprocessing']['FarField']['NSample']
        for (f,port),data in fields.items():
            vectors=[[z*scale for z in data['values'][i:i+3]] for i in range(0,len(data['values']),3)]
            q=sphere_power(data['angles'],vectors,n)
            outgoing=flux[f][fh.index(f'Φ_pow[{flux_index}][{port}] (W)')]
            if outgoing<=0:raise ValueError('Farfield/flux requires positive flux')
            ratio=q['power_w']/outgoing
            ffpower.append(dict(run=label,frequency_ghz=f,port=port,status='RUN',scale=scale,
                                flux_w=outgoing,ratio=ratio,relative_error=abs(ratio-1),
                                passed=abs(ratio-1)<=.02,**q))
    powers={'reference':power_gates(a,sa),'candidate':power_gates(b,sb)}
    passed=all(row['passed'] for row in srows+probes+ffrows+ffpower+auxiliary) and all(x['passed'] for x in powers.values())
    return dict(scope='Diagnostic legacy comparison, not same-build timing evidence' if legacy_reference else 'One matched full RF A/B pair; not repeated medians or hardware generalization',
                passed=passed,one_pair_rf_gates_passed=passed,production_promoted=False,
                legacy_reference=legacy_reference,intentional_feature_changes=feature_changes,
                reference=a['fingerprint'],candidate=b['fingerprint'],
                completion={'reference':a['completion'],'candidate':b['completion']},
                source_unit_proof={'reference':a['source_proof'],'candidate':b['source_proof']},
                csv_delta_scope='All CSV cells finite and header/grid layouts equal; complex S/probe/FF gates separate, other numeric CSV columns each checked at relativeL2 1e-5 or near-zero absoluteL2 1e-12',
                csv=csv_deltas,auxiliary_numeric_csv=auxiliary,scattering=srows,probes=probes,farfield_complex=ffrows,
                power_balance=powers,farfield_to_flux=ffpower,
                limits=dict(complex_S=1e-5,delta_VSWR=.001,field_relative_L2=FIELD_REL,
                            near_zero_absolute_L2=FIELD_ABS,power_residual_w=.02,farfield_flux_relative=.02),
                tool_sha256=sha(__file__))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('reference',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--legacy-reference',action='store_true')
    args=p.parse_args()
    try:
        report=compare_runs(args.reference,args.candidate,args.legacy_reference)
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as error:
        report=dict(passed=False,one_pair_rf_gates_passed=False,production_promoted=False,
                    scope='Input/provenance/completeness rejection; no RF qualification',
                    error=repr(error),tool_sha256=sha(__file__))
    with args.output.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'passed':report['passed'],'output':str(args.output),'production_promoted':False}))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()
