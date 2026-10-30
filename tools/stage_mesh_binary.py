#!/usr/bin/env python3
"""Bounded lossless Gmsh-API MSH2.2 binary cache prototype; not native MFEM qualification."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile
import time

OPTIONS = {'Mesh.MshFileVersion': 2.2, 'Mesh.Binary': 1,
           'Mesh.SaveAll': 0, 'Mesh.Renumber': 0, 'Mesh.PreserveNumberingMsh2': 1}
MAX_TINY_BYTES = 4 * 1024 * 1024
ALLOWED_TYPES = {8, 9, 11, 15}  # P2 segment/triangle/tetrahedron and physical points.


def sha_file(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def key_for(identity: dict) -> str:
    return hashlib.sha256(json.dumps(identity, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def check_source(path: Path, limit: int) -> None:
    if path.stat().st_size > limit:
        raise ValueError('Input exceeds the explicit small conversion budget')
    with path.open('rb') as stream:
        if [stream.readline().strip(), stream.readline().strip()] != [b'$MeshFormat', b'2.2 0 8']:
            raise ValueError('Only FP64 ASCII Gmsh 2.2 input is supported by this prototype')
        sections = {'MeshFormat'}
        for line in stream:
            if line.startswith(b'$'):
                name = line.strip()[1:].decode('ascii')
                sections.add(name[3:] if name.startswith('End') else name)
    if not {'MeshFormat', 'Nodes', 'Elements'} <= sections or sections - {
            'MeshFormat', 'Nodes', 'Elements', 'PhysicalNames'}:
        raise ValueError('Unsupported metadata section would be lost by conversion')



def semantic_snapshot(gmsh) -> dict:
    """Digest native Gmsh node bits + oriented connectivity + physical/entity mapping."""
    nodes = hashlib.sha256()
    tags, xyz, _ = gmsh.model.mesh.getNodes()
    tag_order = sorted(range(len(tags)), key=lambda i: int(tags[i]))
    for i in tag_order:
        tag = int(tags[i])
        coord = [float(v) for v in xyz[3*i:3*i+3]]
        if not 0 < tag < 2**31 or not all(math.isfinite(v) for v in coord):
            raise ValueError('Node tags must fit positive int32 and coordinates be finite')
        nodes.update(json.dumps([tag, [v.hex() for v in coord]],
                                separators=(',', ':')).encode() + b'\n')
    elements = hashlib.sha256()
    types, count, entity_map = {}, 0, []
    seen_tags = set()
    for dim, entity in sorted(gmsh.model.getEntities()):
        blocks, ids, connectivity = gmsh.model.mesh.getElements(dim, entity)
        if not sum(map(len, ids)):
            continue
        groups = list(map(int, gmsh.model.getPhysicalGroupsForEntity(dim, entity)))
        if len(groups) != 1 or groups[0] <= 0 or len(gmsh.model.getPartitions(dim, entity)):
            raise ValueError('Only unpartitioned entities with one positive physical group are supported')
        entity_map.append([int(dim), int(entity), groups])
        records = []
        for kind, block_ids, block_nodes in zip(blocks, ids, connectivity):
            kind = int(kind)
            if kind not in ALLOWED_TYPES:
                raise ValueError(f'Unsupported element type {kind}; preserve P2 explicitly')
            properties = gmsh.model.mesh.getElementProperties(kind)
            width = int(properties[3])
            types[str(kind)] = {'order': int(properties[2]), 'nodes_per_element': width,
                                'dimension': int(properties[1])}
            for j, element_id in enumerate(block_ids):
                element_id = int(element_id)
                if not 0 < element_id < 2**31 or element_id in seen_tags:
                    raise ValueError('Element tags must be unique positive int32')
                seen_tags.add(element_id)
                records.append([int(dim), int(entity), kind, element_id,
                                list(map(int, block_nodes[j*width:(j+1)*width]))])
                count += 1
        # Sorting records leaves each element's local node order/orientation unchanged.
        for record in sorted(records, key=lambda value: value[3]):
            elements.update(json.dumps(record, separators=(',', ':')).encode() + b'\n')
    physical = [[int(dim), int(tag), gmsh.model.getPhysicalName(dim, tag),
                 sorted(map(int, gmsh.model.getEntitiesForPhysicalGroup(dim, tag)))]
                for dim, tag in sorted(gmsh.model.getPhysicalGroups())]
    if '11' not in types or not physical:
        raise ValueError('Prototype requires physical P2 tetrahedra')
    return {'nodes': len(tags), 'elements': count, 'node_bits_sha256': nodes.hexdigest(),
            'oriented_connectivity_sha256': elements.hexdigest(),
            'physical_groups': physical, 'entity_physical_mapping': entity_map,
            'element_types': types}


def compact_witness_value(value):
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value if len(value) <= 160 else value[:160] + '...'
    encoder = json.JSONEncoder(sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256()
    for chunk in encoder.iterencode(value):
        digest.update(chunk.encode())
    return {'items': len(value), 'sha256': digest.hexdigest()}


def first_difference(before, after, path):
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after)):
            if key not in before or key not in after:
                return {'path': path+[key], 'before': compact_witness_value(before.get(key)),
                        'after': compact_witness_value(after.get(key))}
            if before[key] != after[key]:
                return first_difference(before[key], after[key], path+[key])
    elif isinstance(before, list) and isinstance(after, list):
        for index, (left, right) in enumerate(zip(before, after)):
            if left != right:
                return first_difference(left, right, path+[index])
        if len(before) != len(after):
            return {'path': path+['length'], 'before': len(before), 'after': len(after)}
    return {'path': path, 'before': compact_witness_value(before),
            'after': compact_witness_value(after)}


def semantic_difference(before, after):
    changed = [key for key in sorted(set(before) | set(after))
               if key not in before or key not in after or before[key] != after[key]]
    return {'changed_keys': changed,
            'before': {key: compact_witness_value(value) for key, value in before.items()},
            'after': {key: compact_witness_value(value) for key, value in after.items()},
            'first_differences': [first_difference(before.get(key), after.get(key), [key])
                                  for key in changed]}


class SemanticMismatch(ValueError):
    def __init__(self, witness_path, details):
        self.witness_path = Path(witness_path)
        self.details = details
        super().__init__('Gmsh readback changed node bits/connectivity/physical metadata; '
                         f'witness={self.witness_path}')



def validate_cache(directory: Path, identity: dict, limit: int) -> dict:
    manifest = json.loads((directory / 'manifest.json').read_text())
    binary = directory / 'mesh.msh'
    if manifest['identity'] != identity or binary.stat().st_size > limit:
        raise ValueError('Cache identity/size differs')
    if sha_file(binary) != manifest['binary_sha256']:
        raise ValueError('Cache binary hash differs; no automatic overwrite')
    with binary.open('rb') as stream:
        if [stream.readline().strip(), stream.readline().strip()] != [b'$MeshFormat', b'2.2 1 8']:
            raise ValueError('Cached mesh is not expected FP64 binary MSH2.2')
    return manifest


def convert(source: Path, cache: Path, gmsh, reader_sha256: str,
            max_input_bytes: int = MAX_TINY_BYTES,
            max_output_bytes: int = MAX_TINY_BYTES) -> dict:
    start = time.monotonic()
    source = source.resolve()
    check_source(source, max_input_bytes)
    identity = {'schema': 1, 'source_sha256': sha_file(source),
                'converter_sha256': sha_file(Path(__file__)), 'gmsh_version': gmsh.__version__,
                'gmsh_library_sha256': sha_file(Path(gmsh.libpath)),
                'pinned_mfem_reader_sha256': reader_sha256, 'options': dict(OPTIONS)}
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / key_for(identity)
    if target.exists():
        manifest = validate_cache(target, identity, max_output_bytes)
        return {'cache_hit': True, 'binary': str(target / 'mesh.msh'),
                'manifest': manifest, 'lookup_seconds': time.monotonic() - start,
                'native_mfem_qualified': False}
    if gmsh.isInitialized():
        raise ValueError('Converter needs its own Gmsh session')
    temporary = Path(tempfile.mkdtemp(prefix='.candidate-', dir=cache))
    try:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.open(str(source))
            before = semantic_snapshot(gmsh)
            for name, value in identity['options'].items():
                gmsh.option.setNumber(name, value)
            binary = temporary / 'mesh.msh'
            gmsh.write(str(binary))
            if binary.stat().st_size > max_output_bytes:
                raise ValueError('Converted output exceeds explicit small budget')
            gmsh.clear()
            gmsh.open(str(binary))
            after = semantic_snapshot(gmsh)
            if after != before:
                details = {'schema': 1, 'identity': identity,
                           'difference': semantic_difference(before, after),
                           'binary_bytes': binary.stat().st_size,
                           'binary_sha256': sha_file(binary),
                           'scope': 'Integrity failure; no native MFEM/RF qualification'}
                failure_dir = cache.parent / (cache.name + '-failures')
                failure_dir.mkdir(parents=True, exist_ok=True)
                witness_path = failure_dir / (key_for(identity) + '-' +
                                               str(time.time_ns()) + '.json')
                witness_path.write_text(json.dumps(details, indent=2) + '\n')
                raise SemanticMismatch(witness_path, details)
        finally:
            gmsh.finalize()
        manifest = {'identity': identity, 'source_bytes': source.stat().st_size,
                    'binary_bytes': binary.stat().st_size, 'binary_sha256': sha_file(binary),
                    'gmsh_semantic_snapshot': before, 'gmsh_roundtrip_passed': True,
                    'native_mfem_qualified': False,
                    'cold_conversion_seconds': time.monotonic() - start}
        (temporary / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        temporary.rename(target)
        return {'cache_hit': False, 'binary': str(target / 'mesh.msh'),
                'manifest': manifest, 'lookup_seconds': time.monotonic() - start,
                'native_mfem_qualified': False}
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def positive_bytes(value: str) -> int:
    count = int(value)
    if count <= 0:
        raise argparse.ArgumentTypeError('Byte budgets must be positive')
    return count


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('cache', type=Path)
    parser.add_argument('--reader-source', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--max-input-bytes', type=positive_bytes, default=MAX_TINY_BYTES)
    parser.add_argument('--max-output-bytes', type=positive_bytes, default=MAX_TINY_BYTES)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    import gmsh  # Existing antenna Gmsh environment; deliberately not a new dependency.
    result = convert(args.source, args.cache, gmsh, sha_file(args.reader_source),
                     args.max_input_bytes, args.max_output_bytes)
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
