# Stan i dowody optymalizacji

Aktualizacja: 2026-10-18. Mode: goal, Active: M1. Checklisty: [PLAN](PLAN.md); bramki: [MILESTONES](MILESTONES.md). Raport danych: [M1](docs/optimization-baseline.md). Instrukcja narzędzi: [pola](docs/field-validation.md).

## Bieżący checkpoint

- Ostatni zamknięty etap: M0. M1 pozostaje otwarty; żaden wariant optymalizacji anteny nie jest promowany.
- **Zachowana ukończona referencja:** artifacts/m1-antenna-fields-reference-r2-20261018/ —3,50GHz/P2, ta sama siatka medium, FP64 operator/faktory/baza na SSD, UVM/MAGMA,151iteracji,1384,22s. E/B i fields.json z SHA są kompletne. Nie przeliczać od zera bez koniecznej zmiany referencji.
- **Nieukończony kandydat:** artifacts/m1-antenna-fields-fp32-r2-20261018/ — guard6GiB przerwał około141iteracji po1087,70s; minMemAvailable4,70GiB, bezOOM. Brak pól/S/porównania antenowego, brak dowodu przyspieszenia. Procesy i kontenery terminalne, scratch posprzątany; nie ponawiać bez nowego uzasadnienia.
- **Następny krok:** audyt właścicieli alokacji managed/operator/q-data/workspace oraz cgroup peak przy ograniczonym setup/fragmencie GMRES, przed nowym pełnym kandydatem. Wykorzystać już zapisane E/B do przyszłego porównania. Zachować progi1% i medium; nie obniżać progu guard ani tolerancji dla sukcesu.
- Wąskie gardła referencji: preconditioner647s +coarse78s; Krylov522,7s (zawiera basisIO). Logical managed peak44,95GiB, cuDSS peak7,52GiB; nativeRSSHWM6,39GiB nie rozlicza całego UVM/RAM. Globalna telemetria obejmuje desktop. Szczegółowy podział nadal otwarty.
- Jakość: rawresidualFP64~0,1253 to inna miara niż stoppingnormLEFT. Known TEM i niezależne normy pól sprawdzone na coaxie; aktualny błąd pól FP32 **anteny** nie jest jeszcze znany. Nie przenosić kwalifikacji coaxa na antenę.
- Sprzęt: jedna5070Ti16GB +96GBRAM. Bez płatnego compute i bez obowiązkowego multi-GPU. FEM–BEM/MoM pozostaje wymaganym M2, po bramce M1.

## Rejestr eksperymentów

| ID20261018 | Status i decyzja | Dowody |
| --- | --- | --- |
| EXP01 | Coax FP32/FP64: porty zgodne, rawresidual nie znika z FP64; sam storage nie wyjaśnia norm | m1-coax-{raw-residual,fp64-raw-residual}-20261018 |
| EXP02 | Audyt anteny: AIR61,71%elementów, PTFE30,03%; jeden dense BEMblock~11,90GiB, nie dowód oszczędności | m1-mesh-audit-20261018.json |
| EXP03 | Probes TEM E/B/energia PASS; LEFTvsRIGHT pokazuje różnicę raw/stopping, RIGHT więcej iteracji | m1-tem-fields-{left-fp64,left-fp32,right-fp64}-20261018 |
| EXP04 | Tiny natywne L2PASS<1% obu portów, szybki smoke11,25s; wcześniejszy20mmL2FAIL/deadline180s zachowany | m1-tem-validation-20261018.json |
| EXP05 | Całe pola tiny: FP32vsFP64PASS(E≤1,14e−7,B≤6,09e−5); fault B×1,02 prawidłowoFAIL1%; diskvsresidentPASS≤9e−13 | m1-fields-tiny-{reference,fp32,perturbed,detection,disk}-20261018 |
| EXP06 | Pierwszy run anteny przerwany sygnałem, przyczyna nieustalona; background tiny potwierdził livePID po launcherze. Ref-r2PASS, candidate-r2FAIL/hostguard | m1-antenna-field-attempt-20261018.json, m1-background-smoke-20261018 |

Wszystkie ścieżki w tabeli pod artifacts/. Zawierają argv/config/build manifesty, wynik, telemetry i logi. Kontenery mają deadline, a agent śledzi konkretny PID+birth; brak liveuchwytu nie jest sam w sobie sukcesem. Dane są lokalne, ważne liczby/ograniczenia zapisane w raporcie w Git.

## Reguły kolejnych prób

Jedna próba = hipoteza zapisana przed runem, referencja/input/build hash, dokładne argv, limit, wynik i decyzja PROMOTE/REJECT/REPEAT WITH CHANGE/BLOCKED. Statusy: PLANNED/RUNNING/PASS/FAIL/NOT RUN; FAIL kompletności nie jest poprawnym wynikiem RF. Zapisuj brakujące pomiary, nie domysły.

Domyślnie tiny~11s, nativeL2~18s; większy case tylko po filtrze. Cache dependencies/CMake/ccache zachowany. Nie powtarzać3razy/sweepa przed finalistą. Ta sama Luna high uruchamia gotowe polecenia i babysitting; agent główny projektuje oraz analizuje.

Nowa numeracja: M1referencja/profil →M2prototypMaxwellFEM–BEM/MoM →M3pamięćGMRES →M4reuse →M5preconditioner/mixedprecision →M6TensorCores →M7kwalifikacja jednejGPU. Nie odhaczać etapu bez spełnienia kryteriów. Rust wymaga osobnego uzasadnienia; nowy FP32cuDSS wymaga nowej hipotezy, nie powtórki odrzuconej próby.
