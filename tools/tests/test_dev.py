import importlib.util
import json
import struct
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('palace_dev', Path(__file__).parents[1] / 'dev.py')
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


class ToolRegressionTests(unittest.TestCase):
    def test_native_partial_profile_stops_in_first_solve_without_weakening_full_coverage(self):
        self.assertEqual(dev.native_coarse_builds(6, False, None),6)
        self.assertEqual(dev.native_coarse_builds(6, False, {'first':30,'count':2}),1)
        self.assertEqual(dev.native_coarse_builds(2, True, None),1)
        log='PALACE_NATIVE_COMPLEX_COARSE: dimension=20 nnz=100 dtype=complex_fp32 matrix=general\n'
        self.assertTrue(dev.native_complex_coarse_applied(log,dev.native_coarse_builds(6,False,{'first':0}), 'complex_fp32'))
        self.assertFalse(dev.native_complex_coarse_applied(log,dev.native_coarse_builds(6,False,None),'complex_fp32'))

    def test_native_mixed_guards_and_observed_precision_cleanup(self):
        dev.validate_native_mixed(False, False, None, False, None, None)
        dev.validate_native_mixed(True, True, None, False, None, None)
        dev.validate_native_mixed(True, True, None, False, '0:2', None)
        for args in [(True, False, None, False, None, None), (True, True, 512, False, None, None),
                     (True, True, None, True, None, None),
                     (True, True, None, False, None, 2)]:
            with self.assertRaisesRegex(ValueError, 'Native mixed'): dev.validate_native_mixed(*args)
        marker = 'PALACE_NATIVE_COMPLEX_COARSE: dimension=20 nnz=100 dtype=complex_fp32 matrix=general\n'
        self.assertTrue(dev.native_complex_coarse_applied(marker,1,'complex_fp32'))
        self.assertFalse(dev.native_complex_coarse_applied(marker,1))
        log = ('PALACE_NATIVE_MIXED_SCALE: min=0.1 max=10 corrections=2 original=complex_fp64\n'
               'PALACE_NATIVE_MIXED_COARSE: solves=20 corrections=2 max_relative_residual=1e-8 backend=cuda_fp64\n'
               'CUDSS_MEMORY: precision=fp32 managed=1 peak_bytes=100 live_bytes=0 allocations=2\n')
        self.assertTrue(dev.native_mixed_applied(log,1))
        for bad in ['', log+log, log.replace('corrections=2','corrections=1'),
                    log.replace('solves=20','solves=0'), log.replace('1e-8','NaN'),
                    log.replace('1e-8','0.002'), log.replace('live_bytes=0','live_bytes=1'),
                    log.replace('min=0.1','min=0'), log.replace('max=10','max=inf'),
                    log.replace('precision=fp32','precision=fp64'), log.replace('managed=1','managed=0'),
                    log.replace('peak_bytes=100','peak_bytes=0'), log.replace('allocations=2','allocations=0'),
                    log+'PALACE_NATIVE_MIXED_COARSE: malformed\n',
                    log+'PALACE_NATIVE_MIXED_SCALE: malformed\n']:
            self.assertFalse(dev.native_mixed_applied(bad,1))

    def test_ams_changes_preconditioner_only_and_preserves_physics(self):
        _, info, original = dev.fixture('coax-tiny')
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        changed = dev.ams_config(original, 2)
        self.assertEqual(original['Solver']['Linear']['Type'], 'cuDSS')
        self.assertEqual(changed['Solver']['Linear']['Type'], 'AMS')
        for key in ['PCMatReal', 'PCMatShifted']:
            self.assertIs(changed['Solver']['Linear'][key], True)
        self.assertIs(changed['Solver']['Linear']['ComplexCoarseSolve'], False)
        self.assertEqual(changed['Solver']['Linear']['AMSMaxIts'], 2)
        for key in ['Tol', 'MaxIts', 'MaxSize', 'KSPType']:
            self.assertEqual(original['Solver']['Linear'][key], changed['Solver']['Linear'][key])
        self.assertEqual(dev.field_identity(changed, info, build), dev.field_identity(original, info, build))
        dev.validate_ams(None, True)
        dev.validate_ams(2, False, None)
        for cycles in [0, 5, True, 2.0, '2']:
            with self.assertRaisesRegex(ValueError, 'AMS'):
                dev.validate_ams(cycles)
        for option in [True, 256]:
            with self.assertRaisesRegex(ValueError, 'AMS'):
                dev.validate_ams(2, option)

    def test_ams_audit_requires_fixed_device_policy_and_no_cudss(self):
        cfg = 'PALACE_AMS_GPU_CONFIG: cycles=2 tolerance=0 memory_device=1 execution_device=1\n'
        op = 'PALACE_AMS_OPERATOR: dimension=123 cycle_type=14\n'
        self.assertTrue(dev.ams_applied(cfg+op+cfg+op, 2, 2))
        for text in ['', cfg+op, cfg+op+op, (cfg+op)*3,
                     (cfg+op)*2+'CUDSS_MEMORY:',
                     (cfg+op).replace('memory_device=1', 'memory_device=0')*2,
                     (cfg+op).replace('dimension=123', 'dimension=0')*2,
                     (cfg+op).replace('cycles=2', 'cycles=1')*2]:
            self.assertFalse(dev.ams_applied(text, 2, 2))

    def test_native_hybrid_guards_and_actual_configuration_coverage(self):
        dev.validate_native_hybrid(None, False, False, None)
        dev.validate_native_hybrid(256, True, False, None)
        for args in [(True, True, False, None), (255, True, False, None),
                     (16385, True, False, None), (256, False, False, None),
                     (256, True, True, None), (256, True, False, '0:2')]:
            with self.assertRaisesRegex(ValueError, 'Native hybrid'):
                dev.validate_native_hybrid(*args)
        marker = 'PALACE_NATIVE_HYBRID: limit_bytes=268435456 minimum_device_bytes=123 estimated_host_bytes=456\n'
        cleanup = 'CUDSS_MEMORY: precision=fp64 managed=0 peak_bytes=1024 live_bytes=0 allocations=1\n'
        self.assertTrue(dev.native_hybrid_applied(marker+cleanup, 256, 1))
        for text in [marker, cleanup, marker+marker+cleanup,
                     marker+cleanup.replace('managed=0', 'managed=1'),
                     marker+cleanup.replace('live_bytes=0', 'live_bytes=1'),
                     marker.replace('minimum_device_bytes=123', 'minimum_device_bytes=268435457')+cleanup]:
            self.assertFalse(dev.native_hybrid_applied(text, 256, 1))

    def test_deferred_postprocess_requires_safe_two_port_single_frequency_batch(self):
        _, _, config = dev.fixture('tshaped-medium')
        config = dev.port_batch_config(config, True)
        dev.validate_deferred_postprocessing(config, True)
        for release in [False]:
            with self.assertRaisesRegex(ValueError, 'Deferred'):
                dev.validate_deferred_postprocessing(config, release)
        changes = [lambda c: c['Solver']['Driven'].update(Restart=2),
                   lambda c: c['Solver']['Driven'].update(Save=1),
                   lambda c: c['Solver']['Driven']['Samples'][0]['Freq'].append(3.8),
                   lambda c: c['Boundaries']['LumpedPort'][0].update(Excitation=False),
                   lambda c: c['Boundaries'].update(WavePort=[{}]),
                   lambda c: c['Model'].update(Refinement={'MaxIts': 1})]
        for change in changes:
            candidate = json.loads(json.dumps(config)); change(candidate)
            with self.assertRaisesRegex(ValueError, 'Deferred'):
                dev.validate_deferred_postprocessing(candidate, True)

    def test_deferred_postprocess_requires_exact_order_after_solver_release(self):
        _, _, config = dev.fixture('tshaped-medium')
        config = dev.port_batch_config(config, True)
        store = 'PALACE_DEFERRED_POSTPROCESS: action=store excitation=1 frequency_index=0 logical_bytes=123\n'
        release = 'PALACE_FINAL_SOLVER_RELEASED: enabled=1\n'
        first = 'PALACE_DEFERRED_POSTPROCESS: action=measure excitation=1 frequency_index=0\n'
        second = 'PALACE_DEFERRED_POSTPROCESS: action=measure excitation=2 frequency_index=0\n'
        self.assertTrue(dev.deferred_postprocessing_applied(store+release+first+second, config))
        for log in ['', store+release, store+first+release+second,
                    release+store+first+second, store+release+second+first,
                    store+release+first+second+second]:
            self.assertFalse(dev.deferred_postprocessing_applied(log, config))

    def test_energy_workspace_release_requires_release_and_rebuild_for_every_transition(self):
        _,_,config=dev.fixture('tshaped-medium');config=dev.port_batch_config(config,True)
        release='PALACE_POSTPROCESS_ENERGY_RELEASED: excitation=1 frequency_index=0\n'
        rebuild='PALACE_POSTPROCESS_ENERGY_REBUILT: excitation=2 frequency_index=0\n'
        self.assertTrue(dev.postprocess_energy_release_applied(release+rebuild,config))
        for log in ['',release,rebuild,release+release+rebuild,release+rebuild.replace('excitation=2','excitation=1')]:
            self.assertFalse(dev.postprocess_energy_release_applied(log,config))

    def test_partial_initial_fields_preserve_strict_reference_and_physics_checks(self):
        _,info,target=dev.fixture('coax-tiny')
        source=json.loads(json.dumps(target));source['Boundaries']['LumpedPort'][0]['Excitation']=False
        build={'runtime_base_id':'runtime','builder_image_id':'builder'}
        with tempfile.TemporaryDirectory(dir='/dev/shm') as temporary:
            root=Path(temporary);(root/'fields').mkdir()
            for name in dev.expected_field_files(source):
                (root/'fields'/name).write_bytes(struct.pack('<8sQdd',b'PALF64V1',1,1.,0.))
            for name,value in [('config',source),('fixture',info),('build-manifest',build),('result',{'complete':True})]:
                dev.write(root/(name+'.json'),value)
            dev.write(root/'command.json',{'actual_config_sha256':dev.sha(root/'config.json')})
            dev.write(root/'fields.json',{'identity':dev.field_identity(source,info,build),'complete':True,
                'files':dev.field_inventory(root/'fields',dev.expected_field_files(source))})
            self.assertEqual(dev.verified_partial_initial_fields(root,target,info,build),root)
            with self.assertRaises(ValueError):dev.verified_field_reference(root,target,info,build)
            with self.assertRaises(ValueError):dev.verified_initial_fields(root,target,info,build)
            changed=json.loads(json.dumps(target));changed['Boundaries']['LumpedPort'][0]['R']=75.
            with self.assertRaises(ValueError):dev.verified_partial_initial_fields(root,changed,info,build)
            changed=json.loads(json.dumps(source));changed['Boundaries']['LumpedPort'][1]['Excitation']=False
            with self.assertRaises(ValueError):dev.verified_partial_initial_fields(root,changed,info,build)
            dev.write(root/'result.json',{'complete':False})
            with self.assertRaises(ValueError):dev.verified_partial_initial_fields(root,target,info,build)
            dev.write(root/'result.json',{'complete':True})
            next((root/'fields').iterdir()).write_bytes(struct.pack('<8sQdd',b'PALF64V1',1,2.,0.))
            with self.assertRaisesRegex(ValueError,'bytes changed'):
                dev.verified_partial_initial_fields(root,target,info,build)

    def test_partial_seed_requires_explicit_zero_for_unseeded_rhs(self):
        _,_,target=dev.fixture('coax-tiny');source=json.loads(json.dumps(target))
        source['Boundaries']['LumpedPort'][0]['Excitation']=False
        seeded=''.join(f'PALACE_FIELD_RESTART: excitation=2 frequency_index={f} norm_E=1.0e-2\n' for f in range(3))
        zero=''.join(f'PALACE_FIELD_RESTART_ZERO: excitation=1 frequency_index={f}\n' for f in range(3))
        self.assertTrue(dev.field_restart_applied(seeded+zero,target,source))
        self.assertFalse(dev.field_restart_applied(seeded,target,source))
        self.assertFalse(dev.field_restart_applied(seeded+zero+zero,target,source))
        self.assertFalse(dev.field_restart_applied(seeded+zero,target))
        with patch.object(dev,'require_host_memory') as host:
            with self.assertRaises(ValueError):dev.run('coax-tiny','/unused',60,partial_initial_fields=True)
            host.assert_not_called()

    def test_both_port_batch_changes_only_excitation_requests(self):
        _,_,config=dev.fixture('tshaped-medium')
        updated=dev.port_batch_config(config,both_ports=True,reuse=True)
        self.assertFalse(config['Boundaries']['LumpedPort'][0]['Excitation'])
        for old,new in zip(config['Boundaries']['LumpedPort'],updated['Boundaries']['LumpedPort']):
            self.assertEqual({k:v for k,v in old.items() if k!='Excitation'},
                             {k:v for k,v in new.items() if k!='Excitation'})
            self.assertEqual(new['Excitation'],new['Index'])
        self.assertEqual(config['Model'],updated['Model'])
        self.assertEqual(config['Solver'],updated['Solver'])
        self.assertEqual(dev.expected_field_files(updated),{
            f's{e}-f0-{v}.bin' for e in [1,2] for v in ['E','B']})
        selected=dev.port_batch_config(updated,excitation=2)
        self.assertEqual(selected,config)
        for value in [True,0,3,2.5]:
            with self.assertRaises(ValueError):dev.port_batch_config(updated,excitation=value)
        with self.assertRaises(ValueError):dev.port_batch_config(updated,both_ports=True,excitation=2)

    def test_port_reuse_rejects_unqualified_operator_batches(self):
        _,_,config=dev.fixture('tshaped-medium')
        with self.assertRaises(ValueError):dev.port_batch_config(config,reuse=True)
        good=dev.port_batch_config(config,both_ports=True,reuse=True)
        for kind in ['frequency','wave','floquet','refinement','restart','sameexcitation','bool']:
            bad=json.loads(json.dumps(good))
            if kind=='frequency':bad['Solver']['Driven']['Samples'][0]['Freq'].append(3.8)
            if kind=='wave':bad['Boundaries']['WavePort']=[{}]
            if kind=='floquet':bad['Boundaries']['FloquetPort']=[{}]
            if kind=='refinement':bad['Model']['Refinement']={'MaxIts':1}
            if kind=='restart':bad['Solver']['Driven']['Restart']=2
            if kind=='sameexcitation':bad['Boundaries']['LumpedPort'][1]['Excitation']=1
            if kind=='bool':bad['Boundaries']['LumpedPort'][1]['Excitation']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError):dev.port_batch_config(bad,reuse=True)

    def test_port_setup_audit_requires_actual_factorizations_and_rhs_coverage(self):
        _,_,config=dev.fixture('tshaped-medium');config=dev.port_batch_config(config,True,True)
        csr='PALACE_COARSE_CSR: algorithm=fnv1a64 structure=0123456789abcdef values=0123456789abcdef\n'
        time='PALACE_COARSE_SETUP: analysis_s=1.0e-2 factor_s=1.1e-2\n'
        build='PALACE_PORT_SETUP: action=build excitation=1 frequency_index=0\n'
        reuse='PALACE_PORT_SETUP: action=reuse excitation=2 frequency_index=0\n'
        log=csr+time+build+reuse
        self.assertTrue(dev.port_setup_audit(log,config,True)['passed'])
        self.assertFalse(dev.port_setup_audit(log,config,False)['passed'])
        for bad in [log.replace(reuse,''),log.replace(csr,''),log.replace(time,''),log+csr,
                    log.replace('factor_s=1.1e-2','factor_s=nan'),log.replace('excitation=2','excitation=3')]:
            self.assertFalse(dev.port_setup_audit(bad,config,True)['passed'])
        control=csr+time+build+csr+time+reuse.replace('action=reuse','action=build')
        self.assertTrue(dev.port_setup_audit(control,config,False)['passed'])

    def test_port_setup_flags_require_native_coarse_before_resource_allocation(self):
        with patch.object(dev,'require_host_memory') as host:
            for flags in [dict(setup_audit=True),dict(port_setup_reuse=True),
                          dict(setup_audit=True,native_complex_coarse=True,nsys_window='0:2')]:
                with self.assertRaises(ValueError):dev.run('coax-tiny','/unused',60,**flags)
            host.assert_not_called()

    def test_prefetch_requires_direct_cuda_before_resource_allocation(self):
        with patch.object(dev, 'require_host_memory') as host:
            for flags in [dict(), dict(basis='fp64'), dict(direct_basis=True,cpu_reference=True)]:
                with self.assertRaises(ValueError):
                    dev.run('coax-tiny','/unused',60,basis_prefetch=True,**flags)
            host.assert_not_called()
        with patch.object(dev,'require_host_memory',side_effect=RuntimeError('resource gate')):
            with self.assertRaisesRegex(RuntimeError,'resource gate'):
                dev.run('coax-tiny','/unused',60,direct_basis=True,basis_prefetch=True)

    def test_direct_prefetch_profile_is_explicit_diagnostic_not_field_qualification(self):
        from types import SimpleNamespace
        profiler=SimpleNamespace(parse_window=lambda value: (30,2), verified_tool=lambda: {})
        import sys
        with patch.dict(sys.modules, {'nsight_window':profiler}), patch.object(
                dev,'require_host_memory',side_effect=RuntimeError('resource gate')):
            with self.assertRaisesRegex(RuntimeError,'resource gate'):
                dev.run('tshaped-medium','/unused',1800,direct_basis=True,basis_prefetch=True,nsys_window='30:2')
            for flags in [dict(),dict(direct_basis=True,save_fields=True),dict(direct_basis=True,coax_l2=True)]:
                with self.assertRaises(ValueError):
                    dev.run('coax-tiny','/unused',60,nsys_window='30:2',**flags)

    def test_prefetch_requires_positive_actual_markers_per_solve(self):
        marker='PALACE_BASIS_PREFETCH: managed=true stream=0 calls=10 requested_bytes=80\n'
        self.assertTrue(dev.basis_prefetch_applied(marker*2,2))
        for log,count in [(marker,2),(marker*3,2),('',0),
                          (marker.replace('calls=10','calls=0'),1),
                          (marker.replace('requested_bytes=80','requested_bytes=0'),1),
                          (marker.replace('managed=true','managed=false'),1),
                          (marker.replace('stream=0','stream=1'),1)]:
            self.assertFalse(dev.basis_prefetch_applied(log,count))

    def test_one_coax_frequency_is_from_frozen_sweep_and_keeps_both_ports(self):
        _,_,config=dev.fixture('coax-medium')
        for frequency in [3.3,3.55,3.8]:
            selected=dev.diagnostic_config('coax-medium',json.loads(json.dumps(config)),coax_fields=True,coax_frequency=frequency)
            self.assertEqual(selected['Solver']['Driven']['Samples'],[{'Type':'Point','Freq':[frequency]}])
            self.assertEqual(selected['Boundaries'],config['Boundaries'])
        for frequency in [0.,2.4,float('nan'),True]:
            with self.assertRaises(ValueError):
                dev.diagnostic_config('coax-medium',json.loads(json.dumps(config)),coax_fields=True,coax_frequency=frequency)
        with self.assertRaises(ValueError):
            dev.diagnostic_config('coax-medium',json.loads(json.dumps(config)),coax_fields=True,preserve_coax_sweep=True,coax_frequency=3.3)

    def test_coax_diagnostics_preserve_three_frequency_sweep_only_if_explicit(self):
        _,_,config=dev.fixture('coax-medium')
        expected=json.loads(json.dumps(config['Solver']['Driven']))
        selected=dev.diagnostic_config('coax-medium',json.loads(json.dumps(config)),coax_fields=True)
        kept=dev.diagnostic_config('coax-medium',json.loads(json.dumps(config)),coax_fields=True,preserve_coax_sweep=True)
        self.assertEqual(kept['Solver']['Driven'],expected)
        self.assertEqual(len(kept['Domains']['Postprocessing']['Probe']),18)
        self.assertNotEqual(selected['Solver']['Driven'],expected)
        with patch.object(dev,'require_host_memory') as host:
            for name,kwargs in [('tshaped-medium',dict(coax_l2=True)),('coax-medium',{})]:
                with self.assertRaises(ValueError):dev.run(name,'/unused',60,coax_sweep=True,**kwargs)
            host.assert_not_called()

    def test_direct_fp32_native_coarse_is_explicit_and_reaches_resource_guard(self):
        with patch.object(dev,'require_host_memory',side_effect=RuntimeError('resource gate')):
            with self.assertRaisesRegex(RuntimeError,'resource gate'):
                dev.run('coax-medium','/unused',180,basis='fp32',direct_basis=True,native_complex_coarse=True)

    def test_direct_basis_rejects_fp64_before_allocation(self):
        with patch.object(dev,'require_host_memory') as host:
            with self.assertRaisesRegex(ValueError,'requires FP32'):
                dev.run('coax-tiny',Path('/unused'),60,basis='fp64',direct_basis=True)
            host.assert_not_called()

    def test_native_complex_coarse_is_explicit_and_requires_gpu_cudss(self):
        _, info, config = dev.fixture('coax-tiny')
        old = json.loads(json.dumps(config))
        updated = dev.diagnostic_config('coax-tiny', config, native_complex_coarse=True)
        self.assertTrue(updated['Solver']['Linear']['ComplexCoarseSolve'])
        self.assertFalse(updated['Solver']['Linear']['PCMatShifted'])
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        self.assertEqual(dev.field_identity(updated, info, build), dev.field_identity(old, info, build))
        with self.assertRaises(ValueError):
            dev.diagnostic_config('coax-tiny', config, cpu_reference=True, native_complex_coarse=True)
        old['Solver']['Linear']['Type'] = 'AMS'
        with self.assertRaises(ValueError):
            dev.diagnostic_config('coax-tiny', old, native_complex_coarse=True)
        for flags in [dict(basis='fp32'), dict(basis='fp64', cpu_reference=True), dict(basis='fp64', ceed_qpool=True)]:
            with patch.object(dev, 'verified_build', side_effect=AssertionError('must not start')):
                with self.assertRaises(ValueError):
                    dev.run('coax-tiny', '/unused', 60, native_complex_coarse=True, **flags)

    def test_native_coarse_marker_requires_exact_coverage_and_dtype(self):
        log = 'PALACE_NATIVE_COMPLEX_COARSE: dimension=20 nnz=100 dtype=complex_fp64 matrix=general\n'
        self.assertTrue(dev.native_complex_coarse_applied(log*6, 6))
        self.assertFalse(dev.native_complex_coarse_applied(log*5, 6))
        self.assertFalse(dev.native_complex_coarse_applied(log*7, 6))
        self.assertFalse(dev.native_complex_coarse_applied(log.replace('complex_fp64', 'real_fp64'), 1))
        self.assertFalse(dev.native_complex_coarse_applied(log.replace('dimension=20', 'dimension=0'), 1))

    def test_complex_coarse_preserves_operator_and_explicitly_disables_shift(self):
        _, info, config = dev.fixture('coax-tiny')
        original = json.loads(json.dumps(config))
        updated = dev.diagnostic_config('coax-tiny', config, complex_coarse=True)
        self.assertTrue(updated['Solver']['Linear']['ComplexCoarseSolve'])
        self.assertFalse(updated['Solver']['Linear']['PCMatShifted'])
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        self.assertEqual(dev.field_identity(updated, info, build), dev.field_identity(original, info, build))
        with patch.object(dev, 'verified_build', side_effect=AssertionError('must not start')):
            with self.assertRaises(ValueError):
                dev.run('coax-tiny', '/unused', 60, basis='fp64', cpu_reference=True, complex_coarse=True)

    def test_cpu_reference_requires_real_host_device_backend_and_one_execute_marker(self):
        log = ('Device configuration: omp,cpu\nlibCEED backend: /cpu/self/avx/blocked\n'
               'CUDSS_HYBRID_EXECUTE: enabled=1\nPALACE_CUDSS_SERIAL_RHS: enabled=1\n')
        self.assertTrue(dev.cpu_reference_applied(log))
        self.assertFalse(dev.cpu_reference_applied(log.replace('omp,cpu', 'cuda,omp,cpu')))
        self.assertFalse(dev.cpu_reference_applied(log.replace('/cpu/self/avx/blocked', '/gpu/cuda/magma')))
        self.assertFalse(dev.cpu_reference_applied(log.replace('enabled=1', 'enabled=0')))
        self.assertFalse(dev.cpu_reference_applied(log.replace('PALACE_CUDSS_SERIAL_RHS: enabled=1\n', '')))
        self.assertFalse(dev.cpu_reference_applied(log + log))

    def test_cpu_reference_is_explicit_same_physics_and_rejects_other_precision(self):
        _, info, config = dev.fixture('coax-tiny')
        original = json.loads(json.dumps(config))
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        updated = dev.diagnostic_config('coax-tiny', config, cpu_reference=True)
        self.assertEqual(updated['Solver']['Device'], 'CPU')
        self.assertEqual(updated['Solver']['Backend'], '/cpu/self')
        self.assertEqual(dev.field_identity(updated, info, build), dev.field_identity(original, info, build))
        with patch.object(dev, 'verified_build', side_effect=AssertionError('must not start')):
            with self.assertRaisesRegex(ValueError, 'requires FP64'):
                dev.run('coax-tiny', '/unused', 60, cpu_reference=True)
            with self.assertRaisesRegex(ValueError, 'without GPU'):
                dev.run('coax-tiny', '/unused', 60, basis='fp64', cpu_reference=True, ceed_qpool=True)

    def test_explicit_restart_controls_preserve_physics_and_require_field_coverage(self):
        _, info, config = dev.fixture('coax-tiny')
        original = json.loads(json.dumps(config))
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        for size in [0, 241, True, 3.5]:
            with self.assertRaisesRegex(ValueError, '1..240'):
                dev.diagnostic_config('coax-tiny', config, krylov_size=size)
        updated = dev.diagnostic_config('coax-tiny', config, pc_side='right',
                                        krylov_size=64, initial_fields=True)
        self.assertEqual(updated['Solver']['Linear']['MaxSize'], 64)
        self.assertTrue(updated['Solver']['Linear']['InitialGuess'])
        self.assertEqual(updated['Solver']['Linear']['PCSide'], 'Right')
        self.assertEqual(updated['Solver']['Linear']['Tol'], original['Solver']['Linear']['Tol'])
        self.assertEqual(dev.field_identity(updated, info, build), dev.field_identity(original, info, build))
        log = ''.join(f'PALACE_FIELD_RESTART: excitation={s} frequency_index={f} norm_E=1.0e-2\n'
                      for s in [1, 2] for f in range(3))
        self.assertTrue(dev.field_restart_applied(log, config))
        self.assertFalse(dev.field_restart_applied(log + log, config))
        self.assertFalse(dev.field_restart_applied(log.replace('excitation=2', 'excitation=3'), config))
        self.assertFalse(dev.field_restart_applied(log.replace('norm_E=1.0e-2', 'norm_E=NaN', 1), config))

    def test_reference_tolerance_cannot_weaken_fixture_or_use_nonfinite_values(self):
        _, _, config = dev.fixture('coax-tiny')
        for value in [True, 0, 1e-15, 1e-5, float('nan'), float('inf'), '1e-12']:
            with self.assertRaisesRegex(ValueError, 'no weaker'):
                dev.diagnostic_config('coax-tiny', config, linear_tol=value)
        original = json.loads(json.dumps(config))
        changed = dev.diagnostic_config('coax-tiny', config, linear_tol=1e-12)
        original['Solver']['Linear']['Tol'] = 1e-12
        self.assertEqual(changed, original)

    def test_separate_capture_preserves_partial_stdout_diagnostic(self):
        # A delayed stdout suffix must not be split by an intervening stderr line.
        script = ('import os; '
                  'os.write(1, b"PALACE_KSP_CHECK: absolute="); '
                  'os.write(2, b"PALACE_MEMORY_PHASE {}\\n"); '
                  'os.write(1, b"1e-7 relative_initial=1e-7 threshold=1e-6\\n")')
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            with (work/'palace.stdout.log').open('wb') as stdout, \
                 (work/'palace.stderr.log').open('wb') as stderr:
                dev.command([dev.sys.executable, '-c', script], stdout=stdout, stderr=stderr)
            dev.combine_run_logs(work)
            text = (work/'palace.log').read_text()
            self.assertIn('PALACE_KSP_CHECK: absolute=1e-7 relative_initial=1e-7 threshold=1e-6\n', text)
            self.assertIn('PALACE_MEMORY_PHASE {}\n', text)
            self.assertIn('not global event order', text)
            self.assertNotIn('PALACE_MEMORY_PHASE', (work/'palace.stdout.log').read_text())

    def test_memory_phases_require_coverage_order_and_sensible_peaks(self):
        labels = ['setup.begin', 'setup.end', 'operators.begin', 'preconditioner.begin',
                  'preconditioner.end', 'gmres.begin', 'gmres.basis_release.begin',
                  'gmres.basis_release.end', 'gmres.end', 'postprocess.begin',
                  'field_diagnostics.begin', 'field_diagnostics.end', 'postprocess.end', 'driven.end']
        events = []
        previous = 'unmarked'
        for i, label in enumerate(labels):
            events.append(dict(to=label, **{'from': previous}, t_s=i, elapsed_s=1,
                               managed_live_bytes=10, managed_interval_peak_bytes=20,
                               managed_process_peak_bytes=30, cudss_live_bytes=5))
            previous = label
        def log(items):
            return '\n'.join('interleaved stdout PALACE_MEMORY_PHASE ' + json.dumps(e) for e in items)
        self.assertTrue(dev.memory_phase_report(log(events), 1, fields=True, release=True)['complete'])
        self.assertFalse(dev.memory_phase_report(log(events), 1, release_final=True)['complete'])
        self.assertFalse(dev.memory_phase_report(log(events[:-1]), 1, fields=True, release=True)['complete'])
        self.assertFalse(dev.memory_phase_report(log(events), 2, fields=True, release=True)['complete'])
        broken = json.loads(json.dumps(events))
        broken[5]['managed_live_bytes'] = 100
        self.assertFalse(dev.memory_phase_report(log(broken), 1, fields=True, release=True)['complete'])
        broken = json.loads(json.dumps(events))
        broken[5]['from'] = 'wrong phase'
        self.assertFalse(dev.memory_phase_report(log(broken), 1, fields=True, release=True)['complete'])

    def test_final_workspace_phase_is_required_exactly_once(self):
        labels = ['setup.begin', 'setup.end', 'operators.begin']
        solve = ['preconditioner.begin', 'preconditioner.end', 'gmres.begin', 'gmres.end']
        post = ['postprocess.begin', 'postprocess.end']
        labels += solve + post + solve + ['linear_workspace_release.begin',
                                         'linear_workspace_release.end'] + post + ['driven.end']
        def report(names):
            previous = 'unmarked'
            events = []
            for i, label in enumerate(names):
                events.append('PALACE_MEMORY_PHASE ' + json.dumps(dict(
                    to=label, **{'from': previous}, t_s=i, elapsed_s=1,
                    managed_live_bytes=10, managed_interval_peak_bytes=20,
                    managed_process_peak_bytes=30, cudss_live_bytes=5)))
                previous = label
            return dev.memory_phase_report('\n'.join(events), 2, release_final=True)
        self.assertTrue(report(labels)['complete'])
        self.assertFalse(report(labels[:-1])['complete'])
        doubled = labels[:-1] + ['linear_workspace_release.begin',
                                 'linear_workspace_release.end', 'driven.end']
        self.assertFalse(report(doubled)['complete'])

    def test_process_gpu_memory_uses_only_own_pid_and_real_units(self):
        query = type('Query', (), dict(returncode=0, stdout='9, 4000\n42, 256\n'))()
        with patch.object(dev.subprocess, 'run', return_value=query):
            self.assertEqual(dev.process_gpu_memory(42), 256*1024**2)
            self.assertIsNone(dev.process_gpu_memory(7))
            self.assertIsNone(dev.process_gpu_memory(0))
        query.stdout = '42, [N/A]\n'
        with patch.object(dev.subprocess, 'run', return_value=query):
            self.assertIsNone(dev.process_gpu_memory(42))
        with patch.object(dev.subprocess, 'run', side_effect=dev.subprocess.TimeoutExpired('nvidia-smi', 5)):
            self.assertIsNone(dev.process_gpu_memory(42))

    def test_qpool_generator_rejects_unpinned_source(self):
        spec = importlib.util.spec_from_file_location('qpool', Path(__file__).parents[1]/'experiments/ceed_qpool.py')
        qpool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qpool)
        with self.assertRaisesRegex(ValueError, 'Pinned libCEED source changed'):
            qpool.generate('unverified upstream source')

    def test_invalid_hypre_pool_is_rejected_before_gpu(self):
        with patch.object(dev, 'require_host_memory', side_effect=AssertionError('must not start')):
            for size in [0, 15, 4097, -1, '256', True]:
                with self.assertRaisesRegex(ValueError, '16 to 4096'):
                    dev.run('coax-tiny', '/unused', 60, hypre_pool_mib=size)

    def test_low_host_memory_refuses_gpu_before_build(self):
        with patch.object(dev, 'available_memory', return_value=5*1024**3), \
             patch.object(dev, 'verified_build', side_effect=AssertionError('must not start')):
            with self.assertRaisesRegex(ValueError, 'GPU run not started'):
                dev.run('coax-tiny', '/unused', 60)
        with patch.object(dev, 'available_memory', return_value=6*1024**3):
            self.assertEqual(dev.require_host_memory(), 6*1024**3)

    def test_qpool_manifest_rejects_wrong_inputs_or_library(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root/'build/ceed-qpool'
            directory.mkdir(parents=True)
            (root/'tools/experiments').mkdir(parents=True)
            recipe = root/'tools/experiments/ceed_qpool.py'
            recipe.write_text('recipe')
            library = directory/'libceed_qpool.so'
            library.write_bytes(b'prototype')
            native = dict(builder_image_id='builder', runtime_base_id='runtime')
            metadata = dict(recipe={recipe.name: dev.sha(recipe)}, builder='builder', runtime='runtime',
                            library_sha256=dev.sha(library), runtime_library_path='/opt/software/libceed/lib/libceed.so')
            dev.write(directory/'manifest.json', metadata)
            with patch.object(dev, 'ROOT', root):
                self.assertEqual(dev.verified_qpool(native), (directory, metadata))
                library.write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'stale/tampered'):
                    dev.verified_qpool(native)
                library.write_bytes(b'prototype')
                recipe.write_text('changed')
                with self.assertRaisesRegex(ValueError, 'stale/tampered'):
                    dev.verified_qpool(native)
                recipe.write_text('recipe')
                with self.assertRaisesRegex(ValueError, 'stale/tampered'):
                    dev.verified_qpool(dict(builder_image_id='wrong', runtime_base_id='runtime'))
                dev.write(directory/'manifest.json', {**metadata, 'runtime_library_path': '/unexpected/libceed.so'})
                with self.assertRaisesRegex(ValueError, 'Unexpected'):
                    dev.verified_qpool(native)

    def test_disk_basis_is_rejected_before_build_or_gpu(self):
        with patch.object(dev, 'verified_build', side_effect=AssertionError('must not start')):
            for basis in ['fp32-disk', 'fp64-disk']:
                with self.assertRaisesRegex(ValueError, 'RAM/VRAM'):
                    dev.run('coax-tiny', '/unused', 60, basis=basis)

    def test_cgroup_memory_samples_and_disappearance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(dev.cgroup_memory(root), {})
            (root/'memory.current').write_text('1024\n')
            (root/'memory.peak').write_text('4096\n')
            (root/'memory.stat').write_text('anon 512\nfile 256\nshmem 128\nother 10\n')
            self.assertEqual(dev.cgroup_memory(root), {'current_bytes': 1024, 'peak_bytes': 4096,
                                                     'anon_bytes': 512, 'file_bytes': 256, 'shmem_bytes': 128})
            (root/'memory.current').write_text('invalid')
            self.assertEqual(dev.cgroup_memory(root), {})
        self.assertEqual(dev.cgroup_memory(None), {})

    def test_field_reference_rejects_wrong_physics_corruption_and_unfinished_run(self):
        _, info, config = dev.fixture('coax-tiny')
        build = {'runtime_base_id': 'runtime', 'builder_image_id': 'builder'}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'fields').mkdir()
            for name in dev.expected_field_files(config):
                (root/'fields'/name).write_bytes(struct.pack('<8sQdd', b'PALF64V1', 1, 1.0, 0.0))
            for name, value in [('config.json', config), ('fixture.json', info),
                                ('build-manifest.json', build), ('result.json', {'complete': True})]:
                dev.write(root/name, value)
            dev.write(root/'command.json', {'actual_config_sha256': dev.sha(root/'config.json')})
            dev.write(root/'fields.json', {'identity': dev.field_identity(config, info, build),
                                          'complete': True,
                                          'files': dev.field_inventory(root/'fields', dev.expected_field_files(config))})
            dev.verified_field_reference(root, config, info, build)
            changed = json.loads(json.dumps(config))
            changed['Domains']['Materials'][0]['Permittivity'] = 4.4
            with self.assertRaisesRegex(ValueError, 'different physics'):
                dev.verified_field_reference(root, changed, info, build)
            with self.assertRaisesRegex(ValueError, 'different physics'):
                dev.verified_initial_fields(root, changed, info, build)
            dev.write(root/'result.json', {'complete': False})
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                dev.verified_field_reference(root, config, info, build)
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                dev.verified_initial_fields(root, config, info, build)
            dev.write(root/'result.json', {'complete': True, 'field_accuracy_passed': False})
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                dev.verified_field_reference(root, config, info, build)
            # Failed accuracy may seed a new solve but must remain rejected as a reference.
            self.assertEqual(dev.verified_initial_fields(root, config, info, build), root)
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                dev.verified_field_reference(root, config, info, build)
            dev.write(root/'result.json', {'complete': True})
            path = root/'fields'/sorted(dev.expected_field_files(config))[0]
            path.write_bytes(struct.pack('<8sQdd', b'PALF64V1', 1, 2.0, 0.0))
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                dev.verified_field_reference(root, config, info, build)
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                dev.verified_initial_fields(root, config, info, build)

    def test_field_comparison_requires_all_solves_regions_and_finite_errors(self):
        _, _, config = dev.fixture('coax-tiny')
        config = dev.diagnostic_config('coax-tiny', config, True)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def log(values):
                (root/'palace.log').write_text(''.join(
                    f'PALACE_FIELD_COMPARE: excitation={p} frequency_index=0 region=-1 '
                    f'relative_E={v} relative_B={v}\n' for p,v in values))
            log([(1, '1e-5'), (2, '1e-5')])
            self.assertTrue(dev.field_comparisons(root, config)['passed'])
            for values in [[(1, '1e-5')], [(1, 'nan'), (2, '0')], [(1, '0.02'), (2, '0')],
                           [(1, '-0.01'), (2, '0')], [(1, '0'), (1, '0'), (2, '0')]]:
                log(values)
                self.assertFalse(dev.field_comparisons(root, config)['passed'])

    def test_tiny_diagnostic_keeps_medium_and_scales_probe_positions(self):
        _, _, config = dev.fixture('coax-tiny')
        linear = config['Solver']['Linear'].copy()
        derived = dev.diagnostic_config('coax-tiny', config, True, 'right')
        self.assertEqual(derived['Solver']['Linear'], {**linear, 'PCSide': 'Right'})
        self.assertEqual(derived['Solver']['Driven']['Samples'], [{'Type': 'Point', 'Freq': [3.55]}])
        probes = derived['Domains']['Postprocessing']['Probe']
        self.assertEqual(len(probes), 18)
        self.assertEqual(sorted(set(p['Center'][2] for p in probes)), [0.5, 1.0, 1.5])
        with self.assertRaisesRegex(ValueError, 'coax fixture'):
            dev.diagnostic_config('tshaped-medium', {}, True)

    def test_real_archives_and_medium_contract(self):
        for name in dev.CASES:
            directory, info, config = dev.fixture(name)
            self.assertEqual(config['Model']['Mesh'], info['mesh'])
            self.assertTrue(all((directory / part).stat().st_size < 100_000_000 for part in info['archive_parts']))

    def test_changed_archive_and_escaping_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / 'examples/test'
            directory.mkdir(parents=True)
            (directory / 'mesh.zst').write_bytes(b'corrupted')
            dev.write(directory / 'fixture.json', {'mesh': 'mesh.msh', 'archive_parts': ['mesh.zst'], 'archive_sha256': 'bad'})
            with patch.object(dev, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Corrupt'):
                    dev.fixture('test')
                dev.write(directory / 'fixture.json', {'mesh': '../../escape', 'archive_parts': ['mesh.zst']})
                with self.assertRaisesRegex(ValueError, 'escapes'):
                    dev.fixture('test')

    def test_stale_or_tampered_binary_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build = root / 'build'
            (build / 'native').mkdir(parents=True)
            binary = build / 'native/palace.bin'
            binary.write_bytes(b'reference')
            settings = root / 'settings.json'
            settings.write_text('{}')
            dev.write(build / 'manifest.json', {'source_sha256': 'source', 'settings_sha256': dev.sha(settings),
                                              'native': {'palace.bin': dev.sha(binary)}})
            with patch.object(dev, 'BUILD', build), patch.object(dev, 'SETTINGS', settings), patch.object(dev, 'source_hash', return_value='source'):
                dev.verified_build()
                binary.write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'binary changed'):
                    dev.verified_build()
            with patch.object(dev, 'BUILD', build), patch.object(dev, 'SETTINGS', settings), patch.object(dev, 'source_hash', return_value='new source'):
                with self.assertRaisesRegex(ValueError, 'Sources/settings changed'):
                    dev.verified_build()

    def test_new_source_file_invalidates_fingerprint_but_docs_do_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'palace').mkdir()
            (root / 'CMakeLists.txt').write_text('project(example)')
            with patch.object(dev, 'ROOT', root):
                first = dev.source_hash()
                (root / 'README.md').write_text('docs')
                self.assertEqual(dev.source_hash(), first)
                (root / 'palace/new.cpp').write_text('int main() {}')
                self.assertNotEqual(dev.source_hash(), first)

    def test_incomplete_frequency_coverage_or_missing_solve_is_not_success(self):
        config = {'Problem': {'Output': 'postpro'}, 'Solver': {'Driven': {'Samples': [{'Freq': [3.3, 3.8]}]}},
                  'Boundaries': {'LumpedPort': [{'Excitation': True}]}}
        # Exact writer prefix from palace/linalg/iterative.cpp; the missing colon
        # formerly made a completed real GPU run appear incomplete.
        good = 'GMRES solver converged in 10 iterations\nPALACE_KSP_CHECK: absolute=1e-7 relative_initial=1e-7 threshold=1e-6\n'
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'postpro').mkdir()
            (work / 'palace.log').write_text(good * 2)
            csv = work / 'postpro/port-S.csv'
            csv.write_text(' f (GHz), |S[1][1]| (dB)\n3.3,-20\n3.8,-20\n')
            self.assertTrue(dev.validate_output(work, config, 0)['complete'])
            self.assertFalse(dev.validate_output(work, config, 143)['complete'])
            (work / 'palace.log').write_text(good)
            self.assertFalse(dev.validate_output(work, config, 0)['complete'])
            (work / 'palace.log').write_text(good * 2)
            csv.write_text(' f (GHz), |S[1][1]| (dB)\n3.3,-20\n')
            self.assertFalse(dev.validate_output(work, config, 0)['complete'])

    def test_failed_independent_stopping_check_is_not_success(self):
        config = {'Problem': {'Output': 'postpro'}, 'Solver': {'Driven': {'Samples': [{'Freq': [3.5]}]}},
                  'Boundaries': {'LumpedPort': [{'Excitation': True}]}}
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'postpro').mkdir()
            (work / 'postpro/port-S.csv').write_text('f (GHz)\n3.5\n')
            (work / 'palace.log').write_text('GMRES solver converged in 10 iterations\nPALACE_KSP_CHECK: absolute=2.0 relative_initial=0.2 threshold=1e-6\n')
            self.assertFalse(dev.validate_output(work, config, 0)['complete'])


if __name__ == '__main__':
    unittest.main()
