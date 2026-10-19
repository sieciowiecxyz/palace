# M2 — kontrolowana korekcja potencjałów bliskich paneli

EXP44–47, 2026-10-19. **Kontrole operatora i korekcji PASS, pola dielektryka
nadal FAIL 1%.** M2 ACTIVE; żadnej promocji Palace/anteny ani zmiany medium.
Punkt wyjścia: [volume replay EXP42–43](maxwell-transmission.md).

## Metoda i niezależne kontrole

`maxwell_near.py` odtwarza RWG na panelu z rzeczywistego `space.evaluate`,
orientacji i obu wektorów współczynników. J jest afiniczne, div_Γ J stałe;
div wyznaczamy z fizycznego Jacobianu. Dla exp(−iwt), G=exp(ikr)/(4πr):

```text
T[J] = ik ∫ G J − 1/(ik) ∫ grad_x(G) div_Γ(J)
K[J] = ∫ grad_x(G) × J
E = K[t] + T[h]/rho, H = K[h] − rho*T[t], rho=sqrt(eps)
```

Źródło konwencji: pinned Bempp-cl commit
`a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0`,
[`numba_kernels.py`](https://github.com/bempp/bempp-cl/blob/a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0/bempp_cl/core/numba_kernels.py),
`maxwell_efield_potential` i `maxwell_mfield_potential`.
Nie modyfikowano zainstalowanej biblioteki ani jej testów przestrzeni.

1. Na identycznej `triangle_gauss.rule(8)` własne Tt/Kt/Th/Kh zgadzają się
   z natywnym operatorem do1,97e−15 względnie. Kontrola jednego otwartego
   panelu i zamkniętego wielościanu20trójkątów, syntetyczne complex currents.
2. Adaptacja dzieli1→4 jedynie trójkąty bliskie punktowi; bez zmiany samego J.
   Stos ograniczony głębokością12; niewystarczająca głębokość ma jawny licznik.
   Ratio2 vs4 to kryterium odległość/średnica, nie stopień elementu.
3. Niezależna kontrola stałych Jx/Jy, div=0, k=1e−5: normalna składowa grad
   Laplace single-layer = oriented solid angle/(4π). Użyto istniejącej SciPy1.15.3
   `calculate_solid_angles`, a nie drugiego wywołania własnej kwadratury.
   Źródła: [SciPy](https://github.com/scipy/scipy/blob/v1.15.3/scipy/spatial/_spherical_voronoi.py),
   [Van Oosterom–Strackee1983](https://doi.org/10.1109/TBME.1983.325207).
   Bibliografię zweryfikowano w Crossref/PubMed, implementację w lokalnym pinned SciPy.

Static-normal error1,929e−12 mieści się w granicy Helmholtz–Laplace1,989e−12
(≤(1+max kr)k²Area/(8π)); gateabsolute1e−8. To kontrola konkretnej składowej
w granicy statycznej, nie analityczne rozwiązanie całego problemu dielektryka.
Regresje sprawdzają także obrót/przesunięcie, mapowanie pola i powierzchni
podtrójkątów, octant solid angle/orientację/skalę i wyczerpanie głębokości.

## EXP44–45 — mała kontrola i wybór kosztu

| Wariant | Liście na6punktów / regułę | q6/q8 najgorszy punkt/operator | Czas q6 / q8 |
| --- | ---: | ---: | ---: |
| ratio2 | 2550 | 1,97e−11 | 0,196 / 0,210s |
| ratio4 | 10140 | 1,96e−15 | 0,783 / 0,865s |

Bez wyczerpania głębokości; ratio2 wybrano dla dalszej korekcji.
To około4× mniej liści/kosztu małej procedury, nie speedup symulacji anteny.
Pierwszy run EXP44 trwa15,028s/RSS272MB, rozszerzony EXP45 15,781s/RSS279MB.
Regularq8 vs adaptive różni się aż1,627 na tym zbiorze bliskich punktów;
ta różnica sama nie określa prawdziwego błędu. Właśnie dlatego dodano kontrolę
solid angle, a nie uznano zgodności dwóch adaptacyjnych reguł za pełny dowód.

## EXP46–47 — korekcja zachowanych prądów PMCHWT B4

`bempp_near_correction.py` czyta wyniki volume degree5,2240punktów i te same
prądy B4. Odejmujemy regularną całkę q12 wyłącznie paneli bliskich i dodajemy
adaptacyjną całkę. Pozostałe panele pozostają z cache q12. Nie zmieniamy
prądów, współczynników FEM ani fizyki. Nie ma assembly operatorów FEM/BEM,
ich faktoryzacji lub nowego solve.

Na3punktach suma własnych paneli odtwarza cached native E/H q12 do
6,58e−15/4,47e−15. Osobno badamy adaptiveq6/q8 przy selectionradius2 oraz
selectionradius2/4 przy adaptiveq8/ratio2. Każdy gate≤1e−6, zero depth hits.

| Run | Punkty | Czas z runnerem | RSS | Zakres |
| --- | ---: | ---: | ---: | --- |
| EXP46 | 32 | 8,555s | 217MB | tendencyjny:16worst q12/q16 +16rozłożonych |
| EXP47 | 2240 | 117,617s | 217MB | wszystkie punkty zachowanej regułydegree5 |

Full: adaptiveq6/q8 E/H≤8,34e−13, radius2/4≤1,89e−14. Statystyki:
q6/r2:279180liści/25,068s; q8/r2:279180/26,719s;
q8/r4:502040/59,561s, maxdepth4, zeroexhaustion.
Wszystkie punkty mają dodatnie wagi, suma4π/3. Root przeliczył wszystkie
zespolone normy, SHA źródeł/wejść i stany;32wyniki odtwarzają się w pełnym runie.

**Skorygowane oszacowania E/H wynoszą2,888/1,611%: nadal FAIL1%.**
Oldq16 vs corrected różni się o0,0311/0,0316% w całej reguledegree5.
Korekcja opanowała badany mechanizm kwadratury, ale nie usunęła głównej
rozbieżności pól. Nie dowodzi to jeszcze, który składnik dyskretyzacji dominuje.
Coarse-reference B3 i zgodność regułdegree2/5 nadal wymagają kontroli.

Nie porównywać117,6s z czasem pełnego solve: ten run korzystał z zachowanych
potencjałów q12 i wcześniejszego rozwiązania. Nie zmierzono zysku anteny GPU/RAM.
Wszystkie robocze tablice w RAM; zwykłe wyniki NPZ nie są solverowym offloadem.
Zachowano6GiB/4CPU/tmpfs/noaddedSwap, deadline120/180s, bezGPU/cloud/rebuild.

## Odtworzenie i następny krok

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/new-panel-control --physics near-control --level 1 --seconds 120
python3 tools/experiments/bempp_oracle.py run artifacts/new-corrected-volume --physics near-correction --level 2 --near-count 0 --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180
```

Bez `--near-count 0` domyślny celowany subset32, który nie jest pełną normą.
`--near-count` obowiązuje wyłącznie near-correction, reguła objętościowa pochodzi
z zachowanego wejścia. Guardy wiążą role/state/noOOM/materiał/referencelevel,
helpery i MFEM SO, `reference.py`, geometry helper i SHA danych; mount read-only.

Dowody w `artifacts/m2-near-{control,correction,full}-root-analysis-20261019.json`.
EXP44/46 zachowują historyczne SHA sprzed dodania dalszych kontroli/full replay;
aktualne EXP45/47 mają SHA bieżących odpowiednich skryptów i są zweryfikowane.
Najbliższy krok: analogicznie skorygować B3 i sprawdzić degree2/5 bez nowego solve,
potem niezależna zmiana FEM przy zgodnej referencji. Nie powtarzać ślepo B5
lub globalnego q. M2 pozostaje ACTIVE; potrzebne pola/rezonanse/koszt i decyzja.
