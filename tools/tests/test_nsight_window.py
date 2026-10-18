import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('nsight', Path(__file__).parents[1]/'nsight_window.py')
nsight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nsight)


class NsightTests(unittest.TestCase):
    def test_whole_process_capture_waits_for_native_cleanup(self):
        args = nsight.arguments({})
        self.assertIn('--wait=all', args)
        self.assertIn('--kill=none', args)
        self.assertFalse(any(arg.startswith('--capture-range') for arg in args))

    def test_window_rejects_oversized_and_ambiguous_values(self):
        self.assertEqual(nsight.parse_window('2:3'), (2,3))
        for value in [None, True, '', '1', '1:0', '-1:2', '33:2', '0:9', '01:2', '1:2:3', ' 1:2']:
            with self.assertRaises(ValueError): nsight.parse_window(value)

    def test_subtree_pid_is_native_target_not_collector_or_user_app(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as temporary:
            root = Path(temporary)
            for pid,name,children in [(10,'nsys','11'),(11,'nsys-launcher','12'),
                                      (12,'palace-x86_64.bin',''),(99,'palace-x86_64.bin','')]:
                path = root/str(pid); (path/'task'/str(pid)).mkdir(parents=True)
                (path/'cmdline').write_bytes(('/opt/'+name+'\0config.json').encode())
                (path/'task'/str(pid)/'children').write_text('')
                # Nsight may launch Palace from a helper thread, not its main thread.
                (path/'task'/str(pid+1000)).mkdir()
                (path/'task'/str(pid+1000)/'children').write_text(children)
            (root/'12'/'cmdline').write_bytes(b'aliased-command\0config.json')
            (root/'12'/'exe').symlink_to('/opt/palace-x86_64.bin')
            self.assertEqual(nsight.target_pid(10,root), 12)
            self.assertIsNone(nsight.target_pid(77,root))

    def test_sqlite_uses_cpu_launch_time_and_matching_process_and_thread(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as temporary:
            path = Path(temporary)/'trace.sqlite'
            pid = 16777216
            with sqlite3.connect(path) as db:
                db.executescript('''
                    CREATE TABLE StringIds(id INTEGER,value TEXT);
                    CREATE TABLE NVTX_EVENTS(start INTEGER,end INTEGER,globalTid INTEGER,text TEXT,textId INTEGER);
                    CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME(correlationId INTEGER,globalTid INTEGER,start INTEGER);
                    CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL(start INTEGER,end INTEGER,correlationId INTEGER,globalPid INTEGER,demangledName INTEGER);
                    CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY(start INTEGER,end INTEGER,copyKind INTEGER,bytes INTEGER,srcKind INTEGER,dstKind INTEGER);
                    CREATE TABLE DIAGNOSTIC_EVENT(severity INTEGER,message TEXT);
                    INSERT INTO DIAGNOSTIC_EVENT VALUES(2,'Not all CUDA events might have been collected.');
                    INSERT INTO StringIds VALUES(1,'kernel');
                    INSERT INTO CUPTI_ACTIVITY_KIND_MEMCPY VALUES(0,1,1,4096,5,5);
                ''')
                db.executemany('INSERT INTO NVTX_EVENTS VALUES(?,?,?,?,NULL)',
                               [(90,210,pid+3,'Krylov sample'),(100,200,pid+3,'Preconditioner'),
                                (130,170,pid+3,'Coarse Solve'),(145,155,pid+4,'wrong thread'),
                                (100,200,2*pid+7,'other process'),(10,20,pid+3,'setup')])
                db.executemany('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES(?,?,?)',
                               [(42,pid+3,150),(42,2*pid+7,150)])
                db.executemany('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES(?,?,?,?,1)',
                               [(900,920,42,pid),(900,930,42,2*pid),(900,940,999,pid)])
            result = nsight.sqlite_summary(path)
            phases = result['kernel_seconds_by_launch_phase']
            self.assertEqual(phases['Coarse Solve']['calls'],1)
            self.assertEqual(phases['outside NVTX ranges']['calls'],1)
            self.assertEqual(phases['unmatched CUDA launch']['calls'],1)
            self.assertNotIn('wrong thread', phases)
            self.assertNotIn('setup', {r['name'] for r in result['nvtx_ranges']})
            self.assertEqual(result['copies'][0]['bytes'],4096)
            self.assertEqual(result['diagnostics']['DIAGNOSTIC_EVENT'][0]['severity'],2)

    def test_empty_or_unrecognized_capture_is_not_success(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm') as temporary:
            path = Path(temporary)/'trace.sqlite'
            sqlite3.connect(path).close()
            with self.assertRaisesRegex(ValueError,'schema'): nsight.sqlite_summary(path)

    def test_collection_requires_clean_stop_and_rejects_sql_loss_warning(self):
        for clean, warning in [(True, False), (False, False), (True, 'loss'), (True, 'error')]:
            with self.subTest(clean=clean, warning=warning), tempfile.TemporaryDirectory(dir='/dev/shm') as temporary:
                root = Path(temporary)
                ram, output = root/'ram', root/'output'
                ram.mkdir(); output.mkdir()
                (ram/'window.sqlite').touch()
                log = 'PALACE_PROFILE_WINDOW: begin first=1 count=2\nPALACE_PROFILE_WINDOW: end first=1 count=2\n'
                if clean: log += 'PALACE_PROFILE_STOP: clean diagnostic stop; no RF qualification\n'
                (output/'palace.log').write_text(log)
                summary = dict(window_count=1,nvtx_ranges=[dict(name=name, calls=2) for name in
                                           ['Preconditioner','Krylov orthogonalization']],
                               diagnostics={'DIAGNOSTIC_EVENT': ([dict(message='Not all NVTX events might have been collected.')] if warning=='loss' else
                                                                [dict(severity=3,text='Unexpected collector failure')] if warning=='error' else [])})
                profile = dict(first=1, count=2, ram_directory=str(ram), scope='test partial')
                with patch.object(nsight, 'sqlite_summary', return_value=summary):
                    result = nsight.collect(profile, output)
                self.assertEqual(result['complete'], clean and not warning)
                self.assertFalse(ram.exists())
                self.assertTrue((output/'profile-summary.json').exists())
