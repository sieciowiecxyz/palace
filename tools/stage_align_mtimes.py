#!/usr/bin/env python3
"""Restore reference mtimes for byte-identical compiler inputs in another worktree.

The reference must match an existing native manifest. Changed files and compiled
objects are never touched. This repairs worktree checkout timestamp churn, not
compiler flags or dependency changes. Always inspect the build dry-run afterward.
"""
import argparse
import json
import os
from pathlib import Path
from stage_operator_reference import compiler_inputs, source_hash


def align(reference, source, manifest, report):
    reference, source = Path(reference).resolve(), Path(source).resolve()
    if reference == source:
        raise ValueError('Reference and experimental worktree must differ')
    base, current = compiler_inputs(reference), compiler_inputs(source)
    expected = json.loads(Path(manifest).read_text())['source_sha256']
    if source_hash(base) != expected:
        raise ValueError('Reference no longer matches cached native source')
    before = source_hash(current)
    changed = sorted(k for k in base.keys() | current.keys() if base.get(k) != current.get(k))
    times = []
    for name in sorted(base.keys() & current.keys()):
        if name in changed:
            continue
        destination, original = source/name, reference/name
        if destination.resolve() == original.resolve() or destination.is_symlink():
            continue
        stat, ref_stat = destination.stat(), original.stat()
        times.append(dict(path=name, previous_mtime_ns=stat.st_mtime_ns,
                          reference_mtime_ns=ref_stat.st_mtime_ns, sha256=base[name]))
    result = dict(schema=1, reference=str(reference), source=str(source),
                  before_source_sha256=before, unchanged_inputs=times,
                  changed_inputs_untouched=changed, applied=False)
    report = Path(report)
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open('x') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    for row in times:
        path = source/row['path']
        os.utime(path,ns=(path.stat().st_atime_ns,row['reference_mtime_ns']))
    after = source_hash(compiler_inputs(source))
    if after != before:
        raise RuntimeError('Compiler inputs changed during metadata alignment')
    result.update(after_source_sha256=after,applied=True)
    report.write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('reference','source','manifest','report'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    result=align(args.reference,args.source,args.manifest,args.report)
    print(json.dumps(dict(adjusted=len(result['unchanged_inputs']),
                          changed_inputs_untouched=result['changed_inputs_untouched'],
                          source_sha256=result['after_source_sha256']),indent=2))


if __name__=='__main__': main()
