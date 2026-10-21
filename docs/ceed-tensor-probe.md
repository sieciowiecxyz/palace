# M6.2 — biblioteczny FP32/TF32 kontra oryginalne basis apply

EXP107–108, 2026-10-21, jedna RTX5070Ti16GB/96GBRAM. **Filtr mikrooperacji
PASS; brak promocji do solvera.** Oryginalny operator i raw residual niezmienione.

## Metoda

Izolowane tools/experiments/ceed_tensor_probe.{cpp,cu,py}, dwie małe TU.
Istniejący libpalace InitBasisFromRule/MFEM4.9 i libCEED MAGMA z przypiętego
runtime; bez przebudowy dependencies/Palace. CUDA12.9.1/cuBLAS120901.
ND2tetP20,RT1tetP15,H1P2tetP10,ND2triangleP8; Q6/14, interp/curl/div/grad,
forward/transpose/ApplyAdd, components1/2 i niepodzielne sizes.

Q14 tetra: standardowa reguła MFEM. Q6 tetra: **reprezentatywna reguła ściany**,
triangle6points przeniesione na z=0, nie nieistniejąca standardowa tet volume
rule. Sam audyt metadanych nie ustalił dokładnych punktów wszystkich W.3 trace
bases. To rzeczywista tabulacja FE przez fabrykę Palace; nie eksport identycznych
współczynników każdego operatora W.3. Reguły zachowane w pamięci ze względu
na MFEM cache po adresie. Nie ma globalnej zmiany precyzji CeedScalar.

Referencja: faktyczne CeedBasisApply/ApplyAdd; dla257elements również niezależna
pętla CPU long double. CUDA/cublasDgemm sprawdza layout FP64. Kandydaci:
FP64 input → jawna konwersja FP32 → cublasGemmEx → konwersja/output FP64.
Transpose sumuje wszystkie q_components; ApplyAdd dodaje wynik do FP64 caller.
Brak zbędnego packingu layoutu: wejścia/baza mają istniejący component-major
układ; osobne GEMM per component. Konwersje input/output są w każdym apply.
Stała baza FP32 pakowana raz, koszt zapisany oddzielnie. Alokacje/utworzenie
bazy/handle/JIT nie są w steady-state apply; nie jest to benchmark całego jobu.

