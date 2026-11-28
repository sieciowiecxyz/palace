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
