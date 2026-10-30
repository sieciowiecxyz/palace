#!/usr/bin/env python3
"""One bounded MSH2.2 ASCII metadata/hash pass; never loads Gmsh or parses coordinates."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import fcntl
import hashlib
import json
from pathlib import Path
import resource
import time

# Known MSH2 element dimensions/widths; unknown types remain reported, never reinterpreted.
TYPES = {1: (1, 2), 2: (2, 3), 3: (2, 4), 4: (3, 4), 5: (3, 8),
         6: (3, 6), 7: (3, 5), 8: (1, 3), 9: (2, 6), 10: (2, 9),
         11: (3, 10), 12: (3, 27), 13: (3, 18), 14: (3, 14), 15: (0, 1)}
ALLOWED_TYPES = {8, 9, 11, 15}


class Reader:
    def __init__(self, stream, max_bytes, seconds):
        self.stream = stream
        self.sha = hashlib.sha256()
        self.bytes = self.lines = 0
        self.max_bytes = max_bytes
        self.deadline = time.monotonic() + seconds

    def line(self):
        line = self.stream.readline()
        self.bytes += len(line)
        self.lines += 1
        if self.bytes > self.max_bytes:
            raise ValueError('Read byte budget exceeded')
        if self.lines % 4096 == 0 and time.monotonic() > self.deadline:
            raise TimeoutError('Metadata read deadline exceeded')
        self.sha.update(line)
        return line

    def expect(self, text):
        if self.line().strip() != text:
            raise ValueError('Unexpected section delimiter')


def scan(stream, *, max_bytes=400*1024*1024, seconds=30):
    start = time.monotonic()
    reader = Reader(stream, max_bytes, seconds)
    reader.expect(b'$MeshFormat')
    if reader.line().strip() != b'2.2 0 8':
        raise ValueError('Expected FP64 ASCII MSH2.2')
    reader.expect(b'$EndMeshFormat')
    sections = ['MeshFormat']
    names = []
    node_count = element_count = 0
    node_min, node_max = 2**63, 0
    element_min, element_max = 2**63, 0
    ref_min, ref_max = 2**63, 0
    node_ordered, previous = True, 0
    widths = defaultdict(Counter)
    type_counts, tag_counts = Counter(), Counter()
    physical_counts = Counter()
    entity_groups = defaultdict(set)
    int32_errors = invalid_tags = width_errors = 0
    while line := reader.line():
        section = line.strip()
        if not section:
            continue
        if not section.startswith(b'$') or section.startswith(b'$End'):
            raise ValueError('Unexpected content outside a section')
        section = section[1:].decode('ascii')
        sections.append(section)
        if section == 'PhysicalNames':
            for _ in range(int(reader.line())):
                parts = reader.line().split(None, 2)
                names.append([int(parts[0]), int(parts[1]), parts[2].strip().decode()])
            reader.expect(b'$EndPhysicalNames')
        elif section == 'Nodes':
            node_count = int(reader.line())
            for _ in range(node_count):
                tag = int(reader.line().split(None, 1)[0])
                node_min, node_max = min(node_min, tag), max(node_max, tag)
                node_ordered = node_ordered and tag > previous
                previous = tag
                int32_errors += not -(2**31) <= tag < 2**31
                invalid_tags += tag <= 0
            reader.expect(b'$EndNodes')
        elif section == 'Elements':
            element_count = int(reader.line())
            for _ in range(element_count):
                data = [int(x) for x in reader.line().split()]
                element, kind, n_tags = data[:3]
                if n_tags < 0 or len(data) < 3+n_tags:
                    raise ValueError('Malformed element tag count')
                node_refs = data[3+n_tags:]
                if not node_refs:
                    raise ValueError('Element has no connectivity')
                element_min, element_max = min(element_min, element), max(element_max, element)
                ref_min, ref_max = min(ref_min, min(node_refs)), max(ref_max, max(node_refs))
                int32_errors += sum(not -(2**31) <= value < 2**31 for value in data)
                invalid_tags += element <= 0 or min(node_refs) <= 0
                type_counts[kind] += 1
                tag_counts[n_tags] += 1
                widths[kind][len(node_refs)] += 1
                dimension, width = TYPES.get(kind, (-1, None))
                width_errors += width is not None and width != len(node_refs)
                physical = data[3] if n_tags else 1
                geometric = data[4] if n_tags > 1 else 0
                physical_counts[(dimension, physical)] += 1
                entity_groups[(dimension, geometric)].add(physical)
                if len(entity_groups) > 100000:
                    raise ValueError('Entity metadata memory budget exceeded')
            reader.expect(b'$EndElements')
        else:
            end = ('$End'+section).encode()
            while (line := reader.line()) and line.strip() != end:
                pass
            if not line:
                raise ValueError('Unterminated unsupported section')
    multiple = [(key, sorted(groups)) for key, groups in entity_groups.items() if len(groups) != 1]
    unsupported = sorted(set(type_counts) - ALLOWED_TYPES)
    extra_sections = sorted(set(sections) - {'MeshFormat', 'PhysicalNames', 'Nodes', 'Elements'})
    return {
        'scope': 'Source metadata and byte hash only; no Gmsh/MFEM load or coordinate validation',
        'sha256': reader.sha.hexdigest(), 'bytes_read': reader.bytes, 'lines_read': reader.lines,
        'wall_seconds': time.monotonic()-start,
        'process_maxrss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'sections': sections, 'node_count': node_count, 'element_count': element_count,
        'node_tag_range': [node_min, node_max], 'node_tags_strictly_increasing': node_ordered,
        'element_tag_range': [element_min, element_max], 'node_reference_range': [ref_min, ref_max],
        'element_types': dict(sorted(type_counts.items())), 'n_tags': dict(sorted(tag_counts.items())),
        'observed_node_widths': {str(k): dict(v) for k,v in sorted(widths.items())},
        'physical_names': names, 'physical_counts': {f'{dim}:{tag}': count for (dim,tag),count in sorted(physical_counts.items())},
        'geometric_entity_count': len(entity_groups), 'multi_physical_entity_count': len(multiple),
        'multi_physical_examples': [{'dimension': key[0], 'entity': key[1], 'physical_tags': groups} for key,groups in sorted(multiple)[:8]],
        'int32_range_errors': int32_errors, 'nonpositive_element_node_tags': invalid_tags,
        'connectivity_width_errors': width_errors,
        'unsupported_types_for_converter': unsupported,
        'unsupported_sections_for_converter': extra_sections,
        'current_converter_type_entity_gates_pass': not (unsupported or multiple or extra_sections or int32_errors or invalid_tags or width_errors),
        'limitations': ['Coordinates are not parsed or validated', 'Node-reference membership and duplicate element IDs not checked',
                        'Header counts and physical/entity metadata are not a native topology/field qualification'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--expected-bytes', type=int, required=True)
    args = parser.parse_args()
    import sys
    sys.path.insert(0, '/home/sieciowiec/dev/cpp/palace/tools')
    from stage_probe_run import host_lock_path
    sys.path.insert(0, '/home/sieciowiec/dev/python/anteny')
    from infra.local.inference_guard import inference_processes
    import subprocess
    service = dict(line.split('=',1) for line in subprocess.check_output(
        ['systemctl','--user','show','localai-nvfp4.service','--property=ActiveState,SubState,MainPID'],text=True).splitlines())
    processes = inference_processes()
    if service != {'ActiveState':'inactive','SubState':'dead','MainPID':'0'} or processes:
        raise ValueError('Inference service/process guard failed')
    lock_path = host_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.mesh.stat().st_size != args.expected_bytes or args.expected_bytes > 400*1024*1024:
            raise ValueError('Input identity or byte budget mismatch')
        with args.mesh.open('rb') as stream:
            report = scan(stream)
        if report['sha256'] != args.expected_sha256 or report['bytes_read'] != args.expected_bytes:
            raise ValueError('Source identity changed during scan')
        report.update(mesh=str(args.mesh.resolve()), host_lock=str(lock_path), inference_guard=service)
        text = json.dumps(report, indent=2)+'\n'
        if len(text.encode()) > 16384:
            raise ValueError('Metadata output exceeds the small JSON budget')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(json.dumps({k:report[k] for k in ['bytes_read','sha256','wall_seconds','process_maxrss_kib','node_count','element_count','element_types','n_tags','multi_physical_entity_count','unsupported_types_for_converter','current_converter_type_entity_gates_pass']},indent=2))


if __name__ == '__main__':
    main()
