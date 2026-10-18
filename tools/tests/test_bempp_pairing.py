import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

AVAILABLE = all(importlib.util.find_spec(name) is not None for name in ['numpy','scipy'])
if AVAILABLE:
    import numpy as np
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
    fake_api = types.ModuleType('bempp_cl.api')
    fake_package = types.ModuleType('bempp_cl')
    fake_package.api = fake_api
    spec = importlib.util.spec_from_file_location('bempp_pairing',
        Path(__file__).resolve().parents[1]/'experiments/bempp_pairing.py')
    pairing = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,{'bempp_cl':fake_package,'bempp_cl.api':fake_api}):
        spec.loader.exec_module(pairing)


@unittest.skipUnless(AVAILABLE,'Optional NumPy/SciPy; pinned oracle includes both')
class BemppPairingTests(unittest.TestCase):
    def test_duffy_triangle_quadrature_moments(self):
        points,weights = pairing.quadrature()
        self.assertAlmostEqual(sum(weights),0.5)
        np.testing.assert_allclose(points@weights,[1/6,1/6],atol=1e-15)
        np.testing.assert_allclose((points**2)@weights,[1/12,1/12],atol=1e-15)
        self.assertAlmostEqual(np.dot(weights,np.prod(points,axis=0)),1/24)

    def test_spectrum_does_not_report_singular_skew_gram_as_full_rank(self):
        matrix = np.array([[0.,1.,0.],[-1.,0.,0.],[0.,0.,0.]])
        with np.errstate(divide='ignore'):
            result = pairing.spectrum(matrix,np.eye(3),np.eye(3))
        self.assertEqual(result['numerical_rank'],2)
        self.assertTrue(np.isinf(result['condition_2']))
        result = pairing.spectrum(np.diag([2.,3.,4.]),np.diag([4.,9.,16.]),np.eye(3))
        self.assertAlmostEqual(result['diagonal_mass_scaled_condition_2'],1.)

    def test_physical_gram_applies_both_dof_transforms(self):
        from scipy.sparse import csr_matrix
        class Space:
            grid_dof_count=3
            local2global=np.array([[0,1,2]])
            def evaluate(self,triangle,points):
                return np.broadcast_to(np.eye(3)[:,:,None],(3,3,points.shape[1]))
        grid = types.SimpleNamespace(number_of_elements=1,integration_elements=[2.])
        left,right=Space(),Space()
        left.grid=right.grid=grid
        left.dof_transformation=csr_matrix([[1.,0.],[2.,0.],[0.,3.]])
        right.dof_transformation=csr_matrix([[1.],[2.],[3.]])
        np.testing.assert_allclose(pairing.physical_gram(left,right),[[5.],[9.]],atol=1e-15)
