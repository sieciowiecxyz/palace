# Optymalizacja preprocessingu, operatorów i I/O

Mode: goal
Status: complete_scoped
Active: none

## Cel i wynik

Zakończono kampanię dla jawnego profilu medium na jednej RTX 5070 Ti16GB/96GBRAM:
Driven, rank1/OMP1, jeden Point na run, Restart1. Nie jest to kwalifikacja wszystkich
funkcji Palace ani projektu anteny do produkcji.

## Milestones

- [x] M0 — Referencja, źródła/native, krótkie testy i kontrola zasobów.
- [x] M1 — Profil faz i wybór istotnych kosztów.
- [x] M2 — Oddzielne prototypy PRE/OP/IO; negatywne hipotezy zachowane.
- [x] M3 — Oddzielna kwalifikacja: PRE i OP po trzy pary; IO cache DEFER.
- [x] M4 — Lokalna integracja tylko OP/PRE i kontrola interakcji.
- [x] M5 — Trzy pary combined,1,71/2,69/3,80GHz, druga geometria, CPU/MPI2,
  invalidation oraz zapis/reload/restart sprawdzone z jawnymi wynikami negatywnymi.
- [x] M6 — Audyt22punktów, manifest profilu, komendy, rollback i lokalny commit.

Mediana pełnego1,92GHz/oba porty:738,280→630,324s (−14,62%);
peak cgroup66,056→57,029GiB (−13,67%). Wszystkie14par RF w progach.
Kompilacja integracji8,43s z cache, bez przebudowy zależności.

Wykryty istniejący błąd nativeRestart2 CSV pozostaje niezakwalifikowany;
rekomendowany wrapper odrzuca Restart!=1 od czasu sprzed tej próby.
Nie wprowadzono IOcache, zmiany medium/precision, nowego solvera ani TF32.

[Wyniki](docs/optimization-stages/results.md),
[audyt i komendy](docs/milestones/stages-final-audit.md),
[szczegółowe wymagania](MILESTONES.md), [checkpoint](PROGRESS.md).
Źródła scalono lokalnie; bez push/PR i płatnego compute.
