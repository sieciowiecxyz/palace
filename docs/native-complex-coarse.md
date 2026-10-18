# Native complex coarse — M1 / EXP18–19

2026-10-18. Opcjonalna ścieżka FP64 dla jednego ranka CUDA.
**W.3 przeszedł kontrolę numeryczną. M1 zamknięty później po EXP22; [dowody](milestones/M1.md).**
Nie zmieniono defaultów, siatki medium, materiałów ani portów.

## Co zmienia kod

`--native-complex-coarse` ustawia ComplexCoarseSolve=true/PCMatShifted=false
i wybiera `ComplexCuDSSSolver`. Zamiast rzeczywistego bloku
`[Ar Ai; Ai −Ar]` o wymiarze2N tworzy CSR dla `Ar+iAi` o wymiarzeN.
cuDSS dostaje CUDA_C_64F/GENERAL: Maxwell complex-symmetric nie jest
ogólnie Hermitian. Równanie, faktory i obliczenia Krylov pozostają FP64.
Runner wymaga również FP64 storage bazy; CPU, Q-pool i adapter FP32
nie są zakwalifikowane w tym profilu i są odrzucane.

Kod: `palace/linalg/complexcudss.cpp`, wybór w `ksp.cpp`.
CSR scala części Hypre po hostowym odczycie; pakuje RHS przez istniejące
`ComplexVector.Get/Set` na GPU. Synchronizacje są jawne dla poprawności.
Pierwsza wersja ponawia analysis/faktoryzację przy SetOperator; nie ma
promocji symbolic reuse ani obsługi wielu ranków.

Pamięć robocza pozostaje RAM/VRAM. `--release-gmres-basis` i
`--release-final-solver` zwalniają już niepotrzebne obiekty przed pomiarami.
Timer „Disk IO” liczy zwykłe wejścia/wyniki/snapshoty; nie ma disk basis,
mmap/offload ani swapu do zmieszczenia obliczeń.
Runner i probe ustawiają `--ulimit core=0:0`. W przypiętym runtime
sprawdzono `ulimit -c` równy0; po pierwszym segfaultcie `coredumpctl palace`
nie znalazł zrzutu. To potwierdza ustawienie i brak zarejestrowanego dumpa
w tym środowisku.

## Tanie filtry i błąd integracji

- `tools/experiments/complex_coarse.py build`: osobny probe, cached builder,
  bez rekompilacji zależności. Pierwszy build2,049s; drugi zachował binarium.
- `run <nowy-katalog>`: limit60s/2GiB/no extra swap, manufactured3D stencil,
  512complex vs1024real, dwa RHS i dwie faktoryzacje ze stałym wzorcem.
  Obie reprezentacje PASS: relative solution≤1,24e−13, raw≤5,47e−14;
  tracked cuDSS peak2,64MB vs4,92MB, live0poDestroy.
  Czasy są cold/order-biased; nie są benchmarkiem szybkości.
- Pierwszy Palace tiny FAIL/segfault: nowy plik błędnie kompilowany jako
  host CXX. Layout MFEM SparseMatrix zależy od CUDA_VERSION; wrapper
  GetDiag trafił w błędny stan cuSPARSE. Naprawa: ten sam CUDA source
  target co upstream cudss.cpp, compile-time guard i jawny lifetime CSR.
  Nie przebudowano MFEM. Artefakt pierwszego FAIL zachowany.
- Tiny po poprawce: 6/6,153iteracje,12,529s; S/pola zgodne z exactblock,
  cuDSS113,33MB vs167,93MB (−32,5%). Nie ekstrapolować fill liniowo.
- TEM3,55GHz/oba porty:39/42iteracje,18,729s,raw≤9,594e−7;
  q6E≈0,49531%,B≈0,45578%,poniżej1%.
- Fallback Ar+Ai na nowym binarium:6/6,233iteracje,13,650s,polaPASS;
  natywny marker nie wystąpił. Default zachowany.

## Referencja i pełna antena

Stały fixture:3,50GHz/P2, P1 zakończony50Ω, Order2/PA1,
11 218 724 ND DOF, meshSHA
`ec56c9a7de3e9cdc9618b87a2029975d474d6d5621f9fd08b35f24501b6f161e`.
Native coarse:2 196 005complex unknowns,32 284 067nnz.

