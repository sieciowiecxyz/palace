"""Serial global MFEM ND2 adapter for bounded validation, working arrays in RAM.

MFEM owns mesh/FESpace/assembly/orientation; Python exports sparse CSR and
checks the physical basis. This is not a Palace replacement or GPU backend.
"""
import ctypes as ct
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import norm as sparse_norm
import maxwell_fem as fem


def validate_mesh(vertices,tetrahedra,faces):
    vertices = np.ascontiguousarray(vertices,dtype=np.float64)
    if vertices.ndim!=2 or vertices.shape[1]!=3 or len(vertices)<4 or not np.isfinite(vertices).all():
        raise ValueError('Expected finite vertex coordinates Nx3')
    indices = []
    for data,width in [(tetrahedra,4),(faces,3)]:
        data = np.asarray(data)
        if data.ndim!=2 or data.shape[1]!=width or not len(data) or not np.issubdtype(data.dtype,np.integer):
            raise ValueError('Expected integral tetrahedra Nx4 / boundary Nx3')
        if data.min()<0 or data.max()>=len(vertices): raise ValueError('Mesh vertex index outside range')
        if any(len(set(row))!=width for row in data): raise ValueError('Repeated vertex in element')
        indices.append(np.ascontiguousarray(data,dtype=np.int32))
    tetrahedra,faces = indices
    jac = np.transpose(vertices[tetrahedra[:,1:]]-vertices[tetrahedra[:,:1]],(0,2,1))
    if np.min(np.linalg.det(jac))<=0: raise ValueError('Tetrahedra must have positive Jacobians')
    expected = fem.boundary_faces(vertices,tetrahedra)
    canonical = lambda a: sorted(tuple(sorted(map(int,row))) for row in a)
    if canonical(expected)!=canonical(faces): raise ValueError('Boundary does not match tetrahedra')
    # Preserve outward orientations from the audited tetrahedral topology.
    return vertices,tetrahedra,np.ascontiguousarray(expected,dtype=np.int32)


class GlobalND:
    def __init__(self,vertices,tetrahedra,faces,order=2):
        if order not in [1,2]: raise ValueError('Validation bridge only supports ND1/ND2')
        self.vertices,self.tetrahedra,self.faces = validate_mesh(vertices,tetrahedra,faces)
        self.order = order
        self.handle = None
        self.lib = ct.CDLL('/native/libmfem_bridge.so')
        pointer,integer = ct.c_void_p,ct.c_int
        signatures = {
            'create':[integer,pointer,integer,pointer,integer,pointer,integer],
            'info':[pointer,pointer], 'matrix':[pointer,integer,pointer,pointer,pointer],
            'boundary':[pointer,pointer], 'basis':[pointer,integer,integer,pointer,pointer,pointer,pointer],
            'project':[pointer,integer,integer,ct.c_double,pointer],
            'evaluate':[pointer,integer,integer,pointer,pointer,pointer,pointer],
            'destroy':[pointer]}
        for name,args in signatures.items():
            function = getattr(self.lib,'mfem_global_'+name)
            function.argtypes = args
            function.restype = pointer if name=='create' else None if name=='destroy' else integer
        self.lib.mfem_bridge_version.restype = ct.c_char_p
        self.lib.mfem_bridge_git.restype = ct.c_char_p
        self.handle = self.lib.mfem_global_create(len(self.vertices),self.vertices.ctypes.data,
            len(self.tetrahedra),self.tetrahedra.ctypes.data,len(self.faces),self.faces.ctypes.data,order)
        if not self.handle: raise ValueError('MFEM global space creation failed')
        try:
            info = np.empty(6,dtype=np.int32)
            self.call('info',info.ctypes.data)
            self.ndofs,self.local_dofs,self.mass_nnz,self.curl_nnz,self.boundary_count,self.nonidentity = map(int,info)
            self.version,self.git = self.lib.mfem_bridge_version().decode(),self.lib.mfem_bridge_git().decode()
        except BaseException:
            self.close()
            raise

    def call(self,name,*args):
        if not self.handle: raise ValueError('MFEM space is closed')
        code = getattr(self.lib,'mfem_global_'+name)(self.handle,*args)
        if code: raise ValueError(f'MFEM global {name} failed: {code}')

    def close(self):
        if self.handle:
            self.lib.mfem_global_destroy(self.handle)
            self.handle = None

    def __enter__(self): return self
    def __exit__(self,*args): self.close()

    def matrix(self,which):
        if which not in [0,1]: raise ValueError('Choose mass0 or curl1')
        nnz = self.mass_nnz if which==0 else self.curl_nnz
        rows = np.empty(self.ndofs+1,dtype=np.int32)
        cols = np.empty(nnz,dtype=np.int32)
        values = np.empty(nnz,dtype=np.float64)
        self.call('matrix',which,rows.ctypes.data,cols.ctypes.data,values.ctypes.data)
        return csr_matrix((values,cols,rows),shape=(self.ndofs,self.ndofs))

    def boundary(self):
        indices = np.empty(self.boundary_count,dtype=np.int32)
        self.call('boundary',indices.ctypes.data)
        return indices

    def points(self,cell,points):
        points = np.ascontiguousarray(points,dtype=np.float64)
        if not 0<=cell<len(self.tetrahedra): raise ValueError('Cell outside mesh')
        if points.ndim!=2 or points.shape[1]!=3 or not len(points) or not np.isfinite(points).all():
            raise ValueError('Expected finite reference points Nx3')
        if points.min()<-1e-12 or np.max(points.sum(axis=1))>1+1e-12:
            raise ValueError('Reference points outside tetrahedron')
        return points

    def basis(self,cell,points):
        points = self.points(cell,points)
        indices = np.empty(self.local_dofs,dtype=np.int32)
        values,curls = (np.empty((len(points),self.local_dofs,3)) for _ in range(2))
        self.call('basis',cell,len(points),points.ctypes.data,indices.ctypes.data,values.ctypes.data,curls.ctypes.data)
        return indices,values,curls

    def project(self,kind,k=1.):
        if kind not in [0,1,2,3] or not np.isfinite(k): raise ValueError('Unknown or nonfinite projection')
        real,imag = (np.empty(self.ndofs) for _ in range(2))
        self.call('project',kind,0,k,real.ctypes.data)
        self.call('project',kind,1,k,imag.ctypes.data)
        return real+1j*imag

    def evaluate(self,cell,points,coefficients):
        points = self.points(cell,points)
        coefficients = np.asarray(coefficients)
        if coefficients.shape!=(self.ndofs,) or not np.isfinite(coefficients).all():
            raise ValueError('Expected finite global coefficients')
        result = [np.zeros((len(points),3),dtype=np.complex128) for _ in range(2)]
        for factor,part in [(1.,coefficients.real),(1j,coefficients.imag)]:
            part = np.ascontiguousarray(part,dtype=np.float64)
            values,curls = (np.empty((len(points),3)) for _ in range(2))
            self.call('evaluate',cell,len(points),points.ctypes.data,part.ctypes.data,values.ctypes.data,curls.ctypes.data)
            result[0] += factor*values
            result[1] += factor*curls
        return result


