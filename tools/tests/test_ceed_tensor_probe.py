import copy
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
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
                                q_components=(1 if family==2 else 2 if family==3 else 3) if mode==1 else (1 if family in [1,3] else 3),
                                eval=mode,elements=n,transpose=trans,add=add,canaries_passed=True,
                                original_vs_cpu=accuracy(1e-11),original_timing=timing(),methods=methods))
    return dict(complete=True,rows=rows)


def compensated_case(bits=False):
    data=case();data.update(fused=True,compensated=True)
    def lin(tol):
        metric=dict(relative_l2=0.,scaled_max=0.,tolerance=tol,passed=True)
        return dict(alpha=1.23456789012345,homogeneity=copy.deepcopy(metric),superposition=copy.deepcopy(metric))
    for row in data['rows']:
        m=copy.deepcopy(row['methods'][1]);m.update(precision='FP32_fused',extra_fp32_workspace_bytes=row['P']*row['Q']*row['q_components']*4)
        row['methods'].append(m)
        if not row['transpose']:
            m=copy.deepcopy(row['methods'][0]);m.update(precision='mixed_compensated',extra_fp32_workspace_bytes=row['P']*row['Q']*row['q_components']*8)
            row['methods'].append(m)
            row['original_linearity']=lin(1e-11)
            for m in row['methods']:m['linearity']=lin(m['accuracy']['tolerance'])
    if bits:
        data.update(compensated_bits=True,tiny_error_controls=True)
        for row in data['rows']:
            if row['transpose']:continue
            method=copy.deepcopy(row['methods'][-1]);method['precision']='mixed_compensated_bits'
            method['range_stress']=[dict(scale=s,accuracy=copy.deepcopy(method['accuracy'])) for s in
                [1e-300,1e-80,2.**-75,2.**-74,1e-30,1.,1e30,2.**100,2.**101,1e80,1e300]]
            row['methods'].append(method)
    return data


