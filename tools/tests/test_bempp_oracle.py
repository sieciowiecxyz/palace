import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1]/'experiments/bempp_oracle.py'
SPEC = importlib.util.spec_from_file_location('bempp_oracle',SCRIPT)
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


class PythonMountTests(unittest.TestCase):
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
