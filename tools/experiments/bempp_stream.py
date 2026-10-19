"""Fused saved-current potential apply without new solves.

Control compares with cached native q12 plus qualified incremental correction.
Volume mode evaluates the saved FEM on its own positive cell quadrature.
"""
import argparse
import json
from pathlib import Path
import resource
import time
import numpy as np
import numba
import bempp_cl.api as bem
from bempp_cl.api.integration.triangle_gauss import rule
import bempp_transmission as transmission
import bempp_pairing as pairing
import bempp_volume as volume
import bempp_near_correction as correction
import maxwell_near as near
import maxwell_near_jit as kernel
import maxwell_stream as stream

VARIANTS={'base':(12,8,4.),'near6':(12,6,4.),'radius2':(12,8,2.),'far16':(16,8,4.)}


def saved_fem(level,candidate,degree):
    with np.load(candidate/'coupled-solution.npz',allow_pickle=False) as data:
        u=data['electric_fem'];epsilon=float(data['epsilon_r'])
        if int(data['level'])!=level:raise ValueError('Saved FEM level mismatch')
    nodes,qweights=volume.tetra_rule(degree)
    vertices,tets,faces=transmission.coupled.fem.mesh(level-1)
    fields=[[],[],[],[]]
    with transmission.coupled.nd.GlobalND(vertices,tets,faces) as space:
        if u.shape!=(space.ndofs,) or not np.isfinite(u).all():raise ValueError('Invalid saved ND2 vector')
        for cell,tet in enumerate(tets):
            v=vertices[tet];jac=np.linalg.det((v[1:]-v[0]).T)
            ids,value,curl=space.basis(cell,nodes[:,1:])
            for target,x in zip(fields,[nodes@v,jac*qweights,np.einsum('i,pic->pc',u[ids],value),np.einsum('i,pic->pc',u[ids],curl)/1j]):target.append(x)
    points,weights,e,h=map(np.concatenate,fields)
    if not (weights>0).all() or abs(weights.sum()-4*np.pi/3)>1e-12:raise ValueError('Invalid volume rule coverage')
    # Deliberately bias a pilot towards the hardest near-surface points.
    v,_,f=transmission.coupled.fem.mesh(0);tri=v[f]
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
    distance=np.min(np.einsum('fc,pfc->pf',normals,tri[None,:,0]-points[:,None]),axis=1)
    if distance.min()<=0:raise ValueError('Volume target outside fixed polyhedron')
    return points,weights,e,h,-distance,epsilon


