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
