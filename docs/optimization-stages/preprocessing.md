# Audyt i plan: preprocessing siatki

Status: M0 w wykonaniu. Preflight tożsamości wejścia PASS; native preprocessing i pomiary nowych wariantów NOT RUN.
Owner: agent preprocessing, branch `opt/preprocessing-20261029`.
Koordynator scala plan i wspólny checkpoint. Proponowany zakres kodu: `palace/utils/geodata.cpp`, ewentualnie `palace/utils/meshio.cpp`; nie dotykać solverów, wspólnych plików planu ani I/O outputu.

## Granica fazy i dane bazowe

W logu Palace „Mesh Preprocessing” jest timerem wewnątrz „Initialization”, nie obejmuje generowania geometrii ani meshera zewnętrznego. `palace/driver.cpp:59-79` obejmuje w nadrzędnym `INIT` odczyt i przygotowanie siatki, `solver->Preprocess`, partycjonowanie, równomierne refinement oraz utworzenie obiektu `Mesh`. Sam timer `MESH_PREPROCESS` jest zakładany osobno w `geodata.cpp:130` (`Load`) i `:270` (`Partition`). Część dalszego przygotowania MFEM/FE może zostać przypisana do Initialization lub solverowego Setup; nie należy przypisywać całego INIT do tego milestone’u.

Ostatni porównywalny medium run użył już wygenerowanej, stałej siatki; nie mierzył CAD ani generowania siatki. Wyniki: preprocessing 29,224 s (3,54% całości 825,783 s), operator construction 121,501 s lokalnie; na CMP operator construction 401,9 s. I/O Palace 19,612 s to osobna kategoria. Scope może być zagnieżdżony, ale BlockTimer przerywa naliczanie rodzica: końcowa tabela jest exclusive i jej kategorie można sumować w tym single-rank runie. Nie sumować natomiast inclusive wpisów phase trace. Initialization 6,768 s + Mesh Preprocessing 29,224 s daje 35,992 s przygotowania. Nie ma na dziś profilu, który mówi, ile z 29,224 s przypada na odczyt, walidację, transformacje, partycjonowanie i refinement.

## Miejsca w kodzie do sprawdzenia

| Miejsce | Rola / fakt z kodu | Możliwy kierunek | Status |
|---|---|---|---|
| `palace/utils/geodata.cpp:130-264`, `Load` | Ładuje mesh; sprawdza typy i warunki AMR/periodic; opcjonalnie czyści nieużywane elementy, konwertuje typy, reorderyzuje elementy, finalizuje siatkę, robi region refinement i sprawdza granice/interfejsy. Część ścieżek jest warunkowa. | Najpierw rozbić czas na fazy i ranki, potem optymalizować tylko kosztowną ścieżkę faktycznie używaną przez antenę. | `PRE-01` TODO |
| `palace/utils/geodata.cpp:267-369`, `Partition`; zwłaszcza `:314-367` | Wylicza partycjonowanie i rozdziela siatkę; ścieżka zależy m.in. od conformality, AMR i liczby rang. Przy niekonformalnym AMR są dodatkowe konwersje i broadcast porcjowany. | Odrębnie profilować 1 rank i MPI. Rozważyć zmianę tylko wtedy, gdy koszt partycjonowania/broadcastu istotny dla docelowej konfiguracji. | `PRE-03` DEFERRED dla obecnego single-GPU case |
| `palace/utils/geodata.cpp:208-212`, `ReorderMeshElements`; implementacja `:2743+` | Istnieje opt-in `reorder_elements`, który zmienia kolejność elementów/węzłów dla lokalności cache. | Sparowany benchmark on/off może sprawdzić, czy preprocess kosztuje się późniejszym assembly, pamięcią i solverem. Wliczać koszt reordering do całego runu. | `PRE-02` TODO |
| `palace/utils/geodata.cpp:191-205, 2279+, 2375+` | `CleanMesh`, rozcinanie typów elementów i testy typu mesh występują w opcjonalnych ścieżkach; `CheckElements` bywa wywołane ponownie przez konwersję. | Szukać redundantnych przebiegów siatki dopiero po profilerze; bezpieczny mikrotest atrybutów/topologii może wskazać, czy jeden przebieg można współdzielić. | `PRE-04` TODO |
| `palace/utils/geodata.cpp:2174-2215`; konwersje `meshio.cpp` | `LoadMesh` używa wbudowanego czytnika MFEM dla obsługiwanych formatów; COMSOL/Nastran przechodzą przez konwerter do strumienia Gmsh. | Badać parser/format tylko jeśli profil pokaże dominację odczytu lub konwersji. Nie wprowadzać mmap/cache formatu jako założonego rozwiązania. | `PRE-05` TODO |

