# M6.6 — szybsze sweepy częstotliwości

Status: **PLANNED**, po M5, w ramach M6; prośba użytkownika2026-10-21.
Cel: krótszy czas całego zestawu3,3/3,4/3,5/3,6/3,7/3,8/3,9GHz na jednej
RTX5070Ti16GB/96GBRAM, oba porty, bez utraty wiarygodności medium.
To rozszerzenie celu, nie zmiana dotychczasowych progów ani zamknięcie M5.

## Kolejność hipotez

1. **Audyt istniejącego Palace**: SweepUniform, SweepAdaptive i RomOperator;
   ustalić co już reużywa siatkę/spaces/K/C/M, co ponawia assembly/setup i jakie
   PROM/interpolation/error controls są rzeczywiście dostępne. Bez duplikowania
   istniejącego silnika. Obecny opt-in M4 współdzieli faktory tylko przy tym samym f.
2. **Continuation/warm start**: poprzednie E jako start następnego f, przy każdej
   częstotliwości nowe RHS/operatory i niezależnie przeliczone rawresidual.
   Każdy port ma własną historię; nie traktować P1 jako tożsamego rozwiązania P2.
3. **Symbolic reuse**: tylko jeśli identyczny wzorzec CSR potwierdzony, a materiały,
   mesh/porty i konfiguracja reordering się nie zmieniły. Faktory numeryczne
   muszą odpowiadać nowym wartościom A(f); brak ślepego reuse LU między f.
4. **Recycling Krylov/subspace**: oszacować liczbę dodatkowych wektorów/VRAM i
   koszt aktualizacji. Sprawdzić actual residual i stagnację; fallback niezależny
   solve, bez zmiany tolerancji. Nie zakładać, że zwykły GMRES to recycling.
5. **Adaptive sweep/PROM**: pełne solve w wybranych f, tańsza ocena pozostałych.
   Co najmniej jeden punkt kontrolny niewykorzystany do budowy modelu. Błąd pola
   i S oraz residuum oryginalnego układu, nie tylko residuum małego modelu.
   Near-resonance/antyrezonans wymaga osobnej kontroli, nie tylko gładkiej krzywej.

## Eksperymenty i bramka

Najpierw kosztorys i mały analityczny coax, np.3punkty, potem siedem punktów.
Budżet i liczba solve ustalone przed runem; istniejące deadline/caps pozostają.
Jeżeli zestaw nie mieści się w jednym limicie, jawne checkpointy/chunki i suma
całego czasu; nie ukrywać kosztu ponownego setupu ani wrzucać working set na dysk.
Droga antena dopiero po tanim filtrze i realnej prognozie zysku.

Kontrola: niezależne pełne medium solve w tych samych punktach i obu portach,
identyczna geometria/materiały/terminacje. Osobno koszt cold-start, warm setup/JIT,
assembly/analysis/factor/solve, wektory recycling/PROM i dodatkowa pamięć.
Ocena obejmuje cały zestaw, nie samo tańsze wywołanie dla jednego f.
FrozenK dla wszystkich S/VSWR/power/raw, pola w ustalonych kontrolach i punktach
nieużytych przez PROM. Fallback odnotowany i doliczony do kosztu.

Zamknięcie M6.6: porównanie promote/reject z dowodami; lista pomysłów nie wystarcza.
Nie obiecywać zysku przed pomiarem. Wariant promowany przechodzi końcowe M7.
