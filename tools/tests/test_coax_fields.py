import csv
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('coax_fields', Path(__file__).parents[1]/'coax_fields.py')
fields = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fields)


class CoaxFieldTests(unittest.TestCase):
    def test_exact_tem_and_wrong_magnetic_sign_with_real_writer_units(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            post = root/'postpro'
            post.mkdir()
            config = {'Problem': {'Output': 'postpro'}, 'Model': {'L0': 0.001},
                      'Boundaries': {'LumpedPort': [{}, {}]},
                      'Domains': {'Postprocessing': {'Probe': [{'Index': 1, 'Center': [0.25, 0, 1]}]}}}
            (root/'config.json').write_text(json.dumps(config))
            (root/'palace.log').write_text('')
            geometry = {'epsilon_r': 2.1, 'inner_radius_mm': 0.12,
                        'shield_inner_radius_mm': 0.40179519190143026, 'length_mm': 2}
            radius, length, voltage = 0.00025, 0.002, math.sqrt(50)
            logratio = math.log(geometry['shield_inner_radius_mm']/geometry['inner_radius_mm'])
            beta = 2*math.pi*3.55e9/299792458*math.sqrt(2.1)
            e = voltage/(radius*logratio)*complex(math.cos(beta*length/2), -math.sin(beta*length/2))
            energy = math.pi*(1/(1.25663706212e-6*299792458**2))*2.1/logratio*length*voltage**2
            def write(name, row):
                with (post/name).open('w') as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(row[0] if isinstance(row,list) else row))
                    writer.writeheader()
                    writer.writerows(row if isinstance(row,list) else [row])
            erow, brow, vrow, urow = ({'f (GHz)': 3.55} for _ in range(4))
            for port, sign in [(1, 1), (2, -1)]:
                for field, row, unit, values in [
                    ('E', erow, 'V/m', [e, 0j, 0j]),
                    ('B', brow, 'Wb/m²', [0j, sign*e*math.sqrt(2.1)/299792458, 0j])]:
                    for axis, value in zip('xyz', values):
                        row[f'Re{{{field}_{axis}[1][{port}]}} ({unit})'] = value.real
                        row[f'Im{{{field}_{axis}[1][{port}]}} ({unit})'] = value.imag
                vrow[f'V_inc[{port}][{port}] (V)'] = voltage
                urow[f'E_elec[{port}] (J)'] = urow[f'E_mag[{port}] (J)'] = energy
            for name, row in [('probe-E.csv', erow), ('probe-B.csv', brow),
                              ('port-V.csv', vrow), ('domain-E.csv', urow)]:
                write(name, row)
            result = fields.evaluate(root, geometry)
            for port in result['ports'].values():
                self.assertLess(port['E_sample_relative_rms'], 1e-12)
                self.assertLess(port['B_sample_relative_rms'], 1e-12)
                self.assertLess(port['electric_energy_relative_error'], 1e-12)
            # A second frequency has a different physical phase, not duplicated data.
            config['Solver']={'Driven':{'Samples':[{'Type':'Point','Freq':[3.55,3.8]}]}}
            (root/'config.json').write_text(json.dumps(config))
            import cmath
            ratio=cmath.exp(-1j*(3.8/3.55-1)*beta*length/2)
            second=[]
            names=['probe-E.csv','probe-B.csv','port-V.csv','domain-E.csv']
            for name,row in zip(names,[erow,brow,vrow,urow]):
                other=dict(row);other['f (GHz)']=3.8
                for key in row:
                    if key.startswith('Re{'):
                        imaginary=key.replace('Re{','Im{')
                        value=complex(row[key],row[imaginary])*ratio
                        other[key]=value.real;other[imaginary]=value.imag
                second.append(other);write(name,[row,other])
            multi=fields.evaluate(root,geometry)
            self.assertEqual([r['frequency_ghz'] for r in multi['frequencies']],[3.55,3.8])
            for r in multi['frequencies']:
                for port in r['ports'].values():
                    self.assertLess(port['E_sample_relative_rms'],1e-12)
                    self.assertLess(port['B_sample_relative_rms'],1e-12)
            second[1]['f (GHz)']=3.7;write('probe-B.csv',[brow,second[1]])
            with self.assertRaisesRegex(ValueError,'Frequency mismatch'):fields.evaluate(root,geometry)
            write('probe-B.csv',brow)
            with self.assertRaisesRegex(ValueError,'all requested frequencies'):fields.evaluate(root,geometry)
            del config['Solver'];(root/'config.json').write_text(json.dumps(config))
            for name,row in zip(names,[erow,brow,vrow,urow]):write(name,row)
            # A wrong travel-direction sign must be detected, never fitted away.
            for key in brow:
                if key != 'f (GHz)':
                    brow[key] *= -1
            write('probe-B.csv', brow)
            self.assertAlmostEqual(fields.evaluate(root, geometry)['ports']['1']['B_sample_relative_rms'], 2)
            brow['f (GHz)'] = float('nan')
            write('probe-B.csv', brow)
            with self.assertRaisesRegex(ValueError, 'Non-finite'):
                fields.evaluate(root, geometry)
