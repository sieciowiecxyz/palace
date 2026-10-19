"""Test the stdlib RAM guard without importing optional numerical libraries."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


SOURCE=Path(__file__).resolve().parents[1]/'experiments/bempp_fmm_control.py'


class ScratchGuardTests(unittest.TestCase):
    def call_guard(self,free_blocks):
        tree=ast.parse(SOURCE.read_text())
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='scratch_usage')
        stats=SimpleNamespace(f_blocks=131072,f_bfree=free_blocks,f_frsize=4096)
        scope={'os':SimpleNamespace(statvfs=lambda path:stats)}
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(SOURCE),'exec'),scope)
        return scope['scratch_usage']()

    def test_exhausted_or_single_free_page_rejected(self):
        for blocks in [0,1]:
            with self.subTest(blocks=blocks),self.assertRaisesRegex(RuntimeError,'RAM tmpfs exhausted'):
                self.call_guard(blocks)

    def test_usage_and_capacity_in_bytes(self):
        self.assertEqual(self.call_guard(65536),(268435456,536870912))
        self.assertEqual(self.call_guard(131072),(0,536870912))