## Rejestr hipotez i prób

Każdy agent najpierw sprawdza poniższe ID. Dopisuje datę, commit/build/input hash, dokładne polecenie, wyniki, testy poprawności i decyzję. `TODO_TO_CHECK` oznacza hipotezę bez pomiaru; nie jest wynikiem. Po `PASS`/`REJECTED` nowy agent nie powtarza próby bez zmiany mesh, wersji MFEM, hardware, konfiguracji lub ujawnionego błędu.

### PRE-01 — profil faz wewnątrz przygotowania siatki (`TODO_TO_CHECK`)

Hipoteza: 29,2 s ukrywa jedną lub dwie dominujące funkcje, więc ogólna optymalizacja całej fazy grozi pracą nad małym kosztem. Dodać tymczasowe/niskonarzutowe timery wokół istniejących bloków `Load` i `Partition`, a nie logować każdy element. Rozdzielić CPU time/wall time, rank oraz bajty wejścia; osobno oznaczyć koszt I/O. Najpierw krótki profil bez zmiany kodu, jeśli istniejący profiler i dokładne binary pozwalają rozdzielić te fazy.

Zaliczenie: fazy pokrywają się do tolerancji 2% z timerem nadrzędnym, MPI max-rank/wall jest jawny, brak zmian wejścia, topologii lub wyniku. Jeżeli preprocess <5% reprezentatywnego E2E i żaden subetap nie jest istotny przy oczekiwanej liczbie eksperymentów, oznaczyć dalszą optymalizację CPU-preprocess jako `DEFERRED`, nie sztucznie wymuszać speedup.

### PRE-02 — `reorder_elements` end-to-end (`TODO_TO_CHECK`)

Hipoteza: cache locality może obniżyć późniejsze operatory/solver, ale może się nie zwrócić przez koszt reordering albo już dobry ordering wejściowy. Porównać config on/off na identycznym medium mesh i buildzie; preprocess, operators, setup, solve, E2E i peak RAM raportować oddzielnie. Wyników samych operatorów nie używać do decyzji, jeśli reordering dodaje koszt.

Zaliczenie: topologia, materiały/atrybuty, boundary IDs, DOF dimensions i liczby elementów zachowane; rozwiązanie porównane przez normę pola / residuum / S-parametry w zatwierdzonych tolerancjach. Wariant promować tylko przy powtarzalnym E2E zysku ponad szum bez nieakceptowalnego wzrostu pamięci.

### PRE-03 — koszt `Partition` przy docelowym modelu równoległym (`DEFERRED`)

Single-GPU nie oznacza automatycznie single MPI rank, ale brak osobnego pomiaru nie pozwala wnioskować o zysku z nowego partitionera. Najpierw zapisać `MPI size`, `OMP threads`, czas `GetMeshPartitioning`, dystrybucji i rozmiary per-rank. Wrócić do testu tylko dla faktycznej konfiguracji multi-rank albo gdy etap przekroczy 10% E2E. Zachować obecne ścieżki nonconforming AMR i chunked broadcast; nie upraszczać na podstawie konfigu anteny.

### PRE-04 — ograniczenie powtórnych skanów siatki (`TODO_TO_CHECK`)

Hipoteza: opcjonalne clean/split/validation ścieżki mogą wykonywać wielokrotne globalne skany. Profil wywołań i konfiguracji ma wykazać, że dana para skanów wykonuje się w tym samym runie i koszt jest mierzalny. Dopiero potem prototypować współdzielenie już policzonych cech. Nie cache'ować bez jawnej reguły unieważnienia po modyfikacji/refinement; nie zmieniać walidacji dla przyspieszenia.

Zaliczenie: testy tetra/hex/prism/pyramid, curved/linear, conforming/nonconforming oraz region refine odpowiednie do zmienionej ścieżki; identyczne atrybuty i connectivity; brak regresji na MPI jeśli dotknięto partycjonowania.

### PRE-05 — parser/konwersja wejścia (`TODO_TO_CHECK`)

Hipoteza: koszt może zależeć od formatu; COMSOL/Nastran mają koszt konwersji do Gmsh, lecz obecny antenowy fixture może już być Gmsh. Zmierzyć format na fixture reprezentatywnym i porównać tylko równoważne mesh, nie różne eksporty. Nie zmieniać formatu plików projektu ani nie dodawać stałego cache, dopóki oszczędność odczytu nie uzasadni miejsca, walidacji hashy i kosztu zapisu.

## Bramki wykonania tej gałęzi

