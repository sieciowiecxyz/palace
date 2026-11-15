# Port adjoint probe

Purpose: Document the opt-in, two-port true-DOF capture and operator-contraction probe used by the material-derivative pilot.

Read when: Preparing or reviewing a compatible fixed-mesh, single-frequency lumped-port adjoint experiment.

## Contract

The probe is disabled by default. Set exactly one of these modes in the solver environment:

- Capture: set `PALACE_ADJOINT_CAPTURE` to a path for a new output directory.
- Operator-only replay: set both `PALACE_ADJOINT_INPUT` to a prior capture directory and `PALACE_ADJOINT_OUTPUT` to a new output directory.

Do not combine capture with input/output, or set only one of input/output. The output directory must not already exist. Ordinary runs allocate no probe fields and write no probe output.

The current probe accepts only one MPI rank, fixed mesh topology (`refinement.max_it = 0`), P2 with PA1, one fixed frequency, and exactly two separate, positively referenced lumped ports numbered 1 and 2. Wave and Floquet ports are unsupported. These are deliberate guards for the pilot, not general support for arbitrary port counts or adjoint solves.

Capture stores each port's complex true-DOF field as `port1.bin` or `port2.bin`. The binary header is the eight-byte `PALADJ01` marker followed by the true-DOF count, then real and imaginary arrays of doubles. `contractions.json` records the frequency, port indices, true-DOF count, a structural DOF-ordering fingerprint, contractions and—during capture—per-port relative true-RHS residuals. The fingerprint detects ordering changes; it is not a cryptographic identity or a substitute for pinned mesh, executable, and input hashes.

Before accepting a captured field, the probe evaluates the actual system operator on it and compares that result with the corresponding excitation vector. A non-finite or above-tolerance relative true-RHS residual aborts capture. Operator-only replay records the contractions without solving either RHS or applying this residual gate; its completion is not a solved or RF-validated result.

For each source/read port pair, the report keeps the bilinear `E_read^T A E_source` contraction and the negative-control Hermitian contraction `E_read^H A E_source`, along with `E_read^T b_source` and Palace's raw port-mode value. Palace's `x.Dot(y)` conjugates `y`, so the latter contraction is computed as `applied.Dot(read_field)`. With pinned ports and calibrated normalization, the material derivative is `-E_read^T (A_plus - A_minus) E_source / (4 i omega h)`. Readout/RHS changes invalidate this fixed-port formula.

## Scope and limits

The probe supports the calibrated tiny-coax material-derivative experiment only. Its experimental contract depends on the exact frozen native executable, dependencies, input, mesh, field ordering and capture artifacts. The qualification and next gates are maintained in the [adjoint plan](../../../docs/plans/palace-adjoint.md); this page intentionally does not duplicate its measurements or receipts.

The pilot does not establish a universal N-port interface, a general adjoint solver, factorization reuse, speedup, antenna-shape gradients, optimizer behavior, or RF qualification. Shape/optimizer/RF work remains outside the completed material-derivative calibration.
