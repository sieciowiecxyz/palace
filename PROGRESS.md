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
- EXP30–31: actualMFEM4.9ND1/Bemppcoupling ze zbieżnością, trace/pair~1e−15/energyPASS. Całkowity1%E/HFAIL:6,12/5,79%, comparatorFEM6,18/5,82%; Δcoupled–FEM0,57/0,76% niekwalifikujeND2/anteny. docs/maxwell-coupling.md.
- EXP32: primalRWG/SNCGramtracirank90/120,330/480; odrzucićinwersjędoprowadzeniaND2projection. DualRWG/RBCfullrank/κscaled≤2,93, physicalpairing/transforms/constanttracePASS. Plane-traceRWG0błąd20,99→10,43→5,16%, nadalnieND2mortar. docs/maxwell-coupling.md.
- EXP33: actualglobalMFEMND2/faceDOFtransforms/physicalbasis/CSR, Dirichletplane-waveE/H0,1505/0,3317%PASS na8936DOF/1280tet.5,514s/433MB/CSR8,79MB; interpolacjaH1,468%FAIL. BrakcoupledBEM/antenna speedup; docs/maxwell-nd2.md.
- EXP34: actualND2/BC-RBCmortar/localbasisassembler/sparseSchurPASS, currentwholefieldFAIL17,74/15,22→10,07/5,64% mimo raw/far/energyPASS. NativeT/K≤1,22e−16, tinydenseSchur≤1,94e−14; brakpromocjianteny. docs/maxwell-nd2-coupling.md.
- EXP35–37: duality/trace diagnostics i niezależny brzeg. Magnetic F2/B3 E/H0,560/0,751% PASS, F3/B3 0,358/0,904% PASS (H gorsze). Root source/SO/state/quality verification PASS; docs/maxwell-trace-duality.md. Dielectric transmission/rezonanse/scalable assembly/koszt pozostają otwarte.
- EXP38–41: dielectric eps2,94 wykonany, centroidscreening FAIL E/H1,092/1,320% względem PMCHWTB4/q12. RefEchange0,408%>0,3%; potentialB4q8/q12<1e−6. Raw/far/energy małe nie kwalifikują pola. Zachowane NPZ do dalszej analizy bez solve; docs/maxwell-transmission.md.
- EXP42–43: saved-solution volume replay640/2240pts. Degree5 E/H2,888/1,612%, refchange1,945/1,158%, potentialqdelta~7,4e−4 FAIL. Root SHA/state/complexintegral verificationPASS; H_FEM własnanorma q2/q5 zgadza się2,11e−15. Następna hipoteza adaptive near-panel correction; niepromować i nie skalować ślepo referencji.
- Praca RAM/VRAM. FEMcap60GiB/guard6GiB; nowe małe oraclecap6GiB/noadditionalSwap, noOOM. Bezpaidcompute/closedapps; cachekompilacji osobno.80testsPASSwpinnedenv; systemowo67PASS/13SKIP(SciPy). Kod Palace/medium bez zmian.

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
2. M2: volume replay EXP42–43 FAIL, near potential quadrature niezbieżna. Następny mały panel-control na tej samej kwadraturze/DOFmap co pinned Bempp, potem adaptacyjna korekcja tylko near panels. Reużywać saved solutions; nie globalq/B5. Dalej pełne pola/dielektryk/rezonanse/koszt; M2 otwarty bez promocji/cloud.
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


## EXP30 — plan i wynik

EXP30 planprzedrunem: rzeczywisty mały MaxwellFEM–BEM transparent ε=μ=1/ka1.
Instalowany MFEM4.9 ND1 integratorymasy/curlcurl, niezależnyWhitneycheck,
punktowe mapowanie E×n→RWG ze znakami i1/edgeLength, osobny check
FEMboundarypairing=R^TGramSNC/RWG. Nonsymmetric1rowCalderon+FEMGreen, CPUdense.
Pierwszylevel1(20tet/20boundarytri), potemrefinebez zmianywielościanu.
Analytic1%E/H_L2, absfar<0,01, raw1e−10, map/pair1e−12,q4vs6delta1e−6.
CoarseFAILnieoznaczaPASS; osobnyFEMzexactDirichlet pozwalaoddzielićFEerrorodcoupling.
ND1wyłącznieprobe, produkcyjnymediumND2bez zmian; nieGPU/ports/antennaqualification.
Limit180s/6GiB/noextraswap/RAMonly, bridgeTU2,597s+cachehit, bezPalacerebuild.
PierwszybridgebuildFAILbrakcudss.h; dodanoistniejącyinclude/opt/cudss/include,
niebudowano zależności.61unitPASS. Research: Bemppfenicsnc1trace i Maxwell
multitraceexample, MFEMheaders/notes, Hiptmair2007stabilizedcoupling (doocenystability).

