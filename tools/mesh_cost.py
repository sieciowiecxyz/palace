#!/usr/bin/env python3
"""Audit a Gmsh 2.2 ASCII tetrahedral fixture without importing FEM/GPU packages.

Corner-only volumes/areas are geometric estimates for curved quadratic elements.
Element counts are not global H(curl) DOF counts or predictions of BEM accuracy.
"""
import argparse
from array import array
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def audit(path, exterior=20):
    names, types, counts, volume = {}, Counter(), Counter(), defaultdict(float)
    edges, exterior_triangles, exterior_area = Counter(), 0, 0.0
    mesh_hash = hashlib.sha256()
    with path.open('rb') as raw:
        for chunk in iter(lambda: raw.read(1024*1024), b''):
            mesh_hash.update(chunk)
    with path.open() as stream:
        def take():
            return next(stream).strip()
        if take() != '$MeshFormat' or take() != '2.2 0 8' or take() != '$EndMeshFormat':
            raise ValueError('Only Gmsh 2.2 ASCII is supported')
        coordinates = None
        for line in stream:
            section = line.strip()
            if section == '$PhysicalNames':
                for _ in range(int(take())):
                    dim, tag, name = take().split(maxsplit=2)
                    names[(int(dim), int(tag))] = name.strip('"')
                if take() != '$EndPhysicalNames':
                    raise ValueError('Invalid physical names')
            elif section == '$Nodes':
                node_count = int(take())
                coordinates = array('d', [0.0]) * (3*(node_count+1))
                for expected in range(1, node_count+1):
                    node, x, y, z = take().split()
                    if int(node) != expected:
                        raise ValueError('Fixture must have contiguous ordered node IDs')
                    coordinates[3*expected:3*expected+3] = array('d', (float(x), float(y), float(z)))
                if take() != '$EndNodes':
                    raise ValueError('Invalid nodes')
            elif section == '$Elements':
                if coordinates is None:
                    raise ValueError('Missing nodes')
                def xyz(node):
                    if not 1 <= node <= node_count:
                        raise ValueError('Invalid node reference')
                    return coordinates[3*node:3*node+3]
                for _ in range(int(take())):
                    row = list(map(int, take().split()))
                    kind, ntags = row[1:3]
                    if ntags < 1:
                        raise ValueError('Elements must have a physical attribute')
                    tag, nodes = row[3], row[3+ntags:]
                    types[kind] += 1
                    if kind in (4, 11):  # linear or quadratic tetrahedra
                        counts[tag] += 1
                        a, b, c, d = map(xyz, nodes[:4])
                        normal = cross(sub(b, a), sub(c, a))
                        volume[tag] += abs(sum(x*y for x, y in zip(normal, sub(d, a))))/6
                    elif kind in (2, 9):
                        if tag == exterior:
                            exterior_triangles += 1
                            a, b, c = nodes[:3]
                            normal = cross(sub(xyz(b), xyz(a)), sub(xyz(c), xyz(a)))
                            exterior_area += math.sqrt(sum(x*x for x in normal))/2
                            for edge in ((a, b), (b, c), (c, a)):
                                edges[tuple(sorted(edge))] += 1
                    elif kind not in (1, 8, 15):
                        raise ValueError(f'Unsupported element type {kind}')
                if take() != '$EndElements':
                    raise ValueError('Invalid elements')
    if not counts:
        raise ValueError('Missing tetrahedra')
    total, total_volume = sum(counts.values()), sum(volume.values())
    domains = [{'attribute': tag, 'name': names.get((3, tag), str(tag)),
                'tetrahedra': count, 'tetrahedra_fraction': count/total,
                'corner_volume_mesh_units3': volume[tag],
                'corner_volume_fraction': volume[tag]/total_volume}
               for tag, count in sorted(counts.items())]
    n = len(edges)
    return {'schema': 1, 'mesh_sha256': mesh_hash.hexdigest(), 'nodes': node_count,
            'element_types': dict(types), 'tetrahedra': total, 'domains': domains,
            'existing_exterior': {'attribute': exterior, 'triangles': exterior_triangles,
                                 'edges': n, 'non_two_incident_edges': sum(v != 2 for v in edges.values()),
                                 'corner_area_mesh_units2': exterior_area,
                                 'one_dense_complex128_edge_block_bytes': 16*n*n},
            'limitations': ['Corner geometry only for high-order elements; mesh units, not SI',
                            'Element fractions do not determine global DOFs or factor memory',
                            'Existing exterior is not an optimized proposed FEM-BEM interface',
                            'Dense block estimate is illustrative; Maxwell traces may require multiple blocks',
                            'No prediction of achieved error, speed or memory reduction']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.mesh)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
