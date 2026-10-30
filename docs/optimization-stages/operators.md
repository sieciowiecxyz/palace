# Operator construction: source audit and experiment ledger

## Bieżąca decyzja M6 — PROMOTE_PROFILE / M6 CLOSED

OP-06 zakwalifikowano dla uniform Restart1, obu portów i opisanych medium na5070Ti.
TrzyparyOP i combined oraz1,71/2,69/3,80GHz+inna geometria RF PASS.
Kod po lokalnymmerge root: source95822/lib048f; exactflags i ograniczenia w
[wynikach](results.md) i [audycie](../milestones/stages-final-audit.md).
DefaultGSLIB i konserwatywnefallbacki pozostają. LegacyRestartCSVFAIL odziedziczony,
poza profilem; nie poprawiono go ani nie kwalifikowano jakoPASS.
Historyczne IN_PROGRESS poniżej są rozstrzygnięte kolejnymi wpisami/raportami.


## Stan bieżący po kwalifikacji prototypu M2 — 2026-10-30

Ta tabela określa aktualną kolejkę; wcześniejsze wpisy zachowują historyczne etapy próby.
PASS jest zakresowy; nowa optymalizacja wymaga osobnych testów M2/M3.

| ID | Stan i zakres |
|---|---|
| OP-01 | PASS — M1 pełne pokrycie i para ON/OFF; brak nowego speedupu |
| OP-02 | TODO_TO_CHECK — reuse danych tylko przy nowym potwierdzonym koszcie |
| OP-03 | DEFERRED — JIT nie wyjaśnia GSLIB104,52s |
| OP-04 | DEFERRED — K/C/M mały koszt względem geometrySetup |
| OP-05 | TODO_TO_CHECK — Umpire/OMP2 baseline crash; oddzielnie od nowego locatora |
| OP-06 | PASS (M2 + scoped M3) — structural/tiny749/CUDA synthetic + all3 matched full medium pairs/RF gates; production promotion root-owned |

**Worker:** operator-construction track
**Branch:** `opt/operators-20261029`
**Base:** `ff97f08bc936495673017aa12471f4be5ce110a0`
**Status:** M0/M1 closed; operator prototype M2 qualified for structure, curved
probe interpolation and actual CUDA/UVM synthetic complex ND/RT fields. One
same-build operators-only pair measured113.196→12.166s and12.742→3.633GiB cgroup
RAM; this is not repeated medians or full-solver memory/time. Default remains GSLIB;
`PALACE_PROBE_LOCATOR=mfem` is explicit and conservative whole-batch fallback stays.
**M3 update:** [three full pair ledger](operators-m3.md): all6 full-medium runs at
1.92GHz/both ports completed and all3 independent RF comparisons PASS. Median Palace
time738.559→637.773s/cgroup65.713→57.030GiB; production promotion is root-owned.
This qualifies the unchanged case, not other geometries/frequencies/MPI.
Current compiler sourceb834/nativebc7 remain frozen; source review must not change
the qualified product bytes.


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
| OP-01 | `IN_PROGRESS` | Add opt-in low-overhead timers around FE hierarchy construction, each K/C/M getter, coarse/fine assembly, quadrature-data assembly, and CEED operator finalization. One representative medium run and one small supported case; record CPU time, wall time, rank count, JIT calls/time, bytes allocated, backend and timer overhead. | Keep instrumentation if overhead is below 1% and phase times reconcile to existing timer within 2%. If not, revise instrumentation before interpreting hotspots. Never treat profiled timing as the performance result. |
| OP-02 | `TODO_TO_CHECK` | If repeated compatible geometry/coefficient preparation is material, identify exact immutable data that can be shared across K/C/M or levels (quadrature geometry, basis/restriction data, coefficient samples). Probe an existing backend/API reuse path before considering a cache. | Must be keyed by mesh, FE collection/order, mapping, attributes, material/BC values, device/backend, and relevant precision. Compare assembled operator actions and final complex S/residual/energy. Reject if data invalidation is ambiguous, added memory exceeds measured savings, or end-to-end speedup is not above run-to-run noise. |
| OP-03 | `TODO_TO_CHECK` | Test whether CEED/JIT setup or repeated kernel specialization is a significant part of operator construction. Correlate OP-01 phases with NVRTC calls. Compare cold and warm execution in the same pinned image and record module/cache state. | Do not add a Palace cache unless repeated compilation dominates and cache correctness/invalidation is demonstrable. JIT-only time is not sufficient; require total runtime improvement and identical numerical outputs. |
| OP-04 | `TODO_TO_CHECK` | Inspect the full-assembly vs partial-assembly decision and per-level coarse/fine path. If the benchmark uses an expensive path, compare supported existing paths on one deliberately small representative fixture, with identical FE order, mesh, coefficients and solver tolerances. | No lowering FE order, changing mesh/medium, or relaxing solver tolerance. Require operator-action agreement, solver residual and RF checks. Reject a path change that saves construction time but makes repeated operator applies or total solve slower. |
| OP-05 | `TODO_TO_CHECK` | Runtime M0 evidence now identifies CPU/OMP2 allocator failure in mesh bounds (details E05/E06); check allocator reentrancy/thread safety before parallel host work.  If OP-01 attributes a meaningful fraction to host serialization, inspect integrator dispatch/loop granularity and MPI collectives; test one narrow host-side batching or allocation-reuse change behind an opt-in switch. | Only after a named hotspot is identified. Require scaling consistency over repeated runs, no extra peak memory beyond budget, MPI/rank correctness and end-to-end improvement. No speculative parallelism or broad refactor. |

## Ledger rules

Use exactly one status per ID: `TODO_TO_CHECK`, `IN_PROGRESS`, `PASS`, `REJECTED`, `DEFERRED`. For every attempt, record commit SHA, fixture/config/mesh hash, binary/container/build IDs, exact command, warm/cold state, repetitions and median/spread, phase times, peak host/cgroup and GPU memory, operator comparison, solver raw residual, final RF/power checks and artifacts. A timed-out, OOM, incomplete, or unvalidated run is not `PASS`.

Before starting an ID, search this ledger and `PROGRESS.md` for the same question. Update this same entry instead of creating another experiment. `PASS` means the specific hypothesis and scope passed its stated gate, not that a general optimization is proven. A code change must invalidate the previous performance result and trigger integration regression.

## Files and ownership

This track owns only `palace/models/spaceoperator.*`, `palace/fem/bilinearform.*`, related narrowly scoped CEED assembly code, their tests, and this file. It must not edit shared `PLAN.md`, `MILESTONES.md`, `PROGRESS.md`, `docs/INDEX.md`, build manifests, or benchmark runner. The coordinator owns shared planning and integrates changes after all three track reports. Do not merge branches before source review and isolated tests; benchmark runs must be serialized to avoid resource contention.

No accelerator simulation, full build, cloud instance, or numerical setting change was authorized by this planning assignment.


## Wyniki nowych eksperymentów

### OP-01-M0-E01 — zgodność źródeł i zachowanej referencji (`PASS`, provenance only)

Owner: GPT-6.1 Sol high / `opt/operators-20261029`, 2026-10-29; baza `ab4b3a6dbd`.
Sprawdzona historia: audyt OP-01 wskazywał brak dowodu source↔runtime; ten test
uzupełnia M0.1, nie powtarza profilu JIT/CMP ani badania szybkości.

`tools/stage_operator_reference.py` odtwarza dokładnie zakres `tools/dev.py:source_hash`:
400 compiler inputs z CMakeLists/palace/cmake/tools/adapter. Obecny worktree i frozen
SM120 r3 mają ten sam hash **a6ec732f11cc7fe920365ba2aae354b68fe97e81f732d5afd4659ed5187c3338**;
lista odmiennych compiler inputs jest pusta. Różne Git SHA dokumentacji nie oznacza
różnicy źródeł tego solvera. Sprawdzono też trzy pliki native, hash build-manifest,
manifest zachowanego runu, jego pinned image/native-from-image oraz config hash.
Wszystkie 11 kontroli PASS (w tym zgodność settings źródła i bundle). Nie uruchamiano obrazu ani solvera; to powiązanie zachowanej
proweniencji, nie nowa inspekcja zawartości obrazu i nie RF qualification.

