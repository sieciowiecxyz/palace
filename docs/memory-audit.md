# M1 — właściciele alokacji i następny eksperyment

Data: 2026-10-18. Status: historyczny audyt diagnostyczny; M1 został później zamknięty. Pamięć robocza kolejnych prób wyłącznie RAM/VRAM; zakaz dyskowego offloadu pozostaje bez wyjątków. Aktualny zakres i wnioski M1 opisuje [checkpoint](milestones/optimization-M1.md).

## Aktualny audyt resident native complex FP64 — EXP22

`artifacts/m1-cuda-hostclock-antenna-20261018/` zatrzymał się diagnostycznie po4iteracjach W.3. Nie był pełnym solveRF. Daje aktualny tracealloc/free zgodny z medium i native complex, bez historycznego disk storage. Odtworzenie analizy:

```sh
python3 tools/allocation_audit.py artifacts/m1-cuda-hostclock-antenna-20261018/palace.stderr.log --output artifacts/current-allocation-audit.json
```

Raport zachowany w `artifacts/m1-native-current-allocation-audit-20261018.json`.
Szczyt49 583 124 858B, duże alokacje49 392 771 376B (**99,616%**); pozostałe190 353 482B to nieprzypisane drobne bufory. Ten sam stan, bez dodawania osobnego cuDSSpeak.

| Ścieżka alokacji | B w tym samym maksimum |
| --- | ---: |
| cuDSS factors/workspace | 25 008 217 680 |
| MFEM/Palace vectors/workspace | 5 889 957 512 |
| libCEED QFunction assembly | 5 071 206 720 |
| libCEED QFunction evaluation | 4 999 822 592 |
| libCEED basis evaluation | 2 263 841 984 |
| libCEED geometry construction | 2 155 878 272 |
| libCEED other workspace | 2 031 020 376 |
| libCEED element restriction | 1 972 826 240 |

20buforów po538 043 520B daje10,761GB w assembly/basis/QFunction. Nie są automatycznie jedną współdzieloną pulą. Największy pojedynczy bufor cuDSS24,031GB. Triggerpeaku to alokacja89 749 792B w ComplexParOperator::Mult podczas GMRES; nie postprocessing pól. Samo rozpoznanie ścieżki nie rozstrzyga unikatowego semantycznego właściciela każdego bufora.

Native coarse CSR N=2196005/nnz=32284067 ma32-bitowe indeksy i complexFP64 values:4(N+1)+4nnz+16nnz=654465364Bprzed kopiami/stagingiem. Ten logiczny rozmiar jest częścią operator/workspace, nie dodatkowym składnikiem ponad sumę managed. Fineoperator jestPA, nie pełnymCSR11mln×11mln.

To wczesny stan, nie55,148GBpeaku całego35-iteracyjnego solve. Pełny bilansnet-release V/pozostałego solvera jest w [DOF/pamięć](topology-memory.md); GMRESbezZ (osobna bazaZ dotyczy FGMRES, nie tego profilu). Nie utożsamiać logicznej pojemności45V z fizycznymi stronami36Voddanymi po clear. Brak aktywnego audytu każdej drobnej alokacji pozostaje jawną granicą, nie brakującą pamięcią w sumie.

Obecny [profil kerneli/UVM](profiling-window.md) wskazuje295GBmigracji/17,665s i przewagę czasu preconditionera. Hipoteza dla późniejszej pracy FEM: ograniczyć spekulacyjne migracje dużych faktorów i aktywnego workspace przez mniejszą reprezentację/politykę dostępu; porównać całkowityczas+pamięć i K.3/K.4. Nie wdrażać optymalizacji opierającej się tylko na mniejszej rezydencji GPU. Obowiązkowa ocena FEM–BEM poprzedza kolejne promowane zmiany.

## Historyczny audyt — poniżej nie jest aktualnym baseline

## Dowód bez ponownej symulacji

`tools/allocation_audit.py` odtwarza alloc/free i stosy z zachowanego logu. Nie uruchamia Palace, CUDA ani kompilacji. Próg trace to 16 MiB; wszystkie mniejsze alokacje są tylko w łączniku `logical_live_bytes`. Parser wiąże stos z konkretnym zdarzeniem i obsługuje ponowne użycie adresu. Odrzuca brakujące free, duplikaty żywych adresów i niewystarczający stary format. Naprawiono odczyt trzech zdarzeń doklejonych do logu stdout solvera.

```sh
python3 tools/allocation_audit.py artifacts/m1-antenna-fields-fp32-disk-20261018/palace.log --output artifacts/m1-antenna-allocation-audit-20261018.json
```

Źródłem jest historyczny **REJECT** run, którego nie wolno ponawiać. Zapisane dane alokacji służą wyłącznie wskazaniu kosztów operatorów. Nie mierzą resident bazy GMRES ani dopuszczalnego wariantu wydajności. Raport zawiera SHA logu i ścieżkę źródła.

