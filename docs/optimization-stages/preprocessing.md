# Audyt i plan: preprocessing siatki

## Stan bieżący po kwalifikacji M3 — 2026-10-30

Bieżący wynik PRE-03: **kandydat opt-in zakwalifikowany w M3 dla jednego punktu 1,92 GHz**, domyślnie wyłączony.
`PALACE_SINGLE_RANK_DIRECT_MESH=1` dla jednej rangi, siatki conforming bez NURBS
oraz bez AMR pomija zbędny graf partycjonowania i round trip ASCII. Nadal wykonuje
`ParMesh` oraz `Finalize(true, false)` i zachowuje zakrzywione węzły. Pozostałe
konfiguracje korzystają z oryginalnej ścieżki z komunikatem fallback.

- Tiny CPU/OMP1: **55 986 asercji PASS**, zakrzywione tet/hex rzędu 2, topologia,
  atrybuty, węzły, orientacje, flagi, Jacobiany i działanie operatora ND.
- Jedna para medium preprocess-only: **53,361 → 46,025 s (−13,75%)**,
  cgroup peak **2 307 706 880 → 1 834 889 216 B (−20,49%)**.
- M3: trzy pełne pary, oba porty 1,92 GHz, **RF PASS**. Mediana czasu Palace
  **739,008 → 731,570 s (−1,006%)**; etap Mesh **28,121 → 21,375 s (−23,99%)**.
  Pełny peak cgroup prawie bez zmiany (**−0,066%**); nie przenosić zysku RAM
  preprocess-only na cały solve. Wszystkie 164 próbki E/B i 5012 kierunków FF
  na port przeszły bramki; normy pełnych pól objętościowych nie były mierzone.
  Jedna kontrola wymagała jawnego recovery monitora; są 3 pary natywnego czasu
  Palace, lecz tylko 2 czyste pary wall. To nie jest promocja globalnego defaultu.
- Pierwszy test miał jedną błędną asercję o flagach po uniform refinement.
  Oryginalne FAIL i logi zachowano w E02; zatwierdzona korekta kontraktu testu
  w E03 nie zmieniła kodu produktu ani progów numerycznych.

| ID | Stan i zakres |
|---|---|
| PRE-01 | PASS — profil M1/E08–E09, bez twierdzenia o zysku RF |
| PRE-02 | TODO_TO_CHECK — reorder nadal niebadany |
| PRE-03 | PASS tiny + preprocess-only + 3 pełne pary M3 przy 1,92 GHz; opt-in |
| PRE-04 | DEFERRED — bez dowodu bezpiecznej redukcji dalszych skanów |
| PRE-05 | DEFERRED do ścieżki IO-06; brak zmiany parsera w PRE |

Owner: agent preprocessing, branch `opt/preprocessing-20261029`.
Aktualny kod produktu: `palace/utils/geodata.cpp`; test:
`tools/stage_preprocess_partition_test.cpp`. Koordynator posiada wspólny plan,
checkpoint i integrację. Poniższe wcześniejsze plany i wyniki są historią prób;
aktualny stan określa ta sekcja, końcowe wyniki E03/E04 i wynik M3 poniżej.

## Granica fazy i dane bazowe

W logu Palace „Mesh Preprocessing” jest timerem wewnątrz „Initialization”, nie obejmuje generowania geometrii ani meshera zewnętrznego. `palace/driver.cpp:59-79` obejmuje w nadrzędnym `INIT` odczyt i przygotowanie siatki, `solver->Preprocess`, partycjonowanie, równomierne refinement oraz utworzenie obiektu `Mesh`. Sam timer `MESH_PREPROCESS` jest zakładany osobno w `geodata.cpp:130` (`Load`) i `:270` (`Partition`). Część dalszego przygotowania MFEM/FE może zostać przypisana do Initialization lub solverowego Setup; nie należy przypisywać całego INIT do tego milestone’u.

Historyczny pełny medium run sprzed M1 użył już wygenerowanej, stałej siatki; nie mierzył CAD ani generowania siatki. Wyniki: preprocessing 29,224 s (3,54% całości 825,783 s), operator construction 121,501 s lokalnie; na CMP operator construction 401,9 s. I/O Palace 19,612 s to osobna kategoria. Scope może być zagnieżdżony, ale BlockTimer przerywa naliczanie rodzica: końcowa tabela jest exclusive i jej kategorie można sumować w tym single-rank runie. Nie sumować natomiast inclusive wpisów phase trace. Initialization 6,768 s + Mesh Preprocessing 29,224 s daje 35,992 s przygotowania. Wówczas brakowało podziału wewnętrznego; aktualny profil M1 znajduje się w PRE-01-E08/E09, a pomiar kandydata w PRE-03-E04.

## Miejsca w kodzie do sprawdzenia

| Miejsce | Rola / fakt z kodu | Możliwy kierunek | Status |
|---|---|---|---|
| `palace/utils/geodata.cpp:130-264`, `Load` | Ładuje mesh; sprawdza typy i warunki AMR/periodic; opcjonalnie czyści nieużywane elementy, konwertuje typy, reorderyzuje elementy, finalizuje siatkę, robi region refinement i sprawdza granice/interfejsy. Część ścieżek jest warunkowa. | Najpierw rozbić czas na fazy i ranki, potem optymalizować tylko kosztowną ścieżkę faktycznie używaną przez antenę. | `PRE-01` PASS M1 |
| `palace/utils/geodata.cpp:267-369`, `Partition`; zwłaszcza `:314-367` | Wylicza partycjonowanie i rozdziela siatkę; ścieżka zależy m.in. od conformality, AMR i liczby rang. Przy niekonformalnym AMR są dodatkowe konwersje i broadcast porcjowany. | Odrębnie profilować 1 rank i MPI. Rozważyć zmianę tylko wtedy, gdy koszt partycjonowania/broadcastu istotny dla docelowej konfiguracji. | `PRE-03` PASS w zakresie tiny + jednej pary medium preprocess |
| `palace/utils/geodata.cpp:208-212`, `ReorderMeshElements`; implementacja `:2743+` | Istnieje opt-in `reorder_elements`, który zmienia kolejność elementów/węzłów dla lokalności cache. | Sparowany benchmark on/off może sprawdzić, czy preprocess kosztuje się późniejszym assembly, pamięcią i solverem. Wliczać koszt reordering do całego runu. | `PRE-02` TODO |
| `palace/utils/geodata.cpp:191-205, 2279+, 2375+` | `CleanMesh`, rozcinanie typów elementów i testy typu mesh występują w opcjonalnych ścieżkach; `CheckElements` bywa wywołane ponownie przez konwersję. | Szukać redundantnych przebiegów siatki dopiero po profilerze; bezpieczny mikrotest atrybutów/topologii może wskazać, czy jeden przebieg można współdzielić. | `PRE-04` DEFERRED |
| `palace/utils/geodata.cpp:2174-2215`; konwersje `meshio.cpp` | `LoadMesh` używa wbudowanego czytnika MFEM dla obsługiwanych formatów; COMSOL/Nastran przechodzą przez konwerter do strumienia Gmsh. | Badać parser/format tylko jeśli profil pokaże dominację odczytu lub konwersji. Nie wprowadzać mmap/cache formatu jako założonego rozwiązania. | `PRE-05` DEFERRED do IO-06 |

## Rejestr hipotez i prób

Każdy agent najpierw sprawdza poniższe ID. Dopisuje datę, commit/build/input hash, dokładne polecenie, wyniki, testy poprawności i decyzję. `TODO_TO_CHECK` oznacza hipotezę bez pomiaru; nie jest wynikiem. Po `PASS`/`REJECTED` nowy agent nie powtarza próby bez zmiany mesh, wersji MFEM, hardware, konfiguracji lub ujawnionego błędu.

### PRE-01 — historyczny plan profilowania (aktualnie PASS M1)

Hipoteza: 29,2 s ukrywa jedną lub dwie dominujące funkcje, więc ogólna optymalizacja całej fazy grozi pracą nad małym kosztem. Dodać tymczasowe/niskonarzutowe timery wokół istniejących bloków `Load` i `Partition`, a nie logować każdy element. Rozdzielić CPU time/wall time, rank oraz bajty wejścia; osobno oznaczyć koszt I/O. Najpierw krótki profil bez zmiany kodu, jeśli istniejący profiler i dokładne binary pozwalają rozdzielić te fazy.

Zaliczenie: fazy pokrywają się do tolerancji 2% z timerem nadrzędnym, MPI max-rank/wall jest jawny, brak zmian wejścia, topologii lub wyniku. Jeżeli preprocess <5% reprezentatywnego E2E i żaden subetap nie jest istotny przy oczekiwanej liczbie eksperymentów, oznaczyć dalszą optymalizację CPU-preprocess jako `DEFERRED`, nie sztucznie wymuszać speedup.

