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
    transmission_spec=importlib.util.spec_from_file_location('bempp_transmission',
        Path(__file__).resolve().parents[1]/'experiments/bempp_transmission.py')
    transmission=importlib.util.module_from_spec(transmission_spec)
    with patch.dict(sys.modules,{'bempp_cl':package,'bempp_cl.api':api,'bempp_nd2_coupling':coupling}):
        transmission_spec.loader.exec_module(transmission)


@unittest.skipUnless(AVAILABLE,'Optional NumPy/SciPy; pinned oracle includes both')
class ND2SchurTests(unittest.TestCase):
    def test_reference_surface_refinement_preserves_planes_volume_and_orientation(self):
        from collections import Counter
        vertices,faces=transmission.surface_mesh(4)
        self.assertEqual(len(faces),1280)
        edges=Counter(tuple(sorted((int(a),int(b)))) for face in faces for a,b in zip(face,np.roll(face,-1)))
        self.assertEqual(len(edges),1920)
        self.assertEqual(set(edges.values()),{2})
        a,b,c=vertices[faces].transpose(1,0,2)
        self.assertAlmostEqual(float(np.einsum('ij,ij->',a,np.cross(b,c))/6),4*np.pi/3,places=12)
        self.assertTrue(np.all(np.einsum('ij,ij->i',np.cross(b-a,c-a),(a+b+c)/3)>0))
        base_vertices,base_faces=transmission.surface_mesh(1)
        for face in base_faces:
            triangle=base_vertices[face]
            n=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0])
            n/=np.linalg.norm(n)
            self.assertLessEqual(float(np.max((vertices-triangle[0])@n)),1e-12)
        with self.assertRaises(ValueError):transmission.surface_mesh(5)

    def test_transmission_incident_phase_and_weighted_complex_error(self):
        points=np.array([[0.,0.,0.],[.2,-.1,.7]])
        electric,magnetic=transmission.incident(points)
        np.testing.assert_allclose(electric[:,0],np.exp(1j*points[:,2]))
        np.testing.assert_allclose(magnetic[:,1],electric[:,0])
        self.assertEqual(np.count_nonzero(electric[:,1:]),0)
        self.assertEqual(np.count_nonzero(magnetic[:,[0,2]]),0)
        self.assertAlmostEqual(transmission.relative((1.+.2j)*electric,electric,np.array([.3,.7])),.2)
        self.assertEqual(transmission.relative(electric,electric),0.)

    def test_nested_surface_parents_and_rejection_of_crossed_cells(self):
        def volume(level):
            vertices,tets,faces=coupling.fem.mesh(level)
            return types.SimpleNamespace(vertices=vertices,tetrahedra=tets,faces=faces)
        def surface(level,shift=0.):
            vertices,_,faces=coupling.fem.mesh(level)
            return types.SimpleNamespace(vertices=(vertices+shift).T,elements=faces.T,number_of_elements=len(faces))
        coarse=volume(0)
        cells,normals,parents=coupling.boundary_parents(coarse,surface(1))
        self.assertEqual(len(cells),80)
        np.testing.assert_array_equal(np.bincount(parents),np.full(20,4))
        np.testing.assert_allclose(np.linalg.norm(normals,axis=1),1.,atol=1e-15)
        for cell,face in zip(cells,parents):
            self.assertTrue(set(coarse.faces[face]).issubset(coarse.tetrahedra[cell]))
        with self.assertRaises(ValueError):coupling.boundary_parents(volume(1),surface(0))
        with self.assertRaises(ValueError):coupling.boundary_parents(coarse,surface(1,shift=.001))

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
