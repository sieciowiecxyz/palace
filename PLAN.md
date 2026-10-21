# Plan optymalizacji Palace

Polityka SSD doprecyzowana przez użytkownika (2026-10-19): gorące dane solvera w RAM/VRAM; UVM GPU↔RAM. Zwykłe wejścia/wyniki, cache i sporadyczny odczyt SSD są dozwolone. Niewielkie zapisy wymagają pomiaru wolumenu i częstotliwości I/O; nie deklarować zerowego zużycia dysku. Bez swapowania zadania i intensywnego przepisywania bazy/macierzowych workspace na SSD w pętli solvera. Obecny disk basis pozostaje usunięty; dawne wyniki z nim nie stają się przez tę korektę zakwalifikowanym baseline. Nową metodę używającą dysku oceniać po zmierzonym I/O, czasie i dokładności.
Mode: goal
Active: M6

Stan: goal aktywowany 2026-10-18 na polecenie użytkownika. M1 ukończony po referencji/profilu; M2 integracja REJECT, M3 pamięć/prefetch ocenione, M4 pełna para EXP94, M5 ocena PC/mixed/FDTD zakończona EXP104. Aktywny M6: gorące kernele i sweepy. Compute lokalny; bez najmu chmury.

## Cel

Skrócić czas do **wiarygodnego wyniku medium** i zmniejszyć pamięć na RTX 5070 Ti 16 GB + 96 GB RAM. Rozwijać Palace/MFEM/libCEED w C++/CUDA: UVM, cuDSS, mixed precision i Tensor Cores tam, gdzie pomiar uzasadnia ich użycie. FEM–BEM/MoM to obowiązkowy kierunek researchu i prototypowania. Aktualny cel obejmuje jedną kartę; multi-GPU pozostaje poza kryteriami ukończenia. Narzędzia pozostają małe, z cache i odtwarzalnym buildem.

Priorytet użytkownika2026-10-21: optymalizacja pod tę konfigurację sprzętową,
bez hardcodowania jednej geometrii PCB. Reflektory/directory i inne anteny mogą
zmienić koszt oraz najlepszą politykę; uniwersalność algorytmu nie dowodzi zysku
na każdej geometrii. Ocena sweepów M6.6 i dodatkowej geometrii M7.5 obowiązkowa.

Wymagania i uzasadnienie: [speedup](docs/speedup.md). Kryteria: [MILESTONES](MILESTONES.md). Stan wznowienia i wyniki prób: [PROGRESS](PROGRESS.md). Reguły wykonania: [workflow](docs/workflow.md).

Ambicja: dodatkowe ≥1,5× przyspieszenie i ≥25% redukcji porównywalnego szczytu pamięci roboczej. Historyczne 955,176 s to punkt odniesienia do odtworzenia w M1, a nie automatycznie baseline nowego buildu. Oddzielnie mierzyć VRAM, RAM, rozmiar alokacji i transfery; samo przeniesienie danych do RAM nie wystarcza. Szukać najlepszego zmierzonego kompromisu czas/pamięć/błąd/koszt; nie obiecywać globalnego optimum.

## Milestones

- [x] M0 — Research i samodzielny fork z cache; zakres dowodów w docs/migration.md.
- [x] M1 — Referencja, niezależna jakość, profil i koszt powietrza w FEM; docs/milestones/M1.md.
- [x] M2 — ocena FEM–BEM/MoM zakończona REJECT obecnej integracji; bramki promocji pozostają FAIL/niekompletne. docs/milestones/M2-decision.md.
- [x] M3 — FP32direct memory gain i ocena prefetchu; W.1/W.2/W.3 PASS, bez globalnej promocji; docs/milestones/M3.md.
- [x] M4 — reuse setup i deferred postprocessing; pełna para EXP94 PASS, docs/milestones/M4.md.
- [x] M5 — ocena PC/mixed/FDTD zakończona EXP104; mixed W.2/W.3 PASS jako opt-in, hybrid/AMS/directgprMax REJECT; docs/milestones/M5.md.
- [ ] M6 — ACTIVE: gorące kernele CUDA, fuzja/batching, Tensor Cores/TF32/BF16 i sweepy; docs/milestones/M6.md.
- [ ] M7 — Kwalifikacja najlepszego wariantu na jednej 5070 Ti i pakiet do użycia.