### PRE-02 — `reorder_elements` end-to-end (`TODO_TO_CHECK`)

Hipoteza: cache locality może obniżyć późniejsze operatory/solver, ale może się nie zwrócić przez koszt reordering albo już dobry ordering wejściowy. Porównać config on/off na identycznym medium mesh i buildzie; preprocess, operators, setup, solve, E2E i peak RAM raportować oddzielnie. Wyników samych operatorów nie używać do decyzji, jeśli reordering dodaje koszt.

Zaliczenie: topologia, materiały/atrybuty, boundary IDs, DOF dimensions i liczby elementów zachowane; rozwiązanie porównane przez normę pola / residuum / S-parametry w zatwierdzonych tolerancjach. Wariant promować tylko przy powtarzalnym E2E zysku ponad szum bez nieakceptowalnego wzrostu pamięci.

### PRE-03 — historyczne odroczenie przed profilem M1

Single-GPU nie oznacza automatycznie single MPI rank, ale brak osobnego pomiaru nie pozwala wnioskować o zysku z nowego partitionera. Najpierw zapisać `MPI size`, `OMP threads`, czas `GetMeshPartitioning`, dystrybucji i rozmiary per-rank. Wrócić do testu tylko dla faktycznej konfiguracji multi-rank albo gdy etap przekroczy 10% E2E. Zachować obecne ścieżki nonconforming AMR i chunked broadcast; nie upraszczać na podstawie konfigu anteny.

### PRE-04 — ograniczenie powtórnych skanów siatki (`DEFERRED`)

Hipoteza: opcjonalne clean/split/validation ścieżki mogą wykonywać wielokrotne globalne skany. Profil wywołań i konfiguracji ma wykazać, że dana para skanów wykonuje się w tym samym runie i koszt jest mierzalny. Dopiero potem prototypować współdzielenie już policzonych cech. Nie cache'ować bez jawnej reguły unieważnienia po modyfikacji/refinement; nie zmieniać walidacji dla przyspieszenia.

Zaliczenie: testy tetra/hex/prism/pyramid, curved/linear, conforming/nonconforming oraz region refine odpowiednie do zmienionej ścieżki; identyczne atrybuty i connectivity; brak regresji na MPI jeśli dotknięto partycjonowania.

### PRE-05 — parser/konwersja wejścia (`DEFERRED` do IO-06)

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

### PRE-01-E02 — M0: opt-in driver harness (`PASS` w M0; dalsze dowody E04/E05)

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

### PRE-01-E06 — M1: rozbicie preprocessing / parser (`PASS` zakres instrumentacji; final E08/E09)

2026-10-30, aktywny M1 po zamkniętym M0 (`febdc6eb9`). Hipoteza diagnostyczna:
18,6966s `DiskIO` przy operators-only może zawierać MFEM parsing/orientation,
ponieważ istniejący IO BlockTimer obejmuje całe `LoadMesh`, nie wyłącznie read syscalls.
To wniosek z zakresu kodu, nie zmierzony koszt parsera. Bieżący mesh to355MB Gmsh2.2
ASCII; ścieżka Comsol/Nastran dla niego nie wykonuje się.

Plan implementacji: niewielka liczba stałych host-inclusive scopes przez współdzielony
`StageProfile` z root-owned `utils/stageprofile.hpp`. Load/Partition/Refine,
cleanup/finalize/interfaces, LoadMesh native-read/MFEM constructor/conversion oraz
Palace Mesh::Update. Żadnych per-element logów, CUDA sync ani optymalizacji M2.
Zmienna/stream/vector ma zachować pierwotny zakres życia i kolejność operacji.

Runner otrzyma jawne `--stage-trace`; domyślnie brak PALACE_STAGE_TRACE i takie samo
baseline env. Tryb on dodaje wyłącznie PALACE_STAGE_TRACE=1, a flagę zapisuje plan
oraz kanoniczny argv/env fingerprint. Baseline whitelist nie będzie akceptować
profilowania odziedziczonego z archiwalnego command/env.

Testy przygotowania: domyślne/off vs explicit on, brak zmiany config/baseline env,
wykrycie driftu trace flag/argv i odrzucenie niejawnego trace w baseline. Następnie
root musi zbudować scalenie wszystkich trzech ścieżek, wykonać A/B narzutu, sparsować
scope tree i dopiero mierzyć medium. Ten worker nie posiada build/GPU/EM slotu.
M0 native source131d i artefakty pozostają zamrożonym odniesieniem; nowe compiler
inputs wymagają nowego manifestu/buildu. Szczegóły i wynik przygotowania poniżej.

#### PRE-01-E06 — wynik przygotowania

Gotowe lokalne patche: palace/utils/geodata.cpp, palace/fem/mesh.cpp,
tools/stage_probe_run.py i test_stage_probe_run.py. Root-owned stageprofile.hpp
jest tylko odczytany z głównego checkoutu, nie skopiowany/zmieniony w tej gałęzi.
Native build/run nadal NOT RUN; brak slotu. Nie zmieniono algorytmu, kolejności
operacji, solverów, konfiguracji ani lifetime istniejących mesh/stream/vector.

11 stałych nazw scope, najwyżej jedna para begin/end na wywołanie funkcji/bloku:

| Label | Zakres i ograniczenia interpretacji |
|---|---|
| preprocess.load | Całe Load, razem z zagnieżdżonymi scope; nie sumować inclusive z dziećmi |
| preprocess.load.clean | Istniejący CleanUnusedElements blok, wraz z przygotowaniem attr_list |
| preprocess.load.finalize | Istniejący Finalize(refine=true, fix_orientation=false) |
| preprocess.load.check_interfaces | CheckMesh i ewentualne AddInterfaceBdrElements, cały istniejący blok |
| preprocess.load_mesh | Całe LoadMesh, również EnsureNodes/remove curvature i ewentualne periodic |
| preprocess.load_mesh.convert | Wyłącznie istniejący Comsol/Nastran converter; w Gmsh oczekiwana nieobecność |
| preprocess.load_mesh.native_read | Zakres istniejącego ifstream (open, streaming parse, close), nie czysty czas dysku |
| preprocess.load_mesh.mfem_parse | MFEM Mesh constructor; includes stream reads, parsing/topology/orientation; ten sam label w rozłącznych ścieżkach |
| preprocess.partition | Całe Partition, bez zmiany MPI flow |
| preprocess.refine | Istniejący RefineMesh, również checki gdy uniform levels0 |
| mesh.update | Palace Mesh::Update: face-neighbor exchange i mapy atrybutów; także inne wywołania poza preprocessing identyfikować po rodzicu |

Nie rozdzielamy fizycznych read syscalls od parsera MFEM przez sztuczny kopiujący
preload pliku ani zmianę strumienia. native_read minus mfem_parse oznacza w przybliżeniu
pozostały open/close, nie disk vs CPU. Dokładny podział read syscalls wymaga
odrębnego lekkiego pomiaru systemowego. Domniemany koszt parsera18,7s pozostaje
hipotezą do sprawdzenia. W standardowej Gmsh ścieżce konwerter jest nieaktywny.

Dla pokrycia całego driver init root może dodać wspólny scope wokół
solver->Preprocess (units/nondimensionalization) oraz samego make_unique<Mesh>.
Ten worker mierzy Mesh::Update; jego caller EnsureNodes w inline konstruktorze
pozostaje poza tym scope. Nie edytowano shared driver.cpp.

Runner: `prepare --stage-trace` dodaje wyłącznie PALACE_STAGE_TRACE=1 i Boolean
stage_trace w planie/diagnostic-result. Bez flagi nie ma nowego env klucza, również
gdy host ma PALACE_STAGE_TRACE=1. Wartość musi być jawnym bool; inherited trace w
archiwalnym GPU env jest nadal odrzucany. Konfiguracja/baseline env/hash i scoped
LD_PRELOAD zachowane; zmiana trace flag po prepare unieważnia argv/env fingerprint.
Zmiana samego pliku runnera jak zawsze wymaga nowego planu, a stare wyniki historyczne
pozostają poprawnie związane ze swoim starym hashem. Runner kwalifikuje diagnostic
stop; root osobno waliduje coverage/pairing/narzut trace, nie uznaje samych markerów
za zaliczenie M1.

Testy stdlib: 18 runner+13 preflight/output=31 PASS; nowe cztery testy on/off,
host inheritance, config/hash preservation, flag drift i odrzucone baseline trace/
string value. Py_compile i diff-check PASS. Dowody testów w lokalnym
artifacts/optimization-stages/preprocessing/M1-E06/; nie są pomiarem wydajności.

