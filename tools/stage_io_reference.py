#!/usr/bin/env python3
"""Read-only archived-output qualification, not a native I/O benchmark."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_csv(data: bytes) -> dict:
    """Check native numeric-table shape while preserving trailing NULL cells."""
    if not data or not data.endswith(b'\n'):
        raise ValueError('CSV is empty or lacks its final newline')
    rows = list(csv.reader(io.StringIO(data.decode('utf-8'))))
    header = [cell.strip() for cell in rows.pop(0)]
    if not header or any(not cell for cell in header) or len(set(header)) != len(header):
        raise ValueError('CSV headers are empty or duplicated')
    counts = [0] * len(header)
    missing = [False] * len(header)
    for row in rows:
        if len(row) != len(header):
            raise ValueError('CSV contains a ragged row')
        for col, cell in enumerate(row):
            cell = cell.strip()
            if cell in ('', 'NULL'):
                missing[col] = True
            else:
                if missing[col]:
                    raise ValueError('CSV numeric column has an internal NULL hole')
                if not math.isfinite(float(cell)):
                    raise ValueError('CSV contains a non-finite value')
                counts[col] += 1
    return {'sha256': digest(data), 'bytes': len(data), 'header': header,
            'rows': len(rows), 'numeric_rows_per_column': counts,
            'null_cells': len(rows) * len(header) - sum(counts)}


def check_port_s(data: bytes, frequencies: list[float], ports: list[int],
                 excitations: list[int]) -> dict:
    report = inspect_csv(data)
    expected = ['f (GHz)']
    for source in excitations:
        for port in ports:
            expected.extend([f'|S[{port}][{source}]| (dB)',
                             f'arg(S[{port}][{source}]) (deg.)'])
    if report['header'] != expected:
        raise ValueError('Port-S schema differs from configured port/excitation ordering')
    if report['null_cells'] or report['rows'] != len(frequencies):
        raise ValueError('Completed Port-S output is incomplete')
    rows = list(csv.reader(io.StringIO(data.decode())))[1:]
    actual = [float(row[0]) for row in rows]
    if any(not math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-10)
           for a, b in zip(actual, frequencies)):
        raise ValueError('Port-S frequency order differs from the run result')
    return report


def archive_report(run: Path) -> dict:
    run = run.resolve()
    start = time.monotonic()
    metadata = {}
    fingerprints = {}
    for name in ('config.json', 'fixture.json', 'build-manifest.json',
                 'command.json', 'result.json'):
        data = (run / name).read_bytes()
        metadata[name] = json.loads(data)
        fingerprints[name] = digest(data)
    config = metadata['config.json']
    result = metadata['result.json']
    if result.get('complete') is not True or result.get('exit_code') != 0:
        raise ValueError('Archive is not a completed successful execution')
    output = (run / config['Problem']['Output']).resolve()
    if not output.is_relative_to(run):
        raise ValueError('Archive output escapes its run directory')
    files = sorted(p for p in output.rglob('*') if p.is_file())
    # Intentionally exclude the large mesh; use its existing frozen-manifest hash.
    total = sum(p.stat().st_size for p in files)
    if total > MAX_ARCHIVE_BYTES:
        raise ValueError('Replay exceeds the small archived-output byte budget')
    csv_reports = {}
    inventory = {}
    for path in files:
        if not path.resolve().is_relative_to(run):
            raise ValueError('Output symlink escapes its archive')
        data = path.read_bytes()
        name = str(path.relative_to(output))
        inventory[name] = {'bytes': len(data), 'sha256': digest(data)}
        if path.suffix == '.csv':
            csv_reports[name] = inspect_csv(data)
    ports = [port['Index'] for port in config['Boundaries']['LumpedPort']]
    excitations = sorted({p.get('Excitation', 0)
                          for p in config['Boundaries']['LumpedPort']} - {0})
    check_port_s((output / 'port-S.csv').read_bytes(), result['frequencies_ghz'],
                 ports, excitations)
    argv = metadata['command.json']['argv']
    images = [arg for arg in argv if re.fullmatch(r'(sha256:)?[0-9a-f]{64}', arg)]
    if len(images) != 1:
        raise ValueError('Cannot identify one pinned image in archived command')
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                     text=True).strip()
    return {
        'schema': 1, 'scope': 'Archived readback/schema only; native writer NOT RUN',
        'run': str(run), 'source_git_revision': source,
        'metadata_sha256': fingerprints,
        'audited_io_source_sha256': {str(path.relative_to(ROOT)): digest(path.read_bytes())
                                     for path in [ROOT / 'palace/utils/tablecsv.cpp',
                                                  ROOT / 'palace/models/postoperatorcsv.cpp']},
        'source_sha256_from_build_manifest': metadata['build-manifest.json']['source_sha256'],
        'native_hashes_from_build_manifest': metadata['build-manifest.json']['native'],
        'mesh_sha256_from_fixture_not_recomputed': metadata['fixture.json']['mesh_sha256'],
        'image': images[0], 'frequencies_ghz': result['frequencies_ghz'],
        'ports': ports, 'excitations': excitations,
        'solver': config['Solver'], 'output_bytes': total,
        'output_files': inventory, 'csv': csv_reports,
        'vtk_files_present': any(p.suffix in {'.vtu', '.pvtu', '.pvd'} for p in files),
        'archive_inspection_seconds_not_native_io_time': time.monotonic() - start,
        'readback_status': 'PASS', 'native_writer_status': 'NOT RUN',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = archive_report(args.run)
    text = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
