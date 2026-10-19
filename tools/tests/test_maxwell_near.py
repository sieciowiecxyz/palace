import importlib.util
from pathlib import Path
import unittest
import sys
import types
from unittest.mock import patch

AVAILABLE=importlib.util.find_spec('numpy') is not None
if AVAILABLE:
    import numpy as np
    spec=importlib.util.spec_from_file_location('maxwell_near',Path(__file__).resolve().parents[1]/'experiments/maxwell_near.py')
    near=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(near)
    jit_spec=importlib.util.spec_from_file_location('maxwell_near_jit',Path(__file__).resolve().parents[1]/'experiments/maxwell_near_jit.py')
    jit_python=importlib.util.module_from_spec(jit_spec)
    stub=types.ModuleType('numba')
    stub.njit=lambda **kwargs:lambda function:function
    with patch.dict(sys.modules,{'numba':stub}):jit_spec.loader.exec_module(jit_python)


@unittest.skipUnless(AVAILABLE,'Optional NumPy; pinned oracle includes it')
class NearPanelTests(unittest.TestCase):
    def test_explicit_jit_kernel_math_matches_numpy_without_compilation(self):
        point=np.array([.23,.19,.15])
        q=self.quadrature(4)
        expected=near.integrate(point,self.panel(),1.7,*q)
        actual=jit_python.integrate(point,self.panel(),1.7,*q)
        np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-13)

    def test_explicit_jit_tree_matches_numpy_with_bounded_stack(self):
        point=np.array([.23,.19,.15])
        q=self.quadrature(3)
        expected,stats=near.adaptive(point,self.panel(),1.7,*q,ratio=2.,max_depth=2)
        actual,other=jit_python.adaptive(point,self.panel(),1.7,*q,ratio=2.,max_depth=2)
        np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-13)
        self.assertEqual(stats,other)
        self.assertGreater(stats['depth_hits'],0)

    @unittest.skipUnless(importlib.util.find_spec('scipy') is not None,'Optional SciPy; pinned oracle includes it')
    def test_independent_solid_angle_octant_orientation_and_scale(self):
        vertices=np.eye(3)
        self.assertAlmostEqual(near.laplace_normal_reference(vertices,np.zeros(3)),1/8,places=14)
        self.assertAlmostEqual(near.laplace_normal_reference(vertices[[0,2,1]],np.zeros(3)),-1/8,places=14)
        self.assertAlmostEqual(near.laplace_normal_reference(3*vertices,np.zeros(3)),1/8,places=14)
        with self.assertRaises(ValueError):near.laplace_normal_reference(vertices,vertices[0])

    def panel(self):
        vertices=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
        a,b=.4+.2j,-.3+.1j
        currents=np.stack([a*vertices+[.2+.1j,.4-.3j,0.],b*vertices+[-.1+.5j,.3+.1j,0.]])
        return vertices,currents,np.array([2*a,2*b])

    def quadrature(self,order=8):
        x,w=np.polynomial.legendre.leggauss(order)
        x,w=(x+1)/2,w/2
        return np.array([(a,(1-a)*b) for a in x for b in x]).T,np.array([wa*wb*(1-a) for a,wa in zip(x,w) for wb in w])

    def test_rigid_rotation_and_translation_covariance(self):
        point=np.array([.23,.19,.15])
        panel=self.panel()
        rotation=np.array([[0.,0.,1.],[1.,0.,0.],[0.,1.,0.]])
        offset=np.array([.3,-.7,1.2])
        transformed=(panel[0]@rotation.T+offset,panel[1]@rotation.T,panel[2])
        a=near.integrate(point,panel,1.7,*self.quadrature())
        b=near.integrate(point@rotation.T+offset,transformed,1.7,*self.quadrature())
        np.testing.assert_allclose(b,a@rotation.T,rtol=1e-12,atol=1e-13)

    def test_subtriangle_area_mapping_and_depth_exhaustion(self):
        point=np.array([3.,4.,5.])
        panel=self.panel()
        q=self.quadrature(12)
        root=near.integrate(point,panel,1.7,*q)
        a,b,c=np.array([[0.,0.],[1.,0.],[0.,1.]])
        ab,ac,bc=(a+b)/2,(a+c)/2,(b+c)/2
        refined=sum((near.integrate(point,panel,1.7,*q,child=np.array(child))
                     for child in [(a,ab,ac),(ab,b,bc),(ac,bc,c),(ab,bc,ac)]),np.zeros((4,3),complex))
        np.testing.assert_allclose(root,refined,rtol=1e-12,atol=1e-13)
        fields,stats=near.adaptive(point,panel,1.7,*q,ratio=100.,max_depth=0)
        np.testing.assert_allclose(fields,root,rtol=1e-14,atol=1e-14)
        self.assertEqual(stats,dict(leaves=1,max_depth=0,depth_hits=1))

    def test_invalid_limits_and_coincident_target_are_rejected(self):
        panel=self.panel()
        for ratio,depth in [(0.,1),(1.,-1)]:
            with self.assertRaises(ValueError):near.adaptive(np.array([0.,0.,1.]),panel,1.7,*self.quadrature(),ratio=ratio,max_depth=depth)
        with self.assertRaises(ValueError):near.integrate(np.zeros(3),panel,1.7,np.zeros((2,1)),np.array([.5]))
