#!/usr/bin/env python3
"""Completion checks for fixed, explicit-frequency lumped-port runs; not RF equivalence."""
import csv
import json
import math
from pathlib import Path
import re
from collections import Counter


def records(path):
    with path.open(newline='') as stream:
        rows = (row for row in csv.reader(stream) if any(x.strip() for x in row))
        header = [x.strip() for x in next(rows, [])]
        if not header or header[0] != 'f (GHz)' or len(header) != len(set(header)):
            raise ValueError(f'Invalid frequency CSV header: {path.name}')
        yield header
        for row in rows:
            if len(row) != len(header):
                raise ValueError(f'Incomplete CSV row: {path.name}')
            values = [float(x) for x in row]
            if not all(math.isfinite(x) for x in values):
                raise ValueError(f'Nonfinite CSV data: {path.name}')
            yield values


def frequency_index(value, frequencies):
    matches = [i for i, f in enumerate(frequencies)
               if math.isclose(value, f, rel_tol=5e-9, abs_tol=1e-10)]
    if len(matches) != 1:
        raise ValueError('CSV frequency absent, ambiguous or different from configured samples')
    return matches[0]


def expectations(config, reference):
    """Use unchanged config and archived output schemas, never archive numerical values."""
    driven = config.get('Solver', {}).get('Driven', {})
    if (config.get('Problem', {}).get('Type') != 'Driven' or
            driven.get('Restart', 1) != 1 or driven.get('AdaptiveTol', 0) != 0):
        raise ValueError('Full completion currently requires uniform driven runs without restart')
    frequencies = []
    for sample in driven.get('Samples', []):
        if sample.get('Type') != 'Point' or not isinstance(sample.get('Freq'), list):
            raise ValueError('Full completion requires explicit Point frequency samples')
        for value in sample['Freq']:
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError('Invalid configured frequency')
            frequencies.append(float(value))
    if not frequencies or len(set(frequencies)) != len(frequencies):
        raise ValueError('Missing or duplicate configured frequencies')
    frequencies.sort()
    boundaries = config.get('Boundaries', {})
    if any(boundaries.get(key) for key in ('WavePort', 'FloquetPort', 'SurfaceCurrent', 'CurrentDipole')):
        raise ValueError('Full completion currently supports lumped-port excitations only')
    excitations = sorted({port.get('Excitation', 0) for port in boundaries.get('LumpedPort', [])
                          if port.get('Excitation', 0) > 0})
    if not excitations or any(type(x) is not int for x in excitations):
        raise ValueError('Missing valid lumped-port excitations')
    tables = {}
    for path in sorted(Path(reference).rglob('*.csv')):
        iterator = records(path)
        header = next(iterator)
        # Far-field rows carry excitation and angle identities; wide tables carry them in columns.
        long_form = len(header) >= 4 and header[1:4] == ['exc', 'theta (deg.)', 'phi (deg.)']
        rows = list(iterator)
        if not rows:
            raise ValueError('Reference CSV is empty')
        contexts = [list(values) for values in sorted({tuple(row[1:4]) for row in rows})] if long_form else None
        if long_form and {row[0] for row in contexts} != set(excitations):
            raise ValueError('Reference CSV is missing an excitation')
        tables[str(path.relative_to(reference))] = dict(header=header, contexts=contexts)
    if not {'port-S.csv', 'port-V.csv', 'port-I.csv', 'domain-E.csv'} <= set(tables):
        raise ValueError('Reference lacks required physical CSV schemas')
    for name, symbol in (('port-S.csv', 'S'), ('port-V.csv', 'V'), ('port-I.csv', 'I')):
        unit = 'A' if symbol == 'I' else 'V'
        for port in boundaries['LumpedPort']:
            for excitation in excitations:
                label = f"{symbol}[{port['Index']}][{excitation}]"
                required = ([f'|{label}| (dB)', f'arg({label}) (deg.)'] if symbol == 'S' else
                            [f'Re{{{label}}} ({unit})', f'Im{{{label}}} ({unit})'])
                if not set(required) <= set(tables[name]['header']):
                    raise ValueError('Reference port CSV is missing a port/source column')
    contributions = [[exc, sorted(port['Index'] for port in boundaries['LumpedPort']
                                   if port.get('Excitation') == exc)] for exc in excitations]
    return dict(frequencies_ghz=frequencies, excitations=excitations,
                lumped_port_contributions=contributions, tables=tables)