def run(level,output,candidate,reference,mode,side,count,degree,variant):
    begin=time.monotonic()
    def stage(name,**extra):
        row=dict(stage=name,elapsed_s=time.monotonic()-begin,**extra)
        (output/'progress.json').write_text(json.dumps(row)+'\n');print(json.dumps(row),flush=True)
    if mode=='control':
        sample_case=json.loads((candidate/'case.json').read_text())
        if sample_case['level']!=level:raise ValueError('Saved volume level mismatch')
        sample=np.load(candidate/'volume-fields.npz',allow_pickle=False)
        points,weights,e,h=[sample[k] for k in ['points','weights','coupled_E','coupled_H']]
        scores=np.linalg.norm(sample['reference_q12_E']-sample['reference_E'],axis=1)+np.linalg.norm(sample['reference_q12_H']-sample['reference_H'],axis=1)
        epsilon=sample_case['epsilon_r']
    else:
        points,weights,e,h,scores,epsilon=saved_fem(level,candidate,degree)
    original_points=len(points);indices=correction.select(scores,count)
    points,weights,e,h=[a[indices] for a in [points,weights,e,h]]
    ref_case=json.loads((reference/'case.json').read_text())
    if ref_case['epsilon_r']!=epsilon:raise ValueError('Reference epsilon mismatch')
    ref_level=ref_case['surface_level']-(side=='coarse')
    with np.load(reference/f'pmchwt-level{ref_level}.npz',allow_pickle=False) as data:
        if int(data['level'])!=ref_level or float(data['epsilon_r'])!=epsilon:raise ValueError('Reference current metadata mismatch')
        t,htrace=data['electric_trace'],data['magnetic_trace']
    space=bem.function_space(transmission.surface(ref_level),'RWG',0)
    if t.shape!=(space.global_dof_count,) or htrace.shape!=t.shape:raise ValueError('Reference current layout mismatch')
    before=time.monotonic()
    panels=near.panels(space,t,htrace);packed=stream.pack(panels);rho=np.sqrt(epsilon)
    panel_setup_seconds=time.monotonic()-before
    far_order,near_order,radius=VARIANTS[variant];far_rule=rule(far_order);near_rule=pairing.quadrature(near_order)
    before=time.monotonic();stream.evaluate(points[:1],packed,rho,far_rule,near_rule,radius)
    setup_seconds=time.monotonic()-before
    def evaluate(radius):
        before=time.monotonic();fields=[];totals=dict(selected_panels=0,regular_panels=0,leaves=0,depth_hits=0,max_depth=0)
        for first in range(0,len(points),128):
            values,stats=stream.evaluate(points[first:first+128],packed,rho,far_rule,near_rule,radius)
            fields.append(values)
            for key in totals:totals[key]=max(totals[key],stats[key]) if key=='max_depth' else totals[key]+stats[key]
            stage('stream_apply',done=min(first+128,len(points)),total=len(points),radius=radius)
        values=np.concatenate(fields);totals['seconds']=time.monotonic()-before
        return values[:,1]+values[:,2]/rho,values[:,3]-rho*values[:,0],totals
    apply_samples=[]
    for _ in range(3 if mode=='control' else 1):
        ref_e,ref_h,stats=evaluate(radius)
        apply_samples.append(stats['seconds'])
    rel=lambda a,b:transmission.relative(a,b,weights)
    controls=None
    if mode=='control':
        base='reference_q12_' if side=='fine' else 'coarse_'
        old_e,old_h=sample[base+'E'][indices],sample[base+'H'][indices]
        regular_e,regular_h,regular_stats=evaluate(0.)
        expected_e,expected_h,expected_stats=correction.correct(points,panels,epsilon,old_e,old_h,near_order,radius,stage,kernel)
        native_params=bem.DefaultParameters();native_params.quadrature.regular=12
        before=time.monotonic();transmission.interior(space,t,htrace,points[:1],epsilon,native_params)
        native_setup_seconds=time.monotonic()-before
        native_samples=[]
        for _ in range(3):
            before=time.monotonic();native_e,native_h=transmission.interior(space,t,htrace,points,epsilon,native_params)
            native_samples.append(time.monotonic()-before)
        controls=dict(native_q12=dict(E=rel(regular_e,old_e),H=rel(regular_h,old_h)),
                      actual_native_q12=dict(E=rel(native_e,old_e),H=rel(native_h,old_h)),
                      incremental=dict(E=rel(ref_e,expected_e),H=rel(ref_h,expected_h)),
                      regular_stats=regular_stats,incremental_stats=expected_stats,
                      native_compile_or_load_seconds=native_setup_seconds,native_evaluation_seconds=float(np.median(native_samples)),
                      native_samples_seconds=native_samples,fused_apply_samples_seconds=apply_samples)
    finite=bool(all(np.isfinite(a).all() for a in [ref_e,ref_h,e,h]))
    report=dict(scope=__doc__,level=level,epsilon_r=epsilon,mode=mode,reference_side=side,reference_level=ref_level,
        variant=variant,far_order=far_order,near_order=near_order,near_radius=radius,
        original_points=original_points,selected_points=len(points),all_volume_points=len(indices)==original_points,
        volume_degree=degree if mode=='volume' else sample_case['volume_degree'],
        selection_basis='All points for count0; otherwise worst near-surface volume points or cached q12/q16 disagreement plus spanning points',
        field_probe_estimate=dict(E=rel(e,ref_e),H=rel(h,ref_h)),stats=stats,controls=controls,
        jit_compile_or_load_seconds=setup_seconds,panel_setup_seconds=panel_setup_seconds,numba_threads=numba.get_num_threads(),
        nopython_signatures=[str(s) for s in stream._evaluate.nopython_signatures],
        execution_passed=finite,analytic_target_passed=False,
        operator_control_passed=bool(controls and max(v for key in ['native_q12','actual_native_q12','incremental'] for v in controls[key].values())<1e-12 and not stats['depth_hits']) if mode=='control' else None,
        elapsed_seconds=time.monotonic()-begin,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        limitations=['Pilot is biased; complete cell quadrature still needs degree, near/far integration and reference mesh convergence',
                     'No new solve/BEM operator assembly; GlobalND constructor in volume mode assembles small mass/curl forms',
                     'CPU potential apply, not a GPU antenna speedup'])
    np.savez(output/'stream-fields.npz',indices=indices,points=points,weights=weights,coupled_E=e,coupled_H=h,reference_E=ref_e,reference_H=ref_h)
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    for name in ['output','candidate','reference']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--mode',choices=['control','volume'],required=True)
    parser.add_argument('--near-side',choices=['fine','coarse'],default='fine')
    parser.add_argument('--near-count',type=int,choices=[0,32],default=32)
    parser.add_argument('--volume-degree',type=int,choices=[2,5],default=2)
    parser.add_argument('--stream-variant',choices=list(VARIANTS),default='base')
    args=parser.parse_args()
    run(args.level,args.output,args.candidate,args.reference,args.mode,args.near_side,args.near_count,args.volume_degree,args.stream_variant)