## Alokacje w tej samej chwili

Największy zarejestrowany `logical_live_bytes` = **48 513 788 614 B (45,18 GiB)**. Zgadza się z końcowym `CUDA_UVM: peak_managed_bytes`. Duże żywe alokacje wyjaśniają 48 272 526 476 B (99,50%); różnica 241 262 138 B dotyczy pominiętych drobnych alokacji. Kategorie wynikają ze stosów wywołań, nie z deklaracji semantycznego właściciela każdego bufora.

| Ścieżka alokacji | GiB w chwili maksimum | Liczba |
| --- | ---: | ---: |
| libCEED QFunction evaluation | 11,672 | 29 |
| libCEED basis evaluation | 9,303 | 25 |
| cuDSS factors/workspace | 7,519 | 5 |
| MFEM/Palace vectors/workspace | 5,825 | 87 |
| libCEED QFunction assembly | 4,723 | 15 |
| libCEED pozostały workspace | 2,070 | 18 |
| libCEED geometry construction | 2,008 | 2 |
| libCEED element restriction | 1,837 | 1 |

To **logiczny rozmiar managed allocations**, nie pomiar rezydencji GPU ani całego RAM procesu. cuDSS jest już w tej tabeli: nie dodawać ponownie jego osobnego peak 7,52 GiB. Cgroup peak 49,24 GiB jest inną miarą i mógł wystąpić w innej chwili. Native RSS nie rozlicza całego UVM.

48 buforów ma dokładnie **538 043 520 B** każdy, razem **24,05 GiB**. Ten rozmiar odpowiada `1 601 320 elementów × 14 punktów × 3 składowe × 8 B`. Ślady wiążą je z assembly, basis oraz QFunction evaluation. Wskazuje to na duże pośrednie wektory całej siatki, a nie wyłącznie przechowywanie krylovowskiej bazy.

## Weryfikacja źródeł

Przypięty builder zawiera libCEED commit `cbd49027b0ae891f0c8efd9d9cf05bc82385a388`:

