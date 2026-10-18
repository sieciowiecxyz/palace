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
    def test_global_dofs_count_shared_entities_once(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as temporary:
            mesh = Path(temporary)/'test.msh'
            mesh.write_text(MESH)
            result = mesh_cost.audit(mesh,dofs=True)['topology']
        self.assertEqual((result['vertices'],result['edges'],result['faces']), (5,9,7))
        self.assertEqual(result['unconstrained_dofs'], dict(h1_p1=5,h1_p2=14,nd_p1=9,nd_p2=32,rt_degree1=27))
        incidence = {tuple(r['attributes']):r for r in result['material_incidence']}
        self.assertEqual(incidence[1,3]['nd_p2'],8)  # shared face + its three edges
        self.assertEqual(incidence[1,]['nd_p2'],12)
        self.assertEqual(incidence[3,]['nd_p2'],12)
        self.assertEqual(sum(r['nd_p2'] for r in incidence.values()),32)
        self.assertEqual(result['nd_p2_complex128_vector_bytes'],512)

    def test_orientation_preserves_shared_topology_and_rejects_degenerate_corners(self):
        topology = mesh_cost.Topology(100)
        topology.add([1,2,3,4],1)
        topology.add([4,3,2,1],3)
        result = topology.report(2,{})
        self.assertEqual(result['unconstrained_dofs']['nd_p2'],20)
        self.assertEqual(result['material_incidence'][0]['attributes'],[1,3])
        with self.assertRaises(ValueError): topology.add([1,1,2,3],1)

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
