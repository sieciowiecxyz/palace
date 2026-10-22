import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1]))
import dev
import package_bundle as bundle
spec=importlib.util.spec_from_file_location('package_lifecycle',Path(bundle.__file__).parent/'experiments/package_lifecycle.py')
lifecycle=importlib.util.module_from_spec(spec);spec.loader.exec_module(lifecycle)


class PackageTests(unittest.TestCase):
    def test_conmon_negative_timeout_code_needs_independent_matching_control(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);work=out/'deadline';work.mkdir()
            dev.write(work/'result.json',dict(complete=False,exit_code=255))
            dev.write(work/'command.json',dict(argv=['podman','create','--name','owned','--timeout','1'],runtime_image='image'))
            state=dict(StartedAt='2026-10-22T00:00:00+00:00',FinishedAt='2026-10-22T00:00:00.850000+00:00',ExitCode=-1,OOMKilled=False)
            dev.write(work/'container-state.json',state)
            witness=dict(argv=['podman','run','--timeout','1','--entrypoint','sleep','image','30'],podman_version='6.1.4',state=state,returncode=255,elapsed_seconds=1.95)
            process=Mock(pid=12345);process.wait.return_value=1
            for variation in [None,dict(podman_version='wrong'),dict(state=dict(state,OOMKilled=True)),dict(returncode=137),{}]:
                control=out/'control.json'
                if variation is not None:dev.write(control,dict(witness,**variation))
                with patch.object(lifecycle.subprocess,'Popen',return_value=process),patch.object(lifecycle.subprocess,'run',return_value=Mock(returncode=1)),patch.object(dev,'capture',return_value='6.1.4'):
                    if variation=={}:self.assertTrue(lifecycle.check(Path('/bundle'),out,'deadline',control)['passed'])
                    else:
                        with self.assertRaises(ValueError):lifecycle.check(Path('/bundle'),out,'deadline',control if variation is not None else None)

    def test_lifecycle_SIGTERM_uses_owned_live_process_and_needs_no_post_exit_state(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);work=out/'sigterm';work.mkdir()
            dev.write(work/'result.json',dict(complete=False,interrupted=True,interrupted_signal='SIGTERM'))
            dev.write(work/'command.json',dict(argv=['podman','create','--name','owned']))
            (work/'palace.stdout.log').write_text('PALACE_NATIVE_COMPLEX_COARSE: live\n')
            process=Mock(pid=12345);process.poll.return_value=None;process.wait.return_value=130
            with patch.object(lifecycle.subprocess,'Popen',return_value=process),patch.object(lifecycle.subprocess,'run',return_value=Mock(returncode=1)):
                r=lifecycle.check(Path('/bundle'),out,'sigterm')
            self.assertTrue(r['passed']);process.send_signal.assert_called_once_with(lifecycle.signal.SIGTERM)
            self.assertFalse((work/'container-state.json').exists())

    def test_lifecycle_deadline_requires_timeout_exit_duration_and_no_OOM(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);work=out/'deadline';work.mkdir()
            dev.write(work/'result.json',dict(complete=False))
            dev.write(work/'command.json',dict(argv=['podman','create','--name','owned','--timeout','1']))
            state=dict(StartedAt='2026-10-22T00:00:00+00:00',FinishedAt='2026-10-22T00:00:01.050000+00:00',ExitCode=137,OOMKilled=False)
            process=Mock(pid=12345);process.wait.return_value=1
            for bad in [False,True]:
                dev.write(work/'container-state.json',dict(state,OOMKilled=bad))
                with patch.object(lifecycle.subprocess,'Popen',return_value=process),patch.object(lifecycle.subprocess,'run',return_value=Mock(returncode=1)):
                    if bad:
                        with self.assertRaises(ValueError):lifecycle.check(Path('/bundle'),out,'deadline')
                    else:self.assertTrue(lifecycle.check(Path('/bundle'),out,'deadline')['passed'])

    def test_inventory_detects_changed_missing_escaping_and_symlink_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); build = root/'build/sm120/manifest.json'
            dev.write(build, {'source': 'test'}); (root/'input').write_text('bytes')
            m = dict(schema=1, files=bundle.inventory(root), build_manifest_sha256=dev.sha(build))
            dev.write(root/'bundle-manifest.json', m)
            self.assertEqual(bundle.verify(root), m)
            (root/'input').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'payload changed'): bundle.verify(root)
            (root/'input').unlink()
            with self.assertRaisesRegex(ValueError, 'payload changed'): bundle.verify(root)
            (root/'input').symlink_to(build)
            with self.assertRaisesRegex(ValueError, 'payload changed'): bundle.verify(root)
            (root/'input').unlink(); (root/'input').write_text('bytes')
            for change in [dict(files={}), dict(files={'../escape':'sha'}), dict(build_manifest_sha256='stale')]:
                dev.write(root/'bundle-manifest.json', dict(m, **change))
                with self.assertRaises(ValueError): bundle.verify(root)

    def test_image_gate_checks_actual_manifest_native_bytes_and_base_layers(self):
        m = dict(native={k: 'abc'+str(i) for i, k in enumerate(dev.NATIVE_PATHS)}, runtime_base_id='base')
        text = '\n'.join(f'{m["native"][k]}  {v}' for k,v in dev.NATIVE_PATHS.items())
        layers = [{'RootFS': {'Layers': ['base1', 'base2']}}]
        child = [{'RootFS': {'Layers': ['base1', 'base2', 'new']}}]
        with patch.object(dev, 'image_id', return_value='image'), patch.object(dev.subprocess, 'check_output', side_effect=[json.dumps(m), text]), patch.object(dev, 'read_output', side_effect=[layers, child]):
            self.assertEqual(dev.verified_runtime_image('tag', m), 'image')
        for payload in [json.dumps(dict(m, native={})), json.dumps(m)]:
            bad_text = text.replace('abc0', 'wrong')
            with patch.object(dev, 'image_id', return_value='image'), patch.object(dev.subprocess, 'check_output', side_effect=[payload,bad_text]):
                with self.assertRaises(ValueError): dev.verified_runtime_image('tag', m)
        with patch.object(dev, 'image_id', return_value='image'), patch.object(dev.subprocess, 'check_output', side_effect=[json.dumps(m),text]), patch.object(dev, 'read_output', side_effect=[layers,[{'RootFS':{'Layers':['wrong']}}]]):
            with self.assertRaisesRegex(ValueError, 'dependency layers'): dev.verified_runtime_image('tag', m)

    def test_package_profiles_and_incompatible_overlays_are_explicit(self):
        r=bundle.example_options('reference', '/reference'); c=bundle.example_options('memory', '/reference')
        self.assertEqual(r['basis'], 'fp64'); self.assertNotIn('native_coarse_fp32', r)
        self.assertEqual(c['native_coarse_corrections'], 3); self.assertTrue(c['direct_basis'])
        self.assertTrue(c['port_setup_reuse']); self.assertEqual(c['field_reference'], '/reference')
        for options in [r,c]:
            self.assertEqual(options['krylov_size'], 64); self.assertEqual(options['frequencies'], [3.55])
            self.assertTrue(options['coax_l2']); self.assertTrue(options['both_ports'])
        with self.assertRaises(ValueError): bundle.example_options('TF32', '/reference')
        with self.assertRaises(ValueError): bundle.checked_reference(None,{})
        with patch.object(dev, 'require_host_memory') as host:
            for kwargs in [dict(ceed_qpool=True),dict(nsys_window='0:2')]:
                with self.assertRaisesRegex(ValueError, 'overlays'):
                    dev.run('coax-tiny','/unused',60,runtime_image='image',**kwargs)
            host.assert_not_called()

    def test_example_CLI_rejects_unsupported_modes_and_unbounded_walltime(self):
        script=Path(bundle.__file__).with_name('package_example.py')
        for args in [['--profile','tf32'],['--seconds','0'],['--seconds','1801'],['--seconds','1','--native-coarse-corrections','2']]:
            r=subprocess.run([sys.executable,str(script),'/unused',*args],capture_output=True,text=True)
            self.assertEqual(r.returncode,2);self.assertIn('error:',r.stderr)


if __name__=='__main__': unittest.main()
