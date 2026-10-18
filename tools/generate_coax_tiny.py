#!/usr/bin/env python3
"""Generate the fixed 2 mm TEM smoke mesh; optional gmsh 4.13.1, not a runtime dependency.

Geometry follows the audited 20 mm fixture; shorten the validation line, keeping
the same cross section, material, curved geometry and medium FEM settings.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import gmsh

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT/'artifacts/generated-coax-tiny')
OUT = parser.parse_args().output.resolve()
if OUT.exists():
    raise SystemExit('Refusing to overwrite an existing fixture')
OUT.mkdir(parents=True)
a, eps, length = 0.12, 2.1, 2.0
b = a*math.exp(50*math.sqrt(eps)/59.9584916)
gmsh.initialize()
try:
    gmsh.model.add('coax-tiny')
    occ = gmsh.model.occ
    face = occ.cut([(2, occ.addDisk(0, 0, 0, b, b))], [(2, occ.addDisk(0, 0, 0, a, a))])[0]
    extruded = occ.extrude(face, 0, 0, length, numElements=[math.ceil(length/0.35)])
    volumes = [tag for dim, tag in extruded if dim == 3]
    occ.synchronize()
    walls, ends = [], {}
    for dim, tag in gmsh.model.getBoundary([(3, tag) for tag in volumes], oriented=False):
        z = occ.getCenterOfMass(dim, tag)[2]
        if abs(z) < 1e-8:
            ends[3] = tag
        elif abs(z-length) < 1e-8:
            ends[4] = tag
        else:
            walls.append(tag)
    if len(ends) != 2:
        raise ValueError('Missing end ports')
    gmsh.model.addPhysicalGroup(3, volumes, 1)
    gmsh.model.addPhysicalGroup(2, walls, 2)
    for attribute, tag in ends.items():
        if len(gmsh.model.getAdjacencies(2, tag)[0]) != 1:
            raise ValueError('Port must be one-sided')
        gmsh.model.addPhysicalGroup(2, [tag], attribute)
    gmsh.option.setNumber('Mesh.MshFileVersion', 2.2)
    gmsh.option.setNumber('Mesh.MeshSizeMin', 0.04)
    gmsh.option.setNumber('Mesh.MeshSizeMax', 0.04)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)
    tags = [int(t) for block in gmsh.model.mesh.getElements(3)[1] for t in block]
    jacobian = float(min(gmsh.model.mesh.getElementQualities(tags, 'minDetJac')))
    quality = float(min(gmsh.model.mesh.getElementQualities(tags, 'minSICN')))
    if jacobian <= 0 or quality <= 0:
        raise ValueError('Invalid mesh')
    gmsh.write(str(OUT/'coax.msh'))
finally:
    gmsh.finalize()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

geometry = dict(inner_radius_mm=a, shield_inner_radius_mm=b, length_mm=length,
                epsilon_r=eps, geometry_order=2, mesh_size_mm=0.04, one_sided_ports=True)
audit = dict(solver_ready=True, tetrahedra=len(tags), minimum_jacobian=jacobian,
             min_signed_quality=quality, geometry=geometry, gmsh_version=gmsh.__version__,
             mesh_sha256=digest(OUT/'coax.msh'), builder_sha256=digest(Path(__file__)),
             source_model_sha256=hashlib.sha256(json.dumps(geometry, sort_keys=True).encode()).hexdigest(),
             physics_validated=False)
(OUT/'mesh-audit.json').write_text(json.dumps(audit, indent=2)+'\n')
config = json.loads((ROOT/'examples/coax-medium/config.json').read_text())
(OUT/'config.json').write_text(json.dumps(config, indent=2)+'\n')
subprocess.run(['zstd', '-6', '-q', str(OUT/'coax.msh'), '-o', str(OUT/'coax.msh.zst')], check=True)
fixture = dict(schema=1, name='coax-tiny', mesh='coax.msh', mesh_sha256=digest(OUT/'coax.msh'),
               mesh_bytes=(OUT/'coax.msh').stat().st_size, archive_parts=['coax.msh.zst'],
               archive_sha256=digest(OUT/'coax.msh.zst'), config_sha256=digest(OUT/'config.json'),
               scope='2 mm analytical TEM filter; not the antenna or 20 mm reference',
               medium=json.loads((ROOT/'examples/coax-medium/fixture.json').read_text())['medium'])
(OUT/'fixture.json').write_text(json.dumps(fixture, indent=2)+'\n')
print(json.dumps(audit, indent=2))
