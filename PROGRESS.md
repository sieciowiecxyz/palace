# Postępy optymalizacji

Aktualizacja: 2026-10-19. Mode: goal, Active: M2. [PLAN](PLAN.md), [MILESTONES](MILESTONES.md), [raport M1](docs/optimization-baseline.md), [kontrola pól](docs/field-validation.md).

## Wymóg użytkownika

**Dane robocze solvera wyłącznie w RAM/VRAM.** Bez SSD/NVMe scratch, disk basis, out-of-core, plikowego mmap ani swap jako sposobu na zmieszczenie obliczeń. UVM może migrować GPU↔RAM. Nie zamykać aplikacji użytkownika. Cache kompilacji oraz zwykłe wejścia i wyniki pozostają osobną funkcją. Usunięto disk basis; legacy env są odrzucane przed inicjalizacją MPI/CUDA.

## Bieżący checkpoint

- M1 COMPLETE: referencja/normy/topologia/bieżącealokacje/krótkiprofil i końcowy normalpathPASS; M2ACTIVE. Goal pozostaje aktywny, bez promocji nowych defaultów.
- EXP18–19: W.3FP64nativecomplex kwalifikacja35iter/447,462sbezprofilera, raw8,36e−7, maxΔS6,70e−9/E-B9,89e−8 względemtight-r2. To3,50GHz/P2fixturemedium, nie najlepsza geometria produkcyjna. docs/native-complex-coarse.md.
- EXP21: rzeczywiste DOF zgodne z Palace, AIR-exclusive57,586%ND2. Pełny net-release bilans55,148GBmanaged. docs/topology-memory.md.
- EXP22: aktualny residentallocaudit49,583GBpeak,99,616%przypisane dościeżek; cuDSS25,008GB, libCEEDduże bufory18,495GB. docs/memory-audit.md. Nieutożsamiać wczesnegopeaku4iter z35iterpełnego solve.
- CUDA-only+afinicznyhostclock krótki profil W.3PASS, bezwarnings:2iteracje17,665s, P16,278sinclusive,295,472GBUVMmigrations. Held-out1,127µs<10µsmarginesu;1/4939kerneli nieprzypisany przygranicy. docs/profiling-window.md. Historyczne NVTX i failedclock zachowaneREJECT.
- EXP23: PEC Maxwell/Mie zbieżność i1%PASS na1920RWGDOF/33,89s; Bempp/H2Opus przypięte, izolowany Python/JITcache. docs/maxwell-oracle.md.
- EXP24: rzeczywisty H-matrix exact-near/complexSVDfar iCUDAapply jakościowoPASS; macierz−9,16%, ale52,68×wolniejszy apply na małej kuli. Niepromowany; brak peakRAMoszczędności, dielektryka/interfejsu ianteny.
- EXP25–29: native2kernel/H-matrixeta4 −17,31%matrixdata i poprawnyGPUoperator/CPUbasisGMRES. DielectricPMCHWT/Mie far-fieldPASS0,0223% zregułąobjętości i zbieżnością; stareinscribedmeshscatterFAIL. docs/maxwell-native-dielectric.md.
- Praca RAM/VRAM. FEMcap60GiB/guard6GiB; nowe małe oraclecap6GiB/noadditionalSwap, noOOM. Bezpaidcompute/closedapps; cachekompilacji osobno.58testówPASS, kod Palace/medium bez zmian.

## Rejestr eksperymentów


| ID | Wynik i decyzja | Artefakty / ograniczenia |
| --- | --- | --- |
| EXP01 | Coax FP32/FP64: porty zgodne; raw residual nie znika z FP64, sam storage nie wyjaśnia norm. | `artifacts/m1-coax-{raw-residual,fp64-raw-residual}-20261018/` |
| EXP02 | Audyt anteny: AIR 61,71% elementów, PTFE 30,03%; dense BEM block ~11,90 GiB to rachunek ilustracyjny, nie pomiar oszczędności. | `artifacts/m1-mesh-audit-20261018.json` |
| EXP03 | Probes TEM E/B/energia PASS; LEFT vs RIGHT pokazuje różnicę raw/stopping, RIGHT wymaga więcej iteracji. | `artifacts/m1-tem-fields-*` |
| EXP04 | Tiny natywne L2 PASS <1% obu portów; wcześniejszy 20 mm L2 FAIL/deadline 180 s zachowany. | `artifacts/m1-tem-validation-20261018.json` |
| EXP05 | Całe pola tiny FP32 vs FP64 PASS (E≤1,14e−7, B≤6,09e−5); sztuczne B×1,02 prawidłowo FAIL; disk/resident tiny PASS, lecz disk storage odrzucony wymogiem. | `artifacts/m1-fields-tiny-*` |
| EXP06 | Pierwszy antenna run przerwany sygnałem, przyczyna nieustalona; background tiny potwierdził live PID. FP64-disk ref ukończona; wcześniejszy resident FP32 antenna run FAIL/host guard. | `artifacts/m1-antenna-field-attempt-20261018.json`, `artifacts/m1-background-smoke-20261018/`, dalsze dane w raporcie M1 |
| EXP07 | FP32-disk antenna zakończona po 151 iteracjach/1563,128 s; 7 porównań pól PASS (max E 2,75e−5/B 3,66e−3). **REJECT** — storage dyskowy zabroniony; scratch usunięty. | `artifacts/m1-antenna-fields-fp32-disk-20261018/`; szczegóły w raporcie M1 |
| EXP08 | Po usunięciu disk basis resident coax-tiny: 6/6 PASS, 14,06 s, cgroup peak 0,68 GiB; brak pól, anteny i kwalifikacji RF. | `artifacts/m1-no-disk-basis-resident-20261018/` |

Artefakty lokalne zawierają dokładne argv/config/build manifesty, wyniki, telemetry i logi tam, gdzie dany test je generował. FAIL kompletności nie jest wynikiem RF; nie wyprowadzać błędu anteny z nieukończonej próby.

## Następny krok

1. M1 zakończony:47tests/docs-garden/rootreviewPASS, normalpath6/6pola/rawPASS; zachować referencję i cachednative.
2. M2: następny rzeczywisty mały H(curl) FEM–BEMinterface (normalne/orientacja/normalizacja) vspełnyFEM/niezależnepole. Nativeapply i dielectricfar-fieldgotowe; nadalbraknearfieldE/B/scalableassembly/skalowania/anteny. Nie stroićdalejmałejkuli zamiastinterface. M2otwarty, bezpaidcompute.
3. KierunekpóźniejszychoptymalizacjiFEM: zredukowaćworking set i ping-pong UVMfaktorów/workspace. NiepowtarzaćNVTX/captured-onlywariantów z ostrzeżeniami. NiepromowaćTCna podstawie FLOPspecs; obecnyprofil pokazujepresjępamięci i dominacjępreconditionera.

## Reguły pracy

Jedna próba = hipoteza, dokładne argv/hash, limit, wynik i decyzja; FAIL nie jest speedup. Nie powtarzać referencji/sweepów bez potrzeby. Zachować cache CMake/ccache/dependencies. Ta sama Luna high wykonuje wyłącznie gotowe uruchomienia/babysitting i docs-garden; projekt i interpretacja należą do agenta głównego. Cel pozostaje aktywny i nieukończony.

Dodatkowa kontrola guard: aktualny natywny binary w kontenerze odrzucił oba legacy env PALACE_GMRES_FP64_DISK_BASIS/PALACE_GMRES_FP32_DISK_BASIS (exit1, komunikat RAM/VRAM) przed MPI/CUDA. Dowód: artifacts/m1-no-disk-basis-resident-20261018/legacy-rejection.json. Build 63,11 s; resident tiny 14,06 s PASS. Następnie 19 regresji narzędzi PASS, w tym przypadki audytu alokacji i Q-pool; szczegóły w [docs/testing](docs/testing.md). HostSwapTotal=0; nie zmieniano konfiguracji systemu.

## EXP09 — audyt bez nowej symulacji

PASS analizy: tools/allocation_audit.py odtworzył duże alloc/free ze stosami, odzyskał 3 zdarzenia doklejone do stdout i przypisał 99,50% logicznego peak 45,18 GiB. W tej samej chwili 48 buforów po 538 043 520 B = 24,05 GiB, ścieżki libCEED QFunction/basis/assembly. To nie fizyczna rezydencja i nie obietnica odzyskania 24 GiB. Źródła przypiętego libCEED cbd4902 potwierdzają per-operator Q-vectors oraz brak fused curl/div w cuda/gen, dlatego nie uruchamiano ślepego benchmarku nowego backendu. Audyt i hipoteza workspace: [docs/memory-audit](docs/memory-audit.md); dane `artifacts/m1-antenna-allocation-audit-20261018.json`. Nie zmieniano kodu numerycznego ani zależności, cache/build bez rekompilacji. M1 nadal otwarty.

## EXP10 — pilotaż współdzielenia aktywnych Q-wektorów (PARTIAL / NOT QUALIFIED)

Hipoteza: aktywne Q-wektory per operator mogą używać istniejących `CeedGetWorkVector/Restore`, zachowując trwałe i bierne pola oraz oryginalne buforowanie assembly. Prototyp ograniczono do `ApplyAdd`; `EVAL_NONE` i `AtPoints` bez zmian. Pełna `cudaDeviceSynchronize` przed pożyczeniem i przed zwrotem daje konserwatywny porządek, ale może kosztować tyle, że wariant nie będzie wart promocji. Nakładające się `ApplyAdd` są odrzucane. FP64 i algebra pozostają bez zmian. Alternatywna biblioteka libCEED ma przypięte źródło i manifest; build zmienił jeden plik C i użył cache pozostałych obiektów. Build trwał 1,51 s. Odrzucono wcześniejszy pomysł interposera przed GPU z powodu prywatnych symboli libCEED; użyto osobnego pełnego SO, bez modyfikacji bazowych bibliotek/obrazu. Szczegóły: [docs/ceed-qpool.md](docs/ceed-qpool.md).

