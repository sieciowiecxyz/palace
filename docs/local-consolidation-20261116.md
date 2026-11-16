# Local source consolidation 2026-11-16

The canonical `codex/local-cuda` branch fast-forwards the reviewed local
integration branch (native build source `443074662`) and includes the six optimization
commits after independent snapshot `3a0d7db` through `b196a6b`, in order.
The original independent history is retained at
`refs/archive/palace-opt-20261116/heads/master`. Temporary bundles and old clean
checkouts were removed after every bundled head was verified reachable here.
No snapshot was merged. The only conflict in `drivensolver.cpp` retains both
the solve timer and canonical port-adjoint capture; the timer ends before the
capture. The changed source files otherwise match the independent tip, apart
from canonical port-adjoint additions in that driver.

The full native library/executable/adapter build and loader/plugin/NVRTC checks
passed. All eight native recovery controls and one fresh F6 passed the unchanged
preregistered gates: six true RHS <=1e-6, matching iterations, complex S <=1e-7,
field/power/VI relative comparisons <=1e-6 against combined-20261115. This is
scoped numerical agreement, not new RF-target qualification or a general speed
claim. Results are indexed in Anteny research/palace-opt/source-consolidation-20261116/.
The prepared workspace source now points here. Its former repository and duplicate
build outputs were removed after validation; committed history remains here.
Unique legacy evidence is in Anteny .cache/palace-cleanup-20261116/.
The full machine-readable receipt and preserved dirty files
reside outside this repository under
`anteny/.cache/palace-consolidation-20261116/`. The startup patch is excluded:
`palace/utils/geodata.cpp` is byte-for-byte identical to the imported
independent reference `b196a6b`; the original combined receipt also excludes
`startup.patch`.
