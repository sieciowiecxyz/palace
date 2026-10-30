import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location(
    'stage_mesh_binary', Path(__file__).parents[1] / 'stage_mesh_binary.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BinaryMeshGuards(unittest.TestCase):
    def test_cli_keeps_tiny_defaults_and_requires_explicit_positive_large_budgets(self):
        base = ['source.msh', 'cache', '--reader-source', 'reader.cpp']
        args = module.parse_args(base)
        self.assertEqual((args.max_input_bytes, args.max_output_bytes),
                         (4*1024*1024, 4*1024*1024))
        args = module.parse_args(base+['--max-input-bytes', str(400*1024*1024),
                                       '--max-output-bytes', str(256*1024*1024)])
        self.assertEqual((args.max_input_bytes, args.max_output_bytes),
                         (400*1024*1024, 256*1024*1024))
        import contextlib, io
        for value in ['0', '-1']:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                module.parse_args(base+['--max-input-bytes', value])

    def test_semantic_mismatch_witness_is_bounded_and_identifies_exact_fields(self):
        before = {'nodes': 10, 'node_bits_sha256': 'before',
                  'entity_physical_mapping': [[2, 1, [21]], [3, 1, [1]]],
                  'physical_groups': [[2, 21, 'PORT', list(range(10000))]]}
        after = {**before, 'node_bits_sha256': 'after',
                 'entity_physical_mapping': [[2, 1, [22]], [3, 1, [1]]]}
        diff = module.semantic_difference(before, after)
        self.assertEqual(diff['changed_keys'], ['entity_physical_mapping', 'node_bits_sha256'])
        self.assertEqual(diff['first_differences'][0],
                         {'path': ['entity_physical_mapping', 0, 2, 0], 'before': 21, 'after': 22})
        self.assertLess(len(json.dumps(diff)), 4096)
        self.assertEqual(diff['before']['physical_groups']['items'], 1)
        with tempfile.TemporaryDirectory(dir='/dev/shm') as name:
            path = Path(name) / 'failure.json'
            path.write_text(json.dumps(diff))
            failure = module.SemanticMismatch(path, {'difference': diff})
            self.assertIsInstance(failure, ValueError)
            self.assertEqual(json.loads(failure.witness_path.read_text()), diff)
            self.assertIn('witness=', str(failure))

    def test_source_budget_and_supported_metadata(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as name:
            path = Path(name) / 'input.msh'
            path.write_bytes(b'$MeshFormat\n2.2 0 8\n$EndMeshFormat\n$Nodes\n0\n$EndNodes\n$Elements\n0\n$EndElements\n')
            module.check_source(path, 1024)
            with self.assertRaisesRegex(ValueError, 'budget'):
                module.check_source(path, 1)
            path.write_bytes(path.read_bytes() + b'$NodeData\n0\n$EndNodeData\n')
            with self.assertRaisesRegex(ValueError, 'metadata'):
                module.check_source(path, 1024)

    def test_binary_or_other_version_is_not_silently_reconverted(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as name:
            path = Path(name) / 'input.msh'
            for header in [b'2.2 1 8', b'4.1 0 8', b'2.2 0 4']:
                path.write_bytes(b'$MeshFormat\n' + header + b'\n')
                with self.assertRaisesRegex(ValueError, 'ASCII Gmsh 2.2'):
                    module.check_source(path, 1024)

    def test_corrupt_binary_is_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as name:
            cache = Path(name)
            binary = cache / 'mesh.msh'
            binary.write_bytes(b'$MeshFormat\n2.2 1 8\n')
            identity = {'schema': 1}
            (cache / 'manifest.json').write_text(json.dumps(
                {'identity': identity, 'binary_sha256': module.sha_file(binary)}))
            module.validate_cache(cache, identity, 1024)
            binary.write_bytes(binary.read_bytes() + b'corruption')
            with self.assertRaisesRegex(ValueError, 'hash differs'):
                module.validate_cache(cache, identity, 1024)


    def fake_model(self, *, shifted_node=False, reversed_nodes=False, surface_group=21):
        xyz = [float(i) for i in range(30)]
        if shifted_node:
            xyz[0] += 1e-12
        def get_elements(dim, entity):
            if dim == 2:
                return [9], [[1]], [[1, 2, 3, 5, 6, 7]]
            connectivity = list(range(1, 11))
            if reversed_nodes:
                connectivity[-1], connectivity[-2] = connectivity[-2], connectivity[-1]
            return [11], [[2]], [connectivity]
        mesh = SimpleNamespace(
            getNodes=lambda: (list(range(1, 11)), xyz, []), getElements=get_elements,
            getElementProperties=lambda kind: ('P2', 2 if kind == 9 else 3,
                                               2, 6 if kind == 9 else 10, [], 3))
        return SimpleNamespace(model=SimpleNamespace(
            mesh=mesh, getEntities=lambda: [(2, 1), (3, 1)],
            getPhysicalGroupsForEntity=lambda dim, tag: [surface_group if dim == 2 else 1],
            getPartitions=lambda dim, tag: [],
            getPhysicalGroups=lambda: [(2, surface_group), (3, 1)],
            getPhysicalName=lambda dim, tag: f'physical{tag}',
            getEntitiesForPhysicalGroup=lambda dim, tag: [1]))

    def test_equal_counts_do_not_hide_changed_high_order_node_bits(self):
        a = module.semantic_snapshot(self.fake_model())
        b = module.semantic_snapshot(self.fake_model(shifted_node=True))
        self.assertEqual((a['nodes'], a['elements']), (b['nodes'], b['elements']))
        self.assertNotEqual(a['node_bits_sha256'], b['node_bits_sha256'])

    def test_equal_counts_do_not_hide_local_connectivity_orientation_change(self):
        a = module.semantic_snapshot(self.fake_model())
        b = module.semantic_snapshot(self.fake_model(reversed_nodes=True))
        self.assertEqual(a['element_types'], b['element_types'])
        self.assertNotEqual(a['oriented_connectivity_sha256'], b['oriented_connectivity_sha256'])

    def test_equal_counts_do_not_hide_port_attribute_change(self):
        a = module.semantic_snapshot(self.fake_model())
        b = module.semantic_snapshot(self.fake_model(surface_group=22))
        self.assertEqual(a['oriented_connectivity_sha256'], b['oriented_connectivity_sha256'])
        self.assertNotEqual(a['physical_groups'], b['physical_groups'])
        self.assertNotEqual(a['entity_physical_mapping'], b['entity_physical_mapping'])

    def test_new_source_or_reader_identity_cannot_reuse_stale_manifest(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as name:
            directory = Path(name)
            binary = directory / 'mesh.msh'
            binary.write_bytes(b'$MeshFormat\n2.2 1 8\n')
            original = {'source_sha256': 'source1', 'pinned_mfem_reader_sha256': 'reader1'}
            (directory / 'manifest.json').write_text(json.dumps(
                {'identity': original, 'binary_sha256': module.sha_file(binary)}))
            for key in original:
                changed = {**original, key: 'changed'}
                self.assertNotEqual(module.key_for(original), module.key_for(changed))
                with self.assertRaisesRegex(ValueError, 'identity'):
                    module.validate_cache(directory, changed, 1024)


if __name__ == '__main__':
    unittest.main()
