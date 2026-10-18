import importlib.util
from pathlib import Path
import unittest


HAS_NUMPY = importlib.util.find_spec('numpy') is not None
if HAS_NUMPY:
    import numpy as np
    spec = importlib.util.spec_from_file_location('maxwell_hmatrix',
        Path(__file__).resolve().parents[1]/'experiments/maxwell_hmatrix.py')
    hmatrix = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hmatrix)


@unittest.skipUnless(HAS_NUMPY,'Optional NumPy; pinned oracle environment runs the integration probe')
class HMatrixTests(unittest.TestCase):
    def test_complex_partition_and_low_rank_far_blocks(self):
        rng = np.random.default_rng(73)
        points = rng.random((32,3))
        points[16:,0] += 100
        boxes = np.stack([points-0.01,points+0.01],axis=1)
        a = rng.random((32,32))+1j*rng.random((32,32))
        left,right = rng.random(32)+1j*rng.random(32),rng.random(32)+1j*rng.random(32)
        a[:16,16:] = np.outer(left[:16],right[16:])
        a[16:,:16] = np.outer(left[16:],right[:16])
        h = hmatrix.HMatrix(a,boxes,leaf=4,tolerance=1e-10)
        x = rng.random(32)+1j*rng.random(32)
        np.testing.assert_allclose(h.apply_ordered(x[h.order]),(a@x)[h.order],rtol=1e-12,atol=1e-12)
        self.assertLess(h.storage_bytes,a.nbytes)
        self.assertTrue(any(b is not None for _,_,_,b in h.blocks))
        coverage = np.zeros((32,32),dtype=int)
        for i,j,u,v in h.blocks:
            n = u.shape[1] if v is None else v.shape[1]
            coverage[i:i+u.shape[0],j:j+n] += 1
        np.testing.assert_array_equal(coverage,np.ones_like(coverage))

    def test_overlapping_supports_stay_exact(self):
        boxes = np.tile([[-1.,-1.,-1.],[1.,1.,1.]],(8,1,1))
        a = np.arange(64).reshape(8,8).astype(complex)
        h = hmatrix.HMatrix(a,boxes,leaf=2)
        self.assertEqual(h.admissible_count,0)
        self.assertEqual(h.storage_bytes,a.nbytes)
        np.testing.assert_allclose(h.apply_ordered(np.ones(8)),a@np.ones(8))
