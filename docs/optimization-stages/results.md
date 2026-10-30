# Optymalizacja faz — wyniki i zakres kwalifikacji

Stan: **kampania zamknięta zakresowo, profil uniform Restart1 zakwalifikowany**.
To wyniki solvera na jednej RTX 5070 Ti 16 GB / 96 GB RAM,
CUDA/UVM/MAGMA, rank1/OMP1, medium. Nie jest to kwalifikacja projektu anteny do produkcji.

## Co zmieniono

- **OP-06:** lokalizowanie sond przez MFEM dla sprawdzonych wnętrz elementów;
  dotychczasowy GSLIB pozostaje kontrolowanym fallbackiem i ustawieniem domyślnym.
  Usuwa koszt przygotowania GSLIB przy niezmienionych punktach i polach.
- **PRE-03:** jawna ścieżka jednej rangi pomija serializację MeshPart i ponowny
  odczyt ParMesh. Zachowuje order2, topologię, atrybuty, orientację i mapowanie DOF.
- Nie zmieniono geometrii, dokładności medium, precyzji operatora ani tolerancji solve.
  Nie dodano TF32/Tensor Cores, nowego solvera ani SSD spill.

## Pełny medium 1,92 GHz, oba porty

Trzy wcześniej zadeklarowane pary AB/BA/AB; wszystkie sześć próbek w statystyce.
Pierwsza para pochodzi z M4 zgodnie z prerejestracją, nie z wyboru najlepszej próbki.

| Metryka: mediana [min; max] | Baseline | OP + PRE |
|---|---:|---:|
| Native Palace [s] | 738,280 [737,913; 738,976] | 630,324 [630,045; 631,171] |
| Kontroler, czysty wall [s] | 739,611 [739,405; 740,354] | 631,742 [631,416; 632,551] |
| Peak cgroup RAM [GiB] | 66,056 [66,054; 66,058] | 57,029 [57,020; 57,054] |

Różnica median: **14,62% krócej i 13,67% mniej peak cgroup RAM**.
To nie jest pomiar fizycznej rezydencji VRAM ani migracji UVM.
Globalne NVML obejmuje także pulpit; nie przypisywać go wyłącznie solverowi.
Oddzielne M3: OP skrócił pełny run około13,65%, PRE około1,01%.
M4 OP-only637,483s vs combined631,171s to jedna kontrola, nie osobne mediany.

## Poprawność i ograniczenia

- Wszystkie trzy pary combined 1,92GHz mają zapisane RF PASS;
  oba porty, raw relative RHS ≤1e-6, ΔcomplexS ≤1e-5 i ΔVSWR ≤0,001.
- Complex E/B sondy i cały wektor farfield: relL2 ≤1e-5;
  jawny próg absolutny1e-12 dla near-zero, bilans mocy i FF/flux ≤2%.
  Normy próbek nie są pełną objętościową normą pola.
- Świeże pary1,71/2,69/3,80GHz oraz geometria director+2mm mają RF PASS.
  Geometria zachowuje stare materiały, w tym FR4 directora; oba runy miały89iteracji.
  Nie stanowi zmiany produkcyjnej anteny ani reprezentatywnego benchmarku sond.
- Native CPU tiny:749OP +55986PRE assertions. MPI2 fallback:
  OP38+38 i PRE11657+11653; native exit0, raw logi i błędy parsera zachowane.
- PRE M3 ma trzy pary native/RF, ale tylko **dwie czyste pary wall**.
  Jedna ukończona symulacja ma niezmieniony controllerFAIL i osobny dowód recovery.
  Przerwane na polecenie użytkownika2690B pozostaje USER_INTERRUPTED;
  nowy plan resume nie nadpisuje tej próby ani nie czyni jej udaną próbką.

## I/O: świadomie bez promocji

CSV kosztowało milisekundy. Binarny mesh zachował strukturę i pola tiny,
lecz konwersja34,049s + walidacja0,441s daje szacowany zwrot dopiero od22
wczytań identycznej siatki. **IO-06 DEFER**, brak automatycznego cache w zalecanym kodzie.

