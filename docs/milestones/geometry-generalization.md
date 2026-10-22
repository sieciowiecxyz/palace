# M7.5 — zmiana odstępu directora

## Hipoteza i procedura przed symulacją

Sprawdzić, czy zakwalifikowana polityka pamięci zachowuje K również po
istotnej zmianie geometrii. To test solvera, nie strojenie anteny do produkcji.
Director i jego nośnik przesuwamy o+2mm w osi z; długość dystansów/prętów
zmienia się odpowiednio. Główna PCB, feed, reflektor, radom i porty mają
pozostać bez zmian. Osobna referencja FP64 nowej siatki jest obowiązkowa.

Generator `tools/experiments/geometry_variant.py` stosuje kompaktowe, gładkie
przesunięcie z do istniejących węzłów Gmsh2.2/Tet10. Zakres z2/11/14/30mm,
promień wewnętrzny50/zewnętrzny55mm, przesunięcie2mm. Nie jest to jednorodne
skalowanie całej anteny. Topologia/tagi i medium pozostają takie same, nowy
hash wynika ze współrzędnych. Zmiana fizyki wymaga świeżego setupu.

Kolejność: audyt siatki → testy narzędzi/odrzucania starych danych → nowy
pełny FP64/bothports → audyt root → kandydat/ta sama nowa siatka → pełne K.
Jedna para3.500GHz wystarcza do tej kontroli generalizacji; nie zastępuje
W.5 starej geometrii ani nowych median. Bez TF/PROM/seedów/profilera.

- R: FP64basis/coarse, świeże2setup.
- C: directFP32storage/FP64arithmetic, scaledcomplexFP32LU/3fixedFP64IR,
  setupreuse1. Oba RIGHT/K64/Tol1e-6, defer/energy/releases/snapshots.
- Limity lokalne1800s/60GiB/no swap/hostguard; brak płatnego compute,
  wyłączania aplikacji, nowych native buildów lub czyszczenia cache.
- Bramki frozenK: originalraw<=1e-6, coarse<=1e-3, ΔS<=1e-3,
  ΔVSWR<=0.01, power/energy/pola według niezmienionego kwalifikatora.
- Czas obejmuje pełne zadanie i kontrolę pól; osobno cgroup/managed/NVML.
  Bez zysku czasu dopuszczalny jest jawnie opisany zysk pamięci/fallback.

## Przygotowanie i zakres audytu

```sh
OPENBLAS_NUM_THREADS=2 build/m2-oracle/venv/bin/python tools/experiments/geometry_variant.py --output NEW-GEOMETRY --z-window 2 11 14 30 --radial-window 50 55 --shift 2
python3 tools/dev.py prepare tshaped-medium --fixture-dir NEW-GEOMETRY
```

`--fixture-dir` zachowuje wybraną rodzinę przypadku i jej zamrożony profil
medium; sprawdza archive/config/meshSHA oraz ścieżki. Ten sam mechanizm pól
obejmuje również region dielektryka kabla. Zmiany hash/materials/boundaries
unieważniają stare referencje i seedy. Faktory są lokalne dla nowego procesu;
reuse dotyczy wyłącznie dwóch portów tej samej nowej A(f).

