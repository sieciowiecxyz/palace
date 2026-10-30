# OP-06 M3 — three full medium pairs, 2026-10-30

## Current status after OP-06-E19 — repeated full pairs

**All3 matched pairs PASS completion and the independent preregistered RF gates.**
No production promotion was performed; root decides final PRE gate/integration.
Qualified scope: this unchanged medium 1.92GHz/two-port case, rank1/OMP1 CUDA/UVM
RTX5070Ti and current pinned native. Other frequencies/geometries/MPI remain NOT RUN.
The first-pair record below preserves its original pending-review state chronologically.

## First-pair execution record (historical scope)

`PASS_COMPLETION_ONLY`; **RF equivalence review and promotion are root-owned and
pending**. Exactly two authorized sequential full solvesets finished at 1.92 GHz,
both ports, with the unchanged medium mesh/order/materials and full postprocessing.
No additional retry, parameter change, build, cloud job, service action or promotion.
Repeated balanced pairs, other frequencies/geometries/MPI and full RF qualification
remain NOT RUN. Default remains GSLIB; MFEM remains explicit opt-in.
Previous structural/749-unit/CUDA synthetic gates: [M2 ledger](operators.md).

## Preregistered execution

Artifacts under ROOT `/home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/`
`M3-OP06-full-20261030/`: root-owned `preregister.json`, exact `pair1-B-mfem/plan.json`
and `pair1-A-gslib/plan.json`. The worker executed only:

```sh
cd /home/sieciowiec/dev/cpp/palace
/usr/bin/python3 tools/stage_probe_run.py execute /home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/M3-OP06-full-20261030/pair1-B-mfem/plan.json
/usr/bin/python3 tools/stage_probe_run.py execute /home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/M3-OP06-full-20261030/pair1-A-gslib/plan.json
```

B ran first, then A only after B exit0/fullcomplete/two solves/raw-relative-RHS PASS.
Root received the first completion report before A. No stage stop/trace, all18 base
flags retained; only explicit locator choice differs. Both use compiler-source
`b834bebb7a9c774cdb1028352bae62cefc8f4666d281570e26e4ccf7d3a8d46e`,
lib `bc7a8f844f2c0e2374a0ae9dfc36438917a4382b604cde0ec11137c9fe1f26e5`,
adapter3f25, original config9f068/mesh2af, image43ac. Runner checks before/after
identity PASS. All preregistered controlled plan keys compare equal.
Runtime policy each: CUDA/UVM, rank1/OMP1/8CPU,68GiB/noSwap/core0/networknone,
1800s hard deadline, canonical per-user host lock, inactive/dead Strata/PID0
prelaunch,8GiB reserve/6GiB during-run memory guard. No guard or OOM occurred.

## OP-06-E17 / E18 — actual completion and resources

| Observed metric | B: MFEM | A: default GSLIB |
|---|---:|---:|
| Runner wall, s |651.405685|740.757610|
| Palace total, s |649.834812|738.750800|
| Operator construction, s |18.675184|119.911640|
| Solver setup, s |92.223674|91.668123|
| Coarse solve exclusive, s |163.429151|161.518659|
| Preconditioner exclusive, s |249.290564|242.807934|
| Linear solve exclusive, s |62.948716|60.402893|
| Postprocessing exclusive, s |7.197751|7.110825|
| Far fields exclusive, s |2.185063|2.174249|
| Disk IO, s |19.052822|18.611402|
| GMRES iterations / solves |85 / 2|85 / 2|
| Maximum final raw relative RHS residual |8.337233310436e-7|8.339276206246e-7|
| Sampled cgroup peak, GiB |57.026970|65.709187|
| Minimum sampled host available, GiB |19.547791|12.916214|
| Global GPU sampled peak, MiB |15860|15863|
| Ordinary postpro file bytes |2828760|2828880|

Both exit0, complete=true, two solves complete, residual<=1e-6; all8 CSV schemas
and row identities complete including10024 farfield rows and164 E/B probes for
each source. Same1,700,660 order2 elements/11,869,460 ND unknowns. Both own runtime
containers removed; `podman ps` afterwards shows no Palace campaign container.
No fake diagnostic completion: solver_executed=true; rf_result/rf_qualified=false.

