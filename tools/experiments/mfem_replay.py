"""Replay saved FEM on identical interior probes; not a converged volume norm.

No boundary solve or new BEM potentials. Strict interior point location avoids
choosing a normal-field value arbitrarily on a refined FEM face.
"""
import argparse
import json
from pathlib import Path
import resource
import time
import numpy as np
import maxwell_nd as nd


def locate(vertices,tetrahedra,points,chunk=128):
    points=np.asarray(points)
    if points.ndim!=2 or points.shape[1]!=3 or not len(points) or not np.isfinite(points).all() or chunk<1:
        raise ValueError('Expected nonempty finite probe points and positive chunk')
    cells=vertices[tetrahedra]
    inverse=np.linalg.inv(np.transpose(cells[:,1:]-cells[:,:1],(0,2,1)))
    owners=[];coordinates=[];margin=1.
    for first in range(0,len(points),chunk):
        local=np.einsum('tij,ptj->pti',inverse,points[first:first+chunk,None,:]-cells[None,:,0,:])
        bary=np.concatenate([1-local.sum(axis=2,keepdims=True),local],axis=2)
        inside=bary.min(axis=2)>1e-10
        if not np.all(inside.sum(axis=1)==1):
            raise ValueError('Probe lies outside or on/too close to a FEM cell face')
        owner=np.argmax(inside,axis=1);index=np.arange(len(owner))
        owners.extend(owner);coordinates.extend(local[index,owner]);margin=min(margin,float(bary[index,owner].min()))
    return np.asarray(owners),np.asarray(coordinates),margin


def run(level,output,candidate,reference,probes):
    begin=time.monotonic()
    case=json.loads((candidate/'case.json').read_text())
    sample_case=json.loads((probes/'case.json').read_text())
    ref_case=json.loads((reference/'case.json').read_text())
    if case['level']!=level or sample_case['volume_degree']!=2 or not case['epsilon_r']==sample_case['epsilon_r']==ref_case['epsilon_r']:
        raise ValueError('Replay level/material/degree mismatch')
    with np.load(candidate/'coupled-solution.npz',allow_pickle=False) as data:
        coefficients=data['electric_fem']
        if int(data['level'])!=level or float(data['epsilon_r'])!=case['epsilon_r']:raise ValueError('Saved coefficient metadata mismatch')
    sample=np.load(probes/'volume-fields.npz',allow_pickle=False)
    points,weights=sample['points'],sample['weights']
    if weights.shape!=(len(points),) or not np.isfinite(weights).all() or not (weights>0).all() or abs(weights.sum()-4*np.pi/3)>1e-12:
        raise ValueError('Probes must cover the audited positive-volume rule')
    vertices,tets,faces=nd.fem.mesh(level-1)
    owner,local,margin=locate(vertices,tets,points)
    electric=np.empty(points.shape,complex);magnetic=np.empty(points.shape,complex)
    with nd.GlobalND(vertices,tets,faces) as space:
        if coefficients.shape!=(space.ndofs,) or not np.isfinite(coefficients).all():raise ValueError('Invalid saved FEM vector')
        for cell in np.unique(owner):
            ids=np.flatnonzero(owner==cell)
            value,curl=space.evaluate(int(cell),local[ids],coefficients)
            electric[ids],magnetic[ids]=value,curl/1j
        dofs=space.ndofs
    if not np.isfinite(electric).all() or not np.isfinite(magnetic).all():raise ValueError('Nonfinite replayed fields')
    np.savez(output/'probe-fields.npz',points=points,weights=weights,coupled_E=electric,coupled_H=magnetic,
             previous_E=sample['coupled_E'],previous_H=sample['coupled_H'],cells=owner,local_points=local)
    report=dict(scope=__doc__,level=level,probe_level=sample_case['level'],probe_degree=2,
        epsilon_r=case['epsilon_r'],fem_dofs=dofs,points=len(points),min_cell_barycentric_margin=margin,
        execution_passed=True,analytic_target_passed=False,elapsed_seconds=time.monotonic()-begin,
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        limitations=['Fixed coarse probes are not a converged norm on the refined FEM mesh',
                     'Existing GlobalND constructor assembles small mass/curl forms; no new solve or BEM assembly'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level',type=int,choices=[1,2,3],required=True)
    for name in ['output','candidate','reference','probes']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    run(args.level,args.output,args.candidate,args.reference,args.probes)
