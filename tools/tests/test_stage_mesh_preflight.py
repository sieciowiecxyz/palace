import importlib.util
import io
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('stage_mesh_preflight',Path(__file__).parents[1]/'stage_mesh_preflight.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class MeshMetadataTests(unittest.TestCase):
    def fixture(self, mixed=False, multiple=False):
        kind = '2' if mixed else '9'
        connectivity = '1 2 3' if mixed else '1 2 3 4 5 6'
        physical = '22' if multiple else '21'
        return (f'$MeshFormat\n2.2 0 8\n$EndMeshFormat\n$Nodes\n6\n'+''.join(f'{i} 0 0 0\n' for i in range(1,7))+
                f'$EndNodes\n$Elements\n2\n1 9 2 21 1 1 2 3 4 5 6\n2 {kind} 2 {physical} 1 {connectivity}\n$EndElements\n').encode()

    def test_type_and_entity_gates_detect_unsupported_without_coordinate_parse(self):
        good=module.scan(io.BytesIO(self.fixture()))
        self.assertTrue(good['current_converter_type_entity_gates_pass'])
        mixed=module.scan(io.BytesIO(self.fixture(mixed=True)))
        self.assertEqual(mixed['unsupported_types_for_converter'], [2])
        multiple=module.scan(io.BytesIO(self.fixture(multiple=True)))
        self.assertEqual(multiple['multi_physical_entity_count'], 1)
        self.assertFalse(multiple['current_converter_type_entity_gates_pass'])

    def test_byte_hash_covers_exact_input(self):
        import hashlib
        data=self.fixture()
        report=module.scan(io.BytesIO(data))
        self.assertEqual(report['sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(report['bytes_read'],len(data))
        with self.assertRaisesRegex(ValueError, 'budget'):
            module.scan(io.BytesIO(data),max_bytes=8)


if __name__=='__main__':unittest.main()
