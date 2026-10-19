"""Bounded point/panel potential apply, FP64/complex128, no potential matrix.

Reuses qualified panel kernels without fastmath. Independent targets use the
existing Numba thread limit; panel summation order is unchanged per target.
"""
import numpy as np
from numba import njit, prange
import maxwell_near_jit as kernel


@njit(cache=True,parallel=True)
def _evaluate(points,vertices,currents,divergence,centers,diameters2,k,
              far_points,far_weights,near_points,near_weights,radius,max_depth):
    fields=np.zeros((len(points),4,3),np.complex128)
    counts=np.zeros((len(points),4),np.int64)
    triangle=np.array([[0.,0.],[1.,0.],[0.,1.]])
    for i in prange(len(points)):
        field=np.zeros((4,3),np.complex128)
        selected=leaves=hits=deepest=0
        for j in range(len(vertices)):
            distance2=0.
            for c in range(3):distance2+=(points[i,c]-centers[j,c])**2
            if distance2<radius*radius*diameters2[j]:
                value,nleaf,depth,nhit=kernel._adaptive(points[i],vertices[j],currents[j],divergence[j],k,
                    near_points,near_weights,2.,max_depth)
                selected+=1;leaves+=nleaf;hits+=nhit;deepest=max(deepest,depth)
            else:
                value=kernel._integrate(points[i],vertices[j],currents[j],divergence[j],k,
                    far_points,far_weights,triangle)
            field+=value
        fields[i]=field
        counts[i,0]=selected;counts[i,1]=leaves;counts[i,2]=hits;counts[i,3]=deepest
    return fields,counts


def pack(panels):
    if not len(panels):raise ValueError('Expected physical panels')
    vertices,currents,divergence=[np.ascontiguousarray([p[i] for p in panels],dtype=np.float64 if i==0 else np.complex128) for i in range(3)]
    if vertices.shape!=(len(panels),3,3) or currents.shape!=(len(panels),2,3,3) or divergence.shape!=(len(panels),2):
        raise ValueError('Unexpected physical panel layout')
    if not all(np.isfinite(a).all() for a in [vertices,currents,divergence]):raise ValueError('Nonfinite physical panels')
    centers=np.ascontiguousarray(vertices.mean(axis=1))
    diameters2=np.ascontiguousarray(np.max(np.stack([np.sum((vertices[:,a]-vertices[:,b])**2,axis=1) for a,b in [(0,1),(0,2),(1,2)]]),axis=0))
    if (diameters2<=0).any():raise ValueError('Degenerate physical panel')
    return vertices,currents,divergence,centers,diameters2


def evaluate(points,packed,k,far_rule,near_rule,radius=4.,max_depth=12):
    points=np.ascontiguousarray(points,dtype=np.float64)
    if points.ndim!=2 or points.shape[1]!=3 or not len(points) or not np.isfinite(points).all():raise ValueError('Expected nonempty finite targets')
    if not np.isfinite(k) or k<=0 or not np.isfinite(radius) or radius<0 or not 0<=max_depth<=12:raise ValueError('Invalid bounded potential parameters')
    rules=[np.ascontiguousarray(a,dtype=np.float64) for rule in [far_rule,near_rule] for a in rule]
    for q,w in [(rules[0],rules[1]),(rules[2],rules[3])]:
        if q.shape!=(2,len(w)) or not len(w) or not np.isfinite(q).all() or not np.isfinite(w).all():raise ValueError('Invalid triangle rule')
    fields,counts=_evaluate(points,*packed,float(k),*rules,float(radius),int(max_depth))
    return fields,dict(selected_panels=int(counts[:,0].sum()),leaves=int(counts[:,1].sum()),
        depth_hits=int(counts[:,2].sum()),max_depth=int(counts[:,3].max()),
        regular_panels=int(len(points)*len(packed[0])-counts[:,0].sum()))
