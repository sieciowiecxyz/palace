# SPDX-License-Identifier: Apache-2.0
"""Fit the Palace MVP on CPU and export its numeric weights."""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from time import perf_counter

import torch

from export import (NORMALIZATION, PHI_VERSION, SCOPE, bounded_read, export_weights,
                    load_weights, strict_json)
from model import COMPLEX, K, PHI, REAL, OperatorNetwork, fixed_csr

EPS = torch.finfo(REAL).eps
TINY = torch.finfo(REAL).tiny
COAX_CAPTURE = "d48a1ab698d95580dc4013be956b0547a5f24195af2f4faa6115baa46d0abf9a"
COAX_MESH = "0a3a2ffcc69f64b9e0d5bce3a0d6e6f83a3d670b8bdedd8f6fadf05af278bdfe"
# Frozen L-G02 benchmark mesh, including when the capture uses an alias.
WITHHELD_MESH = "293da2decbbd1507f4ac52a357d77e9b52a9e9cc1f9e1ce292e868233f732c66"
SPLITS = ("train", "validation", "test")
SOURCES = {"observed_coarse_rhs", "observed_coarse_residual",
           "manufactured_r_equals_Bc_e", "smooth_projected_mode",
           "restricted_fine_port_excitation"}
REFERENCES = {"exact_manufactured", "verified_Bc_solve", "approximate_preconditioner_only",
              "unlabeled"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def real(data, shape, name):
    value = torch.tensor(data, dtype=REAL)
    require(value.shape == shape and torch.isfinite(value).all(), f"invalid {name}")
    return value


def ints(data, name):
    require(isinstance(data, list) and all(type(i) is int for i in data),
            f"invalid integer array {name}")
    return torch.tensor(data, dtype=torch.int64)


def split_complex(data, shape, name):
    return torch.complex(real(data["real"], shape, name), real(data["imag"], shape, name))


def norm(x):
    return torch.linalg.vector_norm(x)


def coax_adapter(data, digest, record):
    require(digest == COAX_CAPTURE and record["mesh_sha256"] == COAX_MESH
            and record["geometry_id"] == "palace-coaxial-dev", "unrecognized coax identity")
    require(data["phi_imag_implicit_zero"] is True, "unexpected coax Phi representation")
    n = data["n_local"]
    phi = real(data["phi_cols_real"], (PHI, n), "Phi").T.contiguous()
    pair = dict(source_kind="manufactured_r_equals_Bc_e", r=data["manufactured_r"],
                reference_source="MFEM ND1 Phi columns 0+i*4; native Bc.Mult",
                reference_status="exact_manufactured", reference=data["manufactured_e"],
                reference_tolerance=8.56039007361963e-12)
    port = dict(source_kind="restricted_fine_port_excitation", r=data["restricted_port_rhs"],
                outer_rhs_or_port_id=data["port_excitation"], reference_status="unlabeled")
    return (torch.complex(phi, torch.zeros_like(phi)),
            [data["omega_normalized_times_bbox_L"], data["pc_mat_shifted"], data["pc_mat_real"]],
            [pair, port])


class Capture:
    def __init__(self, data, digest, record):
        n = data["n_local"]
        require(type(n) is int and 0 < n and n == data["n_global"] and data["first_row"] == 0
                and data["coarse_order"] == 1, "expected single-rank ND1 CSR")
        self.n = n
        indptr = ints(data["indptr"], "indptr")
        ci = ints(data["indices"], "indices")
        nnz = ci.numel()
        require(indptr.shape == (n + 1,) and indptr[0] == 0 and indptr[-1] == nnz
                and (indptr.diff() >= 0).all() and ((0 <= ci) & (ci < n)).all(), "invalid CSR")
        counts = indptr.diff()
        row = torch.arange(n).repeat_interleave(counts, output_size=nnz)
        require(((row[1:] != row[:-1]) | (ci[1:] > ci[:-1])).all(),
                "CSR columns must be sorted and unique")
        v = torch.complex(real(data["values_real"], (nnz,), "CSR real"),
                          real(data["values_imag"], (nnz,), "CSR imaginary"))
        essential = ints(data["essential_true_dofs"], "essential_true_dofs")
        require(((0 <= essential) & (essential < n)).all() and (essential.diff() > 0).all(),
                "invalid essential true DOFs")
        free = torch.ones(n, dtype=torch.bool)
        free[essential] = False
        require(free.any(), "no free rows")
        self.free = free
        diagonal = row == ci
        d = torch.zeros(n, dtype=COMPLEX)
        d[row[diagonal]] = v[diagonal]
        row_l1 = torch.zeros(n, dtype=REAL).index_add_(0, row, v.abs())
        self.scale = float(row_l1[free].max())
        require(math.isfinite(self.scale) and self.scale > 0, "invalid normalization scale")
        scaled = v / self.scale
        magnitude = scaled.abs()
        row_l2 = torch.zeros(n, dtype=REAL).index_add_(0, row, magnitude.square()).sqrt()
        off_diagonal = torch.zeros(n, dtype=REAL).index_add_(
            0, row[~diagonal], magnitude[~diagonal])
        self.features = torch.stack((d.real / self.scale, d.imag / self.scale,
                                     row_l1 / self.scale, row_l2, off_diagonal,
                                     counts.to(REAL).log1p(),
                                     (~free).to(REAL)), dim=1)
        require(torch.isfinite(self.features).all() and torch.isfinite(scaled).all(),
                "nonfinite normalized CSR or features")
        jacobi_d = d[free]
        squared = jacobi_d.real.square() + jacobi_d.imag.square()
        require((jacobi_d.abs() > 64 * EPS * self.scale).all()
                and torch.isfinite(squared).all() and (squared > 0).all(), "invalid Jacobi diagonal")
        reciprocal = jacobi_d.conj() / squared
        require(torch.isfinite(reciprocal).all(), "nonfinite Jacobi reciprocal")
        self.jacobi = torch.zeros_like(d)
        self.jacobi[free] = (2 / 3) * reciprocal
        self.apply = fixed_csr(indptr, ci, v, n)
        self.normalized = fixed_csr(indptr, ci, scaled, n)
        self.norm_f = norm(v)
        require(torch.isfinite(self.norm_f), "nonfinite CSR Frobenius norm")
        operator = sha256()
        operator.update(indptr.numpy().astype("<i8", copy=False).tobytes())
        operator.update(ci.numpy().astype("<i8", copy=False).tobytes())
        operator.update(v.numpy().astype("<c16", copy=False).tobytes())
        self.operator_sha256 = operator.hexdigest()
        if data["schema"] == "a05-coax-assembly-v1":
            self.phi, context, samples = coax_adapter(data, digest, record)
        else:
            require(data["schema"] == "palace-neural-capture" and data["version"] == 1
                    and data["scope"] == SCOPE and data["geometry_id"] == record["geometry_id"]
                    and data["mesh_sha256"] == record["mesh_sha256"]
                    and data["normalization_version"] == NORMALIZATION
                    and data["phi_version"] == PHI_VERSION, "invalid capture metadata")
            self.phi = split_complex(data["phi"], (n, PHI), "Phi")
            context, samples = data["context"], data["samples"]
        self.context = real(context, (3,), "context")
        require(self.context[0] > 0 and ((self.context[1:] == 0) | (self.context[1:] == 1)).all(),
                "invalid physical context")
        require((self.phi[~free] == 0).all(), "Phi violates essential BC")
        require(1 <= len(samples) <= 8, "expected one to eight captured samples")
        self.samples = [self.read_sample(sample) for sample in samples]
        if data["schema"] == "a05-coax-assembly-v1":
            # Smooth manufactured development mode, derived solely from this capture.
            reference = self.phi[:, 2] + 1j * self.phi[:, 7]
            rhs = self.apply(reference[:, None])[:, 0]
            info = dict(source_kind="smooth_projected_mode", reference_status="exact_manufactured",
                        reference_source="MFEM ND1 Phi columns 2+i*7; replayed Bc matvec",
                        reference_actual_residual_abs=0.0, reference_rhs_norm=float(norm(rhs)),
                        reference_tolerance=0.0)
            require(torch.isfinite(rhs).all() and (rhs[~free] == 0).all() and norm(rhs) > 0,
                    "invalid smooth manufactured RHS")
            self.samples.append((rhs, reference, info))

    def read_sample(self, sample):
        rhs = split_complex(sample["r"], (self.n,), "RHS")
        require((rhs[~self.free] == 0).all(), "RHS violates essential BC")
        rhs_norm = float(norm(rhs))
        require(math.isfinite(rhs_norm), "nonfinite RHS norm")
        status, source = sample["reference_status"], sample["source_kind"]
        require(status in REFERENCES and source in SOURCES, "invalid sample identity")
        reference, actual, tolerance = None, None, None
        if status != "unlabeled":
            require(isinstance(sample["reference_source"], str) and sample["reference_source"],
                    "missing reference source")
            target = split_complex(sample["reference"], (self.n,), "reference")
            require((target[~self.free] == 0).all(), "reference violates essential BC")
            actual = float(norm(rhs - self.apply(target[:, None])[:, 0]))
            tolerance = float(sample["reference_tolerance"])
            require(math.isfinite(actual) and math.isfinite(tolerance) and tolerance >= 0,
                    "invalid reference residual or tolerance")
            if status in {"exact_manufactured", "verified_Bc_solve"}:
                require(actual <= tolerance, "reference failed its Bc residual tolerance")
                reference = target
        info = dict(source_kind=source, outer_rhs_or_port_id=sample.get("outer_rhs_or_port_id"),
                    coarse_application_index=sample.get("coarse_application_index"),
                    reference_status=status, reference_source=sample.get("reference_source"),
                    reference_actual_residual_abs=actual, reference_rhs_norm=rhs_norm,
                    reference_tolerance=tolerance)
        return rhs, reference, info

    def basis(self, model):
        return model(self.phi, self.normalized, self.features, self.context, self.free)


def load_dataset(path):
    raw = bounded_read(path, 1 << 20)
    dataset = strict_json(raw)
    require(dataset["schema"] == "palace-neural-dataset" and dataset["version"] == 1,
            "unsupported dataset manifest")
    records = dataset["captures"]
    require(isinstance(records, list) and records and any(r["split"] == "train" for r in records),
            "expected training captures")
    seen = {}
    for record in records:
        split = record["split"]
        geometry = record["geometry_id"].strip().casefold()
        withheld = re.search(r"(?<![a-z0-9])l[\W_]*g[\W_]*0*2(?![0-9])", geometry)
        require(geometry and not withheld and record["mesh_sha256"] != WITHHELD_MESH,
                "L-G02 is withheld from development")
        require(split in SPLITS, "unknown split")
        for key in ("mesh_sha256", "capture_sha256"):
            require(re.fullmatch("[0-9a-f]{64}", record[key]), f"invalid {key}")
        require(("capture_sha256", record["capture_sha256"]) not in seen, "duplicate capture")
        for key, value in (("geometry_id", geometry), ("mesh_sha256", record["mesh_sha256"]),
                           ("capture_sha256", record["capture_sha256"])):
            require(seen.setdefault((key, value), split) == split, f"{key} crosses splits")
    captures = []
    for record in records:
        capture_raw = bounded_read(path.parent / record["path"], 64 << 20)
        digest = sha256(capture_raw).hexdigest()
        require(digest == record["capture_sha256"], "capture SHA-256 mismatch")
        capture = Capture(strict_json(capture_raw), digest, record)
        group = ("operator_sha256", capture.operator_sha256)
        require(seen.setdefault(group, record["split"]) == record["split"],
                "operator crosses splits")
        captures.append((record, capture))
    return captures, sha256(raw).hexdigest()


def select_columns(w, tau):
    """Detached deterministic two-pass greedy pivots, with original column tie order."""
    with torch.no_grad():
        residual = w.detach().clone()
        selected = []
        unstable = False
        while len(selected) < min(w.shape):
            lengths = torch.linalg.vector_norm(residual, dim=0)
            pivot = int(lengths.argmax())
            length = float(lengths[pivot])
            unstable |= tau / 2 <= length <= 2 * tau
            if length <= tau:
                break
            q = residual[:, pivot] / length
            for _ in range(2):
                residual -= q[:, None] * (q.conj() @ residual)
            residual[:, pivot] = 0
            selected.append(pivot)
        return selected, unstable


def correction_basis(capture, u):
    u = u * capture.free[:, None]
    w = capture.apply(u)
    scale = torch.linalg.vector_norm(w, dim=0)
    tau = max(1e-10, 64 * EPS * math.sqrt(max(capture.n, K)))
    if not torch.isfinite(w).all() or not torch.isfinite(scale).all():
        return None, "invalid_qr", True
    if ((scale == 0) & (w != 0).any(dim=0)).any() or ((scale > 0) & (scale < TINY)).any():
        return None, "invalid_qr", True
    keep = scale > 0
    w, u = w[:, keep] / scale[keep], u[:, keep] / scale[keep]
    if not torch.isfinite(u).all():
        return None, "invalid_qr", True
    if not w.shape[1]:
        return None, "rank_zero", False
    selected, unstable = select_columns(w, tau)
    # Select and trim under no_grad, then factor exactly the chosen full-rank subset.
    with torch.no_grad():
        while selected:
            _, r = torch.linalg.qr(w[:, selected], mode="reduced")
            s = torch.linalg.svdvals(r)
            ratio = float(s[-1] / s[0])
            unstable |= tau / 2 <= ratio <= 2 * tau
            if ratio >= tau:
                break
            selected.pop()
    if not selected:
        return None, "rank_zero", unstable
    ws = w[:, selected]
    q, r = torch.linalg.qr(ws, mode="reduced")
    qr_tol = 64 * EPS * math.sqrt(max(capture.n, K))
    with torch.no_grad():
        identity = torch.eye(len(selected), dtype=COMPLEX)
        valid = (norm(ws - q @ r) <= qr_tol * norm(ws)
                 and norm(q.mH @ q - identity) <= qr_tol)
    if not valid:
        return None, "invalid_qr", True
    return (u[:, selected], q, r), "ok", unstable


def residual(capture, rhs, z):
    return norm(rhs - capture.apply(z[:, None])[:, 0])


def apply_correction(capture, rhs, basis):
    z0 = capture.jacobi * rhs
    e = rhs - capture.apply(z0[:, None])[:, 0]
    s_residual = norm(e)
    if basis is None:
        return z0, s_residual, s_residual, False
    u, q, r = basis
    c = torch.linalg.solve_triangular(r, q.mH @ e[:, None], upper=True)
    term = (u @ c)[:, 0]
    z = z0 + term
    actual = residual(capture, rhs, z)
    slack = torch.minimum(
        64 * EPS * math.sqrt(capture.n) * (norm(rhs) + capture.norm_f * (norm(z0) + norm(term))),
        1e-10 * torch.maximum(norm(rhs), s_residual),
    )
    if not (torch.isfinite(actual) and actual <= s_residual + slack):
        return z0, s_residual, s_residual, True
    return z, actual, s_residual, False


def training_loss(capture, model):
    basis, status, unstable = correction_basis(capture, capture.basis(model))
    if basis is None or unstable:
        return None, "near_rank_boundary" if unstable and status == "ok" else status
    rank = basis[2].shape[0]
    singular_values = torch.linalg.svdvals(basis[2])
    rank_term = (K - rank) / K + 1e-4 * torch.log(singular_values[0] / singular_values[-1])
    losses = []
    for rhs, reference, _ in capture.samples:
        if norm(rhs) == 0:
            continue
        z, actual, _, rejected = apply_correction(capture, rhs, basis)
        if rejected:
            return None, "residual_guard"
        loss = (actual / norm(rhs)).square()
        if reference is not None and norm(reference) > 0:
            loss = loss + 0.01 * (norm(z - reference) / norm(reference)).square()
        losses.append(loss)
    if not losses:
        return None, "zero_rhs_only"
    return torch.stack(losses).mean() + rank_term, "ok"


@torch.no_grad()
def evaluate(capture, model):
    output = {}
    for name, directions in (("B3_phi", capture.phi), ("M_learned", capture.basis(model))):
        basis, status, boundary = correction_basis(capture, directions)
        samples = []
        for rhs, reference, info in capture.samples:
            z, actual, jacobi, rejected = apply_correction(capture, rhs, basis)
            samples.append(dict(**info, jacobi_residual_abs=float(jacobi),
                                residual_abs=float(actual), guard_rejected=rejected,
                                correction_error_abs=None if reference is None
                                else float(norm(z - reference))))
        output[name] = dict(requested_k=K, rank=0 if basis is None else basis[2].shape[0],
                            qr_status=status, near_rank_boundary=boundary, samples=samples)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path, help="new directory for weights and manifest")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    try:
        require(args.epochs >= 1, "epochs must be positive")
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(args.seed)
        captures, digest = load_dataset(args.dataset)
        model = OperatorNetwork()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        steps, skips = 0, {}
        start = perf_counter()
        for _ in range(args.epochs):
            for record, capture in captures:
                if record["split"] != "train":
                    continue
                optimizer.zero_grad(set_to_none=True)
                loss, status = training_loss(capture, model)
                if loss is None:
                    skips[status] = skips.get(status, 0) + 1
                    continue
                require(torch.isfinite(loss), "nonfinite training loss")
                loss.backward()
                require(all(p.grad is not None and torch.isfinite(p.grad).all()
                            for p in model.parameters()), "nonfinite or missing gradient")
                optimizer.step()
                steps += 1
        elapsed = perf_counter() - start
        require(steps > 0, f"no usable training steps ({skips})")
        manifest = export_weights(model, args.output, dict(
            dataset_sha256=digest, captures=[r for r, _ in captures],
            torch_version=str(torch.__version__), seed=args.seed, epochs=args.epochs,
            optimizer="Adam", learning_rate=1e-3, steps=steps, skipped=skips))
        exported, _ = load_weights(args.output)
        results = []
        with torch.no_grad():
            for record, capture in captures:
                require(torch.equal(capture.basis(model), capture.basis(exported)),
                        "weight roundtrip changed the basis")
                results.append(dict(**record, n=capture.n, normalization_scale=capture.scale,
                                    operator_sha256=capture.operator_sha256,
                                    comparison=evaluate(capture, exported)))
        print(json.dumps(dict(model=manifest["weights"], training_steps=steps, skipped=skips,
                              train_seconds=elapsed, comparisons=results), indent=2, allow_nan=False))
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, OverflowError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
