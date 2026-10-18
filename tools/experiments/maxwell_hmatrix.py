"""Small complex H-matrix/CUDA apply probe, not a scalable assembly or FEM coupling.

Dense Maxwell entries are supplied by the independent CPU oracle in RAM. Near
blocks are exact; only geometrically separated RWG supports may be compressed.
"""
import ctypes as ct
import time
import numpy as np


def support_boxes(grid, space):
    boxes = []
    for support in space.global2local:
        elements = [element for element, local in support]
        vertices = grid.vertices[:, grid.elements[:, elements].ravel()]
        boxes.append((vertices.min(axis=1), vertices.max(axis=1)))
    return np.asarray(boxes)


class HMatrix:
    def __init__(self, matrix, boxes, leaf=64, eta=2.0, tolerance=1e-6):
        if matrix.shape!=(len(boxes),len(boxes)) or leaf<2 or not 0<tolerance<1 or eta<=0:
            raise ValueError('Invalid H-matrix probe parameters')
        self.blocks = []
        self.order = []
        def cluster(indices):
            low, high = boxes[indices,0].min(axis=0), boxes[indices,1].max(axis=0)
            begin = len(self.order)
            children = []
            if len(indices)>leaf:
                axis = int(np.argmax(high-low))
                centers = boxes[indices,:,axis].mean(axis=1)
                indices = indices[np.argsort(centers,kind='stable')]
                mid = len(indices)//2
                children = [cluster(indices[:mid]),cluster(indices[mid:])]
            else:
                self.order.extend(indices.tolist())
            return dict(begin=begin,end=len(self.order),low=low,high=high,children=children)
        root = cluster(np.arange(len(boxes)))
        self.order = np.asarray(self.order)
        ordered = matrix[np.ix_(self.order,self.order)]
        self.dense_bytes = matrix.nbytes
        self.admissible_count = 0
        self.max_block_error = 0.0
        def partition(row,col):
            gap = np.maximum(0,np.maximum(row['low']-col['high'],col['low']-row['high']))
            distance = np.linalg.norm(gap)
            diameter = max(np.linalg.norm(row['high']-row['low']),np.linalg.norm(col['high']-col['low']))
            separated = distance>0 and diameter<=eta*distance
            i,j,m,n = row['begin'],col['begin'],row['end']-row['begin'],col['end']-col['begin']
            if separated:
                self.admissible_count += 1
                block = ordered[i:i+m,j:j+n]
                u,s,vh = np.linalg.svd(block,full_matrices=False)
                # Absolute Frobenius tail bound <= tolerance * block norm.
                tail = np.r_[np.cumsum((s*s)[::-1])[::-1],0.0]
                rank = int(np.flatnonzero(tail<=tolerance*tolerance*tail[0])[0]) if tail[0] else 0
                rank = max(1,rank)
                if rank*(m+n)<m*n:
                    left = np.asfortranarray(u[:,:rank]*s[:rank])
                    right = np.asfortranarray(vh[:rank,:])
                    error = np.linalg.norm(block-left@right)/max(np.linalg.norm(block),1e-300)
                    self.max_block_error = max(self.max_block_error,float(error))
                    if error>tolerance*1.0001:
                        raise ValueError('SVD compression error exceeds frozen local bound')
                    self.blocks.append((i,j,left,right))
                    return
            if not row['children'] and not col['children']:
                self.blocks.append((i,j,np.asfortranarray(ordered[i:i+m,j:j+n]),None))
            elif row['children'] and (not col['children'] or m>=n):
                for child in row['children']: partition(child,col)
            else:
                for child in col['children']: partition(row,child)
        partition(root,root)
        self.storage_bytes = sum(a.nbytes+(0 if b is None else b.nbytes) for _,_,a,b in self.blocks)

    def apply_ordered(self,x):
        y = np.zeros(x.shape,dtype=np.complex128)
        for i,j,a,b in self.blocks:
            n = a.shape[1] if b is None else b.shape[1]
            value = x[j:j+n]
            y[i:i+a.shape[0]] += a@value if b is None else a@(b@value)
        return y


