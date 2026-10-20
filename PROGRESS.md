# Postępy optymalizacji

Aktualizacja: 2026-10-20. Mode: goal, Active: M5. [PLAN](PLAN.md), [MILESTONES](MILESTONES.md), [raport M1](docs/optimization-baseline.md), [kontrola pól](docs/field-validation.md).

## Wymóg użytkownika

**Gorące dane solvera w RAM/VRAM.** Cache, wejścia/wyniki i sporadyczne odczyty SSD dozwolone; niewielkie zapisy mierzyć. Bez swapowania zadania i intensywnego dyskowego workspace. UVM GPU↔RAM. Nie zamykać aplikacji użytkownika. Disk basis pozostaje usunięty; polityka I/O w PLAN.md.

## Bieżący checkpoint

- Active M5. M0–M4 ocenione; M2 integracja REJECT, M3 użyteczny zysk pamięci; M4 pełna para EXP94 PASS, bez zmiany globalnych defaultów.
- EXP94 T-Shaped medium3,50GHz/oba porty, samebuild/config: control681,698s → reuse602,944s,44/35iter. Jedna para −11,55%, nie mediana/promocja M7. Raw ||Ax−b||/||b|| ≤8,357e−7.
- Deferred postprocessing: managedpeak65,353→53,084GB (−18,77%) i controlcgroup60,525→56,830GB (−6,11%); reuse sam nie zmienia tego peaku. Jeden dodatkowy E179,5MB w RAM/VRAM. Fizycznej rezydencji VRAM nie utożsamiać z alokacjami.
- Wholefields/S/VSWR/power/energy PASS, W.2 trzyfreq/oba porty i tiny normalpathPASS. EXP92 OOM i EXP93 inline-reference OOM pozostają FAIL. Receipt artifacts/m4-deferred-antenna-root-analysis-20261020.json; dowody docs/milestones/M4.md.
- Regresje124PASS, cachedbuild9,215s, zachowane native/cache i fallback build/m4-reuse/pre-exp94-native. Gorące dane RAM/VRAM; SSDpolicy w PLAN. Bez płatnego compute/zamykania aplikacji.
- Następny krok: M5 audyt cuDSS0.7.1.4/UVM/hybrid/AMS i working set PC. M5 prototypy jeszcze NOT RUN. M6/M7/W.4/W.5 i końcowe trzy pomiary pozostają; Rust/FieldCraft/GUI/CAD poza zakresem.

## Historyczny skrót M1/M2

- M1 COMPLETE: referencja/normy/topologia/bieżącealokacje/krótkiprofil i końcowy normalpathPASS; M2 był wtedy ACTIVE. Goal pozostaje aktywny, bez promocji nowych defaultów.
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
- EXP44–47: RWGpanel/native i niezależny static-normalcontrolPASS, ratio2 czterokrotnie mniejliści. FullfineB4nearcorrection117,617s/217MB adaptive/cutoffPASS, E/H2,888/1,611% nadal FAIL. Root allpoint/weights/input/sourceSHA/complexnorm/subsetregression PASS. Dalsze EXP48–53 poniżej, docs/maxwell-near-panels.md.
- EXP48–53: cached NumBa native/parityPASS, pełny coarse replay18,089s/RSS217MB (NumPyTIMEOUT180s). Obie strony adaptivePASS; correctedreferencechange degree5E/H1,647/0,781%FAIL0,3%, volume2/5agreementFAIL, brakpromocjianteny. docs/maxwell-near-panels.md.
- EXP54–58: epsilon2,94 analyticF3 E/H.443/.717%PASS, actualcoupledF3/B3 i fixed640probes.664/.597% vsB4. Nie pełnyL2; reference/volume convergence nadalFAIL. DefaultND2eps1 regressionPASS. docs/maxwell-fem-refinement.md.
- EXP59–69: fusedT/K matchedCPU32query~2,56×zprzygotowaniem, nieantenna speedup; native teżmatrixfree. OwnF3degree5E/H1,683/.972%, reference/degreeFAIL. DenseB5>cap; następny małyFMMcandidate NOTRUN. docs/maxwell-stream.md.
- Praca RAM/VRAM. FEMcap60GiB/guard6GiB; nowe małe oraclecap6GiB/noadditionalSwap, noOOM. Bezpaidcompute/closedapps; cachekompilacji osobno.95testsPASSwpinnedenv; systemowo79PASS/16SKIP(SciPy). Kod Palace/medium bez zmian.

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

M5: audyt przypiętego cuDSS i istniejących preconditionerów; rachunek czasu oraz
working set przed nowym prototypem. Kolejność docs/milestones/M5.md. M4 zamknięty
po EXP94; końcowa promocja/default/pakiet oraz W.4/W.5 dopiero w M7.

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


### EXP44 — prerejestracja: fizyczny panelkernel i adaptacja przy bliskich punktach

Poprzedni goalturn PROGRESS: commit e5a85ce, volume replaydegree2/5FAIL zachowany.
Nowy maxwell_near.py rekonstruuje affineRWG J oraz div_Gamma z rzeczywistego
space.evaluate/DOFtransform i physicalJacobian. T=ik intGJ-intgradGdiv/(ik),
K=intgradGcrossJ; bez modyfikacji installedBempp. Porównać każdy zTt/Kt/Th/Kh
na identycznej triangle_gauss.rule(8) przeciw pinnedpotentialkernel, relative<1e-12.
Kontrola openonepanel(include_boundary_dofs) i closed20trianglepolyhedron,
syntheticcomplexcurrents, k=sqrt2.94. To operatorcheck, nie fizyczne rozwiązanie.

Adaptive test: singlepanel,6targets wtym distance0,002/0,02/0,2 z obu stron.
DuffyGauss6 vs8 na tej samej distance-subdivisiontree (ratio4,maxdepth12),
każdy point/operatorrelative<1e-6, brakdepth_hits. Raport regularvsadaptive
bez przypisywania exacterror samemu porównaniu. Gdy regular nativecheckFAIL,
nie uruchamiać dalszych poprawekvolume; zdiagnozować normalizację/div/orientację.
Unit84PASS: rigidrotation/translation,area childmap, exhaustion/errorguards i
preallocationflaglimits. Brak BEM/FEM solve/build/GPU/cloud.6GiB4CPU/tmpfs/noSwap.

`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-panel-control-20261019 --physics near-control --level 1 --seconds 120`.
Niepromowaćanteny, niezaliczaćM2 z operatorcontrol. Następne ewentualnie korekcja
savedvolume (subtract regularnear + addadaptive), tylko po tym filtrze i pomiarzekosztu.


EXP44 execution/operatorcontrolPASS15,028s/RSS272MB/noOOM. Regularphysical T/K
vs native peroperator≤1,97e-15, adaptiveq6/q8worst1,96e-15,10140leaves/order,
maxdepth12 alezeroexhaustion. Regularq8 vs adaptive1,627relative na nearpoints;
to nie świadczy samo o złej adaptive ani o jej exactaccuracy. Potrzebny niezależny
kontroler, nie tylko dwa warianty tej samej adaptacji.

### EXP45 — prerejestracja: niezależny solid-angle oracle + koszt ratio

KonwencjaLaplace: normalcomponent intgrad(1/(4piR)) = orientedOmega/(4pi).
Reference z istniejącej SciPy1.15.3 calculate_solid_angles (VanOosterom/Strackee,
DOI10.1109/TBME.1983.325207, bibliografiaCrossref/PubMedzweryfikowana; kodpinnedSciPy
odczytanylokalnie). Nie kopiowaćkernelnear jako oracle. Nowy helper diagnostyczny
nie jest używany przezintegrate/adaptive. Unit octantOmega=pi/2/orientation/scalePASS.
ConstantJx/Jy,div0,k=1e-5 daje normalgrad z (K[Jx]_y-K[Jy]_x)/2. Różnica
Helmholtz–Laplace ograniczona≤(1+maxkr)k²Area/(8pi)≈2e-12, gateabsolute1e-8,
bezdepthhits. To niezależny staticnormalcontrol, nie pełnyphysicalFEMsolve.

ZachowajnativeT/Kgate1e-12 iadaptiveq6/q8worstpointoperator1e-6. Porównaj
ratio2vs4 na tych samych6targets/currents/rules, mierząc czas/leaves/hits.
Fasterratio2dopuszczalne dopiero po obukontrolach.85unitPASS. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-solid-angle-control-20261019 --physics near-control --level 1 --seconds 120`.
6GiB4CPU/noadditionalSwap/tmpfs/noGPU/cloud/build. Nie powtarzaćfullvolume,
niepromowaćanteny. Przyfailnajpierwdiagnoza, bez automatycznejzmianyprogu.


EXP45 operatorcontrolPASS15,781s/RSS279MB/noOOM. Native T/Kmax1,97e-15;
ratio2worstq6/q8pointoperator1,97e-11,2550leaves,0,196/0,210s vs ratio4
10140leaves,0,783/0,865s. Independentconstant-normalstaticerror1,929e-12 ≤
Helmholtz–Laplacebound1,989e-12 ≪1e-8gate,zeroexhaustion. Root actualstate/
currentcase+nearSHA/peroperator and ratioNPZrecompute/regressionvsEXP44 in
artifacts/m2-near-control-root-analysis-20261019.json. Nie twierdzić że to
fullMaxwell/volumequality. Ratio2wybrany do małej następnej korekcji, nieanteny.

### EXP46 — prerejestracja: korekcja32savedpoints bez assembly/solve

bempp_near_correction.py: finePMCHWTB4 currents, cachedvolume degree5.
16worst q12/q16targets +16spanningpoints (wybórtendencyjny, NIE fullL2).
Odtwórzregularq12przezwłasnepanele na3punktach vs cacheE/H<1e-12; potem
odejmijregularnear i dodajadaptive6/8 (distance ratio2, maxdepth12).
Osobno selectionradius2vs4 przyadaptive8/ratio2 bada niekorygowane dalsze panele.
Gates adaptive6/8relative<1e-6 i cutoff2/4relative<1e-6,zeroexhaustion,
bezpromocji/analytic_target=false. Zmierzczas/leaves/RSS przed pełnymreplay.

Runner wiąże volume-output/currents/meta/state/material/referencelevel/SO,
reference.py i helperSHA; inputsread-only. Ref sourceSHA i volumegeometryhelper
wymagają zgodności. Unit85PASS, actualinputcheckPASS. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-subset-20261019 --physics near-correction --level 2 --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
6GiB4CPU/noadditionalSwap/tmpfs/noGPU/cloud/build/solves. Jeśli regularcache
niezgodny, stopdiagnose. Nie utożsamiać subsetcontrol z volumeconvergence.


EXP46 correctioncontrolPASS8,555s/RSS217MB/noOOM,32biasedpoints. Nativecachedq12
vs reconstructed E/H6,58e-15/4,47e-15. Adaptive6/8E/H1,01e-12/1,18e-12;
selectionradius2/4E/H1,76e-14/1,84e-14. Oldq16vs corrected0,1115/0,1189%.
q6r2 .600s/6897leaves, q8r2 .631s/6897, q8r4 1,118s/10200;zeroexhaustion.
Root source/input/state/npzcomplexnorm verification in artifacts/m2-near-correction-root-analysis-20261019.json.
Subset niejest globalL2 ani convergedphysicalreference. Reconstructedcurrents
zachowane; nic nie zmieniło fizycznego rozwiązania.

### EXP47 — prerejestracja: pełnyfine-reference replay ze wszystkimi kontrolami

Zmienić tylko count32→all2240savedpoints, reuse tych samychFEMcurrents/basis/refs.
Korekcje q6/q8radius2 i q8radius4; gateeachglobalE/Hdelta<1e-6, brakdepthhits;
nativeq12 vs3savedpoints<1e-12. Raport correctedvolumeestimate vs savedFEM,
nie qualifiedL2: nadal otwarty coarse-reference i degree2/5convergence.
Prognoza<180s (pilot2,35s/32dla3passes; celowanysubset jest kosztowniejszy niż
przeciętnepunkty). Bezprzedłużania deadline. Limit6GiB4CPU/noaddedSwap/tmpfs.
85unitPASS, bezGPU/cloud/build/assembly/solve. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-volume-b4-20261019 --physics near-correction --level 2 --near-count 0 --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.
Jeśli timeout, zachowaćstage; nie uruchamiaćponownie bez diagnozy. Nie podwyższać
medium ani progu błędów. To korekcjareferencjipostprocessingu, nie optymalizacja
productionPalace ani measuredantenna speedup.


EXP47 exit0/noOOM117,617s/RSS217MB, all2240positiveweights/4pi3. FineB4correction
adaptiveq6/q8E/H8,17e-13/8,34e-13, cutoff2/4 1,88e-14/1,86e-14,zerohits.
Correctedvolumeestimate E/H2,88847/1,61091%FAIL1%; oldq16vs corrected0,0311/0,0316%.
q6r2 279180leaves/25,068s,q8r2 279180/26,719s,q8r4 502040/59,561s.
Root independentlyrecomputedallcomplexnorms,input/source/helper/SHA andstates,
fullindices/weights,subset32regression<1e-13 in artifacts/m2-near-full-root-analysis-20261019.json.
Korekcja finepotential nie usuwa głównej rozbieżności pola. Nie rozstrzyga jeszcze
coarse-reference mesherror vs FEM/coupling; degreeagreement nadalotwarty.
Bez assembly/solve/build/GPU/cloud/swap/offload, zwykłe NPZinput/results wRAM.
85unitPASS pinned, system71PASS/14SKIP. Docs-garden read-only tej samej Luny
i rootreview PASS; root doprecyzował brak assembly operatorów FEM/BEM oraz
usunął dodatkowy nieaktualny licznik71unit z docs/testing. Checker/diffcheckPASS.
Lokalny commit bezpush; M2 ACTIVE, zero productionpromotion.


### EXP48 — prerejestracja: coarseB3subset i koszt przed pełnym replay

Poprzedni goalturn PROGRESS: commit5dbb3f2 fineB4nearcontrolPASS, polaFAIL.
Teraz nowy explicit--near-side coarse wybiera savedPMCHWTB3currents i cached
coarse_E/Hq12 na tych samychdegree5points. FineB4niezmienione, zeroassembly/solve.
Najpierw32targets(samefine q12/q16biasedselection +span), nie normafullvolume.
Nativecachedq12control3points<1e-12, adaptive6/8 i selectionradius2/4 E/H<1e-6,
zeroexhaustion. Zapiszold_q12vs corrected; old_q16=None bo brakcoarseq16cache.
Prądów/kandydataniezmieniać. Pomiar czasu/leaves przedall2240,deadline120s.
85unitPASS.6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-coarse-subset-20261019 --physics near-correction --level 2 --near-side coarse --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Przyfailzdiagnozowaćcache/side/normalization, bez zmianyprogów. Niepromować.


EXP48 coarse32pilot execution/correctionPASS9,268s/RSS216MB/noOOM. Nativeq12
vs rebuiltE/H3,83e-15/5,04e-15, adaptive6/8~1,4e-12,cutoff2/4~3,7e-14,
zeroexhaustion. Coarseoldq12→correctedE/H2,0627/2,2191% na biasedsubset;
niepełnanorma. q6r2 .874s/10104leaves,q8r2 .950s/10104,q8r4 1,437s/13854.
Rootstaty i weightedq12delta niezależnie przeliczone. Oldq16None zgodnie z cache.

### EXP49 — prerejestracja: all2240coarseB3 i porównanie ze skorygowanymB4

Zmienić tylko32→all, ten sam degree5/innyrefside już kontrolowany wEXP48.
KandydatFEM2/BEM3 i oba PMCHWTcurrents pozostająniezmienne. Każdyadaptive6/8 i
cutoff2/4globalE/H<1e-6,native3points<1e-12,zeroexhaustion. Dopiero po pełnym
runie rootporówna coarse/fine corrected na identycznychpointach/weights.
Prognoza~155–180s z pilotem i biasem; cap6GiB4CPU/tmpfs/noaddedSwap,deadline180s
bez przedłużania. Zeroassembly/solve/GPU/cloud/build. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-volume-b3-20261019 --physics near-correction --level 2 --near-count 0 --near-side coarse --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.
Nadal niepromowaćM2/FEM–BEM; field/volume-rule/mesh controls dopiero rozstrzygane.


EXP49 terminalny TIMEOUT 180 s, exit255, RunningFalse/OOMKilledFalse.
Ostatni etap q8/r4:1950/2240 punktów przy179,338s; brak case.json i pełnych pól.
Czasy z logów: nativecontrol4,987s; q6/r2 pełne44,564s; q8/r2 pełne48,028s;
q8/r4 częściowe81,759s. Nie jest to wynik jakościowy ani powód przedłużenia limitu.

### EXP50 — prerejestracja: cached Numba tych samych całek

Poprzedni turn odpowiedział na pytanie o UVM i sprawdził stan; NO PROGRESS
w implementacji. Następna bezpieczna akcja to kontrola gotowego JIT, nie restart EXP49.
Nowy opcjonalny backend numba FP64/complex128, bez fastmath; bounded DFS,
te same całki i kolejność dzieci, cache kodu /jit-cache, dane robocze RAM.
Default NumPy bez zmian. 88 unit PASS w pinned env; testy stubnjit nie dowodzą
kompilacji LLVM. Teraz rzeczywisty mały control: native/operator i NumPy/JIT<1e-12,
adaptiveq6/q8<1e-6, solid-angle abs<1e-8, zero depth exhaustion, podpis nopython.
Osobno czas compile/load i ciepłych kerneli. 6GiB/4CPU/tmpfs/noaddedSwap,
120s, bez GPU/chmury/Palace rebuild. Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-numba-control-20261019 --physics near-control --level 1 --near-backend numba --seconds 120`.
Tylko po PASS rozważyć pełny coarse replay z nowym backendem. M2 ACTIVE.