Bridge2,597s/cachehit,MFEMv4.9release/GetGitStrpusty. Level1/2CPUruny30,793/31,800s,noOOM/exit0.20/160tet,20/80tri,FEM42/254,BEM30/120. MFEM↔Whitney/trace/pair≤1,35e−15, raw1,14e−15/8,34e−15. CoupledE/H20,45/21,73→11,74/11,44%; comparatorFEM21,36/21,92→12,00/11,56%. Zbieżnośćpoprawna, oba1%analyticFAIL. Poziom2far6dir0,006323PASS. Niepromować.


## EXP31 — plan i wynik

EXP31planprzedrunem: poEXP30level1/2map1e−15 i zbieżnościE/H20/22→11,7/11,4%
(FEMDirichlet21/22→12,0/11,6%) uruchomić refinement2wtejsamejgeometrii.
1%E/Hnadalobowiązuje, niepromowaćND1 przezsamrawPASS. Dodaćpełniejszyfar-field
16×24+6kierunków i optycznybilansenergii względemπincpower (gate1e−3), nadal
absfar0,01. DrugiCalderonrowosobno zexactanalyticweakRHS+staryinterpolatedRHS.
CPUdense6GiB/max180s; mainmatrix/FEMmediumproductionbez zmian.

Level3CPUrun37,742s/1280tet/320tri,FEM1748/BEM480, matrix79,424MB/RSS827MB. Map/pair/MFEMmatrix≤1,46e−15, raw4,74e−14; actualE/H6,116/5,785%vsDirichlet6,177/5,823%: 1%fieldFAIL. Δcoupled–FEM0,5691/0,7571%normalizowanedoexactincident, nieboundcałkowitegobłędu. q4vs6delta2,58e−10; niewymuszonyCalderonrow0,7126%interpH/0,6752%exactweakH. Far384+6max0,001622, σscat7,479e−6/σext9,450e−6,energyerror/π6,275e−7PASS. NoOOM/exit0. RootactiveSource/binarySHA/terminalstate wlevel3/root-analysis.json; dalszeND2globalspace/mortar/stabilnośći kosztanteny.62unitPASS; docs-gardenLuna/rootreview/checker/diffcheckPASS. Lokalnycommitbezpush. Goal/M2aktywne.

### EXP32 — Gram RWG/SNC vs RWG/RBC, prerejestracja i wynik

Hipoteza: nie odwracać Gprimal bez małego testu rank/condition; sprawdzić dualRBC
przed ND2mortar. Ten samwielościan, poziomy1→2→3 poPASS, bezFEMsolve/GPU/build.
Dokładneargv wcommand.json: `bempp_oracle.py run artifacts/m2-dual-pairing-level1-20261019
--physics pairing --level 1 --seconds 120`, potem level1-fixed/2/3 do nowychkatalogów.
Cap6GiB/4CPU/memory-swap=memory/rootRO/networknone/tmpfs, istniejącyJITcache.
Przerejestrowanechecks: independentphysicalquad+BCtransforms/dualskewadjoint≤1e−12,
Gdualfullrank/κmassdiag<100, constanttrace/residual≤1e−12. Plane-tracediagnostic,
analytic_targetfalse, niezmienioneM2gates.

Pierwszylevel1FAIL23,311s/exit1/noOOM: brak() dla metodybarycentric_representation.
Błądroota poprawiony bezzmianbackendu/tolerancji; braknumerykidla failedrunu.
Poprawione3runy25,512/25,345/25,919s,RSS419/420/442MB,exit0/noOOM/interfacePASS.
Gprimalrank30/30→90/120→330/480, κraw2,25e17/2,85e17 na wyższychpoziomach:
**REJECT osobnejinwersjiGprimal dla ND2projection**. Nieunieważnia toND1bloku,
który nieodwracaGprimal. Gdualrank30/30,120/120,480/480 iκmassdiag2,154/2,720/2,922.
Weakvsphysicalquadrature≤1,32e−15, Gdual=-Greverse^T≤1,81e−16, exactconstanttrace
L2≤1,13e−15; plane-traceRWG0błąd20,994→10,433→5,157%. To ograniczeniereprezentacji,
nie kontrolaND2/pólMaxwella. Rootpotwierdziłcase/fem/referenceSHA/terminalstate
w artifacts/m2-dual-pairing-root-analysis-20261019.json. NastępneactualglobalMFEMND2,
plane-waveDirichletkontrola, fizyczneB/Rmortar i rozdzieleniebłęduFEM/powierzchni.
65testsPASSwpinnedenv,systemowo62PASS/3SKIP(SciPy); docs-gardenLuna/rootreviewPASS,
historycznylicznik62wEXP30–31doprecyzowany. Checker/diffcheckPASS, lokalnycommitbezpush.
Brakpromocji/natywnegorebuilda/płatnegocompute; M2/goalaktywne.

### EXP33 — prerejestracja: actual global MFEM ND2

