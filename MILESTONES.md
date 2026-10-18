# Kryteria akceptacji optymalizacji Palace

Postęp jest w [PLAN](PLAN.md), dowody i checkpoint w [PROGRESS](PROGRESS.md). Ten plik definiuje bramki; nie zmieniać progów po zobaczeniu wyniku, aby zaliczyć eksperyment. M1 zamraża proponowane niżej tolerancje i ich sposób pomiaru przed nową optymalizacją.

## Wspólny kontrakt K

- **K.1 — Tożsamość:** rewizja/diff źródeł, image/build hash, wejścia/mesh, konfiguracja medium, port/frequency, GPU/CPU/driver i obciążenie tła. Osobno storage, arithmetic, accumulation i residual precision; policy UVM/hybrid, solver i restart.
- **K.2 — Koszt:** setup/solve/postprocess oraz czas całego zadania; build/JIT/transfer osobno. Iteracje, restarty, peak RAM, VRAM per rank/device, workspace, transfery i status ukończenia. Nie sumować nakładających się timerów ani utożsamiać UVM residency z rozmiarem alokacji.
- **K.3 — Dokładność:** niezależnie przeliczone residuum, raw ||Ax−b||/||b||, norma zatrzymania i skalowanie; kryterium błędu niezależne od preconditionera zamrożone w M1. Małe ΔS nie zastępuje kontroli rozwiązania/pól.
- **K.4 — Progi RF:** proponowane max |Δcomplex S| ≤1e−3, |ΔVSWR| ≤0,01 w pasmach i bezwzględna zmiana sumy znormalizowanych mocy portów ≤1e−3. Energia/moc: względna różnica ≤1e−3; pola E/B: błąd względny L2 ≤1%, faza i okolice feedu/szczelin oceniane osobno. W M1 ustalić normy, normalizację i obsługę zer; nie maskować błędu bilansu referencji.
- **K.5 — Uczciwy wynik:** timeout/NaN/OOM/host guard/fałszywa zbieżność = FAIL; brak uruchomienia = NOT RUN. Nie porównywać nieukończonego runu do ukończonego. Każdy PASS ma wskazane artefakty i zakres; build nie dowodzi poprawności numerycznej.
- **K.6 — Limity:** mały test zwykle 60–300 s, pełny maks. 1800 s, niezależny deadline i kontrola RAM. Limity/adaptacje zapisać przed uruchomieniem. Płatny compute wyłącznie w zakresie aktualnej autoryzacji i limitu kosztu; ten plan go nie przyznaje.

## Drabina walidacji W

1. **W.1:** mały kernel/operator vs CPU/FP64, zespolony iloczyn hermitowski, nietypowe rozmiary, partycje/ownership oraz test wykrywający konkretny błąd.
2. **W.2:** examples/coax-medium, trzy częstotliwości i oba porty, odniesienie TEM i complex S.
3. **W.3:** examples/tshaped-medium, 3,50 GHz/P2, identyczny mesh i fizyka, jedna para referencja/kandydat. To benchmark solvera, nie najlepsza antena produkcyjna.
4. **W.4:** dla obiecującego kandydata 1,71 / 2,69 / 3,30 / 3,80 GHz, oba porty; odniesienie z tej samej geometrii. Przy zmianie operatora/precyzji także okolice 2,9 GHz: S/Z/pola zamiast źle uwarunkowanego VSWR.
5. **W.5:** finalista, oba porty: 1,710 / 1,785 / 1,805 / 1,880 / 1,920 / 1,980 / 2,110 / 2,170 / 2,500 / 2,570 / 2,620 / 2,690 / 3,300 / 3,550 / 3,800 GHz. Zachować mesh medium; wygenerować i zahashować brakujące wejścia. To punkty kwalifikacji, nie dowód ciągłego pasma.

W.4/W.5 wymagają przygotowania osobnych konfiguracji; obecny fixture anteny obejmuje tylko W.3. Zmiana samych częstotliwości/portów musi zachować fizyczne terminacje. Trzy powtórzenia bez profilera tylko dla finalisty; mediana, rozrzut i kontrola tła. Profile diagnostyczne raportować osobno.

