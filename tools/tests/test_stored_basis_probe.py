import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/'experiments/stored_basis_probe.py'
SPEC=importlib.util.spec_from_file_location('stored_basis_probe',SOURCE)
probe=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(probe)


class ActualBasisProbeTests(unittest.TestCase):
    def test_invalid_options_before_allocation(self):
        with patch.object(probe.dev,'require_host_memory') as host:
            for device,seconds in [('bad',60),('cuda',0),('cpu',121)]:
                with self.assertRaises(ValueError):probe.run(Path('/unused'),device,seconds)
            host.assert_not_called()

    def test_native_link_and_no_fast_math(self):
        self.assertIn('-lpalace',probe.LINK)
        self.assertIn('-lHYPRE',probe.LINK)
        self.assertIn('-lcuda',probe.LINK)
        self.assertFalse(any('rpath' in flag and 'stubs' in flag for flag in probe.LINK))
        self.assertNotIn('-ffast-math',probe.FLAGS)

    def test_artifact_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(probe,'BASE',Path(folder)),patch.object(probe,'PROGRAM',Path(folder)/'probe'),patch.object(probe,'recipe',return_value={'v':1}):
            probe.PROGRAM.write_bytes(b'original')
            probe.dev.write(probe.BASE/'manifest.json',dict(recipe={'v':1},binary_sha256=probe.dev.sha(probe.PROGRAM)))
            self.assertEqual(probe.verified()['recipe'],{'v':1})
            probe.PROGRAM.write_bytes(b'changed')
            with self.assertRaises(ValueError):probe.verified()
