# SPDX-License-Identifier: Apache-2.0
"""Read, validate and write the Palace v1 numeric model bundle."""

import argparse
from array import array
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

import torch

from model import BLOCKS, CONTEXT, FEATURES, K, PHI, WIDTH, OperatorNetwork

NORMALIZATION = "scalar-row-l1-v1"
PHI_VERSION = "phi-global-nd-v1"
ARCHITECTURE = dict(blocks=BLOCKS, complex_width=WIDTH, basis_k=K, phi_columns=PHI,
                    row_features=FEATURES, context=CONTEXT)
SCOPE = dict(problem="driven_uniform", mpi_ranks=1, coarse_space="conforming_nd",
             coarse_order=1)
WEIGHTS_FILE = "weights.bin"
MANIFEST_LIMIT = 1 << 20


def tensor_table():
    shapes = [(f"lift.{part}", [PHI, WIDTH]) for part in ("real", "imag")]
    for i in range(BLOCKS):
        prefix = f"blocks.{i}"
        for name in ("local", "operator"):
            shapes.extend((f"{prefix}.{name}.{part}", [WIDTH, WIDTH]) for part in ("real", "imag"))
        shapes.extend(((f"{prefix}.gate.weight", [WIDTH + FEATURES + CONTEXT, WIDTH]),
                       (f"{prefix}.gate.bias", [WIDTH])))
    shapes.extend((f"readout.{part}", [WIDTH, K]) for part in ("real", "imag"))
    offset, entries = 0, []
    for name, shape in shapes:
        entries.append(dict(name=name, shape=shape, offset_bytes=offset))
        offset += 8 * math.prod(shape)
    return entries, offset


def metadata():
    tensors, _ = tensor_table()
    return dict(schema="palace-neural-weights", version=1, dtype="float64-le",
                normalization=NORMALIZATION, phi_version=PHI_VERSION,
                architecture=ARCHITECTURE, scope=SCOPE, tensors=tensors)


def export_weights(model, directory, training):
    manifest = metadata()
    entries, size = tensor_table()
    state = model.state_dict()
    if set(state) != {entry["name"] for entry in entries}:
        raise ValueError("unexpected model tensors")
    values = array("d")
    for entry in entries:
        name = entry["name"]
        tensor = state[name]
        if (list(tensor.shape) != entry["shape"] or tensor.dtype != torch.float64
                or not torch.isfinite(tensor).all()):
            raise ValueError(f"invalid model tensor {name}")
        values.extend(tensor.detach().cpu().reshape(-1).tolist())
    if sys.byteorder != "little":
        values.byteswap()
    blob = values.tobytes()
    if len(blob) != size:
        raise ValueError("unsupported host float64 layout")
    manifest["weights"] = dict(file=WEIGHTS_FILE, bytes=size, sha256=sha256(blob).hexdigest())
    manifest["training"] = training
    encoded = json.dumps(manifest, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if len(encoded.encode("utf-8")) > MANIFEST_LIMIT:
        raise ValueError("weight manifest exceeds byte limit")
    directory.mkdir()
    (directory / WEIGHTS_FILE).write_bytes(blob)
    (directory / "manifest.json").write_text(encoded, encoding="utf-8")
    return manifest


def bounded_read(path, limit):
    with path.open("rb") as stream:
        blob = stream.read(limit + 1)
    if len(blob) > limit:
        raise ValueError(f"{path.name} exceeds byte limit")
    return blob


def strict_json(blob):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key {key}")
            result[key] = value
        return result

    def reject(token):
        raise ValueError(f"invalid JSON number {token}")

    return json.loads(blob, object_pairs_hook=unique, parse_constant=reject)


def load_weights(directory):
    manifest = strict_json(bounded_read(directory / "manifest.json", MANIFEST_LIMIT))
    for key, value in metadata().items():
        if json.dumps(manifest.get(key), sort_keys=True) != json.dumps(value, sort_keys=True):
            raise ValueError(f"invalid manifest field {key}")
    entries, size = tensor_table()
    blob = bounded_read(directory / WEIGHTS_FILE, size)
    weights = dict(file=WEIGHTS_FILE, bytes=size, sha256=sha256(blob).hexdigest())
    if len(blob) != size or manifest.get("weights") != weights:
        raise ValueError("invalid weights size or SHA-256")
    values = array("d")
    values.frombytes(blob)
    if sys.byteorder != "little":
        values.byteswap()
    data = torch.frombuffer(values, dtype=torch.float64)
    if not torch.isfinite(data).all():
        raise ValueError("nonfinite weights")
    state = {}
    for entry in entries:
        offset = entry["offset_bytes"] // 8
        shape = entry["shape"]
        state[entry["name"]] = data[offset:offset + math.prod(shape)].reshape(shape)
    # Loading a model must not advance the caller's CPU RNG.
    with torch.random.fork_rng(devices=[]):
        model = OperatorNetwork()
    model.load_state_dict(state)
    return model.eval(), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--reexport", type=Path)
    args = parser.parse_args()
    try:
        model, manifest = load_weights(args.bundle)
        if args.reexport:
            export_weights(model, args.reexport, manifest.get("training"))
        print(json.dumps(manifest["weights"], sort_keys=True))
    except (ValueError, OSError, TypeError, AttributeError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