ZachowaćprodukcyjnymediumND2, nieprzedłużaćND1refinement. Nowy małyCAPI
`mfem_global.cpp` używa istniejącego MFEM4.9/ND_FECollection(2), globalFESpace,
rzadkichBilinearForms oraz GetElementDofs/InvTransformPrimal dlafaceDOFs.
BuildtylkodwaTUs/ccache i linkSO, limit120s, bezrebuildazależności/Palace.
Nowycase `--physics nd2`: ten samzamkniętywielościan, k1/eps=mu1,
exactplanewaveEx=exp(iz),Hy=exp(iz), DirichletzprojectedanalyticboundaryDOFs.
Poziom1→2→3 poexecutionPASS; cap6GiB/4CPU/tmpfs/noaddedSwap/deadline120s.
Gatephysicalbasis/globalmatrixquad/constant/linear/GridFunction≤1e−11,
musząwystąpićnonidentityface transforms. CałepolaE/H≤1%, rawinterior≤1e−10,
q4vs6delta≤1e−6. SparseCSR/lokalnebasiswektorywRAM; brakdenseglobalFEM.
Rzeczywisteargv `python3 tools/experiments/mfem_bridge.py build`, potem
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-global-nd2-level1-20261019
--physics nd2 --level 1 --seconds 120`. Wyższepoziomydonowychkatalogówpoanalizieroota.
Level1takżeregresja staregoND1CAPI. To odniesieniedlapóźniejszegoBCmortar,
nie FEM–BEMsolve/exterior/ports aniantenna speedup. M2/goalaktywne.

EXP33pierwszybuildPASS3,361s, nowySO35dea8a9…; level1containerexit0/noOOM,
runnercompletefalse0,527s. ND2184DOF/20tet, checks≤4,44e−15 iND1legacyPASS;
E/HDirichlet2,204/3,342% (projekcjanie-solve2,451/5,315%). Raw6,83e−16,
aleq4vs6delta3,19e−6>1e−6: diagnostycznyfiltrFAIL, nie wolnopromować.
Korekta: wliczaniu błędu pól użyć dokładniejszejkwadraturyq6 z niezależnymq8,
prógdelta1e−6 bez zmian, poprzedniąróżnicęq4vs6 nadalraportować; niezmienia
toND2/siatki/operatora ani tolerancji pól. Dokładniejszyaudyt licznika
faceorientations: MFEMIsIdentity dotyczyklasytransformacji, nie danegoelementu;
liczyć faktyczne InvTransformPrimal(I) != I. To wymaga jednegoprzyrostowego
rebuilda wyłącznie małegoCAPI. Nowyrun `artifacts/m2-global-nd2-level1-q6-20261019`.

EXP33q6: rebuild3,310s/nowySO1abaa83a…; level1/2/3exit0/noOOM/executionPASS,
runner0,536/1,051/5,514s, RSS281/288/433MB. DOF184/1228/8936,boundary100/400/1600;
actualnonidentitycells19/147/1167, matrixquad≤8,86e−16, polynomials≤3,56e−14.
DirichletE/H2,2046/3,3413→0,5910/1,0541→0,1505/0,3317%: level3analyticPASS.
Oddzielna interpolacjaE/Hlevel3=0,1860/1,4681% (HFAIL), nie ta samareferencja.
Raw6,83e−16/1,73e−15/4,09e−15,q6vs8≤6,94e−12. M/KCSR148552/1128424/8793480B,
sparseLU0,000327/0,005876/0,5362s. Rootzweryfikowałaktywnesource/binarySHA/
terminalstate w artifacts/m2-global-nd2-root-analysis-20261019.json.
69testsPASSwpinnedenv,systemowo63PASS/6SKIP. DalejB/Dmortar/Schur/coupledND2,
bezprzenoszeniażądań1%na samąinterpolację ani deklaracjiantenna speedup.
Docs-gardenLuna/rootreview/checker/diffcheckPASS; dodatkowycachecheck
`MFEM bridge unchanged: cached library retained` bezrekompilacji.
Lokalnycommitbezpush, goal/M2aktywne.

### EXP34 — prerejestracja: actual ND2/BC-RBC mortar i sparseSchur

Rootprojektuje `bempp_nd2_coupling.py`: B=<vND2,BC> i niezależnie
D=<RBC,vND2×n>, pełnefaceDOF/barycentrictransforms. Gate D=−B^T,
normal/coordinates/interiortangentleak≤1e−12; exactconstanttrace≤1e−12,
lineartraceerrorraportowany (RWG0nieND2trace). GdualR=D zamiastGprimalinverse.
FEM A=K−M pozostajesparse; [A,−ikB; C*R,T][u,h]=[0,rhs], C=G/2+Kbem.
Schur=T+ik*C*Gdual^-1*D*A^-1*B; RHSbloki16, nie alokowaćdenseglobalFEM.
Tylko≤512FEMDOF sprawdzićcałyfullcoupled układ≤1e−10. Na większymreference
boundedDirichlet zEXP33+independentwholeE/Hplane-wave. TargetE/H≤1%, raw≤1e−10,
q6vs8≤1e−6, absolutezero-scatterfarfield≤0,01 i energyerror/π≤1e−3.
PrzypiętyBempp `electric_dual` używa RWG/BC i RBC/SNC, kontrolaAPIwsource.
Limit180s/6GiB/4CPU/tmpfs/noaddedSwap, cachedMFEM/JIT, brakbuilda/GPU/paidcompute.
Dokładnyargv: `python3 tools/experiments/bempp_oracle.py run
artifacts/m2-nd2-bc-coupling-level1-20261019 --physics nd2-coupling --level 1 --seconds 180`.
Level2/3 dopiero po rootanalizie. BrakCFIE/stabilizacji/transmission/ports;
to transparentprobe, nie promocja solveraanteny ani zamknięcieM2.

EXP34pierwszylevel1FAIL15,625s/exit1/noOOM. Mortarvalidated12,261s, ale
standardowyBemppDenseAssembler odrzuca requires_dof_transformation dlaBC/RBC.
Brakcoupledfields/Schur/farfieldwyników. Źródłoprzypiętegoassemblera potwierdza
tenbrak, niezmieniaćupstreamenv/nieomijaćchecku. Korekta: lokalnycustomassembler
używa tychsamychregular/singularMaxwellkernels wmake_localised_space, potem
Qtest^T*A_local*Qtrial, gdzieQ=map_to_localised*dof_transformation. Kontrola
punktowalocal/globalbasis≤1e−12, dodatkowo publicznyMaxwellRWG/SNC vs ta ścieżka
dla obuT/K≤1e−12 wlevel1. To kosztownylocaldense tylko małyprototyp, nie scalableBEM.
Poprawionyrun `artifacts/m2-nd2-bc-coupling-level1-local-20261019`, te samebramki/limity.

EXP34locallevel1exit0/noOOM/executionPASS35,789s/RSS680MB. Mortaradjoint1,79e−16,
constanttrace8,74e−16, lineartrace34,055%. CustomMaxwellvsnativeT/K≤1,22e−16,
pointwisemaps≤3,37e−16. Schurraw3,37e−15, tinyfullcrosscheck1,93e−14;
FEM184/BEM30, lokalneBEM360²complex128=2,074MB, reducedSchur14,4KB.
CoupledE/H17,743/15,224%FAIL vs boundedDirichlet2,205/3,341%; q6vs8≤8,06e−13.
Spuriousfar0,005935/energy3,26e−7PASS — far/residuum niekwalifikującałychpól.
Następnylevel2 przytejsamejfizyce/180s/6GiB do
`artifacts/m2-nd2-bc-coupling-level2-local-20261019`; zbieżnośćdecydujeolevel3.

EXP34level2exit0/noOOM/executionPASS43,671s/RSS718MB. CoupledE/H10,072/5,645%FAIL,
Dirichlet0,591/1,054%, deltaE/H10,111/5,827%. Adjoint/interiortangent/normal≤8,28e−16,
constant9,79e−16, linear16,634%, raw1,14e−14, qdelta9,80e−15. Far0,002338/energy7,20e−7PASS.
FEM1228/BEM120, Schur230,4KB, lokalneBEM1440²=33,178MB/operator (144×finaldata).
Do mortaru12,33s/T27,92s/C38,40s/Schur38,43s/pola38,84s; setup/JIT/assembly
dominują, nieLU0,03005s. Nieekstrapolowaćczystegokernelczasu z 2poziomów/JIT.
Rootaktywnesource/helper/binarySHA/terminal/FAILsprawdzone w
artifacts/m2-nd2-bc-coupling-root-analysis-20261019.json. Level3NOTRUN: następne
rozdzieleniesamejgranicyprzyustalonymFEM, najpierwcheaptrace-spaceprobe.
71testsPASSwpinnedenv,systemowo63PASS/8SKIP; docs-gardenLuna/rootreview/checker/diffcheckPASS.
Wynikizapisane w lokalnymcommicie, bezpushdo upstream.
Brakmatched-errorporównania/promocjianteny/M2closure; goalaktywny.

### EXP35 — prerejestracja: trace spaces bez nonlocalBEMsolve

Jednymprocesem1→3surfacehierarchy: RWG/RBC iBC/SNC dualprojection vs bestL2
massprojection w tychsamychprzestrzeniach. ConstantEx i planeEx/Hyexp(iz).
NiezakładaćBCconstantreproduction; zmierzyćosobnobestapproxerror i wpływtestduality.
Gateweakresidual≤1e−12/q4vs6≤1e−6, RWGconstant≤1e−12, massSPD i bestL2
niegorszeoddual o>1e−9. Błędy powierzchniowenieMaxwell1%gate/nieHdivstability.
`trace_load/projection_error` otrzymują orderarg default4 (stare wywołaniabez zmian),
nowypolynomialtest wunit. TylkoCPU6GiB/4CPU/tmpfs/noaddedSwap, limit120s,
cachedBempp/JIT, bezMFEMCAPI/buildów/GPU/paidcompute. Dokładnyargv
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-trace-space-hierarchy-20261019
--physics traces --level 3 --seconds 120`. Wynikwybierzenastępnąprzestrzeń/mortar,
niezmieniaM2gates/medium/productiondefaultów.

