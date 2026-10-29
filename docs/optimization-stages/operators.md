# Operator construction: source audit and experiment ledger

**Worker:** operator-construction track
**Branch:** `opt/operators-20261029`
**Base:** `e288fe1639cef892b4cbfae0d98046a0afa62ae1`
**Status:** source audit complete; every performance hypothesis below is `TODO_TO_CHECK` (no new code or performance experiment has been run).

## Why this track exists

The latest same-mesh medium reference (1.92 GHz, both excitations, local RTX 5070 Ti) reports 121.501 s in the Palace `Operator Construction` timer, 14.71% of 825.783 s total. The corresponding CMP170HX profile reported 401.921 s in that timer, versus 121.315 s locally. The CMP interval showed about 1.08 host CPU cores used and near-zero GPU utilization, without CPU throttling. These numbers establish that the phase is worth investigating, but do not identify its exact hotspot or prove the CPU is the only cause.

The 309 observed NVRTC compilations totaled 24.323 s and module loads 0.088 s in a separate CMP run. That is a measurable contributor to that run, but it cannot explain the entire operator-construction interval. No claim is made that it is caused by the tracked constructors or that caching it would improve the representative run.

## Audited source path

- `palace/drivers/drivensolver.cpp:109-127` builds K, C, M and Curl for the initial frequency, then configures solver setup / same-frequency port reuse. K/C/M are assembled before the uniform sweep; frequency-dependent extra terms and system construction follow separately. Do not reintroduce per-frequency K/C/M assembly. Existing cross-port reuse of setup is a separate solved optimization and is not to be repeated here.
- `palace/models/spaceoperator.cpp:35-82` constructs ND, H1 and RT finite-element collection/space hierarchies, plus the 2D L2 curl space conditionally. This is a plausible one-time setup cost; no per-stage timing yet separates each hierarchy.
- `palace/models/spaceoperator.cpp:373-416` creates a `BilinearForm`, adds configured integrators, assembles coarse operators and, when multilevel is enabled, builds fine-level operators. Auxiliary operators follow a related path at `:419-440`.
- `palace/models/spaceoperator.cpp:445-...` implements the K/C/M getters and selects coefficients and integrators. Audit the full getter implementations before modifying them; exact-zero support and coarse sparsity are intentional contracts.
- `palace/fem/bilinearform.cpp:15-25` assembles quadrature data; `:28-107` constructs partial-assembly CEED suboperators; `:109-113` delegates full assembly; `:118-151` selects full vs partial assembly by FE order; `:153-200` traverses the FE-space hierarchy and assembles/coarsens operators.
- `palace/fem/libceed/operator.cpp:983+` contains full assembly dispatch. The CEED/MFEM path and full-vs-partial selection are correctness-sensitive and must be benchmarked on the same backend and build.

The timer currently aggregates multiple substeps. The audit does not establish what fraction is FE-space construction, quadrature data, JIT, CEED setup, full/partial assembly, communication, or allocations.

## Candidate experiments (not yet run)

Every candidate begins with a phase profile that attributes time; implement only if it is materially present in the representative run.

| ID | State | Hypothesis and minimal test | Promotion gate / rejection condition |
|---|---|---|---|
| OP-01 | `TODO_TO_CHECK` | Add opt-in low-overhead timers around FE hierarchy construction, each K/C/M getter, coarse/fine assembly, quadrature-data assembly, and CEED operator finalization. One representative medium run and one small supported case; record CPU time, wall time, rank count, JIT calls/time, bytes allocated, backend and timer overhead. | Keep instrumentation if overhead is below 1% and phase times reconcile to existing timer within 2%. If not, revise instrumentation before interpreting hotspots. Never treat profiled timing as the performance result. |
| OP-02 | `TODO_TO_CHECK` | If repeated compatible geometry/coefficient preparation is material, identify exact immutable data that can be shared across K/C/M or levels (quadrature geometry, basis/restriction data, coefficient samples). Probe an existing backend/API reuse path before considering a cache. | Must be keyed by mesh, FE collection/order, mapping, attributes, material/BC values, device/backend, and relevant precision. Compare assembled operator actions and final complex S/residual/energy. Reject if data invalidation is ambiguous, added memory exceeds measured savings, or end-to-end speedup is not above run-to-run noise. |
| OP-03 | `TODO_TO_CHECK` | Test whether CEED/JIT setup or repeated kernel specialization is a significant part of operator construction. Correlate OP-01 phases with NVRTC calls. Compare cold and warm execution in the same pinned image and record module/cache state. | Do not add a Palace cache unless repeated compilation dominates and cache correctness/invalidation is demonstrable. JIT-only time is not sufficient; require total runtime improvement and identical numerical outputs. |
| OP-04 | `TODO_TO_CHECK` | Inspect the full-assembly vs partial-assembly decision and per-level coarse/fine path. If the benchmark uses an expensive path, compare supported existing paths on one deliberately small representative fixture, with identical FE order, mesh, coefficients and solver tolerances. | No lowering FE order, changing mesh/medium, or relaxing solver tolerance. Require operator-action agreement, solver residual and RF checks. Reject a path change that saves construction time but makes repeated operator applies or total solve slower. |
| OP-05 | `TODO_TO_CHECK` | If OP-01 attributes a meaningful fraction to host serialization, inspect integrator dispatch/loop granularity and MPI collectives; test one narrow host-side batching or allocation-reuse change behind an opt-in switch. | Only after a named hotspot is identified. Require scaling consistency over repeated runs, no extra peak memory beyond budget, MPI/rank correctness and end-to-end improvement. No speculative parallelism or broad refactor. |

## Ledger rules

Use exactly one status per ID: `TODO_TO_CHECK`, `IN_PROGRESS`, `PASS`, `REJECTED`, `DEFERRED`. For every attempt, record commit SHA, fixture/config/mesh hash, binary/container/build IDs, exact command, warm/cold state, repetitions and median/spread, phase times, peak host/cgroup and GPU memory, operator comparison, solver raw residual, final RF/power checks and artifacts. A timed-out, OOM, incomplete, or unvalidated run is not `PASS`.

Before starting an ID, search this ledger and `PROGRESS.md` for the same question. Update this same entry instead of creating another experiment. `PASS` means the specific hypothesis and scope passed its stated gate, not that a general optimization is proven. A code change must invalidate the previous performance result and trigger integration regression.

## Files and ownership

This track owns only `palace/models/spaceoperator.*`, `palace/fem/bilinearform.*`, related narrowly scoped CEED assembly code, their tests, and this file. It must not edit shared `PLAN.md`, `MILESTONES.md`, `PROGRESS.md`, `docs/INDEX.md`, build manifests, or benchmark runner. The coordinator owns shared planning and integrates changes after all three track reports. Do not merge branches before source review and isolated tests; benchmark runs must be serialized to avoid resource contention.

No accelerator simulation, full build, cloud instance, or numerical setting change was authorized by this planning assignment.


## Wyniki nowych eksperymentów

Brak — wykonano tylko audyt źródeł. Przed pierwszą próbą uzupełnij wpis według [workflow](workflow.md). Nie oznaczać hipotezy PASS za samo przeczytanie kodu.
