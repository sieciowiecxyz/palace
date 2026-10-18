import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('mesh_cost', Path(__file__).parents[1] / 'mesh_cost.py')
mesh_cost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mesh_cost)


MESH = '''$MeshFormat
2.2 0 8
$EndMeshFormat
$PhysicalNames
2
3 1 "AIR"
3 3 "PTFE"
$EndPhysicalNames
$Nodes
5
1 0 0 0
2 1 0 0
3 0 1 0
4 0 0 1
5 0 0 -2
$EndNodes
$Elements
6
1 4 2 1 1 1 2 3 4
2 4 2 3 2 1 3 2 5
3 2 2 20 1 1 2 3
4 2 2 20 1 1 2 4
5 2 2 20 1 1 3 4
6 2 2 20 1 2 3 4
$EndElements
'''


class MeshCostTests(unittest.TestCase):
    def test_domain_counts_are_not_volume_fractions_and_surface_is_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            mesh = Path(temporary) / 'test.msh'
            mesh.write_text(MESH)
            result = mesh_cost.audit(mesh)
        self.assertEqual(result['tetrahedra'], 2)
        air, ptfe = result['domains']
        self.assertEqual(air['tetrahedra_fraction'], 0.5)
        self.assertAlmostEqual(air['corner_volume_fraction'], 1/3)
        self.assertAlmostEqual(ptfe['corner_volume_mesh_units3'], 1/3)
        self.assertEqual(result['existing_exterior']['edges'], 6)
        self.assertEqual(result['existing_exterior']['non_two_incident_edges'], 0)
        self.assertEqual(result['existing_exterior']['one_dense_complex128_edge_block_bytes'], 576)

    def test_unknown_volume_type_and_noncontiguous_nodes_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            mesh = Path(temporary) / 'test.msh'
            for invalid in (MESH.replace('1 4 2 1 1', '1 5 2 1 1'),
                            MESH.replace('5 0 0 -2', '8 0 0 -2')):
                mesh.write_text(invalid)
                with self.assertRaises(ValueError):
                    mesh_cost.audit(mesh)