Audyt sprawdza wszystkie zakrzywione tetraedry: detJ jest wielomianem
stopnia3, a dodatnie współczynniki Bernsteina dają wystarczające dolne
ograniczenie na całym elemencie. FP64 z marginesem1e-10 względnie; bez
formalnej arytmetyki przedziałowej. Nie wystarcza sam znak objętości narożników.
Wzorzec Tet10 z [dokumentacji Gmsh](https://gmsh.info/doc/texinfo/gmsh.html#Node-ordering),
sprawdzony testem afinicznym, losowym odtworzeniem detJ i kontrolą zgiętego
elementu o poprawnych narożnikach, lecz odwróconym wnętrzu.

Pierwsze dwa przygotowania (radial55/70 oraz50/57) zachowano jako **PREP ONLY**:
audyt Jacobianów przeszedł, lecz obejmowały także radom (max1.993/0.235mm).
Nie uruchamiać tych siatek; zawężony promień55mm ma wykluczyć radom.
To koszt przygotowania wejść, nie wynik RF ani nieudany solver.

## Wynik

Przygotowanie PASS: `artifacts/m7-director-gap-plus2-geometry-20261022`,
meshSHA `c66c6f55c8e28b3efe87bdc4eac373e65d69b71cb016454a2c92c7d4dbfaf8fb`.
147607 z2579954węzłów zmienionych; wszystkie1601320zakrzywionych tetraedrów
spełniają dodatni bound, min3.98823e-6. Absorber/porty37996węzłów bez zmian.
Zmienione solid attrs4/5/6 i PECdirectora10; żadnego radomu7 ani głównejPCB2.
Stare rzeczywiste pola i seed odrzucone z powodu innej mesh/physicsidentity:
`stale-data-check.json`. Jednostkowe kontrole materiału/terminacji też odrzucają.
Generator16.775s; native SHAa6ec732f… bez przebudowy,184Python/8shell PASS.

EXP221: nowa pełna referencja
`artifacts/m7-director-gap-plus2-reference-20261022`, dokładnie3.500GHz,
oba porty. EXP222kandydat będzie wysłany dopiero po audycie tej referencji.
Symulacje **NOT RUN** w chwili zapisu prereg; M7.5 pozostaje otwarty.

### EXP221–222 — wynik wykonania

Oba zadania i **pełne K PASS**, aktualny nativea6ec732f…/medium, bez
przebudowy zależności. Ta sama nowa geometria w R/C, świeża własna referencja.

|Miara|FP64|Fixed3|
|---|---:|---:|
|Całe zadanie, oba porty [s]|764.008|755.874|
|Peak cgroup RAM [GB]|61.139|46.601|
|Peak logicznych managed allocations [GB]|57.398|42.172|
|Peak żywych cuDSS allocations [GB]|25.284|13.481|
|Globalny peak NVML [MiB]|15821|15819|
|Iteracje P1/P2|44/45|44/45|

Jedna para: czas−1.065%, RAM−23.779%; nie mediana ani dowód uniwersalnego
speedupu. Tło GPU2316→2212MiB, hostavailable84.48/84.66GB. Zysk pamięci
utrzymany na zmienionej geometrii, fizycznej redukcji VRAM nie wykazano.
NVML obejmuje pulpit; logiczne alokacje nie są rezydentnym working set.

RawR<=8.042e-7/C<=9.444e-7. C91coarseapplies, count3,
maxcoarseresidual6.8592e-5. SetupR2build/C1build+1reuse. Nowe wartości CSR
`94fab340c2a481af` różne od starych `3139379ae1781ad5`; nowy układ
faktycznie zbudowany/faktoryzowany. Po zmianie geometrii nie przeniesiono LU.

14regionalnychwierszy pól PASS, maxE6.383e-7/B5.265e-8; maxΔS3.508e-8,
ΔVSWR5.557e-8, względnaΔenergii1.019e-7/Δpower6.659e-9. Progi bez zmian.
Receipt: `artifacts/m7-director-gap-plus2-fixed3-qualification-20261022.json`.
Koszty/zakres: `artifacts/m7-director-gap-plus2-cost-scope-20261022.json`.
Trzy przygotowania+oba runy zapisały3.789GB zwykłych wejść/wyników/pól;
brak dyskowej bazy/workspace w solverze. Koszt najmu0USD, energia niemierzona.

Dodatkowa obserwacja fizyki przy3.500GHz: FP64 starej geometrii VSWR
1.577/1.668, nowej1.401/1.485. To efekt zmiany anteny, nie błędu precyzji,
nie pełnopasmowe strojenie i nie nowa baza produkcyjna źródłowego repo.

**M7.5 zaliczony w tym zakresie.** Następnie M7.3 odtwarzalny pakiet oraz
M7.4 audyt całości. Native/defaulty i globalny status numerically_validated
pozostają bez zmian; goal nadal aktywny.