MFEM actual backend marker: selected=mfem/reason=interior/probes164;
initial141 + rescued23, fixedcap128/tried72/remaining0, locator wall1.714990161s.
A has no MFEM/search markers. No per-internal-stage trace in either full run.
DOF/model/control proof and complete output hashes are retained in
`pair1-execution-summary.json`; raw logs, telemetry, state, resource-policy,
full-result and postpro/palace.json remain in each exact run directory.

One-pair observations: operators -101.236456s; full Palace total -88.915988s
(-12.0360%, about1.137x); cgroup peak -8.682217GiB (-13.21%). These are one
B-then-A pair, not balanced repeats/medians or a general speedup claim. Difference
in the rest of the solve offsets part of the constructor benefit. Palace process
RSS is not substituted for cgroup memory; global GPU peak is not per-process
VRAM or physical UVM traffic. Ordinary result bytes are not measured physical SSD
writes; no swap/basis/workspace spill was introduced.

**Numerical caveat for root review:** coarse CSR structure hash is identical
`311429ba9b666a4a`, but value hash is B `f6efcc60564e0832` vs A
`615f296eb8461863`. This is not bitwise matrix-equivalence evidence. Same85iterations
and residual PASS do not settle the RF gate. Observed diagonal magnitude-derived
VSWR values are B1.599832499638/1.499557611055 vs A1.599832530915/1.499557624729,
but independent complexS/field/power/farfield comparison is still required.

Root applies the preregistered independent gates: max complexS delta1e-5,
maxVSWR delta.001, complex-field relL2<=1e-5, power residual<=.02,
farfield-to-flux error<=.02. Worker did not invoke old antenna validator (it rejects
new compiler hashes), relax thresholds, mark qualified, or start more simulations.
Next action is root RF review; repeat pairs require another explicit resource slot.

## OP-06-E19 — exact authorized repeats and all-sample analysis

Root first reviewed pair1 RF PASS, then supplied `preregister-repeats.json`.
Worker executed exactly four additional prepared full plans with the same CLI above,
in this order: pair2-A-gslib → pair2-B-mfem → pair3-B-mfem → pair3-A-gslib.
Every run exit0/complete/two solves/85iterations, final raw relative_rhs<=1e-6.
No fail, retry, changed parameters, native build, services/cloud/push or extra runs.
After pair2 the existing root `tools/stage_rf_compare.py A B --output pair2-rf.json`
returned exit0/PASS; root received the necessary report before pair3.
After pair3 the same checker produced `pair3-rf.json` exit0/PASS. Checker bytes
were not modified. `production_promoted=false` throughout.

Each run retained sourceb834/libbc7/adapter3f25/config9f068/mesh2af/image43ac,
all18baseflags, no trace, rank1/OMP1/8CPU/68GiB/noSwap/core0/networknone/hard1800s,
canonical lock, inference prelaunch and memory reserve/guard. All13 preregistered
controlled plan fields compare equal across ALL6 runs. Actual MFEM in all3 runs
selected164=141+23/cap128/tried72/remaining0; controls have no experimental marker.
No OOM/guard failure, all own runtime containers removed. Sources/native unchanged.

### Individual observations (all samples included)

| Pair | Order | Palace A / B, s | Runner A / B, s | Cgroup A / B, GiB |
|---|---|---:|---:|---:|
|1|B→A|738.750800 / 649.834812|740.757610 / 651.405685|65.709187 / 57.026970|
|2|A→B|738.559264 / 637.773216|740.617104 / 639.537113|65.826000 / 57.057552|
|3|B→A|738.067638 / 637.425778|739.926736 / 639.129045|65.713074 / 57.029964|

### Medians and min/max, n=3 per backend

A=GSLIB, B=experimental MFEM; notation median [min,max]. Palace phase durations
are the existing **exclusive** timer categories, not added inclusive profiler spans.
No best sample omitted: slower first B remains in every statistic.

