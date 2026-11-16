# Local source consolidation 2026-11-16

The canonical `integration/local-unified-20261116` branch is now at
`cb4a39ea92324fb822730e3751e5b711a4f0683b` and includes the six optimization
commits after independent snapshot `3a0d7db` through `b196a6b`, in order.
The original independent history is retained at
`refs/archive/palace-opt-20261116/heads/master` and in an external bundle.
No snapshot was merged. The only conflict in `drivensolver.cpp` retains both
the solve timer and canonical port-adjoint capture; the timer ends before the
capture. The changed source files otherwise match the independent tip, apart
from canonical port-adjoint additions in that driver.

Focused Python tests passed; C++/CUDA build, execution, numerical and RF
qualification were not performed. This integration does not establish solver
correctness or transfer prior results to the new build. The full machine-readable
receipt and preserved dirty files reside outside this repository under
`anteny/.cache/palace-consolidation-20261116/`. The startup patch is excluded:
`palace/utils/geodata.cpp` is byte-for-byte identical to the imported
independent reference `b196a6b`; the original combined receipt also excludes
`startup.patch`.
