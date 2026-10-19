import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

AVAILABLE = all(importlib.util.find_spec(name) is not None for name in ['numpy','scipy'])
if AVAILABLE:
    import numpy as np
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
    import maxwell_nd as nd


@unittest.skipUnless(AVAILABLE,'Optional NumPy/SciPy; pinned oracle includes both')
class MaxwellNDTests(unittest.TestCase):
    def test_input_mesh_jacobian_boundary_and_indices_are_validated(self):
        vertices,tets,faces = nd.fem.mesh(0)
        a,b,c = nd.validate_mesh(vertices,tets,faces[:,::-1])
        self.assertEqual(b.dtype,np.int32)
        np.testing.assert_array_equal(c,faces)
        for bad_tets,bad_faces in [
            (tets[:,[1,0,2,3]],faces),
            (tets.astype(float),faces),
            (tets,np.vstack([faces,faces[:1]])),
            (tets,faces[:-1]),
            (tets-100,faces)]:
            with self.assertRaises(ValueError): nd.validate_mesh(vertices,bad_tets,bad_faces)
        with self.assertRaises(ValueError): nd.validate_mesh(vertices*float('nan'),tets,faces)

    def test_reference_points_reject_outside_nonfinite_and_invalid_cell(self):
        space = nd.GlobalND.__new__(nd.GlobalND)
        space.tetrahedra = [[0,1,2,3]]
        for cell,points in [(1,[[.1,.1,.1]]),(0,[[.5,.5,.5]]),(0,[[-.01,0.,0.]]),
                            (0,[[float('nan'),0.,0.]]),(0,[])]:
            with self.assertRaises(ValueError): space.points(cell,points)
        self.assertTrue(space.points(0,[[.1,.2,.3]]).flags.c_contiguous)

    def test_invalid_mesh_rejected_before_native_load_and_close_is_idempotent(self):
        with patch.object(nd.ct,'CDLL') as load:
            with self.assertRaises(ValueError): nd.GlobalND([],[],[])
            load.assert_not_called()
        space = nd.GlobalND.__new__(nd.GlobalND)
        space.handle = None
        space.close()
        with self.assertRaises(ValueError): space.call('info',None)
