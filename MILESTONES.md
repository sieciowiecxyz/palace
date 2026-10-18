# Kryteria lokalnego forka

## M0 - Samodzielny fork i cache
- M0.1: Źródła obecnych rozszerzeń i licencje są w nowym repo; repo antenowe pozostaje zachowane.
- M0.2: Dwa fixtures odtwarzają wejścia z poprawnymi sumami; bounded coax smoke działa z nowej lokalizacji.
- M0.3: Przyrostowy rebuild i ponowny build bez zmian działają; wynik trafia do build/sm120 i ma manifest pochodzenia.
- M0.4: Regresje narzędzi, docs-garden i sprawdzenie diff przechodzą; ograniczenia są jawne.

## M1 - Kwalifikacja dalszej optymalizacji
- M1.1: Przed zmianą numeryki aktywowane są uzgodnione bramki z docs/speedup.md, w tym wyjaśnienie raw residual i kontrola pól.
- M1.2: Przyspieszenie i spadek pamięci są zmierzone na zgodnych wejściach; multi-GPU oraz TC są deklarowane wyłącznie po rzeczywistych testach.