EXP35exit0/noOOM/executionPASS18,643s/RSS347MB. Poziomy1/2/3planeE/Htrace:
RWGdual≈20,99/21,02→10,43/10,41→5,16/5,16%, bestL2≈19,63→10,02→5,06%.
BCdual≈48,94→31,24→20,87%, bestL2≈46,79→30,14→20,09%. ConstantBCdual46,87→30,35→20,57%,
bestL245,33→29,44→19,81%, RWGconstant≈1e−15. Weakresidual≤1,97e−16/qdelta≤5,17e−11.
BCdualitytestniejestgłównympowodemdużegobłęduL2: bestL2pozostajedużo gorszeniżRWG.
ToniedowódHdivstability/coupledcausality. WEXP34h=BC, więc następnyizolowanykontrafakt:

### EXP36 — prerejestracja: magnetic_dual przy stałymFEMlevel2

Ten sam ND2/FEM1228/160tet i BEM120/80tri coEXP34level2. Zmiana tylko spaces:
upstreammaxwell.py `magnetic_dual`: t=BC,h=RWG,testSNC (zamiastRWG/BC/RBC).
G=<SNC,BC>fullrankzEXP32, physicalB=<v,RWG>, D=<SNC,v×n>=−B^T,
G*R=D. C/T/Green/Schur/eps/mu/k/medium/1%E-H/raw/far/energyprogi bez zmian.
BCnieodtwarzaconstanttracepunktowo(EXP35), więc raportowaćerrorbezzerowania;
sprawdzić exactconstantweakloadG*R*u0=<SNC,E0×n>≤1e−12. Dla defaultowegoelectric
nadalwymagać także exactconstantpointwise≤1e−12. Brakpoluzowaniawholefieldgate.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-magnetic-dual-level2-20261019
--physics nd2-coupling --duality magnetic --level 2 --seconds 180`.
CPU6GiB/4CPU/tmpfs/noaddedSwap/cache, bezbuild/GPU/paid. Wynikiwybierajądalszy
testpowierzchniprzyustalonymzakwalifikowanymFEM, niepromocjęanteny.

EXP36pairedlevel2exit0/noOOM. MagneticdualE/H1,424/2,884%FAIL vs electriccontrol
10,072/5,645%FAIL, Dirichletwobydwu0,591/1,054%. Magnetic40,540s/RSS706MB vs
electric43,659s/RSS718MB. Mortar/constantweak≤6,88e−16, raw3,05e−14,
far4,586e−4/energy3,606e−7PASS. BCconstantpointwise30,351% jawne, niezerowane.
T_RWGSNC240²=0,922MB zamiast1440²=33,178MB; K_BCSNCnadal33,178MB. Przestrzeń
hRWG mocnopomaga przytej samej objętości, lecz wholefield1%nadalnieosiągnięte.

### EXP37 — prerejestracja: tylko powierzchnia przy stałymFEM

MagneticdualFEMlevel2/1228DOF/160tet bez zmian; surface2→3, BEM120→480DOF,
80→320tri. Nowygeometryparentlookup po centroids i kontrolawszystkich3vertices
finerBEMface wFEMboundarytriangle. NieintegrujeBEMfaceprzecinającejFEboundaryface:
wymaga nestedrefinement, przeciwny/coarsersurface odrzucany. Unit4childperface,
wronggeometry/crossedfacesrejection. CałkiB/Dnadal≤1e−12; niezmienioneprogi/fizyka.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-magnetic-f2-b3-20261019
--physics nd2-coupling --duality magnetic --level 2 --surface-level 3 --seconds 180`.
CPU6GiB/4CPU/tmpfs/noaddedSwap/cache; brakbuild/GPU/paid. To izolujebłądgranicy;
FEM2DirichletH1,054%samnieprzechodzi1%, więc całościowypromisingrun wymaganastępnie
kwalifikowanegoFEM3 i takiej samejpowierzchni. Nieobniżać1%gate.

