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

## Decyzja i następny eksperyment

Nie promować tego TF32 requested ani FP64 cuBLAS backendu. Zwykłe FP32 jest
lepszym kandydatem jakości/kosztu w tym teście. M6.3 instruction/counter proof
TC **NOT RUN**; brak deklaracji użycia TC i brak uniwersalnego odrzucenia TF32.

Następny tani filtr: fused FP32 accumulation w istniejącym układzie FP64 caller,
konwersje w rejestrach zamiast dodatkowego397MB scratch i całych pack/unpack.
Ta sama kontrola CPU/FP64, rzeczywiste N, transpose/add i pamięć przed integracją.
Potem wyłącznie jawny scope PC z fallbackiem i niezależnym oryginalnym FP64 A
oraz Ax−b. K/W.1→W.2→W.3 i czas całego jobu wymagane przed promocją; zmiana
liczby iteracji oraz UVM może odwrócić mikrobenchmark. BF16/FP16 i cuBLASLt tuning
nie wykonane. M6.4–M6.6/M7 pozostają otwarte.

## Odtworzenie

```sh
python3 tools/experiments/ceed_tensor_probe.py build
python3 tools/experiments/ceed_tensor_probe.py run artifacts/NEW-screen --seconds 120
python3 tools/experiments/ceed_tensor_probe.py run artifacts/NEW-scale --scale --seconds 120
```

Build cache/hashe w build/m6-ceed-tensor; niezmienione dependencies i solver.
Screen source/manifest snapshot w build/m6-ceed-tensor/exp107-screen.
146pinnedtestsPASS, w tym coverage/flags/NaN/progi/mediany i zachowanie
negatywnego mixed wyniku. Przywrócenie solvera niepotrzebne: nie został zmieniony.
Wyniki: artifacts/m6-ceed-tensor-probe-v3-20261021 i m6-ceed-tensor-scale-20261021;
niezależna root analiza artifacts/m6-ceed-tensor-root-analysis-20261021.json.
JSON303735/120695B, stdout4608/2052B; małe normalne wyniki, bez dyskowego workspace.
