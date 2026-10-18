# Plan optymalizacji Palace

Mode: goal
Active: M1

Stan: goal aktywowany 2026-10-18 na polecenie użytkownika. Trwa M1: referencja, diagnostyka i audyt kosztu FEM. Compute lokalny; bez najmu chmury.

## Cel

Skrócić czas do **wiarygodnego wyniku medium** i zmniejszyć pamięć na RTX 5070 Ti 16 GB + 96 GB RAM. Rozwijać Palace/MFEM/libCEED w C++/CUDA: UVM, cuDSS, mixed precision i Tensor Cores tam, gdzie pomiar uzasadnia ich użycie. FEM–BEM/MoM to obowiązkowy kierunek researchu i prototypowania. Aktualny cel obejmuje jedną kartę; multi-GPU pozostaje poza kryteriami ukończenia. Narzędzia pozostają małe, z cache i odtwarzalnym buildem.

Wymagania i uzasadnienie: [speedup](docs/speedup.md). Kryteria: [MILESTONES](MILESTONES.md). Stan wznowienia i wyniki prób: [PROGRESS](PROGRESS.md). Reguły wykonania: [workflow](docs/workflow.md).

Ambicja: dodatkowe ≥1,5× przyspieszenie i ≥25% redukcji porównywalnego szczytu pamięci roboczej. Historyczne 955,176 s to punkt odniesienia do odtworzenia w M1, a nie automatycznie baseline nowego buildu. Oddzielnie mierzyć VRAM, RAM, rozmiar alokacji i transfery; samo przeniesienie danych do RAM nie wystarcza. Szukać najlepszego zmierzonego kompromisu czas/pamięć/błąd/koszt; nie obiecywać globalnego optimum.

## Milestones

- [x] M0 — Research i samodzielny fork z cache; zakres dowodów w docs/migration.md.
- [ ] M1 — Referencja, niezależna jakość, profil i koszt powietrza w FEM.
- [ ] M2 — FEM–BEM/MoM: research, prototyp Maxwell i pomiar opłacalności.
- [ ] M3 — GMRES, kompresja bazy i ograniczenie migracji RAM↔GPU.
- [ ] M4 — Reuse operatorów, preconditionera i faktorów między portami.
- [ ] M5 — Preconditioner, cuDSS i kontrolowana mixed precision.
- [ ] M6 — Tensor Cores/TF32/BF16 na zmierzonym gorącym fragmencie.
- [ ] M7 — Kwalifikacja najlepszego wariantu na jednej 5070 Ti i pakiet do użycia.

Etapy kolejno M1 → M2 → M3 → M4 → M5 → M6 → M7. Każda bramka obejmuje jakość i porównywalne pomiary. Negatywna ocena prototypu może zamknąć hipotezę z dowodami; nie wymuszać integracji wolniejszego solvera. Brak poprawności lub brak wykonania wymaganego testu nie zalicza bramki. Plan i numeracja zastępują wcześniejszą kolejkę z obowiązkowym multi-GPU.

## Kolejka pracy

### M1 — najpierw podstawa porównań

- [x] Dodać i sprawdzić na tiny normę różnicy całych pól, detekcję kontrolowanego błędu i zgodność disk/resident.
- [x] Zachować bieżącą referencję anteny FP64-disk i jej E/B; kandydatFP32 nie ukończył solve przez RAMguard.
- [ ] Rozliczyć właścicieli UVM i host/cgroup peak przed nowym pełnym kandydatem; nie ponawiać bez zmiany.

- [x] Dodać osobne logowanie raw/LEFT residual i sprawdzić wpływ strony preconditionera na znanym TEM.
- [x] Przygotować szybki coax-tiny oraz porównanie analitycznego E/B i całego L2, jawnie oddzielone od anteny.

- [ ] Zinwentaryzować hash wejść, fizyczny wariant, build, ustawienia i dostępne wyniki referencyjne; odtworzyć brakujące minimum na obecnym forku.
- [ ] Prześledzić definicje norm i skalowanie w kodzie; wyjaśnić historyczne raw residual 0,125 / 0,808 mimo małej różnicy S.
- [ ] Ustalić niezależną kontrolę rozwiązania, pól i energii; zamrozić progi przed oceną nowych kandydatów.
- [ ] Zmapować czas: assembly, preconditioner/faktoryzacja, matvec, ortogonalizacja, transfery, postprocessing. Dodać tylko brakujące logi/NVTX.
- [ ] Rozliczyć udział powietrza i granicy zewnętrznej oraz operator/q-data, bazę V/Z, faktory, workspace i kopie; odróżnić alokację, rezydencję GPU oraz peak RAM.
- [ ] Krótki profil reprezentatywnej fazy plus pełny run bez profilera; ustalić największy koszt i następny jeden eksperyment.

### M2 — metoda dopasowana do otwartej anteny

- [ ] W M1 policzyć udział powietrza w elementach/DOF i budżecie pamięci oraz powierzchnię potencjalnego interfejsu; nie utożsamiać objętości z kosztem solvera.
- [ ] Porównać FEM–BEM, powierzchniowy MoM i akcelerację FMM/MLFMA/H²; sprawdzić Maxwell, dielektryki, otwarte cienkie metale, zasilanie i promieniowanie.
- [ ] Przejrzeć istniejące biblioteki, źródła i licencje; oddzielić GPU assembly od GPU matvec/FMM/solve. Nie zakładać CUDA/TC na podstawie etykiety GPU.
- [ ] Przygotować rzeczywisty mały prototyp Maxwell: kula PEC z odniesieniem, potem dielektryk i sprzężony interfejs FEM–BEM. Porównać do FEM przy porównywalnym błędzie.
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
