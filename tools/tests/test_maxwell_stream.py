import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

AVAILABLE=importlib.util.find_spec('numpy') is not None
if AVAILABLE:
    import numpy as np
    root=Path(__file__).resolve().parents[1]/'experiments'
    def load(name):
        spec=importlib.util.spec_from_file_location(name,root/(name+'.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    near=load('maxwell_near')
    stub=types.ModuleType('numba');stub.njit=lambda **kw:lambda f:f;stub.prange=range
    with patch.dict(sys.modules,{'numba':stub}):jit=load('maxwell_near_jit')
    with patch.dict(sys.modules,{'numba':stub,'maxwell_near_jit':jit}):stream=load('maxwell_stream')


@unittest.skipUnless(AVAILABLE,'Optional NumPy; pinned oracle includes it')
class StreamKernelTests(unittest.TestCase):
    def test_point_panel_apply_matches_numpy_sum_and_depth_counts(self):
        q,w=np.polynomial.legendre.leggauss(3);q=(q+1)/2;w=w/2
        rule=(np.array([(u,(1-u)*v) for u in q for v in q]).T,np.array([a*b*(1-u) for u,a in zip(q,w) for b in w]))
        panel=(np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]),np.arange(18).reshape(2,3,3)*(1+.2j),np.array([1+.1j,2-.1j]))
        panels=[panel,(panel[0]+[3.,0.,0.],panel[1],panel[2])]
        points=np.array([[.2,.2,.15],[10.,.2,3.]])
        for radius in [0.,2.]:
            values,stats=stream.evaluate(points,stream.pack(panels),1.7,rule,rule,radius,max_depth=2)
            expected=[];selected=leaves=hits=depth=0
            for point in points:
                total=np.zeros((4,3),complex)
                for p in panels:
                    diameter=max(np.linalg.norm(p[0][a]-p[0][b]) for a,b in [(0,1),(0,2),(1,2)])
                    if np.linalg.norm(point-p[0].mean(axis=0))<radius*diameter:
                        value,s=near.adaptive(point,p,1.7,*rule,ratio=2.,max_depth=2)
                        selected+=1;leaves+=s['leaves'];hits+=s['depth_hits'];depth=max(depth,s['max_depth'])
                    else:value=near.integrate(point,p,1.7,*rule)
                    total+=value
                expected.append(total)
            np.testing.assert_allclose(values,expected,rtol=1e-12,atol=1e-12)
            self.assertEqual(stats,dict(selected_panels=selected,leaves=leaves,depth_hits=hits,max_depth=depth,regular_panels=len(points)*len(panels)-selected))

    def test_invalid_targets_limits_and_panels_rejected(self):
        with self.assertRaises(ValueError):stream.pack([])
        panel=(np.zeros((3,3)),np.zeros((2,3,3)),np.zeros(2))
        with self.assertRaises(ValueError):stream.pack([panel])
        for points in [[],[[0.,float('nan'),0.]]]:
            with self.assertRaises(ValueError):stream.evaluate(points,None,1.,None,None)