class CUDAApply:
    """Explicit small VRAM allocations and complex FP64 cuBLAS; no UVM/disk."""
    def __init__(self,blocks,n):
        self.runtime = ct.CDLL('libcudart.so.12')
        self.blas = ct.CDLL('libcublas.so.12')
        self.allocations = []
        self.bytes = 0
        self.handle = ct.c_void_p()
        self._signature(self.runtime,'cudaMalloc',[ct.POINTER(ct.c_void_p),ct.c_size_t])
        self._signature(self.runtime,'cudaFree',[ct.c_void_p])
        self._signature(self.runtime,'cudaMemcpy',[ct.c_void_p,ct.c_void_p,ct.c_size_t,ct.c_int])
        self._signature(self.runtime,'cudaMemset',[ct.c_void_p,ct.c_int,ct.c_size_t])
        self._signature(self.runtime,'cudaDeviceSynchronize',[])
        self._signature(self.blas,'cublasCreate_v2',[ct.POINTER(ct.c_void_p)])
        self._signature(self.blas,'cublasDestroy_v2',[ct.c_void_p])
        self._signature(self.blas,'cublasZgemv_v2',[ct.c_void_p,ct.c_int,ct.c_int,ct.c_int,
                        ct.c_void_p,ct.c_void_p,ct.c_int,ct.c_void_p,ct.c_int,
                        ct.c_void_p,ct.c_void_p,ct.c_int])
        try:
            self._check(self.blas.cublasCreate_v2(ct.byref(self.handle)))
            self.blocks = [(i,j,self.upload(a),a.shape,None if b is None else self.upload(b),
                            None if b is None else b.shape) for i,j,a,b in blocks]
            self.x,self.y = self.allocate(16*n),self.allocate(16*n)
            self.temporary = self.allocate(16*max([a.shape[1] for _,_,a,b in blocks if b is not None]+[1]))
            self.n = n
            self.one,self.zero = np.array([1+0j],dtype=np.complex128),np.array([0j],dtype=np.complex128)
        except BaseException:
            self.close()
            raise

    @staticmethod
    def _signature(library,name,args):
        function = getattr(library,name)
        function.argtypes,function.restype = args,ct.c_int

    @staticmethod
    def _check(code):
        if code: raise RuntimeError(f'CUDA/cuBLAS error {code}')

    def allocate(self,size):
        pointer = ct.c_void_p()
        self._check(self.runtime.cudaMalloc(ct.byref(pointer),size))
        self.allocations.append(pointer)
        self.bytes += size
        return pointer

    def upload(self,array):
        if not array.flags.f_contiguous or array.dtype!=np.complex128:
            raise ValueError('cuBLAS requires column-major complex128')
        pointer = self.allocate(array.nbytes)
        self._check(self.runtime.cudaMemcpy(pointer,array.ctypes.data,array.nbytes,1))
        return pointer

    def gemv(self,a,shape,x,y,add):
        self._check(self.blas.cublasZgemv_v2(self.handle,0,*shape,self.one.ctypes.data,a,shape[0],x,1,
                                          (self.one if add else self.zero).ctypes.data,y,1))

    def apply(self,x):
        x = np.ascontiguousarray(x,dtype=np.complex128)
        if x.shape!=(self.n,): raise ValueError('Unexpected vector shape')
        self._check(self.runtime.cudaMemcpy(self.x,x.ctypes.data,x.nbytes,1))
        self._check(self.runtime.cudaMemset(self.y,0,x.nbytes))
        for i,j,a,shape,b,bshape in self.blocks:
            value = ct.c_void_p(self.x.value+16*j)
            if b is not None:
                self.gemv(b,bshape,value,self.temporary,False)
                value = self.temporary
            self.gemv(a,shape,value,ct.c_void_p(self.y.value+16*i),True)
        y = np.empty_like(x)
        self._check(self.runtime.cudaMemcpy(y.ctypes.data,self.y,y.nbytes,2))
        return y

    def close(self):
        if self.handle.value:
            self.blas.cublasDestroy_v2(self.handle)
            self.handle = ct.c_void_p()
        for pointer in reversed(self.allocations): self.runtime.cudaFree(pointer)
        self.allocations.clear()