[Oficjalne compute modes CUDA12.9.1](https://docs.nvidia.com/cuda/archive/12.9.1/cublas/index.html#cublascomputetype-t):
FP32 pedantic i żądane FAST_TF32 to osobne warianty z FP32 storage. Pozwolenie
na TC nie jest dowodem wykonania instrukcji TC. Biblioteka cuBLAS oceniona
przed custom kernel/CUTLASS; strojenie cuBLASLt nie zostało wykonane.

## Kontrole i granice

Przed pomiarem ustalone progi relativeL2/scaledMax: FP64 1e-11,
FP32 2e-6, TF32-requested2e-3. To **progi filtra działań**, nie zmiana tolerancji
RF/pól/rawresidual. Canaries sześciu buforów, celowa perturbacja kontrolera,
pełna mała kontrola CPU i porównanie wszystkich wyników GPU z oryginałem.
Parser sprawdza exact coverage, błędy/liczby/progi/flag consistency i mediany;
negatywny mixed wynik zachowuje jako wynik eksperymentu, nie ukrywa go jako
brak wykonania. FP64 layout/reference failure unieważnia cały filtr.

Każdy wariant ma warm-up i3 powtórzenia; wall i CUDA event interval (nie same
instrukcje kernela). Zegar, cache i resident buffers mogą wpływać na crossover.
Powtórzenia ApplyAdd akumulują kolejne wyniki bez resetu w mierzonym bloku;
kontrola dokładności przed timingiem zawsze startuje z jednakowego initial Y.
Testy w całości GPU-resident, **bez presji UVM pełnej anteny**. Rozmiary scratch
są rachunkiem alokowanych własnych tablic, nie pomiarem GPU residency ani
workspace wewnętrznego cuBLAS. Cały proces ≤6GiB/no swap, limit120s.

## Wyniki

EXP107v3:96działań,48małych257/48dużych131071,run13,466s,build4,108s.
EXP108:42działania przez7rozmiarów257/1023/4099/16383/65537/131071/1601320;
**tylko6 działań przy rzeczywistym N1601320**,run18,556s/build4,224s.
Wszystkie reference/canary/action gates PASS. Dwa wcześniejsze FAIL zachowane:
build bez backend.h oraz pierwszy run1,016s z błędnym założeniem volumeQ6.

| Wariant | Max relativeL2 EXP107 | Przy N1601320: czas wall jednego apply |
| --- | --- | --- |
| Oryginalny MAGMA FP64 | kontrola CPU PASS | 3,473–3,744 ms |
| cuBLAS FP64 | 2,374e-16 | 8,898–15,432 ms |
| cuBLAS FP32 pedantic + konwersje | 1,054e-7 | 2,598–3,223 ms |
| cuBLAS TF32 requested + konwersje | 4,973e-4 | 3,325–3,631 ms |

Duże rzeczywiste6działań: FP32/original medianratio0,797 (zakres0,748–0,863),
TF32-requested/original0,958 (0,916–0,971). To mediany **ilorazów** poszczególnych
działań, nie przyspieszenie całej symulacji. FP32 szybsze we wszystkich6;
TF32-requested wolniejsze od FP32 we wszystkich6. Przy N≤4099 obie biblioteczne
ścieżki mixed wolniejsze od oryginału we wszystkich6; nie podmieniać wszystkich
poziomów jednym backendem. W szerszym EXP107 przy131071 FP32 faster39/48,
TF32requested22/48. Błędy TF32 są dużo większe, choć przeszły luźny filtr działań.

Przy rzeczywistym rozmiarze input256 211 200B/output538 043 520B (transpose
odwraca), dodatkowy własny FP32 workspace397 130 720B. Static basis pack
0,037–0,042ms. Kopie/konwersje mogą nasilić UVM traffic w pełnym FEM.
Zysk resident compute nie dowodzi zysku w oversubscribed runie.

## Decyzja po bibliotecznym filtrze

Nie promować tego TF32 requested ani FP64 cuBLAS backendu. Zwykłe FP32 jest
lepszym kandydatem jakości/kosztu w tym teście. M6.3 instruction/counter proof
TC **NOT RUN**; brak deklaracji użycia TC i brak uniwersalnego odrzucenia TF32.

Filtr fused FP32 opisany poniżej. Potem wyłącznie jawny scope PC z fallbackiem
i niezależnym oryginalnym FP64 A
oraz Ax−b. K/W.1→W.2→W.3 i czas całego jobu wymagane przed promocją; zmiana
liczby iteracji oraz UVM może odwrócić mikrobenchmark. BF16/FP16 i cuBLASLt tuning
nie wykonane. M6.4–M6.6/M7 pozostają otwarte.

## EXP109–110 — fused FP32 w rejestrach

Opcjonalny czwarty wariant `--fused`. Własny mały CUDA kernel po ocenie biblioteki,
bez CUTLASS/TC. FP64 x/y, staticFP32basis; cast i fmaf w rejestrach. Forward
przelicza dane wejściowe raz na p i współdzieli je między q_components;
transpose sumuje wszystkie składowe, ApplyAdd zachowuje FP64 initialY.
Specjalizacje P/Q/qcomp, nie geometrii/material/freq; unsupported shape i złe
argumenty jawnie odrzucane, brak cichego innego działania. CPU/reference/
canaries/perturbationdetector i progi2e-6 pozostają. Kolejność sumowania różna
od BLAS, więc to nowy kandydat, wymagający później pełnych bramek K.

EXP109:96działań,13,685s; EXP110:42ladder/6actualN,19,344s.
Cached addon build4,904s, bez native/deps rebuild; drugi run z tej samej binarki.
Wszystkie fused action gates PASS, maxrelativeL2 ≤1,148e-7/scaledmax≤5,003e-7.
Przy actualN1601320/P20/Q14/qcomp3, mediany wall3powtórzeń:

| Akcja | Oryginalny FP64 | FP32 fused | Fused/original |
| --- | --- | --- | --- |
| interp forward | 3,474 ms | 1,342 ms | 0,386 |
| interp transpose | 3,634 ms | 3,550 ms | 0,977 |
| interp transpose Add | 3,738 ms | 3,560 ms | 0,952 |
| curl forward | 3,478 ms | 1,334 ms | 0,384 |
| curl transpose | 3,634 ms | 3,549 ms | 0,977 |
| curl transpose Add | 3,738 ms | 3,562 ms | 0,953 |

Forward ~2,6× szybsze, transpose tylko2–5% mniej czasu. Nie ukrywać kierunków
w jednej średniej ani zastępować wszystkich działań. Brak nowych bramek
RF/fullsolver/UVM; tutaj nadal wszystko mieści się wGPU. Cała ścieżka
fused potrzebuje tylko3360B dodatkowej FP32bazy przy tym rozmiarze, **nie**
397130720B wektorów+bazy wariantu bibliotecznego. To koszt własnych buforów
algorytmu; porównawczy proces nadal alokuje float wektory innych metod.
Nie zmierzono spadku processpeak/fullFEMmemory. W row metadata wspólne
extra_fp32_workspace_bytes odnosi się do biblioteki; per-method fused pole
podaje wyłącznie rozmiar bazy, zweryfikowany przez parser.

Decyzja: kandydatem do M6.4 jest **tylko forward w obrębie PC**. Transpose
zostawić oryginalne FP64 w pierwszej próbie; zysk z wersji fused zbyt mały
do uzasadnienia globalnej podmiany. Read-only audyt źródła wskazał ApplyB w
palace/linalg/iterative.cpp jako granicę wokół B->Mult. Plan integracji:
RAII scopePC z audytem wejść/wyjść, zero mixed poza nim (w szczególności A*x
i niezależny rawresidual). Cache coefficientów musi sprawdzać treść/dimensions
i lifetime; sam adres CeedBasis może zostać ponownie użyty po destroy.
EXP112–113 wdrożyły tę granicę/cache i sprawdziły tiny oraz medium3,55.
Jakość/cleanup PASS, ale więcejiteracji i brak wykazanego speedupu: HOLD przedW.3.
[Raport integracji i hipoteza liniowości](pc-basis-fp32.md). K/W.2 pozostałych
freq/W.3 oraz całkowity czas nadal wymagane przed promocją.

Dowody: artifacts/m6-ceed-fused-{screen,scale}-20261021 i niezależny
artifacts/m6-ceed-fused-root-analysis-20261021.json. JSON394168/157144B,
stdout4608/2052B, zwykłe małe wyniki. Gorące dane tylkoRAM/VRAM.

## Odtworzenie

```sh
python3 tools/experiments/ceed_tensor_probe.py build
python3 tools/experiments/ceed_tensor_probe.py run artifacts/NEW-screen --seconds 120
python3 tools/experiments/ceed_tensor_probe.py run artifacts/NEW-scale --scale --seconds 120
python3 tools/experiments/ceed_tensor_probe.py run artifacts/NEW-fused-screen --fused --seconds 120
python3 tools/experiments/ceed_tensor_probe.py run artifacts/NEW-fused-scale --scale --fused --seconds 120
```

Build cache/hashe w build/m6-ceed-tensor; niezmienione dependencies i solver.
Screen source/manifest snapshot w build/m6-ceed-tensor/exp107-screen.
147pinnedtestsPASS, w tym coverage/flags/NaN/progi/mediany i zachowanie
negatywnego mixed wyniku. Przywrócenie solvera niepotrzebne: nie został zmieniony.
Wyniki: artifacts/m6-ceed-tensor-probe-v3-20261021 i m6-ceed-tensor-scale-20261021;
niezależna root analiza artifacts/m6-ceed-tensor-root-analysis-20261021.json.
JSON303735/120695B, stdout4608/2052B; małe normalne wyniki, bez dyskowego workspace.


EXP111 current-recipe regression after argument bounds hardening(p/q≤40,
qcomp≤3 beforeproducts): build1,811s,96screen13,764s/42ladder19,295s PASS,
allprecisionactioncontrols. CurrentbinarySHAa5900a00…c772aa04;
artifacts/m6-ceed-fused-guard-{screen,scale}-20261021. Root checked strictJSON
and commandmanifest hashes. Not M7 performance repeats or RFqualification.

## EXP114–116: dokładniejszy compensated dot na SM120

Status: **kandydat do małego testu PC, nie promocja solvera**. Dotyczy
forward; transpose/Add pozostają porównaniem oryginalnym/bibliotecznym.
Pierwszy `mixed_compensated`: dwie tablice coefficientów FP32 hi/lo,
input hi/lo, FMA residual produktu i TwoSum sumy, FP64 split/recombine.
Błąd mały, ale wszystkie16 większych działań EXP114 wolniejsze1,33–4,06×
według CUDA interval. Nie uruchomiono niezmienionego wariantu na pełnej antenie.

Drugi `mixed_compensated_bits` zmienia wyłącznie split wejścia: jawne RZ
zachowuje pierwsze24bity significand, reszta29bitów jest zaokrąglana i ważona
2^(E−52), ze znakiem wejścia. Dla E∈[−74,100] bez FP64 odejmowania w pętli;
zero osobno, pozostałe termy używają jawnego FP64 fallback z coefficientami
hi+lo. Wyjściowe dodanie hi/lo nadal FP64. To własny eksperymentalny mixed
algorytm, **nie pełne FP64 ani Tensor Cores**. Współczynniki i fixture są
rzeczywistymi tabulacjami FE, ale test nie dowodzi dokładności każdej możliwej
bazy lub całego PC. Inspiracja [Ogita/Rump/Oishi, Accurate Sum and Dot Product](https://epubs.siam.org/doi/10.1137/030601818),
nie twierdzenie, że dowód tej pracy obejmuje nasz wariant. Semantyka RZ i
reinterpretacji bitów: [NVIDIA CUDA casting intrinsics](https://docs.nvidia.com/cuda/cuda-math-api/cuda_math_api/group__CUDA__MATH__INTRINSIC__CAST.html).
Własny kod Apache2; istniejące libCEED/MFEM pozostają przypięte bez zmian.
Źródła sprawdzone2026-10-21, build CUDA12.9.1/SM120, nie aktualizacja zależności.

| Actual ND20/Q14/N1601320, forward | Oryginał | Compensated bits |
| --- | --- | --- |
| Interp, CUDA interval median | 3,482ms | 3,035ms |
| Curl, CUDA interval median | 3,473ms | 3,048ms |

Około12–13% krótsze **GPU-resident basis action**, nie pełny solve. To mediana
3 powtórzeń wewnątrz jednej próby, nie trzy pełne joby M7. ScalarQC1/trace często
wolniejsze, brak uniwersalnej promocji. Koszt własnych dwóch małych tablic
6720B przy P20/Q14/QC3; benchmark nadal trzyma scratch innych comparatorów,
więc nie jest to zmierzona redukcja peakVRAM procesu.

EXP11596actions/32newforward i EXP11642actions/14newforward PASS. Max typowy
L2~9e-15, zakresowy~9,16e-15, gate1e-11. Small257columns mają niezależny
longdoubleCPUoracle, homogeneity α1,23456789012345, superposition oraz11 osobnych
skal1e-300..1e300 z granicami binarnymi. Negatywne wyniki kandydatów zachowujemy;
original/FP64/control muszą przejść. Usunięto absolutne floors z helpera błędu,
aby tiny references nie ukrywały względnego błędu; wstrzyknięte1e-300 błędy
wymuszają FAIL. Guarded fallback testowany, brak testu pełnej liniowości PC.

```sh
python3 tools/experiments/ceed_tensor_probe.py build
python3 tools/experiments/ceed_tensor_probe.py run artifacts/NEW-comp-screen --fused --compensated --seconds 120
python3 tools/experiments/ceed_tensor_probe.py run artifacts/NEW-comp-scale --scale --fused --compensated --seconds 120
```

Cache addonbuild6,035s, screen14,161s, ladder20,235s; native/dependencies
bez rebuilda/zmian. 6GiB/noSwap/120s każda próba; gorące daneRAM/VRAM.
Dowody: artifacts/m6-compensated-screen-20261021,
m6-compensated-bits-{screen,scale}-20261021 oraz
m6-compensated{,-bits}-root-analysis-20261021.json. Root sprawdził strictcoverage,
wszystkie precision/range/linearity flags oraz commandmanifest przeciw aktualnej
binarce/recipe (SHA9c874f98…8957a294). 152pinnedtestsPASS.
Następne: osobna opt-in integracja PC Hcurl forward z contentcache/cleanup,
tiny→mediumK i kosztem całego jobu; bez usuwania obecnego FP64 fallbacku.

## Aktualizacja EXP167–175

[cuBLASLt assessment](cublaslt-assessment.md): --lt screen/scale wykonane,
obecna biblioteczna ścieżka wolniejsza od FP32 przyactualN, niepromowana.
[Scalony WMMA](tf32-wmma.md): --wmma forward z własnym kernelem,
3procesowe mediany~1.20ms vsfusedFP32~1.337ms, większy błąd~3e-4.
Dynamic exactsymbol+SM120SASS potwierdza TCinstructionpath tylkoWMMA.
Dotychczasowe NOT RUN dla nowych ścieżek powyżej opisują stan historyczny;
aktualny PC/FEMquality/netgain WMMA nadal NOT RUN/HOLD.
