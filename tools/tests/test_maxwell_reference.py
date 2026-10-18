import importlib.util
from pathlib import Path
import math
import unittest
from collections import Counter

spec = importlib.util.spec_from_file_location('mie_reference',Path(__file__).parents[1]/'maxwell_reference.py')
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)


class MaxwellReferenceTests(unittest.TestCase):
    def test_lossless_energy_and_forward_optical_theorem(self):
        for x in [0.1,1.0,2.5]:
            scatter,extinction = ref.cross_sections(radius=x)
            forward = ref.far_field([(0,0,1)],radius=x)[0]
            self.assertAlmostEqual(scatter,extinction,places=12)
            self.assertAlmostEqual(extinction,4*math.pi*forward[0].imag,places=12)
            self.assertLess(abs(forward[1])+abs(forward[2]),1e-14)

    def test_pec_rayleigh_limit_includes_electric_and_magnetic_dipoles(self):
        x = 1e-3
        scatter,_ = ref.cross_sections(radius=x)
        self.assertAlmostEqual(scatter/((10*math.pi/3)*x**6),1,places=5)
        a,b = ref.coefficients(x)
        self.assertAlmostEqual(a[0].imag/(-2*x**3/3),1,places=5)
        self.assertAlmostEqual(b[0].imag/(x**3/3),1,places=5)

    def test_icosphere_closed_outward_and_expected_topology(self):
        for level in range(4):
            vertices,faces = ref.icosphere(level)
            edges = Counter(tuple(sorted((t[i],t[(i+1)%3]))) for t in faces for i in range(3))
            self.assertEqual(len(faces),20*4**level)
            self.assertEqual(len(vertices)-len(edges)+len(faces),2)
            self.assertTrue(all(n==2 for n in edges.values()))
            for t in faces:
                a,b,c = (vertices[i] for i in t)
                u,v = [b[i]-a[i] for i in range(3)],[c[i]-a[i] for i in range(3)]
                cross = (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                self.assertGreater(sum(x*y for x,y in zip(a,cross)),0)

    def test_invalid_reference_inputs_rejected(self):
        for x in [0,-1,4]:
            with self.assertRaises(ValueError): ref.coefficients(x)
        for level in [-1,4,True]:
            with self.assertRaises(ValueError): ref.icosphere(level)