- Bundle: `/home/sieciowiec/dev/cpp/palace/artifacts/m7-sm120-bundle-r3-20261022`.
- Run: `/home/sieciowiec/dev/python/anteny/artifacts/tshaped/port-repair-20261028/rear-route-sma-only/run-local-stages-20261029`.
- Obraz rzeczywistego runu: `43ac46f6430cf44d7a2da0a618a0f5c67c6965cca2fde510f2a96116333e6d76`.
- Builder: `296248155e55ca84f1e362d6a2926682f78c4f0290ab26158a265300244fb55d`.
- Runtime base `43cd...` i generic qualified `65d...` w settings nie zastępują obrazu `43ac...`.
- Native SHA: libpalace `1874bd95a35840fcab57df549021be5a18683306066d05a5666967c56475ffeb`,
  executable `a96bc75796a3a358647431c9b16b3f18a7c71d2d5803c855f648af4fdd53e0b5`,
  adapter `3f25ec819e1a1d053c544afc63b4154103ffa23a7bdda48af547b211836dfd85`.
- Zachowano `numerically_validated: false` globalnego manifestu; nie rozszerzano zakresu kwalifikacji.
- Dowody: `artifacts/optimization-stages/operators-m0/source-reference.json` w tym worktree.

Reprodukcja bez GPU/builda:

```sh
python -m unittest tools.tests.test_stage_operator_reference
python tools/stage_operator_reference.py --bundle /home/sieciowiec/dev/cpp/palace/artifacts/m7-sm120-bundle-r3-20261022 --run /home/sieciowiec/dev/python/anteny/artifacts/tshaped/port-repair-20261028/rear-route-sma-only/run-local-stages-20261029 --output artifacts/optimization-stages/operators-m0/source-reference.json
```

4 testy Python PASS (0,018 s): zgodność hashera z narzędziem builda, brak wymyślonej
RF qualification, invalidation po nowym compiler input i po podmianie native/config/image/settings.
Ponowić tylko po zmianie któregokolwiek compiler input, native, manifestu/obrazu lub fixture.
Nowy kod narzędzia/tests nie jest compiler input; nie wymaga rekompilacji solvera.
OP-01 profilowanie nadal `TODO_TO_CHECK`, pozostałe OP-02–05 bez zmian.

### M0.3 — krótki harness operatorów: istniejący zamiast nowego silnika (`READY`, execution `NOT RUN`)

Źródła już mają no-GMRES testy operator action:

- `test/unit/test-spaceoperator.cpp:99` — exact-zero coarse/fine support.
- `test/unit/test-spaceoperator.cpp:155` — trójpoziomowy ND/H1, curved tetra/hex,
  anisotropic material; porównuje cache QData z niezależnym assembly dla seedów42/314159,
  próg relL2 **2e-13** (zachować ostrzejszy niż ogólny plan1e-10).
- `test/unit/test-libceed.cpp:2351` — istniejący `3D libCEED Benchmarks` zawiera
  assembly/full assembly/action; benchmark_order/ref_levels oraz QData są parametrami.
  To syntetyczny zakres i nie odwzorowuje czasów assembly anteny.

Po uzyskaniu slotu/zgody należy zacząć od pierwszych dwóch istniejących testów,
bez solve, na CPU i opcjonalnie CUDA. Przykład argv **wewnątrz zgodnego środowiska**:

```sh
timeout 120s <cached-unit-tests> 'SpaceOperator retains coarse support while omitting fine exact zeros' --device cpu --backend /cpu/self
timeout 120s <cached-unit-tests> 'CPU preconditioner quadrature data preserves the multigrid operators' --device cpu --backend /cpu/self
```

`<cached-unit-tests>` jest jawnie jeszcze nierozstrzygniętą lokalizacją, nie gotową
komendą Luna. W M0 koordynator musi sprawdzić obecność Catch2/targetu i wyznaczyć
osobny cached test build-dir. Nie należy `cmake --build ... --target unit-tests`
na solver-only `/opt/palace-cudss-build` bez potwierdzenia konfiguracji; standardowy
root test target jest definiowany w `test/unit/CMakeLists.txt`, solver-only subproject
może go nie zawierać. Nie włączać pełnego superbuilda dla dwóch małych testów.

Przed porównaniem zmian koordynator używa istniejącego cached dependency builder,
`/opt/view`, MFEM/HYPRE/libCEED z niego; `tools/dev.py build --jobs 2` rekonfiguruje
tylko `palace/`, zachowuje installed dependencies i ccache. Worktree ma oddzielne
build/output; współdzielony ccache i slot zapewnia koordynator, nie agent.
Nowy standalone action probe byłby dopiero fallbackiem po ustaleniu, że istniejący
unit harness nie jest tanio dostępny. Nie dublować obecnych porównań QData.

Representative medium assembly-only jest **NOT IMPLEMENTED / NOT RUN**. Minimalny
przyszły hook powinien zatrzymać produkcyjny driven flow po `GetStiffnessMatrix`,
`GetDampingMatrix`, `GetMassMatrix`, `GetCurlMatrix` (`drivensolver.cpp:114–117`),
przed utworzeniem `ComplexKspSolver`. Mesh load→nondimensionalization→partition→refine→FE
hierarchy pozostają produkcyjne; marker `diagnostic only / no RF result`, bez
preconditionera/cuDSS/GMRES/postprocessing. Wymaga wspólnego patcha driver/runner
od koordynatora w M1; agent nie zmienia tych współdzielonych plików. Samo zabicie
procesu timeoutem nie daje PASS ani kompletnego pomiaru assembly.

Zgłoszenie do koordynatora: potwierdzić lokalizację i sposób cached buildu unit-tests;
wybrać hook assembly-only dopiero po M0; wykonać CPU/CUDA smoke sekwencyjnie po
uzyskaniu zgody dotyczącej Straty. Cała nowa kwalifikacja obliczeniowa `NOT RUN`.


### OP-01-M0-E02 — cache i wejście assembly-only (`READY`, native build/test `NOT RUN`)

Root zezwolił na read-only inspect starych zatrzymanych builderów. Wystartowano
wyłącznie `palace-pr-builder` i `palace-dev-7ad846998318` (entrypoint sleep),
odczytano metadata/cache i zatrzymano oba; nie kompilowano ani uruchamiano binarek.
`palace-pr-test` pozostał zatrzymany; jego `/work` wskazuje
`/home/sieciowiec/dev/cpp/palace/artifacts/upstream-pr`, dlatego pliki odczytano z hosta.
Nie zmieniono /opt, mountów, cache, deps ani starych artefaktów PR.

Ustalenia (sprawdzone, nie przypuszczenia):

| Cache | Wynik |
|---|---|
| `palace-dev-7ad846998318:/opt/palace-cudss-build` | Dokładne native SHA M7 r3: libpalace1874bd95…, binarka a96bc757…; Ninja/Release, GCC13, C++17, CUDA12.9.1, fmt11.0.2 z `/opt/view`; brak Catch2 i `unit-tests` |
| `palace-pr-builder:/opt/palace-cudss-build/test/unit/palace-unit-tests` | Istnieje, 7 891 360 B, SHA d596a78d3f45377b92f6bc93f421e67fe632e1f24e89da781f6b0debe48caf52; source/ABI **niezgodne z dowodem M7** |
| Stary PR native `libpalace.so` | SHA92ea6386db21dc3859c42b85a94c30aab029989a1a96ba2ba7203147f7d3bda9; 60 nagłówków Palace różni się od M7, także test-spaceoperator i test-libceed mają różne źródła |
| Catch2 w PR builderze | `/opt/pr-deps/include/catch2`, `/opt/pr-deps/lib/libCatch2.a`, config `/opt/pr-deps/lib/cmake/Catch2`; cały `/opt/pr-deps` ma247plików/4 711 006 B |
| Zależności obu builderów | Wspólny bazowy image296248…; MFEM4.9.0, HYPRE3.1.0, libCEED0.12.0/MAGMA2.10.0, OpenMPI5.0.10 |

Stary PR dodatkowo podmienia `/opt/view/include/fmt` na fmt12.1.0. Nie należy
podstawiać jego unit binary/lib ani całego include-prefix do M7 i nazywać tego
kwalifikacją nowego kodu. Te same nazwy testów znalezione w ELF nie dowodzą ABI.
Z PR można bezpiecznie *przygotować osobną kopię* samych Catch2 headers/lib do
świeżej kompilacji testu. Skopiować tylko `include/catch2` i `libCatch2.a`, bez fmt.

Najtańsza izolowana ścieżka builda (polecenia proponowane rootowi, **NOT RUN**):

```sh
# Snapshot zachowanego dev cache do osobnego lokalnego obrazu; stary cache pozostaje.
podman commit --pause=false palace-dev-7ad846998318 localhost/palace:stage-cache-sm120-20261029
# Nowy builder z tym obrazem, root integrated source jako /src/palace:ro,
# root .cache/ccache jako /cache/ccache; network none, bez GPU do kompilacji.
# Zachować /opt/palace-cudss-build i instalacje /opt/view z snapshotu.
podman exec <new-stage-builder> cmake --build /opt/palace-cudss-build --target libpalace palace --parallel 2
```

