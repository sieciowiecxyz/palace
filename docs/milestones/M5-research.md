# M5 — research maksymalnej wydajności na jednej 5070 Ti

Status: część **ACTIVE M5**, M5.5 ocenione w EXP102, M5.6 nadal otwarte.
Checkpoint i kolejność całego etapu: [M5](M5.md).
Aktualne dowody: [profil mixed coarse](../mixed-coarse-profile.md),
[zasoby gprMax](../fdtd-budget.md). Poniższe kroki zachowują wymagania badania.
Cel: krótszy czas do wiarygodnego wyniku na RTX5070Ti16GB +96GB RAM.
Rust, FieldCraft, GUI i integracja CAD są poza zakresem.

## Najpierw dominujący koszt PC — M5.5

1. Rozdzielić pełny czas na setup, analizę/faktoryzację, apply PC, pozostałe
   operatory, ortogonalizację i pomiary. Profil krótkiego okna nie zastępuje
   pełnego runu. Nie sumować nakładających się aktywności GPU i kopii.
2. Dla kandydata policzyć limit zysku całego zadania, working set i bytes/iteration.
   Obecne około25GB cuDSS przekracza16GB VRAM: badać mniejszy koszt/working set
   PC i ograniczenie ruchu, nie tylko szybsze FLOP w niewielkiej części solve.
3. Ocenić wykonalne warianty iteracyjnego coarse solve/AMS na właściwym operatorze
   pomocniczym oraz kontrolowanej mixed precision. Potwierdzić własności operatora;
   nie stosować solvera wymagającego SPD do ogólnego zespolonego Maxwella.
4. Porównać koszt pojedynczej iteracji ORAZ liczbę iteracji/restartów, konwersje,
   workspace i cały czas. Korekcja/fallback pozostają częścią kosztu.

Zamknięcie: pomiar i decyzja promote/reject, zachowane frozen K i FP64 fallback.
Gates M5.1–M5.4 nadal obowiązują; ten research ich nie zastępuje.

## Czy FDTD/CUDA wygrywa szerokopasmowo? — M5.6

Hipoteza: jeden przebieg czasowy na każdy port może dostarczyć wiele
częstotliwości taniej niż oddzielne solve FEM. To wymaga sprawdzenia kosztu
siatki, kroku czasowego i czasu wygaszania; nie jest jeszcze zmierzonym zyskiem.

1. Wybrać jednego kandydata, najpierw gprMax; sprawdzić aktualne źródła/API,
   wersję/licencję oraz rzeczywistą ścieżkę CUDA. Inny projekt tylko przy
   konkretnej przewadze lub brakującej funkcji, nie równoległe portowanie wielu.
2. Przed implementacją oszacować komórki, pola/współczynniki/PML/DFT, szczyt
   RAM/VRAM, ograniczenie CFL i liczbę kroków do zaniku energii. Cienki feed,
   szczeliny i dielektryk muszą mieć wiarygodną reprezentację. Porównać obsługę
   portów50Ω, płaszczyzny odniesienia, normalizację mocy i konwencję fazy.
3. Jeśli wykonalne: najpierw analityczny mały test, potem reprezentatywny
   radiator/PCB. Jawnie oddzielić build/JIT/meshing od czasu rozwiązania.
   Wykorzystać zapisane referencje, cache i limity, bez nowych zależności bez potrzeby.
4. Porównać koszt CAŁEGO zestawu tych samych częstotliwości i obu portów,
   normalizację i dokładność complex S/VSWR/pól/energii. Deklarować pełne czasy
   zaniku/okna DFT; nie przyspieszać przez zbyt wczesne przerwanie przebiegu.
5. Przy obiecującym wyniku przygotować porównanie z właściwą anteną. FEM medium
   pozostaje referencją. FDTD ma własną jawnie opisaną siatkę i kontrolę jej
   zbieżności; nie przedstawiać innej dyskretyzacji jako przyspieszenia Palace.
   Pola porównywać przez wspólne punkty/objętości fizyczne i ustaloną fazę źródła,
   bez dopasowywania fazy do uzyskania PASS.

Zamknięcie: albo benchmark potwierdzający wykonalność/jakość/koszt, albo konkretna
udokumentowana przeszkoda zasobów/funkcji/fizyki. Sama lista repozytoriów nie
zalicza oceny. Niewykonane testy oznaczać NOT RUN. Nie wymuszać integracji
niekwalifikowanego backendu; pełna promocja nadal wymaga K i końcowych W.

## Reguły czasu i zasobów

Mały test60–180s, reprezentatywny pełny run najwyżej1800s po tanim filtrze.
Zachować obecne limity pamięci/guard; budżet nowego testu zapisać przed startem.
Gorące dane w RAM/VRAM; cache i sporadyczny odczyt SSD dozwolone, niewielkie
zapisy mierzone. Bez swap i intensywnego dyskowego workspace; bez płatnego
compute i zamykania aplikacji. Szczegóły polityki I/O w PLAN.md.
Agent główny przygotowuje hipotezy/argv, ta sama Luna obsługuje uruchomienia.
Brak mierzalnego potencjału kończy hipotezę. M6 może uczciwie wybrać fuzję/batching
zamiast TC, jeśli to lepiej przyspiesza pełne zadanie.

Źródła do weryfikacji przy rozpoczęciu: [gprMax](https://docs.gprmax.com/en/latest/inc_README.html),
[fdtdz](https://github.com/spinsphotonics/fdtdz),
[NGSolve GPU](https://docu.ngsolve.org/latest/i-tutorials/unit-5.5-cuda/poisson_cuda.html).
Wstępny research2026-10-19 nie stanowi benchmarku naszej anteny.
