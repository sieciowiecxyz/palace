# Plan: preprocessing, operatory i I/O

Mode: goal
Active: M4

## Cel i zakres

Skrócić czas przygotowania i obsługi wyników Palace na RTX 5070 Ti 16 GB / 96 GB RAM,
bez utraty dokładności medium i dotychczasowych optymalizacji solvera. Nie obiecywać
zysku przed pomiarem. Osobno mierzyć pamięć, czas fazy oraz całe wykonanie.
Wykonanie uruchomione na polecenie użytkownika 2026-10-29. Trzej wykonawcy:
GPT-6.1 Sol high, każdy na swoim branchu; koordynator zbiera i weryfikuje wyniki.
M0 i M1 zamknięte w zakresie diagnostyki/profilowania; M2 zamknięte zakresowo; M3 zamknięte zakresowo; aktywny M4: integracja zakwalifikowanych zmian. Użytkownik zgodził się na zatrzymanie
Straty na czas pomiarów; localai-nvfp4.service inactive/dead, MainPID0. Bez cloud i publikacji.

## Milestones

- [x] M0 — Zamrozić zgodną referencję, źródła/build, testy krótkie i kontrakt pomiaru.
- [x] M1 — Zintegrować minimalne profilowanie trzech faz, zmierzyć narzut i wybrać rzeczywiste hotspoty.
- [x] M2 — Trzy równoległe ścieżki: po jednym uzasadnionym prototypie preprocessing / operatory / I/O.
- [x] M3 — Oddzielnie zakwalifikować każdy patch: poprawność, pamięć, czas; odrzucić nieudane hipotezy.
- [ ] M4 — Scalić wyłącznie zakwalifikowane zmiany lokalnie i sprawdzić interakcje.
- [ ] M5 — Potwierdzić zysk całego medium, sweepu i drugiej geometrii; bez zmiany dokładności.
- [ ] M6 — Zamknąć rejestry, wskazać build rekomendowany, rollback i ograniczenia.

## Organizacja

Trzech wykonawców pracuje w osobnych worktree, na wspólnej przypiętej bazie.
M2 jest etapem równoległym; M3 wymaga zakończenia oceny wszystkich ścieżek
(PASS lub uzasadnione REJECTED/DEFERRED). M4 dopiero po M3. Agent nie przeskakuje bramki.
Kod/research równolegle; ciężkie kompilacje i pomiary sprzętowe kolejno.
Wspólną instrumentację, runner, manifesty, plan i integrację posiada koordynator.
Każdy agent aktualizuje swój ledger przed i po próbie, także przy FAIL/timeout.

Szczegóły: [kontrakt](MILESTONES.md), [workflow i szablon wpisu](docs/optimization-stages/workflow.md),
[preprocessing](docs/optimization-stages/preprocessing.md), [operatory](docs/optimization-stages/operators.md),
[I/O](docs/optimization-stages/io.md), [checkpoint](PROGRESS.md).
Najpierw operator construction, potem preprocessing; I/O ma mały udział, więc zaczyna od taniego replay.
Nie należy rezygnować z niezależnego, taniego audytu I/O z powodu niższego priorytetu.

## Historia

[Poprzedni plan PR i jego M0](docs/optimization-stages/previous-pr-plan.md) zachowany.
Poprzedni checkpoint PR M4 zachowano w
[archiwum](docs/optimization-stages/previous-pr-checkpoint-M4.md), a pliki optimization-M*
dotyczą wcześniejszych kampanii; obecne docs/milestones/M2–M4 opisują tę kampanię.
poprzednie checkpointy M1 i M2 zachowano w archiwum. Te dokumenty
nie zaliczają bramek obecnego planu. Nowe M0–M6 mają dowody w ledgerach tej kampanii
oraz PROGRESS.md. Obecne zamrożone runtime/bundle pozostają nietknięte.
Bez push i publikacji; wdrożenie do antenowego workflow dopiero po M5.
