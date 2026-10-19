import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1]/'experiments/bempp_oracle.py'
SPEC = importlib.util.spec_from_file_location('bempp_oracle',SCRIPT)
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


class PythonMountTests(unittest.TestCase):
    def test_stream_probe_rejects_unused_or_unbounded_control_flags(self):
        with patch.object(oracle.dev,'require_host_memory') as host:
            for options in [dict(physics='nd2',stream_variant='near6'),
                            dict(physics='stream-control',volume_inputs=['a','b'],near_count=0),
                            dict(physics='stream-control',volume_inputs=['a','b'],stream_variant='far16'),
                            dict(physics='stream-volume',volume_inputs=['a','b'],stream_variant='bad')]:
                with self.assertRaises(ValueError):oracle.run(Path('/unused'),2,120,**options)
            host.assert_not_called()

    def test_analytic_dielectric_epsilon_keeps_case_defaults_and_rejects_invalid(self):
        self.assertEqual(oracle.case_epsilon('nd2',None),1.)
        self.assertEqual(oracle.case_epsilon('transmission',None),2.94)
        self.assertIsNone(oracle.case_epsilon('pec',None))
        self.assertEqual(oracle.case_epsilon('nd2',2.94),2.94)
        for physics,epsilon in [('nd2',-1.),('nd2',float('nan')),('pec',1.)]:
            with self.assertRaises(ValueError):oracle.case_epsilon(physics,epsilon)

    def test_fixed_replay_requires_probes_and_rejects_unused_flags_before_allocation(self):
        with patch.object(oracle.dev,'require_host_memory') as host:
            for options in [dict(physics='nd2',probe_input=Path('/unused')),
                            dict(physics='fem-replay',volume_inputs=['a','b']),
                            dict(physics='fem-replay',volume_inputs=['a','b'],probe_input=Path('/unused'),volume_degree=5)]:
                with self.assertRaises(ValueError):oracle.run(Path('/unused'),3,120,**options)
            host.assert_not_called()

    def test_uv_alias_is_mounted_at_configured_home(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base,env,alias = root/'python-3.12.15',root/'venv',root/'python-3.12'
            (base/'bin').mkdir(parents=True)
            (base/'bin/python3.12').touch()
            alias.symlink_to(base,target_is_directory=True)
            (env/'bin').mkdir(parents=True)
            (env/'bin/python').symlink_to(alias/'bin/python3.12')
            (env/'pyvenv.cfg').write_text(f'home = {alias}/bin\n')
            mounts = oracle.python_mounts(env,base)
            self.assertIn(f'{base}:{alias}:ro',mounts)
            self.assertIn(f'{base}:{base}:ro',mounts)
            self.assertEqual(len(mounts),6)
            (env/'pyvenv.cfg').write_text(f'home = {base}/bin\n')
            self.assertEqual(len(oracle.python_mounts(env,base)),4)

    def test_mismatched_base_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = root/'venv'
            env.mkdir()
            (env/'pyvenv.cfg').write_text(f'home = {root}/other/bin\n')
            with self.assertRaises(ValueError):
                oracle.python_mounts(env,root/'base')


class NativeManifestTests(unittest.TestCase):
    def test_near_backend_is_explicit_and_rejected_for_unrelated_cases(self):
        with patch.object(oracle.dev,'require_host_memory') as check:
            for physics,backend in [('pec','numba'),('volume','numba'),('near-control','invalid')]:
                with self.assertRaises(ValueError):oracle.run(Path('/unused'),1,120,physics=physics,near_backend=backend)
            check.assert_not_called()

    def test_near_control_stays_small_and_rejects_unused_input_flags(self):
        with patch.object(oracle.dev,'require_host_memory') as check:
            for level,options in [(2,{}),(1,dict(volume_inputs=['a','b'])),
                    (1,dict(volume_degree=5)),(1,dict(surface_level=2)),(1,dict(epsilon_r=2.94)),(1,dict(near_count=0)),(1,dict(near_side='coarse'))]:
                with self.assertRaises(ValueError):oracle.run(Path('/unused'),level,120,physics='near-control',**options)
            check.assert_not_called()
            for options in [dict(),dict(volume_degree=5)]:
                with self.assertRaises(ValueError):oracle.run(Path('/unused'),2,120,physics='near-correction',**options)
            check.assert_not_called()

    def test_volume_flags_are_rejected_before_host_allocation(self):
        with patch.object(oracle.dev,'require_host_memory') as check:
            for options in [dict(physics='volume'),dict(physics='volume',volume_degree=3),
                    dict(physics='pec',volume_inputs=['a','b']),dict(physics='pec',volume_degree=5)]:
                with self.assertRaises(ValueError):oracle.run(Path('/unused'),2,120,**options)
            check.assert_not_called()

    def test_volume_input_roles_completion_basis_and_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            paths=[root/'candidate',root/'reference']
            for role,path in zip(['candidate','reference'],paths):
                path.mkdir()
                case=dict(execution_passed=True,epsilon_r=2.94,level=2,surface_level=4)
                command=dict(physics='transmission',reference_only=role=='reference',mfem_bridge=dict(binary_sha256='h'),
                             **{key:'h' for key in ['fem_api_sha256','nd_api_sha256','pairing_api_sha256','coupling_api_sha256','reference_sha256','case_sha256']})
                for name,value in [('case.json',case),('command.json',command),
                        ('result.json',dict(complete=True,exit_code=0)),
                        ('container-state.json',dict(Running=False,OOMKilled=False,ExitCode=0))]:
                    oracle.dev.write(path/name,value)
                for name in (['coupled-solution.npz'] if role=='candidate' else ['pmchwt-level3.npz','pmchwt-level4.npz']):
                    (path/name).touch()
            with patch.object(oracle.dev,'sha',return_value='h'):
                checked=oracle.checked_volume_inputs(paths,2)
                self.assertEqual(checked['epsilon_r'],2.94)
                self.assertIn('coupled-solution.npz',checked['candidate']['sha256'])
                with self.assertRaises(ValueError):oracle.checked_volume_inputs(paths,3)
                state=paths[1]/'container-state.json'
                oracle.dev.write(state,dict(Running=True,OOMKilled=False,ExitCode=0))
                with self.assertRaises(ValueError):oracle.checked_volume_inputs(paths,2)
                oracle.dev.write(state,dict(Running=False,OOMKilled=True,ExitCode=0))
                with self.assertRaises(ValueError):oracle.checked_volume_inputs(paths,2)
                oracle.dev.write(state,dict(Running=False,OOMKilled=False,ExitCode=0))
                cmd=oracle.dev.read(paths[0]/'command.json');cmd['nd_api_sha256']='changed'
                oracle.dev.write(paths[0]/'command.json',cmd)
                with self.assertRaises(ValueError):oracle.checked_volume_inputs(paths,2)
                cmd['nd_api_sha256']='h';oracle.dev.write(paths[0]/'command.json',cmd)
                cmd['physics']='volume';cmd['transmission_api_sha256']='h'
                oracle.dev.write(paths[0]/'command.json',cmd)
                saved=oracle.dev.read(paths[0]/'case.json');saved['reference_surface_level']=4
                oracle.dev.write(paths[0]/'case.json',saved)
                (paths[0]/'volume-fields.npz').touch()
                checked=oracle.checked_volume_inputs(paths,2,candidate_physics='volume')
                self.assertIn('volume-fields.npz',checked['candidate']['sha256'])
                saved['reference_surface_level']=3;oracle.dev.write(paths[0]/'case.json',saved)
                with self.assertRaises(ValueError):oracle.checked_volume_inputs(paths,2,candidate_physics='volume')
                saved['reference_surface_level']=4;oracle.dev.write(paths[0]/'case.json',saved)
                cmd['physics']='transmission';oracle.dev.write(paths[0]/'command.json',cmd)
                (paths[1]/'pmchwt-level4.npz').unlink()
                with self.assertRaises(ValueError):oracle.checked_volume_inputs(paths,2)

    def test_transmission_options_rejected_before_host_allocation(self):
        with patch.object(oracle.dev,'require_host_memory') as check:
            for physics,level,surface,epsilon in [('pec',2,None,2.94),
                    ('transmission',1,None,1.),('transmission',2,1,2.94),
                    ('transmission',2,2,-1.),('transmission',2,2,float('nan'))]:
                with self.assertRaises(ValueError):
                    oracle.run(Path('/unused'),level,120,physics=physics,surface_level=surface,epsilon_r=epsilon)
            check.assert_not_called()
            for physics,epsilon in [('pec',1.),('transmission',None),('transmission',-1.)]:
                with self.assertRaises(ValueError):
                    oracle.run(Path('/unused'),2,120,physics=physics,epsilon_r=epsilon,reference_only=True)
            check.assert_not_called()
            with self.assertRaises(ValueError):
                oracle.run(Path('/unused'),2,120,physics='transmission',surface_level=4,epsilon_r=2.94)
            check.assert_not_called()

    def test_duality_option_rejected_before_running_an_unrelated_case(self):
        with patch.object(oracle.dev,'require_host_memory') as check:
            for physics in ['pec','traces','nd2']:
                with self.assertRaises(ValueError):
                    oracle.run(Path('/unused'),1,120,physics=physics,duality='magnetic')
            with self.assertRaises(ValueError):
                oracle.run(Path('/unused'),1,120,physics='nd2-coupling',duality='invalid')
            for physics,level,surface in [('pec',1,2),('nd2-coupling',2,1),('nd2-coupling',1,4)]:
                with self.assertRaises(ValueError):
                    oracle.run(Path('/unused'),level,120,physics=physics,surface_level=surface)
            check.assert_not_called()
    def test_mfem_cache_recipe_tracks_global_source_separately(self):
        bridge = oracle.mfem_bridge
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            local,global_source = root/'local.cpp',root/'global.cpp'
            local.write_text('local API')
            global_source.write_text('global API version1')
            settings = {'builder_image':'builder','runtime_image':'runtime'}
            with patch.object(bridge,'SOURCE',local),patch.object(bridge,'GLOBAL_SOURCE',global_source),\
                 patch.object(bridge.dev,'read',return_value=settings),\
                 patch.object(bridge.dev,'image_id',side_effect=lambda image:image):
                before = bridge.recipe()
                global_source.write_text('global API version2')
                after = bridge.recipe()
                self.assertEqual(before['source_sha256'],after['source_sha256'])
                self.assertNotEqual(before['global_source_sha256'],after['global_source_sha256'])

    def test_mfem_bridge_manifest_rejects_modified_binary(self):
        bridge = oracle.mfem_bridge
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = root/'mfem.so'
            library.write_bytes(b'MFEM bridge')
            recipe = {'source':'mfem-source','runtime':'pinned'}
            oracle.dev.write(root/'manifest.json',dict(recipe=recipe,binary_sha256=oracle.dev.sha(library)))
            with patch.object(bridge,'BASE',root),patch.object(bridge,'LIBRARY',library),\
                 patch.object(bridge,'recipe',return_value=recipe):
                self.assertEqual(bridge.verified()['recipe'],recipe)
                library.write_bytes(b'changed')
                with self.assertRaises(ValueError): bridge.verified()

    def test_native_binary_and_recipe_are_both_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = root/'native.so'
            library.write_bytes(b'cached binary')
            recipe = {'source':'revision-a'}
            oracle.dev.write(root/'manifest.json',dict(recipe=recipe,binary_sha256=oracle.dev.sha(library)))
            with patch.object(oracle,'CUDA_BUILD',root),patch.object(oracle,'CUDA_LIBRARY',library),\
                 patch.object(oracle,'cuda_recipe',return_value=recipe) as current:
                self.assertEqual(oracle.verified_cuda()['recipe'],recipe)
                current.return_value = {'source':'revision-b'}
                with self.assertRaises(ValueError): oracle.verified_cuda()
                current.return_value = recipe
                library.write_bytes(b'changed binary')
                with self.assertRaises(ValueError): oracle.verified_cuda()
