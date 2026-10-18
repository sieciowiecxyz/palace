# Postępy optymalizacji

Aktualizacja: 2026-10-18. Mode: goal, Active: M1. [PLAN](PLAN.md), [MILESTONES](MILESTONES.md), [raport M1](docs/optimization-baseline.md), [kontrola pól](docs/field-validation.md).

## Wymóg użytkownika

**Dane robocze solvera wyłącznie w RAM/VRAM.** Bez SSD/NVMe scratch, disk basis, out-of-core, plikowego mmap ani swap jako sposobu na zmieszczenie obliczeń. UVM może migrować GPU↔RAM. Nie zamykać aplikacji użytkownika. Cache kompilacji oraz zwykłe wejścia i wyniki pozostają osobną funkcją. Usunięto disk basis; legacy env są odrzucane przed inicjalizacją MPI/CUDA.

## Bieżący checkpoint

- M0 zamknięty, M1 otwarty; brak promowanej optymalizacji pełnej anteny. Lokalny sprzęt: jedna RTX 5070 Ti 16 GB + 96 GB RAM, tryb medium, bez płatnego compute.
- Pełna antena FP64-disk reference oraz FP32-disk candidate z porównaniem pól są zachowane historycznie i oznaczone **REJECT**. Nie są dopuszczalnym baseline ani wynikiem dla wymaganego storage RAM/VRAM; nie odtwarzać starych poleceń.
- Wcześniejszy resident FP32 run anteny przerwał RAM guard około 141 iteracji/1087,70 s; brak S/pól. Globalna pamięć obejmowała aplikacje użytkownika, więc ten wynik nie dowodzi, że antena nie mieści się na sprzęcie.
- Nowa referencja wykonania anteny **FP64 resident-only** ukończona: 1089,964 s, 151 iteracji, VSWR P2@3,50 GHz=1,672123; snapshot E/B kompletny. Cgroup peak57,72 GiB, logical managed54,74 GiB, sampled GPU procesu4,89 GiB. Artefakt `artifacts/m1-antenna-resident-fp64-20261018/`; niezależna jakość anteny nadal otwarta, więc nie jest to kwalifikowana referencja dokładności.
- Trace alokacji dużej anteny pozostaje materiałem audytowym. Ostatni disk run miał cgroup peak 49,24 GiB, logical managed high-water ~45,17 GiB i cuDSS peak 7,52 GiB; telemetry obejmowała także globalny desktop. Nie traktować tych danych jako budżetu resident wariantu ani czystego benchmarku.
- Otwarta kwestia jakości: raw residual ~0,125 różni się od stopping norm LEFT. Kontrole TEM i całych pól na małym coaxie przechodzą, ale nie dowodzą poprawności fizycznej ani błędu pełnej anteny.

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

1. Zamrozić nową referencję wykonania FP64 resident, nie kwalifikować jej automatycznie: raw0,125267 vs LEFT stopping9,956e−7.
2. Przygotować kontrolę niezależną od preconditionera: RIGHT i/lub korekta rezydualna z porównaniem całych pól; najpierw mały filtr, jawny rachunek pamięci, bez powtórzenia pełnej anteny bez hipotezy. Domyślnie nie ładować kolejnej 240-wektorowej bazy do większego RIGHT solve.
3. Po zamknięciu jakości wykorzystać profil: setup54,85 s, GMRES950,96 s, z tego timery preconditionera603,23 s i coarse79,57 s; baza155 wektorów zajmuje logicznie27,82 GB. Nie mylić całego solve z samym coarse/cuDSS.
4. Zamknąć M1 przed obowiązkowym prototypem Maxwell FEM–BEM/MoM; M2 i dalsze etapy nie są pomijane.


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

Aktualny build przyrostowy native ukończył się w 7,388 s; 23 testy jednostkowe PASS. Te kontrole walidują narzędzia i małe fixture, nie kwalifikują pełnej anteny. Pełna antena EXP12 ma execution PASS, lecz niezależna jakość pozostaje otwarta; multi-GPU i zbieżność produkcyjna pozostają NOT RUN. Wymóg RAM/VRAM bez SSD/swap pozostaje obowiązujący.

## EXP12 — fazy pamięci i lifetime bazy (filtry i pełny run ukończone)

Kod GMRES potwierdza, że zwykła baza FP64 V jest polem solvera i zostaje po Mult. Opcja release czyści V dopiero po rekonstrukcji i wszystkich checkach; nie zmienia E, statystyk, restartu ani tolerancji. Kolejne Initialize odtwarza V. Markery adaptera emitują monotoniczne czasy i live/peak pomiędzy fazami, bez deviceSync. Domyślne zachowanie pozostaje bez zmian. Walidacja: tiny 6 solve'ów, known-TEM, następnie jedna pełna referencja wykonania FP64; wyniki poniżej. Samo ukończenie nie zamyka M1.


