import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/'experiments/exafmm_build.py'
SPEC=importlib.util.spec_from_file_location('exafmm_build',SCRIPT)
builder=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(builder)


class AddonBuildTests(unittest.TestCase):
    def test_content_and_path_fingerprints_change_without_deleting_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/'header.h').write_text('a')
            first=builder.tree_hash(p);self.assertEqual(first,builder.tree_hash(p))
            (p/'header.h').write_text('b');self.assertNotEqual(first,builder.tree_hash(p))
            second=builder.tree_hash(p);(p/'header.h').rename(p/'other.h');self.assertNotEqual(second,builder.tree_hash(p))

    def test_image_cache_key_changes_with_provision_recipe(self):
        original=builder.image_name()
        with patch.object(builder,'PROVISION',builder.PROVISION+'\n#changed'):
            self.assertNotEqual(original,builder.image_name())
        self.assertNotIn('-ffast-math',builder.FLAGS)
        self.assertNotIn('-shared',builder.FLAGS)
        self.assertIn('-march=x86-64-v3',builder.FLAGS)

    def test_verified_rejects_modified_artifact_or_recipe(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(builder,'BASE',Path(folder)),patch.object(builder,'recipe',return_value={'v':1}):
            p=Path(folder);(p/'module.so').write_bytes(b'placeholder')
            builder.dev.write(p/'manifest.json',dict(recipe={'v':1},files_sha256={'module.so':builder.dev.sha(p/'module.so')}))
            self.assertEqual(builder.verified()['recipe'],{'v':1})
            (p/'module.so').write_bytes(b'changed')
            with self.assertRaises(ValueError):builder.verified()