Etapy kolejno M1 → M2 → M3 → M4 → M5 → M6 → M7. Każda bramka obejmuje jakość i porównywalne pomiary. Negatywna ocena prototypu może zamknąć hipotezę z dowodami; nie wymuszać integracji wolniejszego solvera. Brak poprawności lub brak wykonania wymaganego testu nie zalicza bramki. Plan i numeracja zastępują wcześniejszą kolejkę z obowiązkowym multi-GPU.

## Kolejka pracy

### M1 — najpierw podstawa porównań

- [x] Dodać i sprawdzić na tiny normę różnicy całych pól, detekcję kontrolowanego błędu i kontrolę błędu (dawny disk/resident wycofany).
- [x] Zachować historyczne E/B jako dane porównawcze; referencja korzystała z wycofanego storage dyskowego i nie jest dopuszczalnym nowym runem. Kandydat residentFP32 przerwany guardem przy obciążonym desktopie.
- [x] Dodać ślady dużych alokacji i pomiar cgroup RAM; interpretacja właścicieli pozostaje otwarta.
- [x] Rozliczyć duże alokacje w tej samej chwili i zaplanować hipotezę workspace w RAM/VRAM: docs/memory-audit.md; bez nowej pełnej symulacji.
- [x] Zbadać lifetime i przygotować izolowany Q-pool: oryginalne assembly/passive zachowane, sync przed/po, mały probe PASS; docs/ceed-qpool.md.
- [x] Q-pool przeszedł coax/TEM, lecz zwiększył logical UVM peak w coax-tiny o 5,8% i nie zmniejszył sampled VRAM; brak promocji.
- [x] Osobny seed HYPRE 256 MiB: coax/TEM PASS, sampled VRAM procesu niższy o 3,75 GiB na małym fixture, porty/energie zgodne; pełna antena niezakwalifikowana.
- [x] Rozdzielić fazy solve/postprocessingu: EXP12 resident FP64 i jawne znaczniki; zwalnianie bazy GMRES oraz opt-in finalnego solvera. Zysk lifetime zweryfikowany na tiny, pełne complex-coarse EXP17 zatrzymane guardem (bez promocji).
- [x] Native FP64 complex N×N: probe/coax/TEM/fallback i W.3 PASS; cuDSS setup live25,008GB vs30,641GB exactbloku. Nowa referencja RIGHT1e−9 i medium kontrola pól; docs/native-complex-coarse.md. Bez promocji defaultów i bez podnoszenia cap/guard.

- [x] Dodać osobne logowanie raw/LEFT residual i sprawdzić wpływ strony preconditionera na znanym TEM.
- [x] Przygotować szybki coax-tiny oraz porównanie analitycznego E/B i całego L2, jawnie oddzielone od anteny.

- [x] Hash/fizyka/build zinwentaryzowane; silniejsza resident FP64 referencja tight-r2 i W.3qualified mają snapshoty/SHA i rootanalizę. Stary EXP12 pozostaje tylko referencją wykonania.
- [x] Prześledzić normy/scaling i wyjaśnić LEFT vs RAW; niezależne Ax−b/TEM oraz nowa RIGHTreferencja z kontrolą całych pól. docs/milestones/M1.md.
- [x] Raw RHS niezależne od PC + TEM/L2; W.3medium względem FP64RIGHT1e−9 przechodzi zamrożone K.3/K.4. M1 zamknięty w zakresie W.3; szersze pasma i geometria produkcyjna niezakwalifikowane.
- [x] Rzeczywiste DOF/material incidence zgodne z Palace i bilans net-release EXP21; docs/topology-memory.md. Bieżący audyt EXP22 przypisuje99,616%peaku dościeżek; drobnyremainder jawny.
- [x] Hostphase + bieżący CUDA-onlyprofile na pełnej siatce, niezależniekalibrowany zegar i margines10µs; stareNVTX/clockFAIL zachowane. docs/profiling-window.md.
- [x] DOF/air/interface, PA/coarseCSR/qdata/V/Z/faktory/workspace/kopie rozliczone z jawnym remainder i rozdzieleniemmanaged/cgroup/sampledGPU; docs/topology-memory.md, memory-audit.md.
- [x] Krótki W.3profilePASS i pełnyEXP19bezprofilera. P92%wczesnegookna/UVM295GB→następnyprototypM2 i później rezydencja/workspace; bezpromocjispeedupu.

