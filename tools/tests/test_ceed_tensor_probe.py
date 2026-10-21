import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('tensor_probe',Path(__file__).parents[1]/'experiments/ceed_tensor_probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


def case():
    rows=[]
    def accuracy(tol):return dict(passed=True,relative_l2=0.,scaled_max=0.,tolerance=tol)
    def timing():return dict(wall_ms=[1.,2.,3.],cuda_interval_ms=[1.,2.,3.],median_wall_ms=2.,median_cuda_interval_ms=2.)
    for family in range(4):
        for q in ([6] if family==3 else [6,14]):
            for c in ([1,2] if family==0 and q==14 else [1]):
                for mode in [1,[8,4,2,8][family]]:
                    for n in [257,131071]:
                        for trans,add in [(False,False),(True,False),(True,True)]:
                            methods=[]
                            for p,tol in [('FP64',1e-11),('FP32_pedantic',2e-6),('TF32_requested',2e-3)]:
                                check=accuracy(tol);check['independent_cpu']=accuracy(tol)
                                methods.append(dict(precision=p,accuracy=check,timing=timing()))
                            rows.append(dict(family=family,P=[20,15,10,8][family],Q=q,components=c,N=n*c,
                                eval=mode,elements=n,transpose=trans,add=add,canaries_passed=True,
                                original_vs_cpu=accuracy(1e-11),original_timing=timing(),methods=methods))
    return dict(complete=True,rows=rows)


class TensorProbeTests(unittest.TestCase):
    def test_scaling_requires_full_actual_size_ladder(self):
        data=case();data['suite']='scale';rows=[]
        for r in data['rows']:
            if r['family']==0 and r['Q']==14 and r['components']==1 and r['elements']==257:
                for n in [257,1023,4099,16383,65537,131071,1601320]:
                    v=copy.deepcopy(r);v.update(elements=n,N=n);rows.append(v)
        data['rows']=rows;self.assertEqual(len(rows),42)
        self.assertTrue(probe.validate_case(data))
        data['rows'][-1]['elements']=999
        with self.assertRaises(ValueError):probe.validate_case(data)

    def test_exact_action_coverage_and_negative_mixed_result_preserved(self):
        data=case();self.assertEqual(len(data['rows']),96)
        self.assertTrue(probe.validate_case(data))
        data['rows'][0]['methods'][2]['accuracy']['passed']=False
        data['rows'][0]['methods'][2]['accuracy']['relative_l2']=.1
        self.assertTrue(probe.validate_case(data)) # execution/layout qualification, not mixed acceptance

    def test_reject_missing_duplicate_corrupt_dimensions_reference_or_timings(self):
        for key,value in [('P',99),('N',1),('canaries_passed',False),('original_vs_cpu',dict(passed=False))]:
            data=case();data['rows'][0][key]=value
            with self.assertRaises(ValueError):probe.validate_case(data)
        data=case();data['rows'][1]=copy.deepcopy(data['rows'][0])
        with self.assertRaises(ValueError):probe.validate_case(data)
        data=case();data['rows'].pop()
        with self.assertRaises(ValueError):probe.validate_case(data)
        for value in [[],[1,2],[1,2,float('nan')]]:
            data=case();data['rows'][0]['methods'][0]['timing']['wall_ms']=value
            with self.assertRaises(ValueError):probe.validate_case(data)
        data=case();data['rows'][0]['methods'][0]['accuracy']['passed']=False
        with self.assertRaises(ValueError):probe.validate_case(data)

    def test_reject_changed_tolerances_nonfinite_errors_and_wrong_medians(self):
        for key,value in [('relative_l2',float('nan')),('scaled_max',-1),('tolerance',.9)]:
            data=case();data['rows'][0]['methods'][1]['accuracy'][key]=value
            with self.assertRaises(ValueError):probe.validate_case(data)
        data=case();data['rows'][0]['original_timing']['median_wall_ms']=3.
        with self.assertRaises(ValueError):probe.validate_case(data)