EXP50 PASS exit0/noOOM16,184s runner,14,873s case,RSS296MB. Actualnopython
signature,compile/load1,337s. JITvsNumPyregular<=4,11e-16/adaptive<=1,05e-15,
native<=1,92e-15,static1,929e-12,zerohits. Warmq8ratio2 .0103s vsNumPy.2093s;
ratio4 .0390s vs.8492s: microkernel~20x, not solver/antenna speedup.
Root terminal/sourceSHA/gates audit: artifacts/m2-near-numba-root-analysis-20261019.json.

### EXP51 — prerejestracja: pełny coarse replay z kontrolowanym JIT

Nowa hipoteza względem EXP49TIMEOUT: tylko backendNumPy→Numba, identyczne
2240point/weights/currents/FP64complex128/q6q8/radii2,4. Nativecontrol<1e-12,
adaptive/cutoffE/H<1e-6,zeroexhaustion. Porównać32savedsubsetEXP48 i pełny
fineB4EXP47; żadnej zmianyprogów. 180s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build.
Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-volume-b3-numba-20261019 --physics near-correction --level 2 --near-count 0 --near-side coarse --near-backend numba --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.

EXP51 PASS exit0/noOOM18,089s/RSS217MB,all2240points. CoarsecorrectedE/H
2,8260/1,7906%FAIL1%; native<=5,19e-15,adaptive<=1,44e-12,cutoff<=2,85e-14.
Zeroexhaustion. Q6r2/q8r2/q8r4:2,151/3,183/6,850s vsNumPy44,564/48,028/partial81,759s.
Paired32EXP48regression<3e-16. CorrectedB3→B4E/H1,6474/0,7806%: mesh-reference
stillnotconverged, nearquadraturewasnotsolecause. Rootanalysis artifact
m2-near-coarse-full-root-analysis-20261019.json; sources/inputSHA/gates audited.

### EXP52–53 — prerejestracja: degree2 reference replay

Same saved FEM2coefficients and PMCHWTB3/B4currents; change only saved volume
rule degree5→degree2(640positivepoints). Qualified NumBa backend, allpoints;
first fineB4, then coarseB3. Nativecontrol<1e-12,adaptive/cutoff<1e-6,zerohits.
Root compares correcteddegree2/5 whole-volume estimates AND reference change;
no looser tolerances or new solve. 120s EACH/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build.
Exact argv52:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-degree2-b4-numba-20261019 --physics near-correction --level 2 --near-count 0 --near-side fine --near-backend numba --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Exact argv53 (only after52 terminal):
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-degree2-b3-numba-20261019 --physics near-correction --level 2 --near-count 0 --near-side coarse --near-backend numba --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.

EXP52/53 PASS exit0/noOOM7,981/9,165s,RSS217/216MB; all640points,
native<=9,82e-15/adaptive/cutoff<=1,28e-12/zeroexhaustion. FineE/H2,15175/.86299%;
coarse1,75728/.88825%; correctedreferencechange1,08557/.44227%FAIL0,3%.
Degree5fine2,88847/1,61091%; error-estimate degree2→5 relativechange25,5/46,4%
FAIL1e-6. Root verified weightedcomplexnorms/points/weights and terminal gates:
artifacts/m2-near-volume-degree-root-analysis-20261019.json. Bothreference sides
nearquadraturecontrolled, volume/reference discretization still notqualified.
Next: controlled volume/reference convergence before FEMperturbation; no blindB5/q.
Docs updated; no Palacechanges/build/GPU/cloud/productionpromotion. M2 ACTIVE.

Walidacja końcowa:88unitPASS pinned/system74PASS14SKIP, docschecker i diffcheckPASS.
Ta sama Luna wykonała read-only docs-garden: zgodność wyniku/kodu/scopePASS;
wskazała trzy nieaktualne bieżące liczniki, root poprawił je i checkpoint/nextstep.
Historyczne liczniki EXP zachowano. Lokalne źródła/cache, bezpush.


### EXP54–55 — prerejestracja: niezależny analityczny FEM dla epsilon2,94

Poprzedni turn PROGRESS: commit410a854, cached nearJIT i corrected B3/B4/degree2/5;
niepromowany prototyp. Root teraz rozłożył zapisane błędy wg odległości od20planes
tej samej bryły (modelunits): degree5distance>.2 ma E/H1,791/1,539%, ale
B3→B4change tylko.101/.048%; distance<.05: E/H5,032/1,932%, refchange3,506/1,665%.
Artifact m2-near-boundary-error-analysis-20261019.json; emptybins=null, niepełnenormy.
Hipoteza: FEMresolution jest istotna niezależnie od brzegowego błędu referencji.
Nie rozstrzygać po dopasowaniu trendu: sprawdzić tę samą ND2bryłę F2/F3
z dokładnym Ex=exp(i*sqrt(eps)*z), physicalHy=sqrt(eps)*Ex i Dirichletdata.
Operator curlcurl-eps*M; helper raportuje H/sqrt(eps), względny błąd fizycznegoH
jest taki sam. Eps1 default ND2 i eps2,94 default transmission bez zmian.
Nowy parametr jedynie w analyticND2probe; stare guardedgeometryhelpers bez zmian.
Każdy run raw<1e-10,basis<1e-11,quad6/8delta<1e-6; fieldtarget1% unchanged.
Test nie jest transmisją przez interfejs ani pełną kwalifikacjąM2. 89unitPASS.
120s EACH/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build; exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-eps294-f2-20261019 --physics nd2 --level 2 --epsilon-r 2.94 --seconds 120`.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-eps294-f3-20261019 --physics nd2 --level 3 --epsilon-r 2.94 --seconds 120`.
Run55 only after54 terminal; failureexecution stops sequence, fieldFAIL retained.

EXP54/55 executionPASS noOOM1,071/5,572s,RSS287/432MB. F2DirichletE/H
1,7363/2,4894%FAIL1%; F3 .4431/.7171%PASS1%. Raw<=5,73e-15,q6/8delta<=1,22e-11.
Root checked terminal/currentcaseSHA/eps/k² and normalizations; artifact
m2-nd2-eps294-root-analysis-20261019.json. F3 analytic pass motivates actual
coupledrefinement, not dielectrictransmission qualification or memoryspeedup.

### EXP56 — prerejestracja: dielectric coupled F2→F3 z BEM3 fixed

Jedyna zmiana względem EXP40: FEM2(160tet/1228DOF)→FEM3(1280tet/8936DOF).
Ten sam epsilon2,94, surfaceB3, paramsq4, BC/RWGmortar/Schur; zachować savedu/t/h.
Nativecoupling/transmission helpers unchanged. Existing run robi centroidscreening
vs PMCHWTB2/B3; to nie pełny L2 i nie zastępuje volumeB4reference.
Hipoteza na podstawie EXP54/55: FEM error maleje, ale reference/coarsemesh
nadal ogranicza kwalifikację. Raw<1e-9 i mortar<1e-12; dotychczasowe field/energy
thresholds unchanged, FAIL retained. 180s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build.
Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-eps294-f3-b3-20261019 --physics transmission --level 3 --surface-level 3 --epsilon-r 2.94 --seconds 180`.
Po solve bez ślepego ponawiania; ocenić cachedvolume z samą referencjąB4 zEXP41.

EXP56 executionPASS115,0s/RSS1,325GB/noOOM, screeningFAIL zachowany. Centroid1280
E/H1,4988/1,0847%, referenceB2→B3change7,968/7,643%: not comparable to EXP40
centroid160sample. Farrelative.04498%, energy/pi1,28e-7/raw1,97e-13 PASS.
Savedcoupled-solution.npz preserved. Root terminal/sourceSHA checked.

### EXP57 — prerejestracja: stałe640punkty, bez nowego BEMsolve/potential

Aby nie powtarzać kosztownych potencjałów, nowy bounded `fem-replay` bierze
F3savedu zEXP56 i dokładnie640degree2points/weights zEXP42; referenceB4 currents
zEXP41 służą guardom fizyki. Root porówna replay z correctedB4EXP52 iF2EXP42
na identycznych punktach oraz osobno wnętrzu distance>.2 (modelunits).
Strictbarycentricowner>1e-10 eliminuje niejednoznaczność normalnegoE na faces;
reject zamiast wybierania wartości arbitralnie. Ten zbiór nie jest zbieżną
normąFEM3: żadnej kwalifikacji całego pola na podstawie tego screenu.
Walidacja inputów: terminal/noOOM/sourcehelper/nativeABI/npzSHA/eps/degree2.
Nie eksportować nowych macierzy, nie solve/BEMassembly; mały GlobalNDconstructor
nadal assembles mass/curlforms. 92unitPASS.120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build.
Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fem3-fixed-probes-20261019 --physics fem-replay --level 3 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --probe-input artifacts/m2-transmission-volume-degree2-20261019 --seconds 120`.

EXP57 executionPASS0,761s/RSS296MB/noOOM; all640strictowners,minlambda.1708204.
Root independently compared identicalpoints/weights/current/sourceSHA andallinputSHA.
F2→F3 vs correctedB4: E2,15175→.66355%,H.86299→.59717% onall640probes.
Core distance>.2(modelunits),300points/46,875%vol: E1,19656→.18592%,H.75174→.25188%;
refB3→B4change.05517/.04366%. Near340points: F3E/H.93207/.81265%, refchange1,55555/.62954%.
Rootanalysis m2-fem3-fixed-probes-root-analysis-20261019.json. RefinedFEM helps,
but coarseprobes don't establish fullF3L2 or reference/volumeconvergence.

### EXP58 — prerejestracja: domyślny ND2epsilon1 regression

