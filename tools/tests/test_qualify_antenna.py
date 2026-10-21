import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).parents[1]))
spec=importlib.util.spec_from_file_location('qualify_antenna',Path(__file__).parents[1]/'qualify_antenna.py')
q=importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)


class QualificationTests(unittest.TestCase):
    def tables(self):
        header=['f (GHz)']
        for p in ['1][1','2][1','1][2','2][2']:
            header += [f'|S[{p}]| (dB)', f'arg(S[{p}]) (deg.)']
        s=(header,[[3.3,-20,0,-40,0,-40,0,-20,0]])
        e=(['f (GHz)','E1','E2'],[[3.3,1.,2.]])
        return s,e

    def test_complex_phase_wrap_and_frozen_energy_gate(self):
        s,e=self.tables()
        rotated=json.loads(json.dumps(s))
        for i in [2,4,6,8]:rotated[1][0][i]=360
        self.assertTrue(q.rf_metrics(s,rotated,e,e,[3.3])['passed'])
        bad_energy=(e[0],[[3.3,1.,2.1]])
        self.assertFalse(q.rf_metrics(s,s,e,bad_energy,[3.3])['passed'])
        mismatch=json.loads(json.dumps(s));mismatch[0][1]='|S[2][2]| (dB)'
        with self.assertRaises(ValueError):q.rf_metrics(s,mismatch,e,e,[3.3])
        with self.assertRaises(ValueError):q.rf_metrics(s,s,e,e,[3.4])
        unity=json.loads(json.dumps(s));unity[1][0][1]=0
        with self.assertRaisesRegex(ValueError,'VSWR'):q.rf_metrics(s,unity,e,e,[3.3])
        zero=(e[0],[[3.3,0.,2.]])
        with self.assertRaises(ValueError):q.rf_metrics(s,s,zero,e,[3.3])

    def test_csv_rejects_missing_nonfinite_and_width_errors(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'values.csv'
            for text in ['f,x\n','f,x\n3.3,nan\n','f,x\n3.3,inf\n','f,x\n3.3\n','f,x\n3.3,no\n']:
                p.write_text(text)
                with self.assertRaises(ValueError):q.read_csv(p)
            p.write_text('f,x\n3.3,1\n')
            self.assertEqual(q.read_csv(p),(['f','x'],[[3.3,1.]]))

    def test_incomplete_artifacts_never_qualify(self):
        cfg={'Solver':{'Driven':{'Samples':[{'Freq':[3.3]}]}},
             'Boundaries':{'LumpedPort':[{'Index':1,'Excitation':1},{'Index':2,'Excitation':2}]}}
        with tempfile.TemporaryDirectory() as td:
            paths=[Path(td)/v for v in ['reference','candidate']]
            for p in paths:
                p.mkdir()
                for name,value in [('config.json',cfg),('build-manifest.json',{}),('result.json',{'complete':False,'exit_code':0})]:
                    q.dev.write(p/name,value)
            with self.assertRaisesRegex(ValueError,'Incomplete'):q.qualify(*paths)
            different=json.loads(json.dumps(cfg));different['Solver']['Driven']['Samples'][0]['Freq']=[3.4]
            q.dev.write(paths[1]/'config.json',different)
            with self.assertRaisesRegex(ValueError,'identical'):q.qualify(*paths)

    def receipt(self,f,ref,cand,refmem,candmem):
        return dict(passed=True,frequency_ghz=f,coarse_corrections=2,source_sha256='same',build_manifest_sha256='same',case_without_frequency_sha256='same',
                    metrics=dict(passed=True,max_delta_S=0,max_delta_vswr=0,max_delta_power=0,max_relative_energy=0),
                    fields=dict(passed=True,entries=[dict(relative_E=0,relative_B=0)]),
                    reference=dict(end_to_end_seconds=ref,cgroup_memory_peak_bytes=refmem,iterations=[1,1]),
                    candidate=dict(end_to_end_seconds=cand,cgroup_memory_peak_bytes=candmem,iterations=[1,1]),
                    written_artifact_bytes=[1,1])

    def test_summary_weights_total_time_and_takes_peak_not_sum(self):
        a=self.receipt(3.3,100,50,1000,500)
        b=self.receipt(3.4,200,200,1200,900)
        s=q.summarize([b,a],[3.3,3.4])
        self.assertEqual(s['reference_end_to_end_seconds'],300)
        self.assertAlmostEqual(s['time_saving_percent'],100/6)
        self.assertEqual(s['reference_max_cgroup_bytes'],1200)
        self.assertEqual(s['candidate_max_cgroup_bytes'],900)
        self.assertEqual(s['max_cgroup_saving_percent'],25)
        self.assertEqual(s['total_field_rows'],2)

    def test_fixed_correction_policies_are_explicit_and_never_mixed(self):
        for count in [None,True,1,5,2.0]:
            with self.assertRaisesRegex(ValueError,'fixed correction count'):q.qualify('/unused','/unused',count)
        a=self.receipt(3.3,100,50,1000,500)
        b=self.receipt(3.4,200,200,1200,900);b['coarse_corrections']=3
        with self.assertRaisesRegex(ValueError,'mixes fixed correction'):q.summarize([a,b],[3.3,3.4])
        a['coarse_corrections']=3
        self.assertEqual(q.summarize([a,b],[3.3,3.4])['coarse_corrections'],3)

    def test_summary_rejects_duplicates_failures_and_changed_mesh_or_build(self):
        a=self.receipt(3.3,100,50,1000,500)
        b=self.receipt(3.4,200,200,1200,900)
        for bad in [[a],[a,a],[a,b,b]]:
            with self.assertRaises(ValueError):q.summarize(bad,[3.3,3.4])
        for key,value in [('passed',False),('source_sha256','other'),('build_manifest_sha256','other'),('case_without_frequency_sha256','other')]:
            c=json.loads(json.dumps(b));c[key]=value
            with self.assertRaises(ValueError):q.summarize([a,c],[3.3,3.4])
        c=json.loads(json.dumps(b));c['candidate']['end_to_end_seconds']=float('nan')
        with self.assertRaises(ValueError):q.summarize([a,c],[3.3,3.4])


if __name__=='__main__':unittest.main()
