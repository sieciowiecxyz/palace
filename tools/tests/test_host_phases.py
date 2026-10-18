import importlib.util
import json
from pathlib import Path
import sqlite3
import unittest

spec = importlib.util.spec_from_file_location('host_phases',Path(__file__).parents[1]/'host_phases.py')
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


class HostPhaseTests(unittest.TestCase):
    def fixture(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.executescript('''
            CREATE TABLE ANALYSIS_DETAILS(startTime INTEGER);
            INSERT INTO ANALYSIS_DETAILS VALUES(1000);
            CREATE TABLE PROCESSES(globalPid INTEGER,pid INTEGER,name TEXT);
            INSERT INTO PROCESSES VALUES(16777216,3,'/opt/palace-x86_64.bin');
            CREATE TABLE StringIds(id INTEGER,value TEXT);
            INSERT INTO StringIds VALUES(1,'cudaDeviceSynchronize_v3020');
            INSERT INTO StringIds VALUES(2,'cudaRuntimeGetVersion_v3020');
            CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME(start INTEGER,end INTEGER,globalTid INTEGER,nameId INTEGER);
            INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES(8,9,16777219,2),(10,20,16777219,1),
                (58,59,16777219,2),(60,70,16777219,1),(88,89,16777219,2),(90,100,16777219,1);
        ''')
        events = [(1001,'begin','Linear Solve'),(1030,'begin','Krylov sample'),
                  (1040,'begin','Preconditioner'),(1045,'begin','Coarse Solve'),
                  (1055,'end','Coarse Solve'),(1060,'end','Preconditioner'),
                  (1065,'begin','Krylov orthogonalization'),(1080,'end','Krylov orthogonalization'),
                  (1110,'end','Krylov sample'),(1120,'end','Linear Solve')]
        log = '\n'.join('PALACE_PROFILE_RANGE '+json.dumps(dict(t_ns=t,event=e,name=n)) for t,e,n in events)
        log += '\nPALACE_PROFILE_SYNC '+json.dumps(dict(begin_ns=1009,end_ns=1021))
        log += '\nPALACE_PROFILE_SYNC '+json.dumps(dict(begin_ns=1059,end_ns=1071))
        log += '\nPALACE_PROFILE_SYNC '+json.dumps(dict(begin_ns=1089,end_ns=1101))
        return db,log

    def test_independent_sync_brackets_validate_host_clock_and_complete_scopes(self):
        db,log = self.fixture()
        scopes,metadata = host.ranges(db,log)
        self.assertTrue(metadata['clock_calibration_passed'])
        self.assertEqual(metadata['matched_host_ranges'],5)
        self.assertIn((45,55,16777219,'Coarse Solve'),scopes)
        self.assertEqual(len(metadata['host_sync_brackets']),3)
        self.assertEqual(metadata['held_out'],[1])

    def test_origin_offset_is_calibrated_instead_of_assumed_identical(self):
        db,log = self.fixture()
        db.execute('UPDATE ANALYSIS_DETAILS SET startTime=99999999999')
        _,metadata = host.ranges(db,log)
        self.assertTrue(metadata['clock_calibration_passed'])
        self.assertEqual(metadata['scale'],1)

    def test_held_out_marker_rejects_nonlinear_clock_error_beyond_envelope(self):
        db,log = self.fixture()
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=start*10000,end=end*10000')
        rows = []
        for line in log.splitlines():
            prefix,payload = line.split(' ',1)
            item = json.loads(payload)
            for key in ['t_ns','begin_ns','end_ns']:
                if key in item: item[key] *= 10000
            rows.append(prefix+' '+json.dumps(item))
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=start+40000,end=end+40000 WHERE start=600000')
        with self.assertRaisesRegex(ValueError,'containment'): host.ranges(db,'\n'.join(rows))

    def test_decimal_seconds_and_padded_names_match_integer_ns(self):
        db,log = self.fixture()
        replacement = 'PALACE_PHASE {"event":"begin","name":"  Preconditioner","t_s":0.000001040}'
        log = '\n'.join(replacement if '"t_ns": 1040,' in line else line for line in log.splitlines())
        scopes,_ = host.ranges(db,log)
        self.assertIn((40,60,16777219,'Preconditioner'),scopes)

    def test_wrong_clock_missing_cuda_and_unclosed_scopes_rejected(self):
        for failure in ['clock','missing_cuda','unclosed','wrong_tid']:
            with self.subTest(failure=failure):
                db,log = self.fixture()
                if failure=='clock': db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=20070,end=20080 WHERE start=60')
                if failure=='missing_cuda': db.execute('DELETE FROM CUPTI_ACTIVITY_KIND_RUNTIME')
                if failure=='wrong_tid': db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET globalTid=16777220')
                if failure=='unclosed': log = '\n'.join(line for line in log.splitlines() if not ('1120' in line))
                with self.assertRaises(ValueError): host.ranges(db,log)
