import importlib.util
import json
from pathlib import Path
import sys
import subprocess
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

    def test_antiresonance_keeps_S_power_and_energy_gates_without_VSWR(self):
        s,e=self.tables()
        s=json.loads(json.dumps(s));s[1][0][0]=2.9
        e=(e[0],[[2.9,1.,2.]])
        # Perfect reflection with zero transmission: Z has a pole, S is finite.
        s[1][0][1:]=[0,0,-8000,0,-8000,0,0,180]
        r=q.rf_metrics(s,s,e,e,[2.9],protocol='antiresonance')
        self.assertTrue(r['passed']);self.assertIsNone(r['max_delta_vswr'])
        self.assertIsNone(r['input_impedance'][0]['reference']['input_z_ohm'])
        self.assertIsNone(r['input_impedance'][0]['reference']['delta_z_bound_at_S_gate_ohm'])
        self.assertAlmostEqual(abs(complex(*r['input_impedance'][1]['reference']['input_z_ohm'])),0)
        bad=json.loads(json.dumps(s));bad[1][0][2]=1
        self.assertFalse(q.rf_metrics(s,bad,e,e,[2.9],protocol='antiresonance')['passed'])
        bad_energy=(e[0],[[2.9,1.,2.1]])
        self.assertFalse(q.rf_metrics(s,s,e,bad_energy,[2.9],protocol='antiresonance')['passed'])
        nonpassive=json.loads(json.dumps(s));nonpassive[1][0][1]=.1
        self.assertFalse(q.rf_metrics(nonpassive,nonpassive,e,e,[2.9],protocol='antiresonance')['passed'])
        with self.assertRaisesRegex(ValueError,'VSWR'):q.rf_metrics(s,s,e,e,[2.9])
        with self.assertRaisesRegex(ValueError,'2.900'):q.rf_metrics(s,s,e,e,[3.3],protocol='antiresonance')
        with self.assertRaisesRegex(ValueError,'Unknown'):q.rf_metrics(s,s,e,e,[2.9],protocol='other')

    def test_antiresonance_Z_uncertainty_bound_and_summary_separation(self):
        s,e=self.tables();s=json.loads(json.dumps(s));s[1][0][0]=2.9
        e=(e[0],[[2.9,1.,2.]])
        r=q.rf_metrics(s,s,e,e,[2.9],protocol='antiresonance')
        row=r['input_impedance'][0]['reference']
        z=complex(*row['input_z_ohm'])
        self.assertAlmostEqual(z.real,50*1.1/.9)
        # Exact Cayley identity bounds every complex perturbation |dS| <= 1e-3.
        import cmath
        for angle in [0,.3,1.,2.,3.]:
            sp=.1+1e-3*cmath.exp(1j*angle)
            self.assertLessEqual(abs(50*(1+sp)/(1-sp)-z),row['delta_z_bound_at_S_gate_ohm']+1e-12)
        a=self.receipt(3.3,100,50,1000,500);a['protocol']='antiresonance'
        with self.assertRaisesRegex(ValueError,'antiresonance'):q.summarize([a],[3.3])

    def test_CLI_rejects_antiresonance_receipt_before_matched_requalification(self):
        with tempfile.TemporaryDirectory() as td:
            receipt=Path(td)/'anti.json';output=Path(td)/'summary.json'
            receipt.write_text(json.dumps(dict(protocol='antiresonance',input_paths=['/unused','/unused'])))
            r=subprocess.run([sys.executable,str(Path(q.__file__)), '--summary',str(receipt),
                '--expected-frequencies','2.9','--corrections','3','--output',str(output)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('Matched-band summary cannot mix',r.stderr)
            self.assertFalse(output.exists())

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

    def median_receipts(self):
        rows=[]
        for i,(a,b) in enumerate([(10,5),(20,40),(100,80)]):
            r=self.receipt(3.5,a,b,1000+100*i,500+100*i)
            r.update(input_paths=[f'/ref{i}',f'/cand{i}'],run_container_names=[f'ref{i}',f'cand{i}'])
            rows.append(r)
        return rows

    def test_paired_medians_keep_pairing_and_distinguish_ratio_of_medians(self):
        r=q.paired_medians(self.median_receipts())
        self.assertEqual(r['reference_seconds'],dict(median=20,minimum=10,maximum=100))
        self.assertEqual(r['candidate_seconds'],dict(median=40,minimum=5,maximum=80))
        self.assertEqual(r['paired_speed_ratio']['median'],1.25)
        self.assertEqual(r['ratio_of_time_medians'],.5)
        self.assertAlmostEqual(r['paired_time_change_percent']['median'],-20)
        self.assertEqual(r['time_change_from_medians_percent'],100)
        self.assertEqual(r['reference_cgroup_bytes']['median'],1100)
        self.assertEqual(r['candidate_cgroup_bytes']['median'],600)
        self.assertEqual(r['total_field_rows'],3)

    def test_paired_medians_reject_duplicates_mixed_policy_and_failed_cases(self):
        rows=self.median_receipts()
        for bad in [[],rows[:2],rows+rows[:1],[rows[0]]*3]:
            with self.assertRaises(ValueError):q.paired_medians(bad)
        for key,val in [('input_paths',rows[0]['input_paths']),('run_container_names',rows[0]['run_container_names']),
                        ('frequency_ghz',3.3),('coarse_corrections',3),('source_sha256','different'),
                        ('case_without_frequency_sha256','different'),('build_manifest_sha256','different'),
                        ('passed',False),('protocol','antiresonance')]:
            bad=json.loads(json.dumps(rows));bad[1][key]=val
            with self.assertRaises(ValueError):q.paired_medians(bad)
        bad=json.loads(json.dumps(rows));bad[1]['candidate']['end_to_end_seconds']=float('nan')
        with self.assertRaises(ValueError):q.paired_medians(bad)

    def test_CLI_medians_cannot_mix_modes_or_reinterpret_antiresonance(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'anti.json';p.write_text(json.dumps(dict(protocol='antiresonance',input_paths=['/unused','/unused'])))
            for extra in [[],['--summary',str(p)],['--expected-frequencies','3.5'],['--protocol','antiresonance']]:
                out=Path(td)/'out.json'
                cmd=[sys.executable,str(Path(q.__file__)),'--paired-medians',str(p),str(p),str(p),'--output',str(out),*extra]
                r=subprocess.run(cmd,capture_output=True,text=True)
                self.assertNotEqual(r.returncode,0);self.assertFalse(out.exists())
                self.assertTrue('antiresonance protocol' in r.stderr or '--paired-medians requires' in r.stderr)

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
