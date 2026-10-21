# M6 — decyzja po ocenie kerneli i sweepów

2026-10-21, ocena zakończona EXP176. [M6](M6.md), [sweepy](sweeps.md),
[WMMA](../tf32-wmma.md), [PC FP32](../pc-basis-fp32.md).

## Decyzja

Do M7 przechodzi już kwalifikowana kombinacja: direct FP32 GMRES **storage**,
oryginalna arytmetyka/operator/residual FP64, scaled FP32 native complex LU
z2stałymi FP64 korekcjami oraz reuse setupu obu portów i deferred release.
Siedem par anteny/oba porty PASS; czasy/pamięć/zakres w
[kwalifikacji anteny](antenna-sweep-qualification.md).

Kernele PC FP32/compensated niepromowane: małe pełne runy jakościowo PASS,
bez wykazanego netgain; W.3 dla tych wariantów NOT RUN. Biblioteczny TF32/Lt
wolniejszy od FP32 w rzeczywistych wymiarach; fuzja WMMA dała lokalnie10%
vsfusedFP32 i dowód instrukcji TC, lecz prosta podmiana nie przeszła nowej
bramki W.1. Nie wymuszamy kosztownej anteny po negatywnym filtrze.
Nie jest to odrzucenie wszystkich możliwych implementacji Tensor Cores.

## EXP176 — matematyczny filtr przed PC

Preregistered `--wmma-checks`, N257, INTERP/CURL. alpha1.23456789012345,
superposition i11skal1e-300…1e300, niezależny longdouble CPU, oryginalny
FP64/control/canaries. Deadline120s,6GiB/no swap; wykonanie7.75s/exit0.

| Błąd relativeL2 | INTERP | CURL |
| --- | ---: | ---: |
| Original FP64 homogeneity |1.54e-16|1.88e-16|
| Fused FP32 homogeneity |7.89e-8|8.70e-8|
| Fused WMMA homogeneity |2.33e-4|3.59e-4|
| Fused WMMA superposition |2.38e-4|3.57e-4|

Próg mixedlinearity2e-6 zapisano przed runem (FP32 actionfilter), osobno od
luźnego TF32action2e-3. WMMA nie przechodzi; FP32 przechodzi. To wada
przybliżonej akcji bazy, nie zmierzony defekt całego PC lub błąd VSWR.

Original/FP64 wszystkie11skal PASS1e-11. Wszystkie testowane warianty z
prostym castem FP32 mają ten sam ograniczony zakres:1e-300/1e-80 dają
finitezera irelativeerror1;1e80/1e300 dają10794nonfiniteoutputs perakcja.
Środkowe7skal WMMA przechodzą luźny actionfilter, nadal z błędem~3e-4.
Nie dodano clampingu ani cichego zerowania. Nie istnieje jeszcze kwalifikowany
rangefallback tej nowej ścieżki; brak integracji zachowuje oryginalny operator.

Receipts: `artifacts/m6-wmma-controls-20261021/{case,result,root-analysis}.json`.
Parser zachowuje mieszane wyniki FAIL jako dowód zakończonej oceny, lecz
wymaga poprawnych referencji, skończonych norm i kompletnego coverage.

## Dlaczego nie włączać po prostu FGMRES

`FgmresSolver::Mult` w `palace/linalg/iterative.cpp` jawnie odrzuca
`UseStoredBasis()`: obecna kompresja GMRES nie obsługuje FGMRES. FGMRES
utrzymuje też dodatkowe Z, co widać w Update/Initialize, więc nie jest
bezpłatną zmianą nazwy solvera. Dla wektora E179499584B iK64 pełne V65+Z65
mogą oznaczać~23.33GB samych danych bazy kontra~5.83GB logicznego FP32 V65.
To rachunek maksymalnej reprezentacji, nie peak/rezydencja/pomiar runtime.
Nie stwierdzamy, że FGMRES nie może się opłacić. Wymaga osobnego prototypu
storage V/Z i pomiaru całego zadania; nie uzasadnia promocji obecnego WMMA.

## Zamknięcie oceny, nie całego celu

- M6.1–M6.3: rzeczywiste wymiary, biblioteka przed własnym kernelem,
  conversion/workspace costs i scopedTCinstructionproof ocenione.
- M6.4/M6.5: brak promocji PC bez K/netgain; negativeW.1 kończy prostą
  integrację WMMA. Wcześniejsze pełne małe PC próby bez netgain zachowane.
- M6.6: sweep/PROM/reuse/heldout i7punktów anteny ocenione, bez luźniejszych
  progów. BF16/FP16 nie są zakwalifikowane ani wymagane do promocji finalisty;
  pozostają odrębnymi hipotezami, bez deklaracji o ich uniwersalnej porażce.

M7 pozostaje wymagany: W.4/W.5 (w tym 2.9GHz S/Z/pola), trzy pełne pary
pomiarów, istotnie inna geometria z nową referencją, odtwarzalny pakiet i
końcowy raport jakości/Pareto. Goal aktywny, nieukończony.
