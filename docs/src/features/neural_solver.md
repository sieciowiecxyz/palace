# Experimental Neural Coarse Correction

The experiment changes the coarsest solve in geometric multigrid for a uniform
Driven sweep. It requires a single MPI rank, right-preconditioned FGMRES, at
least two multigrid levels and a conforming, unbroken ND1 coarse space. The
experimental modes require a build with `PALACE_WITH_ML=ON`. HIP is outside
the supported scope.

| `Solver.Linear.NeuralCoarse.Mode` | Coarse solve |
| --- | --- |
| `Off` (default) | Ordinary configured classical coarse solver. |
| `S` (B2) | Fixed Jacobi control. |
| `Phi` (B3) | Jacobi plus an untrained basis of eight projected probe fields. |
| `Learned` (M) | Jacobi plus eight basis columns predicted from the coarse operator, probes and context. |

Phi and Learned use the same rank-revealing QR residual correction against the
original coarse operator. Effective rank can be lower than eight. A coarse
guard can reject the correction. The trial and any classical continuation share
the per-RHS iteration and time budgets. Classical continuation reuses the
current iterate and sets up its coarse solver on demand. The deadline is
checked at solver boundaries, so it cannot interrupt an in-progress setup or
library call.

For an eligible uniform case, merge these fields into the existing
`Solver.Linear` object. Use the same positive time budget for matched runs,
including the `Off` control. For `S`, `Phi` and `Off`, omit `ModelManifest`.

```json
{
  "KSPType": "FGMRES",
  "PCSide": "Right",
  "MaxSolveSeconds": 120,
  "NeuralCoarse": {
    "Mode": "Learned",
    "ModelManifest": "model/manifest.json"
  }
}
```

Place `weights.bin` beside `manifest.json` in the run directory's `model/`.
`MaxRows` and `MaxNonzeros` bound admitted coarse inputs. `MaxWorkingBytes`
bounds estimated model working allocations. CUDA inference also checks
the available device memory at admission.
ATen allocator and library workspace usage can exceed the explicit estimate.
These checks apply to the experimental setup and inference. Local FEM uses
the host and device memory available to Palace without a project-imposed
solver memory cap.

Enabled modes check the physical residual with the original system operator
before publishing a uniform Driven result. Set `PALACE_VERIFY_RESIDUAL=1`
for the classical controls. Retain the per-RHS residual, fallback reason,
iteration counts and timing alongside total Palace time, peak memory and RF
observables. Use matched physics, mesh, excitations and tolerances.

The standalone ATen replay compared C++ and Python basis outputs on CPU and
RTX 5070 Ti with PyTorch 2.10.0+cu128. The real-probe coax case had maximum
absolute differences of `3.74e-17` on CPU and `4.22e-17` on CUDA. This is
inference parity on a captured operator. Combined Palace/MFEM/ATen execution,
end-to-end speed and RF equivalence require matched FEM comparisons.