Probe 6 DOF PASS w bazie i Q-pool: dwa operatory naprzemiennie, aktualizacje danych pasywnych, diagonal i `ApplyAdd`. Q-pool: 16 wywołań/32 pożyczone wektory; czas 0,63 s vs 1,90 s nie jest benchmarkiem (zimny/ciepły JIT). Artefakty: `artifacts/m1-qpool-probe-20261018/`.

Następny filtr to coax-tiny 3 częstotliwości × 2 porty, FP64 i allocation trace; dopiero potem Q-pool TEM L2 przy 3,55 GHz/2 portach. Jednak baza coax-tiny zakończyła się przed solve po 2,8878 s: `cudaMalloc(4294967312)` OOM w lazy 4 GiB HYPRE/Umpire device pool, równolegle z host guard. MemAvailable spadła z 5,34 do 4,84 GB; w tej chwili zaobserwowano też około 15/16 GiB VRAM zajęte przez inne obciążenie. Dwa dalsze runy i pełna antena pozostały NOT RUN, bez retry i bez zamykania aplikacji użytkownika. Błąd baseline nie kwalifikuje ani nie odrzuca numeryki Q-pool. Dodano preflight, który nie uruchamia kontenera GPU przy dostępnej pamięci hosta poniżej 6 GiB; właściwy guard nadal działa podczas runu.

Przypięte źródło hypre 3.1.0 potwierdza leniwie tworzoną pulę device 4 GiB i publiczny setter `HYPRE_SetUmpireDevicePoolSize`. Zmniejszenie jej rozmiaru to osobna, jeszcze niewdrożona i niezmierzona hipoteza; nie łączyć jej z porównaniem Q-pool. Mały probe nie stanowi dowodu zysku pamięci/szybkości dla Maxwella. M1 otwarty, obowiązkowe M2 FEM–BEM/MoM niepominięte.

Root końcowy przegląd: 19 regresji PASS; generator cache kontroluje także runtime ID. Odświeżenie recepty trwało 1,61 s, kolejne wywołanie trafiło w cache bez kompilacji. SHA biblioteki i probe odpowiadają artefaktom PASS 6 DOF. Natywny Palace nie wymagał rekompilacji, a domyślny backend pozostał bez zmian. Następny krok to niezależny test początkowego seedu HYPRE/Umpire, nie retry OOM.

## EXP11 — początkowa pula HYPRE (TINY PASS / ANTENNA NOT RUN)

Zmiana jest opcjonalna: `PALACE_HYPRE_DEVICE_POOL_MIB` / `--hypre-pool-mib 256` ustawia seed po inicjalizacji HYPRE, przed utworzeniem hierarchii FEM. Domyślne 4 GiB pozostaje bez zmian; seed nie jest limitem, a pula może rosnąć. Wszystkie testy zachowały FP64 i średnią dokładność.

Pierwsza para coax-tiny (3 częstotliwości × 2 porty) ukończyła 6 solve z tymi samymi iteracjami [24, 13, 14, 25, 13, 13]. Max Δcomplex S = 8,56e−15, ΔVSWR = 1,34e−14; UVM peak obu runów 322 588 630 B. Te wstępne runy nie izolowały zużycia procesu: globalny GPU to także obciążenie pulpitu. Późniejszy pomiar PID wykazał dla defaultu 4 GiB peak 4 657 774 592 B, a dla seedu 256 MiB 631 242 752 B — różnicę 3,75 GiB w próbkowanym VRAM procesu. Próbowano około raz na sekundę (9/10 próbek); to wynik małego fixture, nie gwarancja dla pełnej anteny. Czasy 10,475 s i 10,388 s są zbliżone, bez wykazanego speedup.

Known-TEM 256 MiB, 3,55 GHz, oba porty: L2 pola E 0,4953%, B 0,5211–0,5363% przy kwadraturach 4/6; wszystkie wartości poniżej 1%. To nie kwalifikuje pól pełnej anteny.

Q-pool sprawdzono osobno względem seedu 256 MiB. Coax-tiny: 11,437 s, sampled VRAM procesu 631 242 752 B, logical UVM peak 341 345 926 B wobec 322 588 630 B w seed-only (+5,8%). TEM L2 ukończył się w 17,561 s. Porty pozostały numerycznie zgodne, ale filtr nie wykazał oszczędności pamięci; Q-pool nie jest promowany i nie ma podstaw do kolejnego pełnego runu.

Audyt historycznego peak 45,18 GiB przypisuje zdarzenie wyzwalające `CompareFieldSnapshots` / `GetMagneticFieldEnergy`, zgodnie ze stosem `peak_trigger_event`. To koszt diagnostyki pól, a nie dowód, że sam GMRES osiąga taki peak. Nie sumować wszystkich buforów ze snapshotu z całą bazą GMRES ani nie wyciągać właściciela z kolejności tekstów stdout/stderr. Następny krok M1 to jawne znaczniki faz i pomiar peaków w solve oraz postprocessingu, po czym ocena budżetu dla referencji FP64 rezydującej wyłącznie w RAM/VRAM.

Pełna antena z Q-pool pozostaje NOT RUN; seed256 MiB bez Q-pool został później użyty w ukończonym EXP12 poniżej. Domyślny seed 4 GiB nie zmienił się. M1 pozostaje otwarty, a obowiązkowy prototyp M2 FEM–BEM/MoM nie jest pominięty.

## Stan walidacji repozytorium

Aktualny build przyrostowy native ukończył się w 8,298 s; 25 testów jednostkowych PASS. Te kontrole walidują narzędzia i małe fixture, nie kwalifikują pełnej anteny. Pełna antena EXP12 ma execution PASS, lecz niezależna jakość pozostaje otwarta; multi-GPU i zbieżność produkcyjna pozostają NOT RUN. Wymóg RAM/VRAM bez SSD/swap pozostaje obowiązujący.

## EXP12 — fazy pamięci i lifetime bazy (filtry i pełny run ukończone)

Kod GMRES potwierdza, że zwykła baza FP64 V jest polem solvera i zostaje po Mult. Opcja release czyści V dopiero po rekonstrukcji i wszystkich checkach; nie zmienia E, statystyk, restartu ani tolerancji. Kolejne Initialize odtwarza V. Markery adaptera emitują monotoniczne czasy i live/peak pomiędzy fazami, bez deviceSync. Domyślne zachowanie pozostaje bez zmian. Walidacja: tiny 6 solve'ów, known-TEM, następnie jedna pełna referencja wykonania FP64; wyniki poniżej. Samo ukończenie nie zamyka M1.


Pierwszy filtr `artifacts/m1-gmres-release-tiny-20261018/`: exit 0 i 6/6 solve w 11,515 s, lecz **FAIL kompletności diagnostyki** (`complete=false`). Ostatni komunikat zwolnienia bazy został rozdzielony przez zmieszanie stdout/stderr; rozpoznano tylko 5/6 pełnych prefiksów. Nie uruchomiono kolejnego TEM. Zmieniono emisję release na pojedynczy wpis stderr, jak markery faz; wymaganie sześciu pełnych komunikatów pozostaje bez zmian. Cached rebuild 7,388 s, 22 unittesty PASS. Powtórzenie z nowym hashem źródeł otrzymuje osobny sufiks `r2`; pierwotnego FAIL nie nadpisujemy.

Retry r2: release i fazy 6/6 PASS, ale kolejny **FAIL kompletności** (5/6 `PALACE_KSP_CHECK`). Interleaving przeciął tym razem stdout z residuum, więc samo przeniesienie release na stderr nie wystarcza. Runner zapisuje teraz stdout/stderr osobno, a dopiero po zakończeniu składa `palace.log` z jawną informacją o braku globalnej chronologii strumieni. Zachowuje surowe logi; test z celowo przerwanym stdout potwierdza integralność komunikatu. 23 unittesty PASS. Kolejny filtr r3 używa tego samego native builda (zmiana wyłącznie Python/logging).


EXP12 r3 filtry **PASS**: tiny save-fields 10,517 s, 6/6 solve (24/13/14/25/13/13), wszystkie stopping checks ≤1e−6, markery i release 6/6. Względem EXP11 seed256 max |ΔS|=3,88e−15, ΔVSWR=6,66e−15, względna zmiana wspólnych energii=2,07e−13 (`artifacts/m1-gmres-release-analysis-20261018.json`). Sampled GPU procesu 631242752 B; cgroup peak506884096 B; logical UVM peak308538406 B. To kontrola numeryczna małego fixture, nie dowód speedup ani kwalifikacja anteny.

TEM r3: 17,586 s, 2/2 solve, pełne coverage; E L2 q4/q6 około0,495%, B0,521–0,536%, oba porty <1%. Logical UVM peak290950486 B, sampled process GPU631242752 B. Baza znika po sprawdzeniu rozwiązania, przed postprocessingiem; liczniki liczą lifetimes, nie rezydencję GPU.

Wykonane polecenie pełnego runu: `python3 tools/dev.py run tshaped-medium artifacts/m1-antenna-resident-fp64-20261018 --seconds 1800 --basis fp64 --hypre-pool-mib 256 --release-gmres-basis --memory-marks --save-fields --background`. Jedna3,50GHz/P2, identyczny mesh medium, bez Q-pool i porównania starej referencji, bez dyskowej pamięci roboczej. Cgroup60GiB, hostguard6GiB, przed uruchomieniem około68,7GiB MemAvailable; GPU miał obciążenie aplikacji użytkownika (około4,8GiB), nie zamykamy ich. Guard/OOM/deadline nadal oznaczają FAIL; ten konkretny run ukończył się naturalnie. M1.2/M1.3 niezależnej jakości nadal otwarte.


