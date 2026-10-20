import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('complex_probe', Path(__file__).parents[1]/'experiments/complex_coarse.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ComplexProbeTests(unittest.TestCase):
    def rows(self):
        return [dict(mode=mode, n=512, dimension=dim, nrhs=2, updates=2,
                     relative_solution=1e-14, relative_rhs_residual=1e-15,
                     cudss_peak_bytes=1000, cudss_live_after_destroy=0,
                     analysis_s=.01, factor_s=.02, solve_s=.001, passed=True)
                for mode, dim in [('native_complex_fp64', 512), ('real_block_fp64', 1024)]]

    def parse(self, rows):
        return probe.parse_probe('\n'.join(json.dumps(row) for row in rows))

    def test_requires_both_representations_and_exact_coverage(self):
        rows = self.rows()
        self.assertEqual(self.parse(rows), rows)
        for bad in [rows[:1], rows+rows, list(reversed(rows))]:
            with self.assertRaises(ValueError): self.parse(bad)
        for key, value in [('nrhs', 1), ('updates', 1), ('dimension', 1024),
                           ('cudss_live_after_destroy', 1), ('passed', False)]:
            bad = self.rows(); bad[0][key] = value
            with self.assertRaises(ValueError): self.parse(bad)

    def test_rejects_nonfinite_costs_and_inaccurate_solutions(self):
        for key in ['relative_solution', 'relative_rhs_residual', 'factor_s', 'cudss_peak_bytes']:
            for value in [float('nan'), float('inf'), -1, True, '0']:
                rows = self.rows(); rows[0][key] = value
                with self.assertRaises(ValueError): self.parse(rows)
        for key in ['relative_solution', 'relative_rhs_residual']:
            rows = self.rows(); rows[0][key] = 2e-10
            with self.assertRaises(ValueError): self.parse(rows)

    def test_hybrid_requires_exact_budget_and_actual_memory_queries(self):
        rows = self.rows()
        for row in rows:
            row.update(hybrid_limit_bytes=256*1024**2, minimum_device_bytes=123,
                       estimated_host_bytes=456)
        text = lambda r: '\n'.join(json.dumps(row) for row in r)
        self.assertEqual(probe.parse_probe(text(rows), 256), rows)
        with self.assertRaises(ValueError): probe.parse_probe(text(rows))
        for key, value in [('hybrid_limit_bytes', 512*1024**2),
                           ('minimum_device_bytes', 257*1024**2),
                           ('minimum_device_bytes', -1), ('estimated_host_bytes', True),
                           ('estimated_host_bytes', float('nan'))]:
            bad = json.loads(json.dumps(rows));bad[0][key] = value
            with self.assertRaises(ValueError): probe.parse_probe(text(bad), 256)
        bad = json.loads(json.dumps(rows));del bad[0]['minimum_device_bytes']
        with self.assertRaises(ValueError): probe.parse_probe(text(bad), 256)

    def test_hybrid_budget_bounds(self):
        for value in [256, 512, 16384, None]: probe.validate_hybrid_mib(value)
        for value in [0, 255, 16385, True, 256.0, '256']:
            with self.assertRaises(ValueError): probe.validate_hybrid_mib(value)
