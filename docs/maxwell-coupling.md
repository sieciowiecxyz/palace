# M2 — rzeczywisty mały interfejs MFEM–Bempp

2026-10-19, EXP30–31. **Wykonanie i kontrola mapowania PASS; próg 1% pól FAIL.**
Prototyp jest izolowany. Palace/medium ND2 niezmienione. M2 i cały goal aktywne.
To następny krok po [PEC/dielectric oracle](maxwell-native-dielectric.md),
nie gotowy solver anteny ani dowód oszczędności jej pamięci/czasu.

## Implementacja i odtworzenie

```sh
python3 tools/experiments/mfem_bridge.py build
python3 tools/experiments/mfem_bridge.py check
python3 tools/experiments/bempp_oracle.py run artifacts/m2-coupling-new --physics coupling --level 3 --seconds 180
```

Nowy katalog wyników. `mfem_bridge.cpp` wywołuje **zainstalowany MFEM v4.9**:
`ND_TetrahedronElement(1)`, `VectorFEMassIntegrator`, `CurlCurlIntegrator`
i rzeczywiste basis/curl. Nie jest to zastąpienie MFEM własnym solverem FEM.
Mały C API przekazuje macierze przez wskaźniki RAM do Pythona, bez dumpów.
`maxwell_fem.py` sprawdza je niezależnymi całkami Whitney i barycentrycznymi.
`bempp_coupling.py` składa i rozwiązuje **sprzężony** układ, nie dwa niezależne
rozwiązania. CPU/dense tylko dla małego filtra; bez CUDA/UVM w tej ścieżce.

Bridge używa publicznych nagłówków i `libmfem.so` z `/opt/view` istniejącego
buildera. Pierwsza próba compile FAIL (`cudss.h`); dodano istniejące
`-I/opt/cudss/include`. Kolejny build2,597s, potem cachehit bez kompilacji.
Brak przebudowy Palace, MFEM i zależności. `.so` w `build/m2-oracle/fem`,
manifest: sourceSHA/binarySHA/obrazy/flags. Runtime mount read-only.
`GetGitStr()` z załadowanego MFEM jest pusty: nie przypisujemy mu hasha
innego checkoutu; wersja4.9 i obrazy są zapisane. MFEM/Bempp licencje BSD-3/MIT,
źródła upstream niezmienione. Kontener6GiB/CPU4/no additional swap/max180s,
working arrays RAM, zwykłe wyniki i build/JIT cache osobno; cleanup po runie.

## Model i równania

Materiał wszędzie εr=μr=1, k=1. Incident E=x̂exp(ikz), H=ŷexp(ikz),
exp(−iωt), outgoing exp(ikr)/r. Dokładnym rozwiązaniem całej przestrzeni jest
ta sama fala płaska, a scattered field ma być zerowe. Geometria interfejsu
jest wtedy dowolna: użyto stałego wypukłego wielościanu z20ścianami,
V=4π/3. Star tetrahedra i uniform8-wayrefinement dzielą go bez przesuwania
wierzchołków na sferę: wszystkie3runy mają identyczną fizyczną granicę.
To **nie** porównanie z Mie gładkiej kuli.

FEMND1: E=sum u_e W_e, krawędzie z globalnym zwrotem według indeksów wierzchołków.
Twisted trace t=E×n w RWG0: `t=R*u`; signed scale ma moduł1/edgeLength.
SNC=n×RWG według rzeczywistego `api/space/maxwell_spaces.py` Bempp.
`G_ij=<SNC_i,RWG_j>`, boundary weak pairing `B=R^T G`.
Sprawdzamy je oddzielną fizyczną kwadraturą v_t·RWG po każdej ścianie.
Nie wolno kopiować współczynników FEM→BEM bez R.

Z Green i z pierwszego wiersza outgoing Calderón:

```text
F = Kcurl - k² Mvolume
    [ F                 -ik RᵀG ] [ u ]   [    0     ]
    [ (G/2 + Kbem)R       Tbem   ] [ h ] = [ t_inc_weak ]

h = H×n, t=E×n
E_scattered = -T_potential h -K_potential t
```

MFEMlocalbasis↔Whitney weryfikowane przez cyrkulacje krawędzi, wartości/curl
w dodatkowych punktach i lokalne macierze na każdym fizycznym tetrahedronie.
R sprawdzane punktowo na obu stronach wspólnych krawędzi. Badany model
wykorzystuje ND1/RWG0 wyłącznie do kontroli interfejsu; antena ma nadal ND2.

Źródła pierwotne i ograniczenia:

- Bempp przypięty `a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0`:
  `api/external/fenics.py::nc1_tangential_trace` stosuje porównanie rotated
  FEMbasis zRWG i jawnie wspiera tylko Nedelecdegree1. Nie jest adapterem MFEMND2.
  `examples/maxwell/maxwell_dielectric.py` ustala konwencję śladów/Calderón.
