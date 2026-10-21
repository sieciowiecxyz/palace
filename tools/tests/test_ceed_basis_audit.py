import importlib.util
import json
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('basis_audit',Path(__file__).parents[1]/'ceed_basis_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


class BasisAuditTests(unittest.TestCase):
    def row(self, **kw):
        return dict(topology=(3<<16)|3,space=3,P=20,Q=14,components=2,q_components=3,
                    elements=100,eval=8,transpose=0,add=0,input_length=4000,
                    output_length=8400,scalar_bytes=8,calls=12,**kw)

    def log(self, rows, **end):
        summary=dict(groups=len(rows),calls=sum(r['calls'] for r in rows),errors=0,overflow=0)
        summary.update(end)
        return '\n'.join('PALACE_BASIS_AUDIT '+json.dumps(r) for r in rows)+'\nPALACE_BASIS_AUDIT_END '+json.dumps(summary)

    def test_real_dimensions_transpose_add_and_weight_contract(self):
        row=self.row();r=audit.analyze(self.log([row]));self.assertEqual(r['groups'][0]['N'],200)
        self.assertEqual(r['max_output_vector_bytes'],67200)
        self.assertEqual(r['groups'][0]['basis_coefficients_bytes'],6720)
        row.update(input_length=100000)
        g=audit.analyze(self.log([row]))['groups'][0]
        self.assertEqual(g['input_bytes'],800000)
        self.assertEqual(g['required_input_bytes'],32000)
        self.assertEqual(g['required_output_bytes'],67200)
        row.update(transpose=1,add=1,input_length=8400,output_length=4000)
        self.assertTrue(audit.analyze(self.log([row]))['passed'])
        row.update(eval=16,transpose=0,add=0,input_length=0,output_length=1400,q_components=1)
        self.assertTrue(audit.analyze(self.log([row]))['passed'])

    def test_reject_bad_counts_missing_markers_and_duplicate_groups(self):
        row=self.row();text=self.log([row])
        for bad in ['',text+text,self.log([row,row]),self.log([row],errors=1),
                    self.log([row],overflow=1),self.log([row],calls=11),self.log([row],groups=2)]:
            with self.assertRaises(ValueError):audit.analyze(bad)
        for bad in ['PALACE_BASIS_AUDIT []\nPALACE_BASIS_AUDIT_END {}',
                    'PALACE_BASIS_AUDIT {}\nPALACE_BASIS_AUDIT_END []']:
            with self.assertRaises(ValueError):audit.analyze(bad)

    def test_reject_wrong_precision_enums_and_short_vectors(self):
        for key,value in [('P',0),('Q',float('nan')),('calls',True),('elements',-1),
                          ('scalar_bytes',4),('space',99),('eval',99),('transpose',2),
                          ('input_length',3999),('output_length',8399)]:
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):audit.analyze(self.log([row]))
