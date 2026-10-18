import importlib.util
import json
import struct
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('palace_dev', Path(__file__).parents[1] / 'dev.py')
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


class ToolRegressionTests(unittest.TestCase):
    def test_complex_coarse_preserves_operator_and_explicitly_disables_shift(self):
        _, info, config = dev.fixture('coax-tiny')
        original = json.loads(json.dumps(config))
        updated = dev.diagnostic_config('coax-tiny', config, complex_coarse=True)
        self.assertTrue(updated['Solver']['Linear']['ComplexCoarseSolve'])
        self.assertFalse(updated['Solver']['Linear']['PCMatShifted'])
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        self.assertEqual(dev.field_identity(updated, info, build), dev.field_identity(original, info, build))
        with patch.object(dev, 'verified_build', side_effect=AssertionError('must not start')):
            with self.assertRaises(ValueError):
                dev.run('coax-tiny', '/unused', 60, basis='fp64', cpu_reference=True, complex_coarse=True)

    def test_cpu_reference_requires_real_host_device_backend_and_one_execute_marker(self):
        log = ('Device configuration: omp,cpu\nlibCEED backend: /cpu/self/avx/blocked\n'
               'CUDSS_HYBRID_EXECUTE: enabled=1\nPALACE_CUDSS_SERIAL_RHS: enabled=1\n')
        self.assertTrue(dev.cpu_reference_applied(log))
        self.assertFalse(dev.cpu_reference_applied(log.replace('omp,cpu', 'cuda,omp,cpu')))
        self.assertFalse(dev.cpu_reference_applied(log.replace('/cpu/self/avx/blocked', '/gpu/cuda/magma')))
        self.assertFalse(dev.cpu_reference_applied(log.replace('enabled=1', 'enabled=0')))
        self.assertFalse(dev.cpu_reference_applied(log.replace('PALACE_CUDSS_SERIAL_RHS: enabled=1\n', '')))
        self.assertFalse(dev.cpu_reference_applied(log + log))

    def test_cpu_reference_is_explicit_same_physics_and_rejects_other_precision(self):
        _, info, config = dev.fixture('coax-tiny')
        original = json.loads(json.dumps(config))
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        updated = dev.diagnostic_config('coax-tiny', config, cpu_reference=True)
        self.assertEqual(updated['Solver']['Device'], 'CPU')
        self.assertEqual(updated['Solver']['Backend'], '/cpu/self')
        self.assertEqual(dev.field_identity(updated, info, build), dev.field_identity(original, info, build))
        with patch.object(dev, 'verified_build', side_effect=AssertionError('must not start')):
            with self.assertRaisesRegex(ValueError, 'requires FP64'):
                dev.run('coax-tiny', '/unused', 60, cpu_reference=True)
            with self.assertRaisesRegex(ValueError, 'without GPU'):
                dev.run('coax-tiny', '/unused', 60, basis='fp64', cpu_reference=True, ceed_qpool=True)

    def test_explicit_restart_controls_preserve_physics_and_require_field_coverage(self):
        _, info, config = dev.fixture('coax-tiny')
        original = json.loads(json.dumps(config))
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        for size in [0, 241, True, 3.5]:
            with self.assertRaisesRegex(ValueError, '1..240'):
                dev.diagnostic_config('coax-tiny', config, krylov_size=size)
        updated = dev.diagnostic_config('coax-tiny', config, pc_side='right',
                                        krylov_size=64, initial_fields=True)
        self.assertEqual(updated['Solver']['Linear']['MaxSize'], 64)
        self.assertTrue(updated['Solver']['Linear']['InitialGuess'])
        self.assertEqual(updated['Solver']['Linear']['PCSide'], 'Right')
        self.assertEqual(updated['Solver']['Linear']['Tol'], original['Solver']['Linear']['Tol'])
        self.assertEqual(dev.field_identity(updated, info, build), dev.field_identity(original, info, build))
        log = ''.join(f'PALACE_FIELD_RESTART: excitation={s} frequency_index={f} norm_E=1.0e-2\n'
                      for s in [1, 2] for f in range(3))
        self.assertTrue(dev.field_restart_applied(log, config))
        self.assertFalse(dev.field_restart_applied(log + log, config))
        self.assertFalse(dev.field_restart_applied(log.replace('excitation=2', 'excitation=3'), config))
        self.assertFalse(dev.field_restart_applied(log.replace('norm_E=1.0e-2', 'norm_E=NaN', 1), config))

    def test_reference_tolerance_cannot_weaken_fixture_or_use_nonfinite_values(self):
        _, _, config = dev.fixture('coax-tiny')
        for value in [True, 0, 1e-15, 1e-5, float('nan'), float('inf'), '1e-12']:
            with self.assertRaisesRegex(ValueError, 'no weaker'):
                dev.diagnostic_config('coax-tiny', config, linear_tol=value)
        original = json.loads(json.dumps(config))
        changed = dev.diagnostic_config('coax-tiny', config, linear_tol=1e-12)
        original['Solver']['Linear']['Tol'] = 1e-12
        self.assertEqual(changed, original)

    def test_separate_capture_preserves_partial_stdout_diagnostic(self):
        # A delayed stdout suffix must not be split by an intervening stderr line.
        script = ('import os; '
                  'os.write(1, b"PALACE_KSP_CHECK: absolute="); '
                  'os.write(2, b"PALACE_MEMORY_PHASE {}\\n"); '
                  'os.write(1, b"1e-7 relative_initial=1e-7 threshold=1e-6\\n")')
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            with (work/'palace.stdout.log').open('wb') as stdout, \
                 (work/'palace.stderr.log').open('wb') as stderr:
                dev.command([dev.sys.executable, '-c', script], stdout=stdout, stderr=stderr)
            dev.combine_run_logs(work)
            text = (work/'palace.log').read_text()
            self.assertIn('PALACE_KSP_CHECK: absolute=1e-7 relative_initial=1e-7 threshold=1e-6\n', text)
            self.assertIn('PALACE_MEMORY_PHASE {}\n', text)
            self.assertIn('not global event order', text)
            self.assertNotIn('PALACE_MEMORY_PHASE', (work/'palace.stdout.log').read_text())

    def test_memory_phases_require_coverage_order_and_sensible_peaks(self):
        labels = ['setup.begin', 'setup.end', 'operators.begin', 'preconditioner.begin',
                  'preconditioner.end', 'gmres.begin', 'gmres.basis_release.begin',
                  'gmres.basis_release.end', 'gmres.end', 'postprocess.begin',
                  'field_diagnostics.begin', 'field_diagnostics.end', 'postprocess.end', 'driven.end']
        events = []
        previous = 'unmarked'
        for i, label in enumerate(labels):
            events.append(dict(to=label, **{'from': previous}, t_s=i, elapsed_s=1,
                               managed_live_bytes=10, managed_interval_peak_bytes=20,
                               managed_process_peak_bytes=30, cudss_live_bytes=5))
            previous = label
        def log(items):
            return '\n'.join('interleaved stdout PALACE_MEMORY_PHASE ' + json.dumps(e) for e in items)
        self.assertTrue(dev.memory_phase_report(log(events), 1, fields=True, release=True)['complete'])
        self.assertFalse(dev.memory_phase_report(log(events), 1, release_final=True)['complete'])
        self.assertFalse(dev.memory_phase_report(log(events[:-1]), 1, fields=True, release=True)['complete'])
        self.assertFalse(dev.memory_phase_report(log(events), 2, fields=True, release=True)['complete'])
        broken = json.loads(json.dumps(events))
        broken[5]['managed_live_bytes'] = 100
        self.assertFalse(dev.memory_phase_report(log(broken), 1, fields=True, release=True)['complete'])
        broken = json.loads(json.dumps(events))
        broken[5]['from'] = 'wrong phase'
        self.assertFalse(dev.memory_phase_report(log(broken), 1, fields=True, release=True)['complete'])

    def test_final_workspace_phase_is_required_exactly_once(self):
        labels = ['setup.begin', 'setup.end', 'operators.begin']
        solve = ['preconditioner.begin', 'preconditioner.end', 'gmres.begin', 'gmres.end']
        post = ['postprocess.begin', 'postprocess.end']
        labels += solve + post + solve + ['linear_workspace_release.begin',
                                         'linear_workspace_release.end'] + post + ['driven.end']
        def report(names):
            previous = 'unmarked'
            events = []
            for i, label in enumerate(names):
                events.append('PALACE_MEMORY_PHASE ' + json.dumps(dict(
                    to=label, **{'from': previous}, t_s=i, elapsed_s=1,
                    managed_live_bytes=10, managed_interval_peak_bytes=20,
                    managed_process_peak_bytes=30, cudss_live_bytes=5)))
                previous = label
            return dev.memory_phase_report('\n'.join(events), 2, release_final=True)
        self.assertTrue(report(labels)['complete'])
        self.assertFalse(report(labels[:-1])['complete'])
        doubled = labels[:-1] + ['linear_workspace_release.begin',
                                 'linear_workspace_release.end', 'driven.end']
        self.assertFalse(report(doubled)['complete'])

    def test_process_gpu_memory_uses_only_own_pid_and_real_units(self):
        query = type('Query', (), dict(returncode=0, stdout='9, 4000\n42, 256\n'))()
        with patch.object(dev.subprocess, 'run', return_value=query):
            self.assertEqual(dev.process_gpu_memory(42), 256*1024**2)
            self.assertIsNone(dev.process_gpu_memory(7))
            self.assertIsNone(dev.process_gpu_memory(0))
        query.stdout = '42, [N/A]\n'
        with patch.object(dev.subprocess, 'run', return_value=query):
            self.assertIsNone(dev.process_gpu_memory(42))
        with patch.object(dev.subprocess, 'run', side_effect=dev.subprocess.TimeoutExpired('nvidia-smi', 5)):
            self.assertIsNone(dev.process_gpu_memory(42))

    def test_qpool_generator_rejects_unpinned_source(self):
        spec = importlib.util.spec_from_file_location('qpool', Path(__file__).parents[1]/'experiments/ceed_qpool.py')
        qpool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qpool)
        with self.assertRaisesRegex(ValueError, 'Pinned libCEED source changed'):
            qpool.generate('unverified upstream source')

    def test_invalid_hypre_pool_is_rejected_before_gpu(self):
        with patch.object(dev, 'require_host_memory', side_effect=AssertionError('must not start')):
            for size in [0, 15, 4097, -1, '256', True]:
                with self.assertRaisesRegex(ValueError, '16 to 4096'):
                    dev.run('coax-tiny', '/unused', 60, hypre_pool_mib=size)

    def test_low_host_memory_refuses_gpu_before_build(self):
        with patch.object(dev, 'available_memory', return_value=5*1024**3), \
             patch.object(dev, 'verified_build', side_effect=AssertionError('must not start')):
            with self.assertRaisesRegex(ValueError, 'GPU run not started'):
                dev.run('coax-tiny', '/unused', 60)
        with patch.object(dev, 'available_memory', return_value=6*1024**3):
            self.assertEqual(dev.require_host_memory(), 6*1024**3)

    def test_qpool_manifest_rejects_wrong_inputs_or_library(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root/'build/ceed-qpool'
            directory.mkdir(parents=True)
            (root/'tools/experiments').mkdir(parents=True)
            recipe = root/'tools/experiments/ceed_qpool.py'
            recipe.write_text('recipe')
            library = directory/'libceed_qpool.so'
            library.write_bytes(b'prototype')
            native = dict(builder_image_id='builder', runtime_base_id='runtime')
            metadata = dict(recipe={recipe.name: dev.sha(recipe)}, builder='builder', runtime='runtime',
                            library_sha256=dev.sha(library), runtime_library_path='/opt/software/libceed/lib/libceed.so')
            dev.write(directory/'manifest.json', metadata)
            with patch.object(dev, 'ROOT', root):
                self.assertEqual(dev.verified_qpool(native), (directory, metadata))
                library.write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'stale/tampered'):
                    dev.verified_qpool(native)
                library.write_bytes(b'prototype')
                recipe.write_text('changed')
                with self.assertRaisesRegex(ValueError, 'stale/tampered'):
                    dev.verified_qpool(native)
                recipe.write_text('recipe')
                with self.assertRaisesRegex(ValueError, 'stale/tampered'):
                    dev.verified_qpool(dict(builder_image_id='wrong', runtime_base_id='runtime'))
                dev.write(directory/'manifest.json', {**metadata, 'runtime_library_path': '/unexpected/libceed.so'})
                with self.assertRaisesRegex(ValueError, 'Unexpected'):
                    dev.verified_qpool(native)

    def test_disk_basis_is_rejected_before_build_or_gpu(self):
        with patch.object(dev, 'verified_build', side_effect=AssertionError('must not start')):
            for basis in ['fp32-disk', 'fp64-disk']:
                with self.assertRaisesRegex(ValueError, 'RAM/VRAM'):
                    dev.run('coax-tiny', '/unused', 60, basis=basis)

    def test_cgroup_memory_samples_and_disappearance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(dev.cgroup_memory(root), {})
            (root/'memory.current').write_text('1024\n')
            (root/'memory.peak').write_text('4096\n')
            (root/'memory.stat').write_text('anon 512\nfile 256\nshmem 128\nother 10\n')
            self.assertEqual(dev.cgroup_memory(root), {'current_bytes': 1024, 'peak_bytes': 4096,
                                                     'anon_bytes': 512, 'file_bytes': 256, 'shmem_bytes': 128})
            (root/'memory.current').write_text('invalid')
            self.assertEqual(dev.cgroup_memory(root), {})
        self.assertEqual(dev.cgroup_memory(None), {})

    def test_field_reference_rejects_wrong_physics_corruption_and_unfinished_run(self):
        _, info, config = dev.fixture('coax-tiny')
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'fields').mkdir()
            for name in dev.expected_field_files(config):
                (root/'fields'/name).write_bytes(struct.pack('<8sQdd', b'PALF64V1', 1, 1.0, 0.0))
            for name, value in [('config.json', config), ('fixture.json', info),
                                ('build-manifest.json', build), ('result.json', {'complete': True})]:
                dev.write(root/name, value)
            dev.write(root/'command.json', {'actual_config_sha256': dev.sha(root/'config.json')})
            dev.write(root/'fields.json', {'identity': dev.field_identity(config, info, build),
                                          'complete': True,
                                          'files': dev.field_inventory(root/'fields', dev.expected_field_files(config))})
            dev.verified_field_reference(root, config, info, build)
            changed = json.loads(json.dumps(config))
            changed['Domains']['Materials'][0]['Permittivity'] = 4.4
            with self.assertRaisesRegex(ValueError, 'different physics'):
                dev.verified_field_reference(root, changed, info, build)
            dev.write(root/'result.json', {'complete': False})
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                dev.verified_field_reference(root, config, info, build)
            dev.write(root/'result.json', {'complete': True, 'field_accuracy_passed': False})
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                dev.verified_field_reference(root, config, info, build)
            dev.write(root/'result.json', {'complete': True})
            path = root/'fields'/sorted(dev.expected_field_files(config))[0]
            path.write_bytes(struct.pack('<8sQdd', b'PALF64V1', 1, 2.0, 0.0))
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                dev.verified_field_reference(root, config, info, build)

    def test_field_comparison_requires_all_solves_regions_and_finite_errors(self):
        _, _, config = dev.fixture('coax-tiny')
        config = dev.diagnostic_config('coax-tiny', config, True)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def log(values):
                (root/'palace.log').write_text(''.join(
                    f'PALACE_FIELD_COMPARE: excitation={p} frequency_index=0 region=-1 '
                    f'relative_E={v} relative_B={v}\n' for p,v in values))
            log([(1, '1e-5'), (2, '1e-5')])
            self.assertTrue(dev.field_comparisons(root, config)['passed'])
            for values in [[(1, '1e-5')], [(1, 'nan'), (2, '0')], [(1, '0.02'), (2, '0')],
                           [(1, '-0.01'), (2, '0')], [(1, '0'), (1, '0'), (2, '0')]]:
                log(values)
                self.assertFalse(dev.field_comparisons(root, config)['passed'])

    def test_tiny_diagnostic_keeps_medium_and_scales_probe_positions(self):
        _, _, config = dev.fixture('coax-tiny')
        linear = config['Solver']['Linear'].copy()
        derived = dev.diagnostic_config('coax-tiny', config, True, 'right')
        self.assertEqual(derived['Solver']['Linear'], {**linear, 'PCSide': 'Right'})
        self.assertEqual(derived['Solver']['Driven']['Samples'], [{'Type': 'Point', 'Freq': [3.55]}])
        probes = derived['Domains']['Postprocessing']['Probe']
        self.assertEqual(len(probes), 18)
        self.assertEqual(sorted(set(p['Center'][2] for p in probes)), [0.5, 1.0, 1.5])
        with self.assertRaisesRegex(ValueError, 'coax fixture'):
            dev.diagnostic_config('tshaped-medium', {}, True)

    def test_real_archives_and_medium_contract(self):
        for name in dev.CASES:
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
