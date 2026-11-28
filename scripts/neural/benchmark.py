#!/usr/bin/env python3
"""Aggregate retained anteny bench reports for one geometry and frequency.

Pass --run ARM:REPETITION=DIRECTORY in execution order. Run directories must
retain their staged input and report.json. Run one analysis per frequency and
use --reference to select a predeclared classical comparison. Physical lineage,
host/build receipts, RF comparisons and repetition order need external review.
"""

import argparse
from collections import Counter
from hashlib import file_digest
import json
import math
from pathlib import Path
import re
from statistics import median


MODES = {"B0": "Off", "B1": "Off", "B2": "S", "B3": "Phi", "M": "Learned"}


def read_run(path, arm, vary_linear):
    report = json.loads((path / "report.json").read_text())
    stage = json.loads((path / "stage.json").read_text())
    env = stage["overrides"]
    if "PALACE_NEURAL_CAPTURE_DIR" in env:
        raise ValueError(f"{path}: data collection is excluded from timed comparisons")
    staged = path / "input"
    config = json.loads((staged / "config.json").read_text())
    linear = config["Solver"]["Linear"]
    neural = dict(linear.pop("NeuralCoarse", {}))
    mode = neural.pop("Mode", "Off")
    model = None
    if mode == "Learned":
        if neural.pop("ModelManifest", None) != "model/manifest.json":
            raise ValueError(f"{path}: missing staged model selector")
        model = stage["model_bundle"]
        for key, name in (("manifest", "manifest.json"), ("weights", "weights.bin")):
            with (staged / "model" / name).open("rb") as f:
                if file_digest(f, "sha256").hexdigest() != model[key]["sha256"]:
                    raise ValueError(f"{path}: staged model {name} differs from receipt")
    if mode != MODES[arm]:
        raise ValueError(f"{path}: {arm} requires mode {MODES[arm]}, found {mode}")
    for key in vary_linear:
        linear.pop(key, None)

    samples = config["Solver"]["Driven"]["Samples"]
    if len(samples) != 1 or samples[0]["Type"] != "Point" or len(samples[0]["Freq"]) != 1:
        raise ValueError(f"{path}: expected a single Point frequency")
    boundaries = config["Boundaries"]
    ports = [*boundaries.get("LumpedPort", []), *boundaries.get("WavePort", [])]
    if len(ports) != 2 or sorted((p["Index"], p.get("Excitation")) for p in ports) != [
        (1, 1), (2, 2)
    ]:
        raise ValueError(f"{path}: expected physical ports 1 and 2 with separate excitations")

    with (staged / config["Model"]["Mesh"]).open("rb") as mesh:
        digest = file_digest(mesh, "sha256").hexdigest()
    image = report.get("image_identity")
    if not image:
        raise ValueError(f"{path}: missing runtime image identity")

    timers = (report.get("palace_timers") or {}).get("durations_s", {})
    total = timers.get("Total")
    if not isinstance(total, (int, float)) or not math.isfinite(total) or total <= 0:
        total = None
    # Use the same log search order as anteny bench report.
    log = next((file for subdir in ("", "result", "results", "modal-results", "input")
                if (file := path / subdir / "palace.log").is_file()), None)
    residual_ports = []
    reasons = []
    port = None
    if log:
        with log.open(errors="replace") as lines:
            for line in lines:
                if sweep := re.match(r"Sweeping excitation index (\d+) ", line):
                    port = int(sweep[1])
                if "PALACE_TRUE_RESIDUAL:" in line and "qualified_linear_solve=true" in line:
                    residual_ports.append(port)
                if mode != "Off" and "PALACE_NEURAL_COARSE:" in line:
                    fields = dict(field.split("=", 1) for field in line.split() if "=" in field)
                    if fields.get("mode") == mode and "fallback_reason" in fields:
                        reasons.append(fields["fallback_reason"])
    eligible = (
        report.get("exit_code") == 0 and report.get("qualification") == "qualified"
        and residual_ports == [1, 2] and len(report.get("true_residuals", [])) == 2
        and total is not None
    )

    output = config["Problem"].get("Output", "postpro")
    metadata = log.parent / output / "palace.json" if log else None
    peak = None
    if metadata and metadata.is_file():
        peak = json.loads(metadata.read_text()).get("PeakNodeMemoryMegabytes")
        if isinstance(peak, dict):
            peak = peak.get("Max")
    return (digest, image, config, env), {
        "model_bundle": model, "neural_settings": neural,
        "path": str(path), "manifest_sha256": report.get("manifest_sha256"),
        "exit_code": report.get("exit_code"), "qualification": report.get("qualification"),
        "eligible": eligible, "qualified_residual_ports": residual_ports,
        "palace_peak_node_memory_mb": peak,
        "max_physical_relative_residual": report.get("true_rhs_max"),
        "palace_total_s": total, "process_wall_s": report.get("process_wall_s"),
        "orchestration_wall_s": report.get("orchestration_wall_s"),
        "fallback_reasons": reasons,
    }


