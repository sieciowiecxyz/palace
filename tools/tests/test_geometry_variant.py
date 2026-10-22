import importlib.util
from pathlib import Path
import unittest

import numpy as np

spec = importlib.util.spec_from_file_location('geometry_variant', Path(__file__).parents[1]/'experiments/geometry_variant.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class GeometryVariantTests(unittest.TestCase):
    def tetrahedron(self):
        corners = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
        return np.vstack([corners, [(corners[a]+corners[b])/2 for a, b in g.EDGES]])

    def test_gmsh_shape_partition_gradient_and_affine_determinant(self):
        np.testing.assert_allclose(g.GRADIENTS.sum(axis=1), 0, atol=1e-14)
        tet = self.tetrahedron()
        np.testing.assert_allclose(g.determinant_coefficients(tet[None]), 1, atol=2e-14)
        transform = np.array([[2., .3, .5], [0., 3., .1], [0., 0., 4.]])
        moved = tet @ transform.T + [100., 20., -12.]
        np.testing.assert_allclose(g.determinant_coefficients(moved[None]), 24, rtol=1e-12)
        np.testing.assert_allclose(g.BERNSTEIN.sum(axis=1), 1)

    def test_quadratic_bend_detects_inversion_invisible_to_corner_volume(self):
        tet = self.tetrahedron(); tet[4, 2] = 2.
        # Corners remain the original positive tet, but the mid-edge bends invert it.
        report = g.jacobian_bounds(tet, np.arange(10)[None])
        self.assertEqual(report['uncertified_elements'], 1)
        self.assertLess(report['minimum_determinant_coefficient'], 0)

    def test_bernstein_polynomial_reconstructs_arbitrary_interior_determinants(self):
        tet = self.tetrahedron(); tet[4:] += np.random.default_rng(4).normal(0, .015, (6, 3))
        points = np.random.default_rng(5).dirichlet([1., 1., 1., 1.], 21)
        jac = np.einsum('na,pnj->paj', tet-tet[:1], g.gradients(points))
        basis = np.array([[6/np.prod([g.math.factorial(int(a)) for a in alpha])
                           * np.prod(point**alpha) for alpha in g.ALPHAS] for point in points])
        coeff = g.determinant_coefficients(tet[None])[0]
        np.testing.assert_allclose(basis @ coeff, np.linalg.det(jac), atol=3e-14)

    def test_translation_plateau_and_protected_outer_support(self):
        xyz = np.array([[0., 0., 0.], [36., 36., 12.035], [0., 0., 12.832],
                        [0., 0., -35.], [0., 0., 30.], [145., 0., 12.]])
        moved, bound = g.deformation(xyz, [2., 11., 14., 30.], [55., 70.], 2.)
        np.testing.assert_array_equal(moved[[0, 3, 4, 5]], xyz[[0, 3, 4, 5]])
        np.testing.assert_allclose(moved[[1, 2]]-xyz[[1, 2]], [[0, 0, 2], [0, 0, 2]])
        self.assertGreater(bound, .5)
        for z, r, s in [([2, 1, 14, 30], [55, 70], 2), ([2, 11, 14, 30], [70, 55], 2),
                        ([2, 11, 14, 30], [55, 70], 4), ([2, 11, 14, 30], [55, 70], 0),
                        ([2, 11, 14, 30], [55, 70], float('nan'))]:
            with self.assertRaises(ValueError): g.deformation(xyz, z, r, s)


if __name__ == '__main__':
    unittest.main()
