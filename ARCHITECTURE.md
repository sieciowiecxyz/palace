# Architektura lokalnego forka Palace

Twarde wymaganie użytkownika (2026-10-18): wszystkie dane robocze solvera w RAM/VRAM. Zakaz przenoszenia bazy, macierzy i workspace na SSD/NVMe oraz używania swap do zmieszczenia zadania. UVM wyłącznie GPU↔RAM. Cache builda i zwykłe wejścia/wyjścia pozostają; historyczne eksperymenty z bazą dyskową są odrzucone i nie są dopuszczalnym baseline wydajności.

## Zasady

Najprostszy czytelny kod, małe zmiany i jawne granice odpowiedzialności. Reużywaj infrastruktury upstream i bibliotek. Testuj realne ścieżki i regresje; nie dodawaj warstw ani zależności na zapas. Zmiana reprezentacji/precyzji nie może ukrywać zmiany równań.

## Mapa

- `palace/`, `cmake/`, `test/`: źródła i testy upstream. Zaimportowane rozszerzenia są w zwykłym kodzie C++, nie stosowane ponownie jako patche.
- `tools/dev.py`: lokalny przyrostowy build, manifesty, rozpakowanie fixtures, ograniczony runner i pakowanie. Python stdlib, Podman, zstd; Linux x86-64.
- `tools/adapter/`: dotychczasowy adapter CUDA UVM/cuDSS; FP32 faktory są opcjonalne, runner domyślnie używa faktorów FP64.
- `tools/adapter/ceed_audit.cpp` i `tools/ceed_basis_audit.py`: opt-in `--basis-audit`, oryginalne apply bez zmian, host metadata/call counts; wymagane logical bytes osobno od długości wektorów. Zero query errors/overflow i ścisły parser wymagane do kompletności; nie profiler/rezydencja/PC-role. docs/ceed-basis-audit.md.
- `tools/experiments/ceed_tensor_probe.{cpp,cu,py}`: izolowany cached MFEM/libCEED action probe kontra cuBLAS FP64/FP32/TF32 requested i --fused FP32registers bez interim floatvectors, CPU oracle/canaries; nie zmienia solvera. Screen i --scale do N1601320, bounded RAM/VRAM; docs/ceed-tensor-probe.md.
- `palace/linalg/complexcudss.cpp`/`mixedcoarse.hpp`: native FP64 domyślnie, opt-in `--native-coarse-fp32` to GENERAL complex FP32 LU +scaling i dwie oryginalne FP64 CUDA korekcje. Odrębne od realnego shima; runner sprawdza dtype/cleanup/coarse residual. W.2/W.3 zakres i ograniczenia w docs/milestones/mixed-coarse-plan.md.
- `tools/runtime.json`: przypięte lokalne obrazy zależności i wersje; `tools/import.json`: pochodzenie zaimportowanych źródeł i zasad vibecoding.
- `tools/containers/`: cienka warstwa ccache na gotowym builderze i runtime z binariami forka.
- `palace/utils/fieldcomparison.hpp`: opcjonalne lokalne snapshoty FP64 i różnica E/B ważona istniejącymi operatorami energii; bez modyfikacji rozwiązania. Runner wiąże referencje hashami fizyki/mesh/dependencies.
- `tools/coax_fields.py`: analityczne porównanie E/B/energii; opt-in native L2 w `palace/utils/coaxdiagnostic.hpp`, tylko znane jednorodne fixtures.
- `tools/generate_coax_tiny.py`: jednorazowe generowanie mniejszego filtra przez opcjonalny gmsh, nie część runtime.
- `tools/allocation_audit.py`: analiza zachowanego large-UVM alloc/free trace ze stosami, bez GPU i bez ponownego runu.
- `docs/reference-correction.md`: diagnostyczne warm-start/restart i tolerance checks; opisuje timeouty pełnej anteny bez promowania ich jako wyniku RF.
- `docs/reference-profiles.md`: filtrowane profile CPU/cuDSS, zespolonego coarse solve i zwalniania solvera; small-case PASS nie kwalifikuje pełnej anteny.
- `docs/native-complex-coarse.md`: opcjonalny natywny complex FP64 coarse solver, zakwalifikowany dla jednego punktu anteny; brak promocji defaultu; późniejszy profil UVM/kerneli w docs/profiling-window.md.
- `tools/experiments/ceed_qpool.py`: izolowany, niezakwalifikowany backend workspace; osobne SO, cache jednego obiektu, manifest i opt-in runnera.
- `tools/mesh_cost.py`: audyt domen Gmsh 2.2, opcjonalne rzeczywiste DOF/material incidence wRAM i koszt powierzchniowy, bez bibliotek FEM/GPU.
- `tools/fdtd_budget.py`: czysty rachunek tablic/CFL i optymistycznego streamingu gprMax uniform/HSG z pinowanych źródeł; nie solver ani benchmark. Same GPU pola/IDs oddzielone od logicznych host arrays i opcjonalnego DFT; docs/fdtd-budget.md.
- `tools/maxwell_reference.py`, `tools/experiments/bempp_{oracle,sphere,dielectric}.py`: izolowane CPU Maxwell/Mie PEC/PMCHWT oracles z prywatnymi przypiętymi zależnościami/cache; brak Bempp w Palace. `maxwell_hmatrix.py`/`maxwell_apply.cu`: exact-near/low-rank-far complex probe, cached2kernelCUDAFP64 i GPUoperator/CPUbasisGMRES. PEC/dielectricfar-fieldPASS wEXP25–29; późniejszyND1interface opisany poniżej. BrakzakwalifikowanegoND2/scalableassembly i promocjianteny.
- `tools/experiments/mfem_bridge.{cpp,py}`: cachedCAPI do istniejącego MFEM4.9, bezrebuildazależności. `maxwell_fem.py`/`bempp_coupling.py`: rzeczywisty CPU ND1FEM–BEM z niezależnymi Whitney/trace/Greenchecks. Zbieżny, lecz1%fieldgateFAIL; ND2projection i antena niezakwalifikowane. Oracle `--physics coupling` izolowany od binariów Palace.
- `tools/experiments/bempp_pairing.py`, oracle `--physics pairing`: CPUaudyt GramRWG/SNC vsRWG/RBC, fizyczna barycentricquadrature/DOFtransforms i projekcja trace. EXP32 odrzuca odwracanieGprimal po utracieranku; Gdual kandydatem, nie gotowymND2mortar ani speedupemanteny.
- `mfem_global.cpp`/`maxwell_nd.py`/`mfem_nd2.py`, oracle `--physics nd2`: istniejącyMFEMglobalND2, rzeczywistefaceDOFtransformations i sparseCSR. EXP33 plane-waveDirichletreferencePASS0,151/0,332%E/H, nieBEM/ports/antena. CachedSO obejmuje legacy/global2TUs, niezależne sourceSHA; brakrebuildaPalace/deps.
- `bempp_nd2_coupling.py`, oracle `--physics nd2-coupling`: rzeczywistyND2/BC-RBCmortar, izolowanylocalbasisassembler i sparseFEM/Schur. EXP34 physicalmap/T-Knative/SchurPASS, wholefieldFAIL10,07/5,64% przyFEM1228/BEM120. LocaldenseBEMniejestskalowalne, brakpromocji; następnewydzieleniebłęduprzestrzenipowierzchniowej.
- `bempp_trace_spaces.py` oraz `bempp_nd2_coupling.py --duality magnetic --surface-level`: izolowane trace diagnostics i nested BEM/FEM. EXP35–37 transparent interface PASS E/H0,560/0,751% (F2/B3), F3/B3 E0,358%/H0,904%; nie monotoniczne dla obu pól. Dielectric transmission, scalable assembly i antenna speedup nadal otwarte; docs/maxwell-trace-duality.md.
- `bempp_transmission.py`, oracle `--physics transmission`: eps1/2,94 coupled ND2 vs niezależny PMCHWT tej samej geometrii; `--reference-only` pomija coupled FEM solve. EXP38–41 rozdzielają siatkę od potentialquadrature, zapisują małe rozwiązania NPZ; centroidscreening FAIL, nie globalL2/antena. Reference-only B4 bez radialprojection; docs/maxwell-transmission.md.
- `mfem_nd2.py --epsilon-r`: analityczna fala z operatorem curlcurl−eps*M, ND2default1/transmissiondefault2,94. `mfem_replay.py`/oracle `fem-replay --probe-input`: saved FEM na identycznych degree2points, strict barycentric owner i role/SHA/ABI guards. EXP54–58: dielectricF3 analyticPASS, coupled fixedpoints E/H0,664/0,597%; brak zbieżnej normy/antenna speedup. docs/maxwell-fem-refinement.md.
- `maxwell_stream.py`/`bempp_stream.py`, oracle `stream-control|stream-volume`: fused T/K dla dwóch prądów, optional cached NumBa FP64/complex128 i bounded targets. NativeBempppotential także matrixfree; mierzone tylko CPUquery. EXP59–69: własne F3degree2/5, reference/volumeFAIL, FMM w osobnym kontrolowanym dodatku; docs/maxwell-stream.md.
- `exafmm_build.py` i `bempp_fmm_control.py`, oracle `fmm-control`: izolowany cached ExaFMM0.1.1/FP64 addon, private FFTW/BLAS; p8 Maxwell actionPASS. Kontrole niezależnych k zwalniane sekwencyjnie; solve przechowuje dwa k w osobnych istniejących RAM tmpfs. failfast na pełny RAM tmpfs. PMCHWTsolve EXP74–76 FAIL independentraw; bez promocji scalability/CUDA/anteny; docs/maxwell-fmm.md.
- `bempp_volume.py`, oracle `--physics volume --volume-inputs`: saved-solution replay na dodatnich regułach objętościowych2/5 i potencjałach BEM wchunk128. SHA/state/role/physics/basis guards; brak nowego BEMassembly/LU, małe MFEMforms nadal tworzone z handle. EXP42–43 volume/reference/potentialqualityFAIL, docs/maxwell-transmission.md.
- `maxwell_near.py`/`bempp_near_control.py`/`bempp_near_correction.py`: fizyczne RWG T/K, distance subdivision i saved-potential near correction. Native/solid-angle oracle oraz full2240point adaptive controls PASS wEXP44–47, E/H2,888/1,611% nadal FAIL. Opcjonalne `maxwell_near_jit.py` (cached NumBa FP64/complex128, bez fastmath), near-side fine/coarse; EXP48–53: pełne B3/B4/degree2/5, brak zbieżności referencji/objętości. CPU/RAM, zero assembly/solve, bez produkcyjnej integracji; docs/maxwell-near-panels.md.
- `tools/nsight_window.py`/`tools/host_phases.py`: przypięty CUDA-only profiler, RAM/tmpfs na trace/SQLite, afiniczna kalibracja zegara z niezależnym markerem i quality gate. `--nsys-window` kończy native diagnostycznie po kilku iteracjach; nigdy nie kwalifikuje RF. Selektywny start cudaProfilerApi/koniec przy naturalnym exit ogranicza pamięć kolektora; EXP88 late W.3 PASS, historyczny whole-process late OOM/forced-stop warning FAIL; docs/basis-prefetch.md.
- `palace/linalg/mixedbasis.hpp`, StoredBasisVector::Dot/AddTo i `PALACE_GMRES_FP32_DIRECT`: opt-in bezpośrednia baza FP32/FP64partials, jeden sharedworkspace, MGS/reliable stopping zachowane. `mixed_basis_probe.py` cachedsm120 i actualcoax-tinyPASS EXP77–79; EXP80–85 actualAPI/MGS/realcomplex/W.2/W.3PASS, W.3 cgroup−2,87GB; bez speedup/defaultpromotion. stored_basis_probe.py linkujeactualAPI; docs/mixed-basis-validation.md. `--basis-prefetch` opcjonalnie zleca managed Dot-source prefetch na stream0, liczniki to requesty, nie migracje; EXP86–90 W.2/W.3 PASS, mała lokalna poprawa, bez globalnej promocji; docs/basis-prefetch.md.
- `tools/tests/`: regresje narzędzi i mały natywny probe cuDSS.
- `examples/tshaped-medium/`, `examples/coax-medium/`, `examples/coax-tiny/`: kompletne wejścia z archiwami siatek i sumami kontrolnymi.
- `build/sm120/`, `.cache/`, `artifacts/`: ignorowane buildy, ccache i wyniki. Obiekty CMake są dodatkowo zachowane w dedykowanym kontenerze buildera.
- `docs/`: instrukcje lokalne i zachowana dokumentacja upstream w `docs/src/`. INDEX prowadzi do obu.

