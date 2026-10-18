# Plan optymalizacji Palace

Mode: normal
Active: none

Stan: workflow przygotowany 2026-10-18; wykonywanie badań i nowe symulacje nie są uruchomione. Pierwszy etap po rozpoczęciu pracy: M1. Utworzenie tego planu nie aktywuje goal mode ani płatnego compute.

## Cel

Skrócić czas do **wiarygodnego wyniku medium** i zmniejszyć pamięć na RTX 5070 Ti 16 GB + 96 GB RAM. Rozwijać Palace/MFEM/libCEED w C++/CUDA: UVM, cuDSS, następnie rzeczywiste multi-GPU i Tensor Cores tam, gdzie pomiar uzasadnia ich użycie. Narzędzia pozostają małe, z cache i odtwarzalnym buildem.

Wymagania i uzasadnienie: [speedup](docs/speedup.md). Kryteria: [MILESTONES](MILESTONES.md). Stan wznowienia i wyniki prób: [PROGRESS](PROGRESS.md). Reguły wykonania: [workflow](docs/workflow.md).

Ambicja: dodatkowe ≥1,5× przyspieszenie i ≥25% redukcji porównywalnego szczytu pamięci hosta. Historyczne 955,176 s to punkt odniesienia do odtworzenia w M1, a nie automatycznie baseline nowego buildu. Szukać najlepszego zmierzonego kompromisu czas/pamięć/błąd/koszt; nie obiecywać globalnego optimum.

## Milestones

- [x] M0 — Research i samodzielny fork z cache; zakres dowodów w docs/migration.md.
- [ ] M1 — Wiarygodna referencja, residuum, profil czasu i rachunek pamięci.
- [ ] M2 — GMRES: FP32 storage, FP64 obliczenia i mniej ruchu RAM↔GPU.
- [ ] M3 — Reuse operatorów, preconditionera i faktorów dla wielu portów.
- [ ] M4 — Preconditioner, budżet cuDSS i kontrolowana mixed precision.
- [ ] M5 — Tensor Cores/TF32 na zmierzonym gorącym fragmencie.
- [ ] M6 — Jedna symulacja na 2 GPU, potem warunkowo 4 GPU/NVLink.
- [ ] M7 — Kwalifikacja finalisty, regresje i pakiet do użycia.

## Ścieżka warunkowa

R — prototyp FEM–BEM jest domyślnie nieaktywny, poza główną sekwencją.

M0 łączy wcześniejszy research z zakończoną migracją; M1–M7 odpowiadają etapom w speedup.md. Odhaczanie dotyczy spełnienia wszystkich ID kryteriów. Odrzucenie optymalizacji z dowodami może zamknąć etap eksperymentalny, ale brak sprzętu, timeout lub nierozstrzygnięta poprawność nie spełniają bramki. Kolejność M1 → M2 → M3 → M4 → M5 → M6 → M7; nie otwierać następnego etapu przed zamknięciem poprzedniego. Zmiana kolejności wymaga jawnej decyzji i aktualizacji zależności, bez osłabiania kryteriów.

## Kolejka pracy

### M1 — najpierw podstawa porównań

- [ ] Zinwentaryzować hash wejść, fizyczny wariant, build, ustawienia i dostępne wyniki referencyjne; odtworzyć brakujące minimum na obecnym forku.
- [ ] Prześledzić definicje norm i skalowanie w kodzie; wyjaśnić historyczne raw residual 0,125 / 0,808 mimo małej różnicy S.
- [ ] Ustalić niezależną kontrolę rozwiązania, pól i energii; zamrozić progi przed oceną nowych kandydatów.
- [ ] Zmapować czas: assembly, preconditioner/faktoryzacja, matvec, ortogonalizacja, transfery, postprocessing. Dodać tylko brakujące logi/NVTX.
- [ ] Rozliczyć operator/q-data, bazę V/Z, faktory, workspace i kopie; odróżnić alokację, rezydencję GPU oraz peak RAM.
- [ ] Krótki profil reprezentatywnej fazy plus pełny run bez profilera; ustalić największy koszt i następny jeden eksperyment.

### M2 — największy podejrzany koszt pamięci

