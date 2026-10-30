import importlib.util
import json
from pathlib import Path
import os
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
from stage_align_mtimes import align
from stage_operator_reference import compiler_inputs,source_hash


class AlignmentTests(unittest.TestCase):
    def test_only_identical_inputs_change_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ref=root/'ref';work=root/'work'
            for base in [ref,work]:
                (base/'palace').mkdir(parents=True)
                (base/'CMakeLists.txt').write_text('same')
                (base/'palace/changed.cpp').write_text('old' if base==ref else 'new')
                os.utime(base/'CMakeLists.txt',ns=(10,100 if base==ref else 200))
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps(dict(source_sha256=source_hash(compiler_inputs(ref)))))
            changed_mtime=(work/'palace/changed.cpp').stat().st_mtime_ns
            result=align(ref,work,manifest,root/'result.json')
            self.assertEqual((work/'CMakeLists.txt').stat().st_mtime_ns,100)
            self.assertEqual((work/'palace/changed.cpp').stat().st_mtime_ns,changed_mtime)
            self.assertEqual(result['before_source_sha256'],result['after_source_sha256'])
            self.assertEqual(result['changed_inputs_untouched'],['palace/changed.cpp'])

    def test_reference_drift_is_rejected_before_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ref=root/'ref';work=root/'work'
            ref.mkdir();work.mkdir()
            for base in [ref,work]: (base/'CMakeLists.txt').write_text('same')
            m=root/'manifest.json';m.write_text('{"source_sha256":"wrong"}')
            with self.assertRaises(ValueError):align(ref,work,m,root/'report.json')
            self.assertFalse((root/'report.json').exists())
