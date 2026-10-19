"""Bounded shared-header arithmetic/traffic probe; no Palace/GMRES qualification."""
import ctypes as ct
import json
from pathlib import Path
import resource
import time
import numpy as np


def run(output):
    started=time.monotonic()
    library=ct.CDLL('/native/libmixed_basis.so')
    pointer=ct.POINTER(ct.c_double)
    function=library.mixed_basis_probe
    function.argtypes=[ct.c_int,*([pointer]*4),ct.c_double,ct.c_double,ct.c_int,ct.c_int,
                      *([pointer]*6),ct.POINTER(ct.c_uint64)]
    function.restype=ct.c_int
    library.mixed_basis_error.restype=ct.c_char_p
    rows=[]
    for n,scaled in [(1,False),(1009,False),(131071,True),(1048576,False)]:
        rng=np.random.default_rng(721+n)
        br,bi,wr,wi=[rng.standard_normal(n) for _ in range(4)]
        if n==1:br[:]=2.;bi[:]=3.;wr[:]=5.;wi[:]=7.
        if scaled:
            scale=10.**np.linspace(-30.,30.,n)
            br*=scale;bi*=scale;wr/=scale;wi/=scale
        inputs=[np.ascontiguousarray(v,dtype=np.float64) for v in [br,bi,wr,wi]]
        outputs=[np.empty(n) for _ in range(4)]
        dots=np.empty(4);times=np.empty(2);sizes=np.empty(3,dtype=np.uint64)
        timings=[]
        trials=6 if n==1048576 else 2
        for trial in range(trials):
            code=function(n,*[v.ctypes.data_as(pointer) for v in inputs],-.375,.625,30,trial%2,
                dots.ctypes.data_as(pointer),*[v.ctypes.data_as(pointer) for v in outputs],
                times.ctypes.data_as(pointer),sizes.ctypes.data_as(ct.POINTER(ct.c_uint64)))
            if code:raise RuntimeError(library.mixed_basis_error().decode())
            timings.append(dict(order='baseline-first' if trial%2 else 'direct-first',
                                direct_ms=float(times[0]),unpack_ms=float(times[1])))
        pr=br.astype(np.float32).astype(np.longdouble);pi=bi.astype(np.float32).astype(np.longdouble)
        xr=wr.astype(np.longdouble);xi=wi.astype(np.longdouble)
        exact=np.array([np.sum(xr*pr+xi*pi),np.sum(xi*pr-xr*pi)],dtype=np.longdouble)
        denominator=np.sqrt(np.sum(xr*xr+xi*xi)*np.sum(pr*pr+pi*pi))
        dot_scale=max(denominator,np.finfo(np.longdouble).tiny)
        dot_errors=[float(np.linalg.norm(dots[i:i+2].astype(np.longdouble)-exact)/dot_scale) for i in [0,2]]
        dot_relative=[float(np.linalg.norm(dots[i:i+2].astype(np.longdouble)-exact)/max(np.linalg.norm(exact),np.finfo(np.longdouble).tiny)) for i in [0,2]]
        ref_r=xr-.375*pr-.625*pi;ref_i=xi-.375*pi+.625*pr
        norm=np.sqrt(np.sum(ref_r*ref_r+ref_i*ref_i))
        axpy_errors=[float(np.sqrt(np.sum((outputs[i].astype(np.longdouble)-ref_r)**2+
                     (outputs[i+1].astype(np.longdouble)-ref_i)**2))/norm) for i in [0,2]]
        yr=br.astype(np.longdouble);yi=bi.astype(np.longdouble)
        original=np.array([np.sum(xr*yr+xi*yi),np.sum(xi*yr-xr*yi)],dtype=np.longdouble)
        original_scale=np.sqrt(np.sum(xr*xr+xi*xi)*np.sum(yr*yr+yi*yi))
        quantization=float(np.linalg.norm(exact-original)/original_scale)
        passed=bool(max(dot_errors+dot_relative+axpy_errors)<1e-12 and quantization<2e-7 and
                    all(np.isfinite(v).all() for v in outputs) and np.isfinite(dots).all())
        rows.append(dict(n=n,scaled=scaled,dot_norm_product_scaled_errors=dot_errors,
            dot_relative_errors=dot_relative,
            axpy_relative_errors=axpy_errors,dot_quantization_norm_product_scaled_error=quantization,
            direct_dot=dots[:2].tolist(),reference_dot=[float(v) for v in exact],
            timings=timings,median_direct_ms=float(np.median([r['direct_ms'] for r in timings])),
            median_unpack_ms=float(np.median([r['unpack_ms'] for r in timings])),
            explicit_device_allocation_bytes=int(sizes[0]),reduction_workspace_bytes=int(sizes[1]),
            unpack_buffer_bytes=int(sizes[2]),arithmetic_passed=passed))
    # Invalid dimensions must be rejected before a CUDA allocation or launch.
    rejection=function(0,*[v.ctypes.data_as(pointer) for v in inputs],-.375,.625,1,0,
        dots.ctypes.data_as(pointer),*[v.ctypes.data_as(pointer) for v in outputs],
        times.ctypes.data_as(pointer),sizes.ctypes.data_as(ct.POINTER(ct.c_uint64)))
    report=dict(scope=__doc__,execution_passed=True,
        arithmetic_passed=bool(all(r['arithmetic_passed'] for r in rows) and rejection!=0),
        invalid_size_rejected=bool(rejection),storage='FP32',arithmetic='FP64',accumulation='FP64',
        tensor_cores=False,longdouble_mantissa_bits=int(np.finfo(np.longdouble).nmant),
        target=dict(same_packed_arithmetic=1e-12,norm_scaled_quantization=2e-7),rows=rows,
        elapsed_seconds=time.monotonic()-started,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        limitations=['Standalone CUDA arithmetic, no MFEM/HYPRE/MPI/GMRES integration or antenna qualification',
                    'Both modes coexist; device byte count is explicit allocations, not process peak VRAM',
                    'Timings include identical work-vector device copies; exclude allocation/transfers/JIT and are not a HYPRE comparison',
                    'Global traffic and UVM migration not profiled; no end-to-end speedup claim'])
    (output/'case.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)


if __name__=='__main__':run(Path('/work'))
