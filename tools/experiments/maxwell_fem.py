"""Small MFEM ND1/Whitney checks and tetra mesh for a Maxwell coupling probe.

ND1 is an explicit small validation discretization, not the antenna medium ND2.
All matrices and quadrature data remain in RAM. No solver storage on disk.
"""
import ctypes as ct
from itertools import combinations
import numpy as np
import maxwell_reference as reference

EDGES = list(combinations(range(4),2))


class MFEM:
    def __init__(self):
        self.lib = ct.CDLL('/native/libmfem_bridge.so')
        for name in ['mfem_bridge_version','mfem_bridge_git']:
            function = getattr(self.lib,name)
            function.argtypes,function.restype = [],ct.c_char_p
        for name in ['mfem_nd1_reference','mfem_nd1_elements']:
            function = getattr(self.lib,name)
            function.argtypes = [ct.c_int,ct.c_void_p,ct.c_void_p,ct.c_void_p]
            function.restype = ct.c_int
        self.version,self.git = self.lib.mfem_bridge_version().decode(),self.lib.mfem_bridge_git().decode()

    def reference(self,points):
        points = np.ascontiguousarray(points,dtype=np.float64)
        if points.ndim!=2 or points.shape[1]!=3 or not len(points) or not np.isfinite(points).all():
            raise ValueError('Expected finite reference points Nx3')
        values,curls = (np.empty((len(points),6,3)) for _ in range(2))
        code = self.lib.mfem_nd1_reference(len(points),points.ctypes.data,values.ctypes.data,curls.ctypes.data)
        if code: raise ValueError(f'MFEM basis failed: {code}')
        return values,curls

    def elements(self,vertices):
        vertices = np.ascontiguousarray(vertices,dtype=np.float64)
        if vertices.ndim!=3 or vertices.shape[1:]!=(4,3) or not np.isfinite(vertices).all():
            raise ValueError('Expected finite tetra vertices Nx4x3')
        jacobians = np.transpose(vertices[:,1:]-vertices[:,:1],(0,2,1))
        if not len(vertices) or np.min(np.linalg.det(jacobians))<=0:
            raise ValueError('MFEM probe requires positive tetrahedra')
        mass,curl = (np.empty((len(vertices),6,6)) for _ in range(2))
        code = self.lib.mfem_nd1_elements(len(vertices),vertices.ctypes.data,mass.ctypes.data,curl.ctypes.data)
        if code: raise ValueError(f'MFEM elements failed: {code}')
        return mass,curl


def gradients(vertices):
    inverse = np.linalg.inv(np.column_stack([np.ones(4),vertices]))
    return inverse[1:,:].T


def basis(lambdas,grad):
    return np.stack([lambdas[:,a,None]*grad[b]-lambdas[:,b,None]*grad[a] for a,b in EDGES],axis=1)


def analytic_matrices(vertices):
    volume = np.linalg.det((vertices[1:]-vertices[0]).T)/6
    if volume<=0: raise ValueError('Positive tetrahedron required')
    grad = gradients(vertices)
    coefficients = np.zeros((6,4,3))
    for e,(a,b) in enumerate(EDGES): coefficients[e,a],coefficients[e,b] = grad[b],-grad[a]
    moment = (np.ones((4,4))+np.eye(4))*volume/20
    mass = np.einsum('eic,ij,fjc->ef',coefficients,moment,coefficients)
    curls = np.asarray([2*np.cross(grad[a],grad[b]) for a,b in EDGES])
    return mass,volume*(curls@curls.T)


def boundary_faces(vertices,tetrahedra):
    entries = {}
    for tet in tetrahedra:
        for local in combinations(range(4),3):
            face = tuple(int(tet[i]) for i in local)
            opposite = next(int(tet[i]) for i in range(4) if i not in local)
            a,b,c = vertices[list(face)]
            if np.dot(np.cross(b-a,c-a),vertices[opposite]-a)>0: face = (face[0],face[2],face[1])
            entries.setdefault(tuple(sorted(face)),[]).append(face)
    if any(len(v)>2 for v in entries.values()): raise ValueError('Nonmanifold tetra mesh')
    return np.asarray([v[0] for v in entries.values() if len(v)==1],dtype=np.int64)


def mesh(refinement):
    if refinement not in [0,1,2]: raise ValueError('Use tetra refinement0..2')
    vertices,faces = reference.icosphere(0,volume_preserving=True)
    vertices = list(vertices)+[(0.,0.,0.)]
    center = len(vertices)-1
    tetrahedra = [(center,*face) for face in faces]
    for _ in range(refinement):
        mids,new_tets = {},[]
        def midpoint(a,b):
            key = tuple(sorted((a,b)))
            if key not in mids:
                mids[key] = len(vertices)
                vertices.append(tuple((x+y)/2 for x,y in zip(vertices[a],vertices[b])))
            return mids[key]
        for a,b,c,d in tetrahedra:
            ab,ac,ad,bc,bd,cd = [midpoint(tet_a,tet_b) for tet_a,tet_b in [(a,b),(a,c),(a,d),(b,c),(b,d),(c,d)]]
            new_tets.extend([(a,ab,ac,ad),(ab,b,bc,bd),(ac,bc,c,cd),(ad,bd,cd,d),
                             (ab,cd,ac,ad),(ab,cd,ad,bd),(ab,cd,bd,bc),(ab,cd,bc,ac)])
        tetrahedra = new_tets
    vertices,tetrahedra = np.asarray(vertices),np.asarray(tetrahedra)
    for tet in tetrahedra:
        if np.linalg.det((vertices[tet[1:]]-vertices[tet[0]]).T)<0:
            tet[1],tet[2] = tet[2],tet[1]
    return vertices,tetrahedra,boundary_faces(vertices,tetrahedra)