Dla zmiany metody FEM → FEM–BEM/MoM zachować geometrię, materiały, porty i porównywalny błąd; dyskretyzacje mogą się różnić i mają osobne hashe. Wymóg identycznego mesh dotyczy zmian precyzji/implementacji w tej samej metodzie.

## M0 - Wiedza, fork i cache

- M0.1: zachowana historia/licencje i rzeczywiste patche; samodzielne przykłady z hashami.
- M0.2: build przyrostowy, cache i eksport z manifestem działają; bounded coax smoke i kontrole narzędzi mają dowody.
- M0.3: granice migracji i historycznych wyników zapisane w docs/migration.md oraz docs/local-optimization-results.md. M0 nie kwalifikuje pełnej anteny na nowym buildzie.

## M1 - Referencja, poprawność i profil

Wymaga M0. Blokuje wszystkie dalsze optymalizacje.

- M1.1: zachowana odtwarzalna referencja na obecnym forku, hash i medium zgodne z benchmarkiem; historyczna konfiguracja odróżniona od najlepszego projektu anteny.
- M1.2: udokumentowana przyczyna lub diagnostycznie rozstrzygnięty błąd historycznych raw residual 0,125/0,808. Kontrola Ax−b/scaling/preconditioning potwierdzona niezależnie; nie wystarcza zmiana etykiety normy.
- M1.3: zamrożony kontrakt K.3/K.4, zaakceptowane pola/energie i miara niezależna od preconditionera. Nierozstrzygnięta referencja oznacza BLOCKED, nie zgodę na obniżanie precyzji.
- M1.4: audyt powietrza/interfejsu i tabela czasu faz oraz pamięci V/Z/operator/faktory/workspace/kopie, krótki wiarygodny profil oraz pełny run bez profilera. Utracone zdarzenia profilera i błąd pomiaru opisane.
- M1.5: wybrana hipoteza FEM–BEM/MoM do M2 i kierunek optymalizacji pamięci FEM na podstawie profilu; oba mają przewidywany efekt i warunek odrzucenia.

## M2 - FEM–BEM/MoM dla otwartej anteny

Wymaga M1. Obowiązkowy research i prototyp, integracja zależy od zmierzonych korzyści.

- M2.1: porównano istniejące implementacje Maxwell/FEM–BEM/MoM i akcelerację FMM/H²: CUDA/OpenCL, rzeczywiste GPU matvec/solve, licencja, ślady H(curl), konwencja fazy, porty, dielektryk i cienkie przewodniki. Źródła/rewizje i koszty integracji zapisane.
- M2.2: rzeczywisty mały prototyp elektromagnetyczny przechodzi odniesienie analityczne kuli PEC oraz kontrolę dielektryka i interfejsu FEM–BEM. Kontrola pól, promieniowania, pasywności/energii i zbieżności; benchmark skalarny to wyłącznie smoke.
- M2.3: dla porównywalnego błędu policzono pamięć (w tym gęste bloki, kompresję i workspace), setup+solve i koszt rosnącego rozmiaru. Redukcja liczby niewiadomych sama nie dowodzi oszczędności; badanie lokalne, bez chmury.
- M2.4: decyzja integracja/odrzucenie z dowodami. Obiecujący prototyp jest izolowany za operatorem/flagą, a promocja dla anteny wymaga K i zgodnego odniesienia fizycznego. Zachować FEM jako fallback; dokumentować nieobsługiwane porty/metale zamiast upraszczać je po cichu.

## M3 - GMRES i pamięć

Wymaga M2.

- M3.1: bezpośrednie operacje FP32 storage/FP64 accumulation sprawdzone wg W.1; MGS, ortogonalność i reliable stopping zachowane. Nie ogłaszać obsługi FGMRES bez osobnej implementacji/kwalifikacji.
- M3.2: osobne wyniki usunięcia rozpakowania, polityki migracji/porcjowania i ewentualnego restartu. Zmierzone bytes/iteration, peak i całkowity solve, także stagnacja/restarty.
- M3.3: W.2/W.3 oraz kontrakt K przechodzą dla promowanego wariantu; wariant ma flagę/fallback. Przy braku zysku udokumentowane odrzucenie i zachowana referencja.

