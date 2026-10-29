# Plan: preprocessing, operatory i I/O

Mode: normal
Active: none

## Cel i zakres

Skrócić czas przygotowania i obsługi wyników Palace na RTX 5070 Ti 16 GB / 96 GB RAM,
bez utraty dokładności medium i dotychczasowych optymalizacji solvera. Nie obiecywać
zysku przed pomiarem. Osobno mierzyć pamięć, czas fazy oraz całe wykonanie.
Plan przygotowany 2026-10-29; goal obliczeniowy pozostaje wstrzymany. Ten etap obejmuje
audyt kodu i dokumentację, bez nowych symulacji, wynajmowania GPU lub wyłączania Straty.

## Milestones

- [ ] M0 — Zamrozić zgodną referencję, źródła/build, testy krótkie i kontrakt pomiaru.
- [ ] M1 — Zintegrować minimalne profilowanie trzech faz, zmierzyć narzut i wybrać rzeczywiste hotspoty.
- [ ] M2 — Trzy równoległe ścieżki: po jednym uzasadnionym prototypie preprocessing / operatory / I/O.
- [ ] M3 — Oddzielnie zakwalifikować każdy patch: poprawność, pamięć, czas; odrzucić nieudane hipotezy.
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
Stare docs/milestones/M1–M4 i optimization-M* dotyczą wcześniejszych kampanii,
nie zaliczają bramek obecnego planu. Nowe M0–M6 mają dowody w ledgerach tej kampanii
oraz PROGRESS.md. Obecne zamrożone runtime/bundle pozostają nietknięte.
Bez push i publikacji; wdrożenie do antenowego workflow dopiero po M5.
