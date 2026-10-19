import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/'experiments/mixed_basis_probe.py'
SPEC=importlib.util.spec_from_file_location('mixed_basis_probe',SOURCE)
probe=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(probe)


class MixedBasisProbeTests(unittest.TestCase):
    def test_no_fast_math_and_cacheable_separate_compile(self):
        self.assertNotIn('--use_fast_math',probe.FLAGS)
        self.assertNotIn('-shared',probe.FLAGS)
        self.assertIn('-std=c++17',probe.FLAGS)

    def test_bad_deadline_rejected_before_host_allocation(self):
        with patch.object(probe.dev,'require_host_memory') as host:
            for seconds in [0,29,121,1800]:
                with self.assertRaises(ValueError):probe.run(Path('/unused'),seconds)
            host.assert_not_called()

    def test_recipe_and_binary_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(probe,'BASE',Path(folder)),patch.object(probe,'LIBRARY',Path(folder)/'probe.so'),patch.object(probe,'recipe',return_value={'v':1}):
            probe.LIBRARY.write_bytes(b'original')
            probe.dev.write(probe.BASE/'manifest.json',dict(recipe={'v':1},binary_sha256=probe.dev.sha(probe.LIBRARY)))
            self.assertEqual(probe.verified()['recipe'],{'v':1})
            probe.LIBRARY.write_bytes(b'changed')
            with self.assertRaises(ValueError):probe.verified()
