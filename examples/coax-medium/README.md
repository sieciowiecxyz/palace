# Kontrolny coax medium

Przewód PTFE długości 20 mm, dwa porty, 3,3 / 3,55 / 3,8 GHz. Siatka geometry order 2, 828 942 DOF. To mały sprawdzian obliczeń i porównania do TEM; nie zastępuje pełnej anteny.

`fixture.json` wiąże config i archiwum siatki. `python3 tools/dev.py prepare coax-medium` rozpakowuje i sprawdza SHA256; runner robi to automatycznie.

Wynik analityczny: S11/S22 około zera, S21/S12 około `exp(-j*2*pi*f/c*sqrt(2.1)*0.020)`, przy zgodnej orientacji portów. Dane źródłowe geometrii są w `mesh-audit.json`. Historyczny błąd TEM około 1,9e-4; po zmianach solvera należy go sprawdzić ponownie.

`reference-S.csv` i `reference.json` zachowują małą historyczną referencję z zakwalifikowanego obrazu; porównanie do niej jest niezależne od kontroli analitycznego TEM.