## M4 - Reuse setup

Wymaga M3.

- M4.1: wykazano kiedy A/P i terminacje są identyczne dla portów; zmierzona liczba setup/faktoryzacji przed/po.
- M4.2: oba porty tej samej częstotliwości spełniają K, poprawne wyjścia/wznowienia; krótszy koszt kompletnego zadania albo udokumentowane odrzucenie.
- M4.3: symbolic reuse/warm start ocenione oddzielnie, jeśli uzasadnione pomiarem. Numeryczne faktory nie są bez dowodu przenoszone między różnymi A(f).

## M5 - Preconditioner/cuDSS

Wymaga M4.

- M5.1: przypięta macierz zgodności wersji/trybów; hybrid memory, hybrid execute i UVM rozróżnione, minimalny oraz rzeczywisty budżet zmierzone.
- M5.2: co najmniej jeden uzasadniony prototyp lub wykazana niezgodność w źródłach/API; AMS na właściwym operatorze i rzeczywiste wykonanie GPU sprawdzone, jeśli próba wykonalna.
- M5.3: powrót do FP32 faktorów wymaga nowego mechanizmu scaling/korekcji/fallback, nie powtórki odrzuconego runu. Zmienny preconditioner wymaga zgodnego solvera i uwzględnienia dodatkowej pamięci.
- M5.4: W.2/W.3/K, koszt setup + wszystkie iteracje i pamięć kwalifikują promotowany wariant; cuDSS FP64 pozostaje dostępnym fallbackiem. Brak poprawy ma raport odrzucenia.

## M6 - Tensor Cores

Wymaga M5.

- M6.1: profil wskazuje kernel i rzeczywiste wymiary; oszacowany limit zysku całego runu. Jeżeli brak sensownego kandydata, wynik analizy i odrzucenie są jawne.
- M6.2: dla wykonalnego kandydata prototyp FP32/TF32 vs FP64 obejmuje packing, konwersje, scatter, transfer i workspace; backend biblioteczny oceniony przed własnym CUTLASS.
- M6.3: deklaracja TC wymaga instrukcji/liczników potwierdzających użycie. TF32 nie jest przedstawiane jako format zmniejszający storage FP32; sprzęt bez TC/TF32 ma fallback.
- M6.4: promocja wyłącznie po K i W.1–W.3 oraz zysku całego runu z uwzględnieniem iteracji. Negatywny wynik zamyka hipotezę, nie uzasadnia wymuszania TF32/BF16.

## M7 - Finalista na jednej 5070 Ti do używania

Wymaga M6.

- M7.1: finalista przechodzi W.2–W.5/K na zintegrowanym buildzie; wariant odniesienia zachowany, progi nie zostały poluzowane po wyniku.
- M7.2: trzy poprawne pomiary finalisty/referencji na tym samym sprzęcie, mediana/rozrzut, pamięć i jakość. Tabela Pareto uwzględnia czasy/koszt/VRAM/RAM; raport podaje osiągnięty zysk i lukę do ambicji ≥1,5×/≥25%, osobno VRAM/RAM i rozmiar danych.
- M7.3: pakiet z manifestem i przypiętymi zależnościami odtwarza przykład; konfiguracja precision/memory/GPU jawna, niewspierane kombinacje odrzucane, cleanup i deadline sprawdzone.
- M7.4: regresje adekwatne do zmian, docs-garden i przegląd końcowy; znane ograniczenia, źródła i wybrane ustawienia zapisane. Goal nie jest osiągnięty wyłącznie dlatego, że zakończono eksperymenty; musi istnieć zmierzona użyteczna poprawa na jednej RTX 5070 Ti oraz zakończona ocena prototypu FEM–BEM/MoM. Wynik TC może być uczciwie negatywny.