| Metric | A median [min,max] | B median [min,max] |
|---|---:|---:|
|Palace total s|738.559264 [738.067638,738.750800]|637.773216 [637.425778,649.834812]|
|Runner wall s|740.617104 [739.926736,740.757610]|639.537113 [639.129045,651.405685]|
|Sampled cgroup peak GiB|65.713074 [65.709187,65.826000]|57.029964 [57.026970,57.057552]|
|CoarseSolve s|161.468731 [161.252031,161.518659]|161.591402 [161.349314,163.429151]|
|DiskIO s|18.611402 [18.512481,18.715227]|18.878056 [18.763973,19.052822]|
|FarFields s|2.166359 [2.149589,2.174249]|2.147309 [2.146513,2.185063]|
|Initialization s|6.453156 [6.413957,6.474651]|6.709821 [6.500153,6.818272]|
|LinearSolve s|60.328789 [60.328039,60.402893]|60.295721 [60.288553,62.948716]|
|MeshPreprocessing s|28.057495 [28.014661,28.154249]|28.276390 [27.951181,28.324819]|
|OperatorConstruction s|119.911640 [119.539133,120.265863]|18.465894 [18.454056,18.675184]|
|Postprocessing s|7.055833 [6.988595,7.110825]|7.086404 [7.077330,7.197751]|
|Preconditioner s|242.553670 [242.444754,242.807934]|242.761841 [242.315979,249.290564]|
|Setup s|91.668123 [91.582628,92.084119]|91.846506 [91.814222,92.223674]|

### Paired ratios and deltas

Ratios are A/B **within each pair**, then summarized; they are not a ratio of
independently selected extrema. Full JSON additionally retains paired phase deltas
and ratios for every nonzero timer, all six raw samples and all resource witnesses.

| Metric | A/B ratios pairs1,2,3 | Median [min,max] reduction B vs A |
|---|---|---:|
|palace_s|1.136829, 1.158028, 1.157888|13.635859% [12.035992,13.646305]|
|wall_s|1.137168, 1.158052, 1.157711|13.622658% [12.062235,13.648077]|
|cgroup_peak_gib|1.152248, 1.153677, 1.152255|13.213671% [13.213094,13.320645]|

Median paired savings: Palace100.641860s; runner100.797691s; cgroup8.683109GiB.
GlobalGPU sampled peaks across all6 runs15860–15863MiB; this is **not** a measured
VRAM saving or physical UVM counter. Three pairs with reversed order reduce a
single-order confound but do not establish universal statistical/hardware scaling.

### Full RF gates across all3 pairs

Each comparison used all finite CSV rows/grids, both sources/all164complex probes,
complex S/VSWR, domain energy/V/I, complex farfield and flux/power tests. No gate
was relaxed to account for varying coarse-matrix value hashes. All passed:

| Pair | Max complex ΔS | Max ΔVSWR | Max probe relL2 | Max complex FF relL2 | Max FF/flux relative error |
|---|---:|---:|---:|---:|---:|
|1|1.735762e-08|3.127676e-08|1.163909e-06|2.785009e-08|1.258772e-02|
|2|1.731714e-08|4.317508e-08|1.363177e-06|2.865832e-08|1.258772e-02|
|3|1.809469e-08|1.871165e-08|1.269598e-06|2.906500e-08|1.258772e-02|

Reference gates remain complexS1e-5/VSWR.001/complexfields1e-5/power residual.02W/
FF-to-flux relative.02. All6 full-result metadata retain RF-qualified=false because
the independent pair reports carry RF equivalence, not automatic promotion.

Evidence: ROOT campaign `repeated-performance.json` (all raw values, medians/min/max,
paired ratios, identities, residuals, backend witnesses and report hashes),
`pair1-rf.json`, `pair2-rf.json`, `pair3-rf.json`, and all6 exact run directories.
No raw artifacts staged in Git. Only own operator ledgers updated; root owns INDEX
registration/integration. Worker STOP after this report; no extra full RF jobs.

## Independent checker/docs review before local doc-only commit

Reviewed root `stage_rf_compare.py`, its18 synthetic regression tests, the isolated
runner-lock test fix, source-unit proof, physical normalization, native angular
sample generation, all3 stored pair reports and all-sample performance summary.
No blocker within the declared rank1/two-port/PEC+dielectric medium scope.
Independent rerun:18 RF tests PASS and25 runner tests PASS (43total); no live host
lock acquired because unit setup patches only the test-local path. Real-flock
exclusive regression still exercises an actual lock on its isolated path.
Read-only re-evaluation of ALL3 actual pairs PASS, both source-unit proofs true,
no production promotion. Source hash remains b834. No GPU/native build/run.
Docs-garden ROOT index/plan/checkpoints PASS (only existing AGENTS length advisory);
root registered this ledger, preserving unrelated Ampere work. Minor root MD fixes
clarify historical M0 HEAD/prototype identity and M3.2 wording, no gate changes.
This is not new numerical scope: M4 interaction/PRE qualification, sweep, other
geometry/frequency/MPI and final production promotion remain root-owned/NOT RUN.
