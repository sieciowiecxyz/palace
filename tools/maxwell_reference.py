"""Independent PEC Mie reference and outward icosphere, stdlib only.

Convention exp(-iwt), outgoing exp(+ikr)/r; incident E=xhat exp(+ikz).
Restricted to 0<ka<=3, where the direct j_n series is well conditioned.
"""
import cmath
from itertools import combinations
import math


def coefficients(x, terms=16):
    if not 0 < x <= 3 or not 2 <= terms <= 24:
        raise ValueError('Reference restricted to 0<ka<=3 and 2..24 terms')
    j = []
    for n in range(terms+2):
        denominator = math.prod(range(1,2*n+2,2))
        term = total = x**n/denominator
        for m in range(1,100):
            term *= -x*x/(2*m*(2*n+2*m+1))
            total += term
            if abs(term) < 1e-17*max(abs(total),1e-300): break
        else: raise ValueError('Bessel series failed to converge')
        j.append(total)
    y = [-math.cos(x)/x,-math.cos(x)/(x*x)-math.sin(x)/x]
    for n in range(1,terms+1): y.append((2*n+1)*y[n]/x-y[n-1])
    a,b = [],[]
    for n in range(1,terms+1):
        psi,xi = x*j[n],x*complex(j[n],y[n])
        dpsi = (n+1)*j[n]-x*j[n+1]
        dxi = (n+1)*complex(j[n],y[n])-x*complex(j[n+1],y[n+1])
        a.append(dpsi/dxi)
        b.append(psi/xi)
    return a,b


def far_field(directions, k=1.0, radius=1.0):
    """Vector F in Escattered=exp(ikr)*F/r+O(r^-2), with fixed phase."""
    a,b = coefficients(k*radius)
    result = []
    for dx,dy,mu in directions:
        if abs(dx*dx+dy*dy+mu*mu-1)>1e-10: raise ValueError('Directions must be unit vectors')
        sin_theta = math.sqrt(max(0,1-mu*mu))
        phi = math.atan2(dy,dx)
        cp,sp = math.cos(phi),math.sin(phi)
        e_theta,e_phi = (mu*cp,mu*sp,-sin_theta),(-sp,cp,0)
        previous,current = 0.0,1.0
        s1=s2=0j
        for n,(an,bn) in enumerate(zip(a,b),1):
            tau = n*mu*current-(n+1)*previous
            factor = (2*n+1)/(n*(n+1))
            s1 += factor*(an*current+bn*tau)
            s2 += factor*(an*tau+bn*current)
            previous,current = current,((2*n+1)*mu*current-(n+1)*previous)/n
        result.append(tuple(1j/k*(s2*cp*t-s1*sp*p) for t,p in zip(e_theta,e_phi)))
    return result


def cross_sections(k=1.0,radius=1.0):
    a,b = coefficients(k*radius)
    scatter = 2*math.pi/(k*k)*sum((2*n+1)*(abs(x)**2+abs(y)**2) for n,(x,y) in enumerate(zip(a,b),1))
    extinction = 2*math.pi/(k*k)*sum((2*n+1)*(x+y).real for n,(x,y) in enumerate(zip(a,b),1))
    return scatter,extinction


def icosphere(level):
    if not isinstance(level,int) or isinstance(level,bool) or not 0<=level<=3:
        raise ValueError('Use refinement level0..3')
    phi = (1+math.sqrt(5))/2
    def unit(v):
        norm = math.sqrt(sum(x*x for x in v))
        return tuple(x/norm for x in v)
    vertices = [unit(v) for a in [-1,1] for b in [-phi,phi]
                for v in [(0,a,b),(a,b,0),(b,0,a)]]
    distances = {(a,b):sum((x-y)**2 for x,y in zip(vertices[a],vertices[b])) for a,b in combinations(range(12),2)}
    edge_length = min(distances.values())
    faces = [t for t in combinations(range(12),3) if all(abs(distances[p]-edge_length)<1e-10 for p in combinations(t,2))]
    def orient(t):
        a,b,c = (vertices[i] for i in t)
        u,v = [b[i]-a[i] for i in range(3)],[c[i]-a[i] for i in range(3)]
        normal = (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        return t if sum(x*y for x,y in zip(normal,a))>0 else (t[0],t[2],t[1])
    faces = [orient(t) for t in faces]
    for _ in range(level):
        midpoints,new_faces = {},[]
        def midpoint(a,b):
            key = tuple(sorted((a,b)))
            if key not in midpoints:
                midpoints[key] = len(vertices)
                vertices.append(unit(tuple(x+y for x,y in zip(vertices[a],vertices[b]))))
            return midpoints[key]
        for a,b,c in faces:
            ab,bc,ca = midpoint(a,b),midpoint(b,c),midpoint(c,a)
            new_faces.extend([(a,ab,ca),(b,bc,ab),(c,ca,bc),(ab,bc,ca)])
        faces = new_faces
    return vertices,faces
