# Palace: mniej pamięci, krótsze obliczenia i metody dla jednej GPU

Polityka SSD doprecyzowana przez użytkownika (2026-10-19): gorące dane solvera w RAM/VRAM; UVM GPU↔RAM. Zwykłe wejścia/wyniki, cache i sporadyczny odczyt SSD są dozwolone. Niewielkie zapisy wymagają pomiaru wolumenu i częstotliwości I/O; nie deklarować zerowego zużycia dysku. Bez swapowania zadania i intensywnego przepisywania bazy/macierzowych workspace na SSD w pętli solvera. Obecny disk basis pozostaje usunięty; dawne wyniki z nim nie stają się przez tę korektę zakwalifikowanym baseline. Nową metodę używającą dysku oceniać po zmierzonym I/O, czasie i dokładności.
Plan przeniesiony z repo antenowego. Historyczne ścieżki `infra/palace`, STATE i polecenia odnoszą się do tamtego repo; aktualny build/runner tego forka opisuje [build.md](build.md).

Badania z 2026-10-18 zakończone 2026-10-22: [audyt wyników i ograniczeń](milestones/final-audit.md), [historyczny kontrakt](milestones/optimization-contract.md). Obecne [PLAN](../PLAN.md) i [MILESTONES](../MILESTONES.md) dotyczą przygotowania lokalnych PR-ów; nie reaktywują badań.

Data opracowania: 2026-10-18. Status: dokument historyczny; poniżej pierwotne cele i kierunki researchu.
Dokument zbiera cele użytkownika, wyniki wcześniejszych prób, weryfikację załącznika i plan dalszej pracy.
Liczby historyczne niżej nie są nowymi benchmarkami; bieżące uruchomienia rejestruje PROGRESS.md.

## 1. Cel i decyzja

**Cel użytkownika:** znacznie skrócić czas do wiarygodnego wyniku anteny i zmniejszyć pamięć roboczą, tak aby medium było praktyczne na RTX 5070 Ti 16 GB + 96 GB RAM. Ten sam rozwijany solver ma obsługiwać CUDA, przekroczenie VRAM przez pamięć hosta (CUDA Unified Memory, dalej UVM) na jednej dostępnej karcie. Multi-GPU zachowujemy jako przyszły kierunek poza kryteriami obecnego celu. Wykorzystać Tensor Cores/TF32 wszędzie, gdzie daje to rzeczywisty zysk przy zaakceptowanym błędzie. Zachować cuDSS jako wspieraną ścieżkę.

**Moja rekomendacja:** małe, mierzalne rozszerzenia Palace/MFEM/libCEED w C++/CUDA. Najpierw wiarygodna referencja i koszt powietrza, potem obowiązkowy prototyp Maxwell FEM–BEM/MoM, pamięć GMRES/migracje, reuse setup, preconditioner i wybrane operacje Tensor Core. Reużyć istniejący kod; przepisywanie solvera do Rust nie jest pierwszą inwestycją.

To wybór na podstawie dotychczasowych danych, a nie dowód globalnej optymalności. Kolejność zmieniamy po pomiarze wskazującym inne dominujące koszty.

Wymagania z rozmowy:

- Otwarty, możliwy do debugowania kod aplikacji. FEKO jest odrzucone przez użytkownika. NVIDIA cuDSS/cuBLAS pozostają zewnętrznymi bibliotekami binarnymi: otwarty fork Palace nie otwiera ich wnętrza.
- Domyślnie **medium**. Nie poprawiać czasu przez niejawne uproszczenie feedu, zmianę materiału, siatki lub pominięcie istotnej fizyki.
- Dopuszczalna niższa precyzja, jeśli oszczędza zasoby i przechodzi kontrolę wyników. Nie ma wymagania, żeby całość pozostawała FP64, ani żeby całość używała TF32.
- Minimalistyczna infrastruktura; wykorzystać istniejące buildy, cache, runner i parser. Nie tworzyć drugiej platformy do tego samego zadania.
- Koszt i czas pracy także są kryteriami. Najpierw lokalny mały eksperyment, potem pojedyncza pełna antena; większa kampania tylko dla obiecującego wariantu.
- Agent główny projektuje, analizuje i kwalifikuje. Istniejący GPT-6 Luna high dostaje gotowe polecenia do uruchamiania/oczekiwania/odbioru, bez delegowania mu projektu solvera.