- [MFEM Maxwell notes](https://mfem.org/maxwell-notes/) i rzeczywiste nagłówki
  z obrazu: covariant H(curl), curl i integratory. Liczniki tego testu nie są
  licznikami reprezentatywnej anteny.
- [Hiptmair–Meury, 22.03.2007](https://api.newton.ac.uk/website/v0/events/preprints/NI07012):
  stabilizowane sprzężenie Maxwell/Robin-CFIE, regularizacja i właściwe przestrzenie.
  Nasz prosty niesymetryczny pojedynczy wiersz **nie implementuje** tej
  stabilizacji; nie zakwalifikowano go przy rezonansach wewnętrznych.
  Nie przenosić wyników ka1 na całe pasmo2–4GHz anteny.

## Wyniki i kontrola niezależna

Comparator: ten sam pełny operator FEM w ograniczonej objętości, z dokładnymi
cyrkulacjami incident E na brzegu i rozwiązanymi wewnętrznymi DOF. To nie jest
referencja FEM na większej domenie powietrza zabsorberem. E/H ważone objętością,
norma exactincident=sqrt(V), także dla różnicy obu rozwiązań.

| Level | Tetra / tri | FEM / BEM DOF | Czas runnera | Coupled E/H L2 | Dirichlet FEM E/H L2 | Δcoupled–FEM E/H |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 20 / 20 | 42 / 30 | 30,793s | 20,45 / 21,73% | 21,36 / 21,92% | 4,133 / 5,206% |
| 2 | 160 / 80 | 254 / 120 | 31,800s | 11,74 / 11,44% | 12,00 / 11,56% | 1,692 / 2,171% |
| 3 | 1280 / 320 | 1748 / 480 | 37,742s | 6,116 / 5,785% | 6,177 / 5,823% | 0,5691 / 0,7571% |

WszystkieexecutionPASS/exit0/noOOM, **wszystkieanalytic_targetFAIL** względem
zamrożonego1%E/H. Raw1,14e−15/8,34e−15/4,74e−14 nie zastępuje kontroli pola.
Zbieżność podobna do niezależnegoFEM wskazuje dominujący błąd dyskretyzacji;
nie oznacza, że błąd coupling można zawsze ograniczyć różnicą doFEM.

Level3 dodatkowo:

- MFEM↔Whitney maxmatrix1,46e−15; pointwisebasis/curl1,11e−16.
- Rpointwise9,14e−16, scale1,11e−15, niezależnyBpair1,34e−15, gate1e−12PASS.
- q4 vsq6: maxzmianaE/H2,58e−10, gate1e−6PASS.
- Drugi, niewymuszony wierszCalderón:0,7126% względem incidentH interpolowanego
  nakrawędziach oraz0,6752% wobec dokładnego słabego analyticRHS. To diagnostyka,
  nie zamiana normy zatrzymania lub dowód stabilności.
- Farmax0,02306→0,006323→0,001622 wsześciukierunkach; wlevel3 dodatkowe16×24
  kierunki nie zwiększyły maximum. |F|gate0,01PASS dopierowlevel2/3.
- Level3σscat=7,479e−6, σext(opticaltheorem)=9,450e−6. Wtransparentcase oba
  exact0; |σext−σscat|/π=6,275e−7, gate1e−3PASS. To normalizacja do incident
  cross-section, nie względny błąd względem zerowego exactscattering.
- Coupled matrix79,424MB, RSS827,06MB, LU0,3011s. Nie zmierzono oszczędności
  peakRAM/czasu anteny, setup/import/JIT dominują wmałym przykładzie.

Artefakty `artifacts/m2-mfem-bem-coupling-level{1,2,3}-20261019`.
Rootsprawdził aktywne source/binarySHA i terminalstate wlevel3/root-analysis.json.
62unittestPASS: meshvolume/orientacja/refinement, Whitneycyrkulacje/gradient/
mass/curlscaling/stałepole/kwadratury, nowy manifest bridge i wcześniejsze testy.

## Następne konkretne prace — bez zamykania M2

1. MFEM **ND2** z globalnym DOF/orientation (wtym face DOF transformations).
   Zastąpienie signedpermutationND1 prostą zmianą liczby DOF jest błędne.
2. TraceND2 ma2DOF/edge+2DOF/face, RWG0 tylko1/edge. Potrzebny osobno
   kwalifikowany mortar/L2projection na odpowiednią powierzchnię lub zgodne
   BEMwyższegorzędu. Sprawdzić pole, adjointweakpairing, błąd projekcji i stabilność;
   nie utrzymywać deklaracji dokładnego punktowego R dla niezgodnych przestrzeni.
   Najpierw mały test rank/condition GramRWG-SNC oraz dualRWG-RBC, bez dużego
   FEMsolve. Gprimal jest skew, nie zakładać SPD/odwracalności. Kandydat na
   zgodny mortar: t wRWG, h wBC, testRBC=n×BC; wtedy GdualR=−B^T i
   B=−R^TGdual^T z fizycznej całki FEMv·BC. To **hipoteza do sprawdzenia**
   punktowo/kwadraturą, nie gotowy adapter. ŹródłaBC/RBC są już wprzypiętymBempp;
   sprawdzić ich barycentric transforms i kosztassembly zanim zwiększymyDOF.
3. Podnieść dokładność tegoprzypadku do1%E/H, potem dielectricFEMtransmission
   i kontrola far-field/energii względem niezależnego oracle.
4. Przy wzroście DOF zachować sparseFEM; rozważyć dokładne Schur/staticcondensation
   z kontrolą względem małego coupled dense, zamiast alokować wielką denseFEM.
   Następnie assemblyBEM bezfulldense i koszt dla anteny/porównywalnegoFEM.
5. M2.4 nadal otwarte: stabilizacja/porty/metale/ND2 i reprezentatywny koszt
   nie są zakwalifikowane. Nie przechodzić doM3 ani promować prototypu.
