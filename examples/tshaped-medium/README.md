# Ye T-Shaped — pełny benchmark medium

Ta sama siatka co w lokalnym badaniu: 1 601 320 tetrahedrów, 11 218 724 DOF, 3,50 GHz, pobudzony P2 i P1 zakończony 50 Ω. Wariant panelu z rzeczywistą trasą zasilania; nie jest deklaracją najlepszego kandydata produkcyjnego.

Order 2, Tol 1e-6, MaxIts 1600, restart 240, PA 1, backend MAGMA. Geometria, materiały i porty są w `config.json` i siatce. `fixture.json` przechowuje sumy kontrolne, a `benchmark-contract.json` zachowuje historyczne pochodzenie (jego pole backend dotyczy oryginalnego przygotowania, przed wyborem MAGMA).

Siatka jest skompresowana zstd i podzielona na części poniżej 100 MB. `python3 tools/dev.py prepare tshaped-medium` z root repo odtwarza `mesh/pcb.msh` i sprawdza SHA256. Rozpakowana siatka jest ignorowana przez Git.

Uruchomienie i ograniczenia: [docs/build.md](../../docs/build.md). Porównuj ten sam port/częstotliwość/mesh. To przykład wydajnościowy; historyczny VSWR około 1,672 przy 3,5 GHz/P2 nie jest zmianą antenowego baseline.

`reference-S.csv` to historyczny wynik P2 przy 3,5 GHz; obraz referencji i hash są w `reference.json`. Nie jest wynikiem nowego buildu.