EXP37F2/B3exit0/noOOM/execution+analyticPASS91,437s/RSS1,323GB.
CoupledE/H0,5603/0,7512%, samFEMDirichlet0,5910/1,0541%, delta0,2906/0,8702%.
AnalitycznepolaPASSniezależnieodgorszegointerpolowanegoDirichletH; nieodrzucać
poprawnegorozwiązaniadlatego, żeten comparator ma1,054%. Mortar≤1,50e−15,
constantweak5,86e−16, raw5,88e−14, qdelta1,72e−13; far6,46e−5/energy3,33e−8PASS.
LocalE14,746MB, localK530,842MB, Schur3,686MB; nieoszczędnośćpeakRAManteny.
Następnykontrafakt przyUSTALONEJBEMB3: zmienićwyłącznieFEM2→3,
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-magnetic-f3-b3-20261019
--physics nd2-coupling --duality magnetic --level 3 --surface-level 3 --seconds 180`.
Te sameprogi/eps/mu/k/6GiB/4CPU/tmpfs/noaddedSwap; tokwalifikuje zbieżnośćobjętości,
nieporty/dielektryk/antennaspeedup. Nieluzować1% i niezamykaćM2na1transparentprobe.


EXP37 F3/B3: exit0/noOOM, analytic+execution PASS, 95,902s/RSS1,345GB.
E/H0,3577/0,9042%; raw2,312e−13, qdelta2,758e−16. E lepsze niż F2/B3,
H gorsze (0,7512→0,9042%); nie ogłaszać monotonicznej poprawy obu pól.
Final paired F2/B2 na tym samym aktualnym kodzie: electric10,072/5,645% FAIL
43,925s/RSS722MB; magnetic1,424/2,884% FAIL40,861s/RSS708MB. Wyniki zgodne
z kodem sprzed parent lookup (Δpól<1e−12). Wszystkie stany terminalne i SHA
case/helperów/MFEM SO, mortar/raw/quad/energy i rozdzielenie PASS/FAIL sprawdzone
przez root w artifacts/m2-trace-duality-root-analysis-20261019.json.
Pierwszy verifier odrzucił intencjonalne null nd_api_sha256 w traces (brak NDbridge);
poprawiono sprawdzanie stosowalnych hashy, bez zmiany progów fizycznych.
Dokumentacja EXP35–37: docs-garden read-only tej samej Luny i root review PASS;
74testsPASS w pinnedenv, system64PASS/10SKIP, checker/diffcheckPASS.
Bez rebuilda Palace/deps, zmian medium i promocji; lokalny commit bez push.


### EXP38 — prerejestracja: transmisja, niezależny PMCHWT na tym samym wielościanie

Nowy izolowany bempp_transmission.py, bez zmian Palace/MFEM/medium. eps=1 najpierw
sprawdza konwencję exp(-iwt), E=K*t+T*h/rho i H=K*h-rho*T*t przez porównanie
z analityczną falą. Potem eps=2,94: FEM A=curlcurl-eps*M i ten sam zewnętrzny
Calderon; niezależny PMCHWT ma dwa operatory wnętrza/zewnętrza oraz brak mortaru.
Pierwotne źródło: pinned Bempp examples/maxwell/maxwell_dielectric.py i
bempp_cl/api/operators/potential/maxwell.py (commit a1eaaef9...). Publiczne fetch
przez web niedostępne; zweryfikowano istniejący przypięty lokalny checkout.
Kontrola centroidów wszystkich tetra z wagami objętości to screening, NIE pełne
L2 pól. Raport ma analytic_target_passed=false bez względu na screening, żeby
nie zaliczyć M2 samymi próbkami. PMCHWT B1/B2 pozwala zmierzyć niepewność
referencji; screening wymaga <1% probe error, <0,3% zmiany referencji, raw<1e-10,
energy/pi<1e-3, farfield<1% (dla eps1 kontrola analityczna). Nie luzować K.

Pierwszy dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-transparent-f2-b2-20261019 --physics transmission --level 2 --surface-level 2 --epsilon-r 1 --seconds 180`.
6GiB/4CPU, bez dodatkowego swap, temp/cwd tmpfs, bez GPU/płatnego compute.
Niezmieniony cached MFEM SO. Unit76PASS; nowa walidacja eps/siatki przed alokacją
oraz zespolonego weighted probe error. Jeśli znaki/reference nie przejdą,
nie uruchamiać eps2,94 przed analizą; nie przechodzić doM3.


