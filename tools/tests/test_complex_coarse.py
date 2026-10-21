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

    def mixed_rows(self):
        rows = []
        for case in ['regular', 'ill_scaled']:
            for mode in ['fp64', 'raw_fp32', 'scaled_refined_fp32']:
                refined = mode == 'scaled_refined_fp32'
                rows.append(dict(case=case, mode=mode, n=512, nrhs=2, updates=2,
                    corrections=2 if refined else 0,
                    factor_dtype='complex_fp64' if mode=='fp64' else 'complex_fp32',
                    residual_dtype='complex_fp64', fault_rejected=True,
                    relative_solution=1e-7 if mode=='raw_fp32' else 1e-13,
                    relative_rhs_residual=1e-7 if mode=='raw_fp32' else 1e-14,
                    componentwise_backward_error=1e-8 if mode=='raw_fp32' else 1e-14,
                    scale_min=.001 if refined and case=='ill_scaled' else .75 if refined else 1,
                    scale_max=1000 if refined and case=='ill_scaled' else .8 if refined else 1,
                    cudss_peak_bytes=1000, cudss_live_after_destroy=0,
                    analysis_s=.01, factor_s=.01, solve_s=.01, correction_s=.001, correction_backend='host_fp64' if mode=='fp64' else 'cuda_fp64', passed=True))
        return rows

    def test_mixed_probe_exact_case_dtype_and_original_equation_gates(self):
        encode = self.encode_mixed
        rows = self.mixed_rows()
        self.assertEqual(probe.parse_mixed_probe(encode(rows)), rows)
        for bad in [rows[:-1], rows+rows, list(reversed(rows))]:
            with self.assertRaises(ValueError): probe.parse_mixed_probe(encode(bad))
        for key,value in [('corrections', 1), ('factor_dtype', 'complex_fp64'),
                          ('residual_dtype', 'complex_fp32'), ('relative_solution', 1e-8),
                          ('componentwise_backward_error', 1e-8), ('fault_rejected', False),
                          ('scale_max', 1), ('passed', False), ('cudss_live_after_destroy', 1),
                          ('correction_s', float('nan')), ('correction_backend', 'host_fp64')]:
            bad = self.mixed_rows();bad[-1][key]=value
            with self.assertRaises(ValueError): probe.parse_mixed_probe(encode(bad))
        bad=self.mixed_rows();bad[1]['relative_solution']=.01
        probe.parse_mixed_probe(encode(bad))
        bad[1]['relative_solution']=.010001
        with self.assertRaises(ValueError): probe.parse_mixed_probe(encode(bad))

    def test_mixed_probe_preserves_failed_raw_illscaled_control_without_weakening_candidate(self):
        rows = self.mixed_rows(); rows[4].update(relative_solution=.2,
            componentwise_backward_error=.42, passed=False)
        encode = self.encode_mixed
        self.assertEqual(probe.parse_mixed_probe(encode(rows))[4]['passed'], False)
        rows[4]['passed'] = True
        with self.assertRaises(ValueError): probe.parse_mixed_probe(encode(rows))
        rows[4]['passed'] = False; rows[5]['relative_solution'] = 1e-8; rows[5]['passed'] = False
        with self.assertRaises(ValueError): probe.parse_mixed_probe(encode(rows))
        rows = self.mixed_rows(); rows[4].update(relative_solution=float('nan'), passed=False)
        with self.assertRaises(ValueError): probe.parse_mixed_probe(encode(rows))

    def encode_mixed(self, rows):
        return 'PALACE_MIXED_COARSE_HELPERS: cases=4 passed=1\n'+'\n'.join(json.dumps(r) for r in rows)

    def test_mixed_requires_exact_cuda_helper_marker(self):
        text = self.encode_mixed(self.mixed_rows())
        for bad in [text.replace('cases=4', 'cases=3'), text.replace('passed=1', 'passed=0'),
                    text.split('\n', 1)[1], text+'\n'+text.split('\n', 1)[0]]:
            with self.assertRaises(ValueError): probe.parse_mixed_probe(bad)

    def test_probe_variant_paths_reject_unknown(self):
        self.assertNotEqual(probe.variant_paths('mixed'), probe.variant_paths('reference'))
        with self.assertRaises(ValueError): probe.variant_paths('other')
