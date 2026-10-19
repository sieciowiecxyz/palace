"""Bounded correction of saved BEM potentials; subset default, full replay explicit.

By default half the targets emphasize old q12/q16 disagreement and the rest
span the data; explicit count0 replays every saved volume-quadrature point.
Subtract the original regular integral only for nearby panels, then add the
distance-refined integral. No new FEM/BEM assembly or solve; CPU/RAM only.
"""
import argparse
import json
from pathlib import Path
import resource
import time
import numpy as np
import bempp_cl.api as bem
from bempp_cl.api.integration.triangle_gauss import rule
import bempp_pairing as pairing
import bempp_transmission as transmission
import maxwell_near as near


def select(scores,limit=32):
    if limit==0:return np.arange(len(scores),dtype=np.int64)
    limit=min(limit,len(scores))
    chosen=list(np.argsort(scores,kind='stable')[-(limit//2):])
    for count in [limit//2,limit,len(scores)]:
        if len(chosen)>=limit:break
        for index in np.linspace(0,len(scores)-1,max(1,count),dtype=int):
            if index not in chosen:chosen.append(int(index))
            if len(chosen)>=limit:break
    return np.asarray(sorted(chosen),dtype=np.int64)


def blend(values,rho):
    return values[1]+values[2]/rho,values[3]-rho*values[0]


def correct(points,panels,epsilon,e,h,order,radius,stage):
    rho=np.sqrt(epsilon)
    regular=rule(12)
    adaptive=pairing.quadrature(order)
    centers=np.asarray([p[0].mean(axis=0) for p in panels])
    diameters=np.asarray([max(np.linalg.norm(p[0][a]-p[0][b]) for a,b in [(0,1),(0,2),(1,2)]) for p in panels])
    fields_e,fields_h=e.copy(),h.copy()
    before=time.monotonic()
    leaves=hits=panel_count=deepest=0
    for i,point in enumerate(points):
        selected=np.flatnonzero(np.linalg.norm(centers-point,axis=1)<radius*diameters)
        delta=np.zeros((4,3),complex)
        for index in selected:
            panel=panels[index]
            old=near.integrate(point,panel,rho,*regular)
            new,stats=near.adaptive(point,panel,rho,*adaptive,ratio=2.)
            delta+=new-old
            leaves+=stats['leaves'];hits+=stats['depth_hits'];deepest=max(deepest,stats['max_depth'])
        de,dh=blend(delta,rho)
        fields_e[i]+=de;fields_h[i]+=dh
        panel_count+=len(selected)
        stage(f'correct_q{order}_radius{radius:g}',done=i+1,total=len(points))
    return fields_e,fields_h,dict(order=order,radius=radius,panels=panel_count,leaves=leaves,
                                depth_hits=hits,max_depth=deepest,seconds=time.monotonic()-before)


def run(level,output,candidate,reference,count=32):
    begin=time.monotonic()
    def stage(name,**extra):
        row=dict(stage=name,elapsed_s=time.monotonic()-begin,**extra)
        (output/'progress.json').write_text(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True)
    case=json.loads((candidate/'case.json').read_text())
    if case['level']!=level:raise ValueError('Saved volume level mismatch')
    data=np.load(candidate/'volume-fields.npz',allow_pickle=False)
    scores=np.linalg.norm(data['reference_q12_E']-data['reference_E'],axis=1)+np.linalg.norm(data['reference_q12_H']-data['reference_H'],axis=1)
    indices=select(scores,count)
    points,weights=data['points'][indices],data['weights'][indices]
    epsilon=case['epsilon_r']
    ref_level=case['reference_surface_level']
    with np.load(reference/f'pmchwt-level{ref_level}.npz',allow_pickle=False) as current:
        if float(current['epsilon_r'])!=epsilon or int(current['level'])!=ref_level:raise ValueError('Current physics mismatch')
        t,h=current['electric_trace'],current['magnetic_trace']
    space=bem.function_space(transmission.surface(ref_level),'RWG',0)
    panels=near.panels(space,t,h)
    # Validate actual saved-current reconstruction against cached native q12 values.
    control_indices=np.unique([0,len(points)-1,int(np.argmax(scores[indices]))])
    reconstructed_e,reconstructed_h=[],[]
    for index in control_indices:
        values=sum((near.integrate(points[index],p,np.sqrt(epsilon),*rule(12)) for p in panels),np.zeros((4,3),complex))
        e,magnetic=blend(values,np.sqrt(epsilon))
        reconstructed_e.append(e);reconstructed_h.append(magnetic)
    old_e,old_h=data['reference_q12_E'][indices],data['reference_q12_H'][indices]
    native_checks=dict(E=transmission.relative(np.asarray(reconstructed_e),old_e[control_indices]),
                       H=transmission.relative(np.asarray(reconstructed_h),old_h[control_indices]))
    if max(native_checks.values())>1e-12:raise ValueError('Saved-current panel reconstruction differs from native q12')
    stage('saved_current_native_q12_control_complete',points=len(control_indices))
    e6,h6,s6=correct(points,panels,epsilon,old_e,old_h,6,2.,stage)
    e8,h8,s8=correct(points,panels,epsilon,old_e,old_h,8,2.,stage)
    e4,h4,s4=correct(points,panels,epsilon,old_e,old_h,8,4.,stage)
    rel=lambda a,b:transmission.relative(a,b,weights)
    quadrature=dict(E=rel(e6,e8),H=rel(h6,h8))
    cutoff=dict(E=rel(e8,e4),H=rel(h8,h4))
    change=dict(E=rel(data['reference_E'][indices],e4),H=rel(data['reference_H'][indices],h4))
    finite=bool(all(np.isfinite(x).all() for x in [e6,h6,e8,h8,e4,h4]))
    all_points=len(indices)==len(scores)
    report=dict(scope=__doc__,level=level,epsilon_r=epsilon,source_volume_degree=case['volume_degree'],
                original_points=len(scores),selected_points=len(indices),reference_level=ref_level,
                all_volume_points=all_points,
                corrected_volume_estimate=dict(E=rel(data['coupled_E'][indices],e4),H=rel(data['coupled_H'][indices],h4)) if all_points else None,
                native_q12_control=native_checks,adaptive_q6_vs8=quadrature,near_radius2_vs4=cutoff,
                old_q16_vs_corrected=change,correction_stats=[s6,s8,s4],
                execution_passed=finite,analytic_target_passed=False,
                correction_control_passed=bool(finite and max(quadrature.values())<1e-6 and max(cutoff.values())<1e-6
                                              and not any(s['depth_hits'] for s in [s6,s8,s4])),
                elapsed_seconds=time.monotonic()-begin,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                target=dict(native_kernel=1e-12,adaptive_quadrature=1e-6,near_radius=1e-6),
                limitations=['Subset is biased; full replay still requires volume-rule convergence and coarse-reference control',
                             'Only fine-reference potentials corrected; coarse-reference convergence remains unqualified',
                             'No change to saved currents or FEM coefficients; no antenna promotion'])
    np.savez(output/'correction-fields.npz',indices=indices,points=points,weights=weights,old_q16_E=data['reference_E'][indices],
             old_q16_H=data['reference_H'][indices],corrected6_E=e6,corrected6_H=h6,corrected8_E=e8,corrected8_H=h8,
             corrected_radius4_E=e4,corrected_radius4_H=h4)
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--near-count',type=int,choices=[0,32],default=32,help='0 replays all saved points;32 is a bounded biased diagnostic')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.level,args.output,args.candidate,args.reference,args.near_count)
