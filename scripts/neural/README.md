# Neural coarse training replay

Use development captures from the actual level-0 multigrid operator. Capture
the complex CSR, projected ND1 probes, essential true-DOF mask and operator
identity. Record the RHS entering the coarse solve in the native V-cycle,
tagged by excitation and coarse application. Keep observed RHS samples
unlabeled unless there is an independently verified correction reference.
For classical, untimed single-rank uniform Driven runs in an ML-enabled build,
set `PALACE_NEURAL_CAPTURE_DIR` to a fresh subdirectory of the configured
output (e.g. `postpro/neural` for output `postpro`). Supply the pinned
geometry, mesh, config and source identities in `PALACE_NEURAL_GEOMETRY_ID`,
`PALACE_NEURAL_MESH_SHA256`, `PALACE_NEURAL_CONFIG_SHA256` and
`PALACE_NEURAL_SOURCE_SHA`. The first excitation is selected by default.
Each operator contributes up to eight observed coarse RHS samples. The CPU
fixture below uses one such sample from coax.

Assign splits by whole geometry, keeping all its frequencies, meshes and
excitations together. The v1 dataset lists capture paths relative to the
dataset file, geometry and mesh identities, capture SHA-256 and split. Keep
L-G02 out of development intake. The coax replay below has one training
geometry and zero validation or test geometries.

With PyTorch `2.10.0+cu128` (used on CPU here), run from the Palace checkout.
Set `work` to the experiment artifact directory and `python` to the matching
PyTorch interpreter. The retained inputs are
`a05-features-capture/{cycle-dataset,cycle-capture}.json` under that directory.

```sh
work="$HOME/dev/rust/ml-coarse-work"
python="$HOME/.local/lib/transcription/gpu-runtime/bin/python"
out=$(mktemp -d)
export CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$python" scripts/neural/train.py "$work/a05-features-capture/cycle-dataset.json" \
  "$out/model" --epochs 4 --seed 0 > "$out/report.json"
"$python" scripts/neural/export.py "$out/model" --reexport "$out/roundtrip"
cmp "$out/model/manifest.json" "$out/roundtrip/manifest.json"
cmp "$out/model/weights.bin" "$out/roundtrip/weights.bin"
sha256sum "$out/model/manifest.json" "$out/model/weights.bin"
```

The smoke replay completed four optimizer steps and checked equality of the
basis after reload. The two SHA-256 values in command order were
`d5a73a50602236cf1bb9a47ee8ecbbc054912f0483cac8bf1005dcea02fb381e` and
`d188321bd61088f0bb37f553ca0f838c49257f7cdfc2982dbe838b8ad5471f90`.
The versioned manifest records the training inputs, tensor shapes and digest
of the adjacent 73,984-byte little-endian FP64 payload. Pin both files
independently when transporting the bundle. The A07 standalone parity replay
used the earlier A06 assembly-capture bundle, with a different weights digest.

For antenna captures, generate lineage from the retained worker archive and
the saved prepared evaluation in the same Anteny Store. Repeat `--pair` for
each run in the dataset. From the Palace checkout, pass the export alongside
the dataset manifest:

```sh
anteny --root "$anteny_root" --json bench capture-lineage \
  --pair "$run_dir" "$evaluation_json" > "$out/lineage.json"
"$python" scripts/neural/train.py "$dataset_json" "$out/model" \
  --verified-lineage "$out/lineage.json"
```

The canonical design recipe groups remeshed captures together. The recorded
source SHA comes from capture staging. Check it against the runtime build
receipt when selecting a training corpus.

## Experimental fine-field warm start

An ML-enabled Palace build can collect and reuse converged electric fields on
a single-rank uniform Driven sweep. To collect while using the classical
solver, set `Solver.Driven.CollectWarmStart` to `true` in the case config.
Each eligible solve checks the final residual on the physical operator. Up to
32 qualified snapshots per invocation go under `Problem.Output/warmstart/`.
Keep that directory with the input config, mesh, Palace revision and solver
report. Leaving the setting enabled in a case opts future runs of that case
into collection. Archive output before reusing a case's output directory.

Each snapshot stores the complex fine-space field, nondimensional angular
frequency, excitation ID, RHS norm, classical starting residual, final residual
and solver tolerance. The compatibility hash covers the discretization,
essential constraints and the input Model, Domains and Boundaries sections.
Use a fixed source of external material or port data throughout a dataset.
This first implementation supports straight-sided 3D conforming ND1 spaces
with at most 16,384 true DOFs. Collection does not require a trained model.
Coarse-grid training captures have a different field layout and purpose.

Select distinct frequencies from the same configuration for training and
validation. Pass the sample paths explicitly, for example:

```sh
python scripts/neural/warmstart.py \
  --train "$train_sample_1" "$train_sample_2" \
  --validation "$validation_sample" \
  --output model.json --rank 32 --epochs 200 > training-report.json
```

The CPU trainer builds one real POD basis from the real and imaginary parts
of training fields. The effective rank is at most 32 and is reduced for
rank-deficient training data. Frequency, excitation ID and log-scaled RHS
norm are available before each solve. Four 128-unit SiLU layers predict
real and imaginary coefficients in this basis. The report includes the split
digests, coefficient loss, reconstructed-field error and a previous-field
comparison on eligible validation points. Frequencies held out from one
geometry test interpolation or extrapolation within that fixed space.

To run inference, set `Solver.Driven.WarmStartModel` to the bundle path
(relative to the solver's working directory or absolute). The default is an
empty path. For each supported excitation Palace forms its ordinary starting
guess, including the configured history, then evaluates the learned candidate
with the current physical operator and RHS. It uses the candidate only if
its residual is finite and strictly smaller. The solver still has to meet
the final physical residual tolerance. The log reports both starting norms
and the selection. Compare end-to-end runs with collection disabled and
identical mesh, sources, sweep order, solver, tolerances and hardware.
