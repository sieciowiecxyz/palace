import importlib.util
from pathlib import Path
import sys
import unittest

HAS_NUMPY = importlib.util.find_spec('numpy') is not None
if HAS_NUMPY:
    import numpy as np
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    spec = importlib.util.spec_from_file_location('maxwell_fem',
        Path(__file__).resolve().parents[1]/'experiments/maxwell_fem.py')
    fem = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fem)


@unittest.skipUnless(HAS_NUMPY,'Optional NumPy; pinned oracle includes it')
class MaxwellFEMTests(unittest.TestCase):
    def test_mesh_refinement_preserves_volume_and_closed_boundary(self):
        for refinement in range(3):
            vertices,tets,faces = fem.mesh(refinement)
            determinant = np.linalg.det(np.transpose(vertices[tets[:,1:]]-vertices[tets[:,:1]],(0,2,1)))
            self.assertGreater(np.min(determinant),0)
            self.assertEqual(len(tets),20*8**refinement)
            self.assertEqual(len(faces),20*4**refinement)
            self.assertAlmostEqual(sum(determinant)/6,4*np.pi/3,places=12)
            self.assertAlmostEqual(fem.reference.signed_volume(vertices,faces),4*np.pi/3,places=12)

    def test_whitney_edge_circulations_and_scaling(self):
        vertices = np.vstack([np.zeros(3),np.eye(3)])
        grad = fem.gradients(vertices)
        midpoint = np.asarray([(vertices[a]+vertices[b])/2 for a,b in fem.EDGES])
        lambdas = np.column_stack([1-midpoint.sum(axis=1),midpoint])
        values = fem.basis(lambdas,grad)
        tangents = np.asarray([vertices[b]-vertices[a] for a,b in fem.EDGES])
        np.testing.assert_allclose(np.einsum('eic,ec->ei',values,tangents),np.eye(6),atol=1e-15)
        m,k = fem.analytic_matrices(vertices)
        scaled_m,scaled_k = fem.analytic_matrices(vertices*3)
        np.testing.assert_allclose(scaled_m,3*m,atol=1e-15)
        np.testing.assert_allclose(scaled_k,k/3,atol=1e-15)
        self.assertGreater(np.linalg.eigvalsh(m).min(),0)
        nodal = np.asarray([2.,3.,-1.,0.4])
        gradient = np.asarray([nodal[b]-nodal[a] for a,b in fem.EDGES])
        np.testing.assert_allclose(k@gradient,0,atol=1e-14)

    def test_tetra_quadrature_moments_and_exact_constant_fields(self):
        lambdas,weights = fem.tetra_quadrature()
        self.assertAlmostEqual(sum(weights),1/6)
        np.testing.assert_allclose(weights@lambdas,np.ones(4)/24,atol=1e-15)
        np.testing.assert_allclose(lambdas.T@(weights[:,None]*lambdas),(np.ones((4,4))+np.eye(4))/120,atol=1e-15)
        vertices = np.vstack([np.zeros(3),np.eye(3)])
        field = np.array([0.2,0.4,-0.3])
        edge_values = np.asarray([np.dot(vertices[b]-vertices[a],field) for a,b in fem.EDGES])
        evaluated = np.einsum('e,pec->pc',edge_values,fem.basis(lambdas,fem.gradients(vertices)))
        np.testing.assert_allclose(evaluated,np.broadcast_to(field,evaluated.shape),atol=1e-15)