- [CUDA reference operator](https://github.com/CEED/libCEED/blob/cbd49027b0ae891f0c8efd9d9cf05bc82385a388/backends/cuda-ref/ceed-cuda-ref-operator.c): `CeedOperatorSetupFields_Cuda` tworzy `q_vecs_in/out` długości `num_elem * Q * size`; operator trzyma je aż do destrukcji. Część e-vectorów korzysta już z `CeedGetWorkVector/CeedRestoreWorkVector`; nie należy ponownie implementować tego samego bez pomiaru.
- [CUDA gen builder](https://github.com/CEED/libCEED/blob/cbd49027b0ae891f0c8efd9d9cf05bc82385a388/backends/cuda-gen/ceed-cuda-gen-operator-build.cpp): `CEED_EVAL_CURL` i `CEED_EVAL_DIV` ustawiają `use_fallback=true` (TODO). **Samo wybranie cuda/gen nie jest implementacją fused Maxwella**; potrzebne operatory nadal mogą wrócić do reference/shared.
- [Dokumentacja backendów](https://libceed.org/en/latest/libCEEDdev/): MAGMA przyspiesza bazę, gen eliminuje część buforów przez fuzję; opis ogólny nie potwierdza obsługi curl/div w naszej rewizji.
- `palace/fem/libceed/ceed.cpp`: na GPU tworzony jest jeden kontekst Ceed, niezależnie od liczby wątków CPU. Nie przypisywać 48 buforów ośmiu kontekstom OpenMP.

Źródła odczytano w istniejącym builderze, bez zmian zależności; builder następnie zatrzymano. Nie wykonano nowego benchmarku backendu, którego ograniczenie jest już widoczne w źródłach.

## Następna hipoteza — mniejszy workspace bez redukcji precyzji

Priorytet: rozdzielić trwałe pola/q-data od tymczasowych aktywnych Q-wektorów i zbadać współdzielenie tych ostatnich pomiędzy sekwencyjnymi operatorami. Alternatywa: porcjowanie elementów, które nie przechowuje osobnego workspace dla wszystkich porcji. Sam podział na wiele operatorów z własnymi buforami nie musi oszczędzić pamięci.

Warunki prototypu:

1. Bez zmiany medium, quadratury, FP64 operatora i równania. Pool w RAM/VRAM; nigdy pliki/mmap/swap. Trwałe pola bierne, współczynniki i stany wymagane między wywołaniami pozostają własnością operatorów.
2. Najpierw wykazać cykl życia, brak nakładania wywołań oraz poprawną kolejność na strumieniu CUDA. Sam powrót hostowej funkcji nie dowodzi ukończenia kernela. Reentrancy, różne długości i aliasing wymagają kontroli; cache biernych pól nie wolno użyć jako scratch.
3. Zmiana we wskazanym pliku libCEED z zachowanym source/object cache; osobny przypięty build zależności tylko jeżeli prototyp go wymaga. Nie przebudowywać całego toolchainu. Wariant bazowy pozostaje.
4. Test analitycznego tiny TEM i dwa różne operatory naprzemiennie, także transpose/diagonal. Limit 60 s zwykłego smoke, do 120 s diagnostyki. Najpierw Δcomplex S, pola E/B, energia i stopping/raw norm. Dopiero po pozytywnym filtrze ograniczony fragment setup/solve i ewentualny pełny case.
5. Promocja wymaga rzeczywistej redukcji peak RAM/VRAM oraz zmierzonego czasu całego zadania; oszczędzenie części 24 GiB to hipoteza. Alokacje wykorzystywane jednocześnie nie mogą zostać połączone. Nie podawać tej liczby jako obietnicy odzyskania 24 GiB.

To hipoteza do dalszej pracy wynikająca z M1; nie jest promowaną optymalizacją i nie pomija aktywnego, obowiązkowego M2 FEM–BEM/MoM. M1 został zamknięty na podstawie późniejszej kwalifikacji jednego punktu W.3 oraz audytu pamięci; walidacja fizyczna całego pasma i enclosure pozostaje poza tym checkpointem.

## Dlaczego mała norma LEFT nie rozstrzyga jakości

W `InitialResidual` lewostronny GMRES mierzy `||B(b−Ax)|| / ||Bb||`. RAW sprawdza `||b−Ax|| / ||b||`. Przeliczany po rekonstrukcji warunek LEFT usuwa błąd samej rekurencji Arnoldiego, ale nie zmienia metryki na RAW.

Historyczne antenowe dane: FP64 ma LEFT `9,9564e−7`, RAW `0,12527`; FP32 storage ma LEFT `9,9608e−7`, RAW `0,80769`. Ta duża różnica istnieje pomimo małej różnicy pól ważonych energią. Nie wolno uznać FP32 za równoważne rozwiązanie tylko na podstawie portów albo LEFT. Nierównomierne ważenie residuum przez preconditioner jest potwierdzone kodem i kontrolnym TEM (RIGHT schodzi z RAW poniżej 1e−6). Późniejsza niezależna referencja RIGHT i solve W.3 przeszły zamrożone bramki M1; nie jest to jednak walidacja fizyczna całego pasma ani enclosure. To nie dowód wadliwej fizyki.

## Doprecyzowanie fazy maksimum

Rozszerzony parser zachowuje `peak_trigger_event` i jego stos. Dla historycznego peaku 48 513 788 614 B zdarzenie wyzwalające było alokacją 120 352 248 B w ścieżce `DomainPostOperator::GetMagneticFieldEnergy` / **CompareFieldSnapshots**. Szczyt wiąże się więc z diagnostyką porównania pól; nie dowodzi maksimum samego GMRES. Nie dodawać do niego całej bazy ani nie wnioskować, że 48 buforów jest w całości working set Krylov.

Kolejność historycznego zmieszanego stdout solvera i stderr alokacji nie jest wiarygodnym zegarem faz: buforowanie pozostawiło ostatnią wydrukowaną iterację 140 przed alokacją diagnostyki wykonywanej po solve. Późniejszy run FP64 resident użył znaczników monotonicznych wprowadzonych przez `--memory-marks`; zmierzone fazy i ograniczenia interpretacji zapisano w [raporcie faz](memory-phases.md). Oddzielne stdout/stderr zachowują kompletne linie, ale końcowy `palace.log` konkatenowany stdout→stderr nie ma globalnej chronologii. Nie wyznaczać kolejności między strumieniami z tego pliku.

Fazy wykazały największy logiczny peak managed podczas GMRES (54,74 GiB), a nie przy późniejszej diagnostyce pól. Jest to licznik alokacji managed, nie pomiar fizycznej rezydencji VRAM/RAM. Sam historyczny resident run FP64 nie rozstrzygał jakości anteny; późniejsza referencja i kwalifikowany solve W.3 są zebrane w [checkpoint M1](milestones/optimization-M1.md). Nie rozszerzają one wyniku na całe pasmo ani enclosure. Szczegóły historycznego wyniku, stopping check, pól i ograniczeń są w [raporcie faz](memory-phases.md); nie sumować peaków z różnych faz ani nie dodawać osobno cuDSS do managed peak.

Późniejszy Q-pool przeszedł kontrolny Maxwell/TEM, ale na coax-tiny zwiększył logical UVM peak o 5,8% i nie zmniejszył sampled VRAM; [wyniki](ceed-qpool.md). Nie promować tej wersji. Osobne zmniejszenie seedu HYPRE dało 3,75 GiB mniej sampled VRAM procesu na coax-tiny, bez istotnej zmiany portów/energii, a known-TEM L2 pozostał poniżej 1%; [dowody](hypre-pool.md).
