"""Small physical RWG panel potentials and distance-based subdivision, CPU/RAM.

Convention matches pinned Bempp exp(-iwt): T=ik*S - grad(S*div)/(ik),
K=curl(S). No new boundary solver or modification of installed Bempp.
"""
import numpy as np


def laplace_normal_reference(vertices,point):
    """Independent analytic normal grad(single layer), via pinned SciPy solid angle.

    Diagnostic only, never used by integrate/adaptive. Vertex order fixes the
    normal; formula of Van Oosterom/Strackee, DOI10.1109/TBME.1983.325207.
    """
    from scipy.spatial._spherical_voronoi import calculate_solid_angles
    directions=np.asarray(vertices)-np.asarray(point)
    lengths=np.linalg.norm(directions,axis=1)
    if np.min(lengths)<=0:raise ValueError('Solid angle target coincides with a vertex')
    orientation=np.sign(np.linalg.det(directions))
    angle=calculate_solid_angles((directions/lengths[:,None])[None,:,:])[0]
    return float(orientation*angle/(4*np.pi))


def panels(space,t,h):
    """Affine currents and constant surface divergence from actual physical basis."""
    t,h=np.asarray(t),np.asarray(h)
    if t.shape!=h.shape or t.shape!=(space.global_dof_count,) or not np.isfinite([t,h]).all():
        raise ValueError('Expected two finite current vectors in the actual space')
    coefficients=space.dof_transformation@np.stack([t,h],axis=1)
    points=np.array([[0.,1.,0.],[0.,0.,1.]])
    result=[]
    for triangle in space.support_elements:
        vertices=space.grid.vertices[:,space.grid.elements[:,triangle]].T
        jacobian=(vertices[1:]-vertices[0]).T
        basis=space.evaluate(triangle,points)
        local=coefficients[space.local2global[triangle]]
        currents=np.einsum('ik,cip->kpc',local,basis)
        inverse=np.linalg.solve(jacobian.T@jacobian,jacobian.T)
        divergence=np.asarray([np.trace((j[1:]-j[0]).T@inverse) for j in currents])
        result.append((vertices,currents,divergence))
    return result


def integrate(point,panel,k,points,weights,child=None):
    """Return T[t],K[t],T[h],K[h] for one (sub)triangle and one target."""
    vertices,currents,divergence=panel
    child=np.array([[0.,0.],[1.,0.],[0.,1.]]) if child is None else child
    delta=child[1:]-child[0]
    uv=child[0]+points.T@delta
    y=vertices[0]+uv@(vertices[1:]-vertices[0])
    j=currents[:,0,None,:]+np.einsum('pi,kic->kpc',uv,currents[:,1:]-currents[:,:1])
    difference=point-y
    radius=np.linalg.norm(difference,axis=1)
    if np.min(radius)<=0:raise ValueError('Target coincides with a panel quadrature point')
    green=np.exp(1j*k*radius)/(4*np.pi*radius)
    gradient=(green*(1j*k*radius-1)/radius**2)[:,None]*difference
    weighted=weights*np.linalg.norm(np.cross(vertices[1]-vertices[0],vertices[2]-vertices[0]))*abs(np.linalg.det(delta))
    electric=np.einsum('p,kpc->kc',weighted,1j*k*green[None,:,None]*j-
                        divergence[:,None,None]*gradient[None,:,:]/(1j*k))
    magnetic=np.einsum('p,kpc->kc',weighted,np.cross(gradient[None,:,:],j))
    return np.stack([electric[0],magnetic[0],electric[1],magnetic[1]])


def adaptive(point,panel,k,points,weights,ratio=4.,max_depth=12):
    """Subdivide nearby triangles only; report exhausted depth, never hide it."""
    if ratio<=0 or max_depth<0:raise ValueError('Invalid panel refinement limits')
    root=np.array([[0.,0.],[1.,0.],[0.,1.]])
    stack=[(root,0)]
    result=np.zeros((4,3),complex)
    leaves=depth_hits=deepest=0
    vertices=panel[0]
    while stack:
        triangle,depth=stack.pop()
        physical=vertices[0]+triangle@(vertices[1:]-vertices[0])
        diameter=max(np.linalg.norm(physical[a]-physical[b]) for a,b in [(0,1),(0,2),(1,2)])
        near=np.linalg.norm(point-physical.mean(axis=0))<ratio*diameter
        if near and depth<max_depth:
            a,b,c=triangle
            ab,ac,bc=(a+b)/2,(a+c)/2,(b+c)/2
            stack.extend((np.array(child),depth+1) for child in [(a,ab,ac),(ab,b,bc),(ac,bc,c),(ab,bc,ac)])
        else:
            result+=integrate(point,panel,k,points,weights,triangle)
            leaves+=1
            deepest=max(deepest,depth)
            depth_hits+=int(near)
    return result,dict(leaves=leaves,max_depth=deepest,depth_hits=depth_hits)