- [ ] Zbadać bezpośredni odczyt bazy FP32 w dot/AXPY z akumulacją FP64; usunąć pełne rozpakowania do FP64.
- [ ] Prototyp małego kernela, następnie integracja z MGS GMRES i test ortogonalności/stagnacji.
- [ ] Osobno porównać UVM oraz ograniczone porcjowanie/prefetch bazy; policzyć transfery i bytes/iteration.
- [ ] Restart 120 vs 240 tylko jeśli profil uzasadnia próbę; sprawdzić liczbę iteracji i koszt całego solve.

### M3 — setup raz, kilka RHS

- [ ] Zmierzyć liczbę SetOperators/faktoryzacji i potwierdzić identyczność operatora oraz terminacji między portami.
- [ ] Prototyp reuse na jednej częstotliwości i obu portach; zachować outputy, wznowienia i postprocessing.
- [ ] Symbolic reuse między częstotliwościami i warm start/recycling badać osobno, tylko gdy koszt setup uzasadnia próbę.

### M4 — tańszy preconditioner

- [ ] Sprawdzić w źródłach/aktualnej dokumentacji zgodność cuDSS hybrid memory, hybrid execute, UVM i MPI; przypiąć wersje.
- [ ] Porównać dwa wykonalne budżety hybrid z UVM, po odczycie wymaganego minimum.
- [ ] Zbadać AMS dla właściwego operatora pomocniczego; potwierdzić wykonanie na GPU.
- [ ] FP32 faktory tylko z nową hipotezą: scaling, korekcja FP64, stagnacja i fallback. Jeśli potrzebny FGMRES, najpierw kompatybilność bazy i rachunek dodatkowych wektorów Z.

### M5 — TF32 bez ukrytych kosztów

- [ ] Wybrać rzeczywisty gorący kernel i rozmiary P2 z profilu; oszacować potencjał zysku całego runu.
- [ ] Research cuBLASLt/libCEED/MFEM; CUTLASS dopiero przy brakującej funkcji. Zapisać link, rewizję, licencję i przydatność.
- [ ] Prototyp batchowania: FP32 vs TF32, potem ewentualna korekcja; zmierzyć także packing/scatter/workspace.
- [ ] Potwierdzić użycie Tensor Cores i sprawdzić całe rozwiązanie. BF16/FP16 to osobne hipotezy z kontrolą błędu, nie domyślna zamiana typu.

### M6 — rozłożenie jednej anteny

- [ ] Wykorzystać istniejący wrapper cuDSS MGMN/MPI, ustalić zgodny build i lokalne ownership danych.
- [ ] Mały test 1 vs 2 GPU, potem pełny case: pamięć per rank/GPU, komunikacja, redukcje, replikacja i jakość.
- [ ] Osobno GPU-resident oraz kontrolowany overflow do RAM; PCIe jako fallback, NVLink wyłącznie na właściwym sprzęcie.
- [ ] 4 GPU dopiero po 2 GPU. Porównać także throughput niezależnych częstotliwości, nie mylić go z przyspieszeniem jednego solve.

### M7 — utrwalić najlepszy zaakceptowany wariant

- [ ] Wykonać kwalifikację częstotliwości/portów według MILESTONES, trzy pomiary finalisty bez profilera.
- [ ] Raport tabeli kompromisów i decyzja promote/reject; zachować działającą referencję oraz fallback.
- [ ] Pakiet z manifestem, cache, jawnymi opcjami i blokadą niewspieranych kombinacji; odtworzyć przykład z pakietu.

### R — wyłącznie po decyzji o zmianie metody

- [ ] Uzasadnić udział powietrza w DOF/pamięci i brak wystarczającej poprawy FEM.
- [ ] Research istniejących BEM/kompresji i licencji, prototyp FP64 kula PEC → dipol → dielektryk.
- [ ] CUDA/TF32 i połączenie z Palace dopiero po poprawności i przewadze małego prototypu.

## Oszczędzanie czasu i compute

Jedna hipoteza na eksperyment. Kolejność: analiza źródeł → mały test → coax → jedna pełna antena → kwalifikacja obiecującego wariantu. Brak dowodu poprawy kończy gałąź; trzy próby bez nowych informacji wymagają zmiany hipotezy. Pełne sweepy i powtarzanie pomiarów tylko dla finalistów. Zachować medium i fizykę, cache oraz istniejące API; bez nowego runtime Rust i przebudowy całego stosu bez uzasadnienia.
