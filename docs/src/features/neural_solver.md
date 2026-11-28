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

For a single-GPU run built with CUDA and Umpire, the opt-in environment
setting `PALACE_NATIVE_MANAGED_POOL=1` backs the MFEM/HYPRE device pool
with CUDA managed memory and retains ordinary host allocation. Leave
`MFEM_MEMORY` and `MFEM_DEVICE` unset when using this profile. Use the
same allocation profile for every arm in a timing comparison.

On the 3.8 GHz coax development case, the stock ML-enabled Palace build
`582c95256` on one RTX 5070 Ti completed three runs of each arm. The
median Palace times were 7.577 s for classical right FGMRES, 8.154 s for
Jacobi, 8.820 s for the untrained basis and 11.098 s for the learned basis.
Both ports met the original-system tolerance in all 12 runs. In all six
learned RHS solves, setup produced rank eight and Palace used classical
continuation after the 20-iteration trial. The largest absolute difference
in a complex S entry between paired classical and learned runs was
1.15e-8. These results apply to the coax development case.