Wniosek o run do koordynatora (nie wykonano): najpierw nowy cached build i zgodna
referencja native/source z wszystkimi trzema trackami. Sparowane tiny preprocess/
operators off/on z tą samą binarką, tym samym config/backendem i tą samą telemetrią,
limit120s każdy; bez reuse starych planów/hash. Potem jeden medium operators-only
trace ON na tej samej 355MB siatce, GPU/MAGMA/OMP1/baseline env, limit300s/64GiB,
z matching OFF control gdy potrzebny do narzutu/atrybucji. Przykład po wskazaniu
przez root faktycznie nowego M1 build-dir:

```sh
python tools/stage_probe_run.py prepare --source /home/sieciowiec/dev/cpp/palace --build <M1_BUILD_DIR> --run /home/sieciowiec/dev/python/anteny/artifacts/tshaped/port-repair-20261028/rear-route-sma-only/run-local-stages-20261029 --output <NOWY_KATALOG_TRIAL> --driver-record /home/sieciowiec/dev/cpp/palace/build/optimization-stages-m0-20261030/driver-injection/host-driver.json --stage operators --seconds 300 --memory-gib 64 --threads 1 --stage-trace
python tools/stage_probe_run.py execute <NOWY_KATALOG_TRIAL>/plan.json
```

To szablon oczekujący nowego manifestu M1, nie gotowy wykonany plan. Root/Luna
mają sprawdzić explicit noRF, counts, scope tree bez podwójnego liczenia i porównanie
narzutu (cel≤1%, rozliczenie timerów≤2% z wyjaśnionymi lukami). Jeśli trace narzuca
większy koszt, poprawić pomiar, nie optymalizować M2 na zniekształconym profilu.
Ponowić E06 dopiero po zmianie scope/helper/build/config albo błędzie coverage.

#### PRE-01-E07 — M1 native qualification OFF/ON (PASS wykonania; pokrycie domknięte E08)

2026-10-30 root granted sole native slot: tiny operators CPU OMP1 OFF/ON (120s/8GiB), then medium operators GPU OFF/ON (300s/64GiB), total series <=900s. No solve/RF. Integrated build optimization-stages-m1-20261030 source3bae7f768d18d24545c110e0f8bf8d46e7467cbb5ce07879ba37da014a2eb2c3, lib30747059009a6f0cc3c52b4662d7a67d255f4b4c678667faf340608d37435714. Fresh root runner plans; same fixture/config/env, only trace flag differs within pair. Driver record from M0 remains current and is revalidated. Parent stage_profile_report.py must parse balanced nested trace and explicit noRF before medium. Gate reports after tiny pair and medium OFF. Preserve raw logs/resources/CPU/GPU, no overhead PASS from single noisy pair, no speedup comparison with old M0 or full solve. No M2 optimization or build. Artifact series /home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/M1-profile-pair-20261030-r1. Native/source/helper drift aborts; native failure stops, no retries/reuse.

E07 tiny gate PASS: OFF/ON operatorsCPU exit0, noRF/solvefalse and cleanup; same identity/env except trace, OFF0 events, ON43 balanced scope instances/31 labels. Root parser PASS. PalaceTotal .545048991/.544669930s, Ops .071393207/.071069497, Mesh .110198897/.111016037, IO .085050200/.086109140. Hostcovered .331228909s. Single tiny noisy pair does not qualify overhead. Initial post-run analysis requested metadata.json (absent); corrected read-only reader to actual palace.json; no native failures/retries. Parent received required gate; proceeding authorized mediumOFF.

E07 mediumOFF PASS: exit0 noRF/solvefalse/cleanup, 0trace events, Init2/Mesh2/Ops1/IO6 and allPC/solve/FF0; unchanged source3bae/lib307470/configall18baselineflagsOMP1. Runner169.540340s, PalaceTotal167.945280s, Mesh27.823336, Ops114.835746, IO18.717746, Init6.513597. 326 telemetry samples; cgrouppeak13,656,379,392B, hostmin71,169,466,368B, globalGPUpeak6276MiB/utilmean0.0859%/max13%. Parent received required mediumOFF gate; proceeding only authorized ON. Not an overhead/speedup verdict.

#### PRE-01-E07 — native qualification result (PASS diagnostic; M1 coverage INCOMPLETE)

Four authorized runs completed once each, no native failures/retries. MediumOFF/ON PalaceTotal167.945280197/168.560026030s (+0.3660%); runner169.540340034/169.921320517s. Ops114.835746092/115.034512038, Mesh27.823336404/28.279284321, IO18.717745522/18.636255203, Init6.513597196/6.554157306. TinyTotal .545048991/.544669930. One sequential pair is not statistical overhead PASS. Source3bae7f.../lib307470.../native/config/helper/environment identical within pair except trace; configMaxSize64 and18 original baseline flags retained.

Both medium exit0, stage operators complete, noRF/solvefalse, noCSV, Init2/Mesh2/Ops1/IO6, allPC/GMRES/FF0, same1,700,660elements/510,048boundary/402,647vertices/materials/boundaryattrs. ON65balanced completed scope instances,31labels,130events; root stage_profile_report parserPASS. Four own containers removed; podman ps has only unrelated rapidmaker-catalog-postgres, no active Palace. Series runner time342.282739s (<900s), no mediumpreprocess/fullsolve duplicate.

Measured PRE hotspots ON (host wall/process CPU seconds):

| Phase | Host wall | Process CPU |
|---|---:|---:|
| Partition |19.423675|19.380008|
| MFEM parsing/mesh constructor |18.635826|18.596096|
| Finalize |5.096528|5.085532|
| RefineMesh incl checks even refinement0 |4.746250|4.735897|
| CheckMesh/interfaces |3.722409|3.713563|
| Mesh::Update |1.484495|1.480933|

Loadinclusive27.491479 includes parse/finalize/interfaces; do not add it to children. PRE roots53.173554s vs legacy Init+Mesh+IO53.469697s: ~0.296143s outside PRE scopes (initialization/wrapper gaps). **IO18.636255 is almost fully MFEM constructor18.635826**, including streaming reads/topology/orientation/parsing. CPU18.596096 ~ wall18.635826 supports CPU-heavy work in that warm local run; it does not isolate physical disk/read syscalls.

Important M1 coverage deficit: all root scopes cover63.885281s/processCPU63.738402 of Total168.560026. Operators roots10.711727s vs legacyOps115.034512 (~104.322785s uncovered). Root timestamps isolate one104.295120816s gap between final root operators.ceed_finalize and operators.K; all other inter-root gaps <=0.000244s. Source brackets this in SweepUniform PostOperator construction beforeK; internal partial assembly logs terminate before remaining work. This is a location hypothesis, not attribution of algorithm. Parent notified; root/operator worker must add enclosing PostOperator/downstream assembly scopes before full M1 coverage PASS. No M2/unauthorized reruns done.

Memory/telemetry OFF/ON:326/327samples, cgrouppeak13,656,379,392/13,680,394,240B; hostavailable minimum71,169,466,368/71,274,016,768B; globalGPUpeak6276MiB both, utilmean0.0859/0.2936%, max13/27%, median0. SMclockmean1276.9/988.1MHz, median225, max2587/2595; desktop/global samples not process-specific residency. Process CPU summed only for instrumented ON roots, not full process/OFF. No swap/core/network,64GiB cgroup/8CPUquota/OMP1, same GPU/MAGMA/UVM env. Raw logs, telemetry, resource-policy, container-state, plans/identities, diagnostics and reports under ROOT/artifacts/optimization-stages/M1-profile-pair-20261030-r1; tiny-qualification.json/medium-off-qualification.json/medium-qualification.json are machine-readable. Slot returned. Two read-only analysis path typos (metadata.json vs palace.json, worktree relative artifact path vs ROOT path) were corrected without native retries or source changes.

#### PRE-01-E08 — M1 R2 PostOperator/GSLIB coverage (PASS)

Root grants exactR2build/source0341e50051ac29e585c3b211d73fd44e89beb1fb583280541bae743589e3372b/lib0546c1cf8855d26a656a9c5791a03bb3882201095104ac0a7b04436fc213fcf9. New evidence justifying repeat: seven enclosing/internal PostOperator/GSLIB scopes added to account for104.3s uncovered inE07. Scope is measurement only, no M2 optimization. Authorized tinyCPUOMP1OFF/ON120s8GiB then single mediumGPUON300s64GiB/8CPUquota/OMP1 with18baselineflags; no mediumOFF/retry/sourcechanges. Beforemedium require tinybalancedtraceparser+true noRF/stop+cleanup. Target explain phasecoverage discrepancy<=2%, not claim speedup orR2formaloverhead fromdifferentbuild. Artifactseries ROOT/artifacts/optimization-stages/M1-profile-coverage-r2-20261030. PreserveallCPU/GPU/wall/provenance logs, strictguard/noSwap/core0.

