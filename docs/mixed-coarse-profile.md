# M5.5 — ruch UVM po mixed coarse

EXP102,2026-10-21. **PASS pomiaru diagnostycznego**, nie nowa kwalifikacja RF.
Referencją jakości/czasu całego zadania pozostaje EXP100 z raportu
[mixed coarse](milestones/mixed-coarse-plan.md).

## Metoda i naprawiony błąd runnera

Ten sam native build sourceSHA8692e80d926a58a74f38bff9c643b578810a94d35d4d534a2c027215fd11607f,
T-Shaped medium3,50GHz/P2, direct FP32 storage/FP64 operator, K64/rightPC,
identyczny seed startowy. Zmieniona wyłącznie opcja mixed coarse. Pinned Nsight
2026.5.1, selective capture30:2, dwa późne kroki GMRES. Kalibracja zegara hosta,
ostrzeżenia i pokrycie iteracji nadal wymagane. Analiza używa enumów z samej
bazy Nsight, nie przypuszczalnych etykiet.

Pierwszy tiny profile wykonał ścieżkę CUDA prawidłowo, ale runner żądał sześciu
setupów z całego coax sweepu po kontrolowanym stopie w pierwszym solve. To
FAIL zachowany w `m5-mixed-profile-tiny-20261021`. Regresja rozdziela jeden
setup profilu od sześciu pełnego runu. V2 PASS,8,453s, brak ostrzeżeń;
RFcomplete nadal false. Typ faktorów i mixed summary/cleanup są teraz bramkami
profile_complete. Nie osłabiono bramek pełnego solve ani kalibracji.

## Wybrane dwie iteracje

| Pomiar | Native FP64 | Scaled FP32 +2×FP64 korekcja |
|---|---:|---:|
| Krylov sample |12,944s|10,530s|
| PC inclusive |11,033s|8,704s|
| W tym coarse |4,450s|2,279s|
| PC poza coarse |6,583s|6,425s|
| Ortogonalizacja |0,644s|0,568s|
| Liczba kerneli w oknie |5262|11420|
| UVM H→D page fault/coherence |9,632GB|8,249GB|
| UVM H→D speculative prefetch |115,596GB|85,280GB|
| UVM D→H eviction |125,897GB|93,105GB|
| Razem UVM |251,125GB|186,635GB|
| D2D (poza powyższą sumą UVM) |15,186GB|15,257GB|

Ruch UVM spadł **25,68%**, czyli125,562→93,317GB/iterację w tym oknie.
To powtarzane migracje stron w obu kierunkach, nie unikatowy working set.
Czas okna spadł18,65%. Nie ekstrapolować tych dwóch iteracji na sumę całego
zadania. Sum czasów kopii/kerneli nie dodawać do walltime: nakładają się.

FP32 wykonuje więcej kerneli przez trzy solve i korekcję, a mimo tego coarse
jest szybszy. Hcurl kernel1,918→1,914s pozostał podobny; nowe ważne cele to
pozostały PC/libCEED/MAGMA i jego dane. Nie jest to dowód wykorzystania TC.
Kalibracja held-out0,327/0,647µs, margines10µs, brak ostrzeżeń i OOM.
RFcomplete=false, profile_complete=true; pełne memory_marks=false zgodnie
z celowym przerwaniem. Partial cgroup nie jest nowym pomiarem szczytu pełnego runu.

## Cały koszt i następny kierunek

W ukończonym EXP100: factor40,528→4,823s, setup83,600→48,390s, coarse61,613→
32,038s, PC poza coarse96,235→95,123s. Pełny runner339,362→273,843s.
Profil wspiera hipotezę mniejszego ruchu UVM; nie pozwala przypisać całego
zysku transferom ani sumować faktora drugi raz z setupem.

Nowy native Total271,522s: nawet całkowite usunięcie32,038s coarse da najwyżej
około1,134× dla całego runu. PC poza coarse95,123s to około35% Total; dalsze
prace powinny mierzyć rzeczywiste rozmiary jego operatorów i ruch pamięci.
M6 może badać batching/fuzję oraz TF32 tam, gdzie kernel i K na to pozwalają.
Same szybsze FLOP nie usuną working set przekraczającego16GB.

Odtwarzanie: komenda W.3 z raportu mixed coarse, bez save-fields/field-reference/
setup-audit/release-final-solver/release-gmres-basis, z `--nsys-window 30:2`
i limitem600s. Control pomija mixed flagę. Bez przebudowy native/dependencies
po zmianach runnera. Profiler temp/SQLite wRAM, bez swap/SSD workspace;
końcowy rep<=64MiB jest zwykłym wynikiem. Mechanizm: [profilowanie](profiling-window.md).

Dowody: `artifacts/m5-mixed-profile-antenna-{control,on}-20261021/`,
`artifacts/m5-mixed-profile-root-analysis-20261021.json`. M5.5 ocenione,
M5.6 zostało później ocenione negatywnie w EXP104 na resource/API gate;
[decyzja](fdtd-budget.md). Bez globalnej promocji mixed.