def probe(matrix,boxes,rhs,solution):
    from scipy.sparse.linalg import LinearOperator,gmres
    started = time.monotonic()
    h = HMatrix(matrix,boxes)
    compression_seconds = time.monotonic()-started
    ordered = matrix[np.ix_(h.order,h.order)]
    rng = np.random.default_rng(7019)
    vectors = [solution[h.order]]+[rng.standard_normal(len(rhs))+1j*rng.standard_normal(len(rhs)) for _ in range(3)]
    errors = [float(np.linalg.norm(h.apply_ordered(x)-ordered@x)/np.linalg.norm(ordered@x)) for x in vectors]
    began = time.monotonic()
    callbacks = []
    candidate,info = gmres(LinearOperator(matrix.shape,matvec=h.apply_ordered,dtype=np.complex128),
                           rhs[h.order],rtol=1e-10,atol=0,restart=100,maxiter=10,
                           callback=callbacks.append,callback_type='pr_norm')
    solve_seconds = time.monotonic()-began
    raw = float(np.linalg.norm(ordered@candidate-rhs[h.order])/np.linalg.norm(rhs))
    delta = float(np.linalg.norm(candidate-solution[h.order])/np.linalg.norm(solution))
    gpu = dict(backend='complex128 cuBLAS Zgemv; no Tensor Cores',scope='apply only, not GPU solve')
    # Same GPU, data stay resident between calls; round-trip timings include PCIe,
    # Python dispatch, cuBLAS launches and sync, not just kernel event time.
    for label,blocks in [('dense',[(0,0,np.asfortranarray(ordered),None)]),('compressed',h.blocks)]:
        device = CUDAApply(blocks,len(rhs))
        try:
            reference = [ordered@x for x in vectors]
            measured = [device.apply(x) for x in vectors]
            error = max(float(np.linalg.norm(a-b)/np.linalg.norm(b)) for a,b in zip(measured,reference))
            begin = time.monotonic()
            for _ in range(8): device.apply(vectors[0])
            gpu[label] = dict(explicit_device_allocation_bytes=device.bytes,
                              average_round_trip_apply_seconds=(time.monotonic()-begin)/8,
                              max_relative_action_error=error)
        finally:
            device.close()
    report = dict(scope='RAM-assembled PEC Maxwell H-matrix probe; no scalable assembly or FEM interface',
                  local_relative_frobenius_tolerance=1e-6,leaf=64,eta=2.0,
                  blocks=len(h.blocks),compressed_blocks=sum(b is not None for _,_,a,b in h.blocks),
                  admissible_blocks=h.admissible_count,max_local_compression_error=h.max_block_error,
                  dense_matrix_bytes=h.dense_bytes,compressed_matrix_bytes=h.storage_bytes,
                  compression_seconds=compression_seconds,max_relative_action_error=max(errors),
                  gmres_info=info,gmres_iterations=len(callbacks),cpu_compressed_solve_seconds=solve_seconds,
                  raw_original_rhs_relative=raw,relative_solution_difference=delta,cuda=gpu,
                  frozen_targets=dict(action=1e-5,raw_original=1e-6,solution_difference=1e-3),
                  quality_passed=bool(info==0 and max(errors)<1e-5 and raw<1e-6 and delta<1e-3 and
                                      gpu['dense']['max_relative_action_error']<1e-12 and
                                      gpu['compressed']['max_relative_action_error']<1e-5),
                  limitations=['Dense assembly and oracle retained in RAM; peak RAM not reduced',
                               'Small CUDA apply timing does not predict antenna or full solve speed',
                               'Operator allocation excludes CUDA context/cuBLAS internal workspace'])
    restored = np.empty_like(candidate)
    restored[h.order] = candidate
    return report,restored
