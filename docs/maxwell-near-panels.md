# M2 — kontrolowana korekcja potencjałów bliskich paneli

EXP44–53, 2026-10-19. **Kontrole operatora i korekcji PASS, pola dielektryka
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
Późniejsze kontrole obu stron i reguł opisano poniżej; zbieżność nadal niezaliczona.

Nie porównywać117,6s z czasem pełnego solve: ten run korzystał z zachowanych
potencjałów q12 i wcześniejszego rozwiązania. Nie zmierzono zysku anteny GPU/RAM.
Wszystkie robocze tablice w RAM; zwykłe wyniki NPZ nie są solverowym offloadem.
Zachowano6GiB/4CPU/tmpfs/noaddedSwap, deadline120/180s, bezGPU/cloud/rebuild.

## EXP48–53 — coarse reference i cache JIT

`--near-side fine|coarse` wybiera B4 lub B3 z tych samych zachowanych prądów.
Coarse ma baselineq12; nie ma cachedq16, więc `old_q16_vs_corrected=null`.
`--near-backend numpy|numba` jest opcjonalny; default pozostaje NumPy.
`maxwell_near_jit.py` używa istniejącej Numba0.61.2, `njit(cache=True)`,
FP64/complex128 bez fastmath. Dane robocze RAM, cache kodu `/jit-cache`.
Nie przebudowywano Palace ani zależności.

EXP50 rzeczywiście skompilował/załadował kernel w1,337s, posiada podpis
nopython. Native operator≤1,92e−15, NumPy/JIT regular≤4,11e−16,
adaptive≤1,05e−15; niezależny static-normal≤1,929e−12. Rozgrzane q8
ratio2:0,0103s vs NumPy0,2093s; ratio4:0,0390s vs0,8492s.
To około20× dla małej całki CPU, nie symulacji anteny.

EXP49 pełny coarse NumPy przekroczył180s: ostatnio1950/2240 punktów
w etapieq8/r4, bezOOM. Brak pełnego wyniku jakościowego. EXP51 zmienił
backend po kontroliEXP50; ukończył wszystkie2240punkty w18,089s/RSS217MB.
Pełne fazy q6/r2 i q8/r2:2,151/3,183s vs44,564/48,028s NumPy.
Nie podajemy ilorazu czasów całych runów, bo EXP49 nie ukończył zadania.
32punktyEXP48 odtworzone wEXP51 do3e−16.

| Reguła objętości | Punkty | E/H względem B4 po korekcji | B3→B4 E/H po korekcji | Czas B4 / B3 |
| --- | ---: | ---: | ---: | ---: |
| degree2 | 640 | 2,152 / 0,863% | 1,086 / 0,442% | 7,981 / 9,165s |
| degree5 | 2240 | 2,888 / 1,611% | 1,647 / 0,781% | 117,617 / 18,089s |

B4degree5 to historyczny NumPyEXP47; pozostałe czasy używają NumBa,
nie są porównaniem skalowania liczby punktów na jednym backendzie.
Dla nowych pełnych runów: native≤9,82e−15, adaptive/cutoff≤1,44e−12,
zero depth hits, RSS≤217MB. Wszystkie punkty i dodatnie wagi zgodne
z zachowaną regułą. Obie strony mają kontrolowane nearquadrature.

**Nadal FAIL:** pole1%, zmiana referencji0,3% i zgodność reguł objętościowych
1e−6. Zmiana oszacowania błędu E/H degree2→5 wynosi względnie25,5/46,4%.
To wyklucza uznanie dotychczasowego błędu pola za zbieżną normę całej objętości.
Nie rozstrzyga samodzielnie błędu FEM/coupling; przed nową kwalifikacją potrzeba
kontrolowanej referencji i całkowania objętości. Nie obniżać progów.

## Odtworzenie i następny krok

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/new-panel-control --physics near-control --level 1 --near-backend numba --seconds 120
python3 tools/experiments/bempp_oracle.py run artifacts/new-corrected-volume --physics near-correction --level 2 --near-count 0 --near-side coarse --near-backend numba --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180
```

Bez `--near-count 0` domyślny celowany subset32, który nie jest pełną normą.
`--near-count/side` obowiązują wyłącznie near-correction, backend wyłącznie
near-control/correction. Reguła objętościowa pochodzi z zachowanego wejścia.
Guardy wiążą role/state/noOOM/materiał/referencelevel, helpery i MFEM SO,
`reference.py`, geometry helper i SHA danych; mount read-only.

Dowody: historyczne `artifacts/m2-near-{control,correction,full}-root-analysis-20261019.json`
oraz nowe `artifacts/m2-near-{numba,coarse-full,volume-degree}-root-analysis-20261019.json`.
EXP44–49 zachowują historyczne SHA; aktualne helpery/sourceSHA zapisano
w manifestach EXP50–53. Nie przedstawiać historycznego SHA jako bieżącego kodu.
Następny krok: zaprojektować zbieżne oszacowanie błędu objętości i referencji
bez ślepego B5/globalq; potem niezależna zmiana FEM, rezonanse i koszt.
M2 pozostaje ACTIVE; nie ma pomiaru zysku anteny RAM/VRAM/czas ani promocji.