- P0: odczytać bieżące ustawienia testowego medium fixture i ustalić baseline wejścia/builda oraz czy benchmark liczy preprocess od zimnego procesu.
- P1: zakończyć PRE-01; wybrać jeden kosztowny, faktycznie aktywny podetap. Jeśli profiling unavailable, zapisać narzędzie i powód, nie zgadywać hotspotu.
- P2: wykonać tylko najtańszy pomiar rozstrzygający z PRE-02/04/05. Nie uruchamiać jednocześnie CPU benchmarków na hostach, jeśli wpływają na wynik; nie uruchamiać EM/GPU bez autoryzacji właściwego celu.
- P3: jeśli wynik obiecuje, implementować pojedynczą zmianę i dodać minimalny test regresyjny. Jeśli brak zysku, oznaczyć hipotezę `REJECTED` z liczbami i zatrzymać tę gałąź.
- P4: na integracji odtworzyć krótki medium test przez ustalony workflow, raportując poprawność fizyczną niezależnie od czasu. Aktualizację shared plan/checkpoint robi koordynator.

## Kontrakt poprawności

Każda zmiana mesh preprocessing musi zachować geometryczne położenia w tolerancji wejściowego formatu, orientację elementów, connectivity, geometry/boundary/material attributes, periodic/crack interfaces, jakość/Jacobian, true-DOF constraints i partition ownership. Porównania wymagają tych samych mesh/materials/source/boundary/config oraz wersji MFEM i Palace. Przy zmianie kolejności lokalnych indeksów porównywać pola po dof-to-physical mapowaniu i fizyczne obserwable; nie wymagać identycznych bajtów macierzy o zmienionej numeracji.


## Wyniki nowych eksperymentów

### PRE-01-E01 — M0: tożsamość wejścia i źródeł (`PASS`, tylko preflight)

Owner: GPT-6.1 Sol high / `opt/preprocessing-20261029`, 2026-10-29.
Baza dokumentacji `ab4b3a6dbd`; kod solvera nietknięty. Nie jest to PASS PRE-01
ani całego M0: native preprocess, jego wydajność/topologia i nowy build NOT RUN.

- Pytanie: czy istniejący medium run jest odtwarzalnym wejściem i czy audytowany
  checkout ma te same compiler inputs, mimo odmiennego Git HEAD?
- Narzędzie: `tools/stage_preprocess.py` (stdlib), hash strumieniowy bez kopii mesh
  i bez GPU/Palace. Odrzuca drift config, mesh size/hash, unsupported mesh header,
  zmianę ścieżki i wyjście poza względny staging. Nie nadpisuje istniejącego raportu.
- Polecenie: `python tools/stage_preprocess.py /home/sieciowiec/dev/python/anteny/artifacts/tshaped/port-repair-20261028/rear-route-sma-only/run-local-stages-20261029 --output artifacts/optimization-stages/preprocessing/M0-E01/input-identity.json`.
- Testy: `python -m unittest discover -s tools/tests -p test_stage_preprocess.py -v`:
  6 PASS, 0,002 s. Same testy to kontrola preflight, nie natywnego FEM.
- Rzeczywisty preflight: 0,146 s w pierwszej próbie; 355110567 B mesh tylko odczytane
  do SHA, stały bufor, bez materializacji mesh/topologii w Pythonie. Wynik i test log
  w `artifacts/optimization-stages/preprocessing/M0-E01/` (nie wersjonować danych).
- Mesh: Gmsh2.2 ASCII; SHA `2af1b2ac9dfd0d785ac7e0a865f26eb2dac447ec9f90ea40d85056c5491452b3`.
- Actual config SHA `9f068760497b1d0223b3d0f1cf3f73c825e40de36b49359591e3f66b536c667f`.
  Oryginalny fixture config SHA `670097b47086e830c6f7435d76d4ea1163bed8a9ca75deab0e8f41406acfac10`;
  to celowa konfiguracja runu, nie błąd. **Actual MaxSize64, fixture MaxSize240**;
  porównanie musi zachować actual64. Order2, PA1, Tol1e-6, MaxIts1600.
- `tools/dev.py:source_hash()` obu compiler-input zbiorów równa się
  `a6ec732f11cc7fe920365ba2aae354b68fe97e81f732d5afd4659ed5187c3338`.
  Obejmuje root CMakeLists, palace/, cmake/, tools/adapter/, także niecommitowane pliki;
  nie obejmuje docs ani nowych narzędzi preflight. Runtime manifest Git47623adc nie
  oznacza driftu compiler inputs. Dowód `source-identity.json`; zgodność zależności,
  obrazu i fizycznie załadowanej binarki pozostaje po stronie koordynatora.
- Actual image `43ac46f6430cf44d7a2da0a618a0f5c67c6965cca2fde510f2a96116333e6d76`.
  Nie zastępować `runtime_base_id` z manifestu ani starym runtime.json.

