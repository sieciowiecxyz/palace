# Archiwum planu PR — zastąpiony 2026-10-29

Treść historyczna; status publikacji wymaga osobnego sprawdzenia.

## Dawny PLAN.md

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
Pakiet i ręczna publikacja: [instrukcja](../upstream-prs.md).

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

[Bramki](../../MILESTONES.md), [checkpoint](../../PROGRESS.md), [wyniki zakończonych badań](../milestones/final-audit.md), [dawny kontrakt](../milestones/optimization-contract.md).
Dawny plan zachowany w Git: `git show 8425a1b:PLAN.md`.


## Dawny MILESTONES.md

# Bramki przygotowania lokalnego PR-a

Postęp wyłącznie w [PLAN](../../PLAN.md). Etapy kolejno; pierwszy PR jest pilotażem.
Bez publikacji na GitHubie. Poniższe kryteria są do wykonania, nie potwierdzają gotowości zmian.

## M0 - Aktualny upstream

- M0.1: pobrano upstream; zapisano domyślną gałąź i SHA, bez resetowania forka badawczego.
- M0.2: sprawdzono, czy kandydat nadal jest potrzebny i nie powiela istniejącej zmiany/PR-a.

## M1 - Jeden niezależny patch

- M1.1: lokalny branch z ustalonego upstream; jedna przyczyna, mały diff i zwykłe mechanizmy Palace, bez zależności od lokalnego adaptera i narzędzi benchmarkowych.
- M1.2: krótki przypadek odtwarza problem; zachowano licencje, styl i dotychczasowe zachowanie poza deklarowaną zmianą.

## M2 - Dowody poprawności i korzyści

- M2.1: adekwatne testy upstream i regresja problemu przechodzą; zakres CPU/CUDA/MPI jawny, niewykonane testy oznaczone NOT RUN.
- M2.2: upstream kontra upstream + ten patch, te same wejścia, ustawienia i warunki. Zapisane polecenia, wyniki oraz ograniczenia; czas i pamięć mierzone oddzielnie. Dawne −23,6% RAM całego profilu nie jest wynikiem tego PR-a.
- M2.3: build przyrostowy z cache; krótki smoke przed droższym pomiarem. Brak zmiany fizyki/medium, progów dokładności i domyślnych precyzji dla uzyskania zysku.

## M3 - Zgodność z praktykami maintainerów

- M3.1: przeczytano aktualne CONTRIBUTING, dokumentację developer/testów i kilka podobnych review; zapisano konkretne źródła oraz wymagania.
- M3.2: lokalny opis po angielsku: problem, rozwiązanie, zakres, testy, wyniki i ograniczenia. Tematy wymagające konsultacji zapisane do decyzji użytkownika; żadnych wysłanych wiadomości.

## M4 - Pakiet do ręcznej publikacji

- M4.1: wskazano branch, bazowe SHA, commity, diff/stat, polecenia testów i plik z opisem PR-a; lokalny przegląd i dokumentacja zakończone.
- M4.2: instrukcja zawiera sprawdzenie zmian, dodanie własnego forka jako origin, push tylko wybranego brancha i utworzenie PR-a do ustalonej gałęzi upstream. Polecenia publikujące pozostają niewykonane.

## Historia

Zakończone badania optymalizacji mają osobne [kryteria](../milestones/optimization-contract.md) i [audyt](../milestones/final-audit.md). Historyczne M0–M7 nie oznaczają zaliczenia powyższych etapów.


## Dawny docs/milestones/M0.md

# PR preparation M0 — PASS (2026-10-22)

- M0.1: `git fetch upstream`; `git ls-remote --symref upstream HEAD` oraz GitHub API potwierdzają `main`, SHA `29ad351f916e47e005a43730513f155eeb634e3e`. Badawczy `codex/local-cuda` zachowany; lokalny branch `pr/driven-release-workspace` / worktree `/home/sieciowiec/dev/cpp/palace-pr-driven-release` oparty dokładnie na tym SHA.
- M0.2: kod `SweepUniform` trzyma KSP przez końcowy postprocessing. Brak znalezionego odpowiednika w przeglądzie otwartych/ostatnich PR (wyszukiwania memory, release, defer, solver lifetime). To zakres wyszukania, nie gwarancja braku równoległej pracy.

Źródła i konsekwencje:

- [#793](https://github.com/awslabs/palace/pull/793), zamknięty bez merge: analogiczny eigenmode lifecycle odrzucony jako duża reorganizacja przy małym zysku. Kandydat driven ma być minimalny i mieć odrębny pomiar, bez kopiowania wyników profilu.
- [#1085](https://github.com/awslabs/palace/pull/1085): otwarty shared Umpire pool; inne rozwiązanie, możliwy wpływ alokatora na metryki.
- [#1058](https://github.com/awslabs/palace/pull/1058): otwarty complex direct solver; przyszły mixed-precision PR wymaga osobnego ponownego sprawdzenia duplikacji.
- `CONTRIBUTING.md` z bazowego SHA: małe skupione zmiany, aktualny main, lokalne testy, konsultacja istotnych funkcji. Na tym etapie tylko odczyt, żadnych publikacji.

Następny etap: wyizolować finalny lifetime KSP w uniform driven, bez flag PALACE_*, adaptera i zmiany numeryki. Historyczne badania: [archiwum](../milestones/optimization-M0.md).

## Dawny docs/milestones/M1.md

# PR preparation M1 — PASS (2026-10-22)

- M1.1: worktree `/home/sieciowiec/dev/cpp/palace-pr-driven-release`, branch `pr/driven-release-workspace`, baza `29ad351f916e47e005a43730513f155eeb634e3e`. Diff obejmuje tylko `drivensolver.cpp`, testy regresji i changelog: 47 dodanych / 4 usunięte linie.
- M1.2: uniform driven zwalnia KSP oraz A/P/A2/K/C/M dopiero po ostatniej częstotliwości ostatniego pobudzenia. Metadata zapisywane przed destrukcją KSP. Bez flag, adaptera, zmiany równań, precyzji lub tolerancji; adaptive frequency/PROM bez zmian. AMR używające uniform sweep pozostaje objęte patchem.
- Reproducer: oryginalna siatka coax upstream, 1 częstotliwość/1 pobudzenie oraz 2 częstotliwości/2 pobudzenia; pola i estymator aktywne. Pierwszy poprawny smoke upstream: 1 solve/9 iteracji, 5,210 s; 4 solves/50 iteracji, 3,711 s. To reprodukcja nakładania workspace, nie dowód zysku pamięci.
- Przyrostowe buildy z cache PASS. Izolowany builder wymagał fmt 12.1.0, C++20, Catch2 v3.8.1 i PRE_TEST discovery; brak tych dostosowań w diff produktu. MFEM 4.9 zachowany zamiast przebudowy całego toolchaina do4.10.

Historia nieudanych prób zachowana w `artifacts/upstream-pr/`: fmt11 powodował błąd kompilacji; odziedziczony GPU backend poprawiono dla CPU. Timeout starego MFEM 4.9/Umpire przy2OMP zdiagnozowany GDB w PrintMeshInfo/host QuickPool. Wszystkie kwalifikowane próby używają1OMP. Nie jest to ogólna diagnoza wszystkich wersji MFEM.

Dalsze dowody: [M2](../milestones/M2.md). Historyczne badania: [archiwum](../milestones/optimization-M1.md).