Koordynator musi utworzyć builder i zapisać jego dokładne ID/env/mounty oraz stan
bazowego cache, zamiast wpisać placeholder do gotowego zlecenia Lunie. Nie używać
`tools/dev.py build` na tej klonowanej instancji bez świadomego kontraktu manifestu:
standardowy helper sprawdza stały image/settings i nie zna nowego snapshot ID.
Nie trzeba rekompilować MFEM/HYPRE/libCEED. Docelowo zmieniają się dwa TU:
`driver.cpp` (root/preprocessing) i `drivers/drivensolver.cpp` (ten patch); zmiana
stempla Git/reconfigure może dotknąć także main.cpp, dlatego koszt zweryfikować
przez dry-run Ninja, bez obietnicy dokładnie dwóch wywołań kompilatora.

Dla dwóch istniejących małych testów przygotowano
`tools/stage_operator_unit_main.cpp`: inicjalizuje MPI/MFEM/HYPRE/libCEED,
uruchamia Catch, finalizuje; nie linkuje całego regression harness ani solvera.
Do kompilacji wystarczą **2 TU**: ten main i aktualny `test/unit/test-spaceoperator.cpp`.
Proponowany compile/link (w nowym builderze, po skopiowaniu wyłącznie Catch2):

```sh
# Do BOTH compile calls dodać dokładne include paths/defines z cached M7 compile rule;
# nie brać flag z PR (fmt12/C++20) i nie udawać, że poniższy skrót już był testowany.
ccache /opt/view/bin/mpicxx -std=c++17 -O2 -fopenmp -DFMT_HEADER_ONLY=1 -I/src/palace/palace -I/stage-deps/include -I/opt/view/include -I/usr/local/cuda/include -I/opt/cudss/include -c /src/palace/tools/stage_operator_unit_main.cpp -o /stage/operator-main.o
ccache /opt/view/bin/mpicxx -std=c++17 -O2 -fopenmp -DFMT_HEADER_ONLY=1 -I/src/palace/palace -I/stage-deps/include -I/opt/view/include -I/usr/local/cuda/include -I/opt/cudss/include -c /src/palace/test/unit/test-spaceoperator.cpp -o /stage/operator-cases.o
/opt/view/bin/mpicxx -fopenmp /stage/operator-main.o /stage/operator-cases.o /stage-deps/lib/libCatch2.a -L/opt/palace-cudss-build -lpalace -L/opt/view/lib -lmfem -lHYPRE -lceed -lfmt -L/usr/local/cuda/lib64 -lcudart -Wl,-rpath,/opt/palace-cudss-build:/opt/view/lib:/opt/cudss/lib:/usr/local/cuda/lib64 -o /stage/operator-unit-tests
```

Ten build wymaga slotu i weryfikacji link dependencies; kompilacja/numerics są
**NOT RUN**, nie jest to gotowy dowód poprawności lub znanej ceny builda. Main
akceptuje `--device`, `--backend`, `--jit-source`; default CPU `/cpu/self`, OMP z
istniejącej funkcji ConfigureOmp. Jawne argv wyboru dwóch testów z E01 pozostają.
Nie traktować starego PR binary jako zamiennika, gdy kompilacja nowego testu zawiedzie.

Hook assembly-only zaimplementowano w `DrivenSolver::SweepUniform` po K/C/M/Curl,
przed `ComplexKspSolver`: `PALACE_STAGE_STOP=operators` → `StageProbeComplete{Operators}`.
Wspólny `utils/stageprobe.hpp`, guard single-rank/DRIVEN/uniform/noAMR, catch i końcowa
metadata należą do roota/preprocessing. Ten branch celowo czeka na integrację headera;
nie budować go samodzielnie bez wspólnego patcha. `PostOperator` jest tworzony przed
assembly, więc mogą powstać puste nagłówki tabel; brak wierszy S i diagnostic marker
muszą odróżniać to od RF solve. Root runner nie może traktować exit0 jako RF PASS.
Normalny przepływ przy nieustawionym PALACE_STAGE_STOP zachowany.

Po hooku źródła **oczekiwanie nie pasują** do starego manifestu: narzędzie raportuje
jedyną różnicę `palace/drivers/drivensolver.cpp`; expected-invalidation PASS zapisano
w `artifacts/optimization-stages/operators-m0/source-reference-after-hook.json`.
Poprzedni E01 provenance PASS dotyczy przypiętej bazy sprzed patcha. Po wspólnej
integracji konieczny nowy manifest źródeł i nowa, osobna binarka. Brak nowej deklaracji
speedupu. Next: root review, wspólny build slot, tiny diagnostic i operator action.


### OP-01-M0-E03 — rzeczywisty izolowany cached build (`PASS`, compilation only)

2026-10-30, root przydzielił slot i zamroził integrated źródła.
Source hash `131d5da3bf54eea5375ce41dfcf718aa9d2e466b8bf6a2abedcb60e152e2d8eb`
identyczny przed/po buildzie i świeżych dwóch TU testu. Settings0d605d50….
Snapshot starego zatrzymanego dev cache: image
`219cb96c3b3956f78beaf037f3ebb52bd02ab014765ab3918c9d21a72dae7e9e`,
nowy builder `palace-stage-m0-build-20261030`; memory32GiB/noSwap,2CPU,
networknone/noGPU, readonly rootsources, współdzielony ccache, osobne writable artefakty.
Oryginalne kontenery, /opt cache, frozen bundle i root build/sm120 nietknięte.

Dry-run: **3TU** (driver,drivensolver,main), zero MFEM/HYPRE/libCEED rebuild.
`cmake --build ... --target libpalace palace --parallel2`: **10,380s**;
setup+native **13,640s**, cały build/test-harness attempt **22,190s**.
Nowy mały operator-main + aktualne test-spaceoperator skompilowane/linkowane w **5,799s**,
z dokładnymi flagami cached M7 (GCC13.3/C++17/fmt11/Eigen/Scn), bez starych PR flags.
Przekopiowano tylko Catch2 headers/lib:3 211 634B; bez fmt12. Nie był potrzebny
nowy superbuild ani pobieranie zależności. Source i binaria mają osobny manifest,
`numerically_validated:false`; build nie dowodzi poprawności numerycznej.

Artefakty: `/home/sieciowiec/dev/cpp/palace/build/optimization-stages-m0-20261030`.
`events.jsonl` ma timestampowane argv/start/end/exit i osobne logi; `build-script.py`
zachowuje przepis, `source-before/after.json`, `dry-run-plan.json`,
`builder-environment.json`, `cached-native-before.json`, `manifest.json`,
`build-summary.json`, compiler-comment i dokładne compile/link commands są zachowane.
Native nowe: libpalace `d1887e64cbd7a0045475b8f84b220f3b8d49666bb3edbf5503ae4987a9002f1b`,
program `043f043380d1f8df3a73ab40a7dc37589eb56538d4984c3180eeb41083863514`;
adapter unchanged3f25ec81…; test executable750020be….

Pierwsza próba CPU testu w noGPU builderze zakończyła się **exit127 przed main**:
`/lib/libcuda.so.1: file too short`. Drugi test `NOT RUN`. Zachowano wynik w
`operator-unit-results.json`; nie zastosowano fallbacku ani zmiany testu.
Wszystkie nowe i oryginalne kontenery kończą jako exited. Niezmienny następny krok:
kwalifikacja tego samego executable z prawidłowym driverem w osobnym runtime.

### OP-01-M0-E04 — kontrolowany runtime CDI, CPU test (`DEFERRED`, timeout)

Root osobno autoryzował CDI i ewentualny bind tylko libcuda. Nowy runtime
`palace-stage-m0-cpu-cdi-20261030` z image219cb…, networknone,
8GiB/noSwap/2CPU, **OMP_NUM_THREADS=2**, readonly artifact mount.
`--device nvidia.com/gpu=all` samo naprawiło loader: lddPASS, bieżący
`/stage/native/libpalace.so` SHA d1887e64…, hostdriver **615.78.08**,
`/usr/lib/libcuda.so.615.78.08` hash/rozmiar w driver-injection/host-driver.json.
Nie był potrzebny dodatkowy bind ani przebudowa. Test nadal `--device cpu --backend /cpu/self`;
to nie jest benchmark GPU.

