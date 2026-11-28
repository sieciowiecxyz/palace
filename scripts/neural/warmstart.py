#!/usr/bin/env python3
"""Train a fixed-space Palace warm-start model from qualified JSON snapshots."""

import argparse
import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn


SAMPLE_SCHEMA = "palace-warmstart-sample-v1"
MODEL_SCHEMA = "palace-warmstart-model-v1"
MAX_DOFS = 16384
MAX_RANK = 32
MAX_SAMPLES = 256
MAX_SAMPLE_BYTES = 1 << 20
MAX_MODEL_BYTES = 32 << 20


@dataclass
class Sample:
    space_id: str
    n: int
    omega: float
    excitation: int
    rhs_norm: float
    field: torch.Tensor
    sha256: str


def number(value, name):
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} must be a finite number") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_sample(path):
    try:
        with path.open("rb") as source:
            raw = source.read(MAX_SAMPLE_BYTES + 1)
        if len(raw) > MAX_SAMPLE_BYTES:
            raise ValueError("sample exceeds 1 MiB")
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
        if not isinstance(data, dict) or data.get("schema") != SAMPLE_SCHEMA:
            raise ValueError(f"expected schema {SAMPLE_SCHEMA}")
        space_id = data["space_id"]
        n = data["n"]
        excitation = data["excitation"]
        if not isinstance(space_id, str) or not space_id.strip():
            raise ValueError("space_id must be a nonempty string")
        space_id.encode("utf-8")
        if type(n) is not int or not 1 <= n <= MAX_DOFS:
            raise ValueError(f"n must be an integer in [1, {MAX_DOFS}]")
        if type(excitation) is not int or not -(1 << 31) <= excitation < (1 << 31):
            raise ValueError("excitation must be a signed 32-bit integer")
        omega = number(data["omega"], "omega")
        rhs_norm = number(data["rhs_norm"], "rhs_norm")
        epsilon = number(data["epsilon"], "epsilon")
        residual = number(data["residual_norm"], "residual_norm")
        initial_residual = number(data["initial_residual"], "initial_residual")
        if omega <= 0 or rhs_norm <= 0 or epsilon <= 0 or initial_residual < 0:
            raise ValueError("invalid frequency, RHS norm, tolerance or initial residual")
        if not 0 <= residual <= epsilon:
            raise ValueError("field label did not meet its absolute residual tolerance")
        field = []
        for name in ("field_real", "field_imag"):
            values = data[name]
            if not isinstance(values, list) or len(values) != n:
                raise ValueError(f"{name} must have exactly n entries")
            field.append([number(value, name) for value in values])
        return Sample(space_id, n, omega, excitation, rhs_norm,
                      torch.tensor(field, dtype=torch.float64, device="cpu"), hashlib.sha256(raw).hexdigest())
    except (KeyError, OSError, ValueError, RecursionError) as error:
        raise ValueError(f"{path}: {error}") from error


def load_splits(train_paths, validation_paths):
    if not train_paths or not validation_paths:
        raise ValueError("both training and validation need samples")
    if len(train_paths) + len(validation_paths) > MAX_SAMPLES:
        raise ValueError(f"at most {MAX_SAMPLES} samples are supported")
    train = [load_sample(path) for path in train_paths]
    validation = [load_sample(path) for path in validation_paths]
    space = (train[0].space_id, train[0].n)
    identities = set()
    for sample in train + validation:
        if (sample.space_id, sample.n) != space:
            raise ValueError("all samples must share one fixed space_id and n")
        identity = (sample.omega, sample.excitation)
        if identity in identities:
            raise ValueError(f"duplicate sample identity {identity}")
        identities.add(identity)
    if {s.omega for s in train} & {s.omega for s in validation}:
        raise ValueError("a frequency point crosses splits")
    if {s.excitation for s in validation} - {s.excitation for s in train}:
        raise ValueError("validation contains an unsupported excitation")
    return train, validation


def features(samples):
    return torch.tensor(
        [[s.omega, s.excitation, math.log1p(s.rhs_norm)] for s in samples],
        dtype=torch.float64, device="cpu",
    )


def finite(tensor, name):
    if not torch.isfinite(tensor).all():
        raise ValueError(f"{name} is nonfinite")
    return tensor


def error_metrics(prediction, target):
    difference = finite(prediction - target, "prediction error")
    # Scale before taking norms to avoid overflow from squaring large entries.
    peak = max(float(difference.abs().max()), float(target.abs().max()))
    if peak == 0:
        return {"rmse": 0.0, "relative_l2": None}
    error_norm = float(torch.linalg.vector_norm(difference / peak))
    target_norm = float(torch.linalg.vector_norm(target / peak))
    return {
        "rmse": (error_norm / math.sqrt(target.numel())) * peak,
        "relative_l2": error_norm / target_norm if target_norm else None,
    }


def history_pairs(train, validation):
    pairs = []
    for index, sample in enumerate(validation):
        previous = [s for s in train if s.excitation == sample.excitation and s.omega < sample.omega]
        if previous:
            pairs.append((index, max(previous, key=lambda s: s.omega)))
    return pairs