EXP38: exit0/noOOM51,407s/RSS761MB, raw3,05e-14 ienergy/pi3,61e-7.
ScreeningFAIL: coupled analytic centroidE/H0,6156/1,3266%, PMCHWT B2analytic
E/H2,6213/2,6363%, refB1→B2change13,678/13,651%. Nie traktować tej referencji
jako dokładnej. Przed eps2,94 oddzielić niedokładność prądów BEM od potencjałów.

### EXP39 — prerejestracja: tylko referencja, bez powtarzania coupled solve

Ten sam zestaw160tetcentroidów (FEMsampling2), PMCHWT B2/B3 i te same solved
currents oceniane potential quadrature4/8. Nie zmieniać boundaryassembly q4,
fizyki eps=1 ani punktów. Zmiana jednej kwadratury po solve rozdziela jej wpływ
od zmiany siatki. Jeśli q4→8 mocno poprawi pole, trzeba osobno zakwalifikować
kwadraturę; jeśli nie, dominuje błąd discretization/reference. Bez promocji.
Zapis małych wyników pmchwt-level*.npz pozwoli uniknąć ponownego assembly przy
następnej diagnostyce. To zwykły artefakt wyniku, nie roboczy offload solvera.

`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-reference-q4-q8-20261019 --physics transmission --level 2 --surface-level 3 --epsilon-r 1 --reference-only --seconds 180`.
6GiB/4CPU/tmpfs/noadditionalSwap, bezGPU/build/płatnego compute.