### Deklaracje fixture i aktywne ścieżki źródłowe (audyt, nie natywna walidacja)

Model: `L0=0.001`, `Lc=300` w jednostkach config; brak jawnego Refinement.
Materiały 1..8: air1; ZYF2.94/.0016 (2,4); PTFE2.1/0 (3);
2.8/.02 (5), 3.2/.02 (6), ASAproxy2.73/.013 (7), 3/.03 (8).
PEC10, absorbing20/order2, lumped P1attr21/P2attr22, oba50Ω, +R,
excitation1/2. Są to deklaracje config, nie policzone inwentarze mesh.

Domyślne `config::ModelData` (`palace/utils/configfile.hpp:157-210`):
CleanUnusedElements=true, CrackBdrElements=true, AddBdrElements=true;
RemoveCurvature=false, MakeSimplex=false, MakeHex=false, ReorderElements=false,
ReorientTetMesh=false, serial/uniform refinement0. Nie wolno uznać crack/interface
ścieżki za nieaktywną tylko dlatego, że config ich nie wypisuje.
W M1 mierzyć `CheckMesh`/`AddInterfaceBdrElements` i `Mesh::Update`:
wrapper robi ExchangeFaceNbrData/BuildCeedAttributes/BuildCeedBdrAttributes
(`palace/fem/mesh.cpp:354+`), więc nie kończyć harnessu przed wrapperem.

### M0: żądanie krótkiego natywnego harnessu (`TODO_TO_CHECK`)

Istniejący `--dry-run` w main tylko parsuje config i sprawdza istnienie mesh;
nie uruchamia Load/Partition/Refine, więc nie zalicza preprocessing. Istniejące
Catch testy `TwoDimensionalDiagonalSquarePort`, `TetToHex`, `LocalEdgeSplit`,
`PeriodicGmsh`, `Default IOData` sprawdzają inne aspekty, nie pełny driver chain.
`mesh::ReadMesh` pomija solver Preprocess/nondimensionalization/refinement/wrapper;
nie jest równoważnym benchmarkiem całego driver preprocessing.

Propozycja minimalna dla koordynatora (wspólna własność driver/runner):
opt-in diagnostyczne zatrzymanie po bloku `palace/driver.cpp:59-79`, przed
`solver->SolveEstimateMarkRefine`. Zachowuje oryginalne `Load` →
`solver->Preprocess` → `Partition` → `RefineMesh` → konstrukcja Palace `Mesh`.
W trybie tym wypisać jednoznaczny `preprocess_only / solve_not_run`, fazy i
inwentarz elementów/atrybutów, wykonać poprawny cleanup. Brak flagi = ten sam flow.
Nie używać tego wyjścia jako ukończonego runu RF ani wpuszczać go do RF parsera.
Alternatywa: odrębny executable z tymi samymi publicznymi wywołaniami i init;
wymaga build glue koordynatora, bez nowego toolchain/dependency rebuild.

Do wykonania przez Lunę po implementacji i przydziale slotu: tiny coax 2mm na tym
samym backendzie/buildzie (≤120s), a następnie stały full mesh preprocess-only
(≤300s), bez solve/operatorów. Root musi zdefiniować rzeczywiste argv nowej flagi,
manifest źródeł i ograniczenia; nie zapisujemy wymyślonego polecenia jako działającego.
Strata aktywna; zgoda na zatrzymanie oczekuje. Żadnego native build/run nie wykonano.

Wznowić PRE-01-E01 tylko po zmianie wejść/manifestu/narzędzia; zwykły kolejny agent
odczytuje zapisany raport. Kolejna konieczna akcja: root M0 runtime/dependencies
qualification i minimalny native harness, potem PRE-01 profiling w M1.

### PRE-01-E02 — M0: opt-in driver harness (`IN_PROGRESS`, native NOT RUN)

Koordynator przekazał własność `palace/driver.cpp` dla tego kroku oraz zatwierdzenie
człowieka na zatrzymanie Straty; według jego kontroli usługa inactive/dead MainPID0,
RAM wolny78GiB, swap0. Ta gałąź nie zatrzymywała usług ani nie uruchamiała build/run.

Implementacja korzysta z nagłówka `utils/stageprobe.hpp`, którego właścicielem
jest root i którego nie tworzy ten worker. Umowa:
`StageProbe::{None,Preprocess,Operators}`, `RequestedStageProbe()`,
`StageProbeComplete{stage}`. Nie używać historycznego KrylovProfileComplete.

- `PALACE_STAGE_STOP=preprocess`: zachowuje oryginalny blok init/Load/Preprocess/
  Partition/Refine/konstrukcję `Mesh`, omija SolveEstimateMarkRefine.