class TensorProbeTests(unittest.TestCase):
    def test_trace_symbols_require_actual_nonempty_kernel_activity(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'trace.sqlite'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE StringIds (id INTEGER,value TEXT)')
                db.execute('CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL (demangledName INTEGER,mangledName INTEGER,start INTEGER,end INTEGER)')
                db.executemany('INSERT INTO StringIds VALUES (?,?)',[(1,'kernel(float*)'),(2,'_Z6kernelPf')])
            with self.assertRaises(ValueError):probe.trace_summary(path)
            with sqlite3.connect(path) as db:db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (1,2,100,200)')
            result=probe.trace_summary(path)
            self.assertEqual(result['kernels'][0]['mangled'],'_Z6kernelPf')
            self.assertEqual(result['kernels'][0]['calls'],1)
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE ENUM_DIAGNOSTIC_SEVERITY_LEVEL (id INTEGER,name TEXT,label TEXT)')
                db.executemany('INSERT INTO ENUM_DIAGNOSTIC_SEVERITY_LEVEL VALUES (?,?,?)',[(1,'Info','Info'),(2,'Warning','Warning')])
                db.execute('CREATE TABLE DIAGNOSTIC_EVENT (severity INTEGER,text TEXT)')
                db.execute('INSERT INTO DIAGNOSTIC_EVENT VALUES (1,"Profiling has started.")')
            self.assertEqual(probe.trace_summary(path)['diagnostic_issues'],[])
            with sqlite3.connect(path) as db:db.execute('INSERT INTO DIAGNOSTIC_EVENT VALUES (2,"Missing CUDA events")')
            self.assertEqual(len(probe.trace_summary(path)['diagnostic_issues']),1)
            with sqlite3.connect(path) as db:db.execute('UPDATE DIAGNOSTIC_EVENT SET severity=1,text="Dropped CUDA events"')
            self.assertEqual(len(probe.trace_summary(path)['diagnostic_issues']),2)
            with sqlite3.connect(path) as db:db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET end=100')
            with self.assertRaises(ValueError):probe.trace_summary(path)
        with self.assertRaises(ValueError):probe.run(Path('/unused'),120,profile=True)

    def test_lt_checked_plan_and_unsupported_coverage(self):
        data=case();data['lt']=True
        data['rows']=[r for r in data['rows'] if r['family']==0 and r['Q']==14 and r['components']==1]
        for row in data['rows']:
            candidate=dict(rank=0,id=23,impl_flags=3,heuristic_state=0,check_status=0,
                           check_state=0,workspace_bytes=1024,eligible=True)
            plan=dict(heuristic_status=0,returned=1,candidates=[candidate],tensor_op_mask=1,tf32_input_mask=2,
                      alignment_bytes=[32,8,8,8],selected_rank=0,selected_id=23,selected_impl_flags=3,selected_workspace_bytes=1024)
            method=copy.deepcopy(row['methods'][2]);method.update(precision='TF32_Lt',supported=True,
                workspace_limit_bytes=64*1024*1024,plan_ms=2.,plans=[copy.deepcopy(plan) for _ in range(row['q_components'])],
                extra_fp32_workspace_bytes=(row['N']*(row['Q']*row['q_components']+row['P'])+row['P']*row['Q']*row['q_components'])*4)
            row['methods'].append(method)
        self.assertEqual(len(data['rows']),12);self.assertTrue(probe.validate_case(data))
        wmma=copy.deepcopy(data);wmma.update(wmma=True,fused=True)
        for row in wmma['rows']:
            method=copy.deepcopy(row['methods'][1]);method.update(precision='FP32_fused',extra_fp32_workspace_bytes=row['P']*row['Q']*row['q_components']*4)
            row['methods'].insert(3,method)
            if not row['transpose']:
                method=copy.deepcopy(row['methods'][2]);method.update(precision='TF32_WMMA_fused',extra_fp32_workspace_bytes=row['P']*row['Q']*row['q_components']*4,shared_bytes_per_block=18432)
                row['methods'].append(method)
        self.assertTrue(probe.validate_case(wmma))
        wmma['rows'][0]['methods'][-1]['shared_bytes_per_block']=0
        with self.assertRaises(ValueError):probe.validate_case(wmma)
        for key,value in [('impl_flags',0),('check_state',1),('workspace_bytes',65*1024*1024)]:
            bad=copy.deepcopy(data);bad['rows'][0]['methods'][-1]['plans'][0]['candidates'][0][key]=value
            with self.assertRaises(ValueError):probe.validate_case(bad)
        bad=copy.deepcopy(data);bad['rows'][0]['methods'][-1]['plans'][0]['selected_id']=24
        with self.assertRaises(ValueError):probe.validate_case(bad)
        method=data['rows'][0]['methods'][-1];method.update(supported=False)
        del method['accuracy'];del method['timing']
        plan=method['plans'][0];plan.update(returned=0,candidates=[])
        self.assertTrue(probe.validate_case(data))
        method['supported']=True
        with self.assertRaises(ValueError):probe.validate_case(data)

    def test_compensated_precision_and_linearity_coverage(self):
        data=compensated_case()
        self.assertTrue(probe.validate_case(data))
        for value in [None,{},dict(alpha=2.)]:
            bad=copy.deepcopy(data);bad['rows'][0]['methods'][-1]['linearity']=value
            with self.assertRaises(ValueError):probe.validate_case(bad)
        bad=copy.deepcopy(data);bad['rows'][0]['methods'][-1]['extra_fp32_workspace_bytes']+=1000
        with self.assertRaises(ValueError):probe.validate_case(bad)

    def test_bits_requires_independent_range_and_fault_controls(self):
        data=compensated_case(True);self.assertTrue(probe.validate_case(data))
        bad=copy.deepcopy(data);bad['tiny_error_controls']=False
        with self.assertRaises(ValueError):probe.validate_case(bad)
        for value in [None,[],data['rows'][0]['methods'][-1]['range_stress'][:-1]]:
            bad=copy.deepcopy(data);bad['rows'][0]['methods'][-1]['range_stress']=value
            with self.assertRaises(ValueError):probe.validate_case(bad)
        for key,value in [('scale',2.),('accuracy',dict(relative_l2=float('nan')))]:
            bad=copy.deepcopy(data);bad['rows'][0]['methods'][-1]['range_stress'][0][key]=value
            with self.assertRaises((ValueError,KeyError)):probe.validate_case(bad)
        # Negative numerical result is preserved as evidence, not promoted.
        bad=copy.deepcopy(data);metric=bad['rows'][0]['methods'][-1]['range_stress'][0]['accuracy']
        metric.update(relative_l2=.1,passed=False)
        self.assertTrue(probe.validate_case(bad))

    def test_fused_fourth_method_requires_small_basis_only_workspace(self):
        data=case();data['fused']=True
        for row in data['rows']:
            method=copy.deepcopy(row['methods'][1]);method['precision']='FP32_fused'
            method['extra_fp32_workspace_bytes']=row['P']*row['Q']*row['q_components']*4
            row['methods'].append(method)
        self.assertTrue(probe.validate_case(data))
        data['rows'][0]['methods'][-1]['extra_fp32_workspace_bytes']+=100000
        with self.assertRaises(ValueError):probe.validate_case(data)

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