### M2 — metoda dopasowana do otwartej anteny

- [x] M1: AIRexclusive57,586%DOF, granica94200ND2trace, denseblok132GiB; nieutożsamiać tego ze speedupem.
- [ ] Porównać FEM–BEM, powierzchniowy MoM i akcelerację FMM/MLFMA/H²; sprawdzić Maxwell, dielektryki, otwarte cienkie metale, zasilanie i promieniowanie.
- [ ] Przejrzeć istniejące biblioteki, źródła i licencje; oddzielić GPU assembly od GPU matvec/FMM/solve. Nie zakładać CUDA/TC na podstawie etykiety GPU.
- [ ] Przygotować rzeczywisty mały prototyp Maxwell: kula PEC z odniesieniem, potem dielektryk i sprzężony interfejs FEM–BEM. Porównać do FEM przy porównywalnym błędzie.
- [x] Część PEC: niezależny Miecomplex, zbieżność i1%PASS; pierwszy CPUH-matrix/CUDAapply poprawny, ale9%oszczędności/53×wolniej — bezpromocji. docs/maxwell-oracle.md. Na etapie EXP23–24 dielektryk/interfejs pozostawały otwarte; dalsze wyniki poniżej.
- [x] EXP25–29: native2kernel/H-matrixeta4−17,31%danych i poprawnyGPUoperator/CPUbasisGMRES; dielectricspherePMCHWT/Miecomplexfar-field/energyPASS ze zbieżnością i jawną regułąobjętości. docs/maxwell-native-dielectric.md. BrakFEMinterface/nearfields/scalableassembly/antenna promotion.
- [x] EXP30–31: actualMFEMND1/Bemppinterface i zbieżność, trace/pair/energyPASS; całkowity1%E/H**FAIL**(6,12/5,79%), bezpromocji. docs/maxwell-coupling.md. NastępneND2globalDOF i traceprojection, potemdielectricFEM/scalableassembly.
- [x] EXP32: fizyczneparowanie/BCtransforms/constanttracePASS. GramRWG/SNCtracirank90/120,330/480 — odrzucićjegoosobneodwracanie. RWG/RBCfullrank/κscaled≤2,93 na małychsiatkach; nadalNOTRUNactualND2mortar i antena. docs/maxwell-coupling.md.
- [x] EXP33: actualglobalMFEMND2/faceDOFs/physicalbasis/CSR i boundedDirichletplane-wavePASS0,151/0,332%E/H,5,514s/433MB. SamainterpolacjaH1,468%niezaliczona. DalejBC/RBCmortar/coupling, niezamknięcieM2. docs/maxwell-nd2.md.
- [x] EXP34: actualND2/BC-RBCmortar i sparseSchur, nativeT/K/physicalmap/tinyfull/energyPASS. WholefieldFAIL17,74/15,22→10,07/5,64%, brakpromocji. Dalejniezależnaprzestrzeńbrzegowa/fixedFEM, nie ślepy matchedrefinement; docs/maxwell-nd2-coupling.md.
- [x] EXP35–37: trace-space audit, paired magnetic/electric-dual, niezależny brzeg i kontrola FEM. Transparent ND2 PASS E/H0,560/0,751% (F2/B3); F3/B3 poprawia E, pogarsza H. Bez promocji anteny; docs/maxwell-trace-duality.md.
- [x] EXP38–41: wykonano eps1/2,94 i niezależny PMCHWT na tej samej geometrii; rozdzielono siatkę i potentialquadrature. F2/B3 vs referenceB4 E/H1,092/1,320% centroidscreening FAIL; nie globalL2. Rozwiązania zachowane, docs/maxwell-transmission.md.
- [x] EXP42–43: saved-solution volume replay, reguły2/5 i dwa potentialq. Degree5 E/H2,888/1,612%, refchange1,945/1,158%, qdelta~7,4e−4 FAIL; centroidy nie kwalifikują pola. Brak BEMsolve/rebuild, docs/maxwell-transmission.md.
- [x] EXP44–47: fizyczne RWG panelintegrals vs native, niezależny solid-angle i adaptive/cutoff kontroler. Korekcja fineB4 na wszystkich2240savedpoints117,617s/217MB; kontrolerPASS, E/H2,888/1,611% nadal FAIL. Dalsze kontrole EXP48–53 poniżej; docs/maxwell-near-panels.md.
- [x] EXP48–53: kontrolowany cached NumBa near-kernel ~20× w mikropróbie; pełny coarse replay18,089s zamiast TIMEOUT180s. Corrected B3/B4 oraz degree2/5 nadal FAIL zbieżności; pola2,888/1,611% niekwalifikowane. Nie jest to speedup anteny; docs/maxwell-near-panels.md.
- [x] EXP54–58: analytic epsilon2,94 F3 E/H0,443/0,717%PASS, actualcoupled F3/B3 i replay identycznych640punktów E/H0,664/0,597% vsB4. Wciąż brak zbieżnej normyF3/reference; defaultND2eps1 regressionPASS. docs/maxwell-fem-refinement.md.
- [x] EXP59–69: fused T/K apply matchesnative/incremental<1e-12, matched32query2,56×zprzygotowaniem. WłasnaF3volume degree2/5 dajeE/H1,463/.865→1,683/.972%; reference/degreeFAIL. DenseB5 ponadcap; następny backend FMM opisany w EXP70–73. docs/maxwell-stream.md.
- [x] EXP70–73: cached ExaFMM build i p8 Maxwell actionPASS<1e-6; p6FAIL, p8two-cache INVALID przez RAM tmpfs exhaustion. Sekwencyjny cykl życia naprawiony bez zwiększenia cap. Wówczas PMCHWTsolve/fieldNOTRUN; późniejsza decyzja po EXP74–76 poniżej. docs/maxwell-fmm.md.
- [ ] Zweryfikować sprzężoną transmisję dielektryczną i ryzyko rezonansów; nie utożsamiać osobnego PMCHWT/Mie z interfejsem FEM–BEM.
- [ ] Zmierzyć setup+solve, macierz/kompresję/workspace i przewidywany koszt docelowej anteny; gęsta macierz BEM bez kompresji może przegrać.
- [ ] Jeśli prototyp daje przewagę i poprawne pola/energię, przygotować izolowaną integrację operatora blokowego w Palace i porównać reprezentatywny case. Inaczej zapisać odrzucenie/ograniczenie; wynik Helmholtz nie kwalifikuje Maxwell.

