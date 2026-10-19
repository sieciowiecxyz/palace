import importlib.util
from pathlib import Path
import sys
import unittest

AVAILABLE=importlib.util.find_spec('numpy') is not None and importlib.util.find_spec('scipy') is not None
if AVAILABLE:
    import numpy as np
    sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'experiments')]
    import mfem_replay as replay


@unittest.skipUnless(AVAILABLE,'Optional NumPy/SciPy; pinned oracle includes both')
class ReplayLocationTests(unittest.TestCase):
    def test_strict_owners_and_physical_reconstruction_with_chunking(self):
        vertices,tets,_=replay.nd.fem.mesh(1)
        bary=np.array([.17,.23,.29,.31])
        points=np.einsum('i,tic->tc',bary,vertices[tets])
        owner,local,margin=replay.locate(vertices,tets,points,chunk=7)
        np.testing.assert_array_equal(owner,np.arange(len(tets)))
        np.testing.assert_allclose(local,np.tile(bary[1:],(len(tets),1)),atol=1e-14)
        self.assertAlmostEqual(margin,.17,places=13)

    def test_face_outside_empty_and_nonfinite_targets_rejected(self):
        vertices=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
        tets=np.array([[0,1,2,3]])
        for points in [[],[[.2,.2,0.]],[[.5,.5,.5]],[[float('nan'),.1,.1]]]:
            with self.assertRaises(ValueError):replay.locate(vertices,tets,points)
