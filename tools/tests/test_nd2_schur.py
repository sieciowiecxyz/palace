import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

AVAILABLE=all(importlib.util.find_spec(name) is not None for name in ['numpy','scipy'])
if AVAILABLE:
    import numpy as np
    from scipy.sparse import csr_matrix
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
    api=types.ModuleType('bempp_cl.api')
    package=types.ModuleType('bempp_cl')
    package.api=api
    spec=importlib.util.spec_from_file_location('bempp_nd2_coupling',
        Path(__file__).resolve().parents[1]/'experiments/bempp_nd2_coupling.py')
    coupling=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,{'bempp_cl':package,'bempp_cl.api':api}):
        spec.loader.exec_module(coupling)


@unittest.skipUnless(AVAILABLE,'Optional NumPy/SciPy; pinned oracle includes both')
class ND2SchurTests(unittest.TestCase):
    def problem(self):
        rng=np.random.default_rng(41)
        random=lambda shape:rng.standard_normal(shape)+1j*rng.standard_normal(shape)
        x=random((8,8))
        a=csr_matrix(x.conj().T@x+3*np.eye(8))
        b=csr_matrix(random((8,3)))
        d=-b.T
        gram=random((3,3))+8*np.eye(3)
        c=random((3,3))
        t=random((3,3))+7*np.eye(3)
        rhs=random((3,))
        return a,b,d,gram,c,t,rhs

    def test_complex_sparse_schur_matches_independent_full_block(self):
        a,b,d,g,c,t,rhs=self.problem()
        u,h,trace,metrics=coupling.schur_solve(a,b,d,g,c,t,rhs,k=.7,block=2)
        r=np.linalg.solve(g,d.toarray())
        full=np.block([[a.toarray(),-.7j*b.toarray()],[c@r,t]])
        exact=np.linalg.solve(full,np.r_[np.zeros(8),rhs])
        np.testing.assert_allclose(np.r_[u,h],exact,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(trace,r@u,rtol=1e-12,atol=1e-12)
        self.assertLess(metrics['raw_block_rhs_relative'],1e-12)
        self.assertLess(metrics['dense_crosscheck_relative'],1e-12)

    def test_rhs_chunking_preserves_solution_and_input_operator(self):
        args=self.problem()
        before=args[5].copy()
        first=coupling.schur_solve(*args,block=1)
        second=coupling.schur_solve(*args,block=3)
        for left,right in zip(first[:3],second[:3]):
            np.testing.assert_allclose(left,right,rtol=1e-12,atol=1e-12)
        np.testing.assert_array_equal(args[5],before)
        self.assertEqual(first[-1]['max_fem_rhs_block_bytes'],8*16)
        self.assertEqual(second[-1]['max_fem_rhs_block_bytes'],8*3*16)