E08 tiny gate PASS: OFF/ON source0341/lib0546/identity/config/envtraceonly; both exit0/operatorsstop/noRF/noCSV/allsolvePCFF0/cleanup. OFF0events, ON48balancedinstances36labels, parserPASS; fivePostscopepresent, GSLIBabsent on tinyconfig. PalaceTotal .535895469/.542917498s; Ops .071118522/.071730752s, PostconstructorON .020629972s/domain .020410252s. Not formal overhead qualification. Parent notified; proceed only singlemediumON300s64GiB.

#### PRE-01-E08 — result (PASS native diagnostics and measured coverage)

Three exactauthorizedR2runs completed once each; no retries/native failures. MediumONrunner170.402894284s, PalaceTotal169.044521576s. TimerIO18.752758415, Init6.561784830, Mesh28.525818083, Ops115.148940169. Source0341e500.../lib0546c1cf... strictmanifest/native/config/helperunchanged before/after; mediumconfig+all18flags unchanged fromR1, onlyinstrumentationbuilddifferent. No newR2mediumOFF; do NOT compare speedup acrossbuilds or callformaloverhead<=1%PASS.

ON72balancedcompletedinstances/38labels/144events, rootreportparserPASS. Coveredhost168.712082479s andinstrumentedCPU168.329686s. PREroots53.590374452 vsTimerInit+Mesh+IO53.840361328 (~.249987s initializationgaps); operatorroots115.121708027 vsTimerOps115.148940169 (gap .027232142s = .0236495%, below2%coveragegoal). Totaluncovered .332439097s (.197%); largestbetweenrootgap .00021122s. E07missing104s explained bynewscope, no unaccountedlargeinterval.

Measured exclusiveleaf wall/processCPU (seconds):

| Leaf | Wall | CPU |
|---|---:|---:|
| operators.probes.gslib_setup |104.519725928|104.314396|
| preprocess.partition |19.506679205|19.463181|
| preprocess.load_mesh.mfem_parse |18.752279465|18.709451|
| preprocess.load.finalize |5.223341047|5.179823|
| preprocess.refine |4.780144694|4.769649|
| preprocess.load.check_interfaces |3.759346155|3.750903|
| operators.materials |3.318622171|3.311881|
| operators.restrictions_suboperators (18) |3.052589917|3.044697|
| operators.hierarchy.nd |2.080273477|2.075026|
| mesh.update |1.488234747|1.484870|
| operators.probes.find_points |.001888219|.001884|

Postconstructorinclusive107.369961658s includesdomain2.843812663 andinterpolator104.521777787 (includesGSLIBsetup104.519725928+FindPoints.001888219). Do notsumparentswithchildren. GeometricGSLIBSetup is61.83%ofentiretruncateddiagnostic/~90.77%ofOperatorConstruction; measuredCPU~wall supportsCPUheavySetup, notslowGPUorCSV/diskwrite. ExactalgorithmwithinMFEM/GSLIB stillresearchTODO, notoptimized. ParentownsnextM2gate; no changetoprobes/materials/precision/solveflowinthistrial. Parsing18.75228vsIO18.75276againshowslegacyIOcontainsMFEMconstructor.

NoRF/resultfalse, solveexecutedfalse, exit0, Init2/Mesh2/Ops1/IO6, allPC/GMRES/FF/setup0, noCSV, same1,700,660mesh/510,048boundary/402,647vertices+attrs. Cgrouppeak13,675,798,528B, hostavailablemin71,391,223,808B,328samples. GlobalGPUpeak6276MiB,utilmean.07012%/max4%/median0,SMclockmean1249.48/median225/max2587MHz; globaldesktopinclusive, notperprocessUVMresidency. All3owncontainersremoved; onlyunrelatedrapidmakerpostgresremains. NoSwap/core0/networknone/64GiB/8CPUquota/OMP1,driver/Strata0guardrevalidated.

Evidence ROOT/artifacts/optimization-stages/M1-profile-coverage-r2-20261030/{tiny-qualification.json,medium-qualification.json,medium-phase-wall-cpu.csv}; eachcase rawstdout/stderr/telemetry/resourcepolicy/containerstate/noRFsidecar+identity/config andONstage-profile.json preserved. Necessarytinygateandfinalcoverage/GSLIBfinding sentparent. Slotreturned; waitingM2authorization.

#### PRE-01-E09 — M1 R2 mediumOFF control (PASS dla obserwowanej jednej pary)

Root authorizes exactlyoneadditionalmediumOFF300s/64GiB/noSwap/OMP1/8CPUquota, source0341/lib0546 sameR2build/config/all18flags asE08ON. Newbasis: unresolvedM1.2overhead ofsevenR2markers, r1pair notsamebuild. Compare previousR2ON169.044521576s tothisOFF (sequentialONthenOFF), noanotherON/retry/probe/sourcechange. Sameexistingguards/driver/pinnedimage andrawtelemetry. Target observedpairdelta<=1%; noise>1% isINCONCLUSIVE/no retries, notnewrequirements. Onepair neverstatisticaloverheadproof orRFqualification. Newoutput ROOT/artifacts/optimization-stages/M1-profile-coverage-r2-20261030/medium-operators-gpu-off-control.

#### PRE-01-E09 — result (PASS observed single-pair target; not statistical proof)

AuthorizedadditionalR2OFF completed once, exit0/noRF/solvefalse/samemesh/Init2Mesh2Ops1IO6/allPCGMRESFF0/noCSV, noPALACE_STAGE_PROFILEevents, native/source0341/lib0546/config/all18flags strictsame aspriorONexcepttrace. Runner170.396110977s, PalaceTotal168.979466720s; priorON169.044521576s => ONminusOFF .065054856s = +.0384987%, observedwholetruncatedrun target<=1% met. PairorderONthenOFF; noanotherON/OFFretry.

| Timer | R2ON | R2OFFcontrol | ONminusOFF % |
|---|---:|---:|---:|
| Total |169.044521576|168.979466720|+.038499|
| Ops |115.148940169|115.673315484|-.453324|
| Mesh |28.525818083|28.085608754|+1.567384|
| IO |18.752758415|18.608975198|+.772655|
| Init |6.561784830|6.556392758|+.082241|

IndividualphaseMeshdifference>1%, whileOpsnegative, illustratessequentialrunnoise/cache/thermalcontext: thissinglepairisnotformal/statisticaloverheadproofnorevidenceofspeedup. Cachewarmstate notflushed, noOFFwholeprocessCPUclock; ONscopedCPUalreadyarchived. Samebackend/OMP1/GPU/cgroup/native/input, timestamps andtelemetryallowreview. RootdecidesfinalM1gatewiththishonestscope.

OFF328telemetrysamples,cgrouppeak13,676,187,648B,hostavailablemin71,128,174,592B,globalGPUpeak6276MiB/utilmean.088415%/median0/max9;powermean40.0935W;SMclockmean1263.55/median225/max2595MHz. PriorONmeanSM1249.48/median225/max2587,desktop/global notprocessresidency. GuardStratainactive/deadPID0/noSwap/core0/networknone64GiB8CPUquotaOMP1. Owncontainerremoved; podmanpsonlyunrelatedrapidmakerpostgres. NoactivePalace;slotreturned.

Evidence ROOT/artifacts/optimization-stages/M1-profile-coverage-r2-20261030/r2-medium-on-off-comparison.json plusnewmedium-operators-gpu-off-control/{plan,diagnostic-result,resource-policy,container-state}.json +rawlogs/telemetry/postpro; priorONuntouched. NoRFsolve/M2/sourcechange/retries.

### PRE-03-E01 — M2 one-rank mesh distribution audit/prototype (przygotowano; E03/E04 PASS)

Reopened afterM1 source+measurement: Partition19.506679wall/19.463181CPU evenrank1. ExistingpathGetMeshPartitioning callsMFEMGeneratePartitioning(1): noMETISsolver, but ElementToElementTable executesbeforeonepartbranch. ThenDistributeMesh always MeshPartitioner→ExtractPart→MeshPart.Print ASCII→string→ParMeshistream evenrank1. MeshPartitioner also buildsedge/vertex/boundarytables. This data roundtrip is actual redundantrepresentationwork; timeinside19.5s notyetisolated, possiblegain boundedabove by19.5s (2.3%ofhistorical825sfullrun, ~11.5%of169sdiagnostic). No measuredspeedupyet.

