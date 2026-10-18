import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('palace_dev', Path(__file__).parents[1] / 'dev.py')
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


class ToolRegressionTests(unittest.TestCase):
    def test_real_archives_and_medium_contract(self):
        for name in ['coax-medium', 'tshaped-medium']:
            directory, info, config = dev.fixture(name)
            self.assertEqual(config['Model']['Mesh'], info['mesh'])
            self.assertTrue(all((directory / part).stat().st_size < 100_000_000 for part in info['archive_parts']))

    def test_changed_archive_and_escaping_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / 'examples/test'
            directory.mkdir(parents=True)
            (directory / 'mesh.zst').write_bytes(b'corrupted')
            dev.write(directory / 'fixture.json', {'mesh': 'mesh.msh', 'archive_parts': ['mesh.zst'], 'archive_sha256': 'bad'})
            with patch.object(dev, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Corrupt'):
                    dev.fixture('test')
                dev.write(directory / 'fixture.json', {'mesh': '../../escape', 'archive_parts': ['mesh.zst']})
                with self.assertRaisesRegex(ValueError, 'escapes'):
                    dev.fixture('test')

    def test_stale_or_tampered_binary_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build = root / 'build'
            (build / 'native').mkdir(parents=True)
            binary = build / 'native/palace.bin'
            binary.write_bytes(b'reference')
            settings = root / 'settings.json'
            settings.write_text('{}')
            dev.write(build / 'manifest.json', {'source_sha256': 'source', 'settings_sha256': dev.sha(settings),
                                              'native': {'palace.bin': dev.sha(binary)}})
            with patch.object(dev, 'BUILD', build), patch.object(dev, 'SETTINGS', settings), patch.object(dev, 'source_hash', return_value='source'):
                dev.verified_build()
                binary.write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'binary changed'):
                    dev.verified_build()
            with patch.object(dev, 'BUILD', build), patch.object(dev, 'SETTINGS', settings), patch.object(dev, 'source_hash', return_value='new source'):
                with self.assertRaisesRegex(ValueError, 'Sources/settings changed'):
                    dev.verified_build()

    def test_new_source_file_invalidates_fingerprint_but_docs_do_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'palace').mkdir()
            (root / 'CMakeLists.txt').write_text('project(example)')
            with patch.object(dev, 'ROOT', root):
                first = dev.source_hash()
                (root / 'README.md').write_text('docs')
                self.assertEqual(dev.source_hash(), first)
                (root / 'palace/new.cpp').write_text('int main() {}')
                self.assertNotEqual(dev.source_hash(), first)

    def test_incomplete_frequency_coverage_or_missing_solve_is_not_success(self):
        config = {'Problem': {'Output': 'postpro'}, 'Solver': {'Driven': {'Samples': [{'Freq': [3.3, 3.8]}]}},
                  'Boundaries': {'LumpedPort': [{'Excitation': True}]}}
        # Exact writer prefix from palace/linalg/iterative.cpp; the missing colon
        # formerly made a completed real GPU run appear incomplete.
        good = 'GMRES solver converged in 10 iterations\nPALACE_KSP_CHECK: absolute=1e-7 relative_initial=1e-7 threshold=1e-6\n'
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'postpro').mkdir()
            (work / 'palace.log').write_text(good * 2)
            csv = work / 'postpro/port-S.csv'
            csv.write_text(' f (GHz), |S[1][1]| (dB)\n3.3,-20\n3.8,-20\n')
            self.assertTrue(dev.validate_output(work, config, 0)['complete'])
            self.assertFalse(dev.validate_output(work, config, 143)['complete'])
            (work / 'palace.log').write_text(good)
            self.assertFalse(dev.validate_output(work, config, 0)['complete'])
            (work / 'palace.log').write_text(good * 2)
            csv.write_text(' f (GHz), |S[1][1]| (dB)\n3.3,-20\n')
            self.assertFalse(dev.validate_output(work, config, 0)['complete'])

    def test_failed_independent_stopping_check_is_not_success(self):
        config = {'Problem': {'Output': 'postpro'}, 'Solver': {'Driven': {'Samples': [{'Freq': [3.5]}]}},
                  'Boundaries': {'LumpedPort': [{'Excitation': True}]}}
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'postpro').mkdir()
            (work / 'postpro/port-S.csv').write_text('f (GHz)\n3.5\n')
            (work / 'palace.log').write_text('GMRES solver converged in 10 iterations\nPALACE_KSP_CHECK: absolute=2.0 relative_initial=0.2 threshold=1e-6\n')
            self.assertFalse(dev.validate_output(work, config, 0)['complete'])


if __name__ == '__main__':
    unittest.main()
