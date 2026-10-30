import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
spec = importlib.util.spec_from_file_location('stage_probe_run',
                                             Path(__file__).parents[1] / 'stage_probe_run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
cdi_identity = runner.cdi_identity


class StageProbeRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir='/dev/shm')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in ('palace','cmake','tools/adapter','build/native','run'):
            (self.root/name).mkdir(parents=True,exist_ok=True)
        (self.root/'CMakeLists.txt').write_text('compiler fixture')
        (self.root/'tools/runtime.json').write_text('{}')
        self.build = self.root/'build'
        self.run = self.root/'run'
        self.mesh = self.run/'coax.msh'
        self.mesh.write_text('mesh identity fixture only')
        self.config = {'Model': {'Mesh':'coax.msh'}, 'Problem':{'Output':'postpro'},
                       'Solver':{'Device':'GPU','Backend':'/gpu/cuda/magma'}}
        runner.dev.write(self.run/'config.json',self.config)
        self.baseline={key:'1' for key in runner.GPU_BASELINE_KEYS}
        self.baseline.update(MFEM_MEMORY='cuda',LD_PRELOAD='/opt/precision/libcudss_fp32.so',
                             PALACE_HYPRE_DEVICE_POOL_MIB='256')
        runner.dev.write(self.run/'command.json',{'actual_config_sha256':runner.dev.sha(self.run/'config.json'),
                                                 'environment':self.baseline})
        runner.dev.write(self.run/'fixture.json',{'mesh':'coax.msh',
                         'mesh_bytes':self.mesh.stat().st_size,'mesh_sha256':runner.dev.sha(self.mesh)})
        for name in runner.dev.NATIVE_PATHS:
            (self.build/'native'/name).write_text('native identity fixture only: '+name)
        self.manifest = dict(source_sha256=runner.source_hash(runner.compiler_inputs(self.root)),
                             native={name:runner.dev.sha(self.build/'native'/name) for name in runner.dev.NATIVE_PATHS},
                             settings_sha256=runner.dev.sha(self.root/'tools/runtime.json'),
                             reference_runtime_image_id=runner.IMAGE)
        runner.dev.write(self.build/'manifest.json',self.manifest)
        self.driver=self.root/'host-libcuda.so'
        self.driver.write_text('driver identity fixture only')
        self.driver_record=self.root/'driver.json'
        runner.dev.write(self.driver_record,dict(path=str(self.driver),bytes=self.driver.stat().st_size,
                                               sha256=runner.dev.sha(self.driver)))
        self.image={'Id':'sha256:'+runner.IMAGE,'Config':{'Env':['MFEM_MEMORY=cuda']}}
        mock.patch.object(runner,'cdi_identity',return_value={'path':'mock-cdi',
                          'sha256':'mock-spec-sha','readonly':True}).start()
        self.capture=mock.patch.object(runner,'capture',return_value=json.dumps([self.image])).start()
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(runner.dev,'available_memory',return_value=96*runner.GIB).start()

    def prepare(self, **kwargs):
        return runner.prepare(self.root,self.build,self.run,self.root/'out',self.driver_record,
                              stage='preprocess',**kwargs)

    def test_prepare_has_hard_guards_readonly_payload_and_no_container_creation(self):
        plan=self.prepare(cpu=True)
        self.assertEqual([call.args[0][:3] for call in self.capture.call_args_list],
                         [['podman','image','inspect']])
        args=plan['argv']
        self.assertIn('--network=none',args)
        self.assertIn('--pull=never',args)
        self.assertEqual(args[args.index('--memory')+1],args[args.index('--memory-swap')+1])
        self.assertEqual(args[args.index('--timeout')+1],'120')
        self.assertIn('core=0:0',args)
        self.assertIn('nvidia.com/gpu=all',args)
        self.assertIn('PALACE_STAGE_STOP=preprocess',args)
        self.assertIn(str(self.mesh.resolve())+':/work/coax.msh:ro',args)
        self.assertNotIn(str(self.driver)+':/lib/libcuda.so.1:ro',args)
        self.assertTrue(plan['identity']['cdi']['readonly'])
        for name,destination in runner.dev.NATIVE_PATHS.items():
            self.assertIn(f'{self.build/"native"/name}:{destination}:ro',args)
        self.assertEqual(json.loads((self.root/'out/config.json').read_text())['Solver']['Device'],'CPU')
        self.assertEqual(json.loads((self.run/'config.json').read_text())['Solver']['Device'],'GPU')
        self.assertFalse(plan['rf_result'])

    def test_adapter_preload_is_scoped_after_env_entrypoint_not_to_env_itself(self):
        plan=self.prepare()
        argv=plan['argv']; image_index=argv.index(runner.IMAGE)
        preload='LD_PRELOAD=/opt/precision/libcudss_fp32.so'
        self.assertNotIn(preload,argv[:image_index])
        self.assertEqual(argv[image_index+1],preload)
        self.assertEqual(argv[image_index+2],'/opt/palace-cudss/bin/palace-x86_64.bin')

    def test_rejects_deadline_and_memory_overbudget_and_unsafe_cpu_threads(self):
        for seconds,memory,threads,cpu,free in [(301,8,1,False,96), (120,71,1,False,96),
                                                (120,8,2,True,96),(120,70,1,False,77),
                                                (120.5,8,1,False,96)]:
            with self.subTest(seconds=seconds,memory=memory,threads=threads,free=free):
                with self.assertRaises(ValueError):
                    runner.validate_policy('preprocess',seconds,memory,threads,cpu,free*runner.GIB)
        runner.validate_policy('operators',300,70,1,False,78*runner.GIB)

    def test_cdi_requires_exact_readonly_host_driver_mapping(self):
        spec=self.root/'nvidia.yaml'
        valid='kind: nvidia.com/gpu\n  - hostPath: '+str(self.driver)+'\n    containerPath: '+str(self.driver)+'\n    options:\n      - ro\n'
        spec.write_text(valid)
        self.assertTrue(cdi_identity(self.driver,spec)['readonly'])
        for invalid in [valid.replace('- ro','- rw'),valid.replace('containerPath: '+str(self.driver),'containerPath: /other')]:
            spec.write_text(invalid)
            with self.assertRaisesRegex(ValueError,'mounted read-only'):
                cdi_identity(self.driver,spec)

    def test_gpu_preserves_every_baseline_flag_and_freezes_environment_hash(self):
        plan=self.prepare()
        for key,value in self.baseline.items():
            self.assertEqual(plan['environment'][key],value)
        self.assertEqual(plan['identity']['baseline_environment_sha256'],
                         runner.environment_hash(self.baseline))
        self.assertEqual(plan['identity']['command_sha256'],runner.dev.sha(self.run/'command.json'))
        self.assertEqual(plan['environment']['PALACE_STAGE_STOP'],'preprocess')
        self.assertNotIn('PALACE_PHASE_TRACE',plan['environment'])

    def test_stage_trace_off_is_default_even_with_host_environment_set(self):
        with mock.patch.dict(os.environ, {'PALACE_STAGE_TRACE':'1'}):
            plan=self.prepare()
        self.assertFalse(plan['stage_trace'])
        self.assertNotIn('PALACE_STAGE_TRACE',plan['environment'])
        self.assertNotIn('PALACE_STAGE_TRACE=1',plan['argv'])
        expected=runner.make_environment('preprocess',1,False,self.baseline)
        self.assertEqual(plan['environment'],expected)

    def test_stage_trace_is_only_an_explicit_extra_flag_without_config_drift(self):
        plan=self.prepare(stage_trace=True)
        self.assertTrue(plan['stage_trace'])
        self.assertEqual(plan['environment']['PALACE_STAGE_TRACE'],'1')
        self.assertIn('PALACE_STAGE_TRACE=1',plan['argv'])
        ordinary=runner.make_environment('preprocess',1,False,self.baseline)
        self.assertEqual({k:v for k,v in plan['environment'].items() if k!='PALACE_STAGE_TRACE'},ordinary)
        self.assertEqual(plan['staged_config_sha256'],plan['identity']['config_sha256'])
        self.assertEqual(plan['identity']['baseline_environment'],self.baseline)
        self.assertEqual(plan['identity']['baseline_environment_sha256'],runner.environment_hash(self.baseline))

    def test_changed_stage_trace_fingerprint_is_rejected_before_execution(self):
        plan=self.prepare()
        plan['stage_trace']=True
        runner.dev.write(self.root/'out/plan.json',plan)
        with self.assertRaisesRegex(ValueError,'command/environment changed'):
            runner.execute(self.root/'out/plan.json')
        self.assertEqual(len(self.capture.call_args_list),1)

    def test_trace_cannot_be_inherited_from_baseline_or_passed_as_a_string(self):
        command=runner.dev.read(self.run/'command.json')
        command['environment']['PALACE_STAGE_TRACE']='1'
        runner.dev.write(self.run/'command.json',command)
        with self.assertRaisesRegex(ValueError,'reviewed whitelist'):
            self.prepare(stage_trace=True)
        with self.assertRaisesRegex(ValueError,'explicit boolean'):
            runner.make_environment('preprocess',1,False,self.baseline,'1')

    def test_gpu_rejects_inherited_history_or_profiling_flags(self):
        command=runner.dev.read(self.run/'command.json')
        command['environment']['PALACE_HISTORY_FIELDS']='/history'
        runner.dev.write(self.run/'command.json',command)
        with self.assertRaisesRegex(ValueError,'reviewed whitelist'):
            self.prepare()
        self.assertFalse((self.root/'out').exists())

    def test_cpu_controlled_override_does_not_inherit_history(self):
        command=runner.dev.read(self.run/'command.json')
        command['environment']['PALACE_HISTORY_FIELDS']='/history'
        runner.dev.write(self.run/'command.json',command)
        plan=self.prepare(cpu=True)
        self.assertNotIn('PALACE_HISTORY_FIELDS',plan['environment'])
        self.assertEqual(plan['environment']['MFEM_MEMORY'],'host')

    def test_changed_archived_environment_and_source_are_detected(self):
        plan=self.prepare()
        command=runner.dev.read(self.run/'command.json')
        command['environment']['PALACE_CUDSS_TRACK']='0'
        runner.dev.write(self.run/'command.json',command)
        observed,_=runner.identity(self.root,self.build,self.run,self.driver_record)
        self.assertNotEqual(observed['baseline_environment_sha256'],plan['identity']['baseline_environment_sha256'])
        self.assertNotEqual(observed['command_sha256'],plan['identity']['command_sha256'])
        mock.patch.object(runner,'no_inference',return_value={}).start()
        with self.assertRaisesRegex(ValueError,'Prepared inputs changed'):
            runner._execute(plan,self.root/'out')
        self.assertEqual(len(self.capture.call_args_list),1)  # prepare image inspect only
        (self.root/'palace/new.cpp').write_text('source changed')
        with self.assertRaisesRegex(ValueError,'Compiler inputs'):
            runner.identity(self.root,self.build,self.run,self.driver_record)

    def test_gpu_telemetry_parses_values_and_keeps_unavailable_as_null(self):
        query=mock.Mock(returncode=0,stdout='2026/10/30 01:00:00, GPU-id, 120, 5, 30.0, 900\n',stderr='')
        with mock.patch.object(runner.subprocess,'run',return_value=query):
            sample=runner.gpu_sample()
        self.assertEqual(sample['devices'][0]['utilization_percent'],5)
        self.assertEqual(sample['devices'][0]['memory_used_mib'],120)
        query.stdout='2026/10/30 01:00:00, GPU-id, N/A, N/A, N/A, N/A\n'
        with mock.patch.object(runner.subprocess,'run',return_value=query):
            sample=runner.gpu_sample()
        self.assertIsNone(sample['devices'][0]['memory_used_mib'])

    def test_native_drift_fails_before_image_or_container_command(self):
        (self.build/'native/libpalace.so').write_text('changed')
        with self.assertRaisesRegex(ValueError,'Native checksums'):
            self.prepare()
        self.capture.assert_not_called()

    def test_refuses_plan_command_mutation_and_repeated_execution(self):
        plan=self.prepare()
        plan['argv'].remove('--network=none')
        runner.dev.write(self.root/'out/plan.json',plan)
        with self.assertRaisesRegex(ValueError,'command/environment changed'):
            runner.execute(self.root/'out/plan.json')
        runner.dev.write(self.root/'out/diagnostic-result.json',{'complete':False})
        with self.assertRaisesRegex(ValueError,'existing execution result'):
            runner.execute(self.root/'out/plan.json')

    def test_inference_name_guard_detects_python_and_native_servers(self):
        proc=self.root/'proc';proc.mkdir()
        for pid,name,command in [(1,'strata',b'/bin/strata\0'),
                                 (2,'python',b'python\0-m\0vllm.entrypoints.openai.api_server\0'),
                                 (3,'python',b'python\0/work/strata_server.py\0'),
                                 (4,'unrelated',b'/bin/other\0')]:
            (proc/str(pid)).mkdir();(proc/str(pid)/'comm').write_text(name)
            (proc/str(pid)/'cmdline').write_bytes(command)
        self.assertEqual({x['pid'] for x in runner.inference_processes(proc)}, {1,2,3})

    def test_prototype_features_are_explicit_and_canonical(self):
        self.assertNotIn('PALACE_PROBE_LOCATOR', self.prepare(cpu=True)['environment'])
        # A new output is required for each prepared case.
        import shutil
        shutil.rmtree(self.root/'out')
        flags={'PALACE_PROBE_LOCATOR':'mfem','PALACE_SINGLE_RANK_DIRECT_MESH':'1'}
        plan=self.prepare(cpu=True,features=flags)
        self.assertEqual(plan['features'], flags)
        for key,value in flags.items():
            self.assertEqual(plan['environment'][key],value)
            self.assertIn(key+'='+value, plan['argv'])
        plan['features']['PALACE_PROBE_LOCATOR']='gslib'
        runner.dev.write(self.root/'out/plan.json',plan)
        with self.assertRaisesRegex(ValueError,'command/environment changed'):
            runner.execute(self.root/'out/plan.json')

    def test_distinct_worktrees_share_a_real_exclusive_host_lock(self):
        import shutil
        shared = self.root/'shared-runtime/host.lock'
        shared.parent.mkdir()
        other = self.root/'other-source'
        other.mkdir()
        for directory in ('palace','cmake','tools'):
            shutil.copytree(self.root/directory,other/directory)
        shutil.copyfile(self.root/'CMakeLists.txt',other/'CMakeLists.txt')
        with mock.patch.object(runner,'host_lock_path',return_value=shared):
            first=self.prepare(cpu=True)
            second=runner.prepare(other,self.build,self.run,self.root/'second-out',
                                  self.driver_record,stage='preprocess',cpu=True)
            self.assertNotEqual(first['source'],second['source'])
            self.assertEqual(first['host_lock'],second['host_lock'])
            with shared.open('a') as held:
                runner.fcntl.flock(held,runner.fcntl.LOCK_EX|runner.fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    runner.execute(self.root/'second-out/plan.json')

    def test_unknown_prototype_features_are_rejected(self):
        for flags in [{'PALACE_STAGE_STOP':'operators'}, {'PALACE_PROBE_LOCATOR':'fast'},
                      {'PALACE_SINGLE_RANK_DIRECT_MESH':True}, ['mfem']]:
            with self.subTest(flags=flags),self.assertRaises(ValueError):
                runner.checked_features(flags)

    def full_prepare(self, **kwargs):
        with mock.patch.object(runner,'full_expectations',return_value={'fixture':'completion schema'}):
            return runner.prepare(self.root,self.build,self.run,self.root/'out',self.driver_record,
                                  stage='full',**kwargs)

    def test_full_prepare_is_explicit_gpu_trace_off_without_stage_stop_or_config_changes(self):
        flags={'PALACE_PROBE_LOCATOR':'mfem','PALACE_SINGLE_RANK_DIRECT_MESH':'1'}
        plan=self.full_prepare(seconds=1800,memory_gib=70,features=flags)
        self.assertFalse(plan['diagnostic_only']);self.assertFalse(plan['rf_qualified'])
        self.assertEqual(plan['configuration_changes'],{})
        self.assertEqual((self.root/'out/config.json').read_bytes(),(self.run/'config.json').read_bytes())
        self.assertNotIn('PALACE_STAGE_STOP',plan['environment'])
        self.assertNotIn('PALACE_STAGE_TRACE',plan['environment'])
        self.assertEqual({k:v for k,v in plan['environment'].items() if k in runner.GPU_BASELINE_KEYS},self.baseline)
        self.assertEqual(plan['features'],flags)
        self.assertEqual(plan['argv'][plan['argv'].index('--timeout')+1],'1800')
        self.assertFalse(any('PALACE_STAGE_STOP=' in x or 'PALACE_STAGE_TRACE=' in x for x in plan['argv']))
        self.assertEqual([call.args[0][:3] for call in self.capture.call_args_list],
                         [['podman','image','inspect']])
        plan['environment']['PALACE_STAGE_STOP']='operators'
        runner.dev.write(self.root/'out/plan.json',plan)
        with self.assertRaisesRegex(ValueError,'command/environment changed'):
            runner.execute(self.root/'out/plan.json')

    def test_full_cpu_trace_threads_and_resource_bounds_are_rejected(self):
        for seconds,memory,threads,cpu,trace in [(1801,8,1,False,False),(0,8,1,False,False),
                (1800,71,1,False,False),(1800,8,2,False,False),
                (1800,8,1,True,False),(1800,8,1,False,True)]:
            with self.subTest(seconds=seconds,memory=memory,threads=threads,cpu=cpu,trace=trace):
                with self.assertRaises(ValueError):
                    runner.validate_policy('full',seconds,memory,threads,cpu,96*runner.GIB,trace)
        runner.validate_policy('full',1800,70,1,False,78*runner.GIB,False)
        for cpu,threads,trace in [(True,1,False),(False,2,False),(False,1,True)]:
            with self.assertRaises(ValueError):runner.make_environment('full',threads,cpu,self.baseline,trace)

    def test_full_native_completion_uses_separate_result_and_cleanup(self):
        plan=self.full_prepare()
        state={'Pid':0,'StartedAt':'2026-10-30T00:00:00Z','OOMKilled':False}
        inspection={'State':state,'Image':runner.IMAGE,'Mounts':[],
                    'HostConfig':{'Memory':8*runner.GIB,'MemorySwap':8*runner.GIB}}
        def capture(argv):
            if argv[:3]==['podman','image','inspect']:return 'sha256:'+runner.IMAGE
            if argv[:2]==['podman','inspect']:return json.dumps([inspection])
            if argv[:2]==['podman','create']:return 'own-container-id'
            raise AssertionError(argv)
        self.capture.side_effect=capture
        def launch(*args,**kwargs):
            kwargs['stderr'].write('PALACE_LOG_BUFFERING: stdout=line\n');kwargs['stderr'].flush()
            process=mock.Mock();process.poll.return_value=0;process.wait.return_value=0
            return process
        full={'complete':True,'diagnostic_only':False,'solver_executed':True,'rf_qualified':False}
        with mock.patch.object(runner,'no_inference',return_value={}), \
             mock.patch.object(runner,'full_expectations',return_value=plan['full_expectations']), \
             mock.patch.object(runner,'check_full',return_value=full) as checked, \
             mock.patch.object(runner,'helper_hashes',return_value=plan['helper_sha256']), \
             mock.patch.object(runner.subprocess,'Popen',side_effect=launch), \
             mock.patch.object(runner.subprocess,'run',return_value=mock.Mock(returncode=0)) as cleanup:
            result=runner.execute(self.root/'out/plan.json')
        self.assertTrue(result['complete']);self.assertTrue(result['solver_executed'])
        self.assertFalse(result['diagnostic_only']);self.assertFalse(result['rf_qualified'])
        self.assertTrue(result['own_container_removed']);checked.assert_called_once()
        cleanup.assert_called_once()
        self.assertTrue((self.root/'out/full-result.json').is_file())
        self.assertFalse((self.root/'out/diagnostic-result.json').exists())
        with self.assertRaisesRegex(ValueError,'existing execution result'):
            runner.execute(self.root/'out/plan.json')

    def mocked_execution(self, failure):
        plan=self.prepare()
        inspection={'State':{'Pid':0},'Image':runner.IMAGE,'Mounts':[],
                    'HostConfig':{'Memory':8*runner.GIB,'MemorySwap':8*runner.GIB}}
        def capture(argv):
            if argv[:3]==['podman','image','inspect']: return 'sha256:'+runner.IMAGE
            if argv[:2]==['podman','inspect']: return json.dumps([inspection])
            if argv[:2]==['podman','create']: return 'own-container-id'
            raise AssertionError(argv)
        self.capture.side_effect=capture
        mock.patch.object(runner,'no_inference',return_value={}).start()
        process=mock.Mock();process.poll.return_value=None;process.wait.return_value=0
        mock.patch.object(runner.subprocess,'Popen',return_value=process).start()
        cleanup=mock.patch.object(runner.subprocess,'run',return_value=mock.Mock(returncode=0)).start()
        if failure=='memory':
            mock.patch.object(runner.dev,'available_memory',side_effect=[96*runner.GIB,5*runner.GIB]).start()
        else:
            mock.patch.object(runner.time,'monotonic',side_effect=[0,0,400,400]).start()
        with self.assertRaises(TimeoutError): runner._execute(plan,self.root/'out')
        cleanup.assert_called_once()
        self.assertEqual(cleanup.call_args.args[0],['podman','rm','--force',plan['name']])
        report=json.loads((self.root/'out/diagnostic-result.json').read_text())
        self.assertFalse(report['complete']);self.assertFalse(report['rf_result'])
        self.assertTrue(report['own_container_removed'])

    def test_memory_guard_cleans_only_owned_container_and_records_failure(self):
        self.mocked_execution('memory')

    def test_outer_deadline_cleans_only_owned_container_and_records_failure(self):
        self.mocked_execution('deadline')


if __name__=='__main__': unittest.main()