Test1 `SpaceOperator retains coarse support while omitting fine exact zeros`:
**timeout exit124 po120,255s**, brak wydrukowanego raportu testu. To nie dowodzi
błędu numerycznego ani konkretnego miejsca zawieszenia (stdout mógł być buforowany).
Test2 `NOT RUN`; brak automatycznego fallbacku do innego wątku/testu. Root dostał
wynik i decyduje o próbie OMP1 lub diagnostyce inicjalizacji. Związek ze znanym
historycznym problemem MFEM4.9/Umpire+OMP2 to hipoteza, nie ustalona przyczyna.

Source hash131d5da3… pozostał identyczny przed/po. CDI runtime zatrzymany;
original/buildcache containers pozostają exited. Poprzedni exit127 nie zamaskowany.
Dowody: `build/optimization-stages-m0-20261030/driver-injection/`:
`events.jsonl`, `results.json`, `loader-validation.json`, `cdi-ldd.log`,
`cpu-test-1.log`, host-driver metadata i `run-script.py`.
M0 operator numerical gate nadal NIEZALICZONY. Ponowić wyłącznie na jawny nowy
wariant runtime/OMP po decyzji roota, z osobnym wpisem/artefaktami.


### OP-01-M0-E05 — startup markers + state telemetry (`PASS`, failure localization only)

Root zezwolił na jeden bounded diagnostic. Dodano flushed stderr markers wyłącznie
w `tools/stage_operator_unit_main.cpp` (MPI, parse, OMP, Device, HYPRE, CEED,
session.run i finalizers); native źródła/lib pozostały131d5da3…/d1887e64….
Recompile **jednego** TU2,217s + relink, te same cached flags; case object unchanged.
Nowy test executable01789d80c2279b494fd68a90aefc496a1f6a0d8abffd355176c9cc8d41b64b97.
Limit45s, CPU/cpuself/OMP2/CDI jak poprzednio,1s /proc CPU/task/wchan telemetry.

Tym razem **SIGSEGV exit139 po1,573s**, po przejściu wszystkich markerów inicjalizacji,
w środku `session.run`. Stack: `umpire::strategy::QuickPool::deallocate` →
`mfem::MemoryManager::Delete_` → `H1_TetrahedronElement::CalcShape` →
`IsoparametricTransformation::Transform` → libpalace+0x657c05 → libgomp worker.
Offline addr2line wskazuje `mesh::GetAxisAlignedBoundingBox(...)[clone ._omp_fn.1]`.
Nie loader ani MPI-init; faza to równoległa geometria/bounds wewnątrz testu.
Nie twierdzić, że markery naprawiły timeout: objawy race mogą być niedeterministyczne.
Nie jest to FAIL dokładności ani zmierzony speedup. Brak drugiego testu/retry.

Artefakty: root `build/optimization-stages-m0-20261030/startup-init-trace/`:
results, raw trace-test.log, cpu-telemetry.jsonl, timestamps/argv/compile/link,
inputs/native hashes i run-script. Kontenery zatrzymane. Kernel próbował core dump;
root powiadomiony i dalsze runtime dostały **core limit0**, żeby zapobiec zapisom crashcore.

### OP-01-M0-E06 — CPU OMP1 + zamrożony baseline OMP2 (`PASS`, CPU/OMP1 only)

Nowy kontrolowany eksperyment po stacku E05, osobno autoryzowany przez root.
Bez rebuilda, ta sama libd1887e64… i unit01789d80…, poprawny CDI driver,
CPU `/cpu/self`,2CPU,8GiB/noSwap, readonly artifacts, **core=0**.
Jedyna zmiana ustawienia obliczeń: **OMP_NUM_THREADS1**. Source hash131d5da3…
i wszystkie native hashes przed/po identyczne.

- Pierwszy test: **PASS20assertions**, wall0,531s, pełne finalizery do MPI.
- Drugi test: **PASS28assertions**, wall0,477s, curved tetra+hex,3 poziomy ND/H1,
  anisotropic coefficient/QData vs niezależne assembly, relL2 gate2e-13.
- To jest kwalifikacja małych operatorów **CPU/OMP1**, nie zmiana defaultu produkcji,
  nie CUDA/medium/RF ani zysk wydajności. Runtime obu starych błędnych OMP2 prób
  pozostają zachowane i nie są zastępowane tym PASS.