| Run w `artifacts/` | Wynik | Zakres |
|---|---|---|
| `m1-native-complex-coarse-antenna-right-20261018` |35iter/419,080s,raw8,36e−7|Trace; porównanie do starego EXP12 FAIL|
| `m1-native-complex-coarse-antenna-tight-r2-20261018` |24iter/360,946s,raw7,28e−10|Nowa ostrzejsza referencja FP64, warm z poprzedniego solve|
| `m1-native-complex-coarse-antenna-qualified-20261018` |35iter/447,462s,raw8,36e−7|Bez phase-trace; kontrola względem tight PASS|

Pierwszy run różnił się od EXP12 w complexS o0,0011899, a regionalne
B o1,17–1,21%; przekroczył zamrożone progi. EXP12 miał raw≈0,125
i nigdy nie był zakwalifikowaną referencją dokładności. Nie podniesiono
progów. Najpierw wyznaczono silniejszą referencję z Tol1e−9, następnie
powtórzono **rzeczywisty 35-iteracyjny** solve medium względem niej.

Root sprawdził K.3/K.4 dla qualified→tight:

| Miara | Zmierzono | Próg |
|---|---:|---:|
|raw relative RHS|8,36e−7|1e−6|
|max ΔcomplexS|6,70e−9|1e−3|
|ΔVSWR|8,30e−9|0,01|
|Δsumy znormalizowanych mocy portów|1,13e−9|1e−3|
|względna różnica energii|2,95e−8|1e−3|
|max względna różnica E/B, całość i regiony|9,89e−8|0,01|

VSWRP2=1,6684235. To benchmark solvera, nie najlepszy projekt produkcyjny.
`root-analysis.json` zawiera SHA/config/build i niezależne przeliczenia CSV
(S: dB/stopnie→complex). Snapshoty E/B i manifesty pozostają w artefaktach.

`--initial-fields` przyjmuje ukończone, zweryfikowane SHA/fizyką/dependencies
przybliżenie, także po nieudanym porównaniu dokładności. To wyłącznie start
nowego solve; źródłowy status jest w command.json. `--field-reference`
nadal odrzuca field_accuracy_passed=false. Niekompletne/uszkodzone dane
i inna fizyka są odrzucane dla obu ról. Parser nie certyfikuje referencji
samymi hashami; dowody jakości powyżej są osobnym krokiem.

## Pamięć i czas — granice porównania

Qualified:cuDSSpeak25,008GB, managedpeak55,148GB, cgrouppeak58,899GB,
sampledGPU-process2GiB. CuDSS zawiera się w managed; nie sumować.
Przed postprocess release zmniejszył managed45,342→8,650GiB;
postprocess potrzebował24,009GiB. Allocator cuDSS live na końcu0.

Pełny exact real-block EXP17 zatrzymał guard: cuDSSlive przy setup30,641GB
vs25,008GB native (około18,4% mniej). Nie ma ukończonego porównywalnego
wall time dla tego bloku. Dawny tańszy realny Ar+Ai miał słabsze kryterium
zbieżności;419/1089s nie stanowi kontrolowanego speedupu (inne PC/strona/start).

Bez phase-trace:setup93,545s,GMRES259,460s,post+fields11,896s.
Exclusive timery GMRES:KSP29,165s,P158,248s,coarse72,105s;
nie dodawać ich ponownie do GMRESinclusive. Trace pełnego runu ma176
sparowanych zdarzeń hostowych, bez braków. Nie mierzy kerneli ani
transferów UVM w tym eksperymencie. Późniejsze EXP22 domknęło M1.4: [profil](profiling-window.md), [alokacje](memory-audit.md).

Źródła API: pinnedMFEM4.9 oraz archiwum cuDSS/CUDA12.9.1,
[functions](https://docs.nvidia.com/cuda/archive/12.9.1/cudss/functions.html),
[types](https://docs.nvidia.com/cuda/archive/12.9.1/cudss/types.html),
sprawdzone2026-10-18. Nowych dokumentów cuDSS nie utożsamiać z0.7.
Kod prototypu Apache2.0; runtime biblioteki NVIDIA ma własne warunki.
