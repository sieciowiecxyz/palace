import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).parents[1]))
import stage_rf_compare as rf


def synthetic_run():
    f=1.92;rho=.1;coupling=.01;loss=.005
    flux=1-rho*rho-coupling*coupling-loss
    config={'Model':{'L0':.001,'Lc':300.},'Domains':{'Materials':[{'Attributes':[2],'LossTan':.01}],
              'Postprocessing':{'Energy':[{'Index':2,'Attributes':[2]}]}},
            'Boundaries':{'LumpedPort':[{'Index':p,'Excitation':p,'R':50.} for p in (1,2)],
                'Postprocessing':{'SurfaceFlux':[{'Index':1,'Type':'Power'}],'FarField':{'NSample':6}}}}
    header=['f (GHz)'];row=[f]
    for src in (1,2):
        for dst in (1,2):
            header.extend([f'|S[{dst}][{src}]| (dB)',f'arg(S[{dst}][{src}]) (deg.)'])
            row.extend([20*math.log10(rho if src==dst else coupling),0.])
    tables={'port-S.csv':(header,[row]),
            'port-V.csv':(['f (GHz)','V_inc[1][1] (V)','V_inc[2][2] (V)'],[[f,math.sqrt(50),math.sqrt(50)]]),
            'domain-E.csv':(['f (GHz)','E_elec[2][1] (J)','E_elec[2][2] (J)'],
                            [[f]+[loss/(4*math.pi*f*1e9*.01)]*2]),
            'surface-F.csv':(['f (GHz)','Φ_pow[1][1] (W)','Φ_pow[1][2] (W)'],[[f,flux,flux]])}
    for field in ('E','B'):
        header=['f (GHz)'];row=[f]
        for port in (1,2):
            for axis in ('x','y','z'):
                for part in ('Re','Im'):
                    header.append(f'{part}{{{field}_{axis}[1][{port}]}} (unit)')
                    row.append(1. if part=='Re' else 0.)
        tables['probe-'+field+'.csv']=(header,[row])
    scale=rf.Z0/.3;raw=math.sqrt(flux*rf.Z0/(4*math.pi))/scale
    angles=rf.sphere(6)+[(45.,45.)]
    tables['farfield-rE.csv']=(['f (GHz)','exc','theta (deg.)','phi (deg.)',
                               'r*Re{E_x} (V)','r*Im{E_x} (V)','r*Re{E_y} (V)',
                               'r*Im{E_y} (V)','r*Re{E_z} (V)','r*Im{E_z} (V)'],
                              [[f,port,*angle,raw,0.,0.,0.,0.,0.] for port in (1,2) for angle in angles])
    plan={key:'same' for key in ('identity','build','source','image_id','seconds','memory_gib',
          'staged_config_sha256','runner_sha256','helper_sha256','full_expectations')}
    plan.update(stage='full',cpu=False,threads=1,stage_trace=False,
                features={'PALACE_PROBE_LOCATOR':'gslib'},
                environment={'MFEM_MEMORY':'cuda','PALACE_PROBE_LOCATOR':'gslib'})
    return dict(config=config,plan=plan,tables=tables,source_proof={'passed':True},
                fingerprint={'config_sha256':'same','mesh_sha256':'same'},completion={'complete':True})