M2 decyzja: ocena zamknięta REJECT po EXP74–76, bez promocji/zmiany frozen gates.
Niezależny FMM residual1,27e-8 nadal>1e-9, pełna transmisja/refinementFAIL.
M3 zaczyna się po udokumentowanym odrzuceniu zgodnie z zasadą negatywnej oceny
powyżej; nie oznacza zaliczenia M2.2/M2.3 jakości. docs/milestones/M2-decision.md.

### M3 — największy podejrzany koszt pamięci

- [x] EXP77–79: sharedFP32/FP64CUDAprobe, opt-in directDot/AddTo, actualcomplexcoax-tinyPASS. Bez promocji/speedupclaim; docs/mixed-basis.md.
- [x] EXP80–85: actualAPIreal/complex/MGS/faultdetector oraz pełneW.2/W.3 PASS; W.3 cgroup−2,87GB, bez speedupclaim. docs/mixed-basis-validation.md.


- [x] Direct FP32 dot/AXPY z FP64, usunięte rozpakowania z MGS/update (jedno przed ApplyBA nadal potrzebne); EXP77–85.
- [x] Kernel/actualAPI/MGS/realcomplex/zero/faultdetector i W.2/W.3/reliable stopping PASS; bez uniwersalnej gwarancji stagnacji.
- [x] EXP86–90: prefetch vs demand UVM, actual bytes/iteration i peak/czas; mała poprawa ortogonalizacji, bez statystycznego speedupclaim; docs/basis-prefetch.md.
- [x] Ocena restartu: 35iter<K64, porównanie120/240 nie ograniczy dotkniętej bazy. NOT RUN z uzasadnieniem; mniejszy restart nieuzasadniony kosztem PC.