EXP39: executionPASS34,290s/RSS456MB/noOOM. B2 q4E/H2,621/2,636%,
q8 1,824/1,830%; B3 q4 0,216/0,217%, q8 0,158/0,158%. Oba czynniki
siatka oraz potentialquadrature wpływają na pole. PMCHWT raw≤4,72e-15.
Root sprawdził stany i błędy B3<0,3%; nie jest to globalL2 ani kwalifikacja
transmisji. Użyj potentialq8 dla kolejnego porównania, boundaryassemblyq4 bez zmian.

### EXP40 — prerejestracja: właściwy kontrast eps=2,94

FEM2/BEM3, zmiana A=curlcurl-eps*M, zewnętrzny Calderon bez zmian. Independent
PMCHWT na tym samym wielościanie, B2/B3 i potentialq8. Porównać kompleksowe
E/H w160tetcentroidach oraz farfield i bilans energii. Raw<1e-10/mortar<1e-12;
screen1% probes/far, refchange0,3%, energy/pi1e-3; pełneL2 i kwadratury nadal
osobną bramką, analytic_target_passed=false. Nie promować tylko za zgodnośćS.
Zapisz mały wynik coupled-solution i prądy PMCHWT do ponownej analizy bez solve.

`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-eps294-f2-b3-20261019 --physics transmission --level 2 --surface-level 3 --epsilon-r 2.94 --seconds 180`.
6GiB4CPU/tmpfs/noaddedSwap, bezGPU/cloud/build. Jeśli nieprzejdzie, ustalić czy
referencja, FEM czy sprzężenie; bez ślepego podnoszenia obu siatek.


EXP40: exit0/noOOM/executionPASS112,166s/RSS1,309GB. ScreeningFAIL: E/Hweighted
centroids0,8851/1,3597%, farrelative0,1116%, raw5,14e-14, energy/pi1,02e-7.
RefB2→B3E/H3,2015/1,9748% — referenceuncertainty ponad0,3%. Root independently
recomputed complex probe differences from npz, positive volumeweights4pi/3 and
state/helper/SO/current-case hashes in artifacts/m2-transmission-root-analysis-20261019.json.
Nie przypisywać różnicy wyłącznie FEM i nie promować. Eksperyment nie kwalifikuje
pełnegoL2/anteny. Zapisane rozwiązania nie wymagają ponownego coupled solve.

### EXP41 — prerejestracja: zwiększyć tylko niezależną referencję

Reference-only eps2,94, te same160centroidów, B3/B4, potentialq8/q12 na tych samych
prądach. B4 uzyskane przez płaskie1→4 subdivisionB3, bez radialprojection; unit
sprawdza1280tri/1920edges, closed2incidence, volume4pi/3 i outward normals/planes.
Nie zmieniać FEM2/BEM3 kandydata, nie powtarzać jego assembly/solve. Po runie
root porówna zachowane probes z nową referencją i sprawdzi jej zbieżność.
Łączny PMCHWTB4ma3840currentDOF, denseblock235,93MB; limit6GiB/180s utrzymany.
77unitPASS. To koszt jednego rozstrzygającego referencecheck, nie większy medium.

`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-reference-b3-b4-20261019 --physics transmission --level 2 --surface-level 4 --epsilon-r 2.94 --reference-only --seconds 180`.
BezFEMsolve/nativebuild/GPU/cloud/swap. Jeśli referencechange nadal>0,3%,
raportować niezbieżność; nie luzować progu ani na ślepo zagęszczać doB5.


EXP41: exit0/noOOM126,619s/RSS1,145GB. PMCHWTB4 3840DOF/235,93MBblock,
raw8,39e-15; B3→B4E/Hreferencechange0,4076/0,1657%. B4q8→q12delta
0,0000830/0,0000837% (<1e-6 względnie); potentialquadrature mały wpływ,
referenceE nadal>0,3%screen. Root independentweightedcomparison zachowanych
EXP40probes vs B4/q12: E/H1,0923/1,3205%FAIL1%, bez nowego coupled solve.
Stan/SHA/helpery i błędy zweryfikowane w artifacts/m2-transmission-refinement-analysis-20261019.json.
To centroiddiagnostic, nie globalL2 i nie measuredantenna memory/speedgain.
77unitPASS w pinnedenv, system65PASS/12SKIP. Docs-garden read-only tej samej
Luny, root review, checker i diffcheck PASS. Lokalny commit bez push.
Bez rebuilda/deps/paidcompute/GPU. M2 ACTIVE, bez promocji solvera.


### EXP42 — prerejestracja: volume replay bez nowego solve

