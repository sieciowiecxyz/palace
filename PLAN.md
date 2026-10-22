# Plan przygotowania PR-ów do Palace

Mode: goal
Active: none

## Cel i granice

Przygotować małe, niezależne zmiany do upstream, sprawdzone lokalnie.
Pierwotny etap był lokalny. Na polecenie użytkownika 2026-10-23 utworzono fork
`sieciowiecxyz/palace` i wysłano tylko branch pilota. PR do upstream nieutworzony;
kontakt/publikacja PR wymagają kolejnego polecenia.
Lokalny pilot ukończony 2026-10-22. Fork i branch opublikowane 2026-10-23.
GitHub potwierdza jeden commit/3pliki; upstream wyprzedził bazę o2commity.
Pakiet i ręczna publikacja: [instrukcja](docs/upstream-prs.md).

## Milestones

- [x] M0 — Pobrać upstream i ustalić aktualną gałąź domyślną (`main`/`master`), SHA oraz możliwe duplikaty zmian. Zachować fork badawczy.
- [x] M1 — Na aktualnym upstream utworzyć lokalny branch pierwszej małej zmiany: skrócenie życia buforów / ograniczenie nakładania pamięci postprocessingu. Przenieść wyłącznie potrzebny patch.
- [x] M2 — Przetestować patch względem czystego upstream: poprawność, regresje i osobno czas/pamięć. Zacząć od krótkiego przypadku; większy tylko gdy potrzebny.
- [x] M3 — Przeczytać zasady contribution i ostatnie review upstream. Dopasować kod oraz lokalny opis PR-a do praktyk projektu.
- [x] M4 — Przygotować lokalny pakiet do przeglądu i instrukcję: jak sprawdzić diff/testy, wypchnąć branch do własnego forka i otworzyć PR. Niczego nie publikować.

## Kolejka kolejnych PR-ów

Po zakończeniu pierwszego: reuse setup/faktoryzacji dla wielu RHS → FP32 storage bazy GMRES z arytmetyką FP64 → mixed precision cuDSS z refinement.
Każdy osobno z aktualnego upstream; kolejność zweryfikować po przeglądzie kodu.
Duplikat, brak mierzalnej korzyści lub zbyt duża zmiana oznacza odłożenie z uzasadnieniem.

## Dokumentacja

[Bramki](MILESTONES.md), [checkpoint](PROGRESS.md), [wyniki zakończonych badań](docs/milestones/final-audit.md), [dawny kontrakt](docs/milestones/optimization-contract.md).
Dawny plan zachowany w Git: `git show 8425a1b:PLAN.md`.
