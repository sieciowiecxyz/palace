import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('pc_audit',Path(__file__).parents[1]/'pc_basis_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
import dev


def valid():return dict(enters=10,exits=10,active=0,mixed_forward=100,pc_original=120,
    outside_original=30,transpose_original=100,alias_original=0,capacity_original=0,
    cache_misses=1,cache_hits=99,allocated_bytes=3360,freed_bytes=3360,live_bytes=0,
    releases=1,closed=True,min_N=8192,scalar_bytes=8)


class PCBasisTests(unittest.TestCase):
    def log(self,r):return 'PALACE_PC_BASIS_END '+json.dumps(r)
    def test_scope_cache_coverage_cleanup_gate(self):
        self.assertTrue(audit.analyze(self.log(valid()))['passed'])
        for key,value in [('enters',0),('exits',9),('active',1),('mixed_forward',0),
                          ('outside_original',0),('transpose_original',0),('closed',False),
                          ('cache_misses',257),('freed_bytes',0),('live_bytes',1),
                          ('releases',2),('scalar_bytes',4),('min_N',0),('cache_hits',False)]:
            r=valid();r[key]=value
            with self.assertRaises(ValueError):audit.analyze(self.log(r))
        for text in ['',self.log(valid())*2,self.log(valid())+'\nPALACE_PC_BASIS_ERROR bad',self.log([])]:
            with self.assertRaises(ValueError):audit.analyze(text)

    def test_compensated_arithmetic_threshold_and_double_table_bytes(self):
        r=valid();r.update(arithmetic='compensated_bits',min_N=8192,allocated_bytes=6720,freed_bytes=6720)
        self.assertTrue(audit.analyze(self.log(r),'compensated_bits')['passed'])
        with self.assertRaises(ValueError):audit.analyze(self.log(r))
        for key,value in [('arithmetic','fp32_fused'),('min_N',16384),('allocated_bytes',256*6720+1)]:
            bad=dict(r);bad[key]=value
            with self.assertRaises(ValueError):audit.analyze(self.log(bad),'compensated_bits')
        with self.assertRaises(ValueError):audit.analyze(self.log(valid()),'compensated_bits')

    def test_runner_rejects_unqualified_combinations_before_runtime(self):
        with patch.object(dev,'require_host_memory',side_effect=AssertionError('runtime reached')):
            for mode in ['pc_basis_fp32_forward','pc_basis_compensated_forward']:
                base={mode:True,'native_complex_coarse':True,'release_final_solver':True,'pc_side':'right'}
                for key,value in [('native_complex_coarse',False),('release_final_solver',False),('pc_side','left'),
                                  ('cpu_reference',True),('nsys_window','0:2'),('ceed_qpool',True),('ams_cycles',2),('cudss_hybrid_mib',256)]:
                    flags=dict(base);flags[key]=value
                    with self.assertRaises(ValueError):dev.run('coax-tiny','/unused',60,**flags)
            with self.assertRaises(ValueError):
                dev.run('coax-tiny','/unused',60,pc_basis_fp32_forward=True,pc_basis_compensated_forward=True)

    def test_scope_only_wraps_B_and_release_precedes_final_marker(self):
        root=Path(__file__).resolve().parents[2]
        text=(root/'palace/linalg/iterative.cpp').read_text()
        body=text[text.index('inline void ApplyB('):text.index('inline void InitialResidual(')]
        self.assertIn('} scope;',body);self.assertIn('B->Mult(x, y);',body)
        self.assertNotIn('A->Mult',body)
        self.assertIn('PALACE_PC_BASIS_COMPENSATED_FORWARD',body)
        driven=(root/'palace/drivers/drivensolver.cpp').read_text()
        self.assertLess(driven.index('PalacePCBasisRelease();'),driven.index('PALACE_FINAL_SOLVER_RELEASED:'))
        release=driven[driven.index('const char *pc_basis ='):driven.index('PALACE_FINAL_SOLVER_RELEASED:')]
        self.assertIn('PALACE_PC_BASIS_COMPENSATED_FORWARD',release)
        cu=(root/'tools/experiments/ceed_tensor_probe.cu').read_text()
        self.assertIn('#include "../adapter/ceed_fused.cuh"',cu)
        self.assertIn('#include "../adapter/ceed_compensated.cuh"',cu)
