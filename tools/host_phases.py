"""Calibrate single-rank host scopes using labeled CUDA calls and a held-out marker."""
from decimal import Decimal
import json


class CalibrationError(ValueError):
    def __init__(self, message, diagnostics):
        super().__init__(message)
        self.diagnostics = diagnostics


def ranges(db, text):
    origins = list(db.execute('SELECT startTime FROM ANALYSIS_DETAILS'))
    processes = [(pid,local) for pid,local,name in db.execute('SELECT globalPid,pid,name FROM PROCESSES')
                 if name.endswith('/palace-x86_64.bin') or name=='palace-x86_64.bin']
    if len(origins)!=1 or len(processes)!=1:
        raise ValueError('Need one profiler clock and one native Palace process')
    pid,local = processes[0]
    main_tid = pid+local
    events,anchors = [],[]
    for line in text.splitlines():
        if line.startswith('PALACE_PROFILE_SYNC '):
            anchors.append(json.loads(line.split(' ',1)[1]))
        elif line.startswith(('PALACE_PHASE ', 'PALACE_PROFILE_RANGE ')):
            item = json.loads(line.split(' ',1)[1],parse_float=Decimal)
            stamp = item['t_ns'] if 't_ns' in item else int(item['t_s']*Decimal(1000000000))
            events.append((stamp,item['event'],item['name'].strip()))
    calls = list(db.execute('SELECT r.start,r.end,s.value FROM CUPTI_ACTIVITY_KIND_RUNTIME r '
                           'JOIN StringIds s ON s.id=r.nameId WHERE r.globalTid=? ORDER BY r.start', (main_tid,)))
    # The adapter emits version-query + synchronize; this signature labels the sync,
    # independently of clock alignment and the other synchronizations in the solver.
    labeled = [(b[0],b[1]) for a,b in zip(calls,calls[1:])
               if a[2].startswith('cudaRuntimeGetVersion') and b[2].startswith('cudaDeviceSynchronize')]
    diagnostics = dict(host_sync_brackets=anchors,labeled_cuda_sync_intervals=labeled,
                       profiler_origin_ns=origins[0][0],clock_calibration_passed=False)
    if len(anchors)<3 or len(labeled)!=len(anchors):
        raise CalibrationError('Need at least three uniquely labeled CUDA clock brackets',diagnostics)
    host_mid = [(a['begin_ns']+a['end_ns'])/2 for a in anchors]
    cuda_mid = [(a+b)/2 for a,b in labeled]
    span = cuda_mid[-1]-cuda_mid[0]
    if span<=0: raise CalibrationError('Nonpositive clock calibration span',diagnostics)
    scale = (host_mid[-1]-host_mid[0])/span
    if not 0.999<=scale<=1.001:
        raise CalibrationError('Clock rate discrepancy exceeds 1000 ppm',diagnostics)
    def mapped(t): return host_mid[0]+scale*(t-cuda_mid[0])
    residuals = [host_mid[i]-mapped(cuda_mid[i]) for i in range(len(anchors))]
    diagnostics.update(scale=scale,midpoint_residual_ns=residuals,
                       fitted_endpoints=[0,len(anchors)-1],held_out=list(range(1,len(anchors)-1)))
    # Interior markers are not used by the fit. Allow an explicit 10us measurement
    # envelope, then refuse to assign launches near phase boundaries in the caller.
    # This is diagnostic timing uncertainty, not a relaxation of RF/residual gates.
    uncertainty = 10000
    violations = [max(0,a['begin_ns']-mapped(s),mapped(e)-a['end_ns']) for a,(s,e) in zip(anchors,labeled)]
    diagnostics.update(api_containment_error_ns=violations,boundary_uncertainty_ns=uncertainty/scale)
    if max(violations)>uncertainty:
        raise CalibrationError('Clock fit fails independent CUDA call containment',diagnostics)
    def relative(t): return cuda_mid[0]+(t-host_mid[0])/scale
    stack,complete = [],[]
    for stamp,event,name in sorted(events,key=lambda r:r[0]):
        if event=='begin': stack.append((stamp,name))
        elif event=='end' and stack and stack[-1][1]==name:
            start,_ = stack.pop()
            complete.append((relative(start),relative(stamp),main_tid,name))
        else: raise CalibrationError('Unmatched host phase boundary',diagnostics)
    if stack: raise CalibrationError('Unclosed host phase boundaries',diagnostics)
    windows = [r for r in complete if r[3]=='Krylov sample']
    if len(windows)!=1: raise CalibrationError('Need exactly one host Krylov window',diagnostics)
    start,end = windows[0][:2]
    if not relative(anchors[0]['end_ns'])<=start<relative(anchors[1]['begin_ns'])<=relative(anchors[-1]['end_ns'])<=end:
        raise CalibrationError('CUDA clock brackets do not bound selected work',diagnostics)
    return complete,dict(source='affine host clock; main-thread CUDA launch attribution',
                         process_global_id=pid,main_global_tid=main_tid,
                         matched_host_ranges=len(complete),**{**diagnostics,'clock_calibration_passed':True},
                         limitations='Endpoint fit checked by interior sync markers; worker launches unassigned to main-thread scopes; GPU times may overlap')