Poprzedni goalturn był PROGRESS: zapisano EXP38–41 i commit c240a7c. Teraz
bempp_volume.py odtwarza savedF2/B3 i PMCHWT B3/B4 bez nowego BEMassembly/LU.
Obecny MFEMhandle przytworzeniu montuje małe serialmass/curl; nie eksportujemy
ich ani nie faktoryzujemy. Nie twierdzić, że cały postprocessing nie ma assembly.
Reguły dodatnie degree2(4pts/tet) i degree5(14pts/tet), dane z MFEMv4.9
fem/intrules.cpp; primarysource pobrano urllib do istniejącego sourcecache
(webfetch niedostępny). Unit sprawdza wszystkie barycentricmonomials do stopnia.
Pierwszy tani filtr degree2:160tet*4=640points, weights sum4pi/3. Te same punkty
obejmują całą domenę. Reference B3q12, B4q12 i B4q16: osobno meshchange i
potentialquad. Chunk128points ogranicza pamięć, nic nie migruje do SSD/swap.

Zamrożone screening1%volumeE/H,0,3%referencechange,1e-6potentialquad, a następnie
osobno degree2/5agreement1e-6. analytic_target_passed=false; volume quadrature
nie jest jeszcze zbieżną całką, brakpromocji. Runner wiąże wszystkieinputSHA,
state/noOOM/role/material/unchangedFEMhelpers/SO przed uruchomieniem.
80unitPASS. Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-volume-degree2-20261019 --physics volume --level 2 --volume-degree 2 --volume-inputs artifacts/m2-transmission-eps294-f2-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.
6GiB4CPU/noaddedSwap/tmpfs, bezGPU/cloud/rebuild. Jeśli timeout, zachowaćdiag,
nie ponawiać bezdiagnozy. Degree5 tylko po informacji o koszcie/kompletności.


EXP42 exit0/noOOM52,526s/RSS493MB,640positivevolumepts/4pi3. Root independently
recomputed volume E/H2,1518/0,8630% from npz. RefB3→B4 E/H1,0746/0,4374%
FAIL0,3%. Potentialq12/q16 E/H7,37e-7/7,67e-7 PASS1e-6 at these points.
ScreeningFAIL: centroid1,09%E underestimated volumequadratureE; don't promote.
Phases: MFEMfields0,062s,B3q12 13,219s(includesinitialJIT),B4q12 14,876s,
B4q16 23,233s. Retained caches, no BEMassembly/solve.

### EXP43 — prerejestracja: oddzielna kontrola degree5

Te same zapisane wektory/material/geometry, zmienić tylko volume_degree2→5.
2240points(14/tet), symetrycznepositiveMFEMruledegree5; sourceURL
https://raw.githubusercontent.com/mfem/mfem/v4.9/fem/intrules.cpp i lokalnycache.
Prognoza~150–180s (steadyPotentialcost*3,5 + initialJIT), limit nadal180s,
6GiB4CPU/noadditionalSwap/tmpfs. Nie zwiększać deadline automatycznie.
Porównać normy/errors względemEXP42 i potential/referencegates bezluzowania.
Nie jest to zmiana medium ani nowy solve. Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-volume-degree5-20261019 --physics volume --level 2 --volume-degree 5 --volume-inputs artifacts/m2-transmission-eps294-f2-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.
Jeśli timeout, zachować dokładnystage, następny run dopiero z diagnozą/pracy
podziałem; nie wyciągać fullfieldwniosku z niedokończonej całki.


EXP43 exit0/noOOM159,317s/RSS494MB,2240positivevolumepts. Degree5 E/H
2,8884/1,6116%; refB3/B4 1,9455/1,1580%; potentialq12/q16 7,38e-4/7,47e-4
FAIL1e-6. Degree2/5error zmiana0,7367/0,7486punktuproc. Nie ogłaszać dokładnego
fullL2; oba oszacowania niespójne. H_FEMsquarednormdelta2,11e-15: te same
wektory i prawidłowe regułycałkujące jego stopień2. Root wszystkiecomplexnormy,
actualsource/helper/SO/inputSHA/noOOM/stany w artifacts/m2-volume-replay-root-analysis-20261019.json.
80unitPASS; bez BEMassembly/LU/rebuild/cloud/GPU/swap, małe MFEMforms nadal
montowane z handle. Docs EXP42–43 i sourceaudit pinned potentialkernels zapisane.
Następna hipoteza: fixed regulartrianglequadrature nie adaptuje się do point-panel
separation. Kontrola własnego panelintegral przeciw pinned kernel na tej samej
regule, potem near correction (subtract regular + add adaptive), bez powtarzania
solve. Jeszcze NOTRUN; bez twierdzenia że usunie cały błąd referencji.
Docs-garden read-only tej samej Luny: jeden wordingissue — rozróżnić standalone
degree2/5agreement od potentialq12/q16. Root poprawił dokument i dodał osobny
preregistered1e-6volume-degreegate FAIL do rootanalysis; casequalityflag nie
obejmuje pary reguł i opis teraz mówi to jawnie. Pozostałe source/artifacts PASS.
80unitPASS pinned, system67PASS/13SKIP; checker/diffcheckPASS. Lokalnycommit bezpush.
