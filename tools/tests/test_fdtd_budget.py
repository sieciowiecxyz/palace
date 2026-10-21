import importlib.util
from pathlib import Path
import math
import unittest

spec = importlib.util.spec_from_file_location('fdtd_budget', Path(__file__).parents[1]/'fdtd_budget.py')
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)


class FDTDBudgetTests(unittest.TestCase):
    def test_counts_use_padded_nodes_and_uint32_ids_even_for_double(self):
        a=budget.estimate([1,2,3],[1,1,1],10)
        b=budget.estimate([1,2,3],[1,1,1],10,'double')
        self.assertEqual(a['nodes'],24)
        self.assertEqual(a['device_base_bytes'],24*48)
        self.assertEqual(b['device_base_bytes'],24*72)
        self.assertEqual(a['ids_bytes'],b['ids_bytes'])
        self.assertEqual(a['host_build_base_bytes'],24*48+22*6)
        self.assertEqual(a['full_field_DFT_one_frequency_bytes'],24*48)

    def test_cfl_scales_with_resolution_and_time_counts_round_up(self):
        a=budget.estimate([10]*3,[1]*3,1)
        b=budget.estimate([10]*3,[.5]*3,1)
        self.assertAlmostEqual(a['dt_seconds'],.001/(budget.C*math.sqrt(3)))
        self.assertAlmostEqual(b['dt_seconds'],a['dt_seconds']/2)
        self.assertGreaterEqual(a['steps']*a['dt_seconds'],1e-9)
        self.assertLess((a['steps']-1)*a['dt_seconds'],1e-9)

    def test_reject_invalid_inputs(self):
        for v in [0,-1,True,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):budget.estimate([1,1,v],[1]*3)
            with self.assertRaises(ValueError):budget.estimate([1]*3,[1]*3,time_ns=v)
        for dims in [[1,2],[],[1,2,3,4]]:
            with self.assertRaises(ValueError):budget.estimate(dims,[1]*3)
        for padding in [True,-1,.5]:
            with self.assertRaises(ValueError):budget.estimate([1]*3,[1]*3,padding=padding)
        with self.assertRaises(ValueError):budget.estimate([1]*3,[1]*3,precision='tf32')

    def test_hsg_forces_double_and_includes_source_padding(self):
        r=budget.hsg_estimate([100]*3,[1.1]*3,[10]*3,11)
        self.assertEqual(r['fine']['padding_per_side_cells'],46)
        self.assertEqual(r['fine']['length_mm'],[11]*3)
        self.assertEqual(r['fine']['cells'],[202]*3)
        self.assertEqual(r['main']['precision'],'double')
        self.assertEqual(r['fine']['precision'],'double')
        self.assertAlmostEqual(r['fine']['dt_seconds'],r['main']['dt_seconds']/11)
        self.assertEqual(r['device_base_bytes'],sum(r[g]['device_base_bytes'] for g in ['main','fine']))
        for ratio in [0,1,2,True,3.0]:
            with self.assertRaises(ValueError):budget.hsg_estimate([100]*3,[1]*3,[10]*3,ratio)
        with self.assertRaises(ValueError):budget.hsg_estimate([10]*3,[1]*3,[9]*3,3)
