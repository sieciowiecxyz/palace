#!/usr/bin/env python3
"""Compare coax diagnostic E/B probes and energies to an analytic matched TEM wave.

Sample errors are not whole-domain L2 errors. This is a cheap physics filter,
not an antenna qualification. Geometry and probes come from explicit run inputs.
"""
import argparse
import cmath
import csv
import json
import math
import re
from pathlib import Path


def csv_rows(path):
    with path.open() as stream:
        rows = [{k.strip(): float(v) for k, v in row.items()}
                for row in csv.DictReader(stream, skipinitialspace=True)]
    if any(not math.isfinite(v) for row in rows for v in row.values()):
        raise ValueError('Non-finite field/energy result: ' + str(path))
    return rows


def evaluate(directory, geometry):
    config = json.loads((directory / 'config.json').read_text())
    post = directory / config['Problem']['Output']
    probes = config['Domains']['Postprocessing']['Probe']
    eps = geometry['epsilon_r']
    a = geometry['inner_radius_mm'] * 1e-3
    b = geometry['shield_inner_radius_mm'] * 1e-3
    length = geometry['length_mm'] * 1e-3
    # Check this known fixture, not an arbitrary coax/port geometry.
    if config['Model']['L0'] != 0.001 or len(config['Boundaries']['LumpedPort']) != 2:
        raise ValueError('Requires known two-port millimetre coax fixture')
    e_rows, b_rows = csv_rows(post/'probe-E.csv'), csv_rows(post/'probe-B.csv')
    voltage_rows, energy_rows = csv_rows(post/'port-V.csv'), csv_rows(post/'domain-E.csv')
    if not len(e_rows) == len(b_rows) == len(voltage_rows) == len(energy_rows) == 1:
        raise ValueError('Expected one frequency and both excitations')
    erow, brow, vrow, energy = e_rows[0], b_rows[0], voltage_rows[0], energy_rows[0]
    f = erow['f (GHz)'] * 1e9
    if any(row['f (GHz)']*1e9 != f for row in [brow, vrow, energy]):
        raise ValueError('Frequency mismatch')
    beta = 2*math.pi*f/299792458*math.sqrt(eps)
    mu0 = 1.25663706212e-6
    eps0 = 1/(mu0*299792458**2)
    capacitance_per_m = 2*math.pi*eps0*eps/math.log(b/a)
    result = {'frequency_ghz': f/1e9, 'probes_per_excitation': len(probes), 'ports': {}}
    for port in [1, 2]:
        inc = vrow[f'V_inc[{port}][{port}] (V)']
        expected_energy = 0.5 * capacitance_per_m * length * inc**2
        errors = {'E': [], 'B': []}
        reference_norms = {'E': [], 'B': []}
        max_relative = {'E': 0.0, 'B': 0.0}
        for probe in probes:
            x, y, z = [v*1e-3 for v in probe['Center']]
            radius = math.hypot(x, y)
            if not a < radius < b or not 0 < z < length:
                raise ValueError('Probe is outside the analytic coax interior')
            distance = z if port == 1 else length-z
            voltage = inc * cmath.exp(-1j*beta*distance)
            e = voltage / (radius*math.log(b/a))
            expected = {'E': [e*x/radius, e*y/radius, 0j],
                        'B': [(-1 if port == 1 else 1)*e*y/radius*math.sqrt(eps)/299792458,
                              (1 if port == 1 else -1)*e*x/radius*math.sqrt(eps)/299792458, 0j]}
            for field, row, unit in [('E', erow, 'V/m'), ('B', brow, 'Wb/m²')]:
                measured = [complex(row[f'Re{{{field}_{axis}[{probe["Index"]}][{port}]}} ({unit})'],
                                    row[f'Im{{{field}_{axis}[{probe["Index"]}][{port}]}} ({unit})'])
                            for axis in 'xyz']
                error = sum(abs(v-w)**2 for v,w in zip(measured, expected[field]))
                norm = sum(abs(v)**2 for v in expected[field])
                errors[field].append(error)
                reference_norms[field].append(norm)
                max_relative[field] = max(max_relative[field], math.sqrt(error/norm))
        result['ports'][str(port)] = {
            **{f'{field}_sample_relative_rms': math.sqrt(sum(errors[field])/sum(reference_norms[field]))
               for field in ['E', 'B']},
            **{f'{field}_max_point_relative_error': max_relative[field] for field in ['E', 'B']},
            'analytic_electric_energy_j': expected_energy,
            'electric_energy_relative_error': abs(energy[f'E_elec[{port}] (J)']/expected_energy-1),
            'magnetic_energy_relative_error': abs(energy[f'E_mag[{port}] (J)']/expected_energy-1)}
    result['scope'] = 'TEM samples/energy; native volume L2 only where logged; not antenna qualification'
    result['model'] = 'matched travelling TEM, zero reflection; numerical port reflections are not fitted away'
    result['volume_l2_checks'] = [
        {'quadrature': int(q), 'excitation': int(p), 'relative_E': float(e), 'relative_B': float(b)}
        for q,p,e,b in re.findall(
            r'PALACE_TEM_L2: quadrature=(\d+) excitation=(\d+) relative_E=([^ ]+) relative_B=([^\s]+)',
            (directory/'palace.log').read_text())]
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--geometry', type=Path, help='Optional mesh-audit.json for legacy runs')
    args = parser.parse_args()
    geometry = (json.loads(args.geometry.read_text())['geometry'] if args.geometry else
                json.loads((args.run/'geometry.json').read_text()) if (args.run/'geometry.json').exists() else
                json.loads((Path(__file__).resolve().parents[1]/'examples/coax-medium/mesh-audit.json').read_text())['geometry'])
    result = evaluate(args.run, geometry)
    (args.run/'tem-fields.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