- `PALACE_STAGE_STOP=operators`: tylko Driven, adaptive_tol<=0, max_it==0,
  single rank. Obsługuje wyłącznie StageProbeComplete{Operators} rzucone przez
  operator worker. Niespodziewane zakończenie lub brak stopu kończy się błędem.
- Wszystkie diagnostyki wymagają single MPI rank. Domyślny flow nadal wywołuje
  ten sam SolveEstimateMarkRefine, te same pamięci/timery i SaveMetadata.
- Diagnostyczny sidecar `postpro/stage-diagnostic.json` zawiera explicit
  diagnostic_only/complete, solve_executed=false, rf_result=false oraz liczniki
  mesh levels/atrybuty. Zapis używa istniejącego collective-safe WriteRootOutputFile
  przed Finalize, więc licznik IO i końcowe metadane pozostają spójne.
- Końcowy marker `PALACE_STAGE_DIAGNOSTIC: stage=preprocess complete=1
  solve_executed=0 rf_result=0` pojawia się dopiero po wspólnym Finalize/SaveMetadata.
  Sidecar nie zastępuje exit0 i finalnego markera. Nie tworzymy żadnego wyniku RF.
- `tools/stage_preprocess.py:check_diagnostic` sprawdza status/schema/mesh,
  pojedynczy końcowy marker, obecność timerów preprocessing i zero solve/FF/PC;
  preprocessing odrzuca jakiekolwiek CSV. Operators dopuszcza puste CSV/header-only
  z pierwszą kolumną `f (GHz)`, bo PostOperator jest tworzony przed assembly; każdy
  niepusty rekord danych (również same NULL) albo headerless dane są odrzucane.
  Caller nadal musi sprawdzić exit0 oraz manifest wejścia/builda.
- Rozszerzone Python testy: 13 PASS, około0,003s, bez native. Pokrywają config/mesh
  drift oraz brak markera, fałszywe bool/statusy, obecność solve mimo etykiety i stare
  CSV; ponadto operators header-only PASS, liczbowe/NULL rekordy i headerless
  dane FAIL. `clang-format` i diff-check PASS. Native compile/probe nadal NOT RUN.

Zmiana compiler inputs jest zamierzona: driver-only SHA teraz
`2b6bfa90f2846d2e2a0c3d66e294dbe84e2fef6463599b6362c2f08fcfc16039`
vs baseline `a6ec732f...c3338`; root header i operator hook jeszcze nie są
uwzględnione. `artifacts/optimization-stages/preprocessing/M0-E02/source-delta.json`.
Końcowy integrated source hash musi obliczyć koordynator po scaleniu.

Dokładne argv solvera po zbudowaniu i stagingu (cwd `/work`, config unchanged):

```sh
env PALACE_STAGE_STOP=preprocess /opt/palace-cudss/bin/palace-x86_64.bin config.json
```

Luna uruchamia je wyłącznie przez przygotowany przez root bounded runner:
tiny coax2mm timeout120s, następnie ten sam staged medium mesh timeout300s,
bez zmiany backendu/precyzji/mesh. Root musi propagować i zapisać nową flagę w
command.json oraz upewnić się, że standardowe runy ją czyszczą; obecny tools/dev.py
nie przekazuje automatycznie nowej zmiennej hosta do kontenera. Marker/sidecar
sprawdzić `check_diagnostic(postpro, stdout_log, stage='preprocess')`; nie wywoływać
RF checkerów na wyniku diagnostycznym.

Przed zaliczeniem: native kompilacja z root header i tiny default-control bez flagi;
tiny/medium preprocess-only; invalid stage i unsupported MPI fail visibly;
porównać domyślny tiny RF z baseline według zatwierdzonych bramek. Nie ma jeszcze
żadnego dowodu przyspieszenia i nie wolno przechodzić do M1 bez domknięcia M0.

### PRE-01-E03 — M0: bounded stage runner i gotowe plany (`PASS`, preparation only)

2026-10-30, ten sam worker/branch; wykonanie native nadal NOT RUN przez tego agenta.
Koordynator zgłosił gotowy build `build/optimization-stages-m0-20261030`, source
`131d5da3bf54eea5375ce41dfcf718aa9d2e466b8bf6a2abedcb60e152e2d8eb`.
Podczas zajętego przez I/O slotu tylko przygotowano pliki i testy mock/replay.
Nie tworzono/uruchamiano kontenerów, nie wykonywano kompilacji ani Palace.

Nowy `tools/stage_probe_run.py` reużywa dev.py (SHA, I/O, cgroup, pamięć),
stage_operator_reference (source/compiler fingerprint) i check_diagnostic.
Dwa jawne kroki CLI: `prepare` sprawdza/zapisuje plan, `execute` dopiero wykonuje.
Nie jest to osobna infrastruktura cloud ani standardowy runner produkcyjny RF.