### M4 — setup raz, kilka RHS

- [x] Zmierzyć liczbę SetOperators/faktoryzacji i potwierdzić identyczność operatora oraz terminacji między portami.
- [x] Prototyp reuse na jednej częstotliwości i obu portach; zachować outputy, wznowienia i postprocessing.
- [x] Symbolic reuse między częstotliwościami i warm start/recycling badać osobno, tylko gdy koszt setup uzasadnia próbę.
- [x] Zmierzyć czas życia postprocessingu między RHS: zwalnianie/rebuild operatorów energii po pomiarach; oba porty muszą ukończyć run przy obecnym limicie, z niezmienionymi energiami/polami.

### M5 — tańszy preconditioner i wybór algorytmu

- [x] Audyt cuDSS0.7.1.4 hybrid memory/execute/UVM/rank1, actualAPI i ograniczeń; docs/native-hybrid-memory.md.
- [x] Dwa wykonalne budżety hybrid po odczycie minimum, W.3P2 vsUVM: numeryczniePASS/netperformanceREJECT, EXP96.
- [x] AMS na realnym shifted pomocniczym PC, actualCUDAtracePASS; tiny/mediumqualityPASS, W3deadlineFAIL. Ocena EXP97, bez promocji.
- [x] EXP98–101: native complex FP32/scaling/dwie FP64 CUDA korekcje, fail-closed i FP64 fallback; API/W.2/W.3 PASS. Jedna para W.3 −19,31% czasu/−19,01% cgroup, bez globalnej promocji; docs/milestones/mixed-coarse-plan.md. Zmienna liczba korekt/FGMRES pozostaje osobną hipotezą.

- [x] EXP100/102: pełne wyłączne timery + strict late CUDA/UVM profile;251,125→186,635GB w dwóch iteracjach, bez ekstrapolacji na całą symulację. Limit zysku coarse i zakres dowodów: docs/mixed-coarse-profile.md.
- [x] M5.6 — EXP103–104 gprMax CUDA/HSG resource/API assessment: samefreq/bothports/timewindow, actualgeometry/hash, publicnesting i36,144GB minimumsinglebox. Directport REJECT; mały solverbenchmark NOT RUN po nieprzejściu resource/API gate. Bez uniwersalnego odrzucania FDTD; docs/fdtd-budget.md.

Szczegóły i warunki odrzucenia: `docs/milestones/M5-research.md`. Research jest ograniczony; negatywna ocena z dowodami kończy hipotezę, nie wymusza migracji backendu.

### M6 — gorące kernele, TF32 i przepustowość pamięci

- [x] M6.1 EXP105–106: rzeczywiste gorące basis actions/wymiary z profilu i host audit, zakres/Amdahl docs/milestones/M6.md oraz docs/ceed-basis-audit.md.
- [ ] Research cuBLASLt/libCEED/MFEM; CUTLASS dopiero przy brakującej funkcji. Zapisać link, rewizję, licencję i przydatność.
- [x] M6.2 pierwszy biblioteczny filtr EXP107–108: oryginalny MAGMA/FP64/FP32/TF32requested, konwersje/workspace i crossover przez actualN1601320. CPU/control/canaries PASS; nie promocja solvera. docs/ceed-tensor-probe.md.
- [ ] Potwierdzić użycie Tensor Cores i sprawdzić całe rozwiązanie. BF16/FP16 to osobne hipotezy z kontrolą błędu, nie domyślna zamiana typu.
- [ ] EXP109–110 fusedFP32 actionfilter PASS; EXP112–113 PCforwardtiny/medium poprawne lecz więcejiteracji/brak wykazanego speedupu, HOLD przedW3. EXP114–116 compensated/bit-split actionfilterPASS, actualNforward~12%taniej/przybłędzie~6e-15, scalar/tracewolniejsze. EXP117–119 scopedPCtiny/mediumKPASS, iteracjebezwzrostu ale netgain niewykazany/HOLD, W3NOTRUN. Następnie audytM6.6 sweep/PROM/reuse; W3/UVM przedpromocją M6.4/M6.5. docs/pc-basis-fp32.md.