def check_full(postpro, stdout, stderr, expected):
    postpro = Path(postpro)
    text = Path(stdout).read_text()
    combined = text + '\n' + Path(stderr).read_text()
    if ((postpro/'stage-diagnostic.json').exists() or
            any(marker in combined for marker in
                ('PALACE_STAGE_DIAGNOSTIC', 'PALACE_STAGE_STOP', 'PALACE_STAGE_PROFILE'))):
        raise ValueError('Full run contains diagnostic/stop/trace markers')
    if not re.search(r'^Device configuration: cuda(?:,|$)', text, re.MULTILINE) or not re.search(
            r'^libCEED backend: /gpu/cuda/\S+', text, re.MULTILINE):
        raise ValueError('Actual CUDA device/backend proof missing')
    metadata = json.loads((postpro/'palace.json').read_text())
    frequencies, excitations = expected['frequencies_ghz'], expected['excitations']
    solves = len(frequencies) * len(excitations)
    solver = metadata.get('LinearSolver', {})
    if (type(solver.get('TotalSolves')) is not int or solver['TotalSolves'] != solves or
            type(solver.get('TotalIts')) is not int or solver['TotalIts'] <= 0):
        raise ValueError('Missing, partial or unexpected solver totals')
    problem = metadata.get('Problem', {})
    if any(type(problem.get(key)) is not int or problem[key] <= 0
           for key in ('MPISize', 'OpenMPThreads', 'MeshElements', 'DegreesOfFreedom')) or any(
            problem[key] != 1 for key in ('MPISize', 'OpenMPThreads')):
        raise ValueError('Missing or unexpected full-run problem metadata')
    counts = metadata.get('ElapsedTime', {}).get('Counts', {})
    durations = metadata.get('ElapsedTime', {}).get('Durations', {})
    if (type(counts.get('Total')) is not int or counts['Total'] != 1 or
            type(counts.get('LinearSolve')) is not int or counts['LinearSolve'] != solves or
            type(durations.get('Total')) not in (int, float) or
            not math.isfinite(durations['Total']) or durations['Total'] <= 0):
        raise ValueError('Incomplete elapsed-time metadata')
    recorded = metadata.get('Excitations')
    if not isinstance(recorded, list) or len(recorded) != 1:
        raise ValueError('Missing excitation metadata')
    contributions = []
    for entry in recorded[0]:
        if (not isinstance(entry, list) or len(entry) != 2 or not isinstance(entry[1], dict) or
                not isinstance(entry[1].get('LumpedPort'), list) or
                any(value for key, value in entry[1].items() if key != 'LumpedPort')):
            raise ValueError('Incomplete or non-lumped excitation metadata')
        contributions.append([entry[0], sorted(entry[1]['LumpedPort'])])
    if sorted(contributions) != expected['lumped_port_contributions']:
        raise ValueError('Excitation metadata does not match configured sources')
    # Actual audit marker uniquely associates a subsequent solve with a port/frequency.
    setup = re.compile(r'^PALACE_PORT_SETUP: action=(?:build|reuse) excitation=(\d+) frequency_index=(\d+)$')
    iteration = re.compile(r'^It (\d+)/(\d+): ω/2π = (\S+) GHz .*')
    residual = re.compile(r'^PALACE_RAW_RESIDUAL: pc_side=\S+ raw=(\S+) rhs=(\S+) ax=(\S+) relative_rhs=(\S+) relative_action=(\S+)$')
    active = None
    seen = {}
    for line in text.splitlines():
        match = setup.match(line)
        if match:
            if active is not None:
                raise ValueError('New solve started before convergence proof')
            key = (int(match[1]), int(match[2]))
            if key[0] not in excitations or not 0 <= key[1] < len(frequencies) or key in seen:
                raise ValueError('Duplicate or unexpected port/frequency solve')
            active = dict(key=key, iteration=False, residual=None)
        elif iteration.match(line):
            match = iteration.match(line)
            if (active is None or active['iteration'] or int(match[1])-1 != active['key'][1]
                    or int(match[2]) != len(frequencies)
                    or not math.isclose(float(match[3]), frequencies[active['key'][1]], rel_tol=5.1e-4)):
                raise ValueError('Solve frequency marker mismatch')
            active['iteration'] = True
        elif line.startswith('PALACE_RAW_RESIDUAL:'):
            match = residual.match(line)
            if match is None or active is None or not active['iteration']:
                raise ValueError('Unassociated or malformed raw residual marker')
            values = [float(x) for x in match.groups()]
            if not all(math.isfinite(x) and x >= 0 for x in values) or values[1] <= 0:
                raise ValueError('Nonfinite or invalid raw residual')
            if not math.isclose(values[0]/values[1], values[3], rel_tol=1e-9, abs_tol=1e-15):
                raise ValueError('Raw residual constituent norms disagree')
            # A reliable restart may emit a larger intermediate residual. Check the final one.
            active['residual'] = values[3]
        elif line.startswith('GMRES solver converged in '):
            if active is None or active['residual'] is None or active['residual'] > 1e-6:
                raise ValueError('Missing or excessive final raw relative residual')
            seen[active['key']] = active['residual']
            active = None
    required = {(excitation, f) for excitation in excitations for f in range(len(frequencies))}
    if active is not None or set(seen) != required:
        raise ValueError('Missing port/frequency convergence evidence')
    paths = {str(p.relative_to(postpro)): p for p in postpro.rglob('*.csv')}
    if set(paths) != set(expected['tables']):
        raise ValueError('Physical CSV file set differs from expected schemas')
    table_counts = {}
    for name, schema in expected['tables'].items():
        iterator = records(paths[name])
        if next(iterator) != schema['header']:
            raise ValueError(f'Physical CSV header mismatch: {name}')
        observed = Counter()
        for row in iterator:
            f = frequency_index(row[0], frequencies)
            key = (f, *row[1:4]) if schema['contexts'] is not None else (f,)
            observed[key] += 1
        required_rows = Counter((f, *context) for f in range(len(frequencies))
                                for context in schema['contexts']) if schema['contexts'] is not None else Counter((f,) for f in range(len(frequencies)))
        if observed != required_rows:
            raise ValueError(f'Physical CSV rows/frequencies/sources incomplete: {name}')
        table_counts[name] = sum(observed.values())
    return dict(stage='full', diagnostic_only=False, complete=True, solver_executed=True,
                rf_qualified=False, total_solves=solves, total_iterations=solver['TotalIts'],
                max_raw_relative_rhs=max(seen.values()), residual_limit=1e-6,
                frequencies_ghz=frequencies, excitations=excitations, csv_rows=table_counts)
