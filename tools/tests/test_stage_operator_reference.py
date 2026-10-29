import json
from pathlib import Path
import tempfile
import unittest

from tools import dev
from tools.stage_operator_reference import NATIVE_FILES, audit, compiler_inputs, sha, source_hash


class OperatorReferenceTests(unittest.TestCase):
    def test_hash_coverage_matches_existing_build_tool(self):
        self.assertEqual(source_hash(compiler_inputs(dev.ROOT)), dev.source_hash())

    def fixture(self, root):
        source, bundle, run = [root / name for name in ('source', 'bundle', 'run')]
        for folder in (source, bundle):
            (folder / 'tools/adapter').mkdir(parents=True)
            (folder / 'palace').mkdir()
            (folder / 'cmake').mkdir()
            (folder / 'CMakeLists.txt').write_text('project(test)')
            (folder / 'palace/op.cpp').write_text('operator source')
            (folder / 'tools/runtime.json').write_text('{"architecture":"120"}')
        native_dir = bundle / 'build/sm120/native'
        native_dir.mkdir(parents=True)
        for name in NATIVE_FILES:
            (native_dir / name).write_text(name)
        manifest = {
            'source_sha256': source_hash(compiler_inputs(bundle)),
            'native': {name: sha(native_dir / name) for name in NATIVE_FILES},
            'builder_image_id': 'builder', 'runtime_base_id': 'base',
            'settings_sha256': sha(bundle / 'tools/runtime.json'), 'numerically_validated': False,
        }
        manifest_path = bundle / 'build/sm120/manifest.json'
        manifest_path.write_text(json.dumps(manifest))
        (bundle / 'build/sm120/runtime-image.json').write_text(json.dumps({
            'image_id': 'pinned', 'build_manifest_sha256': sha(manifest_path),
        }))
        run.mkdir()
        (run / 'config.json').write_text('{}')
        (run / 'build-manifest.json').write_text(json.dumps(manifest))
        (run / 'command.json').write_text(json.dumps({
            'runtime_image': 'pinned', 'native_from_image': True,
            'actual_config_sha256': sha(run / 'config.json'),
        }))
        return source, bundle, run

    def test_valid_provenance_does_not_invent_rf_qualification(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = audit(*self.fixture(Path(tmp)))
        self.assertTrue(result['passed'])
        self.assertFalse(result['global_numerically_validated'])

    def test_added_compiler_input_invalidates_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, bundle, run = self.fixture(Path(tmp))
            (source / 'palace/new.hpp').write_text('new input')
            result = audit(source, bundle, run)
        self.assertFalse(result['passed'])
        self.assertEqual(result['changed_compiler_inputs'], ['palace/new.hpp'])

    def test_replaced_native_or_input_fails(self):
        for kind in ('native', 'config', 'image', 'settings'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                source, bundle, run = self.fixture(Path(tmp))
                if kind == 'native':
                    (bundle / 'build/sm120/native/libpalace.so').write_text('different')
                elif kind == 'config':
                    (run / 'config.json').write_text('{"changed":true}')
                elif kind == 'settings':
                    (source / 'tools/runtime.json').write_text('{}')
                else:
                    p = run / 'command.json'
                    command = json.loads(p.read_text()); command['runtime_image'] = 'other'
                    p.write_text(json.dumps(command))
                self.assertFalse(audit(source, bundle, run)['passed'])


if __name__ == '__main__':
    unittest.main()