Pinnedbuilder7d609652... highestviewlibmfem.so.4.9 resolvesnucrpyipn2tktie6vyzz2hakdcgklpd6, notlowerx5variant. Read-only source underoverlayc00cc97882f279a802968318daea16166e2e5fcd378e550860e624216b002042/diff/tmp/root/spack-stage/spack-stage-mfem-4.9.0-nucrpyipn2tktie6vyzz2hakdcgklpd6/spack-src. MFEMpmesh.cpp107-315 directParMesh(comm,Mesh&,partitioning)duplicateslocalvertices/elements/boundaries, attributes/names andcurvedNodes asParGridFunction, retainsgeometryspace/order. HoweverdirectctorhasnoFinalize; streamconstructor936-985 callsFinalize(refine=true,fix_orientation=false) +EnsureParNodes. Anydirectprototype MUST retainFinalize(true,false), notremovegeometryorder2/refinement/orientationwork. MeshPart.GetMesh aloneREJECTED: explicitNodesnotsetforcurvedmesh.

Plan narrow opt-in PALACE_SINGLE_RANK_DIRECT_MESH=1 onlyrank1/conforming/nonNURBS/allpartitionIDs0; othercasesfailvisiblyifrequested, defaultuntouched. No longlivedstate/cache; constructfromimmutablepostLoadmesh eachtime. Inputmesh/connectivity/coords/nodes/order/attributes/units/refinement/MPI/topologychanges alwaysreconstruct; no stale-cache reuse. PreserveFinalize(true,false), EnsureParNodes andsmeshresetlifetimeafterconstruction. Root-onlycompilerinputsuntouched, patchinchildtreeonly; noheavybuild/runtimepermissionyet.

Meaningfulnativeunitproposed: tinycurvedorder2tetandhex withdifferentdomain/boundaryattrs, comparelegacy/direct counts/connectivity/attrs/nodeFEC/order/values/quadratureJacobians/refinementflags+NDspaces; testagainafteruniformrefinement. MPI>1,NC,AMR,NURBS/prism/pyramid/periodic NOTRUN/notpromoted. Tiny<120s8GiBCPUOMP1; noEMsolve. Rootbuildrequest onlyPalacegeodata TU+smalltest, noMFEMrebuild, thenrunexistingCatchoperatorinitmain withnewstage_preprocess test linked. No mediumuntiltinycorrectnessPASS, parentreview andresource slot.

#### PRE-03-E01 — source audit and bounded prototype ready (native NOT RUN)

Parentapprovedonenarrowhypothesis: skiponepartdualgraphpreparationANDASCIIroundtrip usingexistingMFEMAPI. Patchchildonly palace/utils/geodata.cpp: envPALACE_SINGLE_RANK_DIRECT_MESH exact0/1,defaultoff. Eligible1rankconformingnonNURBS/noAMR; otherwiseoriginalpathplusfallbackreport (supersedesinitialdraftfailunsupportedproposalabove). Emptycustompartitionpathaloneallowsvalue-initializedall0vectorbeforeGeneratePartitioning; explicitpartitionfilealwaysgoesexistingreaderandallIDs0validatedbeforeanydirectconstruction. No bypassfilevalidation. OriginalMPI/nonconformal/NURBS/AMR flowunchanged.

ExistingdirectParMesh→Finalize(true,false) retained; DoNodeReorder keepssameNodesobject/FESpace, updatesvaluesunderMFEMownership. EnsureParNodes isprotected(pmesh.hpp324), soDONOTcallitfromPalace: directconstructoralreadycreatesParGridFunction+ParFiniteElementSpace; prototypeverifiesbothafterFinalize. This matchesEnsureParNodes'no-opcondition (pmesh.cpp2030ff), no manuallyrewirednodes. Serialmeshresetafterpmeshconstruction+finalization, sameeffectiveownershiplifetimeasstreamreturn. No cachestate, nosignaturesreused.

PinnedsourceSHA256 mesh.cpp c939f52988ec9243854ef5eed52de132fba27f738196e83be964f3591f89a262; pmesh.cpp5d4f041b7e952a1df803dc436e97d34e6537fa467751b1ede20e7beafba04a26; pmesh.hpp0e6ce0b6aa97d6f4685bed3f662be912678076bd331243e2297a654ee6966f3f. GeneratePartitioning(1)METISskipconfirmed butadjacencybeforebranch. MeshPart.GetMeshrejectedforNodes. NoMFEMsource/binarychanged.

Newtools/stage_preprocess_partition_test.cpp usesexistingCatchmain+dependencies, no newframework. Curvedquadratic2x2x2tetANDhex, variablematerial1/2 andboundary21/22attrs, exactdefaultExtract/Print/reparse vsdirectthroughpublicPartition. Assertions:counts/connectivity,attributevectors, allnodalcoords/FEC/order2/ordering,ParGridFunction,orientationchecks,tetrefinementflags, quadraturephysicalcoords/Jacobianweights, NDtrueDOFdims ANDindependentlyassembledcurlcurl+massoperatoractionrelative1e-12. Repeatedafteroneuniformrefinement. LazyElementToElementTablequeriedandcomparedafterbothpaths, checkingnoimplicitdependencyonthedroppedGeneratePartitioningcache. CPUOMP1/noEMsolve; nativecompile/testNOTRUN pendingrootslot. DiffcheckPASS/sourceAPIreviewonly.

Proposedexactboundedruntimeonceparentbuildstestexe: env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MFEM_MEMORY=host timeout -k 3 120 /stage/test/preprocess-partition-tests '[stage_preprocess][Serial]' --device cpu --backend /cpu/self. Useexistingstage_operator_unit_main.cpp withnewtestsource, cachedM0Catch2/lib and exactcachedCXX/linkflagsfromM0build-script.py117-127; compileonlynewtest+geodata TU, freshmanifest/nativepaths. 8GiBcgroup/noSwap/core0/hostguard/soleCPUslot. Buildtimeoutnewtest<=180s(link<=60), notrequesteddependencyrebuild. Rootprepare runnerintegrationfornewenv onlyafterreview; currentstrictstage_probe_runwhitelist intentionallyuntouched. MediumdiagnosticonlyifthisstructuraltestPASS+review+slot. FullRF/power/complexScomparisonlaterbeforeanypromotion. MPI>1/NC/AMR/NURBS/prism/pyramid/periodic unsupportedcoverageNOTRUN; defaultunchangedandunsupportedopt-infallbackoriginal.

PRE-04Finalize/PrintMeshInfo/repeatedtopologyscans remainDEFERRED: current4.78sRefine includesboundingbox/PrintMeshInfoevenuniform0, butnoinnerprofileisolatescostandgeometry/topologychangesinvalidatecasualreuse. DoNOTskipFinalize/refinementmarks/geometrychecksforpaperdesignortradeRFqualityforseconds. ParenttoauthorizeM2nativequalification; nocloud/services/build/nativeexecutiondonebythisaudit.

#### PRE-03-E02 — M2 cached build + native tiny gate (FAIL asercji; historia zachowana)

Rootgrantedchildbranchbuild/testslotonly. ArtifactROOT/build/optimization-stages-m2-preprocessing-20261030, baseM1r2source0341/lib0546cache; verifyactorcompilercontentdiffexactlygeodata.cpp, alignunchangedmtimesusingrootstage_align_mtimes.py(recordallmetadataadjustments). Preservechangedgeodatafreshanddonotfakeheaders. Sharedhostlock /run/user/UID/optimization-stages-host.lock pluslegacylock; sourceactorRO/rootccacheRW, noROOTcompilerinputedits. Limitsbuild32GiBnoSwap/core0/jobs2/600s/<=6PalaceTUs/noexternaldeps,total900s; actualnativeCPUtest8GiB/noSwap/core0/OMP1/cpuself120s. FreshCatchmain+newstage_preprocess_partition_test twoTUs, exactcachedCXX/linkflags/CatchCDIhostdriverSHA, unchangedadapter. NativefailSTOP/no loosening; no medium/EM/paidcompute. Source+diff+flags/nativebeforeafter+cleanup evidence required.

#### PRE-03-E02 — result FAIL, stopped (no retry)

Cachedbuild succeeded:only3TUs geodata.cpp + generatedjsonschema.cpp/main.cpp (worktreeGittag/schema stamp), noexternaldependencyrebuild. Alignedmetadataforunchangedinputs; reportchangedcontentexactlygeodata.cpp. Source02ddf3af26ca44b8949ad2c4cd737cbd9fbc7b4a2ae9a66a4401a70011b3cbab,lib493df76aeec5ddb4c76329999e95a6ba9f85567823b2a885d43f8f4c565a2739,bin225e3cfb5ea90323110ca260b02baf5725b4c38dd493de50c6cc5c0fe7cbfb8e,adapter3f25unchanged. Fresh2TUtestcompile/linksuccessful; nooldtestbinaryreuse.