Pełny run EXP12 **execution PASS**, 1089,964 s, 151 iteracji, 3,50GHz/P2; bez OOM/guard/deadline. Wszystkie markery faz i release1/1. Zwalnianie V po solve zmniejszyło logical managed58,706→31,422 GB (25,41GiB), koszt0,181 s. Maksymalny logical managed58,779 GB (54,74GiB) nastąpił w GMRES; postprocessing48,090 GB (44,79GiB). Cgroup peak57,72GiB, sampled GPU4,89GiB, min hostavailable11,98GiB. Peaki nie są addytywne ani dowodem konkretnej rezydencji alokacji. Snapshot E/B ma179499600/240704512 B i SHA w fields.json; pełna analiza root w `root-analysis.json`.

VSWR P2=1,672123; raw ||b−Ax||/||b||=0,1252666005 przy independently recomputed LEFT stopping9,956397e−7. Raw/stopping ratio≈125815; nie wynika to z FP32, bo aktualny solve jest FP64. **Jakość anteny M1.2/M1.3 pozostaje nierozstrzygnięta**; nie promować dalszej precyzji na podstawie samego S lub ukończenia. Ten run zastępuje odrzucone dyskowe wykonanie jako dopuszczalny punkt diagnostyczny, ale nie stanowi jeszcze kwalifikowanej referencji fizycznej. Nie wyliczać speedup względem historycznego disk runu z innym tracingiem/polityką pamięci. [Interpretacja i odtwarzanie](docs/memory-phases.md).


## EXP13 — korekta RIGHT (tiny PASS, pełna antena FAIL/deadline)

Hipoteza M1: LEFT ogranicza ||P r||, więc małe stopping nie kontroluje raw. Wznowienie z pola E nowego resident FP64 jako jednorazowego wejścia pozwoli sprawdzić korektę RIGHT bez ponownego liczenia LEFT. Źródło InitialResidual przy InitialGuess=true skaluje stopping przez ||b|| dla RIGHT, nie przez małe początkowe residuum. Limit bazy64 zamiast240 daje do około11,7GB FP64 V, a nie do43,3GB przy pełnym240; medium/mesh/Tol1e−6 pozostają. To jawna diagnostyczna zmiana solvera, nie zmiana zamrożonego fixture ani promowany default.

Nowe opcje --initial-fields i --krylov-size. Wejście snapshot ma weryfikowane SHA/header, fizykę/mesh/dependencies/coverage oraz completed result, montowane read-only. Jednorazowe wczytanie E przed każdym solve, bez dyskowej bazy/scratch/swap. Naprawiono raportowanie checka dla zerowej liczby iteracji po już zbieżnym initial guess; zwykła reguła zatrzymania bez zmian. Cached rebuild9,808s,24 unittesty PASS.

Filtry przed pełnym runem: (1) tiny LEFT replay6solve, oczekiwane0iter i identyczne pola; (2) tiny RIGHT warm6solve, raw≤1e−6, max|ΔS|≤1e−3, ΔVSWR≤0,01, względna zmiana energii≤1e−3 i ważone różnice E/B≤1% do resident tiny LEFT. Każdy limit90s, FP64/seed256/release/marks, brak płatnego compute. Pierwszy FAIL zatrzymuje sekwencję.

Dopiero po filtrach jedna pełna korekta 3,50GHz/P2 z `artifacts/m1-antenna-resident-fp64-20261018` jako input i diagnostyczne porównanie pól; RIGHT/K64/FP64/Tol1e−6, limit1800s/cgroup60GiB/guard6GiB. Cel raw≤1e−6 (niezależny od preconditionera); pełny finalny raport oddziela algebraiczne residuum od fizyki/discretization error. Porównanie do starego LEFT jest kontrolą wrażliwości na rozwiązanie, nie niezależnym modelem fizycznym. Jeśli budżet lub zbieżność nie wystarczy, FAIL zachować i dobrać kolejny krok na podstawie wyniku.


EXP13 filtry PASS: LEFT replay10,562s, 6×0iter, różnica pól0; odtworzenie initialE nie zmienia wyniku. RIGHT warm12,468s, iteracje40/38/37/41/39/38. Raw max9,7804e−7, max|ΔS|9,947e−6, ΔVSWR3,282e−6, zmiana sumy mocy portów6,958e−6, względna energia1,750e−4. Ważona różnica E9,368e−6, B0,0031115 (0,311%), wszystko w zamrożonych progach. Oba runy: complete/restart/field_accuracy=true i pełne coverage. Root analiza `artifacts/m1-restart-analysis-20261018.json`. LEFT nadal raw do0,0087; jego zerowe iteracje to test replay, nie jakości raw.

Przygotowany pełny run: `python3 tools/dev.py run tshaped-medium artifacts/m1-antenna-right-correction-20261018 --seconds 1800 --basis fp64 --hypre-pool-mib 256 --release-gmres-basis --memory-marks --pc-side right --krylov-size 64 --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m1-antenna-resident-fp64-20261018 --save-fields --background`. Wyłącznie diagnostyka jakości, bez zmiany mesh/Order/PA/Tol. Baza ograniczona64; przewidywany logical solve working set około40–45GiB (hipoteza, nie gwarancja), postprocessing około45–50GiB. MemAvailable przed startem około71,9GiB, GPUbackground około2,7GiB. Same limity i twardy FAIL na guard/deadline. Weryfikacja inputu/referencji dzieli ten sam SHA check zamiast czytać dwa razy identyczny snapshot. Nie porównywać czasu warm correction do solve od zera jako speedup.


EXP13 pełna RIGHT/K64 korekta **FAIL/deadline**, elapsed1800,806s, exit255, bez OOM/hostguard. Ostatnia widoczna, niepełna linia zaczyna się od140 (restart2); ostatnia pełna linia to139, recurrence0,37005. Rzeczywista końcowa iteracja nieznana, bo stdout był buforowany; brak kompletnego solve/S/pól/checka raw. Cgroup peak43,69GiB i min hostavailable27,24GiB potwierdzają, że ograniczenie pamięci zadziałało, lecz zbieżność/czas nie wystarczyły. Nie traktować częściowego recurrence jako certyfikatu raw. Zatrzymano bez retry. Szczegóły i SHA w artifact/root-analysis.json. Ten wariant nie jest promowany.

## EXP14 — ostrzejszy LEFT (tiny PASS, pełna antena FAIL/deadline)

Nowa hipoteza po FAIL RIGHT: zachować LEFT, który skuteczniej minimalizował ważone residuum, ale skorygować zapisany wynik z Tol1e−12 zamiast1e−6. To jawnie ostrzejsza diagnostyka referencyjna, a nie zmiana domyślnego medium ani deklaracja speedup. Siatka/Order2/PA1/fizyka bez zmian. Dotychczasowy raw/stopping ratio≈1,26e5 sugeruje docelowe raw rzędu1e−7 przy LEFT1e−12, lecz NIE jest ograniczeniem błędu ani gwarancją: finalnie wymagamy jawnego raw≤1e−6 i zachowujemy progi pól/RF/energii.

K96 ogranicza do97 wektorów×179499584B≈17,42GB, mniej od27,82GB w referencji151iter. Domyślny restart240 bez zmian. Włączona w runnerze weryfikacja recomputed stopping teraz odrzuca/ponawia także FP64 recurrence gap zamiast tylko wypisywać niezgodny check; bez PALACE_VERIFY_RESIDUAL zwykła ścieżka FP64 niezmieniona. Tolerancja diagnostyczna nie może osłabić progu fixture i musi należeć do[1e−14,Tol fixture]. 25 unittestów PASS.

Najpierw tiny6solve LEFT/K96/FP64/Tol1e−12, input z resident LEFT, porównanie pól do nowego RIGHT tiny, limit120s. Wymagamy raw≤1e−6, pełne checks/coverage, max|ΔS|≤1e−3, ΔVSWR≤0,01, względna energia≤1e−3 i E/B≤1%. Dopiero po PASS pełna antena jako korekta poprzedniej FP64 referencji, limit1800s i identyczne guardy; bez dalszych restartów po FAIL.

EXP14 tiny PASS:15,553s, iteracje73/71/71/74/72/72, verifiedLEFT≤9,904e−13, raw≤8,990e−9. Względem RIGHT tiny ważone E≤2,238e−7/B≤3,375e−7; bez reliable restarts. Root RF/energia z root-analysis.json: {"max_complex_delta_S": 2.468937017680457e-08, "max_delta_VSWR": 3.1780726050811836e-08, "max_relative_energy_delta": 1.29200241662808e-07, "max_raw": 8.989300235472e-09, "max_E": 2.237693287963e-07, "max_B": 3.374143447481e-07} .

Pełny EXP14 przygotowany z K128 zamiast96: mały filtr kończy przed74iter, więc oba K nie wywołują tam restartu; większy K w dużej antenie ogranicza utratę podprzestrzeni obserwowaną przy RIGHT64. Rachunek129×179499584B≈23,16GB basis, około4,67GB mniej od FP64 resident151iter; przewidywany cgroup około53–55GiB, bez gwarancji, guard pozostaje. Pozostałe parametry: LEFT/FP64/Tol1e−12, wejście i field-reference resident FP64 z EXP12, save-fields, seed256/release/marks, limit1800s. Nie zmieniamy raw gate1e−6 ani progów pól/RF/energii. Nowy artifact m1-antenna-left-tight-correction-20261018. Po FAIL żadnego retry bez nowej diagnozy.


