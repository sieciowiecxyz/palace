#!/usr/bin/env python3
"""Freeze preprocessing input identity from an existing run; does not execute Palace.

This is an M0 preflight, not MFEM parsing/topology validation or an RF test. Mesh
bytes are streamed for hashing; no mesh copy, solver allocation or GPU access.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def snapshot(directory):
    directory = Path(directory).resolve()
    started = time.monotonic()
    names = ('config.json', 'command.json', 'fixture.json', 'build-manifest.json')
    documents = {name: json.loads((directory / name).read_text()) for name in names}
    config, command, fixture, build = (documents[name] for name in names)
    actual_config = sha(directory / 'config.json')
    if actual_config != command['actual_config_sha256']:
        raise ValueError('Run config bytes differ from recorded actual_config_sha256')
    mesh_name = Path(config['Model']['Mesh'])
    # Preserve the relative layout expected by a staged benchmark, without silently
    # accepting a changed config pointing at another mesh with the same filename.
    if mesh_name.is_absolute() or '..' in mesh_name.parts:
        raise ValueError('Only staged relative mesh paths are supported')
    if str(mesh_name) != fixture['mesh']:
        raise ValueError('Config mesh path differs from fixture mesh path')
    mesh_path = directory / mesh_name
    if mesh_path.stat().st_size != fixture['mesh_bytes']:
        raise ValueError('Mesh byte count differs from fixture')
    mesh_sha = sha(mesh_path)
    if mesh_sha != fixture['mesh_sha256']:
        raise ValueError('Mesh bytes differ from fixture mesh_sha256')
    with mesh_path.open('rb') as stream:
        header = [stream.readline().strip() for _ in range(3)]
    if header != [b'$MeshFormat', b'2.2 0 8', b'$EndMeshFormat']:
        raise ValueError('This preflight supports Gmsh 2.2 ASCII only')
    boundaries = config.get('Boundaries', {})
    solver = config['Solver']
    keys = ('Order', 'PartialAssemblyOrder')
    actual_medium = {key: solver[key] for key in keys}
    actual_medium.update({key: solver['Linear'][key]
                          for key in ('Tol', 'MaxIts', 'MaxSize')})
    return {
        'schema': 1,
        'scope': 'existing-run input identity only; no native preprocessing or RF execution',
        'run': str(directory),
        'input_hashes': {name: sha(directory / name) for name in names},
        'mesh': {'path': str(mesh_name), 'resolved_path': str(mesh_path.resolve()),
                 'sha256': mesh_sha, 'bytes': mesh_path.stat().st_size,
                 'format': 'Gmsh 2.2 ASCII'},
        'config_sha256_before_run': fixture['config_sha256'],
        'config_sha256_actual': actual_config,
        'fixture_medium': fixture['medium'],
        'actual_medium': actual_medium,
        'model': config['Model'],
        'materials': config.get('Domains', {}).get('Materials', []),
        'boundaries': {key: boundaries[key] for key in ('PEC', 'Absorbing', 'LumpedPort')
                       if key in boundaries},
        'runtime_image': command['runtime_image'],
        'runtime_source_sha256': build['source_sha256'],
        'runtime_git_revision': build['git_revision'],
        'native_sha256': build['native'],
        'current_source_matches_runtime': None,
        'native_preprocessing': 'NOT RUN',
        'limitations': [
            'Current checkout/compiler inputs are not compared to runtime here',
            'No element connectivity, high-order geometry, Jacobian, DOF or BC validation',
            'Attributes listed here are config declarations, not measured mesh inventory',
            'A changed run config is accepted only with its recorded actual hash; '
            'fixture and actual medium are both retained',
        ],
        'preflight_wall_seconds': time.monotonic() - started,
    }



def check_diagnostic(postpro, stdout_log, stage='preprocess'):
    """Accept completed native diagnostics with no solve/data artifacts.

    The caller must additionally require process exit zero and a matched build/input
    manifest. This gate deliberately never declares a physical/RF result valid.
    """
    if stage not in ('preprocess', 'operators'):
        raise ValueError('Unknown diagnostic stage')
    postpro = Path(postpro)
    report = json.loads((postpro / 'stage-diagnostic.json').read_text())
    expected = {'schema': 1, 'stage': stage, 'mpi_ranks': 1}
    if any(report.get(key) != value for key, value in expected.items()):
        raise ValueError('Diagnostic identity does not match requested stage')
    for key, value in [('diagnostic_only', True), ('complete', True),
                       ('solve_executed', False), ('rf_result', False)]:
        if report.get(key) is not value:
            raise ValueError(f'Invalid diagnostic status: {key}')
    levels = report.get('mesh_levels')
    if not levels or any(level.get('elements', 0) <= 0 for level in levels):
        raise ValueError('No completed mesh level')
    marker = f'PALACE_STAGE_DIAGNOSTIC: stage={stage} complete=1 solve_executed=0 rf_result=0'
    if Path(stdout_log).read_text().splitlines().count(marker) != 1:
        raise ValueError('Missing or duplicated final diagnostic completion marker')
    counts = json.loads((postpro / 'palace.json').read_text())['ElapsedTime']['Counts']
    if counts.get('Initialization', 0) <= 0 or counts.get('MeshPreprocessing', 0) <= 0:
        raise ValueError('Diagnostic did not record native preprocessing')
    if stage == 'operators' and counts.get('OperatorConstruction', 0) <= 0:
        raise ValueError('Operator diagnostic did not record construction')
    forbidden = ['LinearSolve', 'EigenvalueSolve', 'Preconditioner', 'CoarseSolve',
                 'TimeStepping', 'FarFields']
    if stage == 'preprocess':
        forbidden += ['OperatorConstruction', 'Setup']
    if any(counts.get(key) != 0 for key in forbidden):
        raise ValueError('Diagnostic performed an unexpected solve or operator phase')
    for csv_path in postpro.rglob('*.csv'):
        if stage == 'preprocess':
            raise ValueError('Diagnostic output contains stale or unexpected physical CSV results')
        # Uniform-driven PostOperator may create tables before K/C/M assembly.
        # Empty files/header-only CSV are harmless; any nonempty data record,
        # including a row of NULL cells, means this is not construction-only.
        with csv_path.open(newline='') as stream:
            records = (row for row in csv.reader(stream)
                       if any(cell.strip() for cell in row))
            header = next(records, None)
            if header is not None and header[0].strip() != 'f (GHz)':
                raise ValueError('Operator diagnostic CSV has no recognized frequency header')
            if next(records, None) is not None:
                raise ValueError('Operator diagnostic CSV contains physical data records')
    return {'stage': stage, 'diagnostic_only': True, 'complete': True,
            'solve_executed': False, 'rf_result': False, 'mesh_levels': levels}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = snapshot(args.run)
    # Never overwrite existing evidence or any input file.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(f"Preprocessing input identity PASS; native preprocessing NOT RUN: {args.output}")


if __name__ == '__main__':
    main()
