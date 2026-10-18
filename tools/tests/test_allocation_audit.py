import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('allocation_audit', Path(__file__).parents[1]/'allocation_audit.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def event(kind, pointer, size, live):
    return 'PALACE_ALLOC ' + json.dumps(dict(event=kind, pointer=pointer, bytes=size,
                                           logical_live_bytes=live))


class AllocationAuditTests(unittest.TestCase):
    def test_peak_stack_association_and_pointer_reuse(self):
        result = module.audit([
            'KSP residual norm 1' + event('alloc', '0x1', 100, 110),
            'PALACE_ALLOC_STACK 0x1 0 /opt/libceed.so(CeedBasisApply+0x1)',
            event('alloc', '0x2', 200, 310),
            'PALACE_ALLOC_STACK 0x2 0 /opt/libcudss.so(+0x1)',
            event('free', '0x1', 100, 210), event('free', '0x2', 200, 10),
            event('alloc', '0x2', 50, 60),
            'PALACE_ALLOC_STACK 0x2 0 /unknown.so(+0x1)',
            'CUDA_UVM: peak_managed_bytes=315 live_managed_bytes=60',
        ])
        self.assertEqual(result['recovered_interleaved_events'], 1)
        self.assertEqual(result['largest_observed_event_live_bytes'], 310)
        self.assertEqual(result['reported_all_allocation_peak_bytes'], 315)
        self.assertEqual(result['unattributed_small_bytes_at_event_peak'], 10)
        self.assertEqual(result['at_event_peak_by_category']['cuDSS factors/workspace']['bytes'], 200)
        self.assertEqual(result['at_event_peak_by_category']['libCEED basis evaluation']['bytes'], 100)

    def test_insufficient_or_corrupt_trace_rejected(self):
        for lines in [[], ['PALACE_ALLOC {"bytes": 10}'],
                      [event('free', '0x1', 10, 0)],
                      [event('alloc', '0x1', 10, 10), event('alloc', '0x1', 10, 20)],
                      [event('alloc', '0x1', 10, 10), 'PALACE_ALLOC_STACK 0x2 0 frame']]:
            with self.assertRaises(ValueError):
                module.audit(lines)


if __name__ == '__main__':
    unittest.main()