Przygotowanie rzeczywiste potwierdziło: native SHA i compiler-input/source SHA
zgodne z nowym manifestem; image ID43ac dostępny lokalnie i przypięty w manifest;
CUDA driver `/usr/lib/libcuda.so.615.78.08` o SHA
`f73320931be3c4eabc120a1a7fea25f34f324c0f93e35891f98e81a722b5dfc3`
zgodny z root driver-injection/host-driver.json. Skontrolowano wyłącznie image
metadata, bez nowego testowego kontenera. Właściwe ładowanie bibliotek w nowym
native stage runie pozostaje do sprawdzenia przez wykonanie.

Plan wykonania posiada: image digest, manifest/native/helper/runner/source/config/
mesh/driver SHA, dokładny argv i env, timestamp UTC, osobny config i jawne zmiany
CPU Device/Backend. Mesh jest montowany read-only bez kopii: tiny istniejący2,1MB,
medium istniejący355110567B; root/source anten pozostają read-only. Native pliki
są montowane read-only pod faktyczne `/opt/palace-cudss/bin`, `/opt/palace-cudss/lib`
i `/opt/precision`; driver read-only na `/lib/libcuda.so.1`, dodatkowo CDI GPU.

Ochrona wykonania: host lock `build/optimization-stages-host.lock`, sprawdzenie
inactive/dead/MainPID0 Straty i procesów LLM, cgroup memory==memory-swap (zero swap),
sprawdzenie memory.swap.max==0, reserve8GiB/guard6GiB, network none, pull never,
core0. Twardy container timeout plus guard monitora, source/native/input recheck
przed/po. Nie ufa edytowanemu argv/env: wylicza kanoniczny command ponownie.
Po sukcesie lub błędzie usuwa tylko własny kontener; zapisuje diagnostic-result.json,
który zawsze ma rf_result=false. Brak automatycznego powtarzania istniejącego wyniku.
Błędy cleanup także odbierają complete i są zapisywane.

Gotowe plany (kanoniczny r2; wcześniejsze r1 zostały unieważnione zmianą hash helperów):
`/home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/M0-probes-prepared-r2-20261030/`:

| Podkatalog | Stop | Backend / OMP | Deadline | Cgroup |
|---|---|---|---|---|
| tiny-preprocess-cpu | preprocess | CPU / cpu/self /1 | 120s | 8GiB /2CPU |
| tiny-operators-cpu | operators | CPU / cpu/self /1 | 120s | 8GiB /2CPU |
| medium-preprocess-gpu | preprocess | oryginalny GPU backend /1 | 300s | 64GiB /8CPU |
| medium-operators-gpu | operators | oryginalny GPU backend /1 | 300s | 64GiB /8CPU |

Każdy ma `plan.json` i staged config. Średni run bazowy rzeczywiście wypisał
1 OpenMP thread (`palace.stdout.log:10`); brak jawnej zmiennej OMP w jego command
nie oznacza4 wątków — ConfigureOmp domyślnie wybiera1. GPU plany zachowują actual
numerics/config, w tym MaxSize64; mają jawny kontrolowany limit64GiB zamiast70GiB
referencji i OPENBLAS_NUM_THREADS=1, więc nie są A/B E2E z dawnym runem. CPU tiny
zmienia wyłącznie Solver.Device/Backend i MFEM_MEMORY w jawnej diagnostyce;
nie ponawiać znanej awarii OMP2 bez nowej hipotezy.

Po skopiowaniu identycznego runnera do root tools i uzyskaniu slotu, dokładne argv:

```sh
python tools/stage_probe_run.py execute /home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/M0-probes-prepared-r2-20261030/tiny-preprocess-cpu/plan.json
```

Następne tylko po analizie wyniku: analogicznie tiny-operators-cpu,
medium-preprocess-gpu, medium-operators-gpu. Nie wykonywać wszystkich ślepo w pętli.
Zmiana runner/helper/source/native/config wymaga nowego przygotowania; stare plany
mają fail-closed checksum i nie są automatycznie nadpisywane.

Testy: 7 nowych unittest PASS/0,008s: budżety/timeout/OMP1, no network/no swap/
read-only/CDI/core0, native drift przed Podmanem, edytowany argv/retry rejection,
LLM guard i mockowane low-memory/deadline z cleanup własnego kontenera i zapisanym
FAIL. Dodatkowo13 dotychczasowych preflight/output tests PASS. Py_compile i
Git diff-check PASS. Wyniki w kanonicznym katalogu r2/runner-tests.log;
preparation-audit.json rozróżnia PREPARED od NOT RUN. Bramka fizyczna i wydajność
nie zostały zaliczone przez samo przygotowanie.

