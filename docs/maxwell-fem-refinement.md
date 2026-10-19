# M2 — oddzielenie błędu FEM od referencji BEM

EXP54–58, 2026-10-19. **Poprawa w identycznych punktach, brak kwalifikacji
całej objętości i anteny.** M2 ACTIVE. Punkt wyjścia:
[near correction i brak zbieżności](maxwell-near-panels.md).

## Diagnoza zapisanych pól

Obie strony PMCHWT B3/B4 mają kontrolowane nearquadrature. Na degree5
punktach odległych o>.2 od ścian bryły (jednostki modelu, nie mm anteny)
zmiana referencji E/H to0,101/0,048%, ale błąd sprzężonego F2 wynosi1,791/1,539%.
Przy distance<.05 odpowiednio3,506/1,665% i5,032/1,932%. Referencja jest
niestabilna głównie przy powierzchni; również FEM wymaga niezależnej kontroli.
Biny są diagnostyką, nie zastępują pełnej normy ani jej zamrożonych progów.

## EXP54–55 — znana fala w jednorodnym dielektryku

Rozszerzenie istniejącego `--physics nd2 --epsilon-r 2.94`. Domyślnie ND2
nadal epsilon1; transmission nadal2,94. Bez zmiany guarded geometry/basis API,
native MFEM SO i kompilacji. Analityczne E=(exp(i*k*z),0,0), k=sqrt(eps),
mu=k0=1, operator curlcurl−eps*M i interpolowane Dirichlet boundary data.
Helper raportuje curlE/(ik)=H/sqrt(eps); względny błąd fizycznego H jest
identyczny, bo ten sam stały czynnik dzieli licznik i mianownik.

| FEM | Tet / DOF | Projekcja E/H | Rozwiązanie Dirichlet E/H | Czas runnera / RSS |
| --- | ---: | ---: | ---: | ---: |
| F2 | 160 / 1228 | 2,106 / 5,337% | 1,736 / 2,489% | 1,071s / 287MB |
| F3 | 1280 / 8936 | 0,546 / 2,566% | 0,443 / 0,717% | 5,572s / 432MB |

Raw≤5,73e−15, q6/8delta≤1,22e−11, basis/orientation gatePASS.
Tylko Dirichlet F3 przechodzi1%; projekcja jest innym wektorem.
To kontrola rozdzielczości wewnętrznego FEM, nie transmisji przez granicę.
EXP58 bez flagiepsilon odtworzył dokładnie zapisane liczby Dirichlet EXP33
E/H0,150508/0,331747%;5,520s/RSS432MB, epsilon1/k1/raw4,09e−15.

## EXP56–57 — rzeczywiste sprzężenie i porównywalne próbki

Zmieniono wyłącznie FEM2→3, BEM3/materiał/q4/BC-RWG-Schur i fizyka bez zmian.
Solve EXP56:114,960s/RSS1,325GB, raw1,97e−13 i energy/pi1,28e−7PASS.
Nowe centroidy1280 dawały E/H1,499/1,085% vs PMCHWTB3, ale referenceB2→B3
zmieniała się aż7,968/7,643%. Nie porównywać tego bezpośrednio z160centroidamiF2.

`mfem_replay.py` / `--physics fem-replay` używa savedu i identycznych640
stopnia2 punktów/wag zEXP42. Locator wymaga dokładnie jednego elementu
z każdą barycentric coordinate>1e−10; odrzuca face/outside/NaN zamiast
wybierać arbitralną wartość normalnego E. Minimum wEXP57 wyniosło0,17082.
Nie przelicza BEMpotentials ani solve; GlobalND konstruktor nadal tworzy
małe mass/curl forms. Replay0,761s/RSS296MB.

Root porównał z corrected PMCHWTB4 zEXP52 oraz B3 zEXP53:

| Punkty | F2 E/H vs B4 | F3 E/H vs B4 | B3→B4 E/H |
| --- | ---: | ---: | ---: |
| Wszystkie640 | 2,152 / 0,863% | 0,664 / 0,597% | 1,086 / 0,442% |
| Core300, distance>.2 | 1,197 / 0,752% | 0,186 / 0,252% | 0,055 / 0,044% |
| Near340, distance≤.2 | 2,830 / 0,965% | 0,932 / 0,813% | 1,556 / 0,630% |

**To stały zbiór próbek, nie zbieżna norma L2 na F3.** Wagi pochodzą z
F2; nie rozstrzygają całkowania skoków normalnego pola na wewnętrznych
ścianach F3. Cała objętość, reference mesh0,3%, rezonanse i koszt przy zgodnym
błędzie nadal otwarte. Core300 także nie zastępuje pełnego pola.

## Odtworzenie i dalsza praca

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/new-analytic-dielectric --physics nd2 --level 3 --epsilon-r 2.94 --seconds 120
python3 tools/experiments/bempp_oracle.py run artifacts/new-coupled-f3 --physics transmission --level 3 --surface-level 3 --epsilon-r 2.94 --seconds 180
python3 tools/experiments/bempp_oracle.py run artifacts/new-fixed-probes --physics fem-replay --level 3 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --probe-input artifacts/m2-transmission-volume-degree2-20261019 --seconds 120
```

Replay wymaga terminalnych wejść: saved transmission candidate i reference-only
PMCHWT oraz oddzielnego saved volume degree2. Guardy sprawdzają role, fizykę,
source geometry/basis, native ABI i SHA wszystkich danych. Dane montowane read-only;
pozostałe physics odrzucają probe-input, nie wolno nadpisać stopnia próbek.

Dalsze własne F3volume i kontrola kosztu zostały wykonane w
[EXP59–69](maxwell-stream.md): reference/volumeFAIL zachowane. Natywny Bempp
potencjał również matrixfree; wcześniejsza hipoteza o nativepotentialmatrix
była błędna. Nowy wariant scala T/K i zmniejsza temporarybuffers.
M2 ACTIVE, bez promocji anteny; medium bez zmian.

Dowody: `artifacts/m2-near-boundary-error-analysis-20261019.json`,
`artifacts/m2-nd2-eps294-root-analysis-20261019.json`,
`artifacts/m2-fem3-fixed-probes-root-analysis-20261019.json`.
Dane robocze wyłącznie RAM, zwykłe NPZ input/result i JIT code cache osobno.
BrakGPU/chmury/build.