def audit_basis(space,mass,curl):
    lambdas,weights = fem.tetra_quadrature(4)
    points = lambdas[:,1:]
    rows,cols,masses,curls = [],[],[],[]
    constant,linear = space.project(0),space.project(1)
    matrix_error=constant_error=linear_error=direct_error=0.
    for cell,tet in enumerate(space.tetrahedra):
        vertices = space.vertices[tet]
        jacobian = np.linalg.det((vertices[1:]-vertices[0]).T)
        indices,values,rot = space.basis(cell,points)
        rows.append(np.repeat(indices,space.local_dofs))
        cols.append(np.tile(indices,space.local_dofs))
        masses.append((jacobian*np.einsum('p,pic,pjc->ij',weights,values,values)).ravel())
        curls.append((jacobian*np.einsum('p,pic,pjc->ij',weights,rot,rot)).ravel())
        x = lambdas@vertices
        for coefficients,exact_value,exact_curl in [
            (constant,np.broadcast_to([1.,0.,0.],x.shape),np.zeros_like(x)),
            (linear,x[:,[2,0,1]],np.ones_like(x))]:
            value = np.einsum('i,pic->pc',coefficients[indices],values)
            rotation = np.einsum('i,pic->pc',coefficients[indices],rot)
            error = max(np.max(abs(value-exact_value)),np.max(abs(rotation-exact_curl)))
            if coefficients is constant: constant_error=max(constant_error,float(error))
            else: linear_error=max(linear_error,float(error))
            native_value,native_curl = space.evaluate(cell,points[:3],coefficients)
            direct_error = max(direct_error,float(np.max(abs(native_value-value[:3]))),float(np.max(abs(native_curl-rotation[:3]))))
    rows,cols = np.concatenate(rows),np.concatenate(cols)
    for source,target in [(masses,mass),(curls,curl)]:
        reconstructed = coo_matrix((np.concatenate(source),(rows,cols)),shape=mass.shape).tocsr()
        matrix_error = max(matrix_error,float(sparse_norm(reconstructed-target)/sparse_norm(target)))
    return dict(physical_quadrature_matrix_relative=matrix_error,exact_constant_max=constant_error,
        exact_linear_max=linear_error,global_basis_vs_gridfunction_max=direct_error,
        nonidentity_face_transform_cells=space.nonidentity)


def plane_field_errors(space,coefficients,k=1.,order=4):
    lambdas,weights = fem.tetra_quadrature(order)
    error_e=error_h=volume=0.
    for cell,tet in enumerate(space.tetrahedra):
        vertices = space.vertices[tet]
        jacobian = np.linalg.det((vertices[1:]-vertices[0]).T)
        indices,values,curls = space.basis(cell,lambdas[:,1:])
        electric = np.einsum('i,pic->pc',coefficients[indices],values)
        magnetic = np.einsum('i,pic->pc',coefficients[indices],curls)/(1j*k)
        phase = np.exp(1j*k*(lambdas@vertices)[:,2])
        exact_e,exact_h = np.zeros_like(electric),np.zeros_like(magnetic)
        exact_e[:,0],exact_h[:,1] = phase,phase
        error_e += jacobian*np.dot(weights,np.sum(abs(electric-exact_e)**2,axis=1))
        error_h += jacobian*np.dot(weights,np.sum(abs(magnetic-exact_h)**2,axis=1))
        volume += jacobian/6
    return dict(relative_E_L2=float(np.sqrt(error_e/volume)),relative_H_L2=float(np.sqrt(error_h/volume)),
                volume=volume,quadrature=order)