### PRE-01-E04 — M0: pierwsze native tiny stage probes (`PASS`, CPU/OMP1 only)

2026-10-30: root przydzielił slot na dokładnie dwa tiny (preprocess, potem operators
wyłącznie po PASS pierwszego), deadline120s każdy. Medium nie uruchomiono.
Pierwsze uruchomienia harnessu nie weszły do Palace main i są zachowane:

- r2 exit125, 0,824s: kontener pozostał `created`, StartedAt0001/PID0. CDI hook nie
  mógł utworzyć libcuda.so.1, bo ręczny bind blokował ścieżkę symlinka. Usunięto
  zbędny bind; runner teraz sprawdza dokładny readonly mount host drivera w lokalnym
  CDI spec i jego SHA. Sam driver nadal ma sprawdzony hash, bez konfliktu z CDI.
- r3 exit127, 0,905s: `/usr/bin/env` nie załadował globalnego LD_PRELOAD adaptera
  (`undefined symbol: CEED_VECTOR_NONE`). Palace nie był execowany, stdout pusty.
  LD_PRELOAD przesunięto do argumentu env dotyczącego wyłącznie Palace; dodano
  regresję położenia argumentu. Dawne native_started=true w tym wyniku oznaczało
  tylko start entrypointu; `failure-classification.json` jawnie koryguje zakres.
  Obecny runner rozróżnia container_started od `palace_main_marker_seen`.

Obie poprawki mieszczą się w upoważnieniu root na rutynowy fix harnessu przed
wykonaniem native; nie zmieniono solvera, wejść ani zbudowanych binariów. Nie
powtarzano nieudanego wykonania Palace. r2/r3 mają SUPERSEDED i zachowane wyniki,
każdy następny plan w nowym katalogu, bez nadpisania/próby na starym output.

Kanoniczne artefakty:
`/home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/M0-probes-prepared-r4-20261030/`.
`tiny-qualification.json` wiąże źródło/native, fazy i cleanup obu wykonań.

| Case | E2E runner [s] | Palace Total [s] | MeshPreprocessing [s] | OperatorConstruction [s] |
|---|---:|---:|---:|---:|
| tiny-preprocess-cpu | 1,440244692 | 0,397669974 | 0,111074483 | 0 |
| tiny-operators-cpu | 1,394139857 | 0,551554674 | 0,110954472 | 0,077533825 |

To pojedyncze testy przerwania na etapach, nie sparowany benchmark ani speedup.
Initialization / DiskIO odpowiednio: 0,150915580 /0,086925294s oraz
0,229111146 /0,085603884s. Total ma także małe nieprzypisane narzuty startowe;
nie interpretować inclusive trace ani E2E jako kosztu pojedynczej funkcji.

Oba exit0, explicit diagnostic_only=true/solve_executed=false/rf_result=false,
końcowy marker po metadanych. Init count2, MeshPreprocessing count2; operators
count0 vs1; LinearSolve/PC/Coarse/FF/Setup count0. Żadnych CSV ani pozornych
S-parametrów; readback sidecarów/metadata/logów PASS. W obu mesh ma13086 elementów,
2450 boundary elements, 2835 vertices, attrs[1], bdr attrs[2,3,4].

Source SHA nadal `131d5da3bf54eea5375ce41dfcf718aa9d2e466b8bf6a2abedcb60e152e2d8eb`,
libpalace SHA `d1887e64cbd7a0045475b8f84b220f3b8d49666bb3edbf5503ae4987a9002f1b`,
image43ac i pozostałe native SHA zgodne z manifestem przed i po. CPU/OMP1,
MFEM_MEMORYhost, cgroup8GiB, memory-swap8GiB=zero dodatkowego swapu,
RLIMIT_CORE soft/hard0, siećnone, CDI. OOM=false, host reserve zachowany,
oba własne kontenery usunięte (container exists exit1); brak aktywnych Palace
kontenerów po wykonaniu. Zaobserwowane cgroup peaks około151MB, nie pełny profil
VRAM/pamięci anteny.

Nowe guard testy CDI i scoped preload: razem9 runner tests+13 preflight/output
=22 PASS/0,013s. Root runner/tests skopiowane z tego worktree po rutynowych fixach.
`runner-tests.log` w r4; compiler inputs nie zmieniły się (Python nie wymaga rebuild).
Przygotowano także r4 medium-* plany z nowymi hashami, ale **NOT RUN** i wymagają
nowego slotu koordynatora. To zamyka tiny część M0 harnessów, nie całe M0,
nie kwalifikuje RF/default flow ani medium GPU. Następna decyzja należy do root.