Zmiana parametruepsilon nie może zmienić defaultuND2. Powtórzyć tani F3analytic
bez flagiepsilon i porównać z zachowanym EXP33 po samejgranicypól/kodunormy.
Expectedepsilon1,k1,Dirichlet E/H.1505/.3317%, raw/quad/basis gates unchanged.
120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build. Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-eps1-default-regression-20261019 --physics nd2 --level 3 --seconds 120`.

EXP58 execution/analyticPASS5,520s/RSS432MB/noOOM,epsilon1/k1. Dirichlet E/H
.150508/.331747% identyczne z EXP33(m2-global-nd2-level3-q6-20261019/case.json).
Root ponadto odtworzył physicalprobe coordinates z cell/localmap do<1e-13
w EXP57; savedinput/sourceSHA/terminalnoOOM verified. Aktualny docs/wyniki i
nextstep zapisane. Niepromowane: M2volume/reference/rezonanse/koszt nadalotwarte.

Walidacja robocza:92unitPASS pinned; system76PASS16SKIP. Docschecker/diffcheckPASS.

Docs-garden read-only tej samej Luny: PASS, brak sprzeczności scope/kodu/artefaktów.
Rootreview: physicalpointreconstruction i epsilon1default exactregression sprawdzone;
żadnego utożsamienia fixedpointów z convergedL2. Checker/diffcheckPASS.
Lokalny commit bezpush. M2ACTIVE, goal nieukończony; brak zmiany medium/anteny.


### EXP59 — prerejestracja: streaming potential, bez macierzy punkt×DOF

Poprzedni turn PROGRESS: commit91b7f5f, rzeczywistyFEM3solve i identical640probes
poprawiają E/H. Nowa bezpieczna akcja: mała kontrola pełnej sumy potencjałów,
aby później obliczyć właściwą F3volume rule bez kosztownego nativepotentialmatrix.
maxwell_stream.py: existing cached nearjit FP64/complex128/no fastmath,
NumBa parallel over targets (existing threadlimit2), stała kolejność paneli.
Każdy farpanel liczy regularq12, bliski adaptiveq8/ratio2; selectionradius4.
Kontrola32saveddegree2points vs cachednativeq12(radius0) i osobno incremental
qualifiednearcorrection(q8/r4). GatekażdeE/H<1e-12, finite,zeroexhaustion,
actualnopythonsignature; compile/load i ciepłyapply osobno. 95unitPASS; stubnjit
wunitach nie jest dowodem LLVM. Zero nowego solve/BEMassembly/GPU/cloud/build.
120s/6GiB4CPU/tmpfs/noaddedSwap. DaneRAM, cache kodu osobno. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-control-20261019 --physics stream-control --level 2 --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Po PASS dopiero pilot32na realnej reguleF3degree2; nie uruchamiać full bez oceny kosztu.

EXP59 operator/executionPASS9,157s/RSS250MB/noOOM. Actualnopython,threads2,
compile/load2,900s. Full32point potentialapply .0582s, native/incremental
E/H<=8,88e-15, zeroexhaustion. Pilotfieldestimate2,887/.942% biased, not norm.
Rootauditedallinput/sourceSHA and terminalstates; artifact
m2-stream-control-root-analysis-20261019.json. No potentialmatrix/solve.

### EXP60 — prerejestracja: kosztowy pilot na własnej reguleF3degree2

SavedF3u(EXP56), PMCHWTB4currents(EXP41), 5120positivecellquadraturepoints;
wybrać32(16closest20planes+16spanning), bez nowego solve. Ten pilot nie jest
normąobjętości. Basefarq12/nearquad8/radius4, samequalifiedkernel. Sprawdzić
finite/nopython/zerodepthhits i czas cieplegoapply/leaves przedfull5120.
120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build. Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-pilot-20261019 --physics stream-volume --level 3 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.

EXP60 executionPASS5,241scase/RSS430MB/noOOM.5120original/32biasedpoints,
apply.0599s,setup.0160s,maxdepth4,zerohits. PilotE/H3,327/1,596% niepełnanorma.
Conservativeapply estimate .06*5120/32~9,6s plus setup<10s; supports fullrun
without extending120s caps. No potentialmatrix/solve.

### EXP61–62 — prerejestracja: własna pełna regułaF3degree2 i nearquadrature

Change only32→all5120points/weights, savedu/currents unchanged. EXP61base:
farq12/nearquad8/radius4. EXP62near6: farq12/nearquad6/radius4. Root porówna
weightedcomplexE/Hdelta<1e-6, samepoint/weights/SHA, zeroexhaustion. Wyniknormy
nadal wymaga radius/far, degree i reference mesh controls; niepromować samychminimów.
120s EACH/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build. Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-base-20261019 --physics stream-volume --level 3 --near-count 0 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-near6-20261019 --physics stream-volume --level 3 --near-count 0 --stream-variant near6 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
EXP62 po terminalnym executionPASS61; bez retry/extension.

EXP61/62 executionPASS all5120points,case14,417/13,311s,RSS431/433MB,noOOM.
BaseE/H1,463205/.864503%: EFAIL1%, HscreenPASS; notconvergedvolume.
Apply9,248/8,166s,zeroexhaustion,maxdepth4,1,101,292leaves.
Rootweightednear6vs8delta E/H=1.41677e-12/1.41611e-12PASS1e-6,samepointsweights.

### EXP63–65 — prerejestracja: radius/far i reference mesh na tej samej regule

SavedF3coefficients/currentinputs unchanged, all5120degree2. Finevariants radius2
(qfar12/qnear8/r2) i far16(qfar16/qnear8/r4) porównać zbase weightedE/H<1e-6.
CoarseB3base vsfineB4 mierzyreferencechange, frozen0,3% niezmieniony.
120s EACH/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build, bezretry.
Exactargv63:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-radius2-20261019 --physics stream-volume --level 3 --near-count 0 --stream-variant radius2 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Exactargv64:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-far16-20261019 --physics stream-volume --level 3 --near-count 0 --stream-variant far16 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Exactargv65:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-coarse-20261019 --physics stream-volume --level 3 --near-count 0 --near-side coarse --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Sequential after terminalexecutionPASS, interpretation root only. No fieldqualification yet.

EXP63–65 all5120 executionPASS/noOOM,RSS<=434MB. Fine radius2/far16E/H
1,463205/.864503%; coarse1,583615/.860008%. Case13,864/17,838/10,107s,
apply8,697/12,668/4,928s,zerohits. Rootweightedbase deltasradius2<=2,21e-14,
far16<=1,42e-15; near6<=1,42e-12PASS1e-6. ReferenceB3→B4 E/H1,55485/.75206%
FAIL0,3%; fieldEFAIL1%. Artifact m2-stream-f3-degree2-root-analysis-20261019.json.
No densepotentialmatrix/solve; notantenna speedup or convergednorm.

### EXP66–67 — prerejestracja: własna regułaF3degree5

Change onlydegree2→5:5120→17920positivepoints, savedF3u andPMCHWTcurrents unchanged.
FineB4base then coarseB3base. Hypothesis: resolve volumequadrature sensitivity
and reference mesh change before claiming trueL2. Near/far controls qualified
on degree2; degree5control remains separate if field/reference promising.
Costestimate3,5×apply9,25s plus setup~5s, allow~2×extra nearwork<120s; no capraise.
Frozen field1%/reference.3%/volumeagreement1e-6 unchanged. No solve/GPU/build/cloud.
120s EACH/6GiB4CPU/tmpfs/noaddedSwap. Exactargv66:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree5-base-20261019 --physics stream-volume --level 3 --near-count 0 --volume-degree 5 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Exactargv67:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree5-coarse-20261019 --physics stream-volume --level 3 --near-count 0 --volume-degree 5 --near-side coarse --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Next only after terminalexecutionPASS, no autoretry. Rootanalysis only.

EXP66/67 executionPASS all17920degree5points,noOOM,RSS442/440MB,case37,210/22,216s,
apply31,985/17,035s,zeroexhaustion,maxdepth5/6. FineE/H1,68335/.97150%,
coarse1,75075/1,04841%. Rootcorrectedreferencechange1,72451/.87598%FAIL0,3%;
relative degree2→5 fieldestimatechange13,0779/11,0139%FAIL1e-6.
FEM_Hsquarednorm q2/q5 exactlysame: expected curlND2degree1, |H|²degree2.
Root allinput/sourceSHA/state, positiveweights4pi/3, pilotfullregression audited;
artifact m2-stream-f3-volume-root-analysis-20261019.json. Degree5near/farcontrols
NOTRUN, niepromować. Nie ponawiać tego samego solve/ślepego volumeq.

Źródłowa korekta hipotezy: native Bempp NumBa potential NIE tworzy pełnej
macierzy punkt×DOF. Pinned core/numba_assemblers.py i numba_kernels.py
maxwell_efield_potential/maxwell_mfield_potential liczą bezpośrednią aplikację,
ale mają global_points/tmp/diff w rozmiarze panel×quad i osobne T/K/currents.
Nowy stream fuses cztery T/K dla2currents i ogranicza pertarget temporary do
panelu. Wcześniejsze słowa 'nativepotentialmatrix' w EXP59/roadmap były błędną
hipotezą, nie zmierzoną alokacją. Nie raportować oszczędności macierzy ani
przyspieszenia względem native bez matchedmeasurement.

### EXP68 — prerejestracja: matched native+correction vs fused apply

Ten sam32pointcontrol/currents/q12+adaptiveq8radius4, dokładność<1e-12.
Dodać rzeczywistą native q12evaluation (warmup1point/cachetime osobno),
porównać z cached q12; osobno panelpreparation, fusedapply i incrementalcorrection.
Native NumBa również matrixfree. Test nie mierzy peakmemorydelta/antenna speed.
120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build; źródła geometry/nearjit bez zmian.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-native-comparison-20261019 --physics stream-control --level 2 --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.

FMM feasibility audit only, NOTRUN/notinstalled: pinned Bempp0.4.2 fmm_assembler.py
supports MaxwellT/K; Dockerfile pins exafmm-t0.1.1. Official Bempp handbook confirms
assembler='fmm', https://bempp.com/handbook/api/boundary_operators.html and
https://bempp.com/handbook/core/assembling_operators.html . Local exafmm=None.
ExafmmInterface creates cwd/.exafmm/*.tmp; must stay /scratch tmpfs under existing
caps, never disk. Dense referenceB5N7680 has4operators+15360²block≥7,550GB beforeLU,
over6GiBcap, so no denseB5 attempt. Nextcandidate independent PMCHWT-FMM reference
with small denseT/K/action/solution controls beforehighermesh; no guarantee of benefit.

EXP68 operatorPASS17,072s/RSS292MB/noOOM. Actualnativeq12 exactlycached,
othercontrols<=8,88e-15. Nativewarm/load9,064s, first32evaluation2,837s;
fusedpanelsetup1,758s/apply.05955s, incremental.07555s. Single native32timing
is not robust warmed benchmark: add3repeats, report samples/median andsetup
rather than applying microkernelratio to end-to-end. No peakmemorydelta claim.

### EXP69 — prerejestracja: repeat matched warmed potential query

Same32points/currentinputs/numerics asEXP68, only3warmmeasurements permethod,
withnativewarmup1point andexplicit panelssetup/JITcost. Median/samples reported;
includesnativeq12+incremental vsfusedpanelsetup+apply; sourcewithoutpointmatrixclaim.
120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build, no retries. Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-native-repeat-20261019 --physics stream-control --level 2 --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.

EXP69 PASS22,897s/RSS292MB/noOOM, nativeactualq12exactcached i pozostałe
controls<=8,88e-15. Nativequeries2,8344/2,8550/2,8697s,fused.05931/.05892/.05861s;
incremental.07567s,wspólnepanelprep1,77788s. Matched pojedynczequeryzprep:
4,70855→1,83680s (~2,56x); amortizedquery2,93067→.05892s(~49,7x), tylkoCPU32points.
Root allinput/sourceSHA/terminalgatesaudited w m2-stream-repeat-root-analysis-20261019.json.
Nie mierzonodeltapeakRAM aniantenna speedup. Nativealreadymatrixfree fact corrected.
Docs/INDEX/ARCH/PLAN i nextstep zaktualizowane; nadalM2ACTIVE i nierozwiązane
field/volume/reference gates. FMMaudytkandydataNOTRUN, bezinstalacjideps.

Walidacja historycznego commitu e57ba76:95unitPASS pinned/system79PASS16SKIP, checker/diffcheckPASS.
Ta sama Luna: read-only docs-gardenPASS, bez sprzeczności i bez edycji.
Rootreview: native-no-pointmatrix correction, matchingcost z commonpanelprep,
frozenFAILgates i FMM/tmpfsNOTRUN sprawdzone. Commit lokalny, bezpush.
Następne M2FMMsource/małyMaxwelloracle; brak nowej antena/medium/defaultpromotion.


### EXP70 — prerejestracja: izolowany cached ExaFMM addon

Poprzedni turn PROGRESS: commite57ba76 fusedpotential i własnaF3volume/refFAIL;
nextreferenceFMMcandidate. Root przypiął exafmm-t v0.1.1 do commit
78b7d56f988b3843ba502faf4ac60b0c013aa206; LICENSE BSD3Clause (setup metadataMIT
nie jest źródłem licencji). Sourcecheckoutclean bez modyfikacji upstream.
Pybind11headers2.13.6 prywatnytarget .cache/m2-build-deps, bez zmian venv/Bempp.

Read-only dependencyprobes dużego PalacebuilderImage(25,4GB) nie wystartowały
z cap6GiB: OCIinit 'OOM-killed?' lubparentreset, także z Luny. Nie dowodzi
hostOOM: MemAvailable~69GiB,parentcgroup memoryevents oom0, runtimeimage /bin/true
startuje pod tym samymcap. Nie podniesiono limitów ani zamknięto aplikacji.
Zamiast kolejnych prób nowy mały cached builder frompinnedUbuntu24.04 digest
68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac,
tylko g++/ccache/FFTW/OpenBLAS, bez Palace/dependencyrebuild i bez kasowaniacache.

exafmm_build.py: namedimageprovision max180s/6GiB4CPU, cached image byrecipe;
compile1TU przezccache -c, osobnylink, max120s/6GiB4CPU/tmpfs/noaddedSwap/networknone.
Headers/PythonbinaryABI/source/builder/runtimeimage/flags i prywatneFFTW/BLAS
librarySHA wmanifest. Tworzone obrazy/cache są softwarecache, nie solveroffload.
NumericalsolverNOTRUN; successfulbuild nie kwalifikuje importu/FMM/Maxwell.
Root przygotował kod; Luna tylkoexactbuildargv i terminalmonitoring, bez decyzji.
Exactargv:
`python3 tools/experiments/exafmm_build.py build`.
Po PASS osobny runtimeimport i małyMaxwellFMMvsdense przedB5. NofullPalacebuild/GPU/paidcompute.

EXP70 buildPASS21,455s, imageprovision/compile terminalexit0/noOOM.
BinarySHA7bb42c3049da13405d4c2a604352af6b89b14ed54466c4c51243b56b660c6e48.
Rootrecipe/artifactfingerprintverified; no runtime/numericalpass yet. Imagesmall
Ubuntu+FFTW/BLAS+g++ solves provisioning path without changing Palacebuildercache.

### EXP71 — prerejestracja: cached rebuild + runtime MaxwellFMMvsdense

First repeat samebuildargv: expectverifiedno-op/noC++compile, preservesbinarySHA.
Then runtimeimportprivateCPython3.12module+libs on originaloracleruntime, no newvenvdeps.
SurfaceB2RWG120, k=1/sqrt(2,94), quadregular/singular4, FMMorder6/ncrit32.
Three deterministic complexvectors eachT/K; weightedgeometry same asdense,
relativeactiongate1e-6, dtypecomplex128, nohiddenGLOBALdensefallback. Require
nontrivialtree depth>=2 andallFMMtmp under /scratchtmpfs512MiB; privatelibsfromreceipt.
No transmission solve/Mie/antenna or scalabilityqualification on operatorpass.
99systemtests:83PASS16SKIP. Numericalrun120s/6GiB4CPU/noaddedSwap/noGPU/paidcompute.
Exactargvs sequential:
`python3 tools/experiments/exafmm_build.py build`.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-maxwell-o6-n32-20261019 --physics fmm-control --level 2 --fmm-order 6 --fmm-ncrit 32 --seconds 120`.
OnlyaftercachedbuildterminalPASS; no retries or limit changes.