ActualCPUOMP1native0.614424s exit42:29826assertions,29825PASS/1FAIL. Failureatnewtestline57:unconditionalCheckRefinementFlags(actual)==true. **All per-tet actual-vs-baseline refinement flag equalities passed**, all nodal/attrs/connectivity/orientation/physicalquadrature/Jacobian/NDoperatoractionchecks also passed, includingafteruniformrefinement. Thereforethisfailuredoesnotshowdirect/baselinegeometrydivergence; likelytestinvariantincorrectafteruniformrefinement. NeverthelessgateFAILretainedandstopped, no changingassertion/threshold/rerunwithoutrootreview.

Source-onlydiagnosis:MFEMUniformRefinement3D_basemesh.cpp10125ff constructsnewTetrahedra with default0refinementflags (tetrahedron.hpp45-56/defaultInitref_flag0); PalaceRefineMeshcomments explicitlyrequireFinalizeafteruniformrefinementonlyforlocalAMR. Sinceallper-tetflagsequalandactualCheckfalse, baselineCheckmustalsofalseforsamestate. Proposedreview:requirebothfullymarkedbeforeuniformrefinement, assertflagconditionequalityafterit, optionallyexplicitFinalizeboththentestagain. Thiswouldcorrecttestcontract, notloosenprecision; notappliedyet. ParentreceivednecessaryFAILdecisionreportandartifactpaths.

Totalbuild/testorchestration19.197086s; ownbuilder/runtimebothstoppedinfinally, onlyunrelatedrapidmakerpostgresactive, globalslotreleased. No medium/EM/native-retry. Artifactfailure-analysis.json recordsactualcounts/sourcefacts; originalpreprocess-unit-results.jsonpassed=false,logs/rawfailureunchanged. LimitsnoSwap/core0/networknone,build32GiB2CPU/testing8GiB2CPUOMP1,driver/CDI/inferenceguardvalid; allsource/nativeprovenanceanddirtydiffpreserved. Awaitrootdecision.

#### PRE-03-E03 — approved test-contract correction + one fresh unit run (PASS)

Rootreviewexplicitlyapproves correctingreferenceassumption afterUniformRefinement: helpercompares actual/base CheckRefinementFlags withCAPTURE+recordstage; initialbothrequirevalid; preserveallper-tetexactflags,geometry/node/NDactionassertionsandthresholds. Addthirdstate:explicitFinalize(true,false)BOTH,requirebothvalidandcompareentiregeometry/actionagain. Productgeodata/librarysource02dd/native493dunchanged; test-onlycompileoneTU+link<=60s,CPUOMP1sameCDI/8GiB/noSwap/core0/120s. OriginalE02FAILhistoryretained, newartifactattempt-r2; oneauthorizedexecution,no medium.

#### PRE-03-E03 — result PASS (tiny CPU/OMP1 structural gate only)

Approvedtest-onlycorrectionexecutedonce; productsource02ddf3af.../library493df76a.../adapter/binUNCHANGED,noPalacerebuild. Freshone-test-TUcompile+link withsamecachedflags/main/Catch. Newtestsourcebc299ce9b3e94a7f5029b98c945199355a01f5e3c0de5f39874b4aed3f4541d5,exe43a5f1077a0eaaa8fd13ebb64ccc7478ccc906fe6d19560495ec04c2aaa3d420. CPUOMP1exit0,55,986assertionsPASS/oneCatchcasewithtet+hexgenerator; nativecommand .714680s,totalorchestration8.747032s. Alloldper-tetflags/nodes/connectivity/attributes/orientation/Jacobian/NDactionchecksretained; numericthresholdsunchanged. AdditionalfullcomparisonafterexplicitFinalizeboth strengthenscoverage.

Flagrecords(tet): partitioned baseline1/direct1; uniform_refined baseline0/direct0; refinalized baseline1/direct1. Hexallthreestates1/1. ConfirmsoriginalE02failurewasincorrecttestexpectationafterMFEMuniformtetrefinement, notobservedproductdivergence. E02originalFAIL/log/binarykeptunchanged; E03PASSspecifictotestcontractfixandtinystructuralchecks,noRF/medium/speedupclaim.

Runtimeinspectproves8GiBMemory==MemorySwap(noextraswap),coreulimit0; sameCPUOMP1/cpuself/CDI/driver/inferenceguard; freshunitlddloads/stage/native/libpalace.so. Ownbuilder/runtimebothstopped, onlyunrelatedrapidmakerpostgresactive; sharedslotreturned. Root/build/.../attempt-r2/{inputs,inputs-after,compile-flag-proof,results,cdi-proof,inference-guard}.json +testsource/rawcompiler/runtime/testlogsandflagrecords. No furthernative/mediumauthorized untilparentreview.

#### PRE-03-E04 — authorized medium preprocess-only OFF/ON (PASS jednej pary)

Rootpreparedexactplans ROOT/artifacts/optimization-stages/M2-PRE03-20261030/{baseline-medium,direct-medium}/plan.json andgrantedsoleexecution slot. Childsource02dd/lib493d notmerged; rootrunneronly(feature+globalhostlock current),180s64GiB/noSwap/core0/OMP1/CDIeach,original355MBmesh/config/all18flags,traceOFF. Sequentialbaseline0thendirect1onlyiffirstPASS; nooperators/GSLIB/GMRES/RF. Guards/source/native/helperfrozen,no codechanges. Comparetruefastpathmarker/no fallback,metadata/counts/attrs/order andtimers/resources. Warmcacheonepair,nothreemedianorfullRFpromotion; nativefailSTOP/no retry. TinyE03structural55,986PASSscope alreadyreviewed.

#### PRE-03-E04 — result PASS medium diagnostic, candidate not globally promoted

Exactrootpreparedtwoattemptsexecutedonceeach, baselinefeature0thendirect1,source02ddf3af/lib493df76a/bin225e3/adapter3f25unchangedbybefore/afterhashguard. Bothstagepreprocess exit0/noRF/solvefalse/noCSV, Init2/Mesh2/IO5/Ops0/allGMRES/PC/FF0, owncontainersremoved; onlyunrelatedrapidmakerpostgresactive. Sameoriginalmesh/config/all18baselineflags/backend/OMP1, exceptdirect0vs1; bothtraceOFF. Explicitactualdirectmarker1 ranks1/ascii_round_trip0, nofallback; baselinefastpathmarker0.

| Timer | Baseline0 s | Direct1 s | Delta s | Delta % |
|---|---:|---:|---:|---:|
| PalaceTotal |53.360878837|46.025047751|-7.335831086|-13.747583|
| MeshPreprocessing |27.769618768|21.104537609|-6.665081159|-24.001342|
| DiskIO |18.739782245|18.471197705|-.268584540|-1.433232|
| Init |6.795602429|6.393504432|-.402097997|-5.917032|
| Runner incl checks/cleanup |54.589635164|47.619604503|-6.970030661|diagnostic only|

Cgrouppeak2,307,706,880→1,834,889,216B (-472,817,664B,~20.49%); samples105/91,hostavailableminimum81,000,873,984/80,891,928,576B,globalGPUpeak2248MiBboth. GlobalGPUincludesdesktop/notprocessUVMresidency.64GiB/noextraswap/core0/8CPUquota/OMP1/CDI/driver/inactiveStrata guard same. LowVRAMherebecausepreprocessonly,notsolve.

Metadata sidecarcounts/attrs equal:1,700,660elements,510,048boundary,402,647vertices; materials1..8/boundaryIDs10,20,21,22,30,35,41,48,55,56,65,72,75,83,150. Printedcurvatureorder2both. **Mediumfullconnectivity/nodalarraysnotdumped**: equalmetadataisnotprooffullmeshbitidentity; tinyE03fullstructuralchecks55,986PASScovertet/hexquadraticgeometry+orientation/refinement+NDaction. FullRF/complexS/fieldsresidual,power/energyNOTRUN. ThisonewarmcachebaselineOFF→directONpairismeasuredpreprocessgain, notthree-mediansorfullsimulation/E2E13.7%speedup. MostobserveddeltaMesh(-6.665s)matcheseliminatingrepresentationroundtrip; innerPartitionnotisolatedbecausetraceOFF, do notattributeall19.5sorsavingsinIOtothisfeature.