## 2. Jaki problem optymalizujemy

Ye T-Shaped: dwa porty, cienki laminat PTFE ZYF300CA-C, metalowe płatki i szczeliny, director, reflektor oraz rzeczywiste zasilanie coax/SMA. Priorytet n78, następnie LTE B1/B3/B7. W projekcie istnieje też kierunek feedera do czaszy; obecny benchmark panelu nie potwierdza wydajności kompletnej paraboli.

Fizyczny cel anteny to VSWR poniżej 1,6 na interesujących częstotliwościach, optymalnie poniżej 1,5, bez pogorszenia innych pasm, izolacji, sprawności i promieniowania. **Optymalizacja solvera ma zachować wynik danego modelu, a nie sztucznie obniżać jego VSWR.** Wariant użyty w benchmarku wydajności nie jest automatycznie najlepszym baseline antenowym.

Aktualna ścieżka obliczeń: FEM częstotliwościowe → operator partial assembly → GMRES → wielopoziomowy preconditioner → cuDSS na złożonym poziomie coarse. cuDSS nie rozkłada całego operatora wysokiego rzędu. Palace już wspiera partial assembly i MPI/GPU; to funkcje do wykorzystania, nie nowe wynalazki. [Palace: GPU i równoległość](https://awslabs.github.io/palace/dev/guide/parallelism/)

## 3. Co już wiemy — nie powtarzać bez powodu

Źródła lokalne: [raport](local-optimization-results.md), [zakończona checklista](../LOCAL_OPTIMIZATION.md), artefakty `artifacts/infra/local-optimization-20261018/`. Wszystkie liczby niżej dotyczą wcześniejszych pomiarów, nie tej sesji researchu.

| Fakt | Wynik i znaczenie |
|---|---|
| Duży przypadek | 3,50 GHz, port 2; 1 601 320 tetrahedrów, 11 218 724 DOF |
| Parametry | Order=2, Tol=1e-6, MaxIts=1600, MaxSize=240, PartialAssemblyOrder=1, backend MAGMA |
| Wybrany wariant | Operator/faktory FP64, zapis bazy GMRES FP32, arytmetyka FP64, UVM, niezależna kontrola normy zatrzymania |
| Czas, 3 powtórzenia | Mediana 955,176 s; referencja z bazą FP64 na SSD 1194,812 s; 20,06% krótszy czas |
| Ograniczenie porównania | To nie jest porównanie z pełnym FP64 mieszczącym się w dużej karcie GPU |
| Pamięć | Szczyt cgroup około 45,36 GiB; całe GPU około 15,5 GiB, łącznie z innymi użytkownikami GPU |
| Zgodność | max delta complex S około 4,15e-6; delta VSWR około 1,33e-5; zgodne z ustalonymi progami |
| Iteracje | 151 w obu wariantach; niezależnie przeliczona względna norma zatrzymania około 9,96e-7 |
| Próba faktorów FP32 | Duży model nie uzyskał zaakceptowanego wyniku w 1800 s; kontrola wykryła rozjazd rekursji i wymusiła restart |
| Profil częściowy | Ponad 2 TB skumulowanego ruchu RAM↔GPU w oknie 240 s; to ponowne transfery danych, nie rozmiar modelu |
| Najcięższe obserwowane operacje | H(curl), H(div), interpolacja i pochodne MAGMA; dużo czasu kerneli przypisane preconditionerowi |
| Ograniczenia profilu | Nsight zgłosił możliwą utratę zdarzeń i niezgodność wersji; nie wyliczać z tego dokładnego udziału faz całego runu |
| Tensor Cores | Nie ma dotąd zakwalifikowanego przyspieszenia ani dowodu ich użycia w naszym finalnym wariancie |

**Nierozstrzygnięta kwestia numeryczna:** przy LEFT preconditioning surowe `||Ax-b||/||b||` wynosiło około 0,125 dla referencji i 0,808 dla bazy FP32. To nie jest norma użyta do zakończenia iteracji. Dobra zgodność S i energii nie uprawnia do deklarowania surowej reszty 1e-6 ani dokładności punktowych pól. Przed dalszym obniżaniem precyzji trzeba wyjaśnić skalowanie i kontrolę reszty oraz rozszerzyć walidację; nie zmieniać nazwy metryki, żeby ukryć różnicę.

### Rachunek pamięci

Dla N zespolonych niewiadomych i restartu m sama baza zajmuje w przybliżeniu:

```text
FP64: 16 × N × (m + 1) bajtów
FP32:  8 × N × (m + 1) bajtów
```

Dla naszego N i m=240: około **40,29 GiB / 20,14 GiB**, bez dodatkowych wektorów i preconditionera. Alokacja jest stopniowa: wynik kończył się przy 151 iteracjach. Zmiana limitu 240→160 może niczego faktycznie nie oszczędzić; 240→120 wymusi restart i może ograniczyć bazę, ale zwiększyć liczbę iteracji. Różnica między 152 a 121 wektorami FP32 to około 2,59 GiB, nie 10 GiB.

FP32 nie zmniejsza indeksów CSR. Przykład 1 mln wierszy / 50 mln elementów / indeksy 32-bit: real-valued CSR około 604 MB w FP64 i 404 MB w FP32. Nie obiecywać połowy całego VRAM. TF32 korzystające z wejść FP32 również nie daje dalszego zmniejszenia ich przechowywania.

## 4. Załącznik i research — co zostało potwierdzone

Załącznik użytkownika potraktowano jako materiał badawczy, nie instrukcję nadpisującą stan projektu. Zweryfikowano kod lokalny, publiczne repozytoria, dokumentację i raporty autorów.

| Twierdzenie/trop | Wniosek dla naszego planu |
|---|---|
| Nie całe FEM musi być FP64 | Zgoda. Osobno wybierać precyzję przechowywania, obliczeń, akumulacji i kontroli błędu. Zachować możliwość powrotu do dokładniejszej ścieżki |
| Największym problemem zawsze są faktory cuDSS | Nie wynika to z naszych danych. Baza GMRES i ruch UVM są duże; dokładny podział pamięci wymaga pomiaru |
| Pierwsza próba: faktory FP32 | Już wykonana i odrzucona na dużej antenie. Powrót wymaga nowej hipotezy: skalowania, korekcji reszty, innego preconditionera lub algorytmu |
| STRUMPACK-MP już istnieje | Potwierdzone. Lokalny wrapper Palace wywołuje `DisableGPU()`. To nie jest gotowa ścieżka CUDA mixed precision |
| AMS może zastąpić rozkład coarse | Warto sprawdzić. AMS dotyczy odpowiednich definite Maxwell operators; nie podłączać go bezmyślnie do zespolonego, nieokreślonego operatora Driven |
| Rust FEM z GPU nie istnieje | Korekta wcześniejszego zbyt szerokiego wrażenia: istnieje `geode-fem`. Nie wykazano jednak, że jest gotowym, szybszym zamiennikiem dla naszego modelu |
| TF32 automatycznie przyspieszy solver | Nie. Może pogorszyć zbieżność; szybkość jednej iteracji nie jest czasem do poprawnego rozwiązania |

W `geode-fem` autorzy udostępnili test A100 z 2026-10-07: ścieżka automatycznie używająca TF32 zatrzymała poprawę przy reszcie około 0,163; większe przebiegi FP32 miały jawne reszty rzędu 5e-3–2e-2 zamiast 1e-6. To ich wyniki dla konkretnej wersji i preconditionera, nie nasze pomiary i nie dowód przeciw każdemu mixed precision. Dają jednak mocny powód, by nie migrować na podstawie samej deklaracji GPU/Rust. [Raport autorów, przypięta rewizja](https://github.com/rjwalters/geode-fem/blob/43db1c626bdc2367f896905d7807979789ee22b3/benchmarks/gpu_driven_scaling/results_large_a100.toml)

Istnieje też pozytywny precedens: autorzy pracy o MFEM z marca 2026 pokazują przyspieszenia wybranych operacji FEM dzięki FP64 Tensor Cores i fuzji kerneli na GH200/GB200. To wskazówka do organizacji obliczeń, nie wynik dla naszego P2 na tetrahedrach ani RTX 5070 Ti. Trzeba oddzielić zysk samej zmiany precyzji od fuzji i ograniczenia ruchu pamięci. [Publikacja i konfiguracje eksperymentów](https://arxiv.org/html/2603.09038v1)

## 5. Repozytoria: co wykorzystać, a czego nie integrować od razu

Sprawdzono 2026-10-18. SHA wskazuje snapshot researchu, nie polecenie aktualizacji działającego runtime. Funkcja w bibliotece upstream nie oznacza jeszcze działającej integracji w naszym buildzie.

| Repozytorium | Rola i ograniczenie | Decyzja |
|---|---|---|
| [awslabs/palace](https://github.com/awslabs/palace) | FEM, MPI, Krylov, multigrid, istniejąca fizyka/porty | Główna baza; małe opcjonalne zmiany |
| [mfem/mfem](https://github.com/mfem/mfem) | Dane FEM, urządzenia, wrapper cuDSS; lokalne źródło już zawiera komunikację i rozkład wierszy MGMN | Reużyć i zweryfikować zamiast pisać od nowa |
| [CEED/libCEED](https://github.com/CEED/libCEED) | Partial assembly i backend MAGMA; odpowiedni poziom do optymalizacji lokalnych działań FEM | Główne miejsce eksperymentu Tensor Core |
| [hypre-space/hypre](https://github.com/hypre-space/hypre) | AMS/AMG i obsługa GPU zależna od opcji/builda; AMS wymaga właściwego operatora pomocniczego | Wczesny ograniczony benchmark alternatywy dla coarse cuDSS; [warunki AMS](https://hypre.readthedocs.io/en/latest/solvers-ams.html) |
| [ginkgo-project/ginkgo](https://github.com/ginkgo-project/ginkgo) | Gotowy compressed-basis GMRES i kernele GPU | Źródło algorytmu/testów lub izolowany adapter. Nie zakładać, że CB-GMRES automatycznie obsłuży nasz distributed operator i wszystkie normy; [przykład](https://ginkgo-project.github.io/ginkgo-generated-documentation/doc/master/cb_gmres.html) |
| [NVIDIA/CUDALibrarySamples](https://github.com/NVIDIA/CUDALibrarySamples/tree/master/cuDSS) | Przykłady właściwego użycia cuDSS | Podstawa małych testów zgodności wersji i komunikacji |
| [NVIDIA/cutlass](https://github.com/NVIDIA/cutlass) | Kernele macierzowe CUDA/Tensor Core | Dopiero gdy cuBLASLt nie daje dobrego kernela dla zmierzonych rozmiarów; jawny dobór SM120 |
| [pghysels/STRUMPACK](https://github.com/pghysels/STRUMPACK) | Faktoryzacja i kompresja; osobna duża zależność | Rezerwa. Palace wyłącza GPU w wrapperze; istnieje też zgłoszenie konfliktu kontekstu CUDA. To zgłoszenie użytkownika, nie nasza reprodukcja: [issue #803](https://github.com/awslabs/palace/issues/803) |
| [rjwalters/geode-fem](https://github.com/rjwalters/geode-fem) | Rust/Burn, FEM/DG, CUDA; rzeczywisty projekt i publiczne benchmarki | Obserwować/podpatrywać; brak podstaw do migracji naszego medium |
| [ecrc/h2opus](https://github.com/ecrc/h2opus) | H², kompresja, GPU i wybrane operacje multi-GPU | Tylko dla prototypu BEM; biblioteka algebry, nie elektromagnetyki. Zweryfikować complex arithmetic i port na aktualny CUDA; sprawdzony master pochodzi z 2022 r. |
| [bempp/bempp-cl](https://github.com/bempp/bempp-cl) | Otwarte operatory BEM Maxwella; przydatna niezależna referencja | Walidacja prototypu BEM, nie gotowy backend CUDA do Palace |
| [bempp/bempp-rs](https://github.com/bempp/bempp-rs) | Rust BEM; README wskazuje Laplace/Helmholtz | Nie utożsamiać z kompletnym solverem Maxwella/anteny |
| [chelsea0x3b/cudarc](https://github.com/chelsea0x3b/cudarc) | Rust wrappers CUDA, cuBLASLt, NCCL itd. | Ewentualnie mały niezależny prototyp; brak powodu do nowej warstwy FFI w obecnym Palace |

Najważniejsze snapshoty researchu: Palace `e1bdf9b7d8eb09cf32f947510b527ad879cc9e15`, MFEM `54d7f64513464396faa5bf86ff68d64956315c9d`, libCEED `bf0eb79a1ab0ddd48015e00a6d9a16e7bdd706c9`, Ginkgo `35f409a23f452ee4371d56ddb3891a5ff7b00ca0`, geode-fem `43db1c626bdc2367f896905d7807979789ee22b3`.

Lokalne checkouty sprawdzone podczas tego audytu: Palace `0fb92e08e6c8c28488c393cef3f738c4b5e8c4bc`, MFEM `10b0b596dbc26dca384b9f25f23026b1a6403592`. Pochodzenie faktycznie uruchamianego obrazu należy brać z manifestu buildu, nie z bieżącego HEAD katalogu.

## 6. Architektura, którą warto rozwijać

```text
Istniejący model / mesh medium / porty
                  ↓
Palace + MFEM + libCEED: operator FEM, początkowo FP64
                  ↓
GMRES: kompaktowa baza + kontrola reszty + lokalne dane per MPI rank
                  ↓
Preconditioner: multigrid, wybrane operacje FP32/TF32 po walidacji
                  ↓
Coarse: cuDSS FP64 / cuDSS hybrid / test AMS

Każda karta: własna część danych, budżet VRAM, logi pamięci i migracji
Między kartami: komunikacja MPI/P2P; NVLink wykorzystany, gdy dostępny
Pamięć hosta: kontrolowany overflow zamiast niejawnych kopii całego problemu
```

### Pamięć i GMRES

Pierwszy cel kodowy: bezpośredni odczyt bazy FP32 w dot/AXPY z konwersją do FP64 w kernelu i redukcją FP64. Obecny patch wielokrotnie rozpakowuje cały wektor do bufora FP64. Zmniejszyć zapis/odczyt buforów, zachowując na początku kolejność MGS; sam dot i AXPY nadal mają zależność przez współczynnik projekcji.

Potem zbadać przetwarzanie blokami i ewentualnie CGS2/blokową ortogonalizację. Zmiana algorytmu wymaga oddzielnej kontroli ortogonalności, liczby redukcji i zbieżności. Nie obiecywać dużego spadku szczytowego VRAM wyłącznie po usunięciu jednego scratch buffera.

Trzy polityki pamięci do porównania, a nie trzy równoczesne obowiązkowe mechanizmy:

1. Device-resident dla aktywnych danych, gdy się mieszczą.
2. UVM z budżetem, poprawnym ownerem GPU, advice/prefetch i kontrolą migracji.
3. Jawne porcjowanie starej bazy z RAM przez ograniczone bufory pinned, jeśli UVM thrashuje. Nie pinować dziesiątek GB bez potrzeby.

### Preconditioner i precyzja

Zachować osobne wybory dla storage, arithmetic, accumulation i residual evaluation. Nowe FP32 faktory mają sens dopiero z kontrolowaną korekcją względem dokładniejszego operatora i pomiarem całkowitego kosztu. Adaptacyjne rozwiązanie wewnętrzne może wymagać FGMRES; **obecny patch skompresowanej bazy obsługuje tylko MGS GMRES i jawnie odrzuca FGMRES**. FGMRES przechowuje też preconditioned vectors, co trzeba uwzględnić w pamięci.

Korekcja ma postać `r = b - A_ref*x`, przybliżone rozwiązanie dla poprawki `d`, potem `x = x + d`. Gdy dotyczy tylko preconditionera, jego korekcję sprawdzamy względem odpowiedniego `P_ref`, a końcową poprawność nadal względem `A_ref`. Konwersja utraconych danych FP32 z powrotem do FP64 nie odtwarza dokładnej referencji. Stałe faktory wykorzystywać ponownie; kontrolować stagnację i koszt konwersji/korekcji.

AMS badać na kompatybilnym operatorze pomocniczym/shifted multigrid; nie stosować CG do całego zespolonego układu Driven na podstawie nazwy „Maxwell”. Zmiana preconditionera może zmieniać normę preconditioned residual, więc porównanie musi zawierać też miarę niezależną od niego.

### Tensor Cores

Najpierw grupować lokalne zastosowania baz/interpolacji/pochodnych do wielu elementów. Wtedy wspólna mała macierz bazy może działać na większej liczbie kolumn. Zwykły GEMV lub CSR SpMV nie staje się efektywnym GEMM przez zmianę typu danych. Koszt gather/scatter, paddingu, workspace i konwersji jest częścią benchmarku.

Porównać: aktualny MAGMA → dokładniejszy odpowiednik operacji → FP32 → TF32 z akumulacją FP32, początkowo wyłącznie wewnątrz preconditionera. Sprawdzić rzeczywiste instrukcje/liczniki Tensor Core. „magma”, „tensor” w nazwie albo wysoki GPU utilization nie są takim dowodem.

Opcja rezerwowa: cuBLAS fixed-point emulation FP64, udokumentowana dla SM12.x od CUDA 13.0u2; obecny zakwalifikowany runtime jest na CUDA 12.9.1. To osobny build i mikrobenchmark, nie globalny przełącznik naszego libCEED. BF16x9 w sprawdzonej tabeli dotyczy SM10.0/10.3, więc nie przenosić tej obietnicy na RTX 5070 Ti. [cuBLAS: formaty i emulacja](https://docs.nvidia.com/cuda/cublas/index.html#floating-point-emulation)

Nie zmieniać głównego operatora na TF32 bez osobnego badania błędu operatora. Kontrola `b - A_approx*x` nie dowodzi rozwiązania `A_ref*x=b`. Dla operatora mieszanego raportować obie reszty i błędy obserwabli.

### Multi-GPU i cuDSS

Podział jednego problemu to osobna funkcja od wysłania różnych częstotliwości na różne karty. Oba tryby są użyteczne; pierwszy zwiększa dostępną pamięć dla pojedynczego przypadku, drugi przepustowość kampanii.

Lokalny MFEM już ma `cudssSetCommLayer`, communicator oraz `cudssMatrixSetDistributionRow1d` dla CSR/RHS/rozwiązania. **Najpierw uruchomić i sprawdzić istniejącą ścieżkę, potem poprawiać brakujące elementy.** Sprawdzić każdy rank, przynależność GPU, globalne/lokalne wymiary, typy indeksów, sumowanie reszt i brak pełnych kopii bazy na każdej karcie.

Nie utożsamiać UVM, cuDSS hybrid memory i cuDSS hybrid execute. To różne mechanizmy. Oficjalna dokumentacja opisuje MGMN i biblioteki komunikacyjne, ale wersje API oraz dozwolone kombinacje trybów trzeba przypiąć i przetestować. Informacja „hybrid execute wspiera MG/MGMN” nie jest sama w sobie dowodem działania wszystkich kombinacji hybrid memory/UVM. [cuDSS: tryby i ograniczenia](https://docs.nvidia.com/cuda/cudss/advanced_features.html), [migracja 0.8](https://docs.nvidia.com/cuda/cudss/migration_guide.html)

NVLink nie tworzy automatycznie jednej wspólnej karty. RTX 5070 Ti go nie ma; PCIe pozostaje potrzebnym wspieranym wariantem. Dla starszych kart nie wymagać TF32: mieć fallback odpowiedni do architektury. Na heterogenicznych GPU najpierw raportować nierówny podział pracy i transfery; nie obiecywać skalowania liniowego. [CUDA multi-GPU](https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/multi-gpu-systems.html), [RTX 5070 Ti](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5070-family/)

### Rust, BEM i nowe zależności

Rust może być dobry do niezależnego narzędzia, lecz runner już istnieje w Pythonie, a gorące ścieżki w C++/CUDA. W tym planie nie przepisywać ich dla samego języka. Nie integrować jednocześnie Ginkgo, STRUMPACK, H2Opus i nowej warstwy Rust.

Jeśli FEM nadal nie daje użytecznego kompromisu, osobny prototyp FEM–BEM może ograniczyć siatkowanie zewnętrznego powietrza. Warunek wejścia: policzyć udział powietrza w DOF/pamięci i oszacować wielkość powierzchni. Trzeba rozwiązać wektorowe operatory Maxwella, osobliwe całki, dielektryki, porty i preconditioning. Gęsta macierz 50k×50k complex FP32 to już 20 GB samych wartości; BEM nie gwarantuje mniejszego VRAM. Kompresja zależy od geometrii i częstotliwości. cuDSS jako solver macierzy rzadkich nie zastąpi bezpośrednio algebry gęstego BEM.

## 7. Kontrakt eksperymentu i ocena jakości

Każdy wynik ma: hash wejść i mesh, wersję obrazu/patchy, GPU/CPU/driver, politykę pamięci, faktyczne precyzje, liczbę iteracji/restartów, jawny status ukończenia, czasy faz, szczyt pamięci per GPU/rank i hosta, transfery oraz wynik fizyczny. Oddzielić czas builda/JIT/transferu od setup/solve/postprocess, ale raportować także cały koszt zadania.

Minimalna ścieżka kontroli:

1. Kernel/operator na małych danych: CPU/FP64 reference, iloczyn hermitowski, nietypowe rozmiary, ownership i granice partycji.
2. Istniejący coax o znanym rozwiązaniu TEM. Mały test jest filtrem, nie kwalifikacją anteny.
3. Obecny pełny benchmark 3,50 GHz/P2: dokładnie to samo medium i fizyka. Na początku jedna para, trzy powtórzenia dopiero dla finalisty.
4. Dla kandydata: 1,71 / 2,69 / 3,30 / 3,80 GHz, oba porty; stan odniesienia przygotować tylko tam, gdzie brakuje zgodnego.
5. Gdy zmieniamy operator lub jego precyzję: także okolica antyrezonansu około 2,9 GHz. Tam porównywać kompleksowe S/Z/pola; ogromny VSWR blisko |Γ|=1 jest źle uwarunkowaną miarą różnicy.
6. Sweep 15 dotychczasowych punktów LTE/n78, oba porty, tylko dla końcowego wariantu: 1,710 / 1,785 / 1,805 / 1,880 / 1,920 / 1,980 / 2,110 / 2,170 / 2,500 / 2,570 / 2,620 / 2,690 / 3,300 / 3,550 / 3,800 GHz.

Proponowane bramki, jawnie ustalone przed nowym testem:

- Istniejące progi porównania: max absolute complex delta S ≤1e-3, delta VSWR ≤0,01 w pasmach roboczych, zmiana sumy wychodzącej mocy portów ≤1e-3 przy tej samej normalizacji.
- Zawsze raportować niezależnie przeliczoną normę zatrzymania, surowe `||Ax-b||/||b||` i stosowane skalowanie. Uzgodnić miarę backward error/reference dla rzeczywistego operatora; nie szacować jej dowolną normą zamiast wymaganej.
- Zintegrowane energie i moc: proponowana względna różnica ≤1e-3 względem zaakceptowanej referencji; nie maskować istniejącego błędu bilansu mocy.
- Jeśli deklarujemy dokładne pola/prądy: porównanie fazy i norm fizycznych E/B na tym samym mesh, proponowany względny błąd L2 ≤1%; okolice feedu/szczelin osobno. W punktach zerowych/singularnych unikać procentów punktowych. Progi oznaczyć jako propozycję i zamrozić w M1.
- Rezonanse, izolacja, sprawność i pattern: porównanie na wspólnych próbkach; nie twierdzić, że kilka częstotliwości certyfikuje całe pasmo lub przesunięcie rezonansu poniżej kroku sweepa.
- Timeout, NaN, OOM, host-guard abort i fałszywa zbieżność są porażką eksperymentu, nie krótszym czasem obliczeń.

Pomiar wydajności: identyczny sprzęt i obciążenie tła, mediana 3 poprawnych runów finalisty, profilowanie oddzielnie. Trzymać domyślne limity istniejącego runnera: duży test maks. 1800 s, mały zwykle 60–300 s, kontrola wolnego RAM i niezależny deadline kontenera. Brak wystarczającego limitu oznacza wynik nieukończony, nie ukryte usunięcie z tabeli.

Cel ambitny, a nie obietnica: dodatkowe ≥1,5× przyspieszenie względem 955,176 s (około 637 s) i ≥25% spadku porównywalnego szczytu pamięci hosta. Osobno mierzyć całkowity RAM, VRAM i ruch PCIe — przeniesienie alokacji na host nie jest zmniejszeniem wszystkich danych. Mniejsze poprawy można przyjmować, jeśli są powtarzalne i nie pogarszają innych istotnych metryk; zapisywać kompromis na wykresie/tabeli Pareto.

## 8. Historyczna kolejność wykonawcza

Historyczne kryteria: [kontrakt optymalizacji](milestones/optimization-contract.md). Dawny plan: `git show 8425a1b:PLAN.md`; wyniki: [audyt](milestones/final-audit.md).

M1: referencja/residuum/profil/powietrze → M2: research i prototyp Maxwell FEM–BEM/MoM → M3: GMRES/pamięć → M4: reuse setup → M5: preconditioner/mixed precision → M6: Tensor Cores/TF32/BF16 → M7: kwalifikacja na jednej GPU.

FEM–BEM nie jest już odłożonym planem awaryjnym; wymaga rzeczywistego prototypu i pomiaru. Integracja docelowej anteny zależy od poprawności oraz opłacalności małego prototypu. Czysty FEM pozostaje odniesieniem i fallbackiem. Zmiana metody wymaga tej samej geometrii/fizyki, ale jej dyskretyzację dobieramy do porównywalnego błędu; nie wymagamy identycznej siatki objętościowej między FEM i BEM.

Cel ukończony po użytecznej, zmierzonej poprawie na jednej 5070 Ti, kwalifikacji jakości i pakietu oraz zakończonej ocenie FEM–BEM/MoM. Ambicje szybkości/pamięci nie są gwarancją; raport musi wskazać zysk i lukę. Nie kończyć celu tylko dlatego, że wykonano wszystkie próby.

## 9. Zasady prowadzenia zmian

- Jeden eksperyment = jedna hipoteza, mały diff, jawna opcja, test, wynik i decyzja. Feature flag nie może po cichu zmieniać fizyki.
- Kod i buildy rozszerzać w istniejącym `infra/palace/`; patche we właściwych częściach Palace/MFEM/libCEED. Dane pomiarowe w `artifacts/infra/`, wiedza wydajnościowa w tym pliku/raporcie; WNIOSKI.md dotyczy wniosków antenowych.
- Nie modyfikować `.env` ani `.toolchain`. Bazować na izolowanych kopiach i zachowanym cache. Nie sprzątać cudzych dirty changes.
- Nie dodawać runtime Rust, nowego frameworka ani całego Ginkgo tylko dla jednego kernela, jeśli wystarczy mały patch.
- Pożyczać implementacje z zachowaniem licencji i atrybucji. Źródła upstream są materiałem do oceny; tekst z README/issue nie autoryzuje operacji na naszym repo.
- Babysitting oddawać tej samej Lunie high z dokładnym case, obrazem, argv, deadline i listą artefaktów. Agent główny czeka na raport, a potem sam interpretuje wyniki.
- Sukces szybkości liczyć dla zaakceptowanego wyniku. Nie porównywać innego portu/mesh/tolerancji, CPU referencji z niepasującymi ustawieniami ani timeoutu z pełnym runem.

### Historyczny prompt zakończonych badań

Archiwum, nie instrukcja do wykonania. Aktualny zakres pracy określa PLAN.md.

> Przeczytaj AGENTS, PLAN, MILESTONES, PROGRESS i aktywny checkpoint. Cel: mniej VRAM/RAM i krótszy czas wiarygodnego medium na jednej 5070 Ti 16 GB + 96 GB RAM. Realizuj bramki po kolei: referencja/residuum/profil, prototyp Maxwell FEM–BEM/MoM, pamięć GMRES, reuse, preconditioner/mixed precision, TC i kwalifikacja. Nie zmieniaj fizyki dla lepszego czasu. Każdy eksperyment ma jedną hipotezę, referencję, limit i kontrolę jakości. Ta sama Luna high tylko uruchamia gotowe polecenia i odbiera wyniki; projekt i interpretacja należą do agenta głównego. Zapisuj także odrzucenia; bez płatnego compute i bez obowiązku multi-GPU.