EXP14 pełna LEFT/Tol1e−12/K128 korekta **FAIL/deadline** po1800s, bez OOM/hostguard. Cgroup peak57 916 420 096B (~53,94GiB); brak kompletnego solve, S i porównania pól. Widoczne recurrence przy139iter/restart1 to9,78791e−4 wobec celu około1,67e−8. Ostatnia linia140 jest urwana; ze względu na block-buffered stdout NIE znamy faktycznej ostatniej iteracji. Nie interpretować jej jako wykonanych140iter ani porównania iter/s z innymi runami. Root analiza i SHA logu w artifact/root-analysis.json. Bez automatycznego retry i bez obniżania raw gate.

W obu pełnych korektach brak porównania pól wynika z nieukończenia solvera, nie ze zmierzonego przekroczenia1%. `field_accuracy_passed=false` bez entries nie jest numerycznym błędem pól. Ukończona pozostaje wyłącznie wcześniejsza FP64 LEFT1e−6 referencja wykonania (raw0,125), a niezależna jakość pełnej anteny nadal jest otwarta.

Dodano jawny PALACE_LINE_BUFFERED_LOG w lokalnym runnerze: native main ustawia line buffering przed MPI i emituje marker potwierdzenia; runner wymaga go dla complete. Osobne stdout/stderr pozostają. To usuwa wielokilobajtowe opóźnienie postępu, nie zmienia solvera. Cached build8,298s,25 unittestów PASS. Ostatni krótki replay na tym buildzie ma sprawdzić także0iter oraz nowy marker.

Dalszy kierunek M1: bez kolejnych30-minutowych prób w ciemno. Krótki profil preconditioner/CEED/orthogonalizacja przy wczesnych iteracjach z wiarygodnym logiem; sprawdzić w źródłach, czy niezależna referencja FP64 na CPU RAM może uniknąć thrashingu UVM i jaki jest koszt transferu do cuDSS. Osobno sprawdzić liniowość/złożenie preconditionera oraz rozkład residuum (w tym gradient/charge), zanim dobierzemy korektę. To hipotezy NOT RUN, nie przyczyny potwierdzone. M1 nadal blokuje promocję precyzji i M2, ale nie pomijamy obowiązkowego FEM–BEM.

Końcowa regresja logów/replay PASS: `artifacts/m1-line-buffered-replay-tiny-20261018/`,11,437s,6×0iter, markerlinebuffer/restart/pola/fazy wszystkie true. Żadna pełna symulacja obecnie nie działa. [Wyniki EXP13/14 i ograniczenia](docs/reference-correction.md).


## EXP15 — źródłowo potwierdzony CPU/RAM reference + cuDSS hybrid execute (PLANNED)

Przegląd przypiętego MFEM4.9.0 `linalg/cudss.cpp`: CuDSSSolver::ArrayMult przekazuje RHS.Read()/SOL.Write(), więc ich miejsce zależy od MFEM Device. Dokumentacja odpowiadająca CUDA12.9.1 potwierdza host pointers dla CUDSS_CONFIG_HYBRID_EXECUTE_MODE, odróżniając go od HYBRID_MODE przechowującego faktory w RAM: https://docs.nvidia.com/cuda/archive/12.9.1/cudss/types.html . Sprawdzony kod GMG zeruje initial guess przy pierwszym presmooth; nie dowodzi to pełnej liniowości, ale nie ma podstaw do twierdzenia, że carryover jest potwierdzoną przyczyną.

Nowa hipoteza przed rozbudową mikrobenchmarku: CPU libCEED i FP64 GMRES w RAM + coarse cuDSS hybrid execute mogą uniknąć GPU-UVM working set wielokrotnie większego od16GiB. To wariant REFERENCYJNY M1, nie porzucenie celu CUDA ani promocja produkcyjna. Dodano opt-in --cpu-reference: DeviceCPU,Backend/cpu/self,MFEM_MEMORYhost,8OMP/1OpenBLAS thread, FP64basis, cuDSS execute1. GPU default bez zmian. Niedozwolone FP32basis i GPUQpool wtymtrybie; hybridexecute i hybridmemory nie łączymy. Runner wymaga rzeczywistych markerów CPU backendu i cuDSSexecute, nie ufa samej fladze. --phase-trace włącza istniejący BlockTimer/NVTX trace; osobne logi i linebuffer pozostają. Pamięć robocza wyłącznie RAM/VRAM, CUDAalokacje cuDSS nadal śledzone, brak offloadu/swap.

Cached build8,973s,27unittestów PASS. Najpierw CPU tiny RIGHT warm z LEFTinput i GPU RIGHTfield-reference,6solve, limit120s; raw≤1e−6 i te same progi K.4. Następnie tylko poPASS CPU knownTEM RIGHT/L2,2solve,limit120s,analityczneE/B≤1%. Te krótkie próby jednocześnie sprawdzają zgodność cuDSS0.7.1.4 i hostpointer, zanim wydamy czas na pełną antenę. Dopiero po rootanalizie dobrać jedną dużą kontrolę. Osobny pomiar A/P i liniowości pozostaje dalszą możliwością, nie został zaimplementowany ani uznany za wykonany.