def train_model(train, validation, rank, epochs, seed):
    if not 1 <= rank <= MAX_RANK or epochs < 1:
        raise ValueError(f"rank must be in [1, {MAX_RANK}] and epochs must be positive")

    x_train, x_validation = features(train), features(validation)
    mean = finite(x_train.mean(dim=0), "feature mean")
    scale = finite(x_train.std(dim=0, unbiased=False), "feature scale")
    scale = torch.where(x_train.amin(dim=0) == x_train.amax(dim=0), 1.0, scale)
    x_train = finite((x_train - mean) / scale, "normalized training features")
    x_validation = finite((x_validation - mean) / scale, "normalized validation features")

    fields_train = torch.stack([s.field for s in train])
    fields_validation = torch.stack([s.field for s in validation])
    snapshots = fields_train.flatten(0, 1)
    amplitude = float(snapshots.abs().max())
    if amplitude == 0:
        raise ValueError("training fields have numerical rank zero")
    _, singular, right = torch.linalg.svd(snapshots / amplitude, full_matrices=False)
    threshold = singular[0] * max(snapshots.shape) * torch.finfo(snapshots.dtype).eps
    rank = min(rank, int((singular > threshold).sum()))
    basis = right[:rank].T.contiguous()
    y_train = ((fields_train / amplitude) @ basis).flatten(1)
    y_validation = finite(
        ((fields_validation / amplitude) @ basis).flatten(1), "validation coefficients"
    )

    torch.manual_seed(seed)
    widths = [3, 128, 128, 128, 128, 2 * rank]
    layers = [nn.Linear(a, b, dtype=torch.float64, device="cpu")
              for a, b in zip(widths, widths[1:])]
    network = nn.Sequential(*(module for layer in layers[:-1]
                              for module in (layer, nn.SiLU())), layers[-1])
    optimizer = torch.optim.Adam(network.parameters(), lr=1e-3)
    for _ in range(epochs):
        optimizer.zero_grad()
        loss = finite(nn.functional.mse_loss(network(x_train), y_train), "training loss")
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        training_loss = finite(nn.functional.mse_loss(network(x_train), y_train), "training loss")
        validation_prediction = network(x_validation)
        validation_loss = finite(
            nn.functional.mse_loss(validation_prediction, y_validation), "validation loss"
        )
        prediction_coeff = finite(validation_prediction * amplitude, "predicted coefficients")
        true_coeff = finite(y_validation * amplitude, "reference coefficients")
        prediction_field = finite(
            prediction_coeff.unflatten(1, (2, rank)) @ basis.T, "predicted field"
        )
        pairs = history_pairs(train, validation)
        report = {
            "space_id": train[0].space_id,
            "rank": rank,
            "epochs": epochs,
            "train_examples": len(train),
            "validation_examples": len(validation),
            "train_frequency_points": len({s.omega for s in train}),
            "validation_frequency_points": len({s.omega for s in validation}),
            "normalized_coefficient_mse_train": float(training_loss),
            "normalized_coefficient_mse_validation": float(validation_loss),
            "validation_coefficient": error_metrics(prediction_coeff, true_coeff),
            "validation_field": error_metrics(prediction_field, fields_validation),
            "validation_history": {"examples": len(pairs)},
        }
        if pairs:
            indices, previous = zip(*pairs)
            indices = list(indices)
            history_field = torch.stack([s.field for s in previous])
            history_coeff = finite((history_field @ basis).flatten(1), "history coefficients")
            report["validation_history"].update(
                history_coefficient=error_metrics(history_coeff, true_coeff[indices]),
                history_field=error_metrics(history_field, fields_validation[indices]),
                model_coefficient=error_metrics(prediction_coeff[indices], true_coeff[indices]),
                model_field=error_metrics(prediction_field[indices], fields_validation[indices]),
            )

        # Fold target amplitude into the last linear layer for the runtime contract.
        bundle = {
            "schema": MODEL_SCHEMA,
            "space_id": train[0].space_id,
            "n": train[0].n,
            "rank": rank,
            "excitations": sorted({s.excitation for s in train}),
            "mean": mean.tolist(),
            "scale": scale.tolist(),
            "basis": basis.tolist(),
            "layers": [
                {
                    "weight": finite(layer.weight * factor, "export weight").tolist(),
                    "bias": finite(layer.bias * factor, "export bias").tolist(),
                }
                for layer, factor in zip(layers, [1.0] * 4 + [amplitude])
            ],
        }
    return bundle, report


def write_bundle(path, bundle):
    payload = json.dumps(bundle, allow_nan=False, ensure_ascii=False, separators=(",", ":"))
    payload = (payload + "\n").encode("utf-8")
    if len(payload) > MAX_MODEL_BYTES:
        raise ValueError("model exceeds 32 MiB")
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(payload)
            output.close()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="The history baseline reuses the latest lower-frequency training field "
               "with the same excitation. Metrics compare models on those same held-out points.",
    )
    parser.add_argument("--train", type=Path, nargs="+", required=True, metavar="SAMPLE")
    parser.add_argument("--validation", type=Path, nargs="+", required=True, metavar="SAMPLE")
    parser.add_argument("--output", type=Path, required=True, metavar="MODEL")
    parser.add_argument("--rank", type=int, default=MAX_RANK)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() in {p.resolve() for p in args.train + args.validation}:
            raise ValueError("output would replace an input sample")
        torch.set_num_threads(1)
        train, validation = load_splits(args.train, args.validation)
        bundle, report = train_model(train, validation, args.rank, args.epochs, args.seed)
        report.update(seed=args.seed, torch_version=str(torch.__version__),
                      train_sha256=[s.sha256 for s in train],
                      validation_sha256=[s.sha256 for s in validation])
        summary = json.dumps(report, allow_nan=False, separators=(",", ":"))
        write_bundle(args.output, bundle)
    except (OSError, OverflowError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    print(summary)


if __name__ == "__main__":
    main()
