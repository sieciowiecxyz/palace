"""Optional cached Numba FP64/complex128 implementation of the near-panel oracle.

Same panel integrals, child order and distance rule as maxwell_near.py. No
fastmath, changed tolerance, GPU backend or working arrays stored on disk.
"""
import numpy as np
from numba import njit


@njit(cache=True)
def _integrate(point,vertices,currents,divergence,k,points,weights,child):
    result=np.zeros((4,3),np.complex128)
    d0,d1=child[1]-child[0],child[2]-child[0]
    determinant=abs(d0[0]*d1[1]-d0[1]*d1[0])
    v0,v1=vertices[1]-vertices[0],vertices[2]-vertices[0]
    cross=np.cross(v0,v1)
    jacobian=np.sqrt(np.dot(cross,cross))*determinant
    delta=np.zeros(3)
    gradient=np.zeros(3,np.complex128)
    current=np.zeros((2,3),np.complex128)
    for q in range(len(weights)):
        u=child[0,0]+points[0,q]*d0[0]+points[1,q]*d1[0]
        v=child[0,1]+points[0,q]*d0[1]+points[1,q]*d1[1]
        for c in range(3):delta[c]=point[c]-vertices[0,c]-u*v0[c]-v*v1[c]
        r2=np.dot(delta,delta)
        if r2<=0:raise ValueError('Target coincides with a panel quadrature point')
        r=np.sqrt(r2)
        green=np.exp(1j*k*r)/(4*np.pi*r)
        factor=green*(1j*k*r-1)/r2
        for c in range(3):
            gradient[c]=factor*delta[c]
            for j in range(2):
                current[j,c]=currents[j,0,c]+u*(currents[j,1,c]-currents[j,0,c])+v*(currents[j,2,c]-currents[j,0,c])
        weight=weights[q]*jacobian
        for j in range(2):
            for c in range(3):
                result[2*j,c]+=weight*(1j*k*green*current[j,c]-divergence[j]*gradient[c]/(1j*k))
            result[2*j+1,0]+=weight*(gradient[1]*current[j,2]-gradient[2]*current[j,1])
            result[2*j+1,1]+=weight*(gradient[2]*current[j,0]-gradient[0]*current[j,2])
            result[2*j+1,2]+=weight*(gradient[0]*current[j,1]-gradient[1]*current[j,0])
    return result


@njit(cache=True)
def _adaptive(point,vertices,currents,divergence,k,points,weights,ratio,max_depth):
    capacity=3*max_depth+1
    stack=np.zeros((capacity,3,2))
    depths=np.zeros(capacity,np.int64)
    stack[0,1,0]=stack[0,2,1]=1.
    top=1
    result=np.zeros((4,3),np.complex128)
    leaves=hits=deepest=0
    physical=np.zeros((3,3))
    while top:
        top-=1
        triangle=stack[top].copy()
        depth=depths[top]
        for i in range(3):
            for c in range(3):
                physical[i,c]=vertices[0,c]+triangle[i,0]*(vertices[1,c]-vertices[0,c])+triangle[i,1]*(vertices[2,c]-vertices[0,c])
        diameter2=0.
        for a in range(3):
            for b in range(a):
                distance2=0.
                for c in range(3):distance2+=(physical[a,c]-physical[b,c])**2
                diameter2=max(diameter2,distance2)
        distance2=0.
        for c in range(3):distance2+=(point[c]-(physical[0,c]+physical[1,c]+physical[2,c])/3)**2
        close=distance2<ratio*ratio*diameter2
        if close and depth<max_depth:
            va,vb,vc=triangle[0],triangle[1],triangle[2]
            ab,ac,bc=(va+vb)/2,(va+vc)/2,(vb+vc)/2
            children=np.empty((4,3,2))
            children[0,0],children[0,1],children[0,2]=va,ab,ac
            children[1,0],children[1,1],children[1,2]=ab,vb,bc
            children[2,0],children[2,1],children[2,2]=ac,bc,vc
            children[3,0],children[3,1],children[3,2]=ab,bc,ac
            for child in range(4):
                stack[top]=children[child]
                depths[top]=depth+1
                top+=1
        else:
            result+=_integrate(point,vertices,currents,divergence,k,points,weights,triangle)
            leaves+=1
            deepest=max(deepest,depth)
            hits+=int(close)
    return result,leaves,deepest,hits


def arguments(point,panel,k,points,weights):
    return (np.ascontiguousarray(point,dtype=np.float64),np.ascontiguousarray(panel[0],dtype=np.float64),
            np.ascontiguousarray(panel[1],dtype=np.complex128),np.ascontiguousarray(panel[2],dtype=np.complex128),
            float(k),np.ascontiguousarray(points,dtype=np.float64),np.ascontiguousarray(weights,dtype=np.float64))


def integrate(point,panel,k,points,weights,child=None):
    child=np.array([[0.,0.],[1.,0.],[0.,1.]]) if child is None else np.ascontiguousarray(child,dtype=np.float64)
    return _integrate(*arguments(point,panel,k,points,weights),child)


def adaptive(point,panel,k,points,weights,ratio=4.,max_depth=12):
    if ratio<=0 or max_depth<0:raise ValueError('Invalid panel refinement limits')
    result,leaves,depth,hits=_adaptive(*arguments(point,panel,k,points,weights),float(ratio),int(max_depth))
    return result,dict(leaves=leaves,max_depth=depth,depth_hits=hits)
