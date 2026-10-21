# M6.3 — cuBLASLt i dowód Tensor Cores

Stan 2026-10-21: **EXP167–168 wykonane; obecna ścieżka Lt niepromowana**.
Screen12/ladder42akcji i wszystkie niezależne kontrole PASS. Lt przy actualN
wolniejszy od FP32 we wszystkich6akcjach, większy błąd. Model `strata`
odładowano przez jego API po jawnej zgodzie użytkownika; wcześniejsza odmowa
preflight z małym VRAM była NOT RUN i została zachowana w historii.
Nowy scalony [prototyp WMMA](tf32-wmma.md) ma osobny dowód instrukcji TC;
nie przypisujemy go nieprzezroczystym kernelom biblioteki.

## Research i wybór biblioteki

- [cuBLAS12.9.1](https://docs.nvidia.com/cuda/archive/12.9.1/cublas/index.html):
  używamy istniejącej biblioteki w przypiętym obrazie `tools/runtime.json`;
  licencja NVIDIA CUDA Toolkit, nie nowa zależność. Lt daje heurystyki,
  kontrolę workspace/alignment i metadane implementacji. Sam FAST_TF32
  zezwala na określoną precyzję; nie dowodzi wykonania instrukcji TC.
- [libCEED actual source](https://github.com/CEED/libCEED/blob/cbd49027b0ae891f0c8efd9d9cf05bc82385a388/backends/magma/ceed-magma-basis.c),
  BSD-2-Clause: audyt EXP105/source receipt w `artifacts/m6-kernel-selection-20261021.json`
  wiąże kopię z buildera z tą rewizją/SHA. P/Q<=40 korzysta z własnej
  nietensorowej ścieżki MAGMA, więc samo przestawienie math mode cuBLAS
  nie zamienia aktywnych wywołań solvera na Tensor Cores.
- [MFEM](https://github.com/mfem/mfem), BSD-3-Clause: istniejące FE/tabulacje
  i integracja libCEED pozostają źródłem rzeczywistego operatora oraz
  niezależnej pętli CPU w probe. NativeMFEM4.9 z istniejącego obrazu/builda,
  jego binarna tożsamość w recipe probe; bez zmiany wersji lub domniemania,
  że upstreamHEAD odpowiada zainstalowanej bibliotece. Domyślne piny
  `cmake/ExternalGitTags.cmake` nie są dowodem rewizji odziedziczonego obrazu.
- CUTLASS/własny WMMA: odroczone do oceny Lt. Biblioteka już udostępnia
  potrzebny pierwszy eksperyment. Nie przebudowujemy całego stosu.

## Dlaczego FLOP/s nie wystarczy

Actual ND2/CURL forward: P20,Q14,3składowe,N1601320.
`2*P*Q*3*N = 2690217600` operacji przy liczeniu FMA jako2.
FP64 x ma256211200B, y538043520B; optymistyczne minimum to794254720B
przy jednokrotnym odczycie x i zapisie y, bez macierzy bazy/cache misses.
To zaledwie3,387operacji/B. Nie jest to pomiar transferu ani założenie o
rezydencji UVM. Oddzielny pack/GEMM/unpack dodaje ruch i bufory FP32;
TF32 zachowuje32-bit storage. Dlatego oceniamy całe apply i setup oraz
porównujemy fusedFP32 bez pośrednich wektorów, a nie tylko czas GEMM.

## Dokładny eksperyment

`tools/experiments/ceed_tensor_probe.{cpp,cu,py}` + `ceed_lt_probe.hpp`:

- Opcjonalne `--lt`, osobno od compensated. Stare screen/scale bez flagi
  zachowują pokrycie i metody; żadnych zmian natywnego solvera/defaultów.
- ND2/Q14 INTERP/CURL, forward/transpose/ApplyAdd; screen12akcji przy
  N257/131071. Po kontroli screen ladder42akcji przez7rozmiarów do1601320.
- Do8heurystyk per składowa; pierwszy sprawdzony AlgoCheck z metadanymi
  tensor-op i TF32input. Brak exhaustive autotuningu. Wszystkie zwrócone
  heurystyki/statusy/selectedID/flags i rzeczywiste alignment zapisane.
- Workspace limit64MiB, jeden współdzielony bufor dla składowych; osobno
  FP32 input/output/basis bytes oraz czas planowania. Konwersja x i y
  jest wewnątrz mierzonych3powtórzeń apply. Basis-pack once osobno.
- Brak algorytmu zostaje jawnie `supported=false`, bez fikcyjnego czasu.
  Błąd runtime nie jest uznawany za prawidłowy brak wsparcia.
- Istniejące originalMAGMA/FP64-layout/longdoubleCPU/canaries/fault controls
  i luźny filtr TF32action2e-3. To nie zmiana frozenRF/fields/raw tolerancji.
- Deadline120s,6GiB cgroup/no swap, lokalnie; minimum2048MiB wolnego VRAM.
  Wyniki czasu wymagają wolnego GPU; nie mierzyć konkurując z `strata`.

Komendy wykonane przez tę samą Lunę (przy powtórce użyć nowych katalogów):

```sh
python3 tools/experiments/ceed_tensor_probe.py check
python3 tools/experiments/ceed_tensor_probe.py run artifacts/m6-lt-screen-20261021 --lt --fused --seconds 120
```

Ladder dopiero po analizie root, do nowego katalogu:

```sh
python3 tools/experiments/ceed_tensor_probe.py run artifacts/m6-lt-scale-20261021 --lt --fused --scale --seconds 120
```

## Instrukcje i dalsza bramka

`ncu` nie znaleziono wPATH, driver `RmProfilingAdminOnly=1`; nie zmieniamy
uprawnień ani drivera. Gotowa droga do zbadania po execution: istniejący
przypięty NsightSystems/CUDA activity wRAM wskazuje wywołany kernel,
[cuobjdump12.9](https://docs.nvidia.com/cuda/archive/12.9.1/pdf/CUDA_Binary_Utilities.pdf)
`--gpu-architecture`/`--function`/`--dump-sass` pozwala ograniczyć statyczną
analizę do właściwej architektury/funkcji. Samo SASS lub nazwa kernela nie
jest licznikiem wykonanych instrukcji; ewentualne warunkowe gałęzie trzeba
wykazać. EXP169 trace wykonany:5052kernelcalls/29symboli, brak utraty zdarzeń.
Początkowy parser błędnie uznał Info/enum tables za failure; oryginalne
receipts zachowane, offline root-reanalysis.json PASS po naprawie klasyfikacji
według severity enum i testach. EXP170 exactfunction/SASS lookup wSM120
bibliotek cuBLASLt i cuBLAS nie znalazł symboli; status **NOT PROVEN**, nie
wniosek o braku TC. Module/JIT mapping pozostaje nierozstrzygnięty.
Własny WMMA uzyskał odrębny, ścisły dowód wEXP173; patrz raport powyżej.

Promocja PC dopiero po wykazanej korzyści i W.1→W.2→W.3 z oryginalnymFP64
operator/residual/fields oraz całym czasem i pamięcią. Przy negatywnym tanim
filtrze bez kolejnej wielkiej anteny. BF16/FP16 osobne hipotezy; żadnego
założenia o dostępności FP64emulation z nowszego CUDA naSM120.

## Ocena kosztu EXP168

ActualN1601320: forward Lt3.600/3.580ms vsoriginal3.478/3.484,
fusedFP32~1.337ms. Transpose Lt3.308–3.714ms vsFP32pedantic2.914–3.513.
Lt wolniejszy od FP32 we wszystkich6actual-size akcjach. MaxrelativeL2
3.316e-4/scaled6.792e-4 (luźny actionfilterPASS). Selectedalgorithm23,
implflags262658; selectedworkspace<=327360B, probe alokuje64MiBceiling.
Nie exhaustive autotuning/wholejob kwalifikacja. Decyzja: odrzucić obecną
osobną pack/GEMM/unpack ścieżkę do promocji PC; zbadać brakującą fuzję
FP64input/output we własnym WMMA przed pełną anteną. Dowody:
`artifacts/m6-lt-{screen,scale,trace,sass,sass-cublas}-20261021`,
`artifacts/m6-lt-root-analysis-20261021.json`.