## Audyt, ograniczenie restartu i profil

1. Niezależny pełny replay **14 unikalnych par PASS**, w tym director+2mm:
   niezmieniony `compare_runs`, rzeczywiste hashy siatek/native/źródeł,
   frozen unit proof i27ukończonych runów. Preaudit zachowano osobno.
   Maksima14par: ΔS4,64e-8, ΔVSWR7,66e-8, pola2,90e-6,
   FF2,23e-7; bilans mocy0,00572W i FF/flux1,705% — wszystkie poniżej bramek.
2. M5.2 invalidation rozliczono testami kontrolera: zmiana staged Permittivity,
   atrybutu BC, FE order, backendu albo raw mesh odrzuca plan przed utworzeniem
   kontenera; brak Popen, receipt pozostaje false. Locator cache jest lokalny
   dla InterpolationOperator i kontroluje mesh/nodes sequence oraz obcy mesh;
   istniejące749native assertions obejmują odmowę stale reuse i fallback map pola.
   IO cache jest DEFER, nie promowano trwałego cache faktorów między konfiguracjami.
   Osiem rzeczywistych CSV na run jest ponownie czytanych i wiązanych hashami;
   nie jest to kwalifikacja restartu z volumetric snapshot.
   Full wrapper wspiera uniform explicitPoint/Restart1; Restart0/2 odrzuca.
   Native smoke: pełny A6solves PASS; Restart2 po pierwszym zbieżnym solve
   (39iteracji/raw9,5991e-7) kończy się **FAIL: Column idx not found in table**.
   B-full/B-restart NOT RUN, bez retry. Parser tworzy nazwy col_N, reload zmienia
   Column.name bez przebudowy name_to_index, PrintDomainE szuka nieistniejącego idx.
   Insert/lookup/reload/PrintDomainE są identyczne z frozen a6; różnice parsera
   to wyłącznie trace scopes. To statyczny dowód odziedziczonego defektu,
   nie dodatkowy frozen-native test ani dowód błędu wszystkich wersji upstream.
   **TODO osobno:** naprawa legacy reload; positive restart nie jest zakwalifikowany.
   Nie blokuje to predeklarowanego uniform Restart1: wrapper odrzuca Restart!=1
   już od4b9652a58, a Restart1 omija reload. Nie rozszerzać profilu po tym FAIL.
3. Kod scalono lokalnie w `130c7819c`; source root jest identyczny z testowanym
   `95822ec5...`, więc nie przebudowywano ponownie tych samych źródeł.
   Zapisano manifest **scopedqualification.json** po niezależnym przeglądzie, związany z SHA
   oryginalnego manifestu i dokładnymi18flagami+2featureflags. Nie nadpisywać
   `numerically_validated=false`, historycznych planów ani wyników. Sidecar jawnie
   odrzuca Restart!=1 i zmianę20flag; reuse/defer wymagają Restart1, a energy-release
   jest częścią tej samej niezakwalifikowanej konfiguracji restartu (presence0 też aktywuje).

Rollback na tej samej binarce: `PALACE_PROBE_LOCATOR=gslib` oraz
`PALACE_SINGLE_RANK_DIRECT_MESH=0`. Frozen M7r3 pozostaje zachowany.
A100/CMP, inne GPU, pełny upstream suite i ogólne przyspieszenie MPI pozostają NOT RUN.

Dowody lokalne: `artifacts/optimization-stages/M6-final-audit-20261030/full-audit.json`
(macierz22bramek i14replayów; poprzedni preaudit.json niezmieniony),
`M5-combined-repeat-20261030/repeated-performance.json`,
`M5-sweep-geometry-20261030/`, `M3-PRE03-full-20261030/three-pair-summary.json`.
Dokładne argv są w planach per-run. Nie wykonywać ponownie ukończonych planów.

Rekomendowany build: `build/optimization-stages-m4-integration-20261030/native/`.
Komendy uruchomienia i rollback: [audyt M6](../milestones/stages-final-audit.md).