def assemble(vertices,tetrahedra,mfem):
    from scipy.sparse import coo_matrix
    ref_vertices = np.vstack([np.zeros(3),np.eye(3)])
    midpoints = np.asarray([(ref_vertices[a]+ref_vertices[b])/2 for a,b in EDGES])
    values,_ = mfem.reference(midpoints)
    tangents = np.asarray([ref_vertices[b]-ref_vertices[a] for a,b in EDGES])
    transform = np.einsum('eic,ec->ei',values,tangents)
    basis_map_error = float(np.max(abs(transform@transform.T-np.eye(6))))
    if basis_map_error>1e-12: raise ValueError('MFEM ND1 edge circulation map is not a signed permutation')
    check_points = np.asarray([[0.1,0.2,0.3],[0.25,0.25,0.25],[0.4,0.1,0.1]])
    checked_values,checked_curls = mfem.reference(check_points)
    grad = gradients(ref_vertices)
    expected = basis(np.column_stack([1-check_points.sum(axis=1),check_points]),grad)
    expected_curls = np.asarray([2*np.cross(grad[a],grad[b]) for a,b in EDGES])
    pointwise_error = float(max(np.max(abs(checked_values-np.einsum('me,pec->pmc',transform.T,expected))),
                                np.max(abs(checked_curls-(transform.T@expected_curls)[None,:,:]))))
    if pointwise_error>1e-12: raise ValueError('MFEM pointwise basis/curl differs from Whitney representation')
    native_mass,native_curl = mfem.elements(vertices[tetrahedra])
    local_mass = np.einsum('ij,ejk,lk->eil',transform,native_mass,transform)
    local_curl = np.einsum('ij,ejk,lk->eil',transform,native_curl,transform)
    errors = []
    for tet,m,k in zip(tetrahedra,local_mass,local_curl):
        exact_m,exact_k = analytic_matrices(vertices[tet])
        errors.extend([np.linalg.norm(m-exact_m)/np.linalg.norm(exact_m),np.linalg.norm(k-exact_k)/np.linalg.norm(exact_k)])
    if max(errors)>1e-12: raise ValueError('MFEM local matrices disagree with independent Whitney integrals')
    edge_map,edges,dofs,signs = {},[],[],[]
    for tet in tetrahedra:
        local_dofs,local_signs = [],[]
        for a,b in EDGES:
            key = tuple(sorted((int(tet[a]),int(tet[b]))))
            if key not in edge_map:
                edge_map[key] = len(edges)
                edges.append(key)
            local_dofs.append(edge_map[key])
            local_signs.append(1 if tet[a]<tet[b] else -1)
        dofs.append(local_dofs)
        signs.append(local_signs)
    dofs,signs,edges = np.asarray(dofs),np.asarray(signs),np.asarray(edges)
    rows = np.broadcast_to(dofs[:,:,None],local_mass.shape).ravel()
    cols = np.broadcast_to(dofs[:,None,:],local_mass.shape).ravel()
    orientation = signs[:,:,None]*signs[:,None,:]
    mass,curl = [coo_matrix(((a*orientation).ravel(),(rows,cols)),shape=(len(edges),len(edges))).tocsr()
                 for a in [local_mass,local_curl]]
    metadata = dict(mfem_version=mfem.version,mfem_git=mfem.git,
                    reference_edge_circulation_error=basis_map_error,
                    pointwise_basis_curl_error=pointwise_error,
                    max_relative_mfem_whitney_matrix_error=float(max(errors)))
    return mass,curl,edges,dofs,signs,edge_map,metadata


def plane_coefficients(vertices,edges,k):
    a,b = vertices[edges[:,0]],vertices[edges[:,1]]
    phase = np.exp(1j*k*(a[:,2]+b[:,2])/2)*np.sinc(k*(b[:,2]-a[:,2])/(2*np.pi))
    return (b[:,0]-a[:,0])*phase,(b[:,1]-a[:,1])*phase


def tetra_quadrature(order=4):
    nodes,weights = np.polynomial.legendre.leggauss(order)
    nodes,weights = (nodes+1)/2,weights/2
    bary,quad = [],[]
    for u,wu in zip(nodes,weights):
        for v,wv in zip(nodes,weights):
            for w,ww in zip(nodes,weights):
                bary.append([1-u,u*(1-v),u*v*(1-w),u*v*w])
                quad.append(wu*wv*ww*u*u*v)
    return np.asarray(bary),np.asarray(quad)


def plane_field_errors(vertices,tetrahedra,dofs,signs,coefficients,k,order=4):
    lambdas,weights = tetra_quadrature(order)
    error_e=error_h=volume=0.0
    for tet,index,orientation in zip(tetrahedra,dofs,signs):
        points = vertices[tet]
        determinant = np.linalg.det((points[1:]-points[0]).T)
        grad = gradients(points)
        local = coefficients[index]*orientation
        values = np.einsum('e,pec->pc',local,basis(lambdas,grad))
        curls = np.asarray([2*np.cross(grad[a],grad[b]) for a,b in EDGES])
        h = local@curls/(1j*k)
        phase = np.exp(1j*k*(lambdas@points)[:,2])
        exact_e,exact_h = np.zeros_like(values),np.zeros_like(values)
        exact_e[:,0],exact_h[:,1] = phase,phase
        error_e += determinant*np.dot(weights,np.sum(abs(values-exact_e)**2,axis=1))
        error_h += determinant*np.dot(weights,np.sum(abs(h-exact_h)**2,axis=1))
        volume += determinant/6
    return dict(relative_E_L2=float(np.sqrt(error_e/volume)),relative_H_L2=float(np.sqrt(error_h/volume)),
                volume=volume,quadrature=order)
