import copy
import math
from pathlib import Path
import sys
import unittest
import json
import tempfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
import field_roi


class ROIContract(unittest.TestCase):
    def rows(self):
        return [dict(frequency_ghz=3.5,port=p,field=v,quadrature=q,roi=r,
                     relative_complex_L2=1e-6,phase_rms_degrees=1e-5,
                     phase_undefined_reference_fraction=0.,reference_norm_squared=1.,points=64)
                for p in (1,2) for v in ('E','B') for q in (4,6) for r in field_roi.ROIS]

    def test_complete_and_missing_or_duplicate(self):
        rows=self.rows();self.assertTrue(field_roi.assess(rows,[3.5])['passed'])
        for bad in (rows[:-1],rows+[rows[0]],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError):field_roi.assess(bad,[3.5])
        with self.assertRaises(ValueError):field_roi.assess(rows,[3.3,3.5])
        with self.assertRaises(ValueError):field_roi.assess(rows,[3.5,3.5])

    def test_quality_and_phase_failures(self):
        for k,v in [('relative_complex_L2',.01001),('phase_rms_degrees',.58),
                    ('phase_undefined_reference_fraction',1e-5),('reference_norm_squared',0.),
                    ('points',0),('relative_complex_L2',math.nan),('phase_rms_degrees',math.inf)]:
            rows=copy.deepcopy(self.rows());rows[0][k]=v
            with self.assertRaises(ValueError):field_roi.assess(rows,[3.5])

    def test_quadrature_is_not_hidden_by_small_global_error(self):
        rows=self.rows();rows[0]['relative_complex_L2']=.001
        with self.assertRaises(ValueError):field_roi.assess(rows,[3.5])

    def test_rejected_schedules_do_not_read_fields_or_launch(self):
        root=field_roi.dev.ROOT
        r=root/'artifacts/ref';c=root/'artifacts/cand';o=root/'artifacts/not-created'
        with patch.object(field_roi.dev,'require_host_memory',side_effect=AssertionError('Must reject before work')):
            for kwargs in ({}, {'pairs':[dict(reference=str(r),candidate=str(c),frequency_ghz=3.5)]*2},
                           {'pairs':[dict(reference=str(c),candidate=str(r),frequency_ghz=3.5)]}):
                with self.assertRaises(ValueError):field_roi.run(r,c,o,'antenna',**kwargs)

    def test_explicit_assessment_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); fields=root/'fields.json'; output=root/'assessment.json'
            fields.write_text(json.dumps(dict(entries=self.rows())))
            argv=['field_roi.py','assess',str(fields),'--frequencies','3.5','--output',str(output)]
            with patch.object(sys,'argv',argv),patch('builtins.print'):
                field_roi.main()
                self.assertTrue(json.loads(output.read_text())['passed'])
                with self.assertRaises(ValueError):field_roi.main()


if __name__=='__main__':unittest.main()
