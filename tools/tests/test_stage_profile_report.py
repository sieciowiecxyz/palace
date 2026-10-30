import json
import unittest
from tools.stage_profile_report import summarize, PREFIX


def event(kind, name, stamp, wall=None):
    row = dict(event=kind, name=name, t_ns=stamp)
    if wall is not None:
        row['wall_s'] = wall
    return PREFIX+json.dumps(row)+'\n'


class TraceTest(unittest.TestCase):
    def test_nested_is_not_double_counted(self):
        text = event('begin', 'outer', 0)+event('begin', 'inner', 1_000_000_000)
        text += event('end', 'inner', 3_000_000_000, 2)+event('end', 'outer', 5_000_000_000, 5)
        report = summarize(text)
        self.assertEqual(report['covered_host_s'], 5)
        self.assertEqual(report['phases'][0]['exclusive_s'], 3)
        self.assertEqual(report['phases'][0]['inclusive_s'], 5)

    def test_repeated_scopes_aggregate(self):
        text = ''.join(event('begin', 'read', i*2_000_000_000)+event('end', 'read', i*2_000_000_000+1_000_000_000, 1) for i in range(3))
        report = summarize(text)
        self.assertEqual(report['phases'][0]['count'], 3)
        self.assertEqual(report['covered_host_s'], 3)

    def test_incomplete_or_inconsistent_trace_is_rejected(self):
        cases = ['', event('begin', 'a', 0), event('end', 'a', 0, 0),
                 event('begin', 'a', 0)+event('end', 'b', 1_000_000_000, 1),
                 event('begin', 'a', 0)+event('end', 'a', 1_000_000_000, 2)]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(ValueError):
                summarize(text)
