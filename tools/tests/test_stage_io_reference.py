import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'stage_io_reference', Path(__file__).parents[1] / 'stage_io_reference.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StageIOReferenceTests(unittest.TestCase):
    def test_partial_source_columns_keep_native_trailing_null_semantics(self):
        report = module.inspect_csv(b'f,source1,source2\n1,0.1,0.2\n2,0.3,NULL\n')
        self.assertEqual(report['numeric_rows_per_column'], [2, 2, 1])
        self.assertEqual(report['null_cells'], 1)

    def test_rejects_internal_hole_and_nonfinite_or_truncated_output(self):
        for data in (b'f,s\n1,NULL\n2,0.1\n', b'f,s\n1,nan\n',
                     b'f,s\n1,0.1', b'f,s\n1,0.1,0.2\n'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                module.inspect_csv(data)

    def test_completed_two_source_schema_requires_both_port_columns(self):
        headers = ['f (GHz)']
        for source in [1, 2]:
            for port in [1, 2]:
                headers += [f'|S[{port}][{source}]| (dB)',
                            f'arg(S[{port}][{source}]) (deg.)']
        raw = (','.join(headers) + '\n1.92,' + ','.join(['0'] * 8) + '\n').encode()
        report = module.check_port_s(raw, [1.92], [1, 2], [1, 2])
        self.assertEqual(report['rows'], 1)
        with self.assertRaises(ValueError):
            module.check_port_s(raw, [2.69], [1, 2], [1, 2])
        with self.assertRaises(ValueError):
            module.check_port_s(raw.replace(b'0\n', b'NULL\n'), [1.92], [1, 2], [1, 2])

    def test_reordered_source_headers_fail(self):
        raw = b'f (GHz),|S[1][2]| (dB),arg(S[1][2]) (deg.)\n1.92,0,0\n'
        with self.assertRaises(ValueError):
            module.check_port_s(raw, [1.92], [1], [1])


if __name__ == '__main__':
    unittest.main()
