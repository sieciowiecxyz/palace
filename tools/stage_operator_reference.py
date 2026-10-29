#!/usr/bin/env python3
"""Audit operator benchmark source/native provenance without building or running Palace."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


NATIVE_FILES = ('libpalace.so', 'palace-x86_64.bin', 'libcudss_fp32.so')


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def compiler_inputs(root: Path) -> dict[str, str]:
    """Match tools/dev.py source_hash coverage, including new/uncommitted inputs."""
    files = [root / 'CMakeLists.txt']
    for directory in ('palace', 'cmake', 'tools/adapter'):
        files.extend(p for p in (root / directory).rglob('*') if p.is_file())
    return {str(p.relative_to(root)): sha(p) for p in sorted(files)}


def source_hash(inputs: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(inputs.items()):
        digest.update(name.encode() + b'\0')
        digest.update(bytes.fromhex(value))
    return digest.hexdigest()


def audit(source: Path, bundle: Path, run: Path) -> dict:
    load = lambda p: json.loads(p.read_text())
    manifest_path = bundle / 'build/sm120/manifest.json'
    manifest = load(manifest_path)
    runtime = load(bundle / 'build/sm120/runtime-image.json')
    inputs, frozen = compiler_inputs(source), compiler_inputs(bundle)
    native = {name: sha(bundle / 'build/sm120/native' / name) for name in NATIVE_FILES}
    command = load(run / 'command.json')
    run_manifest = load(run / 'build-manifest.json')
    changed = sorted(name for name in inputs.keys() | frozen.keys()
                     if inputs.get(name) != frozen.get(name))
    checks = {
        'source_matches_frozen': not changed,
        'source_matches_manifest': source_hash(inputs) == manifest['source_sha256'],
        'frozen_matches_manifest': source_hash(frozen) == manifest['source_sha256'],
        'native_matches_manifest': native == manifest['native'],
        'source_settings_match': sha(source / 'tools/runtime.json') == manifest['settings_sha256'],
        'frozen_settings_match': sha(bundle / 'tools/runtime.json') == manifest['settings_sha256'],
        'runtime_manifest_hash': sha(manifest_path) == runtime['build_manifest_sha256'],
        'run_manifest_matches_frozen': run_manifest == manifest,
        'run_uses_pinned_image': command['runtime_image'] == runtime['image_id'],
        'run_uses_image_native': command['native_from_image'] is True,
        'run_config_matches_record': sha(run / 'config.json') == command['actual_config_sha256'],
    }
    return {
        'schema': 1,
        'scope': 'Recorded source/native/input provenance only; not a live image or RF test',
        'passed': all(checks.values()),
        'checks': checks,
        'source_sha256': source_hash(inputs),
        'source_file_count': len(inputs),
        'changed_compiler_inputs': changed,
        'native_sha256': native,
        'runtime_image_id': runtime['image_id'],
        'builder_image_id': manifest['builder_image_id'],
        'runtime_base_id': manifest['runtime_base_id'],
        'settings_sha256': manifest['settings_sha256'],
        'global_numerically_validated': manifest['numerically_validated'],
        'config_sha256': sha(run / 'config.json'),
        'paths': {'source': str(source), 'bundle': str(bundle), 'run': str(run)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.source.resolve(), args.bundle.resolve(), args.run.resolve())
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end='')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
