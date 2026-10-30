import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))
from stage_full_check import expectations, check_full


class FullCompletionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir='/dev/shm')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.out = self.root/'postpro'; self.out.mkdir()
        self.stdout = self.root/'stdout.log'; self.stderr = self.root/'stderr.log'
        self.stderr.write_text('')
        self.config = {'Problem': {'Type': 'Driven'},
                       'Solver': {'Driven': {'Samples': [{'Type': 'Point', 'Freq': [1.92]}]}},
                       'Boundaries': {'LumpedPort': [{'Index':1,'Excitation':1}, {'Index':2,'Excitation':2}]}}
        self.metadata = {'LinearSolver': {'TotalSolves':2,'TotalIts':85},
                         'Problem': {'MPISize':1,'OpenMPThreads':1,'MeshElements':50,'DegreesOfFreedom':454},
                         'ElapsedTime': {'Counts': {'Total':1,'LinearSolve':2}, 'Durations': {'Total':825.7}},
                         'Excitations': [[[1,{'LumpedPort':[1]}], [2,{'LumpedPort':[2]}]]]}
        self.save_metadata()
        for name, symbol, unit in [('port-S.csv','S',None), ('port-V.csv','V','V'), ('port-I.csv','I','A')]:
            header = ['f (GHz)']
            for source in (1,2):
                for port in (1,2):
                    label=f'{symbol}[{port}][{source}]'
                    header.extend([f'|{label}| (dB)',f'arg({label}) (deg.)'] if symbol=='S' else
                                  [f'Re{{{label}}} ({unit})',f'Im{{{label}}} ({unit})'])
            self.write_csv(name,header,[[1.92]+[.1]*(len(header)-1)])
        self.write_csv('domain-E.csv',['f (GHz)','E_elec[1] (J)','E_elec[2] (J)'],[[1.92,.1,.2]])
        self.write_csv('farfield-rE.csv',['f (GHz)','exc','theta (deg.)','phi (deg.)','r*Re{E_x} (V)'],
                       [[1.92,1,0,0,.2],[1.92,2,0,0,.3]])
        self.log='Device configuration: cuda,omp,cpu\nlibCEED backend: /gpu/cuda/magma\n'
        for source in (1,2):
            self.log+=(f'PALACE_PORT_SETUP: action=build excitation={source} frequency_index=0\n'
                       'It 1/1: ω/2π = 1.920e+00 GHz (total elapsed time = 1 s)\n'
                       'PALACE_RAW_RESIDUAL: pc_side=right raw=8e-6 rhs=10 ax=10 relative_rhs=8e-7 relative_action=4e-7\n'
                       'GMRES solver converged in 42 iterations (avg. reduction factor: 0.7)\n')
        self.stdout.write_text(self.log)
        self.expected=expectations(self.config,self.out)

    def write_csv(self,name,header,rows):
        with (self.out/name).open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(header);writer.writerows(rows)

    def save_metadata(self):
        (self.out/'palace.json').write_text(json.dumps(self.metadata))

    def check(self):
        return check_full(self.out,self.stdout,self.stderr,self.expected)

    def test_complete_is_not_rf_qualification_and_plan_roundtrip_is_canonical(self):
        self.assertEqual(self.expected,json.loads(json.dumps(self.expected)))
        result=self.check()
        self.assertTrue(result['complete']);self.assertTrue(result['solver_executed'])
        self.assertFalse(result['diagnostic_only']);self.assertFalse(result['rf_qualified'])
        self.assertEqual(result['total_solves'],2)
        self.assertEqual(result['max_raw_relative_rhs'],8e-7)

    def test_partial_solver_metadata_is_rejected(self):
        for key,value in [('TotalSolves',1),('TotalSolves',True),('TotalIts',0)]:
            with self.subTest(key=key,value=value):
                old=self.metadata['LinearSolver'][key];self.metadata['LinearSolver'][key]=value
                self.save_metadata()
                with self.assertRaises(ValueError):self.check()
                self.metadata['LinearSolver'][key]=old
        self.metadata.pop('ElapsedTime');self.save_metadata()
        with self.assertRaisesRegex(ValueError,'elapsed-time'):self.check()

    def test_missing_problem_metadata_and_wrong_port_contributions_are_rejected(self):
        problem=self.metadata.pop('Problem');self.save_metadata()
        with self.assertRaisesRegex(ValueError,'problem metadata'):self.check()
        self.metadata['Problem']=problem
        self.metadata['Excitations'][0][1][1]['LumpedPort']=[1]
        self.save_metadata()
        with self.assertRaisesRegex(ValueError,'Excitation metadata'):self.check()

    def test_missing_port_or_residual_proof_is_rejected(self):
        for log in [self.log.split('PALACE_PORT_SETUP: action=build excitation=2')[0],
                    self.log.replace('PALACE_RAW_RESIDUAL:', 'IGNORED_RESIDUAL:'),
                    self.log.replace('excitation=2','excitation=1')]:
            with self.subTest(log=log):
                self.stdout.write_text(log)
                with self.assertRaises(ValueError):self.check()

    def test_final_raw_relative_residual_must_be_finite_small_and_consistent(self):
        for replacements in [(('raw=8e-6','raw=2e-5'),('relative_rhs=8e-7','relative_rhs=2e-6')),
                             (('raw=8e-6','raw=nan'),),
                             (('relative_rhs=8e-7','relative_rhs=nan'),),
                             (('relative_rhs=8e-7','relative_rhs=1e-12'),)]:
            with self.subTest(replacements=replacements):
                log=self.log
                for old,new in replacements:log=log.replace(old,new)
                self.stdout.write_text(log)
                with self.assertRaises(ValueError):self.check()

    def test_reliable_restart_checks_final_raw_residual(self):
        intermediate='PALACE_RAW_RESIDUAL: pc_side=right raw=1 rhs=10 ax=10 relative_rhs=.1 relative_action=.05\n'
        self.stdout.write_text(self.log.replace('PALACE_RAW_RESIDUAL:',intermediate+'PALACE_RAW_RESIDUAL:'))
        self.assertTrue(self.check()['complete'])

    def test_frequency_and_excitation_metadata_must_match(self):
        self.stdout.write_text(self.log.replace('1.920e+00','2.600e+00'))
        with self.assertRaisesRegex(ValueError,'frequency'):self.check()
        self.stdout.write_text(self.log)
        self.metadata['Excitations']=[[[1,{}]]];self.save_metadata()
        with self.assertRaisesRegex(ValueError,'excitation'):self.check()

    def test_stage_stop_trace_or_diagnostic_output_is_rejected(self):
        for marker in ('PALACE_STAGE_DIAGNOSTIC:','PALACE_STAGE_STOP=operators','PALACE_STAGE_PROFILE '):
            self.stderr.write_text(marker)
            with self.subTest(marker=marker),self.assertRaisesRegex(ValueError,'diagnostic/stop/trace'):self.check()
        self.stderr.write_text('');(self.out/'stage-diagnostic.json').write_text('{}')
        with self.assertRaises(ValueError):self.check()

    def test_csv_missing_file_port_header_partial_row_frequency_and_nonfinite(self):
        path=self.out/'port-S.csv';original=path.read_text()
        path.unlink()
        with self.assertRaisesRegex(ValueError,'file set'):self.check()
        path.write_text(original.replace('|S[2][2]| (dB)','wrong'))
        with self.assertRaisesRegex(ValueError,'header'):self.check()
        path.write_text(original.replace('1.92','2.6'))
        with self.assertRaisesRegex(ValueError,'frequency'):self.check()
        path.write_text(original.replace('0.1','NULL',1))
        with self.assertRaises(ValueError):self.check()
        path.write_text(original.splitlines()[0]+'\n')
        with self.assertRaisesRegex(ValueError,'incomplete'):self.check()

    def test_long_form_csv_requires_every_source_and_no_duplicates(self):
        path=self.out/'farfield-rE.csv';lines=path.read_text().splitlines()
        path.write_text('\n'.join(lines[:2])+'\n')
        with self.assertRaisesRegex(ValueError,'incomplete'):self.check()
        path.write_text('\n'.join(lines+[lines[1]])+'\n')
        with self.assertRaisesRegex(ValueError,'incomplete'):self.check()

    def test_unsupported_sampling_and_reference_missing_port_are_rejected(self):
        self.config['Solver']['Driven']['Samples'][0]['Type']='Linear'
        with self.assertRaisesRegex(ValueError,'Point'):expectations(self.config,self.out)
        self.config['Solver']['Driven']['Samples'][0]['Type']='Point'
        p=self.out/'port-S.csv';p.write_text(p.read_text().replace('|S[2][2]| (dB)','wrong'))
        with self.assertRaisesRegex(ValueError,'port/source'):expectations(self.config,self.out)

    def test_cpu_or_missing_cuda_backend_is_rejected(self):
        for value in (self.log.replace('Device configuration: cuda,omp,cpu','Device configuration: cpu'),
                      self.log.replace('/gpu/cuda/magma','/cpu/self'),
                      self.log.replace('libCEED backend: /gpu/cuda/magma\n','')):
            self.stdout.write_text(value)
            with self.assertRaisesRegex(ValueError,'CUDA device/backend'):
                self.check()


if __name__=='__main__':unittest.main()