- [ ] M6.6 — ACTIVE: EXP120–130 frequency-major reuse, per-port history i per-f deferred release; coax3/7freq oraz W3medium3,5/3,6GHz oba porty PASS. Antena996,519→915,924s (jedna para −8,09%), cgroup48,720→47,660GB; pola/raw/frozenK PASS. EXP131–133 linear predictor coax PASS, antena fallback/brak netgain/REJECT. EXP135–138 complex projection math/coax PASS, antena coarse mixed2IR gate FAIL/HOLD. EXP139–142: verified history single-f i legacy coax PASS; antena odtwarza klasę błędu coarse2IR w121s, nie bitowo ten sam RHS. EXP143–147: fixed3 coax PASS i singleP2 executionPASS, pełny3freqsweep deadlineFAIL (5/6), bez promocji/defaultchange. EXP148–152: symbolic reuse ma upperbound~2,2% na obecnym3f; full recycling wymaga dodatkowych wektorów/zmiany solvera, niepromowany; PROM4 medium held-out/rawPASS, ale whole-strategy +19,77% czasu/+11,77%cgroup vsbestuniform, REJECT promocji. Dalej: pełny7f anteny w jawnych bounded chunks; EXP153–154 pierwszy3,3GHz/oba porty cold fullFP64 vs combinedFP32storage/mixed2IR/reuse PASS, −26,98%czasu/−23,62%cgroup jednej pary. Pozostałe6f NOTRUN; docs/milestones/antenna-sweep-qualification.md. Potem W4/W5/mediany/nowa geometria i pakiet M7. docs/milestones/sweeps.md.

### M7 — utrwalić najlepszy zaakceptowany wariant

- [ ] Wykonać kwalifikację częstotliwości/portów według MILESTONES, trzy pomiary finalisty bez profilera.
- [ ] Raport tabeli kompromisów i decyzja promote/reject; zachować działającą referencję oraz fallback.
- [ ] Pakiet z manifestem, cache, jawnymi opcjami i blokadą niewspieranych kombinacji; odtworzyć przykład z pakietu.

- [ ] M7.5 — co najmniej jedna istotnie zmodyfikowana geometria anteny (np. reflektor/director), nowy mesh/reference i te same K; brak geometry-specific hardcode. Raportować zmianę fizyki osobno od błędu przyspieszonego solvera.

## Oszczędzanie czasu i compute

Jedna hipoteza na eksperyment. Kolejność: analiza źródeł → mały test → coax → jedna pełna antena → kwalifikacja obiecującego wariantu. Brak dowodu poprawy kończy gałąź; trzy próby bez nowych informacji wymagają zmiany hipotezy. Pełne sweepy i powtarzanie pomiarów tylko dla finalistów. Zachować medium i fizykę, cache oraz istniejące API. Zakres: maksymalna użyteczna wydajność symulacji na obecnej 5070 Ti/96GB RAM. Bez prac nad Rust, FieldCraft, GUI i integracją CAD. Zachować obecny silnik jako referencję; inny backend wyłącznie jako narzędzie do mierzalnego przyspieszenia obliczeń.

Praktyczna pętla pracy: sekundy na test operatora, około 34 s na obecny coax (limit 180 s); pełny case maks. 1800 s po tanim filtrze. Cache zależności/obiektów/ccache jest obowiązkowo zachowany, nie przebudowywać solvera po zmianie samych dokumentów lub runnera.