Evidence ROOT/artifacts/optimization-stages/M2-PRE03-20261030/pair-result.json withallplans/identities/native/configenvchecks,rawlogs/telemetry/resourcepolicy/containerstates/noRFsidecars. Parentreceivednecessarypairreport. Nofurthernative/build/sourcechanges; slotreturned, awaitM3/M4review. Productcandidatecontinuesopt-inonly/defaultunchanged.

### Cross-track OP06 independent source review (read-only, 2026-10-30)

RootrequestedinspectiononlyduringactiveOPcontrol, nocompute/sourcechanges. Reviewedactorprobelocator.hpp/interpolator.cpp/.hpp/test-probelocator.cpp againstff97f08bc; snapshotSHA+notes ROOT/artifacts/optimization-stages/M2-OP06-independent-PRE-review-20261030/review.json. No blockingcandidatebugfound forrank1validtet/hex supportedH1/ND/RTscope. Strictinterior+forwardfinitecheck, boundedK128/deterministicties/wholebatchfallback,point-majorcomplexlayout,mesh+nodesequence/foreignfieldinvalidations anddefaultGSLIBpath reviewed. No164probe/outputsubset removal seen.

NOTRUNbyreviewer:runtime/build,actualCUDAdevice-residentProbeFieldvalues/HostReadmigration,MPI/AMR/NC/periodic/prism/pyramid/noGSLIB. CPUknown-reference/complex/layouttestsstrong; operators-onlytimingdoesnotexecuteProbeFieldsolvedGPUfields, soM3mustretainall164complexfield+S/residualcomparison (orboundedCUDAknownreference/replayfirst). MFEMdocumentsrawGetNodeswritesrequireNodesUpdated; sequencecachehonorsthatcontract, not silentrawmutations. Forwardresidualsanitythreshold isnotuniversalfield-errorbound onthinelements; no thresholdlooseningproposed. RootdecidesM3/fixesafterOPslot.

### PRE-03 — M2 handoff: docs-garden i przegląd przed commitem

Wykonano `.agents/skills/docs-garden/SKILL.md` w zakresie własnego diffu:
`geodata.cpp`, test i ten ledger; sprawdzono ARCHITECTURE/INDEX oraz powiązane
wyniki E02/E03/E04. Poprawiono nieaktualny nagłówek „aktywny M1 / native NOT RUN”,
statusy kolejki i jawnie oddzielono historyczne plany od wyników. Nie usunięto
pierwszego FAIL ani zatwierdzonej korekty kontraktu testu. Wspólne pliki planu,
indeksu i checkpointu należą do koordynatora i nie są zmieniane w tym commicie.

Review kodu: brak zmiany geometrii/precyzji; domyślny flow pozostaje oryginalny,
custom partition file nie jest pomijany, AMR/NC/MPI/NURBS mają fallback. Tiny
kontroluje dokładne flagi/węzły/topologię i działanie ND; jedna para medium daje
wynik preprocessingu, pełne RF nadal NOT RUN. Nie uruchamiano ponownie zakończonych
testów ani compute. Source hash nadal `02ddf3af26ca44b8949ad2c4cd737cbd9fbc7b4a2ae9a66a4401a70011b3cbab`,
lib `493df76aeec5ddb4c76329999e95a6ba9f85567823b2a885d43f8f4c565a2739`.
Docs check i `git diff --check` PASS; dalszy krok to dokładny plan M3 od root.

### M3 PRE / M5.2–M5.3 — przygotowanie tylko do odczytu (2026-10-30)

Podczas wyłącznego slotu OP nie uruchomiono MPI, buildu, Gmsh ani symulacji.
Raport: ROOT/artifacts/optimization-stages/M5-generalization-PRE-readonly-20261030/report.json.
Znaleziono medium M7.5: `artifacts/m7-director-gap-plus2-geometry-20261022/mesh/pcb.msh`,
336 693 277 B; SHA c66c6f55c8e28b3efe87bdc4eac373e65d69b71cb016454a2c92c7d4dbfaf8fb
zweryfikowany dla geometrii i własnej referencji. Sprawdzono SHA archiwum, configów
oraz metadane. Nie tworzono nowego mesh/fixture.

Własna stara referencja: `artifacts/m7-director-gap-plus2-reference-20261022`,
3,5 GHz / oba porty / K64 / order2 / tol1e-6; actual config SHA
628ae137148c5bb41ef349578ee3dc646a445e5e532e21561f48c331ff58669c.
Nominalny config fixture ma tylko P2/K240 — nie mylić go z actual reference.
Stara referencja fields identity 0fa6583e133556f370831769932813e2f4c493a01058a5f8a846fdc23d1184ff;
1 601 320 elementów / 11 218 724 ND DOF, zapisane pełne E/B obu portów.
Duże payloady pól sprawdzono rozmiarem i zachowanymi hashami manifestu, bez ich
ponownego pełnego hashowania. Historyczne FP64 764,008 s / 61,139 GB cgroup;
fixed3 755,874 s / 46,601 GB to inna polityka precyzji, nie wyniki PRE/OP.

**Brak probes i FF w starym actual config i wynikach.** Są S/I/V, energia,
power oraz E/B snapshots. Niezmieniony przypadek sprawdzi PRE, ale nie OP06/FF.
Root wybierze nowy derived config identyczny dla A/B, własną świeżą referencję,
znane punkty wewnętrzne po dokładnym mapowaniu P2 i jawny jednakowy FF/output audit.
Nie kopiować ślepo 164 punktów innej anteny i nie dobierać punktów dla speedupu.
Stary M7 stanowi provenance geometrii; nie jest oracle nowych outputów. Nowa
referencja unieważnia stare seedy/faktory. Limity wymagają nowego root planu;
historyczne koszty nie gwarantują czasu/RAM po dodaniu probes/FF.

MPI2: gotowa tania propozycja OP wykorzystuje aktualny cached rescue
`build/optimization-stages-m2-operators-rescue-20261030/test/probe-unit-tests`,
case `MFEM probe locator keeps GSLIB ownership at boundaries and outside`.
Ten case nie wymaga rank1; przy MPI2 gałąź mfem ma wrócić do całego GSLIB i
porównać wartości zespolone z oracle. Pełne argv / pinned image / matching native /
manifest i propozycja 120 s / CPU OMP1 / 8 GiB no-swap w raporcie i
`op-mpi2-command-proposed-NOTRUN.txt`. Launcher w obrazie potwierdzony jako OpenMPI5.0.10.
CDI wyłącznie dla ładowania zależności CUDA; payload `--device cpu --backend /cpu/self`.
**Polecenia nie wykonano.**

PRE MPI2 nie ma jeszcze gotowego zgodnego cached testu: bieżący case wymaga
size1, a StageStop jawnie zabrania MPI2. Najmniejsza poprawna bramka to nowy mały
case `[stage_preprocess][Parallel]` w istniejącym tiny harness: publiczne Partition,
root-only curved tet, opcja0/1, jawny fallbackoriginal, równe lokalne nodes/attrs/
topologia/ND action. Jeden test TU + link z cache, bez rebuild MFEM/produktu;
przygotowanie i wykonanie dopiero po slocie/root review. Nie uruchamiać OP testu
z biblioteką PRE493d — layout InterpolationOperator jest inny; potrzebny matching
native lub świeży combined test. PRE/OP full paired M3 i MPI2 nadal NOT RUN tutaj;
worker czeka na dokładny plan po zakończeniu slotu OP.

### PRE-03-M3-E01 — pełny medium, trzy sparowane runy (PASS w opisanym zakresie)

Rootpreregister ROOT/artifacts/optimization-stages/M3-PRE03-full-20261030/preregister.json;
soleGPUslot granted po OP. Exactplany:1A-off→1B-direct,2B-direct→2A-off,3A-off→3B-direct.
Po każdejparze root stage_rf_compare.py(A,B), FAIL/guard/OOM/deadline STOPbezretry.
Każdyfullrun1800s/68GiB/noSwap/core0/OMP1/8CPUquota/CDI/image43ac; source02dd/lib493d,
config9f/mesh2af/all18baselineflags,GSLIBdefaulti traceOFF. Różnicatylkodirect0/1.
Polecenia /usr/bin/python3 tools/stage_probe_run.py execute plan.json zROOT; nieedytować
aktywnychhelpers/sources. Bramka:raw<=1e-6,ΔcomplexS<=1e-5,ΔVSWR<=.001,
fieldsrelL2<=1e-5,power/FFflux<=.02. Rodzajmierzonegopola wgexactcheckeroutputmanifest,
nieudawaćbitwisezgodności. Raportkażdejpary+pełne3pairedmedian/minmaxWall/Palace/fazy/RAM;
brakzyskupełnegonieukrywać. ŻadnychinnychGPU/build/MPI/cloud/geometry/Strataakcji.