class RFComparisonTests(unittest.TestCase):
    def setUp(self):
        self.a=synthetic_run();self.b=copy.deepcopy(self.a)
        self.b['plan']['features']['PALACE_PROBE_LOCATOR']='mfem'
        self.b['plan']['environment']['PALACE_PROBE_LOCATOR']='mfem'

    def compare(self,legacy=False,integration=False):
        with mock.patch.object(rf,'load_run',side_effect=[self.a,self.b]):
            return rf.compare_runs('a','b',legacy_reference=legacy,integration=integration)

    def combined_pair(self):
        for run,value in ((self.a,'0'),(self.b,'1')):
            run['plan']['features']['PALACE_SINGLE_RANK_DIRECT_MESH']=value
            run['plan']['environment']['PALACE_SINGLE_RANK_DIRECT_MESH']=value

    def test_default_rejects_combined_feature_changes(self):
        self.combined_pair()
        with self.assertRaisesRegex(ValueError,'one prototype flag'):self.compare()

    def test_explicit_integration_accepts_exact_forward_pair(self):
        self.combined_pair()
        result=self.compare(integration=True)
        self.assertTrue(result['passed']);self.assertTrue(result['integration'])
        self.assertEqual(len(result['intentional_feature_changes']),2)
        self.assertIn('combined integration',result['scope'])
        self.assertIn('not repeated medians',result['scope'])
        self.assertFalse(result['production_promoted'])

    def test_integration_rejects_reverse_single_and_implicit_baselines(self):
        with self.assertRaisesRegex(ValueError,'exactly'):self.compare(integration=True)
        self.combined_pair();self.a,self.b=self.b,self.a
        with self.assertRaisesRegex(ValueError,'exactly'):self.compare(integration=True)
        self.a,self.b=self.b,self.a
        self.a['plan']['features'].pop('PALACE_SINGLE_RANK_DIRECT_MESH')
        self.a['plan']['environment'].pop('PALACE_SINGLE_RANK_DIRECT_MESH')
        with self.assertRaisesRegex(ValueError,'exactly'):self.compare(integration=True)

    def test_integration_rejects_legacy_before_loading(self):
        with mock.patch.object(rf,'load_run') as load:
            with self.assertRaisesRegex(ValueError,'not a legacy'):
                rf.compare_runs('a','b',legacy_reference=True,integration=True)
            load.assert_not_called()

    def test_integration_retains_environment_provenance_and_rf_gates(self):
        self.combined_pair();self.b['plan']['environment']['uncontrolled']='1'
        with self.assertRaisesRegex(ValueError,'environment'):self.compare(integration=True)
        self.b['plan']['environment'].pop('uncontrolled')
        self.b['plan']['source']='different'
        with self.assertRaisesRegex(ValueError,'source'):self.compare(integration=True)
        self.b['plan']['source']=self.a['plan']['source']
        self.b['tables']['surface-F.csv'][1][0][1]+=.03
        self.assertFalse(self.compare(integration=True)['passed'])

    def test_single_flag_op_to_combined_remains_default(self):
        self.combined_pair()
        self.a['plan']['features']['PALACE_PROBE_LOCATOR']='mfem'
        self.a['plan']['environment']['PALACE_PROBE_LOCATOR']='mfem'
        result=self.compare()
        self.assertTrue(result['passed']);self.assertFalse(result['integration'])
        self.assertEqual(set(result['intentional_feature_changes']),{'PALACE_SINGLE_RANK_DIRECT_MESH'})

    def test_matched_pair_passes_closed_power_and_native_farfield_gates(self):
        result=self.compare();self.assertTrue(result['passed'])
        self.assertFalse(result['production_promoted'])
        self.assertEqual(result['intentional_feature_changes']['PALACE_PROBE_LOCATOR'],
                         {'reference':'gslib','candidate':'mfem'})
        self.assertTrue(all(abs(x['residual_w'])<1e-14 for x in result['power_balance']['reference']['rows']))
        for item in result['farfield_to_flux']:
            self.assertEqual(item['integrated_directions'],6)
            self.assertEqual(item['supplied_directions'],7)
            self.assertAlmostEqual(item['ratio'],1.,places=12)

    def test_bad_port_cannot_hide_behind_high_amplitude_other_port(self):
        for run in (self.a,self.b):
            h,rows=run['tables']['probe-E.csv']
            for i,name in enumerate(h):
                if '[1][1]' in name:rows[0][i]*=1e9
        h,rows=self.b['tables']['probe-E.csv']
        for i,name in enumerate(h):
            if '[1][2]' in name:rows[0][i]*=1.001
        report=self.compare();self.assertFalse(report['passed'])
        errors=[x for x in report['probes'] if x['field']=='E']
        self.assertTrue(next(x for x in errors if x['port']==1)['passed'])
        self.assertFalse(next(x for x in errors if x['port']==2)['passed'])

    def test_bad_frequency_cannot_hide_behind_high_amplitude_other_frequency(self):
        for run in (self.a,self.b):
            for name,(header,rows) in run['tables'].items():
                extra=copy.deepcopy(rows)
                for row in extra:
                    row[0]=3.55
                    if name=='domain-E.csv':
                        for i in range(1,len(row)):row[i]*=1.92/3.55
                rows.extend(extra)
            header,rows=run['tables']['probe-E.csv']
            for i in range(1,len(header)):rows[0][i]*=1e9
        header,rows=self.b['tables']['probe-E.csv']
        for i in range(1,len(header)):rows[1][i]*=1.001
        result=self.compare();self.assertFalse(result['passed'])
        errors=[x for x in result['probes'] if x['field']=='E' and x['port']==1]
        self.assertTrue(next(x for x in errors if x['frequency_ghz']==1.92)['passed'])
        self.assertFalse(next(x for x in errors if x['frequency_ghz']==3.55)['passed'])

    def test_zero_reference_requires_explicit_absolute_l2_gate(self):
        self.assertTrue(rf.vector_delta([0j],[5e-13])['passed'])
        x=rf.vector_delta([0j],[2e-12]);self.assertFalse(x['passed'])
        self.assertIsNone(x['relative_l2']);self.assertEqual(x['criterion'],'absolute_l2')

    def test_phase_wrap_uses_complex_vector_and_wrapped_diagnostic(self):
        a=complex(-1,1e-7);b=complex(-1,-1e-7)
        x=rf.vector_delta([a],[b]);self.assertTrue(x['passed'])
        self.assertLess(x['max_phase_error_rad'],1e-6)

    def test_complex_s_delta_fails_even_when_vswr_change_is_small(self):
        h,rows=self.b['tables']['port-S.csv']
        rows[0][h.index('|S[1][1]| (dB)')]=20*math.log10(.10002)
        x=self.compare();self.assertFalse(x['passed'])
        p=x['scattering'][0];self.assertGreater(p['max_delta_complex_S'],1e-5)
        self.assertLess(p['delta_vswr'],.001)

    def test_vswr_gate_detects_sensitive_high_reflection_despite_small_complex_delta(self):
        for run,value in ((self.a,.99),(self.b,.9900001)):
            header,rows=run['tables']['port-S.csv']
            rows[0][header.index('|S[1][1]| (dB)')]=20*math.log10(value)
        row=self.compare()['scattering'][0]
        self.assertLess(row['max_delta_complex_S'],1e-5)
        self.assertGreater(row['delta_vswr'],.001)
        self.assertFalse(row['passed'])

    def test_incomplete_or_nonfinite_stored_full_result_is_rejected(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as directory:
            root=Path(directory)
            (root/'config.json').write_text(json.dumps({'Problem':{'Output':'postpro'}}))
            (root/'plan.json').write_text(json.dumps({'source':directory}))
            good={'complete':True,'diagnostic_only':False,'solver_executed':True,'exit_code':0,
                  'full':{'max_raw_relative_rhs':8e-7}}
            for key,value in [('complete',False),('solver_executed',False),('exit_code',1),
                              ('full',{'max_raw_relative_rhs':float('nan')})]:
                result=copy.deepcopy(good);result[key]=value
                (root/'full-result.json').write_text(json.dumps(result))
                with self.subTest(key=key),self.assertRaisesRegex(ValueError,'full-result'):
                    rf.load_run(root)

    def test_farfield_extra_angles_not_integrated_but_all_are_compared(self):
        fields=rf.farfields(self.a)
        item=fields[1.92,1];vectors=[item['values'][i:i+3] for i in range(0,len(item['values']),3)]
        first=rf.sphere_power(item['angles'],vectors,6)['power_w']
        vectors[-1]=[1e9,0j,0j]
        self.assertEqual(first,rf.sphere_power(item['angles'],vectors,6)['power_w'])
        self.b['tables']['farfield-rE.csv'][1][6][4]=1e9
        x=self.compare();self.assertFalse(next(v for v in x['farfield_complex'] if v['port']==1)['passed'])

    def test_power_gate_includes_loss_and_rejects_bad_flux(self):
        self.b['tables']['surface-F.csv'][1][0][1]+=.03
        result=self.compare();self.assertFalse(result['passed'])
        self.assertFalse(result['power_balance']['candidate']['passed'])

    def test_unaccounted_conductor_loss_is_not_qualified_by_dielectric_formula(self):
        self.b['config']['Domains']['Materials'][0]['Conductivity']=1.
        gates=rf.power_gates(self.b,rf.scattering(self.b['tables']['port-S.csv']))
        self.assertFalse(gates['passed']);self.assertEqual(gates['status'],'NOT_RUN')

    def test_auxiliary_csv_values_cannot_change_silently(self):
        self.b['tables']['domain-E.csv'][1][0][1]*=1.001
        report=self.compare();self.assertFalse(report['passed'])
        row=next(x for x in report['auxiliary_numeric_csv'] if x['file']=='domain-E.csv')
        self.assertFalse(row['passed']);self.assertEqual(len(row['failed_columns']),1)

    def test_units_not_proved_means_not_run_never_fitted_to_flux(self):
        self.b['source_proof']={'passed':False,'error':'changed units'}
        result=self.compare();self.assertFalse(result['passed'])
        self.assertEqual(result['power_balance']['candidate']['status'],'NOT_RUN')
        self.assertTrue(all(x['status']=='NOT_RUN' for x in result['farfield_complex']))
        self.assertEqual(next(x for x in result['farfield_to_flux'] if x['run']=='candidate')['status'],'NOT_RUN')

    def test_changed_config_mesh_build_environment_are_rejected(self):
        for area,key,value in [('config','new',1),('fingerprint','mesh_sha256','different'),
                               ('plan','build','different')]:
            old=copy.deepcopy(self.b);self.b[area][key]=value
            with self.subTest(area=area,key=key),self.assertRaises(ValueError):self.compare()
            self.b=old
        self.b['plan']['environment']['uncontrolled']='1'
        with self.assertRaisesRegex(ValueError,'environment'):self.compare()

    def test_missing_probe_and_mismatched_angular_grid_are_rejected(self):
        self.b['tables']['probe-E.csv'][0][1]='unknown column'
        with self.assertRaises(ValueError):self.compare()
        self.b=copy.deepcopy(self.a)
        self.b['tables']['farfield-rE.csv'][1][0][2]=1.
        with self.assertRaisesRegex(ValueError,'angle grids'):self.compare()

    def test_csv_reader_rejects_nan_and_partial_records(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as d:
            path=Path(d)/'bad.csv'
            for text in ['f (GHz),x\n1.92,nan\n','f (GHz),x\n1.92\n','f (GHz),x\n']:
                path.write_text(text)
                with self.subTest(text=text),self.assertRaises(ValueError):rf.table(path)

    def test_recovered_controller_failure_is_declared_not_rewritten_as_clean_wall(self):
        self.a['fingerprint'].update(recovered_controller_failure=True,
                                     controller_result_complete=False,
                                     controller_wall_scope='Recovered controller failure')
        report=self.compare()
        self.assertTrue(report['passed'])
        self.assertTrue(report['recovered_controller_failure']['reference'])
        self.assertFalse(report['reference']['controller_result_complete'])
        self.assertIn('never a clean successful wall',report['timing_scope'])

    def test_forged_supplement_cannot_bypass_incomplete_full_result(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as directory:
            root=Path(directory)
            (root/'config.json').write_text(json.dumps({'Problem':{'Output':'postpro'}}))
            (root/'plan.json').write_text(json.dumps({'source':directory}))
            (root/'full-result.json').write_text(json.dumps({'complete':False}))
            (root/'completion-recovery.json').write_text(json.dumps({'complete':True}))
            with self.assertRaisesRegex(ValueError,'supplemental'):
                rf.load_run(root)

    def test_legacy_mode_is_labelled_diagnostic_not_timing_evidence(self):
        result=self.compare(legacy=True)
        self.assertTrue(result['passed']);self.assertTrue(result['legacy_reference'])
        self.assertIn('not same-build',result['scope'])

    def test_missing_or_tampered_frozen_source_cannot_establish_units(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as d:
            path=Path(d);self.assertFalse(rf.source_proof(path,path)['passed'])
            manifest={'source_sha256':rf.LEGACY_SOURCE,'files':{}}
            (path/'bundle-manifest.json').write_text(json.dumps(manifest))
            self.assertFalse(rf.source_proof(path,path)['passed'])


if __name__=='__main__':unittest.main()
