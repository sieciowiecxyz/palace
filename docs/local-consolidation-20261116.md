# Local source consolidation 2026-11-16

The `integration/local-unified-20261116` branch starts at canonical
`7b296edc53c96cfe68d8586135a4fd18e1db0ce4` and transplants the six
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
`anteny/.cache/palace-consolidation-20261116/`. Rejected startup captures are
not used; the exact rejected startup mechanism was not identified, so its
activation state has not been independently verified.
