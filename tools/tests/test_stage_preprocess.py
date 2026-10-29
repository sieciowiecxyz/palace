import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('stage_preprocess',
                                             Path(__file__).parents[1] / 'stage_preprocess.py')
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


class PreprocessingPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir='/dev/shm')
        self.addCleanup(self.temporary.cleanup)
        self.run = Path(self.temporary.name)
        (self.run / 'mesh').mkdir()
        self.mesh = self.run / 'mesh/test.msh'
        # Only the header is inspected, deliberately not an MFEM correctness fixture.
        self.mesh.write_bytes(b'$MeshFormat\n2.2 0 8\n$EndMeshFormat\n')
        self.config = {'Model': {'Mesh': 'mesh/test.msh', 'L0': 0.001},
                       'Domains': {'Materials': [{'Attributes': [1], 'Permittivity': 2.94}]},
                       'Boundaries': {'LumpedPort': [{'Index': 1, 'Attributes': [21],
                                                       'Excitation': 1, 'R': 50}]},
                       'Solver': {'Order': 2, 'PartialAssemblyOrder': 1,
                                  'Linear': {'Tol': 1e-6, 'MaxIts': 1600, 'MaxSize': 64}}}
        self.write('config.json', self.config)
        self.command = {'actual_config_sha256': stage.sha(self.run / 'config.json'),
                        'runtime_image': 'image-digest'}
        self.write('command.json', self.command)
        self.fixture = {'mesh': 'mesh/test.msh', 'mesh_bytes': self.mesh.stat().st_size,
                        'mesh_sha256': stage.sha(self.mesh), 'config_sha256': 'before-run',
                        'medium': {'Order': 2, 'PartialAssemblyOrder': 1, 'Tol': 1e-6,
                                   'MaxIts': 1600, 'MaxSize': 240}}
        self.write('fixture.json', self.fixture)
        self.write('build-manifest.json', {'source_sha256': 'source-digest',
                                           'git_revision': 'revision',
                                           'native': {'palace-x86_64.bin': 'binary-digest'}})

    def write(self, name, value):
        (self.run / name).write_text(json.dumps(value))

    def test_keeps_actual_and_fixture_medium_and_does_not_claim_native_pass(self):
        report = stage.snapshot(self.run)
        self.assertEqual(report['actual_medium']['MaxSize'], 64)
        self.assertEqual(report['fixture_medium']['MaxSize'], 240)
        self.assertEqual(report['boundaries'], self.config['Boundaries'])
        self.assertEqual(report['native_preprocessing'], 'NOT RUN')
        self.assertIsNone(report['current_source_matches_runtime'])

    def test_rejects_unrecorded_config_change(self):
        self.config['Model']['L0'] = 1.0
        self.write('config.json', self.config)
        with self.assertRaisesRegex(ValueError, 'config bytes'):
            stage.snapshot(self.run)

    def test_rejects_same_size_mesh_drift(self):
        self.mesh.write_bytes(self.mesh.read_bytes().replace(b'2.2', b'2.1'))
        with self.assertRaisesRegex(ValueError, 'mesh_sha256'):
            stage.snapshot(self.run)

    def test_rejects_size_and_format_drift(self):
        self.mesh.write_bytes(b'not a mesh')
        with self.assertRaisesRegex(ValueError, 'byte count'):
            stage.snapshot(self.run)
        self.fixture.update(mesh_bytes=self.mesh.stat().st_size,
                            mesh_sha256=stage.sha(self.mesh))
        self.write('fixture.json', self.fixture)
        with self.assertRaisesRegex(ValueError, 'Gmsh 2.2'):
            stage.snapshot(self.run)

    def test_rejects_changed_mesh_path_even_with_updated_config_hash(self):
        self.config['Model']['Mesh'] = 'mesh/other.msh'
        self.write('config.json', self.config)
        self.command['actual_config_sha256'] = stage.sha(self.run / 'config.json')
        self.write('command.json', self.command)
        with self.assertRaisesRegex(ValueError, 'mesh path differs'):
            stage.snapshot(self.run)

    def test_rejects_staging_escape(self):
        self.config['Model']['Mesh'] = '../outside.msh'
        self.write('config.json', self.config)
        self.command['actual_config_sha256'] = stage.sha(self.run / 'config.json')
        self.write('command.json', self.command)
        with self.assertRaisesRegex(ValueError, 'staged relative'):
            stage.snapshot(self.run)


class DiagnosticOutputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir='/dev/shm')
        self.addCleanup(self.temporary.cleanup)
        self.run = Path(self.temporary.name)
        self.postpro = self.run / 'postpro'
        self.postpro.mkdir()
        self.report = {'schema': 1, 'stage': 'preprocess', 'mpi_ranks': 1,
                       'diagnostic_only': True, 'complete': True,
                       'solve_executed': False, 'rf_result': False,
                       'mesh_levels': [{'elements': 1}]}
        self.counts = {key: 0 for key in ['LinearSolve', 'EigenvalueSolve',
                       'Preconditioner', 'CoarseSolve', 'TimeStepping', 'FarFields',
                       'OperatorConstruction', 'Setup']}
        self.counts.update(Initialization=2, MeshPreprocessing=2)
        self.log = self.run / 'palace.stdout.log'
        self.log.write_text('PALACE_STAGE_DIAGNOSTIC: stage=preprocess complete=1 '
                            'solve_executed=0 rf_result=0\n')
        self.write()

    def write(self):
        (self.postpro / 'stage-diagnostic.json').write_text(json.dumps(self.report))
        (self.postpro / 'palace.json').write_text(
            json.dumps({'ElapsedTime': {'Counts': self.counts}}))

    def test_accepts_only_diagnostic_scope(self):
        report = stage.check_diagnostic(self.postpro, self.log)
        self.assertTrue(report['complete'])
        self.assertFalse(report['rf_result'])
        self.assertFalse(report['solve_executed'])

    def test_rejects_missing_final_marker_and_stale_rf_results(self):
        (self.postpro / 'port-S.csv').write_text('stale physical result')
        with self.assertRaisesRegex(ValueError, 'physical CSV'):
            stage.check_diagnostic(self.postpro, self.log)
        (self.postpro / 'port-S.csv').unlink()
        self.log.write_text('interrupted before final marker\n')
        with self.assertRaisesRegex(ValueError, 'completion marker'):
            stage.check_diagnostic(self.postpro, self.log)

    def test_rejects_solve_phase_even_with_diagnostic_label(self):
        self.counts['LinearSolve'] = 1
        self.write()
        with self.assertRaisesRegex(ValueError, 'unexpected solve'):
            stage.check_diagnostic(self.postpro, self.log)

    def operators_output(self):
        self.report['stage'] = 'operators'
        self.counts['OperatorConstruction'] = 1
        self.log.write_text('PALACE_STAGE_DIAGNOSTIC: stage=operators complete=1 '
                            'solve_executed=0 rf_result=0\n')
        self.write()

    def test_operators_accepts_header_only_csv_and_blank_records(self):
        self.operators_output()
        (self.postpro / 'port-S.csv').write_text(
            '        f (GHz), |S[1][1]| (dB), arg(S[1][1]) (deg.)\n\n  , ,  \n')
        (self.postpro / 'domain-E.csv').write_text('')
        report = stage.check_diagnostic(self.postpro, self.log, stage='operators')
        self.assertTrue(report['complete'])
        self.assertFalse(report['rf_result'])

    def test_operators_rejects_data_records_including_null_rows(self):
        self.operators_output()
        output = self.postpro / 'port-S.csv'
        for row in ['1.92,-20,+10', 'NULL,NULL,NULL']:
            with self.subTest(row=row):
                output.write_text('f (GHz),|S[1][1]| (dB),phase\n' + row + '\n')
                with self.assertRaisesRegex(ValueError, 'physical data records'):
                    stage.check_diagnostic(self.postpro, self.log, stage='operators')

    def test_operators_rejects_headerless_data(self):
        self.operators_output()
        (self.postpro / 'port-S.csv').write_text('1.92,-20,+10\n')
        with self.assertRaisesRegex(ValueError, 'recognized frequency header'):
            stage.check_diagnostic(self.postpro, self.log, stage='operators')

    def test_rejects_invalid_status_and_wrong_stage(self):
        self.report['solve_executed'] = 0  # Must be the JSON boolean, not a number.
        self.write()
        with self.assertRaisesRegex(ValueError, 'diagnostic status'):
            stage.check_diagnostic(self.postpro, self.log)
        self.report['solve_executed'] = False
        self.report['stage'] = 'operators'
        self.write()
        with self.assertRaisesRegex(ValueError, 'identity'):
            stage.check_diagnostic(self.postpro, self.log)


if __name__ == '__main__':
    unittest.main()