#### PRE-03-M3-E01 — pair1 PASS; pair2 monitoring end-race, STOP

Pair1 A→B zakończona, rootchecker pair1-rf.json PASS. Palace738.249863→731.226210s,
Mesh28.121020→21.375176s; wszystkie8CSV/probes164/FF10024rows, oba porty85iteracji.
MaxΔS3.4231e-8,ΔVSWR4.6609e-8; probepointL2max1.14384e-6,FFL2max2.542e-8,
powerresidualmax.00021545W,FFfluxmax1.2588%. Jedna para nie zastępuje trzech median.

Pair2-B-direct completePASS; pair2-A-off PythonrunnerFAIL po zniknięciu cgroup:
FileNotFoundError memory.swap.max, elapsed740.161669s. Oryginalny full-result.json
complete=false zachowany, SHA f543e23205ea0a64346d78c69483bd1dc9af9b3e473d570962d33bb88d3c0cd0.
Native ma końcowe timery739.008s/2solves85its i wszystkie8CSV. Na zlecenie root
zebrano ograniczone czasowo podman events dla dokładnego CID04180b54...:
**died ContainerExitCode=0**, timeNano1793355193146280025; remove także0.
Raw monitor-race-podman-events.jsonl SHA7c500a3b86ad60990d5717ad0e4fb054b0563e74cb3627bbf0057f8ed4505b03;
monitor-race-events-proof.json zapisany przy pair2-A-off. Terminalsession29566 exit1
należy do monitora Python, nie Palace. Brak retry/checkerpair2/edycjiresult/helpers;
cleanup potwierdzony, pair3 obaNOTRUN. Root naprawia race i decyduje o jawnej
niezależnej kwalifikacji istniejących wyników. Worker STOP/czeka; nie zaliczono
po cichu nieukończonego harness receipt jako PASS.

#### PRE-03-M3-E01 — jawny recovery root; para3r2 autoryzowana

Root niezależnie sprawdził supplemental completion-recovery.json dla pair2-A-off,
wiążący event nativeexit0/oryginalnyFAIL/plan/identity/pełneoutputy. Pair2-rf.json PASS;
oryginalny controller receipt nadalFAIL i wall tej próbki wyłączony z czystych statystyk.
Nie ponawiano compute. Użytkownik jawnie ponownie zezwolił StrataOFF/continue;
rootservice0. Monitorrootcommit1520a583e po niezależnymOPreview/91testach poprawia
race; planów starych pair3 NIEwykonujemy. Nowy preregister-pair3r2.json i dokładne
pair3r2-A-off→pair3r2-B-direct otrzymały soleGPUslot. Same PREsource02dd/lib493d,
physics/config9f/mesh2af/all18flags,68GiB/noSwap1800s/OMP1; różni się tylko wersja
monitora między parami (wewnątrz każdej pary taka sama). Po RFgate ostatniejpary
3nativepairedmedians dozwolone, lecz tylko2czyste wallpairs; brak udawania3wallmedian.
PierwszyFAILSTOP/no retry; bez edycji aktywnych helpers lub kodu produktu.

#### PRE-03-M3-E01 — wynik końcowy: 3 pary native + RF PASS

Zakończono dokładnie sześć autoryzowanych solve: pair1 A→B, pair2 B→A oraz
nowe pair3r2 A→B. Stare plany pair3-A/B pozostały NOT RUN. Każda para przeszła
root `stage_rf_compare.py`; bramki pozostały niezmienione. Pair2-A ma jawny
supplemental completion-recovery i native exit0 z eventów Podman; oryginalny
controller FAIL zachowany. Nie wykonywano ponownie tej symulacji.

| Miara | A off: mediana [min, max] | B direct: mediana [min, max] |
|---|---:|---:|
| Palace Total [s] |739,007857 [738,249863;744,922888]|731,570240 [731,226210;734,089966]|
| MeshPreprocessing [s] |28,121020 [27,873131;28,331267]|21,375176 [21,336886;21,735001]|
| OperatorConstruction [s] |120,513707 [120,058165;121,265227]|119,760551 [119,707518;119,783647]|
| Setup [s] |91,804289 [91,760155;92,576705]|91,768951 [91,721659;91,870776]|
| Peak cgroup [GB decimal] |70,608499 [70,566187;71,267557]|70,561608 [70,554399;70,928703]|

Native Total: różnica median **−7,437617 s / −1,00643%**. Sparowane B/A:
0,990486076 / 0,989935672 / 0,985457660 (mediana0,989935672).
Różnice czasu par:−7,023653 /−7,437617 /−10,832922s. Mesh zyskuje około6,5–6,7s
w każdej parze; mediana sparowanej różnicy−6,596267s. Zysk fazy jest wyraźny,
ale pełna symulacja poprawia się tylko około1%; brak dużego zysku full RAM:
różnica median−46,891MB/−0,06641%. Nie przypisywać całej zmienności innych faz
tej optymalizacji; aktualny default pozostaje off, połączenie z OP to osobna bramka.

Czysty wall ma **tylko 2 pary (pair1/pair3r2)**: A743,580718s [739,818623;747,342813],
B734,192078s [732,936400;735,447755], mediana różnicy−9,388641s/−1,26263%.
Pair2-A oryginalny wall740,161669s jest zachowany jako raw controller-failure sample,
ale nie wchodzi do czystych wall-statystyk ani twierdzenia o3 udanych wall parach.
Monitor/hash par1/2:303ea41b...; pair3r2:65c111d7..., jednak wewnątrz każdej pary
wersja taka sama. RF checker dla pair1 f2b2e275..., dla pair2/3 5c63ed2b...;
zmiana dodaje tylko jawne obsłużenie proof-recovery, a progi/normalizacja są równe.

RF maksima ze wszystkich3 par: ΔcomplexS3,423073e-8; ΔVSWR4,660876e-8;
L2 próbek E/B1,304300e-6; L2 complexFF2,541981e-8. Maksymalny raw residual
8,339296e-7<=1e-6. Power residual<=.000215467W; względny FF/flux<=.012587722
(1,2588%)<2%. Każdy solve miał2porty/85iteracji,164punkty E/B na port,
5012kierunków FF na port,10024wiersze FF i wszystkie8CSV. Nie są to wyniki
bitwise; pointwise faza słabych składowych ma osobne diagnostyki, a pełna norma
objętościowa pól nie była częścią tego runu.

Wszystkie6próbek mają identyczne: source02ddf3af.../lib493df76a.../adapter3f25...,
config9f.../mesh2af..., GPU CUDA/MAGMA/1MPI/OMP1/all18baselineflags; różni się
jedynie explicit direct0/1. TraceOFF, GSLIB original w obu wariantach,68GiB
Memory==MemorySwap/no dodatkowego swap/core0/8CPUquota/image43ac. Wszystkie
markery direct obecne tylkoB, fallback brak. Min hostavailable13,06GiB lubwięcej;
globalNVMLpeak15858–15868MiB obejmuje pulpit, nie traktować jako process UVM.
Source/native ponownie sprawdzono po zakończeniu. Wszystkie własne kontenery
usunięte; tylko unrelated rapidmakerpostgres działa. Slot GPU zwolniony; bez
innych native/build/MPI/cloud/Strata działań.

Raport odtwarzalny: ROOT/artifacts/optimization-stages/M3-PRE03-full-20261030/
`three-pair-summary.json`, `raw-six-samples.csv`, `summarize-pre03.py`, per-phase
med/min/max i sparowane ratios oraz wszystkie identity/policy/telemetry hashes.
Zachowano pair1-rf.json, pair2-rf.json, pair3r2-rf.json, raw logs i recovery/events.
M3 PRE zakończony w tym zakresie; generalizacja drugiej geometrii/MPI oraz
połączenie PRE+OP wymagają kolejnych jawnych planów root. Brak globalnej promocji.

#### M3 — docs-garden i lokalny handoff

Sprawdzono własny doc-only diff, ARCHITECTURE/INDEX i raport trzech par.
Aktualny skrót oddziela ~24% zysku Mesh od ~1% całego solve oraz płaskiego
full peak RAM. Zachowano controller FAIL, dowód native exit0, jawny recovery,
dwie wersje monitora i tylko dwie czyste wall pary. Nie zmieniono wymagań ani
historycznych artefaktów. Shared PLAN/INDEX/checkpoint pozostają własnością root.
Ponownie potwierdzono source02dd/lib493d; bez uruchamiania nowego compute.
Docs-garden check i diff-check PASS. Dalsze M4/M5 wykonuje wyłącznie koordynator
według nowego planu; ten worker zatrzymuje się po commicie dokumentacji.
