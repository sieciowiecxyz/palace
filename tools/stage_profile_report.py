#!/usr/bin/env python3
"""Aggregate single-rank host phase traces, keeping inclusive/exclusive time distinct."""
import argparse
import json
from pathlib import Path

PREFIX = 'PALACE_STAGE_PROFILE '


def summarize(text):
    stack, totals, count = [], {}, 0
    for line in text.splitlines():
        if not line.startswith(PREFIX):
            continue
        event = json.loads(line[len(PREFIX):])
        name, stamp = event['name'], event['t_ns']
        if not isinstance(stamp, int):
            raise ValueError('Trace timestamps must be integer nanoseconds')
        if event['event'] == 'begin':
            if stack and stamp < stack[-1]['start']:
                raise ValueError('Trace starts before its parent')
            stack.append(dict(name=name, start=stamp, children_s=0.0))
        elif event['event'] == 'end':
            if not stack or stack[-1]['name'] != name:
                raise ValueError('Trace scopes are unmatched or concurrent; single-rank host scopes required')
            frame = stack.pop()
            wall = (stamp-frame['start'])/1e9
            if wall < 0 or abs(wall-event['wall_s']) > 1e-7:
                raise ValueError('Trace duration disagrees with timestamps')
            exclusive = wall-frame['children_s']
            if exclusive < -1e-7:
                raise ValueError('Children exceed parent time')
            row = totals.setdefault(name, dict(count=0, inclusive_s=0.0, exclusive_s=0.0))
            row['count'] += 1
            row['inclusive_s'] += wall
            row['exclusive_s'] += max(0.0, exclusive)
            if stack:
                stack[-1]['children_s'] += wall
            count += 1
        else:
            raise ValueError('Unknown phase trace event')
    if stack or not count:
        raise ValueError('Incomplete or absent trace')
    return dict(scope='Host wall time only; no CUDA synchronization; uninstrumented gaps excluded',
                completed_scopes=count, covered_host_s=sum(x['exclusive_s'] for x in totals.values()),
                phases=sorted((dict(name=k, **v) for k, v in totals.items()),
                              key=lambda x: x['exclusive_s'], reverse=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.log.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
