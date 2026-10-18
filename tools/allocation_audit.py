#!/usr/bin/env python3
"""Attribute a saved large-UVM allocation trace without rerunning the solver."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re


def category(stack):
    joined = '\n'.join(stack)
    if '/libcudss.so' in joined:
        return 'cuDSS factors/workspace'
    if 'AssembleCeedGeometryData' in joined:
        return 'libCEED geometry construction'
    if 'CeedOperatorLinearAssembleQFunction' in joined:
        return 'libCEED QFunction assembly'
    if 'CeedQFunctionApply' in joined:
        return 'libCEED QFunction evaluation'
    if 'CeedBasisApply' in joined:
        return 'libCEED basis evaluation'
    if 'CeedElemRestrictionApply' in joined:
        return 'libCEED element restriction'
    if '/libceed.so' in joined:
        return 'libCEED other workspace'
    if '/libmfem.so' in joined or '/libpalace.so' in joined:
        return 'MFEM/Palace vectors or workspace'
    return 'unresolved'


def audit(lines):
    active, allocations = {}, []
    current = None
    peak, snapshot, events, stack_frames = 0, [], 0, 0
    interleaved_events = 0
    reported_peak = None
    peak_event = None
    for line in lines:
        if 'PALACE_ALLOC {' in line:
            position = line.index('PALACE_ALLOC {')
            interleaved_events += int(position != 0)
            event, _ = json.JSONDecoder().raw_decode(line[position + len('PALACE_ALLOC '):])
            if 'event' not in event or event['event'] not in ['alloc', 'free']:
                raise ValueError('Need alloc/free trace with pointer IDs; old trace is insufficient')
            pointer = event['pointer']
            size = event['bytes']
            if not isinstance(size, int) or size < 0:
                raise ValueError('Invalid allocation size')
            current = None
            if event['event'] == 'alloc':
                if pointer in active:
                    raise ValueError('Live pointer allocated twice')
                current = {**event, 'stack': []}
                active[pointer] = current
                allocations.append(current)
            else:
                previous = active.pop(pointer, None)
                if previous is None or previous['bytes'] != size:
                    raise ValueError('Unmatched large-allocation free')
            events += 1
            if event['logical_live_bytes'] > peak:
                peak = event['logical_live_bytes']
                # Keep the allocation objects: following stack lines belong to this event.
                snapshot = list(active.values())
                peak_event = current if current is not None else event
        elif line.startswith('PALACE_ALLOC_STACK '):
            _, pointer, _, frame = line.rstrip().split(' ', 3)
            if current is None or pointer != current['pointer']:
                raise ValueError('Stack does not belong to current allocation')
            current['stack'].append(frame)
            stack_frames += 1
        elif 'CUDA_UVM:' in line:
            match = re.search(r'peak_managed_bytes=(\d+)', line)
            if match:
                reported_peak = int(match[1])
    if not events or peak_event is None:
        raise ValueError('No attributable allocation events')
    groups = defaultdict(lambda: {'bytes': 0, 'allocations': 0})
    sizes = defaultdict(lambda: {'bytes': 0, 'allocations': 0, 'categories': set()})
    for allocation in snapshot:
        owner, size = category(allocation['stack']), allocation['bytes']
        groups[owner]['bytes'] += size
        groups[owner]['allocations'] += 1
        sizes[size]['bytes'] += size
        sizes[size]['allocations'] += 1
        sizes[size]['categories'].add(owner)
    traced = sum(a['bytes'] for a in snapshot)
    if traced > peak:
        raise ValueError('Traced live allocations exceed allocator total; trace is inconsistent')
    return {
        'scope': 'Logical managed allocation bytes, not physical RAM/VRAM residency; large events only',
        'events': events, 'stack_frames': stack_frames, 'recovered_interleaved_events': interleaved_events,
        'largest_observed_event_live_bytes': peak,
        'reported_all_allocation_peak_bytes': reported_peak,
        'peak_trigger_event': peak_event,
        'peak_context_hint': ('field_snapshot_comparison' if any('CompareFieldSnapshots' in frame
                              for frame in peak_event.get('stack', [])) else 'not identified by this stack'),
        'attributed_large_bytes_at_event_peak': traced,
        'unattributed_small_bytes_at_event_peak': peak - traced,
        'at_event_peak_by_category': dict(sorted(groups.items(), key=lambda item: -item[1]['bytes'])),
        'at_event_peak_by_size': [dict(size_bytes=n, **{**v, 'categories': sorted(v['categories'])})
                                 for n, v in sorted(sizes.items(), key=lambda item: -item[1]['bytes'])],
        'limits': ['Stack-based categories are evidence of the allocation path, not unique semantic ownership',
                   'Only allocations >= trace threshold appear; small allocations can change the true peak',
                   'cuDSS is included in managed bytes: do not add its separate allocator peak',
                   'A disk-basis run does not measure resident GMRES basis; no SSD strategy is recommended'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.log.open() as stream:
        result = audit(stream)
    with args.log.open('rb') as stream:
        result['log_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
    result['source'] = str(args.log.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['largest_observed_event_live_bytes',
                                           'attributed_large_bytes_at_event_peak',
                                           'at_event_peak_by_category']}, indent=2))


if __name__ == '__main__':
    main()