Pierwszy filtr `artifacts/m1-gmres-release-tiny-20261018/`: exit 0 i 6/6 solve w 11,515 s, lecz **FAIL kompletności diagnostyki** (`complete=false`). Ostatni komunikat zwolnienia bazy został rozdzielony przez zmieszanie stdout/stderr; rozpoznano tylko 5/6 pełnych prefiksów. Nie uruchomiono kolejnego TEM. Zmieniono emisję release na pojedynczy wpis stderr, jak markery faz; wymaganie sześciu pełnych komunikatów pozostaje bez zmian. Cached rebuild 7,388 s, 22 unittesty PASS. Powtórzenie z nowym hashem źródeł otrzymuje osobny sufiks `r2`; pierwotnego FAIL nie nadpisujemy.

Retry r2: release i fazy 6/6 PASS, ale kolejny **FAIL kompletności** (5/6 `PALACE_KSP_CHECK`). Interleaving przeciął tym razem stdout z residuum, więc samo przeniesienie release na stderr nie wystarcza. Runner zapisuje teraz stdout/stderr osobno, a dopiero po zakończeniu składa `palace.log` z jawną informacją o braku globalnej chronologii strumieni. Zachowuje surowe logi; test z celowo przerwanym stdout potwierdza integralność komunikatu. 23 unittesty PASS. Kolejny filtr r3 używa tego samego native builda (zmiana wyłącznie Python/logging).


EXP12 r3 filtry **PASS**: tiny save-fields 10,517 s, 6/6 solve (24/13/14/25/13/13), wszystkie stopping checks ≤1e−6, markery i release 6/6. Względem EXP11 seed256 max |ΔS|=3,88e−15, ΔVSWR=6,66e−15, względna zmiana wspólnych energii=2,07e−13 (`artifacts/m1-gmres-release-analysis-20261018.json`). Sampled GPU procesu 631242752 B; cgroup peak506884096 B; logical UVM peak308538406 B. To kontrola numeryczna małego fixture, nie dowód speedup ani kwalifikacja anteny.

TEM r3: 17,586 s, 2/2 solve, pełne coverage; E L2 q4/q6 około0,495%, B0,521–0,536%, oba porty <1%. Logical UVM peak290950486 B, sampled process GPU631242752 B. Baza znika po sprawdzeniu rozwiązania, przed postprocessingiem; liczniki liczą lifetimes, nie rezydencję GPU.

Wykonane polecenie pełnego runu: `python3 tools/dev.py run tshaped-medium artifacts/m1-antenna-resident-fp64-20261018 --seconds 1800 --basis fp64 --hypre-pool-mib 256 --release-gmres-basis --memory-marks --save-fields --background`. Jedna3,50GHz/P2, identyczny mesh medium, bez Q-pool i porównania starej referencji, bez dyskowej pamięci roboczej. Cgroup60GiB, hostguard6GiB, przed uruchomieniem około68,7GiB MemAvailable; GPU miał obciążenie aplikacji użytkownika (około4,8GiB), nie zamykamy ich. Guard/OOM/deadline nadal oznaczają FAIL; ten konkretny run ukończył się naturalnie. M1.2/M1.3 niezależnej jakości nadal otwarte.


Pełny run EXP12 **execution PASS**, 1089,964 s, 151 iteracji, 3,50GHz/P2; bez OOM/guard/deadline. Wszystkie markery faz i release1/1. Zwalnianie V po solve zmniejszyło logical managed58,706→31,422 GB (25,41GiB), koszt0,181 s. Maksymalny logical managed58,779 GB (54,74GiB) nastąpił w GMRES; postprocessing48,090 GB (44,79GiB). Cgroup peak57,72GiB, sampled GPU4,89GiB, min hostavailable11,98GiB. Peaki nie są addytywne ani dowodem konkretnej rezydencji alokacji. Snapshot E/B ma179499600/240704512 B i SHA w fields.json; pełna analiza root w `root-analysis.json`.

VSWR P2=1,672123; raw ||b−Ax||/||b||=0,1252666005 przy independently recomputed LEFT stopping9,956397e−7. Raw/stopping ratio≈125815; nie wynika to z FP32, bo aktualny solve jest FP64. **Jakość anteny M1.2/M1.3 pozostaje nierozstrzygnięta**; nie promować dalszej precyzji na podstawie samego S lub ukończenia. Ten run zastępuje odrzucone dyskowe wykonanie jako dopuszczalny punkt diagnostyczny, ale nie stanowi jeszcze kwalifikowanej referencji fizycznej. Nie wyliczać speedup względem historycznego disk runu z innym tracingiem/polityką pamięci. [Interpretacja i odtwarzanie](docs/memory-phases.md).