EXP71 terminal exit0/noOOM, executionPASS but operator_controlFAIL. Root checked
case/command/container-state: p6/ncrit32, complex128,120DOF,480sources/targets,
two73node depth2trees. T relative action error2.15e-6/2.24e-6; K1.95e-5/1.66e-5
at k1/sqrt2.94, exceeding frozen1e-6. Elapsed26.331s/sharedRSS497680384B.
Build repeat cache no-op0.105s. No numerical qualification or speedup promotion.

### EXP72 — prerejestracja: MaxwellFMM order8, unchanged action gate

Previous goal response was an explanation/plan (no progress); EXP71 is terminal,
so next safe action is p6→p8 only. Same geometry/B2, ncrit32, quad4, k/vectors,
complex128 and1e-6gate. Added report-only actual FMM tempfile bytes and tmpfs
occupancy/capacity; cwd remains512MiB RAM tmpfs,6GiB/4CPU/noaddedSwap/networknone.
No source/Palace rebuild, no paidcompute/GPU, max120s. A pass qualifies small
operator actions only; then actual PMCHWTsolution control before higher reference.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-maxwell-o8-n32-20261019 --physics fmm-control --level 2 --fmm-order 8 --fmm-ncrit 32 --seconds 120`.

EXP72 terminalexit0/noOOM28.036s/RSS708407296B, operatorFAIL. k1T/K4.14e-8/
5.55e-7 meetgate, ksqrt2.94 T/K.27650/.83602 invalid. Root found scratch_used
536870912==capacity; firstfile302215176B, second234651648B truncated atcap.
Pinned ExaFMM fmm.h precompute closes ofstream without checking errors, and
evaluate rereads its tables. Runtimeexit0 is not numericalvalidity. This is
tmpfs/RAM exhaustion, NOT SSD scratch or proof highorder mathematicalfailure.

### EXP73 — prerejestracja: sequential-wave cache lifetime, same512MiBcap

Independent k1/kdielectric controls don't need coexistence. Snapshot receipts,
release each tree via upstream clear_fmm_cache, delete only its runtime tmpfiles
via upstream cleanup_fmm_tmp; preserve source/JIT/build caches. New failfast check
before numericalaction rejects exhausted tmpfs. Same p8/ncrit32/q4/vectors/gate,
120s/6GiB4CPU, no capincrease, no SSD fallback. Not yet PMCHWT simultaneous2k.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-maxwell-o8-sequential-20261019 --physics fmm-control --level 2 --fmm-order 8 --fmm-ncrit 32 --seconds 120`.

EXP73 terminalexit0/noOOM, execution/operatorPASS, analyticFalse. Root inspected
case/state:28.331s/RSS624742400B, Terrors4.14e-8/4.67e-8, K5.55e-7/4.71e-7.
Both tables302215176B individually, peakRAMtmpfs302219264B/end0/cap536870912B.
This removes spurious corruption by sequential independent-wave lifetime, not
a solution for simultaneousPMCHWT or proof antenna memory/speed improvement.
Next: budget true PMCHWT2k storage and solve-vs-dense, no change to frozen gates.
Docs maxwell-fmm/stream, PLAN/M2/INDEX/ARCH/testing updated; M2 remainsACTIVE.

EXP73 finalvalidation:101testsPASS pinned; system85PASS/16SKIP. SameLuna
read-only docs-garden reviewed code/untracked/report: no numerical/scope
contradictions; stale current-suite95 corrected to101 (historical e57ba76 count
retained with explicitlabel). Checker/diffcheckPASS. Root verified currentcaseSHA
match EXP73command and terminalstate exit0/noOOM. No antenna/promotion/M3 claim.
Local commit only, no push to public upstream.

### EXP74 — prerejestracja: actual PMCHWT FMM vs independent dense solve

Previous turn progress: f41aeca, cachedaddon/MaxwellactionPASS after RAM-lifetime
fix. Next full small PMCHWT at sameB2/p8/ncrit32/q4/k1/sqrt2.94/complex128.
Each wave retains its302MBtable on one existing RAMtmpfs mount: /scratch or/tmp,
512MiB each, same total6GiB/4CPU/noswap cap. No table/tree rebuild per iteration,
noSSDscratch. Root prepared exact matrix blocks from frozen transmission helper
without editing it; bothdense andFMM share geometry/RWG-SNC/projections. Dense
is independent tiny oracle only, not a scalable preconditioner or FMMfallback.
Actual LinearOperator GMRES rtol1e-10, restart32/onecycle, max120s. Report raw
FMM and independentdense residuals, coefficientdifference, iterations/matvec/setup
cost and sharedRSS. Gates raw<1e-9, coefficientrel<1e-6; no field/Miequalification
from small solve. Nonconvergence/frozenindependentrawFAIL remainsfailure.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-pmchwt-o8-20261019 --physics fmm-solve --level 2 --fmm-order 8 --fmm-ncrit 32 --seconds 120`.

EXP74 terminalexit0/noOOM, sourceSHA/terminal verified byroot before edits.
GMRES32/info1, FMMraw.018024085 vs independentraw.018024085, coefficienterr6.484%.
Dense raw2.467e-15. Solve52.868s,34matvec54.398s(include finalcheck), total81.259s,
RSS717533184B. Both RAMtmpfs302219264B peak/end0, no overflow/rebuild.
FAIL is nonconvergence, not evidence that converged FMM solution meets gates.

### EXP75 — prerejestracja: sparse adjacent-panel near-ILU for M2 solve control

One change: leftpreconditioner from existing exact singular_part sparse matrices
of fourMaxwelloperators, no dense oracle entries, no singularRWGGram inversion.
Same PMCHWTblocksigns; spilu drop_tol1e-3/fill_factor5. Report actual sparse/factor
nnz/bytes and setup. Same p8/quad4/B2/32GMRESsteps/rtol1e-10/raw1e-9/coeff1e-6.
Still M2 solver feasibility (not moving to M3/M5 or promoting preconditioner).
No cache/dependency rebuild, unchanged6GiB4CPU/tmpfs512MiBeach/noSwap/120s.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-pmchwt-near-ilu-20261019 --physics fmm-solve --level 2 --fmm-order 8 --fmm-ncrit 32 --fmm-preconditioner near-ilu --seconds 120`.

EXP75 terminalexit0/noOOM71.560s/RSS721100800B, solveFAIL. NearILU matrix12960nnz/
260164B, factors39578nnz/793488B, setup.00960s. GMRES26/info1 stoppedcycle before
rtol; rawFMM9.464e-10 meets1e-9gate but notrequested1e-10 stopping, independent
raw1.302e-7 FAIL, coeffrel3.850e-7 PASS. Solve43.060s vs52.868s unpreconditioned
(bothincomplete, not qualifiedspeedup). Error floor now operatoraccuracy, not
simply iterationcap. No promotion/relaxedgates.

### EXP76 — prerejestracja: p9 precision step with predicted RAM table budget