EXP15 pierwszy tiny **FAIL** po3,245s,code4=NOT_SUPPORTED na coarseSOLVE,beziteracji. CPU/backend/execute markery były obecne; nie mylić poprawnego wybrania trybu z ukończeniem solve. Przyczyna źródłowo ustalona: `MfemWrapperSolver<ComplexOperator>::Mult` wysyła nrhs=2 (real+imag), a archiwalna dokumentacja odpowiadająca cuDSS0.7 pozwala hostowe dense vectors tylko dla nrhs=1 (https://docs.nvidia.com/cuda/archive/12.9.1/cudss/advanced_features.html). To nie ogólny brak obsługi CPU ani OOM.

Konkretna poprawka przed retry: tylko gdy PALACE_CUDSS_HYBRID_EXECUTE=1 i wrapper używa mfem::CuDSSSolver o rozmiarzeN dla zespolonegoN, wykonujemy dwa niezależne Mult po1RHS. Realny preconditioner algebraicznie działa osobno na real/imag; default ArrayMult2 na CUDA pozostaje. Runner wymaga markera faktycznego przejścia serialRHS. Nie patchujemy/rebudujemy zależnego MFEM. Filtr z nowym sufiksemr2 i znanym patchem, potemTEMwyłączniepoPASS;brakpełnegoGPUretry. 27unittestówPASS.


EXP15 r2 oba filtry PASS po serialRHS fix. CPU RIGHT warm tiny19,678s,40/38/37/41/39/38iter; actual raw RELATIVEmax9,7803867e−7 (wartość2,3343e−7 to ABSOLUTE, nie relative). Względem GPU RIGHT max|ΔS|9,156e−16,ΔVSWR1,333e−15,energia0; polaE≤1,934e−14/B≤1,508e−13. Rootanaliza i SHA w `artifacts/m1-cpu-right-tiny-r2-20261018/root-analysis.json`. TEM CPU19,843s,62/64iter; rawrelative8,5273e−7/9,0263e−7, E_L2q6≈0,49531%,B≈0,45578%,oba<1%. Konfiguracjaaktualniefaktycznieomp,cpu/host-std/cpuavx,execute1/serialRHS1. TinyCPU nie jest szybsze od dawnego GPUtiny; to walidacja alternatywnej referencji, nie speedup. Cgroup756/821MB i sampledGPU245MB to mały przypadek, nie budżet pełnej anteny.

Następny POMIAR workset z limitem300s: `python3 tools/dev.py run tshaped-medium artifacts/m1-cpu-antenna-replay-20261018 --seconds 300 --basis fp64 --cpu-reference --hypre-pool-mib 256 --release-gmres-basis --memory-marks --phase-trace --pc-side left --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m1-antenna-resident-fp64-20261018 --background`. Oczekiwanie0iter jak przy replaytiny, oryginalneTol1e−6 iK240,beznowejreferencjidokładności. Porównaniepól/RFdozaładowanegowynikupotwierdza przeliczenietego samegoFEM,nierozstrzygaraw0,125. PomiarbaseworksetitimerówpierwszychA/P pozwoli dobraćK dlawiarygodnejkontroliprzednastępnąpełnąkorektą. Cgroup60GiB/guard6GiB bez zmian,poFAILstop. Brakpaidcompute/offloadu/swap,niezmieniamyźródełwczasierunu.


EXP15 CPU large replay **FAIL/cgroup OOM** po247,6s, exit137 iOOMKilled=true, nie deadline ani hostguard. Osiągnięto0iter i rawRELATIVE0,1252666005, lecz brakS/pólkońcowych;niekwalifikować. Ostatni zaobserwowany cgroupHWM63,102GB(~58,77GiB), próbkowanie może nie uchwycić chwilowego szczytu przedOOM przycap60GiB; minhostavail7,47GiB>guard6. Managedpeak8,901GB nie obejmuje CPUheap; nie sumować z cgroup. Telemetria: około30GiB przedGMRES, około40GiB po pierwszych aplikacjachP, szybkiwzrost>58GiB przy postprocess. To mierzalnie wyklucza prostąCPUreferencję wtymprofilubezmodyfikacjipamięci.

Krótki profile trace dał dwie inkluzywne aplikacjeP13,616/12,464s;coarse1,182/0,133s zawiera się wP. PozostałyczasP≈12,43/12,33s,jednak dwa różneinputy i warmupnie są benchmarkiemmedianowym. CPU nie promować: fullOOM i brakprzewagiczasu. Napotkaneproblemy nieuzasadniają zwiększaniacap/guard ani powtarzaniapełnychrunów. Rootanaliza+SHAw artifact/root-analysis.json. OsobnytestliniowościA/P nadalNOTRUN.

## EXP16 — dokładny zespolony coarse solve (TINY FILTER PASS)

Kod currentMfemWrapperSolver<ComplexOperator>::SetOperator przy ComplexCoarseSolve=false tworzy realAr+Ai; przytrue tworzy równoważny rzeczywisty blok [Ar Ai;Ai −Ar] i odtwarza znak imag. To istniejąceAPIupstream, nie nowysolverani zmianarównaniaA. Hipoteza: lepsza reprezentacja fazy coarse zmniejszy liczbę iteracji RIGHT do wiarygodnego raw, kosztemwiększychfaktorów. Nowyopt-in --complex-coarse wymusza ComplexCoarseSolvetrue/PCMatShiftedfalse,inneparametrymediumbez zmian. Na razieniełączymyCPUprofile (niekwalifikowanekombinacje),GPUdefault bez zmian.

Najpierwten sam GPUtinyRIGHTwarm6solve coEXP13/K128,limit120s,FP64/seed256/release/marks/trace,inputLEFTold,referenceGPURIGHT. Qualitygates:raw≤1e−6,complexS≤1e−3,VSWR≤0,01,energia/power≤1e−3,polaE/B≤1%. Promisingfilterprzedjakąkolwiekpełnąpróbą: suma iteracji≤70% z233w zwykłymRIGHTwarm i faktorpeak≤3×tinydefault. To filtrkosztu, nie gwarancja skalowania dużejanteny. Jeśli nieprzejdzie, zapisaćodrzuceniei nie uruchamiać dużej. 28unittestówPASS,zmianyrunnera nie wymagająprzebudowynative.


EXP16 tiny RIGHT **PASS filtr**, nie promocja anteny: 153 iteracje vs233 (−34,3%), 12,534s; raw relative≤9,101e−7. Root sprawdził S z prawidłowym przeliczeniem dB/stopnie→complex (nie Re/Im): max|ΔS|2,511e−8, ΔVSWR2,641e−8, Δpower2,952e−8, względna energia1,277e−7. PolaE≤2,240e−7/B≤2,286e−7. FaktorycuDSS167934380B vs61473620B, 2,732×: mieści filtr≤3×, ale większa antena może mieć inny fill. Rootanaliza+SHA w artifacts/m1-complex-coarse-right-tiny-20261018/root-analysis.json.

## EXP17 — zwolnienie finalnego solvera (TINY PASS, FULL GUARD)

Opt-in --release-final-solver tylko fixed-mesh uniform sweep. Po ostatnim rzeczywistym porcie/freq i kompletnych kontrolach GMRES zapisuje metadata, niszczy KSP (z faktorami) przed A/P/A2/K/C/M; zachowuje Curl, E/B, RHS, przestrzenie i materiały potrzebne pomiarom. Default bez zmiany matematyki/lifetime; brak AMR/adaptive qualification. Marker dokładnie1× i opcjonalne fazy linear_workspace_release.begin/end. Cel: nie trzymać martwych faktorów podczas dużych buforów pomiaru pól. Nie ograniczamy jakości, nie wyłączamy walidacji pól. Pamięć wyłącznie RAM/VRAM, bez dyskowego workspace/swap.

Build cached9,635s,29unittestówPASS. Pierwszy filtr: ten samtiny6solveRIGHT/FP64/K128/complexcoarse, dodane release-final-solver; reference pola z EXP16. Tolerancje RF jakEXP16; identyczne iteracje i S/energie oczekiwane, tylko zmiana lifetime. Jeśli FAIL stop. Dopiero poPASS jeden full GPU RIGHT/complexcoarse/K64,1800s,cap60GiB/guard6GiB,initial/referenceEXP12. Warmstart nie dowodzi jakości referencji; raw≤1e−6 i pola/RF pozostają wymagane. Szacunek pamięci nie jest dowodem dopasowania pełnego przypadku.


EXP17 tiny **PASS**: identyczne153iteracje,12,567s, raw≤9,101e−7. Pola względemEXP16 E≤3,069e−15/B≤1,508e−13. Root CSV: max zmiana S w jednostkach dB/stopnie2,501e−10, I4,801e−18A,V2,411e−16V, energia0; zgodność do zaokrągleń, nie bitwise. Final release dokładnie1×: managed386820886→127942182B (−258878704B); cuDSS167934380→0B. Peak tiny nie zmniejszył się (występuje wcześniej), więc nie obiecywać redukcji globalpeak. Cgroup578367488B/GPU631242752B. Rootanaliza w artifact. Następny full zgodnie z predeclared1800s/K64; bez zmian źródeł podczasrunu.


EXP17 full complex-coarse RIGHT/K64 **FAIL host_memory_guard** po399,828s,exit137,OOMKilled=false. ContainerExited/PID0potwierdzone. Ostatnia rzeczywista wypisana iteracja16/restart0, recurrence1,339219e−2; brak końcowego raw/S/pól. Zbieżność częściowa silniejsza niż realcoarse EXP13, ale nie jest PASS ani porównaniem czasu do wyniku. Cgroup61550936064B(~57,33GiB), GPU-process5280628736B. Przy preconditioner.end cuDSS live30641370420B, setup110,957s. Ostatni zaraportowany logical managed HWM48998044042B pochodzi sprzedGMRES, nie z końca runu; nie sumować faktorów (są wewnątrz managed). Nie podnosimycap/guard, nie zamykamyaplikacjiużytkownika i nie retry tego samegokonfigu. Rootanaliza+SHA w artifact.

Następny najmniejszy krok M1: zbadać bezpośredni FP64 complex-coarseN×N zamiast obecnego realnego bloku2N×2N; najpierw mały, wytworzony układ/probe API pinnedcuDSS0.7 i pomiar, następnie coax/TEM tylko poPASS. Archiwum dokumentacji12.9.1 types opisuje SYMMETRIC jako realny, HERMITIAN nie jest właściwy dla ogólnego kompleksowo-symetrycznego Maxwell; dla prototypu zacząć od poprawnego GENERAL/CUDA_C_64F, nie narzucać Hermitian ani obiecywać 2×oszczędności. Źródło wrappera palace/linalg/solver.cpp tworzy[Ar Ai;Ai−Ar]. To hipoteza zmniejszenia faktorów bez obniżenia precyzji, nie wykonany eksperyment. FP32coarse/TCnadalniepromowane; M1otwarty.


Checkpoint integracji EXP15–17: docs-garden LunaPASS, rootdiffreviewPASS,29unittestówPASS,docscheckerPASS (istniejące miękkie591tokAGENTS),gitdiffcheckPASS,manifest source/native/depsPASS. Cachednativebuild9,635s. Zmianywyłącznieopt-in; fullqualityM1nadalOPEN. Żadnej symulacji pozostawionej live; bezcloud/paidcompute. Commitlokalny, niepushupstream. Następnie przygotować mały nativecomplex FP64probe; nie ponawiaćfullblokowego wariantu.


## EXP18 — native complex FP64 API probe (PLANNED)

Cel M1: uniknąć realnego bloku2N×2N dla dokładnego coarse solve, bez redukcji precyzji. Najpierw samodzielny known-solution probe pinnedcuDSS0.7: ten sam kompleksowo-symetryczny, nie-Hermitowski stencil3D, dwa RHS i refaktoryzacja zmienionych wartości przy stałym wzorcu. Porównać CUDA_C_64F/GENERAL N z równoważnym realnym blokiem2N/SYMMETRIC; sprawdzić x/rawrelative i cleanup. Dane i faktory wyłącznie managedRAM/VRAM; żadnych zależności rebuild. Limit60s/2GiB,noextraswap. Kryteria przedrunem:relative_solution i raw_rhs_relative≤1e−10, zero live cuDSSallocatorbytes poDestroy i poprawna liczba case/update. Pomiar małychpeak/time jest filtremAPI/reprezentacji, nie prognozą pełnegoantennafill ani speedup. Integracja coarse w Palace dopiero poPASS. Źródło API: archiwum CUDA12.9.1/cuDSS functions i types (sprawdzone2026-10-18); licencja kodu własnego taka jakforkApache2.0.


EXP18 **PASS**:512complexGENERAL i1024realSYMMETRIC, nrhs2×2aktualizacje. Relative_solution/native6,96e−16,block1,24e−13; raw_rhs/native2,67e−16,block5,47e−14. CuDSSpeak2637284B vs4920228B (−46,4%),live0poDestroy. Build2,049s,run2,985s,31unittestówPASS. Czasy faz mocno cold/order-biased (complex pierwszy1,1sfactor,realpóźniej~0,002s),nie uznajemy za benchmark szybkości. FilterAPI nieprognozuje fillpełnejanteny. Rootanaliza+SHA w artifact. Następnie mała opt-in integracja nativecomplexcoarse dla jednegoMPIranku w Palace; FP64operator/tolerancje bez zmian.


## EXP19 — opt-in native complex coarse integracja (PLANNED)

PoPASS EXP18 integrować ComplexCuDSSSolver<Solver<ComplexOperator>> dla rank1GPU; bez realbloku2N, FP64GENERAL. Konstruować CSR unionAr/Ai, wyłącznie RAM/VRAM. Domyślny solver iMGM/CPUbez zmian, profileCPU/hybrid/FP32adapterzabronione. Pierwsza wersja jawnie refaktoryzuje i wykonuje analysis przy każdymSetOperator (reuseM4później); pakujevec przezistniejąceComplexVector.Get/SetGPU, synchronizuje dla poprawności. To koszt prototypu, niepromocja. Filtrtiny6solveRIGHT/K128/Tol1e−6,porównanieEXP16complexblock: raw≤1e−6,|ΔS|≤1e−3,ΔVSWR≤0,01,energia/power≤1e−3,E/B≤1%; potemTEM<1%. Rachunek dużegoRAM dopiero po rzeczywistychpeak/timefiltrów. BrakwiększejantenyprzedPASS,limitybez zmian.


EXP19 pierwsze tinyFAILsegfault5,294s,nieOOM,przedsolve. StackClearGPUSparse→cusparseDestroySpMat zSetOperator. Źródło pinnedMFEM4.9: SparseMatrix ma CUDA_VERSION-zależny layout, GetDiag tworzy/wymienia wrapper i defaultkonstruktor inline wołaInitGPUSparse. Nowycomplexcudss.cpp był błędnie kompilowany jako hostCXX przy późnym includeCUDA; istniejącycudss.cpp jest wTARGET_SOURCES_DEVICE. Konkretna poprawka: dodaćnativeplik do tej samej listyCUDA i compile-time#error gdy wróci dohostCXX wMFEMCUDA. Dodatkowo jawneClear po skopiowaniu CSR przed zwolnieniemassembly, kontrola wymiarów. Retrytinywyłączniepo tej poprawce, nowy suffixr2; bez zmiany fizyki/progów.


EXP19 r2 **PASS** po CUDAcompilefix:6×native17146/260044nnz, te same26/25/24/27/26/25iteracje co exactblock,12,529s. Rawmax9,101e−7, polaE≤3,270e−15/B≤1,506e−13 względem EXP16. CuDSSpeak113329412B vs167934380B (−32,5%), cgroup529842176B vs578367488B (−8,4%w tejparze), sampledGPU631242752B bez zmiany. To redukcja małego przypadku,nie oszacowaniepełnego fill. Nativephase30% mniejfaktorów daje podstawędoTEM, nie promocję. RootRFanaliza+SHA w artifact. NastępnyfiltrTEM3,55GHz/2porty FP64RIGHT,natywneL2kwadratury4/6,limit120s; progiE/B<1%,raw≤1e−6. No pełnyrun przedPASS.


EXP19 TEM **PASS**:3,55GHz2ports,39/42iter,18,729s,raw_rhs≤9,594e−7. NatywneL2q6E≈0,49531%,B≈0,45578%,oba<1%; q4zgodne. Native17146/260044nnz dwukrotnie, cuDSS113329412B,live0porelease. Cgroup597676032B/GPU631242752B. RootsprawdziłlogdokładnychL2/raw; bezpromocji pełnej anteny.

Następny jeden fullGPU RIGHT/K64/nativecomplex FP64,1800s,initial/referenceEXP12, savefields,seed256,obarelease,trace/marks. PreflightbieżącegoRAM;cap60GiB/guard6GiBbez zmian. Orientacyjnybudżet: dotychczasnonfactor~18GB +nativefactor~21GB (tylkoekstrapolacja ztiny,niegwarancja) + do12GBbazy + ok7GBworkingMG i cgroupdelta. Ryzykofill/hostguardjawne; niepowtarzać poFAIL bezdiagnozy. Raw1e−6,E/B1%,complexS1e−3,VSWR0,01/energy-power1e−3; staryEXP12zraw0,125 niejestdowodem prawdziwościreferencji,każdąrozbieżnośćinterpretować bezpoluzowaniaprogów. Brakpaidcompute/diskworkspace/swap.


EXP19 full native **solver COMPLETE/quality NOT PROMOTED**:419,08s,35iter,rawRHSrelative8,35543e−7 (RIGHTniezależnieponownieAx−b),VSWRP2@3,5GHz≈1,668. NativecoarseN2196005,nnz32284067,cuDSSpeak25008217684B (~23,29GiB),managedpeak55147611962B,cgroup58895593472B (~54,85GiB),sampledGPU2GiB. Finalsolver/basisreleasePASS,45vectors8077481280B,allocatorlive0. OOMfalse,guardnietrigger,minhostavailable11,82GB. ZreferencjąEXP12:globalE0,1774%,B0,5910%,ale regionalB2=1,1656%/B4=1,2094% >1%. KryteriumK4FAILvsstaryniekwalifikowanyref; nie promować ani nie podnosićtolerancji. Wynik może być dokładniejszym rozwiązaniem starych równań,ale wymaga kontroli. Czasy419vs1089s nie są kontrolowanym speedup:innePC,stronaiwarmstart. Rootanaliza+SHAwartifact.

Następny testreferencjiFP64: ten samnativerightK64,mediumbez zmian, --linear-tol1e−9,warmstart z nowegoEXP19full,porównaniepóldoEXP19full;1800s/cap60GiB/guard6GiB. To3rzędyostrzejszyraw cel,niepoluzowanie. Oczekujemy małej korekty,raw≤1e−9 i pola≤1%/S≤1e−3/VSWR≤0,01/energy-power≤1e−3. Jeśli nieprzejdzie, niepromować i nie retry bezdiagnozy. Nowyinput jest ukończonym solve,niecertyfikatemdokładnościpól. Celem jest stabilność numeryczna i diagnostyka niekwalifikowanejstarejreferencji,nieomijanieM1.


Tightcheck pierwszypreflight **NOTRUN**: obecnyverifierodrzuciłEXP19także jako input zpowodufield_accuracy_passed=false. Nie uruchomiłGPU. Naprawasemantyki: --field-reference nadalBEZWZGLĘDNIEodrzuca takąreferencję (regresjapozostaje), --initial-fields osobnoprzyjmujeukończone,bajtowozweryfikowane snapshoty zgodnejfizyki jako PRZYBLIŻENIEstartowe. Wciążodrzuca niekompletność,zmienionefizyki,uszkodzenia/deps. command.json jawniezapisujesourceaccuracyfalse orazscopeinitialonly.33testsPASSwtymrolereference-vs-initial; bezrebuildnativeboPythononly. To niezmianaprogów/zaakceptowanierejectedaccuracyjako wzorca.

Konkretne nowe argv tight-r2: bez --field-reference, z --initial-fields EXP19full iTol1e−9,savefields. Najpierw strictejszesamodzielneFP64rozwiązaniezraw≤1e−9,zapisane jako kandydatreferencjiM1. Potem dopierorozwiązaniemediummożebyćporównanezTIGHTjako referencją (nie odwrotnie); progiK4pozostają1%/1e−3/0,01. Do tego czasuM1otwarty,żadnejpromocji. RóżnicezEXP12takżewS=0,0011899>1e−3,zachowaneFAIL. Limit1800/cap60GiB/guard6GiBbez zmian.


Tight-r2 **COMPLETE**:360,946s,24iter,niezależnyrawRHS7,28157336e−10 (threshold3,00779933e−8absolute),FP64nativeN2196005/32284067nnz. No fieldcomparison wtymrunnie,niezaliczaćjeszczeK4. CuDSS25,008GB/live0,managed53,173GB,cgroup56,916GB(~53GiB),GPU-processsample2GiB;hostmin11,782GB. SnapshotyE/Bkompletne/SHA. RootporównałS/energie docandidatemediumnative: bardzo mała różnica,zachowana w root-analysis.json. To silniejszykandydatreferencjiM1,niepromocjainnychoptymalizacji.

Następnyjeden W3fullbezszczegółowegoBlockTimertrace: nativeRIGHT/FP64/K64/Tol1e−6, initial=oryginalnyEXP12 (ten samstart coEXP19traced35iter), field-reference=tight-r2,savefields. Limit900s,cap60GiB/guard6GiB,seed256/obarelease/marks,bez--phase-trace. Oczekujemy35iteriK3/K4PASS; nie używamy0iterreplay jako benchmarkusolve. Tenrun ma wykazaćstabilnośćpólwzględemostrzejszejreferencji i pełnykosztbeztrace. Warunki tła i warmstart podane; nadalnieporównywać419/1089jako czystegospeedupu względemzimnegoLEFT. PrzyFAILstop.


EXP19 fullqualified **W3/K3/K4PASS**:bezphase-trace,447,462s,35iter,rawRHS8,35543267e−7. VSWRP2@3,5GHz=1,6684235. Porównanie do tight-r2raw7,282e−10: E/Bwszystkichregionów≤9,886e−8 (relative), dużo poniżej1%; rootRF/S/VSWR/energia/powerPASS, dokładneliczby+SHAwroot-analysis.json. Nieprzestawionoprogów;staryEXP12 pozostaje niekwalifikowanąrefwykonaniazraw0,125,anowąreferencjąM1jestściślejszeFP64solve. NativeFULL1055alloc/CUDSS47alloc/live0;faktorpeak25,008GB,UVM55,148GB,cgroup58,899GB,GPU-processsample2GiB,minhostavail9,908GB;bezOOM/guard. To jeden punkt/portbenchmarkFEM,niekwalifikacja całejantenyprodukcyjnej ani precyzjiTF32/FP32.

Phase-table fullbeztrace:setup93,545s,GMRES259,460s(zawieraP/coarse),post7,610s+field4,286s. Nativebeforefinalrelease45,342GiBmanaged→8,650GiB (−36,69GiB),cuDSS0porelease;postmanaged24,009GiB,nieutrzymujefaktorów. Stdtableexclusive:LinearSolve29,165s+Preconditioner158,248s+Coarse72,105s≈259,52s,niesumowaćdoGMRESinclusive. UVMtransfers/kernelattribution nadalNOTMEASURED wtejwersji; historyczneNsightlosteventsopisane. M1.4 orazpełnabilansDOF/pamięciM1 pozostająotwarte; nieprzeskakiwaćM2dopóki całabramkaM1niespełniona.


Fallbackregression nowego binarium **PASS**:6solve233iter,13,650s,rawmax9,781e−7,polaE≤3,467e−15/B≤1,502e−13,marker native nieobecny. CuDSS61473620B/live0,UVM331344422B. Regressions33PASS. Brak aktywnych runów po kwalifikacji. Native11,682s cachedbuild; osobnyprobe2,049s/drugibuildcachehit; brakrebuilddeps. M1referencjaW.3uzyskana,profilkerneli/transferów i pełnybilanspamięci nadalotwarte. Po docs-garden/rootdiffreview lokalnycommit (upstreamniepushować).


Domknięcie docs/codeEXP18–19: docs-gardenLuna33testsPASS,rootpoprawiłstareopisyINDEX/M1 i dodałhistorycznepointeryw memory-phases/optimization-baseline. Dodatkowycorelimit0: devrunner+probe --ulimitcore=0:0; prawdziwy pinnedruntime /bin/sh ulimit-c zwrócił0, coredumpctl dla pierwszegopalacesegfaultunieznalazłdumpu. To lokalnylimitkontenera,bezglobalnychzmianOS. Przebudowanywyłącznieten samprobe1,932s,hashbinariumidentyczny; nativemanifestf35d5d0a26e23ec88b4237854bb0a17f41770cbe7a6f1d2fa2832827ba213f86zweryfikowany. Brakfullretry zpowodudokumentacji.


Checkpoint przed commitemEXP18–19: końcowy docs-gardenLunaPASS,rootdiffreviewPASS,33unittestyPASS,docscheckerPASS (istniejące miękkieAGENTS591~tok),gitdiffcheckPASS,source/native/depsmanifestPASS. Wszystkie przygotowane symulacje terminalne, brakpalace-run kontenerów. WorkingstoragewyłącznieRAM/VRAM,corelimit0zweryfikowany;bezpaidcompute. Lokalnycommit,niepushupstream. DalejM1.4krótkiprofildanych/kerneli/UVM i pamięci; nieaktywowaćM2ani nieukończyćgoal bezpozostałychdowodów.


## EXP20 — krótkie okno kerneli/UVM (ACTIVE)

M1.4: Nsight2026.5.1CLI z oficjalnegoNVIDIA225594886B, SHA61829db6392e5c293ada1319df86a97c3356bc810335a1975cb551fcfe3eca08. Wyodrębniony lokalnie bez zmianCUDA/OS; runtime--versionpotwierdza2026.5.1.161. Poprzedni2025profilmiałlostevents; nieliczyć naobecne wyniki. Nowyprofil ma nativeNVTXokno FIRST:COUNT zregisteredrange Krylov sample@palace, a natywny solver synchronizuje CUDA i kończy kontrolowanym wyjątkiem po kilku iteracjach; main przechwytuje go przed niepełnym RF postprocessingiem. Nsight używa --trace=cuda-sw,nvtx oraz --kill=none. Profile jest świadomieczęściowy,nieRFcompletion/PASSsolution.

Najpierwcoax-tinyFP64nativeFIRST1:COUNT2,limit120s,cap60GiB/guard6GiB; potem pełnasiatkaFIRST2:COUNT2,limit600s poAPIprofilePASS,bezpowtarzania całego solve. Tracecuda,nvtx,CPU sampling/contextswitch/off,UMperpagefaultsoff; zliczyćmigracjebytes/kerneliinadzór nadutraconymizdarzeniami. Temp/logbuforyprofilera wtmpfsRAM; zachowaćmałyreportjakozwykływynik(max64MiB),podsumowanieSQLitewstdlib. DaneFEM/baza/macierz nadalRAM/VRAM,corelimit0. Progi przedprofilem:obaNVTXmarkery i2pełneiteracje,niezerowekernel/transferrecordygdyobecne,braklost/mismatch/nieobsługiwanejwersji; liczbęnieznanychprzypisańraportowaćnieukrywać. Nieinterpretowaćczęściowego okna jako całego benchmarku ani sumyGPUtimejako walltime.


EXP20 pierwszy tiny: 9,36s, exit143, 1409 kerneli, ale SQL DIAGNOSTIC_EVENT zawiera ostrzeżenia o możliwie niepełnych CUDA/NVTX events i fallback HW→software. **REJECT dla wiążącej atrybucji**. Pierwotny profile_complete=true był błędem walidatora (sprawdzał stdout, nie SQL). Zachowano oryginalny wynik i osobny root-analysis.json z korektą. Poprawka: SQL warning gate, wymagany clean-stop marker, jawne software tracing, sync+kontrolowane unwind bez SIGTERM, PID celu z dzieci wszystkich wątków. 38 regresji PASS; następny jeden tiny r2, przed full krótkim oknem. Żadnego disk workspace ani zmiany tolerancji.


EXP20 dalsze małe filtry: r2 8,438s clean-stopFAIL (stop-shutdown kończył sesję przed cleanupem celu); r3 8,55s clean-stopPASS po stop/waitall, CUDA+NVTXwarnings; r4 8,44s cudaProfilerAPI+flush nie usunęływarnings; r5 9,41s cały boundedproces bez triggeredcapture: CUDAwarning zniknął, NVTXwarning pozostał. **Wszystkie REJECT profilowania**, brak RF i brak full antena retry. Obecny kod zachowuje prostszy wariant r5: sync+nativeunwind, wholeprocesscapture, okno iteracji wybierane po NVTX offline. TargetPIDtelemetry poprawiona i zmierzona; wszystkie temptrace/SQLite w/dev/shm, final małe raporty zwykłe wyniki. Buildy przyrostowe8,6–8,9s, brak dependencyrebuild. NieaktywowaćM2 na podstawie tych profili.

## EXP21 — rzeczywiste DOF i bilans resident pamięci (PASS zakresu audytu)

`tools/mesh_cost.py --dofs` liczy unikatowe wierzchołki/krawędzie/ściany tetra i materialincidence wRAM, bez plików roboczych; 17,349s, maxRSS663875584B. SHAmesh identyczne W3. 383949vertices/2196005edges/3413357faces/1601320tet; ND2=11218724,H1p2=2579954,RTdegree1=15044031 — wszystkie zgodne z runtime. AIRexclusive6460374DOF=57,586%; pozostaje4758350nonair/shared, nie jest to dowód speedupu. Obecny exteriorsurface94200ND2traceDOF: jeden densecomplex128blok141978240000B (~132,23GiB), vs wcześniejszy RWG-edge estimate11,90GiB dla innej przestrzeni. FEM–BEM wymaga kompresji/FMM lub odpowiednio dobranej mniejszej powierzchni i jawnej kwalifikacji dyskretyzacji.

Bilans na tym samymEXP19gmrespeak55147611962B: cuDSS25008217684 + netVrelease6461985024 + inne linear-solvernetrelease14390057060 + pozostaje9287352194 = dokładniepeak. Vnet odpowiada36complexNDwektorom, podczasgdycapacitylog45; nieutożsamiać host/device/mirrors. Netrelease nie rozstrzyga właściciela każdego bufora, a cuDSS już zawarty wmanaged. Źródła/SHA/checks w artifacts/m1-topology-memory-balance-20261018.json oraz m1-mesh-dofs-20261018.json; docs/topology-memory.md. 41regresjiPASS. M1 nadalotwarty, brakpromocjidefaultów.


EXP20 normalpath regression (profiling OFF):6/6coaxsolvePASS,12,545s,rawmax9,10045e−7; maxΔcomplexS9,09e−16,E3,18e−15/B1,51e−13względemnativetiny-r2. Profilemarkerynieobecne; releasememorygatesPASS. Artefakty artifacts/m1-nsys-normal-regression-20261018 oraz root-analysis.json. 41testsPASS; docs-gardenLuna/rootreview: przywrócono właściwy opis --trace=cuda-sw,nvtx (r5jawnysoftwaretrace, niehistorycznyHWfallback). Dodano gateexit0/noOOM i cleanupRAMtakże przy wyjątkach runnera. M1/goal pozostająaktywne.


## EXP22 — domknięcie bieżącego profilu i alokacji

Directenvr6 i filtrCCCLr7 nieusunęłyNVTXwarning; hipotezy odrzucone. CUDA-only+hostclocktiny r8PASS, ale fullshort z identycznymczasem w hostclockcallee FAILkalibracji; jegoRAMreport216MB/SQLite660MB zostały usunięte zgodnie z limitemretencji64MiB. Nie rekonstruowaćprzyczyny bez surowychdanych. Run267,39s dostarczył aktualnytracealloc,któryniezależyodNsightclock: peak49583124858B,duże49392771376B,unknownsmall190353482B. TriggerComplexParOperatorMult/GMRES,20buforów538043520B; tabelawdocs/memory-audit.md, raportartifactm1-native-current-allocation-audit-20261018.json.

Nativecached8,813s/9,851s/8,619s bezdependencyrebuild. Dodanohostscopes i3labeledCUDAmarkers. Affinefitendpoints/held-outmid+10µsexplicituncertainty, ambiguitymarked zamiastwymuszonejatrybucji. CaptureCUDAProfilerAPIr9tinywarning→REJECT; wholeprocessCUDA-onlyr10tinyPASS9,43s, heldout553ns,6boundarykernels.47testówPASS obejmuje offset/niezgodnyczas/nieliniowymarker i uncertaintyboundaries; progifizyki bez zmian.

Fullshort `artifacts/m1-cuda-affine-antenna-20261018` **profilePASS**: nativeexit0/noOOM/noGuard, cleanpartial4iter, scope2:2@3,50GHz/P2. Clockscale1,00000012239,heldout1127,2ns,containment667,25ns,margines10000ns;4939ROIkernele/1ambiguous/0unmatched,25hostranges. P16,278s(coarse5,490s),orthog0,156s,window17,665s. UVMHtoDpagefault11,549GB,prefetch136,977GB,DtoHeviction146,945GB;D2D15,186GB. Migracjesum295472009216B,nieunikatowepages;czasówGPU/UM/hostniesumować. Reports214MB/SQLite652MBRAMonly,JSON+SHAzachowane. Całyprofil269,94s niejestbenchmarkiemRFspeedup;managed49,583GB,cgroup56,856GB,minhost8,855GiB. Rootanaliza/SHAwm1-cuda-affine-antenna.../root-analysis.json.


DomknięcieM1: normalpath m1-cuda-affine-normal-regression-20261018 complete/fields/releasePASS,6solve13,674s,raw9,10045e−7,E3,0631e−15/B1,5036e−13,ΔS7,813e−16.47tests/docschecker/diffcheckPASS; docs-gardenLuna i rootreview. Brakpromocjidefaultów, brakpełnegosweepa. M1gates zestawione wdocs/milestones/M1.md; aktywnyM2, goalcałośćnieukończony.

## EXP23 — niezależny Maxwell PEC/Mie oracle

Przypięto Bempp-cl a1eaaef9…/MIT i H2Opus cbc7985d…/BSD3; API i granice w docs/maxwell-oracle.md. BemppCPUoracle, nie nativeCUDA; H2Opusreal-onlytypedef, complexintegracja niepotwierdzona. ExaFMMwrapper używa.tmp — nieaktywny, przyszłybackend wymagaRAMaudytu. Prywatny Python3.12.15/uv/JITcache, braknative/dependencyrebuild.

Pierwszylaunch m2-pec-sphere-level1-cold-20261018 FAILexit127/Pid0/0,19s: brakmountaliasuuvPython, fizykaNOTRUN. Rootnaprawiłmount+regresję. Luna wykonała3CPUruny120/480/1920RWGDOF,19,32/19,81/33,89s,exit0/noOOM. PoleMiecomplex8,899/2,254/0,5643%;scatter14,855/3,838/0,96565%;raw≤8,77e−15. Level1/2analyticFAIL,level3PASS, niezmienny1%próg, bezfitufazy/amplitudy. Phase/opticaltheorem/Rayleigh/BesselSciPychecks. Level3RSS452MB/matrix58,98MB; wzorzecCPU, nieantena/ports/interface.

## EXP24 — complex H-matrix i CUDA apply (jakośćPASS, bezpromocji)

Root: geometricalcluster wsparćRWG/exactnear/complexSVDfar, Frobenius1e−6/leaf64/eta2. Przedrunem progiaction1e−5/rawOriginal1e−6/Δsolution1e−3/Δfar-field1e−4. Pierwszargv z kropką kończącą zdanie: argparseFAIL, nicnieuruchomione. Jawnaargvlista→m2-pec-hmatrix-cuda-level3-20261019 ukończony40,868s/noOOM.984bloki/248compressed, compression0,1556s, CPUGMRES170iter/0,6423s. Matrix58,9824→53,5795MB(−9,16%), originalraw1,591e−9/Δsolution2,275e−8/Δfar-field1,096e−11, analyticfield0,5643%; qualitygatesPASS.

CUDAcomplex128cublasZgemvapplyonly: explicitalloc59,0439→53,6414MB;8warmroundtrips0,1010→5,3194ms,52,68×wolniej. Python/PCIe/sync+CUDA, niekernel-only; brakTC/UVM. Denseoracle/kopiepozostająwRAM,RSS1,404GB; brakpeakRAMsaving. Nieintegrowaćper-blockdispatch jako speedupu i nieekstrapolowaćnaantenę. Dalej batch/nativeapply, kompresja/scalableassembly, dielectricMie/FEM–BEMinterface. M2.1–M2.4 nadalniepełne,M3nieaktywny.55unitPASS, bezpaidcompute/closedapps/diskworkspace; Palace/mediumdefaultsbez zmian. Docs-gardenLuna/checker/diffcheckPASS; rootpoprawiłstarylicznik47→55 wtesting i sprawdziłkod/źródła/SHAartefaktów. Lokalnycommitbezpush; goal/M2aktywne.


## EXP25 — plan i wynik

EXP25 plan przed runem (2026-10-19): izolować koszt dispatch od matematyki
EXP24. Ta sama H-matrix FP64/leaf64/eta2/tolerancje; native packing i dwa
kernele CUDA zamiast984Python/cuBLAScall. Porównać exactdense/cuBLASperblock/
native w jednym procesie, action≤1e−5 i dotychczasowe raw/fieldbez zmian;
zmierzyć wszystkie jawne alokacje wraz z metadanymi i round-trip osobno od
GPUeventtime. CachedjednoTUbuild≤120s, oracle≤180s/6GiB/noSwap, RAM/VRAMonly.
Brak promocji anteny na podstawie małego operatora; wynik i decyzja poniżej.

Native2kernelkompilacja1,752s/cachehit; max180soracle40,565s/noOOM. Ta samaeta2: nativeapply0,2114ms vsper-block5,2371ms i dense0,1220ms. HybridGPUoperator/CPUbasisGMRES170iter/0,07770s, rawOriginal1,591e−9/Δsolution2,275e−8. Bezpromocjianteny; niepełnyGPUsolver.


## EXP26 — plan i wynik

EXP26 planprzedrunem: po udanym EXP25native sprawdzić jedną zmianę eta2→4
(szersza dopuszczalność kompresji wyłącznie rozłącznych supports). Leaf64,
SVD1e−6, cała geometria i qualitygatesbez zmian. Sprawdzić dane/meta/workspace,
nativeapply/cublasdense/CPU iGPUoperatorGMRES. Limit180s/6GiB/noextraswap;
budżet natywnej biblioteki bezrebuilda, bezpromocjianteny zmałegotestu.

Eta4PASS/noOOM/40,819s. Matrixdata58,9824→48,7699MB(−17,31%); nativealloc49,5404MBwrazmetadata/workspace. Nativeapply0,1875ms vsdense0,1016ms, więc nadalwolniej. Hybrid0,07494s/170iter/raw3,218e−9; farfielddelta2,681e−11. PeakRAMniespadł, fullassemblydensepozostaje.


## EXP27 — plan i wynik

EXP27 planprzedrunem: kontrola dielektryka PMCHWT/Maxwell na kuli ka1/εr2,94/μr1,
według scaledmultitrace przypiętego Bemppdielectricexample, allRWG/SNC.
Nowy niezależny dielectricMie (transparent/Rayleigh/opticaltheorem/passivity
unitchecks). Najpierwlevel2/960DOF podwójnegośladu, potemlevel3jeśliznaki/faza/
energiapoprawne. Zamrożonypróg1%complexfield/scattering/energy i raw1e−10,
bezfitufazy. CPUonly/6GiB/noextraswap/≤180s, braknativebuildów.

ObaCPUruny technicallycomplete/noOOM:level2/3 35,285/108,849s. Complexfield3,354→0,8495%, scattering6,308→1,6154%: obaanalyticFAILpróg1%, energiapoprawna/raw≤9,08e−15. Geometryauditbezfituprzewiduje−6,2728/−1,6106%scatter; stareFAILzachowane. Danepełnewdocs/maxwell-native-dielectric.md.


## EXP28 — plan i wynik

EXP28 planprzedrunem: EXP27level3pole0,8495%PASS,scatter1,6154%FAIL. Geometryczny
audyt daje Vmesh/Vsphere0,991394, aeq0,997123; Mieaeq przewiduje−1,6106%scatter,
bezfitu. Testować jawną siatkę volume-preserving: skala=(Vsphere/Vmesh)^(1/3),
niezależnaodε/freq/pól, target nadal kula r1 i te sameprogi1%/raw1e−10.
NieprzemianowywaćstaregoFAIL. Najpierwlevel1potem2, każda≤120s/6GiB CPUonly,
sprawdzićzbieżnośćpolazespolonego/energii. Nie jest to zmiana fizykianteny.

Jawnyvolume-preservingflatmeshPASSdlaobu siatek, niezmienionyMier1/progi1%. Level1/2 27,318/35,553s,field0,1764→0,02228%,scatter0,3067→0,03856%,energy1,142e−5→1,286e−7;raw≤5,35e−15/noOOM. Radiusvertex1,046133/1,011541wyłączniezobjętości. Niekwalifikuje near-fieldaniPCB/anteny.


## EXP29 — plan i wynik

EXP29 planprzedrunem: końcowa kontrola integracyjna PECnativeeta4 po dodaniu
dielectricmode/sharedMiehelper/geometryflag. Nie zmieniać matematykiPEC ani
progów. Jeden level3run≤180s/6GiB, cachedSO, kontrolaactualsourcesSHA/native
manifest, raw/complexFF i noOOM. Nie jest to nowy benchmarkanteny.

KońcowaintegracjaactualcodePASS/noOOM/40,784s, field0,5643%/scatter0,96565%. Nativeeta4apply0,2242ms vsdense0,1035ms; residentGPUevent0,1498ms. CPUcompressedGMRES0,5986s vsGPUoperator+CPUbasis0,07777s/170iter/rawOriginal3,218e−9. Rootsprawdziłsource/binarySHA i terminalstate w m2-native-dielectric-root-analysis-20261019.json.58unitPASS; M2/goalaktywne, brakFEMinterface/scalableassembly/antenna speedup. Docs-gardenLuna/checker/diffcheckPASS; rootreview kodu/manifestów/wykonanychźródeł zakończony. Nativecache i referencjaPalace zachowane, brakpushdo upstream. Goal/M2nadalaktywne.
