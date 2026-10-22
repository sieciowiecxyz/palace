"""Small local distribution around the existing pinned runtime; no compiler/cloud.

The OCI image stays in the local Podman store. Moving hosts requires transferring
that image once, not uploading its dependency layers with every simulation.
"""
from pathlib import Path
import re
import shutil

import dev


def checked_reference(reference, manifest):
    if reference is None:
        raise ValueError('Bundle requires --reference: a verified full-FP64 coax-tiny3.55GHz run')
    reference = Path(reference).resolve()
    config = dev.read(reference/'config.json')
    info = dev.read(reference/'fixture.json')
    expected = dev.fixture('coax-tiny')[1]
    if (info != expected or dev.read(reference/'build-manifest.json') != manifest or
            config['Solver']['Driven']['Samples'] != [{'Type': 'Point', 'Freq': [3.55]}]):
        raise ValueError('Bundle reference must match the current build and coax-tiny3.55GHz fixture')
    dev.verified_field_reference(reference, config, info, manifest)
    log = (reference/'palace.log').read_text()
    if not (dev.validate_output(reference, config, 0)['complete'] and
            dev.native_complex_coarse_applied(log, 2, 'complex_fp64') and
            dev.port_setup_audit(log, config, False)['passed']):
        raise ValueError('Bundle reference must have complete fresh two-port FP64 execution')
    env = dev.read(reference/'command.json')['environment']
    if any(k in env for k in ['PALACE_GMRES_FP32_BASIS', 'PALACE_NATIVE_COARSE_FP32',
                              'PALACE_REUSE_PORT_SETUP', 'PALACE_INITIAL_FIELDS', 'PALACE_HISTORY_FIELDS']):
        raise ValueError('Bundle reference is not cold full FP64')
    raw = [float(v) for v in re.findall(r'PALACE_TRUE_RESIDUAL: norm_Ax_minus_b=[\deE+.-]+ norm_b=[\deE+.-]+ relative=([\deE+.-]+)', log)]
    if len(raw) != 2 or not all(0 <= x <= 1e-6 for x in raw):
        raise ValueError('Bundle reference fails original raw residual')
    return reference


def inventory(root):
    return {str(p.relative_to(root)): dev.sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and p.name != 'bundle-manifest.json'}


def verify(root):
    root = Path(root).resolve()
    manifest = dev.read(root/'bundle-manifest.json')
    if manifest.get('schema') != 1 or not manifest.get('files'):
        raise ValueError('Invalid bundle manifest')
    for relative, expected in manifest['files'].items():
        path = root/relative
        if not path.resolve().is_relative_to(root) or path.is_symlink() or not path.is_file() or dev.sha(path) != expected:
            raise ValueError('Bundle payload changed or escaped: ' + relative)
    if manifest['build_manifest_sha256'] != dev.sha(root/'build/sm120/manifest.json'):
        raise ValueError('Bundle build manifest changed')
    return manifest


def create(output, reference, manifest, runtime):
    reference = checked_reference(reference, manifest)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc', '*.unpacking')
    # Include compiler inputs for source_hash verification, never dependency caches
    # or build objects. These sources are not compiled during reproduction.
    for name in ['palace', 'cmake', 'tools', 'docs']:
        shutil.copytree(dev.ROOT/name, output/name, ignore=ignore)
    for name in ['CMakeLists.txt', 'LICENSE', 'NOTICE', 'THIRD-PARTY-LICENSES',
                 'THIRD-PARTY-NOTICES', 'PLAN.md', 'MILESTONES.md', 'ARCHITECTURE.md']:
        shutil.copy2(dev.ROOT/name, output/name)
    shutil.copy2(dev.ROOT/'tools/package_example.py', output/'reproduce.py')
    for case in dev.CASES:
        directory, info, _ = dev.fixture(case)
        files = ['fixture.json', 'config.json', *info['archive_parts']]
        files += [p.name for p in directory.iterdir() if p.is_file() and p.suffix in ('.json', '.csv', '.md') and p.name not in files]
        for name in files:
            target = output/'examples'/case/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(directory/name, target)
    build = output/'build/sm120'; build.mkdir(parents=True)
    shutil.copytree(dev.BUILD/'native', build/'native')
    dev.write(build/'manifest.json', manifest)
    dev.write(build/'runtime-image.json', runtime)
    shutil.copytree(reference, output/'reference', ignore=ignore)
    metadata = dict(schema=1, runtime_image_id=runtime['image_id'],
                    runtime_base_id=manifest['runtime_base_id'],
                    build_manifest_sha256=dev.sha(build/'manifest.json'),
                    source_sha256=manifest['source_sha256'],
                    source_revision_at_packaging=dev.capture(['git', '-C', dev.ROOT, 'rev-parse', 'HEAD']),
                    source_reference=str(reference), profiles=['memory', 'reference'],
                    requirements='Linux x86-64, Python3.11+, Podman+NVIDIA CDI, zstd; loaded pinned runtime image/base; SM120 CUDA12.9.1/cuDSS0.7.1.4',
                    precision='FP64 physical operator/residual; memory profile FP32 GMRES storage+FP64 arithmetic/scaled complex FP32 LU/3 fixed FP64 IR/setup reuse; reference full FP64 fresh setup',
                    memory='UVM RAM/VRAM, 60GiB cgroup/no task swap, hostguard, bounded walltime; ordinary input/output on disk',
                    qualification='Current M7 numerical evidence in docs; example is tiny two-port3.55GHz/TEM, not independent antenna manufacturing validation; global defaults unchanged',
                    image_distribution='Pinned image/base stay in local Podman store; use podman save/load once to move hosts. No registry or per-run 3GB upload.',
                    numerically_validated=False, files=inventory(output))
    dev.write(output/'bundle-manifest.json', metadata)
    verify(output)
    print(f'Local bundle: {output}; immutable payload {sum((output/p).stat().st_size for p in metadata["files"])} bytes')


def example_options(profile, reference):
    if profile not in ('memory', 'reference'):
        raise ValueError('Unsupported package profile')
    options = dict(basis='fp64', pc_side='right', krylov_size=64,
                   native_complex_coarse=True, hypre_pool_mib=256, memory_marks=True,
                   release_gmres_basis=True, release_final_solver=True, setup_audit=True,
                   save_fields=True, both_ports=True, frequencies=[3.55], coax_l2=True,
                   release_postprocess_energy=True, defer_postprocessing=True,
                   field_reference=reference)
    if profile == 'memory':
        options.update(basis='fp32', direct_basis=True, native_coarse_fp32=True,
                       native_coarse_corrections=3, port_setup_reuse=True, field_reference=reference)
    return options