One change fromEXP75: order8→9. Pinned fmm.h filelayout predicts complex128
table:20*nsurf²*(depth+1)*16+26*(2*(2*p)^3*8*8)*depth*8+8,nsurf=6*(p-1)^2+2.
Geometry.h gives8M2M/26M2Lpositions. Atactualdepth2 p8=302215176B(exactobserved),
p9=453578504B(fits512MiB); p10=654602248B DOESNOTFIT, do not blindlyrunp10.
Added preflight budget and exactpostbuildfile-sizeguard, nohighercaps. Same
nearILU/32steps/rtol/raw/coeffgates, allFP64complex128,120s/6GiB4CPU/noSwap.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-pmchwt-o9-near-ilu-20261019 --physics fmm-solve --level 2 --fmm-order 9 --fmm-ncrit 32 --fmm-preconditioner near-ilu --seconds 120`.

EXP76 terminalexit0/noOOM, rootverifiedsourceSHA/state. p9independentraw1.272e-8
stillFAIL1e-9, coeff3.004e-8 PASS; info1/26iter, FMMraw9.464e-10 notrtol1e-10.
Solve59.005s,total88.396s,RSS900726784B. Bothtables453578504B equalpredicted,
tmpfs453578752B each/end0. p9highercost reducesoperatorfloor but doesnotqualify.

### M2 decision — assessment CLOSED / integration REJECT, M3 ACTIVE

Existing PLAN already allows negative hypothesis closure with evidence; after
actual CUDA/H-matrix/coupled/transmission/FMM assessments, reject current
productionintegration. M2.2wholefield/convergence andM2.3matchedqualitycost remain
FAIL/incomplete, NOTPASS. No gates relaxed and no antenna/BEM promotion.
Decision audit docs/milestones/M2-decision.md links scope/results and unsupported
feed/thinmetals; avoid endless p increases without qualified speed/memory.
ActiveM3 direct FP32basis/FP64 operations in existing FEM, baseline preserved.
Sourceaudit: iterative.cpp Unpacks StoredBasisVector forbasisread/MGS; vector.cpp
Pack/Unpack; optin existing but NOTqualified on currentM1reference. NextsmallCUDA
probe→cachedincrementalbuild→W.1 thenW.2/W.3. PLAN/MILESTONES/INDEX/M2/M3 synced.

Rootcostcaveat: reported RSS includes dense oracle but is not wholecgrouppeak;
tmpfs pages separate. No claim totalprocessmemory reduced based only onRSS.
Sourceaudit confirms unpack in everycompressed MGS k-loop and beforeApplyBA;
direct mixed dot/axpy is intended firstM3 prototype, no newprecision runyet.

Final EXP74–76 validation:102unitPASS pinned; system86PASS/16SKIP. SameLuna
read-only docs-gardenPASS: M2negativeassessment vs failednumericalgates explicit,
M3ACTIVE, tmpfs/RSS/p10limits agree withsource/artifacts. Checker/diffcheckPASS.
Rootreview complete; localcommit only/no push. No fullantenna/speedup promotion.

### EXP77 — prerejestracja M3: shared FP32-storage/FP64 arithmetic CUDA probe

Previous turn progress f58d028: M2assessmentCLOSED/productionREJECT, M3ACTIVE.
Root audited compressed MGS: iterative.cpp unpacks basis insideeachk and before
ApplyBA. LocalDot(w,b)=sum(w*conj(b)), linear firstargument. New pure header
mixedbasis.hpp defines partialdot/complexaxpy with floatloads castdouble BEFORE
products/accumulation. Not wired into GMRES yet. Header shared with isolated
CUDA probe; no ABIcasts, fastmath, FP32accum or TensorCoreclaim.

Compile only oneCUDA TU sm120 via existingbuilder/ccache, separatelink,120s;
no Palace/dependencies rebuild. Subsequent identicalbuild expects cache no-op.
Numerics same pinnedPython/NumPy environment andruntime;6GiB4CPU/noSwap,
RAMtmpfs512MiBeach/networknone, localGPUfree>=768MiB,60sdeadline. Largest
vector2^20, explicitdevicealloc~77MB plusCUDAcontext (not fullprocesspeak).
Reference longdouble math on SAME quantizedfloatstorage; gate normalizeddot/
axpy1e-12, separate FP32quantization norm-product-scaled gate2e-7.
Casesn1(nontrivialcomplexsign),1009,131071(dynamicrange1e-30..1e30),1048576;
rejectn0 beforeallocation. Two-stage FP64reduction, partialcount<=65536.
Compare direct dot+axpy vs unpack→sameFP64kernels, identicalworkvectorreset.
Alternate executionorder acrosspairedtrials; eventtimers excludealloc/H2D/JIT,
includecommonDtoDresets. NOT HYPRE/GMRES/fullantenna benchmark or UVMprofile.
105systemtests89PASS16SKIP. Rootdesign; sameLunaexactargv/babysitting only.
Exactargvs sequential, later only afterprior terminalPASS:
`python3 tools/experiments/mixed_basis_probe.py build`.
`python3 tools/experiments/mixed_basis_probe.py build` (cache repeat).
`python3 tools/experiments/mixed_basis_probe.py run artifacts/m3-mixed-basis-cuda-20261019 --seconds 60`.

EXP77 allterminalPASS/rootverifiedsource/header/worker receipts andstateexit0/noOOM.
First build1.503s(manifest), repeatno-op; noMFEM/Palace rebuild. Sharedheader
complexarithPASS atall4sizes; maxnormalizeddot4.43e-18,axpy4.40e-17,
FP32quantizationnorm-scaled8.87e-10. LargestN1048576 median.109695msdirect vs
.119766msunpack(~8.4%lowerprobeeventtime, NOTGMRES/HYPRE/antenna gain).
Explicitdevicealloc76546064B includesbothpaths, reductionworkspace1048592B,
baselineunpack16777216B; no peakVRAMdelta measured. Probeelapsed.501s/RSS476MB.

### EXP78 — prerejestracja: opt-in Palace direct basis and cached incremental build

Root wired StoredBasisVector::Dot/AddTo with shared1MiBmaxpartials perGMRES,
floatloads→FP64products/accumulation, MFEMforall+HYPREFP64sums/MPIcomplexreduce.
Real path added separately (not yetGPUqualified); complexconventionmatches
LocalDot(w,b). PALACE_GMRES_FP32_DIRECT requires FP32storage and existingMGS;
defaultFP64 and FP32unpack path preserved. OneUnpack beforeApplyBA remains
because operator expectsFP64; innerMGS/update avoidrepeatedfullvectorconversion.
Reliable residual/restarts unchanged. No newFMM/no model/mesh/Order changes.

Before incrementalbuild root copied verified11MiBpre-M3nativebinaries+manifest
to build/m3-basis/pre-m3-native (cache/fallback, not solverdata). Firstcoreheader
APIchange may invalidate Palace TUs, but installeddependencies untouched; jobs2,
existingccache/CMakeobjects retained. Tinycodeprobe recompiles afternewrealhelper,
worker adds relative-to-dot control besidesnormproductgate. Numericgates unchanged.
Next afterterminalbuild: separateFP64 /FP32unpack /FP32direct coax-tiny W.1 with
samebuild/reference/RIGHTpc, wholefields/residual/TEM checks before largercase.
Exactargv sequential:
`python3 tools/experiments/mixed_basis_probe.py build`.
`python3 tools/experiments/mixed_basis_probe.py run artifacts/m3-mixed-basis-cuda-v2-20261019 --seconds 60`.
`python3 tools/dev.py build --jobs 2` (onlyifprobeexecution/arithmeticPASS).

EXP78 allterminalPASS. Probe refreshedrecipe afterrealhelper and extra relative
dotcheck, complexdata allPASS; nativePalacebuild227.712s, installeddependencies
unchanged. Corevectorheader change invalidatedsolverTUs: ccache9hits/329misses,
83buildsteps. NofullMFEM/hypre rebuild. Subsequentimplementation.cpp-only edits
should use retainedobjects; don't deletecaches. Native libpalaceSHA3893de4b66aa9543
6f98958a9057df3f5a61b27c2dd5efdc292c8cee9be12b41. BuildsuccessNOTnumericalPASS.

### EXP79 — prerejestracja: actual Palace coax-tiny three storage paths

Samecurrentnativebuild/mesh/physics, RIGHTpc, defaultFP64operators/factors,
onecoaxdiagnostic3.55GHz, explicitTEMvolumeL2 andsavedfullfields. BaselineFP64,
existingFP32unpack, thennewFP32direct; bothcandidatesreferenceidenticalFP64fields.
No nativecomplexcoarse combination yet (existingrunnerguardFP64onlypreserved).
SamefrozenK field/raw/TEM/S gates; compare actualmarkers/directflag plus residual
and wholefields, not justexecution. Threecheap<=60sruns, localGPU/noappsclose,
existingRAM/VRAMonlyrunnercaps. These are W.2tinyfilters; W.1orthogonality/realpath
and largerW.2/W.3 stillpending, no speedup/promotion fromtiny alone.
Exactargvs sequential (next onlyafterprevious terminalexecutionPASS):
`python3 tools/dev.py run coax-tiny artifacts/m3-coax-tiny-fp64-20261019 --basis fp64 --pc-side right --coax-l2 --save-fields --memory-marks --phase-trace --seconds 60`.
`python3 tools/dev.py run coax-tiny artifacts/m3-coax-tiny-fp32-unpack-20261019 --basis fp32 --pc-side right --coax-l2 --save-fields --field-reference artifacts/m3-coax-tiny-fp64-20261019 --memory-marks --phase-trace --seconds 60`.
`python3 tools/dev.py run coax-tiny artifacts/m3-coax-tiny-fp32-direct-20261019 --basis fp32 --direct-basis --pc-side right --coax-l2 --save-fields --field-reference artifacts/m3-coax-tiny-fp64-20261019 --memory-marks --phase-trace --seconds 60`.

EXP79 three terminalexit0/noOOM, rootverifiedsamecurrentnativeSHA/config/fields
and rawmarkers. FP64/unpack/direct62/64iter, maxraw9.026e-7/9.045e-7/9.042e-7.
DirectfieldE/B7.528e-7/1.004e-8,ΔS3.412e-9,ΔVSWR6.751e-9,Δportpower6.823e-9.
TEMq4/6PASS~.4953%E/.4558%B. Times18.714/18.723/18.709s, no speedupclaim.
Cgroup610.3/589.8/595.1MB; GPUprocess4.658/4.658/4.687GB, no GPUpeakreduction.
Rootanalysis artifacts/m3-coax-tiny-root-analysis-20261019.json.
Docs mixed-basis/ARCH/INDEX/PLAN/M3/testing updated. M3stillACTIVE; W.1actual
orthogonality/realpath/faultdetector and largerW.2/W.3pending. No promotion.

Finalvalidation EXP77–79:106unitPASS pinned/system90PASS16SKIP. SameLuna
read-only docs-gardenPASS, no scope/source/metric contradictions. Checker and
diffcheckPASS. Rootreview numerical receipts/rootanalysis/currentnative match.
M3ACTIVE; commitlocalonly, no publicpush/defaultpromotion/goalcompletion.

### EXP80 — prerejestracja: actual exported Palace vector API / MGS CPU + CUDA

Previous turn progress cb40b75: complexcoax-tiny/raw/TEM/S/fieldPASS; W.1real/
orthogonality/faultdetector pending. New oneTU probe links verified libpalace.so
StoredBasisVector methods (not copiedCUDAkernels); native/sourceSHA pinned.
No Palace/dependency rebuild, cachedmpicxx/link max120s, repeat expectsno-op.
CPU andCUDA separate one-rankprocesses, vectors n0/1/1009/65537/131071, floatdata
owned independently: originalsource overwritten afterPack while savedUnpack
reference retained. Compare directDot/AddTo vs legacyFP64Dot/Add on samequantized
data; scaled+relative dot/axpy gates1e-12. Complexn1: expected31-i, deliberately
wrong31+i must exceed gate. Real/complexMGS16vectors4097DOF, storedGram/normalized
orthog<2e-7, directvslegacy normalizedvector<1e-12. No near-dependentbasis or
multi-rank guarantee. SameFP32storage/FP64arithmetic/reduction, noTCclaim.
Runtime6GiB4CPU/noSwap/RAMtmpfs512MiBeach/networknone,60s each; CUDA initial
HYPREUmpirepool256MiB via existingpublicAPI; no appsclose/paidcompute. No solver
performancepromotion from APIprobe. 109systemtests93PASS16SKIP.
Exactargvs sequential, nextonlyafterprior terminalPASS:
`python3 tools/experiments/stored_basis_probe.py build`.
`python3 tools/experiments/stored_basis_probe.py build` (cache).
`python3 tools/experiments/stored_basis_probe.py run artifacts/m3-stored-api-cpu-20261019 --device cpu --seconds 60`.
`python3 tools/experiments/stored_basis_probe.py run artifacts/m3-stored-api-cuda-20261019 --device cuda --seconds 60`.

EXP80 stopped atbuildlinkexit1 after7.385s, no numericalrun. CPPcompile passed;
GPU-built libceed requires libcuda.so.1 missing in driverlessbuilder. Unresolved
cu* fromlibceed; not arithmeticfailure. No retries/limits/dependencychanges.

### EXP81 — prerejestracja: link-time driver stub, real runtime driver

Onlylink/provisionfix: explicitCUDAtoolkit driverstub -lcuda atbuildtime,
--no-as-needed; NEVER stubrpath. Runtime CDI realNVIDIAdriver injected forboth
CPU andCUDA processes, like existingPalaceCPUreference runner. CPU still uses
mfem::Device(cpu)/HYPREhostarithmetic, not GPUtiming. CUDA256MiBpoolunchanged.
Same oneTU/cache, exactEXP80inputs/gates/caps/deadlines, noPalacerebuild.
Exactargvs same four asEXP80, samefreshartifactpaths (no numericalrun existed).
Nextonlyafterprior terminalPASS; no autosourcefix/retry delegated.

EXP81 allterminalPASS/rootverifiedsource/native/binary/state. ActualprobeSHA
3fae204af9c819e6a5da3b1b35860d752469418e836e772b421bf5c51dc6d5d9; Luna first
message accidentallyquoted earlierstandaloneCUDAreceipt, rootusesactualmanifest.
Build1.494s/cacherepeatno-op, noPalace/depsrebuild. CPU/CUDA10/10realcomplex
casesPASS, includingzero,sourceoverwrite,complex31-i vswrong31+i detector.
Maxreldot CPU1.09e-13/CUDA2.17e-14, axpy0 vslegacy. MGSGram max2.724e-9,
orth max6.309e-11, normalizedvectorΔCPU<=2.475e-16/CUDA<=9.015e-17. AllgatesPASS.
CPU .191s/RSS308809728B;CUDA .595s/RSS511172608B/pool256MiB. One-rankwell-
conditionedMGSonly, no near-dependent/distributed claim. Rootanalysis stored
artifacts/m3-stored-api-root-analysis-20261019.json. W.1currenttargetscopePASS.

### EXP82 — prerejestracja: coax-medium native coarse + direct FP32, full sweep

NextW.2samefrozenmediummesh/Order/physics, 3.3/3.55/3.8GHz bothports, RIGHTpc,
tol1e-6/restart240. Newexplicit --coax-sweep preservesexistingfixturefrequencies
while enablingTEMq4/q6/probes instead of silentlysingle3.55GHz. DefaultoldCLI
unchanged. Nativecomplexcoarse uses sameFP64factor/operator forbothvariants;
newcombinednativecoarse+FP32allowed ONLYexplicitdirectflag (oldunpackstillguarded),
pendingthisqualification. No factorprecisionchange/shiftedmatrix; modelunchanged.
FP64reference vsFP32direct: samecurrentnative, fullfields/S/raw/TEM withfrozenK.
180s each, localRAM/VRAMonly/no paidcompute/appsclose, caches/fallbackpreserved.
No nativeCPU/Qpoolcombination; nsys remainsFP64only. No promotion onexecution.
111systemtests95PASS16SKIP. Exactargvs sequential nextafterterminalPASS:
`python3 tools/dev.py run coax-medium artifacts/m3-coax-medium-native-fp64-20261019 --basis fp64 --native-complex-coarse --pc-side right --coax-l2 --coax-sweep --save-fields --memory-marks --phase-trace --seconds 180`.
`python3 tools/dev.py run coax-medium artifacts/m3-coax-medium-native-fp32-direct-20261019 --basis fp32 --direct-basis --native-complex-coarse --pc-side right --coax-l2 --coax-sweep --save-fields --field-reference artifacts/m3-coax-medium-native-fp64-20261019 --memory-marks --phase-trace --seconds 180`.

EXP82 referenceTIMEOUT authoritative terminalRunningFalse/ExitCode-1/noOOM,
runnerexit255/181.026s;4/6solves, no candidate. Nativecoarse WASapplied (four
dimension155934/nnz2466144 complexFP64markers); resultboolFalse meansnotall6
requiredmarkers, not ignoredflag. Incompletepostprocessing/memorymarks expected,
no promotion. TEMq4~13.7s +q6~23.2s PERsolve: sixchecks alone~222s>180limit,
so unchangedretry cannotfinish. Fourrawchecks<1e-6 not fullqualification.

### EXP83 — prerejestracja: bounded frequency shards, same full W.2 quality

Keep180s/run; split existing3.3/3.55/3.8GHz into onefrequency/twoportjobs.
New --coax-frequency selects ONLYexistingfrozenfixturepoint, preservesmesh/
boundaries/ports/physics/tol/restart and allTEMq4/q6/wholefields/Schecks. Mutually
exclusivewith --coax-sweep; no weakerquadrature or omittedport. Same nativeFP64
coarse forFP64ref andexplicitFP32direct. Reference/candidate grouped perfrequency,
allthreepairsmustPASS before W.2 fullsweepqualification. No Palacerebuild.
Rootfirstreviews3.3pair beforequeueingremaining. 112systemtests96PASS16SKIP.
For each pair F in [3.3,3.55,3.8], tag in [330,355,380], exactcommands:
`python3 tools/dev.py run coax-medium artifacts/m3-coax-medium-native-fp64-F-20261019 --basis fp64 --native-complex-coarse --pc-side right --coax-l2 --coax-frequency F --save-fields --memory-marks --phase-trace --seconds 180`.
`python3 tools/dev.py run coax-medium artifacts/m3-coax-medium-native-direct-F-20261019 --basis fp32 --direct-basis --native-complex-coarse --pc-side right --coax-l2 --coax-frequency F --save-fields --field-reference artifacts/m3-coax-medium-native-fp64-F-20261019 --memory-marks --phase-trace --seconds 180`.
Paths replace F by tag (argvfrequency numericF). No autosourcechanges/retries;
nextonlyafterprior authoritative terminalexecutionPASS, root ownsanalysis.

EXP83 firstpair3.3GHzterminalPASS, samecurrentnative/coaxmesh/config,45/47iter
each, reference114.311s/candidate115.312s. Candidate maxraw8.335e-7, E/BΔ
7.554e-7/8.503e-9, TEMq4/6~.4937%E/.4558%B PASS. Nativecoarsemarkers2each,
candidateDIRECTtrue. RootverifiedS/native/state andmemoryphase intervals;
rootanalysis artifacts/m3-coax-medium-330-root-analysis-20261019.json.
Allocationmetricmanagedpeak4.7996→4.2176GB(~12.1%lower); GMRESphase4.429/3.297s
vs4.390/3.316s. This is NOTphysicalRAM/VRAM reduction: cgroup2.758→2.924GB,
GPUprocess4.660→4.689GB. No speedupclaim, other2frequenciesstillpending.
Next exactremainingEXP83pairs355/380, sameflags/caps/gates; rootreviewedfirstpair.

EXP83 all6shards terminalPASS, full W.2 threefreq/bothports/raw/TEMq4q6/fields/S
covered. All45/47iter; candidateEΔ<=7.554e-7/B<=8.503e-9, raw<=8.335e-7.
Rootanalysis artifacts/m3-coax-medium-sweep-root-analysis-20261019.json includes
allstates/fields/complexS/VSWR/portpower andallocationmetrics. Allocationpeak
same12.126%lower allfreq; physicalcgroup/GPUpeaksNOTimproved. Runs114.3sFP64,
115.3/116.4/115.3sFP32direct: no speedup. Geometry/Order/restart240 preserved;
full3freqsinglejobEXP82 remainsTIMEOUT, not rewritten asPASS.

### EXP84 — prerejestracja W.3: fresh samebuild FP64 reference, one medium antenna

W.1actualAPI/MGS andW.2fullsweep PASS justify bounded W.3. Same frozen3.50GHz/P2,
Order2/PA, mesh/ec56c9a7..., nativecomplexFP64coarse, RIGHTpc, explicitK64 to
match qualifiedM1profile, tol1e-6, hyprepool256MiB, releasebasis/finalsolver.
Both futurevariants must use SAME savedinitialapproximation fromcompleted
m1-antenna-resident-fp64-20261018 (startingguess only, not accuracyreference).
FreshFP64 checked against independentlytighter nativecoarse r2raw7.28e-10;
root preflight verifiedinput/reference/source/geometry hashes beforelaunch.
Candidate later referencesfreshFP64 plusfrozenK. No profilers/phase-trace,
no input/mesh/highquality changes. Existingfullrun1800s/60GiB/noswap/hostguard6GiB,
no paidcompute/appsclose, source/build/inputcache retained. Not a coldstart
benchmark; samewarmguess asM1profile, disclosure retained in commandmanifest.
Currentnative unchanged fromEXP78; no rebuild needed. Firstreference only:
`python3 tools/dev.py run tshaped-medium artifacts/m3-antenna-native-fp64-20261019 --basis fp64 --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --save-fields --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m1-native-complex-coarse-antenna-tight-r2-20261018 --seconds 1800`.
Rootreviewterminalquality before preparingcandidateexactargv; no auto retry.

EXP84 terminalPASS/rootverifiedstate/currentnative/freshfieldreferencebytes.
35iter, rawRHS8.35543e-7, E/Bvsindependenttight6.9955e-8/9.8852e-8, sevenentries.
Elapsed414.164s; cgroup58889510912B, managedpeak55147611962B, cuDSS25008217684B.
GPUprocesscounter2147483648B (doesnotmeasureallUVMresidency); minhostavailable
17846087680B>6GiBguard. Initialguess/nativecoarse/release/memoryflags confirmed.
No claim speedupfrom414vsolder447; background/cache/time differ. Freshreference
nowqualified forsamebuildcandidatecomparison, notcoldstartbenchmark.

### EXP85 — prerejestracja: FP32direct W.3 matched fresh reference

Onlybasisrepresentation/operations change vsEXP84: FP32DIRECT, allFP64operator/
factor/reduction/residual, samefrozenmesh/port/freq/order/warmguess/K64/tol1e-6/
pool256MiB/releaseflags. ReferencefreshEXP84 plusitsindependenttightcontrol.
Compare actualraw,wholefields,S/Z/VSWR,energy/portpower,allocation/cgroup/time;
no newtrace/profiler, no deadline/capchange, no environment/app intervention.
Rawguard1e-6 and frozenK fields1%/ΔS1e-3/VSWR.01/power1e-3; fallbackretained.
Rootverifiedfreshreferenceinput beforelaunch; sameoneGPU/local/no paidcompute.
Exactargv:
`python3 tools/dev.py run tshaped-medium artifacts/m3-antenna-native-direct-20261019 --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --save-fields --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m3-antenna-native-fp64-20261019 --seconds 1800`.

EXP85 terminalPASS, rootverifiedsamecurrentnative/state/raw/wholefields/S/energy.
35iter/no restart, rawRHS8.35625e-7, maxΔE/B1.1323e-8/1.5949e-9. ΔS3.447e-10,
ΔVSWRP2 6.777e-10,Δportpower5.123e-11,Δenergy1.388e-9 allfrozenKPASS.
Cgroup58889510912→56018751488B (−2870759424B/~4.87%); managed55147611962→
52276667194B (−2870944768B/~5.21%). cuDSSsame25008217684B. GPUprocesscounter
2147483648→2176843776B excludesfullUVMresidency, not VRAMreductionproof.
Time414.164→409.715s onlyonepair, no statisticallyestablishedspeedup.
Allocationowner model:36materializedFP64vectors vs36packed+2FP64workvectors+
1MiBpartials predicts EXACTmanagedpeakdelta;45logicalVcapacity includesuntouched
device allocations, don't calllogicalbytesphysical. Rootanalysis complete in
artifacts/m3-antenna-root-analysis-20261019.json. Goalusefulmemorygain observed
but NOTcomplete: M3policy test, M4/M5/M6/M7/finalqualification stillrequired.
Docs mixed-basis-validation, PLAN/M3/INDEX/ARCH/testing updated; M3ACTIVE.

Finalvalidation EXP80–85:112unitPASS pinned; system96PASS/16SKIP. SameLuna
read-only docs-gardenPASS, source/metric/scope reviewed incl actualprobe receipt,
EXP82FAIL retained, W2shards andsamebuildwarmW3, no falseVRAM/speed/defaultclaim.
Checker/diffcheckPASS; rootanalysis matches currentnative andterminalstates.
M3ACTIVE/policyexperiment next; M4–M7pending. Localcommit only/no push.

## EXP86 — opt-in managed basis prefetch (preregistered, 2026-10-19)
M3 active. Hypothesis: prefetch only FP32direct Dot sources before MFEM
stream0 kernels may reduce demand faults; may also evict PC pages and lose.
No CPU preferred/readmostly advice, no extra sync, no physics/restart change.
Strict managed-pointer/concurrentManagedAccess checks; CUDA errors fail.
Log request counts/bytes, never call them measured transfers/residency.
Primary source CUDA12.9 Runtime API memory cudaMemPrefetchAsync, accessed
2026-10-19: https://docs.nvidia.com/cuda/archive/12.9.0/cuda-runtime-api/group__CUDART__MEMORY.html
Installed MFEM forall.hpp:598 default kernel stream, cuda.hpp:28 stream0 sync.
Current qualified native+manifest preserved build/m3-basis/pre-prefetch-native.
Incremental build only; no dependency rebuild. First filter samebuild coax-tiny
FP32direct RIGHT,3.55GHz/bothports/TEM/fields,60s. Compare raw<=1e-6, fields1%,
S1e-3/VSWR.01/power1e-3 and positive prefetch markers per solve.
If pass, matched W.3 no-prefetch/prefetch warmstart K64/nativecoarse/pool256,
1800s/60GiB/no swap/hostguard6GiB; root analyzes total time/memory/quality.
Do not promote speedup from requested bytes or a single small run.

EXP86 tiny terminalPASS/rootverified: samebuild/config,62/64iter,raw<=9.045e-7.
MaxΔS9.132e-10/ΔVSWR9.707e-10; fields within1%; exact rootmetrics in
artifacts/m3-prefetch-tiny-root-analysis-20261019.json. Prefetch requests
3906+4160 (1.392+1.482GB requested, not migrated). 19.661/18.699s onepair
smallcase not speedup evidence. Build13.846s/5steps only Palace, cache counts
cumulative; dependencies untouched. Proceed matched W.3 per preregistration.
Exact tiny argv: common `python3 tools/dev.py run coax-tiny <output> --basis fp32 --direct-basis --pc-side right --coax-l2 --save-fields --field-reference <ref> --memory-marks --phase-trace --seconds 60`; control output=m3-prefetch-tiny-control-20261019/reference=m3-coax-tiny-fp64-20261019; candidate output=m3-prefetch-tiny-on-20261019/reference=control plus --basis-prefetch (all artifacts/).

EXP86 W.3 control terminalPASS/rootverified:408.622s/35iter/raw8.35621e-7,
all7fieldregionsPASS vs qualified FP32direct, E7.238e-9/B5.086e-10. Cgroup
56025440256B. No prefetch marker. Samebuild candidate now uses this reference.
Control exactargv: `python3 tools/dev.py run tshaped-medium artifacts/m3-prefetch-antenna-control-20261019 --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --save-fields --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m3-antenna-native-direct-20261019 --seconds 1800`.
Candidate changes output=m3-prefetch-antenna-on-20261019/reference=control
and adds --basis-prefetch; all other args identical.

EXP86 W3 candidate terminalPASS/rootverified, samebuild/config,35iter,
raw8.35655e-7, maxfieldE7.489e-9/B4.233e-10. Native coarse/prefetch applied.
Cgroup56025440256→56021962752B (effectivelysame), managedsame52276667194B,
cuDSSsame25008217684B. Marker1260requests/56542368960requestedB consistent
with35*36complexpartreads*11218724*4; NOT measured migrations. Whole run
408.622→396.526s (~3% onepair), NOT statistically established speedup.
Full frozenKmetrics: artifacts/m3-prefetch-antenna-root-analysis-20261019.json.

## EXP87 — measured late GMRES UVM movement (preregistered, 2026-10-19)
Extend existing diagnostic-only Nsight runner to explicit FP32direct (including
prefetch); no RF qualification in partial profile. No C++/native change.
Samebuild W3/control+prefetch, window30:2 (latebasis), samewarmstart/K64/
nativecomplexcoarse/pool256. Count actual Nsight copy enums/bytes periteration,
phase times inclusive, no sum of overlappingcopy/kernel times. Capture excludes
RF fields and stopscleanly afterwindow; timeout1800/60GiB/no swap/guard6GiB.
Temporary profiler output RAM /dev/shm; saved bounded report is diagnostic output,
not solver disk scratch. Retain profilerwarnings/clockcoverage failure as failure.
Exact commonargv: `python3 tools/dev.py run tshaped-medium <output> --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --nsys-window 30:2 --seconds 1800`. Outputs artifacts/m3-prefetch-profile-{control,on}-20261019; on adds --basis-prefetch.

EXP87 FAIL: full-process late-window collector exceeded60GiB cgroup, exit137/
OOMKilled true,456.588s, peak64424509440B. Profilecompletefalse/clockfalse/
CUDAeventlosswarning; no transfer or phase metrics accepted. No retry/capraise.
NormalEXP86 W3 passed; this failure is diagnostic collector memory pressure.

## EXP88 — bounded selected-window collection (preregistered, 2026-10-19)
Fix diagnostic collection instead of raising memory limit: cudaProfilerStart/
Stop around existing selectediterations, nsys --capture-range=cudaProfilerApi
--capture-range-end=stop; process still exits via clean diagnostic exception.
Start after draining earlier kernels, then retain all3clock syncanchors for2iter.
CUDA profiler API only in adapter/weak hook, opt-in PALACE_PROFILE_CAPTURE_RANGE.
No ordinary run math/precision/allocationpolicy change; fallback native+manifest
build/m3-basis/pre-selective-profile-native. CUDA12.9 profiler and Nsight
2026.5.1 pinned primary guidance, accessed2026-10-19:
https://docs.nvidia.com/nsight-systems/UserGuide/index.html
First smoke coax-tiny window0:2 <=60s, both diagnostic control andprefetch if
needed. Require cleanstop/clock/coverage/no collectorwarnings, not RFpass.
Then rerun late30:2 W3 diagnostic pair at same1800s/60GiB/no swap cap (new
artifacts m3-selective-profile-{control,on}-20261019, exactEXP87argv).
Add captureflag onlyprofiling runner/unsetforordinary, counters marker begin/end.

EXP88 firsttiny FAIL as completeprofile:10.422s/exit0/1.832GBcgroup, all
clock/window/cleanstop/coveragePASS but DIAGNOSTIC_EVENT severity2 'Not all
CUDA events might have been collected.' No totals accepted. Primary NVIDIA
engineer explains same2026.5.1 forcedflush-warning case (not proof forours):
https://forums.developer.nvidia.com/t/nsight-systems-2026-5-1-produced-112-collected-100-warning-despite-complete-coverage-of-32-kernels/384749
Nexttiny diagnostic changes only --capture-range-end=none: capture starts at
selectedwindow but collection ends at natural cleanprocess exit, so capture
includes boundedcleanup; window remains offlinefiltered. Keep warninggate
unchanged, no largecase untilwarningfree. No native rebuild for CLI-onlychange.

EXP88 tinyv2 PASS/rootverified: profilecomplete true, capture/window/clock/
coverage/cleanstop true, zero collectorwarnings. Naturalexitaftercapture-start
fixeswarningwithoutgateweakening. 8.423s/1.397GBcgroup. Partial diagnostic
resultcompletefalse deliberate, not RFpass. Proceedlate W3 pair withsame
newnative andsameparams asEXP87, only boundedcapture policy changed.

EXP88 latecontrol terminalPASS/profileonly rootverified:383.343s/57.623GB
cgroup, profilecomplete true/zerowarnings/allclockcoveragePASS. Twoiter late
window15.192s,PC13.567s inclusive/coarse4.869s included,orthog.706s.
Measured UVM HtoD10.900GBfault+126.512GBspeculative/DToH137.320GBeviction;
actualenum mapping retainedinreport, not requestedbytes. Candidate sameargv
except artifacts/m3-selective-profile-on-20261019 and --basis-prefetch.

EXP88 latecandidate terminalPASS/profileonly rootverified:381.014s/57.571GB
cgroup, samebuild/config, profilecomplete/clockcoverage/cleanstopPASS,
zerowarnings. Selected2iter14.761s vs15.192; orthog.330 vs.706s,PC13.505
vs13.567s (coarse4.879 vs4.869included). ActualUVM total272.984 vs274.732GB,
−0.6363%, periter136.492 vs137.366GB; no claimalltransfersareblocking.
Explicit HtoDprefetch5.654GB, fault9.982GB/speculative121.123GB/DToHeviction
136.224GB; numericenumlabels retained in artifacts/m3-prefetch-profile-root-analysis-20261019.json.
Decision: useful localorthogimprovement, not cure forPC residency; prefetch
remainsopt-in, no whole-solve speeduppromotion fromonepair. FP32directmemory
gainEXP85 remains primaryqualifiedbenefit. Restart120vs240 notrun:35iter<K64,
so neither reduces materializedbasis; below35 changes convergence/cost for
limitedsaving; no evidence tospendrun onthat now. M3.2 policy assessmentdone.

## EXP89 — final M3 W.2 prefetch quality regression (preregistered, 2026-10-19)
Newnative EXP88 no ordinaryphysicschange. Threeexistingmediumcoaxfrequency
shards3.3/3.55/3.8GHz,bothports,180s each, nativecomplexcoarseFP64/RIGHT;
FP32direct+prefetch vs independentqualifiedEXP83 FP64 fields (samefrozenmesh).
No new speedclaim fromdifferentbuildreference. Need raw<=1e-6/wholefields1%,
ΔS1e-3/VSWR.01/power1e-3, allTEMq4/q6,positiveprefetch/native markers.
Exact commonargv: `python3 tools/dev.py run coax-medium <output> --basis fp32 --direct-basis --basis-prefetch --native-complex-coarse --pc-side right --coax-l2 --coax-frequency <f> --save-fields --field-reference <ref> --memory-marks --phase-trace --seconds 180`.
Outputs artifacts/m3-prefetch-medium-{330,355,380}-20261019; references
artifacts/m3-coax-medium-native-fp64-{330,355,380}-20261019. Standardnoswap
60GiB/6GiBhostguard, no dependencybuild/paidcompute. StoponfirstFAIL.

EXP89 terminalPASS all3shards/bothports/45,47iter/raw<=8.334e-7,wholefields
E<=7.555e-7/B<=9.423e-9. Allq4/q6TEM records E<.495%/B<.457%. Native
andprefetchmarkersapplied; rootRFdeltas qualification pending analysisreceipt.
115unitPASS pinned/system99PASS16SKIP.

## EXP90 — integrated W.3 quality after diagnostic hook change (preregistered)
EXP86 W3 used immediateprecedingnative; EXP88 onlyadds inactive diagnostic
hook toordinarypath. Still rerun fullW3 oncurrentnative toprove integrated
quality; no needrepeatbuild. Samephysics/warmstart/K64/pool256/nativecoarse.
Exactargv: `python3 tools/dev.py run tshaped-medium artifacts/m3-prefetch-antenna-final-20261019 --basis fp32 --direct-basis --basis-prefetch --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --save-fields --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m3-prefetch-antenna-control-20261019 --seconds 1800`.
Same60GiB/noswap/6GiBhostguard; field/raw/S/VSWR/power frozenK, memory
expected same compressedbasis; speed statisticalqualification deferredtoM7.

EXP90 terminalPASS/rootverifiedcurrentnative:35iter/399.446s/raw8.35668e-7,
wholeE/B6.684e-9/4.860e-10,ΔS2.946e-10/ΔVSWR2.865e-10/power3.076e-11.
Currentnative matches allEXP89shards andEXP90, no activeprofileflags inW3.
EXP89 RFmaxΔS5.666e-9/ΔVSWR4.794e-9/totalportpower1.077e-8, allTEMPASS.
Rootreceipt artifacts/m3-prefetch-final-root-analysis-20261019.json. NoW4/W5
claim. Nextrelink existingactualAPIprobe againstcurrentnative CPU/CUDA,
6GiB/4CPU/noswap/RAMtmpfs512MiBeach/60s perrun, using existingtool.

EXP90 actualAPI relink currentnative CPU/CUDA PASS/all10rows+realcomplexMGS,
ownership/conjugationdetectorsPASS, FP64accum/quantization gates unchanged.
No managedprefetch flag inAPIprobe; actualprefetch qualifies viaEXP86/89/90.
M3.1–M3.3 assessment complete: usefulmemorygain, policybytes measured;
optionalprefetchkept/no globaldefaults/speedpromotion; restartconditionalnotrun
justified. W4/W5 and allM4–M7 remain. ActiveM4 sourceaudit setupreuse next.
New report docs/basis-prefetch.md and M4 checkpoint; finaldocsreview pending.

FinalEXP86–90 validation:115pinnedPASS/system99PASS16SKIP;8shellPASS,
docschecker/diffcheckPASS. SameLuna read-onlydocs-garden foundstaleM3ACTIVE
line in mixed-basis-validation; rootcorrected. Rootreviewedcode+currentnative
receipts andstrict profile enumtotals; no gateweakening, no SSDoffload/default
change. M3completeassessment/M4ACTIVE. Next sourceaudit existingdrivenloop/
SetOperator/factorizationcounts before writingcache. GlobalgoalNOTcomplete:
M4–M7/W4/W5/finalreproduciblequalification remain. Localcommitonly/no push.

## EXP91 — one-frequency port setup reuse (preregistered, 2026-10-19)
M4 sourceaudit: drivensolver.cpp SweepUniform outerexcitation/innerfrequency
reassembles A2/A/P and calls kspSetOperators perRHS. Nativecomplexcoarse
SetOperator clearsanalysis/factors everycall. EXP89 2nativecoarsemarkers per
singlefrequency confirms2factorizations. LumpedPort AddDamping loopsallactive
ports irrespectiveexcitation; AddExcitation filtersidx onlyRHS. A2/A/P depend
onfrequency/materials/mesh/boundaries, notexcitationidx. Restrictprototype to
singlefrequency/fixedmesh/oneMPIrank/multipleLPexcitations/noWave/Floquet.
Keep same A2/A/P ownership throughlastsolve; no multfreqfactorcache/reordering.
Runtime --port-setup-reuse opt-in, --setup-audit for control/candidate.
Audit records driverbuild/reuse, native CSRfnv1a64 structure/values fingerprints
(notcryptographicproof) and synchronizedanalysis/factor times. Noextra
workingcopy/cache ofmatrices, no SSD/swap, preserveglobaldefault. Native+manifest
fallback build/m4-reuse/pre-m4-native. Buildcached onlychangedPalaceTUs.
First samebuild tinycoax3.55GHz/bothports/fields/TEM/right FP32direct/nativecoarse
matchedcontrol/reuse,60s. Require raw1e-6,wholefields1%/S1e-3/VSWR.01/power1e-3,
onebuild+onereuse marker and1nativefactor vs2control, samebaselineCSRhashes.
Ifpass W2 threefrequencyshards180s each and justifiedbothportsantennaW3
withunchangedmesh/terminations, notdeclareantennaspeed fromcoaxonly.
Symbolicreuse decisionseparate fromnumericreuse basedmeasuredanalysiscost.

EXP91 buildPASS15.611s/5steps, no dependencyrebuild. FournewunitguardsPASS
(37devtests total); typo ininitialunithelpername corrected beforebuild.
Tinycommon exactargv: `python3 tools/dev.py run coax-tiny <output> --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --setup-audit --coax-l2 --save-fields --memory-marks --release-gmres-basis --release-final-solver --field-reference <ref> --seconds 60`.
Control artifacts/m4-reuse-tiny-control-20261019/ref artifacts/m3-coax-tiny-fp64-20261019;
candidate artifacts/m4-reuse-tiny-on-20261019/ref control, adds --port-setup-reuse.

EXP91 terminalPASS/rootfrozenKPASS, samebuild/config39/42iter, raw<=9.601e-7.
2build/2nativefactors control vs1build/1reuse/1nativefactor candidate. Control's
twoCSRstructure+valuefingerprints identical. Cross-process candidatevaluehash
differs; do NOT claimbitwise CSRreproducibility acrossprocesses. Fingerprints
are diagnostic identity ofbaselineportsetups, notqualitynorm. Frozenquality
usesactualraw/S/VSWR/power/wholefields; receipt m4-reuse-tiny-root-analysis.
18.623→17.755s onepair tiny, noantenna/statisticalspeedclaim. Peak629→593MB.
Proceed W2: currentnative/bothports3pointshards withsameparams; first355control
then355reuse and330/380reuse vsqualifiedFP64refs. No otheralgorithmchange.
Exactcommonargv: `python3 tools/dev.py run coax-medium <output> --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --setup-audit --coax-l2 --coax-frequency <f> --save-fields --memory-marks --release-gmres-basis --release-final-solver --field-reference <ref> --seconds 180`.
Control355 output artifacts/m4-reuse-medium-control-355-20261019/ref artifacts/m3-coax-medium-native-fp64-355-20261019; reuse output artifacts/m4-reuse-medium-on-{355,330,380}-20261019 adds --port-setup-reuse,355ref currentcontrol/others respectiveEXP83FP64.

EXP91 W2 all4runs terminalPASS, rootreceiptpending:45/47iter/raw<8.34e-7,
fields/TEM/auditPASS. 355control115.196s vsreuse110.150s,2→1factor. Independent
330/380refsPASS. BaselinecontrolportCSRfingerprintsidentical; not crossprocess
bitwise claim. Analysis1.1–1.3s/factorhot1.14s inW2, initialJITfactor8.4s.

## EXP92 — bounded both-port antenna study with explicit partial seed
Historicalcold M1 oneport151iter/1090–1384s; two coldports likelyexceed1800s.
Use the SAME existingP2 approximate field seed (m1resident) incontrol/candidate;
P1 remains explicitzero. Thisis initialguessonly, notaccuracyreference. Preserve
strictfullsnapshotvalidation; new --partial-initial-fields explicitly allows
verifiedsourceexcitation subsettarget, requiringidenticalotherphysics/mesh/
dependencies, originalsourceinventory/complete/hash. No fabricatedmergedresults.
Runner passesverifiedexcitationmask; driver zeros unseededRHS withdistinctmarker,
neverreusesprecedingportfield accidentally. Missingseedfiles stillfailbeforelaunch.
No change to strictaccuracyreferencepath. No warmstartspeedclaim/comparison;
setupreuse controlledbyidenticalstarts. Unitguards thenexistingtinyfilter and
W3bothportscontrol/reuse,1800s/60GiB/no swap/6GiBguard. K64/pool256/RIGHT,
FP32direct/nativecoarse, no prefetch. IfcoldP1doesnotfit stopatcap andrecordFAIL,
notraisebudget/altermesh/tolerance. Both-ports flagchangesonlyRHSrequests,
preservesallphysicalportimpedances. W4/W5 remainfinalM7.

EXP92 partialseedunitguardsPASS (39devtests). --excitation selectsoneexisting
physicalLPforseed/shards, neverchanges R/geometry. Beforeheavycase actualtiny
filter: sourceoneP2 (`--excitation 2 --coax-fields --save-fields`), thenbothports
control/reuse withverifiedpartialP2seed andtightertol1e-8 soP2 still exercises
PC. SameK64/nativecoarse/pool256/right, no prefetch;60s each. Rootargv below
are sentexactly tosameLuna. Newbuildonlydrivensolver weakseedbranch, depscached.
Tiny source artifacts/m4-partial-seed-tiny-source-20261019; bothcontrols
artifacts/m4-partial-seed-tiny-{control,on}-20261019, refsqualifiedEXP91tiny
controlthenfreshcontrol; no accuracyclaimedfromsourceexecutionalone.

EXP92 integratedtinybuild9.535s/sourceP2+bothcontrol/reuse PASS, partialmask
zerosP1/loadsP2provenactualmarkers. Tightfiltertol1e-8 requiresreliablerestart
onP1:58/17iters bothvariants, finalchecks<=9.20e-9; failedintermediate
recurrencecheckretained/corrected. Fields+setupauditsPASS. FulltargetP2seed
M1residentpasses strictpartialverify againstcurrenttarget+native (rootchecked).

EXP92 W3 commonexactargv: `python3 tools/dev.py run tshaped-medium <output> --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --setup-audit --both-ports --save-fields --memory-marks --release-gmres-basis --release-final-solver --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --partial-initial-fields --seconds 1800`.
Controloutput artifacts/m4-reuse-antenna-control-20261019. No completebothport
fieldrefexistsyet; controlraw/S/energy/E+Bsaved, P2crosscheckagainstqualified
M3fullfield afterwards, P1qualityscopeexplicitno independenttightfullrefyet.
Candidateoutput artifacts/m4-reuse-antenna-on-20261019, adds --port-setup-reuse
and --field-reference artifacts/m4-reuse-antenna-control-20261019. Guard60GiB/
noswap/host6GiB, stopat1800s. No alteredmesh/physics/tolerance.

EXP92 W3 control FAIL/OOM exit137/550.848s, cgroup64378429440B, hostguard
notcrossed. P1completed44iter/raw7.490e-7 andsavedfields; P2started butnot
complete. DoNOTuseincompletewholejobasaccuracyref ordeclare2RHSqualified.
Peakcauseevidence: managedlive48.686GB afterP1solve→65.177GB duringpostproc;
remainslive, nextPCend64.929GB (peak66.264), thenOOM. No capraise/retryunchanged.

## EXP93 — release domain-energy workspace between solves (preregistered)
Hypothesis: persistent DomainPostOperator mass/energyworkspace causes betweenRHS
pressure. Add explicit opt-in release afterallmeasurements/fielddiagnostics/
AddEstimate, rebuildsameoperators onlyafter nextGMRES. Preservemeasurementcache,
primaryE/B, CSV/fields andphysicaldefinitions; no visualization writes/AMR for
thispilot. Neverholdtwoenergyoperators while rebuilding. Same releasepolicy
inreusecontrol/candidate isolates setupreuse; measuremarker livebytesdrop.
MinimalPostOperator resetAPI; no newdeps/diskcache/floatingtypechange.
Tinycontrol+policy pairedagainstlastqualifiedEXP92 samephysicalfields then
mediumsinglefrequency/bothports,180s; onlythenbothportantenna control+reuse
at1800s/60GiB/noswap/guard6GiB andsameverifiedpartialseed. Ifmemorydropnot
observed orqualityfail, keepFAIL andinvestigate, notrelaxgates.

EXP93 initialvalidation40devtestsPASS. Tiny commonexactargv: `python3 tools/dev.py run coax-tiny <output> --basis fp32 --direct-basis --native-complex-coarse --port-setup-reuse --setup-audit --pc-side right --krylov-size 64 --hypre-pool-mib 256 --coax-l2 --save-fields --memory-marks --release-gmres-basis --release-final-solver --field-reference <ref> --seconds 60`.
Control artifacts/m4-energy-tiny-control-20261019/ref artifacts/m4-reuse-tiny-on-20261019.
Candidate artifacts/m4-energy-tiny-on-20261019/ref currentcontrol adds
--release-postprocess-energy. CheckenergyCSVaswellasraw/S/wholefields/TEM;
markers releaseP1 andrebuiltP2 eachonce, measuredlivebytesdrop. No dualoperator
copies (resetemptyfirst, replacementconstructedonlybeforelaterpostproc).

EXP93 tinyterminalPASS/rootverifiedsamebuild/config39/42iter/raw<9.601e-7,
fields/audit/release+rebuildPASS; maxrelativeCSVenergy3.483e-9. Managedlive
127.942→91.082MB atrelease thenrebuild127.942MB. Actualdrop36.860MB, not
assumed16GBfullmodel. Build40.273s/12Palacesteps/noexternaldepsrebuild.
Medium355 nowcontrolreleaseonly vsreuse+release, samephysics/K64/pool256.
Common exactargv: `python3 tools/dev.py run coax-medium <output> --basis fp32 --direct-basis --native-complex-coarse --setup-audit --release-postprocess-energy --pc-side right --krylov-size 64 --hypre-pool-mib 256 --coax-l2 --coax-frequency 3.55 --save-fields --memory-marks --release-gmres-basis --release-final-solver --field-reference <ref> --seconds 180`.
Outputs artifacts/m4-energy-medium-{control,on}-20261019; controlref artifacts/m4-reuse-medium-control-355-20261019, onref currentcontrol/add --port-setup-reuse.

### Historyczny research integracji, 2026-10-19 — poza aktywnym zakresem
Poniższe propozycje Rust/SolidCraft/FieldCraft zostały wycofane przez użytkownika;
nie stanowią zadań ani warunków ukończenia aktualnego goal.
Useraskswholegoalstatus, accuracyvspeed, Rust/SolidCraft andalternativeengines.
LateststateEXP93 tinyPASS, mediumpairpreparedNOTLAUNCHED; no palace-run
containers live whenchecked. M4stillACTIVE/WIP; M5–M7 notcomplete.
Primaryresearch: SolidCraftROADMAP Scope(ownerdecision2026-10-07) defers
Simulation; separate tangency-labs/fieldcraft ispureRustCAE forstructures/heat/
LBM, notfoundRFMaxwellbackend. FieldCraft docs/adr/0001-libraries.md requires
permissive/cleanroomdependencies, itsownsolveralgebra; crates/lbm-gpu implements
wgpu/WGSLFP32flow checkedagainstCPU, notantennaEM/cuDSS. Noauthorendorsement
ofPalacefound. Proposedfuturecontribution: Rustanalysis/export/resultadapter
withPalaceasanexternalworker, notimmediatefullrewrite; confirmmaintainerfit.
URLs: https://github.com/tangency-labs/solidcraft/blob/main/ROADMAP.md
https://github.com/tangency-labs/fieldcraft/blob/main/README.md
https://github.com/tangency-labs/fieldcraft/blob/main/docs/adr/0001-libraries.md
https://github.com/tangency-labs/fieldcraft/blob/main/crates/lbm-gpu/src/lib.rs
Alternativeresearch: gprMaxdocumentedCUDAFDTD+ports/S/gain; fdtdzCUDAphotonic
lowlevel, ngsolve.gpu supportsCUDAngscuda (officialcurrentdemoPoisson, notproof
ourRFpipeline). No sameantenna benchmarkagainstPalaceperformed. Consider
boundedreferenceantennaFDTDpilotbeforeanyreplacementclaim; finefeed/slots/CFL
needcostestimate. Sources https://docs.gprmax.com/en/latest/inc_README.html
https://github.com/spinsphotonics/fdtdz
https://docu.ngsolve.org/latest/i-tutorials/unit-5.5-cuda/poisson_cuda.html
RustCUDApossiblevia cudarc(https://github.com/chelsea0x3b/cudarc); language
rewritealone doesnotchangeworking-set/iterations/kernelmath. Goalunchanged;
nextauthorizedrun remainsEXP93mediumfilterthenboundedfullantennapair.

### Aktualizacja planu na prośbę użytkownika, 2026-10-19
Dodano M4.4 lifecycle energii; M5.5 koszt/working-set PC, M5.6 ograniczone
porównanie FDTD/CUDA (zysk jednego szerokopasmowego przebiegu jako hipoteza),
oraz M6.5 fuzja/batching bez wymuszania TC.
Numeracja M0–M7 i ActiveM4 zachowane. Nowe kryteria nie są zaliczone przez
wcześniejsze runy. Rust/FieldCraft/GUI/CAD są poza zakresem obecnego goal.
Zmiany tylko MD; żadne nowe symulacje/buildy nie zostały uruchomione.

Korekta zakresu od użytkownika w tym samym turnie: bez researchu/implementacji
Rust ani FieldCraft. Usunięto proponowane M5.7 przed zatwierdzeniem planu.
M5.5/M5.6/M6.5 służą wyłącznie maksymalnemu przyspieszeniu wiarygodnych
symulacji na aktualnej5070Ti/96GBRAM. IntegracjeCAD/GUI nie są zadaniem.

### Doprecyzowanie polityki SSD przez użytkownika, 2026-10-19
Cache, zwykłe pliki i sporadyczny odczyt SSD dozwolone; niewielkie zapisy
oceniać po pomiarze bajtów/częstotliwości i czasu. Gorące dane solvera RAM/VRAM.
Bez swapowania zadania i intensywnego przepisywania workspace na dysk.
Nie przywrócono disk basis ani nie zmieniono runtime/limitów kontenera.
Historyczne zakwalifikowanie wyników bez zmian. Aktualizacja wyłącznie MD.

### EXP93 wznowienie, 2026-10-20
Poprzedni turn: progress (polityka SSD zapisana w repo). M4 pozostaje aktywny.
Docker był nieaktywny; uruchomiono lokalny daemon, bez przebudowy. RAM available
około77GiB, GPU wolne13,26GiB; aplikacji użytkownika nie zamykano.
Następny test: wcześniej zarejestrowana para coax-medium3,55GHz/bothports,
release-only vsrelease+reuse, identyczny build i polityka pamięci. Limit180s.
Nowe ścieżki artifacts/m4-energy-medium-{control,on}-20261020.

EXP93 medium3,55GHz rootverifiedPASS: samebuild/config/mesh,45/47iterboth,
control109,269s vsreuse102,770s (jedna para, nie statystyczna promocja).
Cgrouppeak3253268480→2665140224B (−588128256B), GPU-processcounterbez
zmiany; nie jest to pomiar całej rezydencji UVM. MaxΔS5,1434e−9,
ΔVSWR5,09994e−9, energyrelative5,8431e−9; wholeE9,4406e−7/B1,1535e−8.
Energyrelease manageddrop355899672B; control2setups, reuse1setup.
Receipt artifacts/m4-energy-medium-root-analysis-20261020.json.

Następny filtr EXP93 fullantenna3,50GHz/bothports: sameFP32direct/nativecoarse,
RIGHT/K64/pool256, releaseenergyinboth/controlvsreuse, rawtolunchanged,
partialinitial source artifacts/m1-antenna-resident-fp64-20261018(P2);
P1explicit zero. Newoutputs artifacts/m4-energy-antenna-{control,on}-20261020.
Limit1800s/60GiB/noswap/hostguard6GiB, no raising cap. Controlmaynotbe
fullindependentaccuracyreference: compareP2toqualifiedreference separately;
candidatefieldreference fullcontrol onlyafterwholejobcomplete. Stoponfailure.

EXP93 fullcontrol PASS execution684,805s,44/35iter/raw7,494e−7/8,357e−7,
peakcgroup60525092864B. Release managed65177433822→49902109334B,
actualdrop15275324488B (agent incorrectly copied medium355899672B; rootcorrected).
ReusecandidateFAIL/OOM137 entering P1 field diagnostics; cgroup64104218624B,
managedlive65177433822B, no P2/wholefieldqualification. Not retried unchanged.
Both share identical solver/postprocess managed phases until comparison begins;
reference field diagnostics add scratch on top of retained25,008GBcuDSS and
15,275GBenergy operators. Wholejobqualitycandidate remainsFAIL.

## EXP94 — defer two-port measurements until solver destruction (2026-10-20)
Hypothesis: avoid overlap of25GBfactors+energy/fielddiagnostics by solving both
RHS before measuring. Cache only first true-DOF complex E in RAM/VRAM
(16*Nbytes; antenna179499584B), compute B later with unchanged Curl/omega.
No solver data on disk, no physics/tolerance/mesh changes; finalsolverdestroyed
before any measurements, original excitation order/energy/fields preserved.
Opt-in --defer-postprocessing; exactlytwoLP/onefreq/fixedmesh/restart1/rank1,
no visualization/wave/Floquet; requires --release-final-solver. No newdefault.
First tiny/reference EXP93tiny, then medium355/reference EXP93mediumcontrol,
then samefullcontrol at1800s/60GiB/noswap/guard6GiB. SavefirstEonly once;
log/audit exact storeP1→solverrelease→measureP1→measureP2. Raw/S/VSWR/energy/
wholefields gates unchanged. New code needs cached build and regression suite.

Runtime faktycznie używa Podman, nie Docker. Przywrócono niepotrzebnie
uruchomiony Docker do uprzedniego stanu inactive; dalsze runy przez Podman.
EXP94 regresje124PASS; fallback build/m4-reuse/pre-exp94-native zachowany.

EXP94 cachedbuild9,215s/no deps; tiny39/42iter18,726s, medium45/47iter103,033s
PASS raw/TEM/wholefields/deferredaudit. Root checked S+energy <1e−5 vs existing
references, actual errors logged in next receipts. Next full matchedsamebuild
control defer/no-reuse vsdefer/reuse, ref EXP93fullcontrol for first, thenfresh
control forsecond. Both retainreleaseenergy andsamepartialseed/K64/pool256.
Artifacts/m4-deferred-antenna-{control,on}-20261020,1800s/60GiB/noswap.
This isolates reuse undercommondeferredpolicy andcheckswholequality vsEXP93.

EXP94 pełna matched para rootverifiedPASS: control681,698s vsreuse602,944s,
44/35iterboth; sameconfig/buildmanifest/fixture, dwa setupy vsjeden. Rawrelative
candidate7,492212451061e−7/8,356430312650e−7. MaxΔcomplexS2,366618e−8,
ΔVSWR5,138175e−8, Δsumymocy7,077207e−9, Δenergyrelative1,815256e−8,
wholeE/B2,141e−7/1,782e−8;14regionentries. Deferredcontrol vsEXP93 E/B
2,108e−7/1,500e−8. Rootreceipt artifacts/m4-deferred-antenna-root-analysis-20261020.json.
Managedpeak65353018230→53084415322B; deferredcontrolcgroup60525092864→56829792256B,
reuse56832888832B. Actualfullenergyreleasedrop15275324488B; firstEcache179499584B.
No memorycapraise, no diskworkspace; nativecoarseFP64 unchanged.

Final currentbuild filters: defaultposttiny17,712s/39,42iterPASS; deferredmedium
3,30GHz102,608s/45,47 and3,80GHz102,785s/45,47 bothPASS/TEM/wholefields.
MaxE1,034e−6/B1,142e−8 on3,30GHz, no phasefit. Mid355103,033s PASS earlier.
M4.3 symbolicmultifrequency NOT RUN (one-f shard; single analysis17,35s max2,88%
currentfulltime). Same verifiedpartialseed both runs, no warmstartspeedclaim.
M4 complete assessment, M5 active withindexedcheckpoint; M7 wholeband/statistics
remainNOTRUN. No globaldefaultpromotion. Docs-garden beforecommit required.

EXP94 finalvalidation:124 pinnedregressionsPASS/8shellPASS/docscheckerPASS.
SameLuna read-onlydocs-garden foundno materialdiscrepancies. Rootreviewed
source lifecycle/ownership/guards, samebuildreceipts andactualraw/S/power/fields.
Currentnative verified; no livePalacecontainers. Localcommit only (sole remote
is publicupstream), no push. M5 begins source/APIresearch next; goalactive.