## Granice

Środowisko zależności pochodzi z istniejącego, przypiętego obrazu lokalnego. Zwykły build nie pobiera ani nie buduje ponownie MFEM/libCEED/hypre. Przeniesienie środowiska wymaga eksportu/importu obrazów; nie ma jeszcze rejestru obrazów ani zweryfikowanego cold builda wszystkich zależności.

Nowy eksport ma `numerically_validated=false`. Historyczna kwalifikacja dotyczy wskazanych starych binariów i przypadków. Runner sprawdza kompletność wykonania; osobna analiza sprawdza S, energię, residuum i pola. Obecny cel dotyczy jednej 5070 Ti. Obsługa podziału na 2 GPU pozostaje poza jego kryteriami i nie została zakwalifikowana.

- M4 opt-in: `DrivenSolver::SweepUniform` zachowuje A2/A/P dla stałego f/port RHS,
  a defer trzyma tylko pierwszy true-DOF E do pomiarów po `ksp.reset()`.
  DomainPostOperator reset/rebuild nie kasuje pól/CSV. Runner audytuje coverage,
  setup i kolejność; brak zmiany defaultów. Dowody/ograniczenia: docs/milestones/M4.md.

- M5 `--cudss-hybrid-mib`: nativecomplex FP64 pozostaje GENERAL/GPU; adapter
  włącza host/device memory przedanalysis, jawny limit po MIN/estimates. CuDSS
  deviceworkspace nieUVM, reszta FEM UVM; runner weryfikuje actualconfig i cleanup.
  Badawcze/niepromowane, docs/native-hybrid-memory.md. Brak TF32/BF16 factors.

- M5 `--ams-cycles`: opt-in realshiftedPC z istniejącym HypreAms/GMG, stały
  AMS tol0, audyt HYPREdevicepolicy/operatorów. FullA niezmienione; profilepokazuje
  CUDAkernelswcoarse, ale W3deadlineFAIL. docs/ams-assessment.md. ScaledcomplexFP32
  z FP64correction jest osobnym niezrealizowanym planem, nie starym realnym shim.
