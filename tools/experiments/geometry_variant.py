#!/usr/bin/env python3
"""Compact axial mesh deformation and conservative quadratic-tet Jacobian audit.

Experimental preprocessing, NumPy only; no CUDA/native changes. Gmsh 2.2 ASCII
Tetrahedron10 order: https://gmsh.info/doc/texinfo/gmsh.html#Node-ordering
Unchanged topology is shared by the new reference/candidate, never old fields.
"""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dev

EDGES = [(0, 1), (1, 2), (2, 0), (0, 3), (2, 3), (1, 3)]
GRAD_L = np.array([[-1., -1., -1.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
ALPHAS = np.array([(a, b, c, 3-a-b-c) for a in range(4)
                   for b in range(4-a) for c in range(4-a-b)])
POINTS = ALPHAS / 3.
BERNSTEIN = np.array([[6 / math.prod(math.factorial(int(a)) for a in alpha)
                       * np.prod(point ** alpha) for alpha in ALPHAS] for point in POINTS])
INV_BERNSTEIN = np.linalg.inv(BERNSTEIN)


def gradients(points):
    g = np.empty((len(points), 10, 3))
    g[:, :4] = (4 * points[:, :, None] - 1) * GRAD_L
    for k, (a, b) in enumerate(EDGES, 4):
        g[:, k] = 4 * (points[:, a, None] * GRAD_L[b] + points[:, b, None] * GRAD_L[a])
    return g


GRADIENTS = gradients(POINTS)


def determinant_coefficients(tets):
    # Subtract a corner to avoid large-coordinate cancellation in sum(N'_i X_i).
    jac = np.einsum('bna,pnj->bpaj', tets - tets[:, :1], GRADIENTS, optimize=True)
    values = np.linalg.det(jac)
    return values @ INV_BERNSTEIN.T


def jacobian_bounds(coordinates, tetrahedra):
    minimum = math.inf
    bad = 0
    for start in range(0, len(tetrahedra), 2048):
        coeff = determinant_coefficients(coordinates[tetrahedra[start:start+2048]])
        low, high = coeff.min(axis=1), coeff.max(axis=1)
        # Sufficient all-domain positivity, with conservative floating-point margin.
        margin = 1e-10 * np.maximum(np.abs(low), np.abs(high))
        bad += int(np.count_nonzero(~np.isfinite(coeff).all(axis=1) | (low <= margin)))
        minimum = min(minimum, float(low.min()))
    return dict(tetrahedra=len(tetrahedra), uncertified_elements=bad,
                minimum_determinant_coefficient=minimum,
                method='Degree3 determinant Bernstein coefficients, sufficient positive bound over whole tet; FP64 margin1e-10 relative. Not interval arithmetic or mesh convergence.')


def smooth(t):
    t = np.clip(t, 0., 1.)
    return t*t*(3-2*t)


def deformation(xyz, z_window, radial_window, shift):
    a, b, c, d = z_window
    inner, outer = radial_window
    if not (all(math.isfinite(v) for v in [*z_window, *radial_window, shift])
            and a < b <= c < d and 0 <= inner < outer and shift != 0):
        raise ValueError('Require finite ordered windows and nonzero finite shift')
    minimum_axial_slope = 1 - 1.5 * abs(shift) / min(b-a, d-c)
    if minimum_axial_slope <= .5:
        raise ValueError('Deformation axial derivative bound must exceed0.5')
    z = xyz[:, 2]
    weight = smooth((z-a)/(b-a)) * (1-smooth((z-c)/(d-c)))
    radius = np.hypot(xyz[:, 0], xyz[:, 1])
    weight *= 1-smooth((radius-inner)/(outer-inner))
    result = xyz.copy()
    result[:, 2] += shift * weight
    return result, minimum_axial_slope


def load_mesh(path):
    """Retain coordinates/connectivity only in RAM; reject unsupported mesh types."""
    with path.open() as f:
        if [next(f).strip() for _ in range(3)] != ['$MeshFormat', '2.2 0 8', '$EndMeshFormat']:
            raise ValueError('Require Gmsh2.2ASCII')
        while next(f).strip() != '$Nodes':
            pass
        n = int(next(f)); xyz = np.zeros((n+1, 3))
        for expected in range(1, n+1):
            row = next(f).split()
            if int(row[0]) != expected:
                raise ValueError('Require dense ordered node IDs')
            xyz[expected] = list(map(float, row[1:]))
        if not np.isfinite(xyz).all() or next(f).strip() != '$EndNodes':
            raise ValueError('Invalid coordinates')
        while next(f).strip() != '$Elements':
            pass
        count = int(next(f)); tets = np.empty((count, 10), dtype=np.int32)
        cells = 0; protected = set(); groups = {}
        for _ in range(count):
            row = list(map(int, next(f).split()))
            kind, ntags = row[1:3]
            if ntags < 2 or kind not in (9, 11):
                raise ValueError('Require tagged Triangle6/Tetrahedron10 only')
            tag, entity = row[3:5]; nodes = row[3+ntags:]
            if len(nodes) != (6 if kind == 9 else 10) or min(nodes) < 1 or max(nodes) > n:
                raise ValueError('Invalid node connectivity')
            if kind == 11:
                tets[cells] = nodes; cells += 1
            if kind == 9 and tag in (20, 21, 22):
                protected.update(nodes)
            # Bounding boxes per physical volume or elementary PEC surface expose
            # all affected solids; this is not a claim that only a director moves.
            if kind == 11 and tag != 1 or kind == 9 and tag == 10:
                key = (kind, tag, entity)
                ids = groups.setdefault(key, set()); ids.update(nodes)
        if next(f).strip() != '$EndElements' or not cells:
            raise ValueError('Invalid tetrahedral mesh')
    return xyz, tets[:cells], sorted(protected), groups


def generate(output, z_window, radial_window, shift):
    started = time.monotonic()
    output.mkdir(parents=True, exist_ok=False)
    source = dev.prepare('tshaped-medium')
    _, info, config = dev.fixture('tshaped-medium')
    xyz, tets, protected, groups = load_mesh(source)
    moved, slope = deformation(xyz, z_window, radial_window, shift)
    if not np.array_equal(xyz[protected], moved[protected]):
        raise ValueError('Deformation moves absorbing boundary or ports')
    original = jacobian_bounds(xyz, tets)
    changed = jacobian_bounds(moved, tets)
    if original['uncertified_elements'] or changed['uncertified_elements']:
        dev.write(output/'jacobian-failure.json', dict(original=original, changed=changed))
        raise ValueError('Curved tetrahedron positivity not certified; no runnable fixture written')
    summaries = []
    for key, indices in sorted(groups.items()):
        indices = sorted(indices); old, new = xyz[indices], moved[indices]
        delta = np.abs(new-old).max()
        if delta > 0:
            summaries.append(dict(kind=key[0], attribute=key[1], entity=key[2],
                                  old_bbox=[old.min(axis=0).tolist(), old.max(axis=0).tolist()],
                                  new_bbox=[new.min(axis=0).tolist(), new.max(axis=0).tolist()],
                                  max_displacement=float(delta)))
    mesh = output/info['mesh']; mesh.parent.mkdir(parents=True)
    with source.open() as src, mesh.open('w') as dst:
        for line in src:
            dst.write(line)
            if line.strip() == '$Nodes':
                dst.write(next(src))
                for i in range(1, len(xyz)):
                    line = next(src)
                    dst.write(line if np.array_equal(xyz[i], moved[i]) else
                              f'{i} {moved[i,0]:.17g} {moved[i,1]:.17g} {moved[i,2]:.17g}\n')
                shutil.copyfileobj(src, dst)
                break
    dev.write(output/'config.json', config)
    archive = output/'mesh/pcb.msh.zst'
    subprocess.run(['zstd', '-q', '-3', '-T2', str(mesh), '-o', str(archive)], check=True, timeout=120)
    new_info = dict(info, mesh_sha256=dev.sha(mesh), mesh_bytes=mesh.stat().st_size,
                    archive_sha256=dev.sha(archive), archive_parts=['mesh/pcb.msh.zst'],
                    config_sha256=dev.sha(output/'config.json'),
                    scope='M7.5 deformed geometry performance fixture; not manufacturing optimization',
                    parent_mesh_sha256=info['mesh_sha256'])
    if new_info['mesh_sha256'] == info['mesh_sha256']:
        raise ValueError('No geometry change')
    report = dict(schema=1, parent_mesh_sha256=info['mesh_sha256'], mesh_sha256=new_info['mesh_sha256'],
                  generator_sha256=dev.sha(__file__), recipe=dict(z_window=z_window, radial_window=radial_window, shift_mm=shift),
                  minimum_continuous_axial_slope=slope, protected_boundary_nodes=len(protected),
                  protected_boundary_unchanged=True, original_jacobian=original, changed_jacobian=changed,
                  affected_groups=summaries, elapsed_seconds=time.monotonic()-started,
                  nodes=len(xyz)-1, changed_nodes=int(np.count_nonzero(np.any(xyz != moved, axis=1))),
                  limitations=['Topology and material tags unchanged; new coordinates and new independent FP64 reference required',
                               'Compact axial deformation also reparameterizes nearby air/support geometry; see affected groups',
                               'Positive determinant bound is not mesh convergence, fabrication validation or proof of RF improvement'])
    dev.write(output/'geometry-audit.json', report)
    dev.write(output/'fixture.json', new_info)  # Publish contract only after all checks.
    dev.fixture('tshaped-medium', output)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--z-window', type=float, nargs=4, required=True)
    p.add_argument('--radial-window', type=float, nargs=2, required=True)
    p.add_argument('--shift', type=float, required=True)
    args = p.parse_args()
    print(json.dumps(generate(args.output, args.z_window, args.radial_window, args.shift), indent=2))