### PRE-01-E05 — M0: medium operators GPU z pełnym baseline env (`PASS`, diagnostic only)

2026-10-30, root zlecił wyłącznie jeden medium operators run; timeout300s,
64GiB/noSwap/8CPU/OMP1. Nie wykonywano osobnego medium preprocess ani żadnego
ponowienia. Kod native pozostał source131d/libd188. Runner poprawiono wyłącznie
w zakresie harnessu: GPU bierze pełne `command.json.environment` z tego samego
archiwalnego runu i zamraża hash command/env. Obecny archiwalny słownik ma18 kluczy
(22 efektywne po czterech jawnych dodatkach StageStop/OMP/OPENBLAS/LD_LIBRARY_PATH).
Każdy oryginalny klucz i wartość zachowane. Whitelist odrzuca nowe/missing klucze,
profiling/history oraz nieoczekiwany preload. CPU tiny nadal ma kontrolowany override.
LD_PRELOAD pozostaje argumentem env tylko dla Palace, nie środowiskiem helpera.

Baseline environment SHA:
`fdbfc42d3163baa7716aae5a93b247ac479664f4739dc108b5290d9f06809a3b`.
Zachowane m.in. CUDA_MANAGED/CUDSS_TRACK/native-complex-FP64 request,
HYPRE_DEVICE_POOL_MIB256, MEMORY_MARKS, FP32 basis/direct storage i reuse/defer/release.
Te flagi nie oznaczają, że uruchomiono coarse solver/GMRES — diagnostyka kończy się wcześniej.
Actual i staged config mają identyczne bajty/SHA
`9f068760497b1d0223b3d0f1cf3f73c825e40de36b49359591e3f66b536c667f`,
w tym endpoints/MaxSize64. Backend `/gpu/cuda/magma`, GPU/OMP1 potwierdzone stdout;
HYPRE pool268435456B marker również potwierdzony.

Dowody:
`/home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/M0-probes-prepared-r5-20261030/medium-operators-gpu/`
oraz nadrzędny `medium-qualification.json`. Source/native/command/config/mesh/driver/
CDI identity sprawdzone przed i po. Root runner/tests skopiowane z tego worktree;
nie zmieniono źródeł C++ ani binariów.

| Exclusive faza Palace | Czas [s] | Count |
|---|---:|---:|
| Initialization | 6,459404456 | 2 |
| Mesh Preprocessing | 27,748371953 | 2 |
| Operator Construction | 113,312344804 | 1 |
| Disk IO | 18,696631067 | 6 |
| Total | 166,272812518 | 1 |

Runner E2E167,685248504s. Setup/LinearSolve/Preconditioner/CoarseSolve/FarFields/
Postprocessing zero czasów i wywołań. Exit0/OOM=false; final marker i sidecar
complete=true, diagnostic_only=true, solve_executed=false/rf_result=false.
Postpro zawiera wyłącznie config_resolved.json, palace.json, stage-diagnostic.json;
żadnych CSV/pól/wyników RF. Mesh1700660 elements,510048 boundary elements,
402647 vertices; materiały1..8, bdr[10,20,21,22,30,35,41,48,55,56,65,72,75,83,150].

Dodano GPU samples do istniejącej telemetrii:323 próbek/323 poprawne odczyty.
Global GPU util mean0,126935%, median0%, max9%; global memory peak6276MiB.
Cgroup peak13657325568B (około12,72GiB), minimum wolnej pamięci hosta70965628928B.
Globalne GPU wartości obejmują też desktop i nie dowodzą fizycznej rezydencji UVM
tego procesu; nie sumować osobnych szczytów RAM/VRAM. N/A pozostaje null, nie zero.
Prawie zerowa sampled GPU activity wskazuje na potrzebę profilowania host-side
construction w M1; nie dowodzi konkretnej funkcji ani speedupu.

Guard Straty inactive/dead/PID0, memory==memory-swap64GiB oraz runtime swapmax0,
core soft/hard0, networknone/CDI, timeout300s, brak host-memory stop. Własny kontener
usunięty i container exists exit1; brak aktywnych Palace kontenerów po zakończeniu.

14 runner tests+13 preflight/output =27 PASS/0,019s. Nowe testy: pełne dziedziczenie
baseline flag, env/command hash drift i source drift, odrzucenie profiling/history,
CPU override oraz parsowanie GPU z N/A=null. Raw logs/plan/resource-policy/
container-state/telemetry i wynik zachowane; nie raportować przyspieszenia względem
825s pełnego solve. To kwalifikuje diagnostyczne wejście i zatrzymanie na tej siatce,
nie default RF flow ani M1 hotspot profile. Slot zwolniony; dalszy etap ustala root.
