import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('prom_sweep', Path(__file__).parents[1]/'experiments/prom_sweep.py')
prom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prom)


class PromProbeTests(unittest.TestCase):
    def config(self):
        _, _, cfg = prom.dev.fixture('coax-tiny')
        cfg = prom.dev.diagnostic_config('coax-tiny', cfg, True, preserve_coax_sweep='n78')
        return cfg

    def log(self):
        text = ''
        for e in [1,2]:
            for f in [3.3,3.9]:
                text += f'PALACE_PROM_SAMPLE: excitation={e} frequency_ghz={f}\n'
                text += 'PALACE_TRUE_RESIDUAL: norm_Ax_minus_b=1e-8 norm_b=1 relative=1e-8\n'
        for e in [1,2]:
            for i in range(7):
                text += f'PALACE_PROM_RAW: excitation={e} frequency_index={i} training={int(i in (0,6))} dimension=4 relative=1e-8\n'
        return text

    def test_probe_changes_only_explicit_adaptive_controls(self):
        cfg = self.config()
        changed = prom.probe_config(cfg, 2)
        self.assertNotIn('AdaptiveTol', cfg['Solver']['Driven'])
        self.assertEqual(changed['Solver']['Driven'].pop('AdaptiveTol'), .01)
        self.assertEqual(changed['Solver']['Driven'].pop('AdaptiveMaxSamples'), 2)
        self.assertEqual(cfg, changed)
        tighter=prom.probe_config(cfg,3,1e-8)
        self.assertEqual(tighter['Solver']['Linear']['Tol'],1e-8)
        self.assertEqual(cfg['Solver']['Linear']['Tol'],1e-6)
        for tol in [True,0,1e-11,1e-5,float('nan'),float('inf'),'1e-8']:
            with self.assertRaises(ValueError):prom.probe_config(cfg,3,tol)
        for count in [0,1,5,True,2.0,'2']:
            with self.assertRaises(ValueError): prom.probe_config(cfg, count)
        for key, value in [('Save', True), ('Restart',2), ('AdaptiveTol',.1)]:
            bad=json.loads(json.dumps(cfg));bad['Solver']['Driven'][key]=value
            with self.assertRaises(ValueError):prom.probe_config(bad,2)
        for freq in [[3.3,3.4], [3.9,3.3], [3.3,3.3,3.9], [3.3,float('nan'),3.9]]:
            bad=json.loads(json.dumps(cfg));bad['Solver']['Driven']['Samples']=[{'Type':'Point','Freq':freq}]
            with self.assertRaises(ValueError):prom.probe_config(bad,2)

    def test_held_out_original_residual_is_not_reduced_residual(self):
        cfg=prom.probe_config(self.config(),2)
        a=prom.audit(self.log(),cfg,2)
        self.assertTrue(a['execution_complete']);self.assertTrue(a['original_residual_passed'])
        self.assertEqual(a['held_out'],10)
        # A completed reduced solve is not accuracy PASS when the original residual is large.
        a=prom.audit(self.log().replace('dimension=4 relative=1e-8','dimension=4 relative=0.01'),cfg,2)
        self.assertTrue(a['execution_complete']);self.assertFalse(a['original_residual_passed'])
        for bad in [self.log()+self.log(), self.log().replace('frequency_index=3','frequency_index=2'),
                    self.log().replace('training=0','training=1'),self.log().replace('dimension=4','dimension=0'),
                    self.log().replace('dimension=4','dimension=100'), self.log().replace('relative=1e-8','relative=nan'),
                    self.log().replace('frequency_ghz=3.9','frequency_ghz=4.0'),
                    self.log().replace('norm_b=1 relative=1e-8','norm_b=1 relative=1e-3')]:
            with self.assertRaises(ValueError):prom.audit(bad,cfg,2)


if __name__ == '__main__': unittest.main()
