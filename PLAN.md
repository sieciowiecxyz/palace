# Plan optymalizacji Palace

Twarde wymaganie użytkownika (2026-10-18): wszystkie dane robocze solvera w RAM/VRAM. Zakaz przenoszenia bazy, macierzy i workspace na SSD/NVMe oraz używania swap do zmieszczenia zadania. UVM wyłącznie GPU↔RAM. Cache builda i zwykłe wejścia/wyjścia pozostają; historyczne eksperymenty z bazą dyskową są odrzucone i nie są dopuszczalnym baseline wydajności.
Mode: goal
Active: M2

Stan: goal aktywowany 2026-10-18 na polecenie użytkownika. M1 ukończony po referencji, aktualnym audycie pamięci i profilu; aktywny M2: prototyp Maxwell FEM–BEM. Compute lokalny; bez najmu chmury.

## Cel

Skrócić czas do **wiarygodnego wyniku medium** i zmniejszyć pamięć na RTX 5070 Ti 16 GB + 96 GB RAM. Rozwijać Palace/MFEM/libCEED w C++/CUDA: UVM, cuDSS, mixed precision i Tensor Cores tam, gdzie pomiar uzasadnia ich użycie. FEM–BEM/MoM to obowiązkowy kierunek researchu i prototypowania. Aktualny cel obejmuje jedną kartę; multi-GPU pozostaje poza kryteriami ukończenia. Narzędzia pozostają małe, z cache i odtwarzalnym buildem.

Wymagania i uzasadnienie: [speedup](docs/speedup.md). Kryteria: [MILESTONES](MILESTONES.md). Stan wznowienia i wyniki prób: [PROGRESS](PROGRESS.md). Reguły wykonania: [workflow](docs/workflow.md).

Ambicja: dodatkowe ≥1,5× przyspieszenie i ≥25% redukcji porównywalnego szczytu pamięci roboczej. Historyczne 955,176 s to punkt odniesienia do odtworzenia w M1, a nie automatycznie baseline nowego buildu. Oddzielnie mierzyć VRAM, RAM, rozmiar alokacji i transfery; samo przeniesienie danych do RAM nie wystarcza. Szukać najlepszego zmierzonego kompromisu czas/pamięć/błąd/koszt; nie obiecywać globalnego optimum.

## Milestones

- [x] M0 — Research i samodzielny fork z cache; zakres dowodów w docs/migration.md.
- [x] M1 — Referencja, niezależna jakość, profil i koszt powietrza w FEM; docs/milestones/M1.md.
- [ ] M2 — FEM–BEM/MoM: research, prototyp Maxwell i pomiar opłacalności.
- [ ] M3 — GMRES, kompresja bazy i ograniczenie migracji RAM↔GPU.
- [ ] M4 — Reuse operatorów, preconditionera i faktorów między portami.
- [ ] M5 — Preconditioner, cuDSS i kontrolowana mixed precision.
- [ ] M6 — Tensor Cores/TF32/BF16 na zmierzonym gorącym fragmencie.
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
- [ ] Zmierzyć setup+solve, macierz/kompresję/workspace i przewidywany koszt docelowej anteny; gęsta macierz BEM bez kompresji może przegrać.
- [ ] Jeśli prototyp daje przewagę i poprawne pola/energię, przygotować izolowaną integrację operatora blokowego w Palace i porównać reprezentatywny case. Inaczej zapisać odrzucenie/ograniczenie; wynik Helmholtz nie kwalifikuje Maxwell.

### M3 — największy podejrzany koszt pamięci

- [ ] Zbadać bezpośredni odczyt bazy FP32 w dot/AXPY z akumulacją FP64; usunąć pełne rozpakowania do FP64.
- [ ] Prototyp małego kernela, następnie integracja z MGS GMRES i test ortogonalności/stagnacji.
- [ ] Osobno porównać UVM oraz ograniczone porcjowanie/prefetch bazy; policzyć transfery i bytes/iteration.
- [ ] Restart 120 vs 240 tylko jeśli profil uzasadnia próbę; sprawdzić liczbę iteracji i koszt całego solve.

### M4 — setup raz, kilka RHS

- [ ] Zmierzyć liczbę SetOperators/faktoryzacji i potwierdzić identyczność operatora oraz terminacji między portami.
- [ ] Prototyp reuse na jednej częstotliwości i obu portach; zachować outputy, wznowienia i postprocessing.
- [ ] Symbolic reuse między częstotliwościami i warm start/recycling badać osobno, tylko gdy koszt setup uzasadnia próbę.

### M5 — tańszy preconditioner

- [ ] Sprawdzić w źródłach/aktualnej dokumentacji zgodność cuDSS hybrid memory, hybrid execute, UVM i MPI; przypiąć wersje.
- [ ] Porównać dwa wykonalne budżety hybrid z UVM, po odczycie wymaganego minimum.
- [ ] Zbadać AMS dla właściwego operatora pomocniczego; potwierdzić wykonanie na GPU.
- [ ] FP32 faktory tylko z nową hipotezą: scaling, korekcja FP64, stagnacja i fallback. Jeśli potrzebny FGMRES, najpierw kompatybilność bazy i rachunek dodatkowych wektorów Z.

### M6 — TF32 bez ukrytych kosztów

- [ ] Wybrać rzeczywisty gorący kernel i rozmiary P2 z profilu; oszacować potencjał zysku całego runu.
- [ ] Research cuBLASLt/libCEED/MFEM; CUTLASS dopiero przy brakującej funkcji. Zapisać link, rewizję, licencję i przydatność.
- [ ] Prototyp batchowania: FP32 vs TF32, potem ewentualna korekcja; zmierzyć także packing/scatter/workspace.
- [ ] Potwierdzić użycie Tensor Cores i sprawdzić całe rozwiązanie. BF16/FP16 to osobne hipotezy z kontrolą błędu, nie domyślna zamiana typu.

### M7 — utrwalić najlepszy zaakceptowany wariant

- [ ] Wykonać kwalifikację częstotliwości/portów według MILESTONES, trzy pomiary finalisty bez profilera.
- [ ] Raport tabeli kompromisów i decyzja promote/reject; zachować działającą referencję oraz fallback.
- [ ] Pakiet z manifestem, cache, jawnymi opcjami i blokadą niewspieranych kombinacji; odtworzyć przykład z pakietu.

## Oszczędzanie czasu i compute

Jedna hipoteza na eksperyment. Kolejność: analiza źródeł → mały test → coax → jedna pełna antena → kwalifikacja obiecującego wariantu. Brak dowodu poprawy kończy gałąź; trzy próby bez nowych informacji wymagają zmiany hipotezy. Pełne sweepy i powtarzanie pomiarów tylko dla finalistów. Zachować medium i fizykę, cache oraz istniejące API; bez nowego runtime Rust i przebudowy całego stosu bez uzasadnienia.

Praktyczna pętla pracy: sekundy na test operatora, około 34 s na obecny coax (limit 180 s); pełny case maks. 1800 s po tanim filtrze. Cache zależności/obiektów/ccache jest obowiązkowo zachowany, nie przebudowywać solvera po zmianie samych dokumentów lub runnera.