def summarize(runs, reference):
    times = {rep: run["palace_total_s"] for rep, run in runs.items() if run["eligible"]}
    pairs = [(t, reference[rep]) for rep, t in times.items() if rep in reference]
    ratios = [t / baseline for t, baseline in pairs]
    enough = len(pairs) >= 3
    reasons = Counter(reason for run in runs.values() for reason in run["fallback_reasons"])
    observed = sum(reasons.values())
    fallback = observed - reasons.get("none", 0)
    complete_fallback_coverage = bool(runs) and all(
        len(run["fallback_reasons"]) == 2 for run in runs.values()
    )
    return {
        "runs": runs, "eligible_repetitions": len(times),
        "median_palace_total_s": median(times.values()) if times else None,
        "worst_palace_total_s": max(times.values(), default=None),
        "matched_repetitions": len(ratios),
        "ratio_of_paired_medians": (
            median(t for t, _ in pairs) / median(b for _, b in pairs) if enough else None
        ),
        "worst_paired_time_ratio": max(ratios) if enough else None,
        "fallback_reasons": dict(reasons), "fallback_rhs_observed": observed,
        "fallback_rate": fallback / observed if complete_fallback_coverage else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", required=True, metavar="ARM:REP=DIR")
    parser.add_argument("--reference", choices=("B0", "B1"), default="B0")
    parser.add_argument("--vary-linear", action="append", default=[], choices=(
        "Type", "KSPType", "MaxSize", "PCSide", "ComplexCoarseSolve", "PCMatShifted",
    ), help="Allow a named classical solver treatment to differ within the cohort.")
    args = parser.parse_args()
    arms = {arm: {} for arm in MODES}
    match = None
    seen = set()
    order = []
    model_bundle = neural_settings = None
    try:
        for spec in args.run:
            label, directory = spec.split("=", 1)
            arm, rep = label.split(":", 1)
            path = Path(directory).resolve(strict=True)
            if arm not in MODES or not rep or rep in arms[arm] or path in seen:
                raise ValueError(f"invalid or duplicate run: {spec}")
            identity, run = read_run(path, arm, args.vary_linear)
            if arm == "M":
                if model_bundle is not None and model_bundle != run["model_bundle"]:
                    raise ValueError(f"{path}: different models among learned repetitions")
                model_bundle = run["model_bundle"]
            if arm in ("B2", "B3", "M"):
                if neural_settings is not None and neural_settings != run["neural_settings"]:
                    raise ValueError(f"{path}: different settings among coarse correction arms")
                neural_settings = run["neural_settings"]
            if match is not None and match != identity:
                raise ValueError(f"{path}: mesh, runtime image, environment or untreated config differs")
            match = identity
            arms[arm][rep] = run
            seen.add(path)
            order.append(label)
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))

    digest, image, config, _ = match
    reference = {rep: run["palace_total_s"] for rep, run in arms[args.reference].items()
                 if run["eligible"]}
    print(json.dumps({
        "mesh_sha256": digest, "image_identity": image,
        "frequency_ghz": config["Solver"]["Driven"]["Samples"][0]["Freq"][0],
        "reference": args.reference, "vary_linear": args.vary_linear,
        "supplied_run_order": order,
        "arms": {arm: summarize(runs, reference if arm != args.reference else {})
                 for arm, runs in arms.items()},
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