Za zgodą roota wykonano także pojedynczy15s control bez szerokiego kopiowania:
nowy runtime montuje **frozen r3 native** readonly jako `/frozen-native`,
ldd potwierdza lib1874bd95…; ten sam unit z identycznymi przed-hook headers,
CPU/cpuself/**OMP2**,core0. **FAIL exit1 po0,473s**, `Unknown pointer!` i SIGSEGV
w `QuickPool::deallocate`/`_Rb_tree_rebalance_for_erase`. Pokazuje dziedziczony
problem także na starym M7; nie jest wyłącznie skutkiem nowych stage hooks.
To pojedyncza obserwacja, nie dowód deterministyczności każdej awarii.

Dowody: root `build/optimization-stages-m0-20261030/omp1-controlled/`:
results/inputs/events, wszystkie ldd+raw test logs,0,5s CPU/task telemetry,
run-script; root `qualification-summary.json` zbiera wyłącznie ten zakres.
Wszystkie nowe i stare kontenery zakończone jako exited. Nie poprawiano
MFEM/Umpire/algorytmu i nie uruchamiano medium. Kolejne testy wymagają nowego
aktywnego kroku koordynatora.

**OP-05 TODO_TO_CHECK — uzupełnienie po odkryciu:** sprawdzić rzeczywiste
MFEM_THREAD_SAFE i Umpire pool/thread-safe konfiguracje z pinned builder;
wyizolować współbieżne użycie ElementTransformation/scratch/allocator w
GetAxisAlignedBoundingBox. Root cause nie jest jeszcze udowodniony, więc nie
promować mutexa, serializacji ani przebudowy dependency na podstawie samego stacka.
Przed nowym eksperymentem użyć tego wpisu: OMP2 na obecnym CPU runtime jest znanym
niekwalifikowanym wariantem; prostych powtórek bez nowej hipotezy nie wykonywać.


### OP-01-M1-E01 — named operator construction instrumentation (`IN_PROGRESS`)

Owner GPT-6.1 Sol high, `opt/operators-20261029`; base **febdc6eb9**, 2026-10-30.
Sprawdzono E01–E06/M0, nie powtarzano testów OMP2 ani profilu JIT. Koordynator
zamknął M0. Działa tylko M1: instrumentacja, bez optymalizacji/reassembly/cache zmian.
Baseline native: source131d5da3… / libd1887e64… z poprzednich artefaktów;
nowe CPP i root-owned stageprofile.hpp wymagają nowego manifestu po integracji.

Patch dotyka **3 CPU CPP**, nie nagłówków API/FEM ani dużych CUDA TU:
`models/spaceoperator.cpp`, `fem/bilinearform.cpp`, `drivers/drivensolver.cpp`.
Wspólny `utils/stageprofile.hpp` należy do roota i musi wejść przy integracji.
`StageProfile` mierzy host inclusive wall/processCPU; nie synchronizuje CUDA,
nie mierzy czasu zakończenia kolejkowanych kerneli. Włączanie tylko
`PALACE_STAGE_TRACE=1`. Bez tej flagi pozostaje wyłączony.

**22 stałe etykiety**, inwentarz `artifacts/optimization-stages/operators-m1/labels.json`:

| Etykieta | Granica pomiaru |
|---|---|
| operators.fec.nd / h1 / rt | Każdy istniejący ConstructFECollections, osobno |
| operators.hierarchy.nd / h1 / rt | Każdy ConstructFiniteElementSpaceHierarchy, osobno |
| operators.boundary_attributes | SetUpBoundaryProperties dla PEC |
| operators.materials | Konstruktor MaterialOperator, przed pozostałymi boundary objects |
| operators.lumped_ports | Konstruktor LumpedPortOperator, obejmuje geometrię/atrybuty portów |
| operators.wave_ports | Konstruktor WavePortOperator; empty config nadal może dać bliski zeru czas |
| operators.constructor_body | Tylko body po initializers: optional2D L2, BC check/print; nie cały constructor |
| operators.K / C / M | Całe główne getters, włącznie z coefficient setup/wrapperem BC |
| operators.Curl | GetCurlMatrix w uniform driven, jawny const Operator& zachowany |
| operators.restrictions_suboperators | Jeden aggregate wokół całego CEED parallel region: restriction/basis lookup i integrator/suboperator setup |
| operators.ceed_finalize | CeedOperatorCheckReady/finalize, poza workerami |
| operators.quadrature_data | Całe AssembleQuadratureData, brak zmian wywołań integratorów |
| operators.full_assembly | CeedOperatorFullAssemble, gdy wybrana ścieżka FA |
| operators.bilinear_hierarchy | Całe Assemble po hierarchy, bez nowych logów perlevel |
| operators.interpolator_setup | DiscreteLinearOperator restriction/interpolator/suboperator parallel region |
| operators.interpolator_finalize_multiplicity | Finalize + istniejąca multiplicity host-build/device-copy/reciprocal |

Żaden StageProfile nie jest wewnątrz OpenMP workera ani pętli per-element,
per-integrator/geometrię. Restriction i suboperator setup są celowo jednym
bucketem: rozdzielanie worker-local scope’ów bez thread IDs dawałoby niejednoznaczne
zagnieżdżenie przy CPU parallel. Jeśli ten bucket dominuje, kolejny M1 profil
może zawęzić go do istniejących funkcji/stacków, zamiast logować każdy element.
Raw K/C/M initial path z4 partial assemblies daje szacunkowo25 scope instances
przed operators-only stop; **rzeczywiste count jeszcze NOT RUN**. PC/hierarchy lub
inne materiały mogą dać więcej wywołań, choć liczba etykiet pozostaje22.

Member construction używa małego lokalnego helpera + immediate lambda. Każdy
builder wywołany dokładnie raz; C++17 return-value elision zachowuje bezpośrednią
konstrukcję, także klas bez copy/move. Nie dodano pól do SpaceOperator, zmiany
kolejności członków, limitów/tolerancji, assembly policy ani precision. Jawny
returntype const Operator& w Curl chroni dotychczasową referencję. Scope’y
bilinear mają tylko dodatkowe braces i RAII, pętle i ich kolejność bez zmian.

Wykonane kontrole lekkie: diffcheckPASS, static inventory22unikalne fixedlabelsPASS,
brak worker-local logging i dodanych device sync sprawdzony w kodzie;
docscheckerPASS. To nie dowodzi poprawności nowego buildu ani jego narzutu.
Bez nowej kompilacji, symulacji lub zmiany usług/kontenerów w tym kroku.

**Prośba test/build do koordynatora:** zintegrować wspólny header i3CPP raz z innymi
ścieżkami; przyrostowo odbudować potrzebne TU w nowym cache, zachować M0native.
Najpierw dwa istniejące operator action tests CPU/OMP1 (20+28assertions,
2e-13) oraz tiny operators-only trace. Zweryfikować kompletny trace, runtimecounts,
labelcoverage i inclusive nesting; porównać trace off/on na tej samej binarce,
backend/threads/config. Profilowane timings nie promują speedupu. Dopiero po
narzut≤1%/jasnej granicy powtarzalności wykonać jeden wymagany medium
operators-only profile, rozliczyć największe bucket/y względem istniejącego
construction timera (bez dodawania nested durations). Jeśli hot bucket pozostanie
nienazwany, wrócić do sampling zamiast przechodzić do M2 na podstawie intuicji.
Wszystkie M1 numerical/timing gates obecnie `NOT RUN`.


### OP-01-M1-E02 — integrated instrumentation build + CPU tiny OFF (`PASS`, narrow scope)

Root wydał slot na jeden wspólny build trzech ścieżek, potem dwa testy operatorów.
Wyłącznie root integrated źródła: hash
`3bae7f768d18d24545c110e0f8bf8d46e7467cbb5ce07879ba37da014a2eb2c3`,
settings0d605d50…. Zweryfikowano niezmienność przed/po całym zadaniu.
Nowy izolowany snapshot image
`4a314d49b81c31ef6b99fde45a12ceb1ad823083ba68d3eb3cb1feb51e5aba19`
z zatrzymanego M0 cache; stare /opt, frozen M0/r3 i root build/sm120 zachowane.

Dry-run **8 Palace TU**: driver/drivensolver/bilinearform/mesh/spaceoperator/geodata/
tablecsv i mainstamp. `mesh.cpp` jest w tej konfiguracji kompilowany jako CUDA TU,
ale to istniejący plik Palace, nie rebuild MFEM/libCEED/HYPRE. Wykonano jedynie
library+executable,2jobs,32GiB/noSwap/core0/noGPU/networknone i shared ccache.
**Native build23,852s**, setup+native25,895s; pierwsze wykonanie z cleanup30,936s.
C++17 helper konstruktorów skompilował się poprawnie, zero zmian ABI/headerów klas.

Nowe native w `/home/sieciowiec/dev/cpp/palace/build/optimization-stages-m1-20261030/native`:
libpalace30747059009a6f0cc3c52b4662d7a67d255f4b4c678667faf340608d37435714,
program ee866d11a21c101ceebc3a9c79e745b0b43f1acd130925494b6b85ddc3962c47,
adapter unchanged3f25ec81…. Manifest zawiera source/settings/native i referencję43ac…,
`numerically_validated:false` pozostaje; nie nadpisuje dawnych kwalifikacji.

Wolno było ponownie użyć unit executable01789d80… po dowodzie:
Gitfebdc źródła dokładnie odpowiadają M0hash131d; **122 istniejące publiczne nagłówki
bez różnic**, nowe stageprofile.hpp nie zmienia layoutu klas używanych przez test;
aktualny test-spaceoperator i tiny main identyczne z kompilowanymi źródłami.
Dowód `unit-abi-reuse-proof.json`. Stary PR unit binary nieużyty.

Zapisana pomyłka setupu: `shutil.copyfile` zachował payload unit executable,
ale zgubił executable bit (0644 zamiast0755); pierwsze uruchomienie zwróciło126
`Permission denied` przed testem. Przywrócono **wyłącznie tryb pliku0755** według
istniejącego unit binary, SHA niezmieniony. Brak rebuilda/source/backend/threads/
precision fallbacku. Pierwotny błąd zachowany w `operator-unit-results-initial-permission.json`
i surowym logu; poprawka i kolejne dokładnie te same testy w osobnym
`executable-mode-correction/`.

CPU/CDI, OMP1/core0, profiler jawnie **OFF**, obecna M1lib sprawdzona przez ldd:
- Test coarse support: **PASS20assertions,0,464s**.
- Test independent multilevel/QData/curvedtet+hex: **PASS28assertions,0,514s**, gate2e-13.
- Brak PALACE_STAGE_PROFILE output w obu logach; wykonano same operatory bez EM solve.

Artifacts: `build-summary.json`, `manifest.json`, `source-before/after.json` (równe),
`events.jsonl`/timestampowane argv/start/end/exit, raw build/unit/ldd logs,
`builder-environment.json`, ccache stats, saved build-script, unit ABI proof i
osobne dowody poprawki praw pliku. Wszystkie nowe M1 i zachowane M0 kontenery
zakończone jako exited. Żadnego medium/harness phaseRun/cloud w tym slocie.

**Zakres PASS:** kompilacja i CPU/OMP1 tiny operator action z profileOFF.
Profil ON, runtime liczba scope’ów, narzut/attribution i RF/medium/CUDA nadal
**NOT RUN**. Nie wyciągać speedupu z tych czasów testów lub builda. Next decyzja
koordynatora o tiny stage trace i porównaniu tej samej binarki OFF/ON.


### OP-01-M1-E03 — uzupełnienie niepokrytych104s: PostOperator / GSLIB (`IN_PROGRESS`)

Koordynator r1 odnotował poprawne diagnostic exit i niezaliczone pokrycie faz.
Odczytano niezależnie native log/JSON/config z
`/home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/M1-profile-pair-20261030-r1/medium-operators-gpu-on`:
po `operators.ceed_finalize` end jest **104,295120816s** do `operators.K` begin.
Config ma **164 probes i6Energy**; stdout:1 700 660elementów, mesh curvature order2.
Przyczyna nie wynika jeszcze z samej luki. GetStiffnessMatrix ma w r1inclusive0,152s,
więc bez brakującego outer scope nie przypisywać tych104s do samego K/C/M.

Source path: `SweepUniform` tworzy `PostOperator<DRIVEN>` przed K/C/M. W jego member
initializers są kolejno CSV, DomainPostOperator, SurfacePostOperator,
InterpolationOperator; dopiero potem body z fields/directory/CSV initialization.
Probe InterpolationOperator przy niepustej mapie zawsze wywołuje GSLIB `Setup`
na całej przestrzeni mesh i dopiero `FindPoints` dla punktów. Hipoteza:
koszt jest globalnym przygotowaniem point locator, nie164operacjami interpolacji.
**Czasów poszczególnych metod jeszcze nie zmierzono.**

Root compiler inputs w tym zadaniu **nietknięte** (IO worker używał stabilnego M1).
Dopisano w childworktree wyłącznie instrumentację, bez lazy-init/cache/zmian probe:

| Nowy fixed label | Granica |
|---|---|
| operators.post.constructor | Całe utworzenie PostOperator w SweepUniform, C++17 elision |
| operators.post.domain | Istniejąca immediate lambda DomainPostOperator, std::move zachowane |
| operators.post.surface | SurfacePostOperator member constructor |
| operators.post.interpolator | Cały InterpolationOperator member constructor, także op initializer |
| operators.post.body | PostOperator body po member initializers |
| operators.probes.gslib_setup | Dokładnie dotychczasowe op.Setup(mesh,bb_tol,newton_tol,npts) |
| operators.probes.find_points | Dokładnie dotychczasowe op.FindPoints(xyz,ordering) |

Łącznie **29 fixed operator labels**, poprzednie22 zachowane; bez per-probe/
per-element logging. CSV member ctor pozostaje w reszcie outer constructor;
body InitializeCSVDataCollection objęte post.body i istniejącymi I/O scope’ami.
Jeśli r2 pokaże dominującą resztę outer constructor, dopiero wtedy oddzielić
post_op_csv; nie trzeba dodawać jego scope na zapas. Powrót z lambda ma ten sam
typ/te same argumenty i gwarantowane C++17 elision, nie zmienia lifetime/ABI.
Nowe pliki scope: models/postoperator.cpp i fem/interpolator.cpp; outer w już
zmienianym drivensolver.cpp. Żadnych zmian klas/headerów/danych/tolerancji.

**Dodatkowy source research z faktycznego pinned MFEM4.9.0** (bez uruchamiania
kontenera, podman cp ze stopped M1 builder do ignored artifacts):
`/tmp/root/spack-stage/spack-stage-mfem-4.9.0-nucrpyipn2tktie6vyzz2hakdcgklpd6/spack-src/fem/gslib.cpp`,
SHA bdb21dcde44a1d3e880b0a9247707b7433eb14fd0f66b3a3abcba5794b776dcf;
installed gslib.hpp SHA126d800810c11b5b342d320fd5f7756cde5ea20093c5d1b48e6e19ef88ae0181.
Kopie z zachowaną licencją tylko artifacts, nie Git. Próba dostępu web do źródła
była niedostępna; oparto wniosek na rzeczywiście zainstalowanym źródle.

- `Setup`: gslib.cpp183–235 wywołuje SetupSplitMeshesAndIntegrationRules,
  GetNodalValues, ustawia local_hash_size=mesh_points_cnt, potem findpts_setup_3.
- `SetupSplitMeshes`:1207–1244 tworzy4 reference hex pieces dla tetrahedra;
 1436–1470 dodaje4internal split entries na każdy tetrahedron. To reprezentacja
  wewnętrzna GSLIB; FEM mesh anteny nie jest zmieniany.
- `GetNodalValues`:1472–1487 alokuje `vdim * NE_split_total * (meshOrder+1)^dim`
  współrzędnych, a następnie oblicza je po elementach źródłowego mesh.
- Dla all-tetra N=1 700 660/order2/FP64/3D daje to **6 802 640internal pieces,
  183 671 280sample points i4 408 110 720B ≈4,11GiB** samych coordinates.
  To wyliczenie logicznego bufora na podstawie kodu, nie pomiar peak/RAM/VRAM.
- Argument164 to `npt_max`, liczba punktów przetwarzanych jednocześnie podczas
  iteracji (installed header229–234), nie limit elementów/mapowania całego Setup.

Wniosek source: globalna rozbudowa tetrahedra dla locate164punktów jest
wiarygodnym kandydatem na koszt CPU/pamięci, ale udział104s wymaga r2timing.
Nic nie optymalizowano ani nie usunięto. Przy potwierdzeniu następny etap może
badać reprezentację/cache point locator z pełnym zachowaniem mapowania probes;
nie uznawać redukcji liczby probes za równoważny test performance.

Dowody statyczne: `artifacts/optimization-stages/operators-m1/labels-r2.json`,
`post-probe-source-evidence.json`, zarchiwizowane MFEMsource. Diffcheck/docscheckerPASS.
Nowy build, trace, poprawność/coverage/overhead r2 **NOT RUN**. Rootowi przekazać
nowe2CPP i incremental outer wrapper; nie nadpisać jego późniejszych własnych
zmian drivera lub operator ledger. Wymagany jeden wspólny przyrostowy build,
tiny proof i potem uzasadniony medium operators-only trace dla attribution;
bez przechodzenia do M2 na podstawie samego source.


### OP-01-M1-E04 — R2 cached build / CPU tiny OFF (`PASS`, narrow scope)

2026-10-30 root zintegrował nowe PostOperator/GSLIB scope’y i zamroził źródła.
Przydzielony pojedynczy build slot, bez phaseRun/medium. Nowy katalog:
`/home/sieciowiec/dev/cpp/palace/build/optimization-stages-m1-r2-20261030`.

Source **0341e50051ac29e585c3b211d73fd44e89beb1fb583280541bae743589e3372b**,
settings0d605d50…, wszystkie fingerprinty source-before/after równe.
Snapshot zatrzymanego M1 buildera do nowego image
`7d6096526275f2f56de270768a3ad29f8d774f9efa5a4f756b0cc6799063ea9e`;
nowy builder palace-stage-m1-r2-build-20261030,32GiB/noSwap/2CPU/core0,
networknone/noGPU, rootsources readonly i sharedccache. Starsze M1/M0/r3
cache/native nietknięte.

Dry-run: **3 CXX TU** (drivensolver/interpolator/postoperator), brak mainstamp
lub MFEM/HYPRE/libCEED rebuild. Native build **14,186s**, setup+native15,357s,
pełny slot z oboma testami i cleanup **21,322s**. C++17 PostOperator/member
value-elision skompilował się poprawnie. Adapter3f25ec81… zweryfikowany unchanged.

Native library:
`0546c1cf8855d26a656a9c5791a03bb3882201095104ac0a7b04436fc213fcf9`;
executable nadal ee866d11… (główna funkcja nietknięta), adapter3f25ec81….
Manifest zachowuje reference43ac/source/settings/native i globalfalse qualification.
Kopiowanie executable przez copy2/explicit0755; znany błąd praw z E02 nie powtórzony.

Po ponownym dowodzie122publicheaders i unit main/cases sources identycznych
użyto unit01789d80… z właściwą nową biblioteką (ldd potwierdza /stage/native).
Osobny CDI runtime CPU/cpuself/OMP1,8GiB/noSwap/core0, profile jawnieOFF:
**PASS20assertions + PASS28assertions**, każdy0,514s. Brak profile output.
Testy potwierdzają aktualne małe operatory; nie uruchamiają nowej pełnej ścieżki
PostOperator/GSLIB, więc jej runtime qualification czeka na tiny phaseRun.
Nie wykonano attribution/overhead/performance ani RF checka.

Wszystkie nowe R2 i stare M1/M0 kontenery zakończone jako exited. Root dostał
native/manifest ready dla preprocessing workera R2 profile. Przepis, komplet
argv/timestamps/rawbuild/unit/ldd logs, ABI proof i build-summary w artefaktach.
Kolejny krok należy do roota: tiny proof i pomiar Setup vsFindPoints z zachowaniem
tej samej konfiguracji. Nie przypisywać104s do GSLIB przed nowym timingiem.
Wyliczenie183,7Mpunktów próbkowania bazuje na **potwierdzonym mesh curvature order2**
z rzeczywistego stdout, nie na samym solver FEorder; nadal jest logiczne,
warunkowe dlaallTet/FP64, a nie measuredpeak.


## OP-06 — M2 bounded probe-location prototype

Owner/branch as above. Evidence below preserves stable IDs and negative outcomes;
preparation entries are superseded by their linked measured gates. All runs local,
no cloud/services/push. No reduced mesh/probes, coefficient projection or precision
change. One heavy slot at a time, cached builds with dependency/cache preservation.

**Artifact abbreviations** (absolute root `/home/sieciowiec/dev/cpp/palace`):

- `N0` = `build/optimization-stages-m2-operators-20261030` (source8854/libfb3d).
- `N1` = `build/optimization-stages-m2-operators-rescue-20261030` (sourceb834/libbc7).
- `A0` = `artifacts/optimization-stages/M2-OP06-20261030`.
- `A1` = `artifacts/optimization-stages/M2-OP06-rescue-20261030`.
- Source/full SHA, exact argv/env/cache/CUDA/adapter settings, raw logs, unit
  sources and before/after identity checks are in each manifest/host script;
  these ordinary artifacts stay ignored, never in Git.

| Fingerprint | SHA256 |
|---|---|
| Frozen root reference source |0341e50051ac29e585c3b211d73fd44e89beb1fb583280541bae743589e3372b|
| Initial OP06 source (`N0`) |8854d938e0314b18ae251bcd1a25913cd7c023bf7a3b038a4f38a9f8e689007a|
| Initial OP06 library |fb3d0bd7bb6a074358f78a81b70e3bf08a2b7eb0742ee650749a6c59a9f1a549|
| Qualified rescue source (`N1`) |b834bebb7a9c774cdb1028352bae62cefc8f4666d281570e26e4ccf7d3a8d46e|
| Qualified rescue library |bc7a8f844f2c0e2374a0ae9dfc36438917a4382b604cde0ec11137c9fe1f26e5|
| Unchanged adapter |3f25ec819e1a1d053c544afc63b4154103ffa23a7bdda48af547b211836dfd85|
| Actual GPU replay tool source |1346d9c3f48735f12328057c1dea8a096525f9fee25e68c66ec1783f0d866c8e|

**Shared protocol:** fixed runtime image43ac; actual config9f068/mesh2af and164
probes, curvature2/1,700,660tets/402,647vertices/510,048boundary elements. Builds
32GiB/noSwap/2CPU/core0/noGPU/networknone; tiny tests8GiB/OMP1/CPU/cpu-self/CDI
for valid loader only,60s limit. Medium constructors64GiB/OMP1/cpus8/CUDA/CDI/
core0/noSwap/networknone/300s with all18 baseline flags, canonical user-host lock,
inference/reserve guards and cleanup. Geometry-only diagnostics32GiB/OMP1/cpus2,
120s; actual GPU replay32GiB/cpus8/300s. Deviations/failures recorded per ID.
All timers are scoped; global sampled GPU usage is not per-process/UVM telemetry.
Kernel physical-I/O bytes were not collected; result sizes are not disk counters.

### OP-06-E01 — existing MFEM locator feasibility (`PASS`, source only)

Root M1 attribution: GSLIBSetup104.5197wall/104.3144CPU vs FindPoints0.001888s.
Read-only copies of pinned MFEM4.9 source: operator-worktree
`artifacts/optimization-stages/operators-m2/mfem-source-manifest.json`, not Git.
Mesh::FindPoints (mesh.cpp13755–13871) scans curved centers×queries
O(NE*Nprobe)=278,908,240distances, then inverse nearest and vertex-neighbor cells;
explicitly not100% reliable. GridFunction::GetVectorValue preserves DOF/Piola maps
and is itself used by serial GSLIB InterpolateGeneral(gslib.cpp1961–2001).
Selected rank1 opt-in with strict interior/forward check and wholebatch oracle
fallback; no custom Maxwell solver/BVH/geometry approximation.

### OP-06-E02 — initial opt-in patch prepared (`PASS`, implementation gate E04)

`PALACE_PROBE_LOCATOR=mfem`; absent/explicitgslib unchanged. Unknown env rejected.
All164 coordinates/IDs/complex point-major ordering retained. Per-instance mesh
pointer/GetSequence/GetNodesSequence invalidation; official NodesUpdated required
for direct node edits. Unsupported rank/dimension/volume/field-map, missing or
boundary ambiguity use wholebatch GSLIB. Initial class-layout change required fresh
library/test executable. Fixed guards: strictinterior1e-7, forward residual<=1e-12
scale. Default acquires no experiment clocks/logs. No numerical claim at preparation.

### OP-06-E03 — first cache gate (`DEFERRED`, resolved E04)

`N0` first dry-run requested110PalaceTUs, over25cap; compiler/tests never started.
Preliminary regex also falsely matched Palace's own libceed/hypre wrapper names;
manual plan showed no external dependency build. Stopped after3.67s, rawfailure
and dry-run retained. Not a numerical failure; no blind110-TU rebuild.

### OP-06-E04 — content-proven cache repair + initial tiny (`PASS`, narrow)

Compared exact input bytes against frozen root: only interpolator.cpp/.hpp differ.
Root approved copying **mtime only** for400 byte-identical actor inputs, preserving
actor atime/changed-input times and all root metadata; compiler hash unchanged.
No tree mirror/spill. Dry-run15PalaceTUs, native42.762s/setup43.618s. Fresh2TU
unit from current headers/new library: **664 assertions/5cases PASS,1.065s**, both
orderings and complex curved ND/RT/H1 plus fallback/invalidation. `N0/repair1`
contains inventory/proof/logs; all containers stopped, source-before/after equal.
No medium/RF/speedup qualification.

### OP-06-E05 — real164 prelaunch lock failure (`DEFERRED`, resolved E06)

Exact first runner attempt exited1 before container/native launch: per-worktree
`build/optimization-stages-host.lock` parent absent. Did not mkdir a competing
lock. Root fixed canonical `/run/user/<uid>/optimization-stages-host.lock` and
cross-worktree regression. `A0/candidate-medium/prelaunch-lock-failure.json`
preserves failure; no simulation result attributed to this attempt.

### OP-06-E06 — simple native locator on real164 (`REJECTED` for benefit)

`A0/candidate-medium-r2`: exit0 but selectedgslib/reasonnot_found. Native attempt
0.995s, then full GSLIBSetup104.328wall/104.126CPU. Operators115.925s/total169.130s;
peak12.737GiB cgroup, globalGPUmax7682MiB. No exact missed IDs logged yet.
Safe fallback worked but no speedup; no promotion or default-control retry.
Actual p2DOFs preserved; no solve/RF. Full typed summary/rawtiming/telemetry retained.

### OP-06-E07 — standalone shared-load diagnostic prepared (`PASS`, measured E08)

New tool uses exact public production chain Load→DrivenSolver.Preprocess(units)→
Partition→Refine→allMeshwrappers/EnsureNodes, then finalmesh.back and normalized
probe map. No PostOperator/GSLIB/FE solve. One load, three existing inverse guesses
Center/ClosestPhysNode/ClosestRefNode, max16/ref1e-15/physical4e-15/element1e-8,
OpenHalfUniform/relativeguessorder-1. Reports per-ID coordinates/reference/residual;
missing reference null. Host verifies supplied identity JSON before/after.

### OP-06-E08 — three-guess actual diagnostic (`PASS`, initial-guess fix rejected)

`A0/locator-diagnostic`: first tool compile failed on temporary MPI_Comm passed to
reference argument; saved `compile-failure1`. Mechanical local-comm fix only;
no runtime before repair. Compile6.624s/link0.214s; one CPU process56.953s,
load/units/partition/refine/wrap52.959s, peak2.088GiB. Each guess found141/164,
missed SAME23 IDs **3,4,9–26,29–31**,0rescues/0boundary/0bad residual among found.
Attempts0.9605/0.9665/0.9759s; maxresidual4.86e-17. Changing initial guesses alone
rejected on unchanged inputs. This did not prove outside or distinguish candidate
neighborhood vs all-candidate inverse failure. Raw rows/config normalization proof
preserved; no GSLIB/solve/RF.

### OP-06-E09 — bounded extra candidates prepared (`PASS`, measured E10)

Pinned KDTree header has nearest1/radius APIs, **no k-nearest-N**. Chose K128 before
run: one curved GetElementCenter pass, Euclidean/eID lexicographic maxheap for only
missing points; no adaptive K/unbounded inverse scan/full center cloud. Same
Center/max16/tolerances; only strict+valid forward maps accepted. Reconstructed
original nearest/vertex-neighbor set for diagnostic attribution on conforming mesh.
Tests proposed sliver/decoy/cap/ties/boundaries; production still unchanged.

### OP-06-E10 — actual fixedK128 diagnostic (`PASS`, geometry only)

`A0/locator-diagnostic-k128`: **all23rescued →164/164**. Selection0.58817s,
inverse+neighborhood0.02537s, total0.61356s;72tried=45Outside+4Unknown+23Inside,
accepted center ranks2–7, maxresidual2.776e-17,0boundary/bad acceptances. Exactly
128candidates per missing point;2,944entry cap/39,115,180distances/1global center
pass. **All23true cells outside entire original nearest-cell vertex neighborhood;
mesh conforming**: same inverse proves omitted candidates caused these misses.
Native57.474s including one load, compile7.024s/link0.264s, peak2.0873GiB. No
library/GSLIB/solve/fields/RF. Report484,293B; no extra K/tolerance retries.

### OP-06-E11 — shared helper integration prepared (`PASS`, gate E12)

Internal probelocator.hpp used only by interpolator.cpp/test/diagnostic, not public
class header; fixedK/search/quality cannot drift. Production derivedMISS rescue
followed by allpoint quality guard; opt-in aggregate initial/rescued/cap/tried/
remaining log only. Unresolved/boundary/unsupported retains wholebatch GSLIB.
No new class-layout change versus8854. Diagnostic-only neighbor proof stays out
of production; fresh adversarial tests required before medium.

### OP-06-E12 — native/shared adversarial gate (`PASS`, CPU/OMP1)

`N1`: **1CPP** rebuild4.619s/setup5.697s; fresh main0.314s/case3.519s/link0.264s.
**749assertions/10cases PASS,1.165s** =original664+85new, fullslot16.180s.
Known curved aspect10 targettet+closer disconnected decoy proves originalMISS/new
rescue; complexrandom ND/RT/H1scalar/vector compare GSLIB+known reference with
unchanged abs1e-11+rel1e-10. True cellrank129 behind128closer decoys remainsmissing,
tried128 and production oraclefallback passes. Ties/NE<K/noMISSzero-work/boundary/
outside plus old IDs/order/invalidenv/empty/mesh-invalidation pass. Runtime logs
four fieldrescues(initial0/rescued1/tried2), capfailure(0/0/tried128/remain1).
Native/unit/source identity equal before+after; fresh unit d703cd7…; allcleanup.
Non-GSLIB build/MPI>1/unsupported-volume runtime remain NOT RUN.

### OP-06-E13 — actual164 production constructor (`PASS`, not full RF)

`A1/candidate-medium`: sourceb834/libbc7, **actualmfem selected,141+23rescued,
cap128/tried72/remain0; zeroGSLIBSetup/FindPoints**. Location1.62299wall/1.61952CPU
(includes rescue0.63345s), PostInterp1.62504s/allPost4.51094s.
Operators12.165725s/diagnosticTotal65.568107s/runner67.073s; cgrouppeak3.63324GiB,
globalGPUmax7952MiB. Same actual geometry/p2DOFs. Stage stop before solver,
fields/residual/S/VSWR/FF NOT RUN here; tiny749 remains field evidence at this point.
No extra run; parent prepared a matched default control next.

### OP-06-E14 — one same-build control (`PASS`, constructor only)

`A1/baseline-medium` and `A1/pair-comparison.json`: same sourceb834/libbc7/config/
mesh/image/all18flags/trace/resources; **only mfem vs explicitgslib differs**.
Default setup102.59144wall/102.38236CPU +FindPoints0.00188s, no experiment logs.
Both complete/exit0/same counts/noRF.

| Diagnostic metric | gslib baseline | mfem candidate | Change |
|---|---:|---:|---:|
| OperatorConstruction |113.195641s|12.165725s|−89.25%,9.30×|
| Whole operators-only diagnostic |166.716360s|65.568107s|−60.67%,2.54×|
| Cgroup peakRAM |12.74160GiB|3.63324GiB|−9.10836GiB/−71.49%|

ONE sequential candidate→baseline pair, cache not flushed, profiled; not three
medians/balanced ABBA/fullGMRES speedup or peakRAM. GlobalGPU sampledmax6290MiB
baseline vs7952candidate; **not** per-process VRAM savings/regression/physicalUVM.
No fullRF/solvedfields or repeated perf qualification. Raw pair identity/scopes kept.

### OP-06-E15 — CUDA/UVM field replay prepared (`PASS`, measured E16)

One public production load+SpaceOperator ND/RT, one mfem locator and one GSLIB
oracle; no K/C/M/PostOperator/KSP/GMRES/coefficient projection. Fresh `.cu` compiled
with actual cached CUDA12.9/C++17/compute120+sm120 rule, no native rebuild.
Rule file is in **operator worktree** artifacts/optimization-stages/operators-m2/
gpu-replay-prepare (the shorthand ROOT path does not exist); also independently
captured exact Ninja command during execution. Toolsource1346 frozen.

Declared before run: allfinite, complex global relL2<=1e-9 and maxabs<=1e-8*
max(1,refMax), phase only when BOTH amplitudes>1e-6*max(1,refMax), explicit mask/
null for excluded values. Zero reference norm handled without a fake denominator.
FP64 DOFs exactly binary pattern `(((uint32(i)*1664525+seed+97*component)&1023)-512)*2^-10`,
NDseed17/RT103. CUDA forall writer architecture witness must be nonzero; CPU
fallback writes0/fails. Managed pointer attributes mandatory. First explicit
HostRead+128strided exact samples, then GPU refill before EACH backend sampling.
This does not relax final fullRF1e-5/residual/power gates or count physical UVM bytes.

### OP-06-E16 — actual CUDA synthetic field replay (`PASS`, not full RF)

`A1/gpu-field-replay`: one `.cu` compile14.537s/link0.264s, no error/fix/retry.
Native executablef594e1153776b87db5ef3218e0c7a2d9f932570137c9a62f0ea462e7cb6aa7f3.
Identity sourceb834/libbc7/adapter3f25/tool1346/config9f068/mesh2af before+after equal;
all18 flags/readonly mounts and32GiB/8CPU/OMP1/300s/noSwap/core0/networknone.
Canonical lock,31during-run inactive/dead/PID0 checks and memory guards PASS.
Actual RTX5070TiCC12.0: **CUDA writer1200 and managed pointers type3 in ALL6fills**;
128strided exact samples per real/imag part pass. No CPU fill/projected substitute.
All164×3complex values perfield retain IDs/ordering/normalization. Meshrevision fixed.

| Field | Global complex relL2 | Maxabs error | Scaled gate | Maxphase rad |
|---|---:|---:|---:|---:|
| E ND |4.9133e-14|1.8345e-10|1.8064e-5|1.2368e-12|
| B RT |9.5320e-14|7.9382e-7|2.7616e-2|3.4310e-13|

Both pass predeclared gates/allfinite. All492values perfield above phasefloor,
0excluded; masks retained. RTreferenceMax2.7616e6/ND1806.398 explain scaled
absolute limits; **not** claimed absolute error<=1e-8. FP64 DOF counts11,869,460ND /
15,951,066RT per complex part; CUDA refilled before every backend call.

Wall: preprocess53.338s/SpaceOperator7.230s/nativeCtor1.6407s/oracle103.4304s,
exactlyONE GSLIBSetup103.4284wall/103.2216CPU. Native141+23/tried72/cap128/0fallback.
FirstHostRead ND15.117ms/RT19.852ms; after fresh GPU fill sampling NDnative11.526ms/
oracle11.770ms, RT14.855/14.820ms. These are API/copy/sample times, not physicalUVM
migration counters or a fullsolver transfer benchmark.
Runtime166.874s/tool165.787sCPU165.443s/slot185.228s; cgrouppeak12.3666GiB **includes
oracle**, globalGPUmax6794MiB/util9% (short kernels proved by witness, not sampler).
Report354,052B, ordinary metadata only, no solver SSDspill. Cleanup complete.
Full report/values/masks/proof, exactargv/env, identity/ldd/policy/telemetry/rawlogs/
stage-profile retained. **Actual synthetic GPU→HostRead ND/RT equality qualified;
fullRF/residual/S/efficiency/pattern and repeated performance pairs NOT RUN.**

### M2 local source/docs review and handoff — 2026-10-30

Docs-garden skill read/applied; reviewed owning code/tests/artifact manifests,
ARCHITECTURE/INDEX/workflow. Corrected stale current header/base/status and
condensed repeated M2 protocol wording while preserving E01–E16, negative results,
limits and exact evidence routes (verbose pre-garden copy ignored in artifacts).
INDEX already links this ledger; shared root plan/index/checkpoint untouched.
Source review found no blocker within qualified rank1/currentgeometry scope:
shared fixedK/quality/fallback, existing DOF/Piola APIs, no new public layout vs8854,
per-instance identity+both revisions. Raw node writes require NodesUpdated;
non-GSLIB/MPI>1/unsupported types/othergeometry/fullRF remain NOT RUN.
No product/test/tool bytes changed by this cleanup: preserve compilerb834/libbc7/
CUDAtool1346. Clang-format dry checks, diff/docs check and staged-source/secret audit
precede one local commit. Only eight owned source/test/tool/ledger files staged;
no .env/credentials/private keys/rawartifacts/binaries. No GPU/build/cloud/services/
push/PR during review. Stop after commit; root supplies exact M3 job plans later.
