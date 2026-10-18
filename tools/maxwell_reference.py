"""Independent PEC Mie reference and outward icosphere, stdlib only.

Convention exp(-iwt), outgoing exp(+ikr)/r; incident E=xhat exp(+ikz).
Restricted to 0<ka<=3 (dielectric |mka|<=6), for a well-conditioned direct j_n series.
"""
import cmath
from itertools import combinations
import math


def _regular_bessel(x,terms):
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
    return j


def coefficients(x, terms=16):
    if not 0 < x <= 3 or not 2 <= terms <= 24:
        raise ValueError('Reference restricted to 0<ka<=3 and 2..24 terms')
    j = _regular_bessel(x,terms)
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


def dielectric_coefficients(x,epsilon_r,terms=16):
    """Nonmagnetic passive sphere, same exp(-iwt)/outgoing h1 convention."""
    epsilon_r = complex(epsilon_r)
    m = cmath.sqrt(epsilon_r)
    if not 0<x<=3 or not 2<=terms<=24 or epsilon_r.real<=0 or epsilon_r.imag<0 or abs(m*x)>6:
        raise ValueError('Use passive positive-epsilon sphere: ka<=3, |mka|<=6')
    j,inside = _regular_bessel(x,terms),_regular_bessel(m*x,terms)
    y = [-math.cos(x)/x,-math.cos(x)/(x*x)-math.sin(x)/x]
    for n in range(1,terms+1): y.append((2*n+1)*y[n]/x-y[n-1])
    a,b = [],[]
    for n in range(1,terms+1):
        psi,xi,p = x*j[n],x*complex(j[n],y[n]),m*x*inside[n]
        dpsi = (n+1)*j[n]-x*j[n+1]
        dxi = (n+1)*complex(j[n],y[n])-x*complex(j[n+1],y[n+1])
        dp = (n+1)*inside[n]-m*x*inside[n+1]
        a.append((m*p*dpsi-psi*dp)/(m*p*dxi-xi*dp))
        b.append((p*dpsi-m*psi*dp)/(p*dxi-m*xi*dp))
    return a,b


def far_field(directions, k=1.0, radius=1.0,epsilon_r=None):
    """Vector F in Escattered=exp(ikr)*F/r+O(r^-2), with fixed phase."""
    a,b = coefficients(k*radius) if epsilon_r is None else dielectric_coefficients(k*radius,epsilon_r)
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


def cross_sections(k=1.0,radius=1.0,epsilon_r=None):
    a,b = coefficients(k*radius) if epsilon_r is None else dielectric_coefficients(k*radius,epsilon_r)
    scatter = 2*math.pi/(k*k)*sum((2*n+1)*(abs(x)**2+abs(y)**2) for n,(x,y) in enumerate(zip(a,b),1))
    extinction = 2*math.pi/(k*k)*sum((2*n+1)*(x+y).real for n,(x,y) in enumerate(zip(a,b),1))
    return scatter,extinction


def signed_volume(vertices,faces):
    volume = 0.0
    for ia,ib,ic in faces:
        a,b,c = (vertices[i] for i in [ia,ib,ic])
        cross = (b[1]*c[2]-b[2]*c[1],b[2]*c[0]-b[0]*c[2],b[0]*c[1]-b[1]*c[0])
        volume += sum(x*y for x,y in zip(a,cross))/6
    return volume


def icosphere(level,volume_preserving=False):
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
    if volume_preserving:
        # Geometry-only conservation rule; no material/frequency/field fit.
        scale = ((4*math.pi/3)/signed_volume(vertices,faces))**(1/3)
        vertices = [tuple(scale*x for x in v) for v in vertices]
    return vertices,faces
