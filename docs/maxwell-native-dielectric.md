# M2 — native CUDA apply i kontrola dielektryka

2026-10-19, EXP25–29. **Dalszy prototyp; brak promocji solvera anteny.**
Kontynuacja [pierwszego oracle](maxwell-oracle.md). PEC i dielektryk mają
kontrolę zespolonego far-field/Mie i optical theorem. Brak FEM–BEM interface,
kwalifikacji portów, near-field E/B oraz assembly bez pełnej gęstej macierzy.

## Native apply: usunięcie wywołania Python/cuBLAS na każdy blok

`tools/experiments/maxwell_apply.cu` to osobna biblioteka, bez zmian Palace.
Pakuje complex128 z column-major do wierszy w RAM; jeden warp liczy wiersz.
Pierwszy kernel stosuje dokładne bloki bliskie i prawe faktory dalekie;
drugi stosuje lewe faktory. AtomicAdd FP64 zbiera wkłady do y. Osobne rank
workspace i metadane w VRAM, bez UVM i bez zapisu macierzy na dysk.
Wejścia są sprawdzane, ABI HostBlock40B kontrolowane w C++/Python;
CUDA errors przerywają run, zasoby i eventy są zwalniane.

```sh
python3 tools/experiments/bempp_oracle.py build-cuda
python3 tools/experiments/bempp_oracle.py run artifacts/m2-native-new --level 3 --seconds 180 --compression --native-apply --compression-eta 4
```

Jeden TU, nvcc SM120/O3/FP64 bez fast-math, istniejący builder/ccache,
oddzielny `build/m2-oracle/cuda/libmaxwell_apply.so`. Build1,752s, kolejne
wywołanie cachehit bez kompilacji. Manifest wiąże sourceSHA, flagi, obrazy
i binarySHA. Brak przebudowy Palace/MFEM/zależności; builder po pracy stop.
Runtime mount SO read-only. Limity nadal6GiB/no additional swap/180s/oneGPU.

### Porównanie przy tej samej jakości i precyzji

EXP25 eta2 izoluje dispatch; EXP26 zmienia **wyłącznie** geometryczną
dopuszczalność eta2→4, nadal nie nakładające się wsparcia RWG. Leaf64,
Frobenius1e−6 i wszystkie progi jakości niezmienione. Nie jest to TF32/TC.

| Jedna macierz / 1920RWG DOF | EXP25 eta2 | EXP26 eta4 | EXP29 eta4, końcowa integracja |
| --- | --- | --- | --- |
| Cały runner | 40,565s | 40,819s | 40,784s |
| Matrix data / dense58,9824MB | 53,5795MB (−9,16%) | 48,7699MB (−17,31%) | 48,7699MB |
| Native explicit GPU bytes, także metadata/workspace | 54,2851MB | 49,5404MB | 49,5404MB |
| Dense cuBLAS round-trip apply | 0,1220ms | 0,1016ms | 0,1035ms |
| Per-block cuBLAS compressed apply | 5,2371ms | 5,469ms | 5,351ms |
| Native compressed round-trip apply | 0,2114ms | 0,1875ms | 0,2242ms |
| Native GPU event, resident input | 0,1665ms | 0,1606ms | 0,1498ms |
| CPU compressed GMRES | 0,6374s | 0,6149s | 0,5986s |
| GPU operator + CPU SciPy GMRES | 0,07770s | 0,07494s | 0,07777s |

Każdy wariant:170iter, wszystkie gatesPASS, noOOM. Native eta2 jest około25×
szybszy od per-block dispatch, lecz **nadal wolniejszy od dense cuBLAS apply**.
To mała jednorazowa próba, nie stabilny benchmark anteny; wahania czasów
między runami nie są dowodem regresji/progresji algorytmu.
Round-trip obejmuje PCIe/Python/sync, 8powtórzeń po4kontrolnychwektorach.
Event:64powtórzenia, dwa kernele i zerowanie y, bez transferu x/y.
Explicit bytes wykluczają CUDA context/cuBLAS wewnętrzny workspace.

EXP29:852bloki/424compressed, maxaction3,215e−9, raw woryginalnym układzie
3,218e−9, Δsolution4,803e−8, Δfar-field2,681e−11. Far-field policzony teraz
z rozwiązania **GPU-operator/CPU-basis GMRES**, nie z CPU LU. Miecomplex0,5643%,
scatter0,96565%, energy5,65e−12. Progi1% i wcześniejsze action/raw/Δfield bez
zmian. Assembly dense wRAM, retainedoracle i kopie: RSS1,414GB; redukcja danych
operatora nie oznacza oszczędności peakRAM. Nadal brak pełnego GPU GMRES,
portów, FEM coupling i dowodu zysku na antenie.

Artefakty: `artifacts/m2-pec-native-apply-level3-20261019`,
`m2-pec-native-eta4-level3-20261019`, `m2-native-integrated-regression-20261019`.
**Decyzja:** zachować jako sprawny numeryczny probe; nie promować do Palace.
Nie kontynuować strojenia małej kuli zamiast pracować nad interface/assembly.

## Dielektryk: PMCHWT i niezależny Mie

`bempp_dielectric.py`: ka1, εr2,94, μr1, lossless, CPUcomplex128/RWG-SNC.
Według przypiętego Bempp `examples/maxwell/maxwell_dielectric.py`:
`A=[[M,T/rho],[-rho*T,M]]`, rho=sqrt(εr),
`(Aint+Aext)[E×n,H×n]=[Einc×n,Hinc×n]`, farE=−Tpot(H×n)−Mpot(E×n).
Konwencja exp(−iωt)/outgoingh1 jakPEC, bezfitufazy/amplitudy.
Niezależna seria Miego dla dielektryka: kontrola SciPy≤1,076e−15 dla
ka0,1/1/2,5, test transparent εr1, Rayleigh, lossless optical theorem,
passywność dodatniego Imε. Wartości lossless/lossy zgodne z naszą konwencją;
[opis algorytmów Miego](https://miepython.readthedocs.io/en/latest/07_algorithm.html)
jest źródłem wzorów, nie zależnością ani dowodem działania FEM interface.
Ograniczenie wzorca: ka≤3, |mka|≤6, μr1; testBEMlossy NOT RUN.

### Oddzielenie błędu geometrii od operatora

EXP27 standardowa płaska icosphere (wierzchołki na r1):

| Level / dof obu śladów | Czas | Complex field | Scattering | Energy | 1%target |
| --- | --- | --- | --- | --- | --- |
| 2 / 960 | 35,285s | 3,3542% | 6,3081% | 1,242e−7 | FAIL |
| 3 / 3840 | 108,849s | 0,8495% | 1,6154% | 1,748e−9 | FAIL |

Raw≤9,08e−15/noOOM. Level3 matrix235,93MB/RSS1,167GB. Nie przemianowanoFAIL.
Rachunek geometrii: level3 ma Vmesh/Vsphere0,991394 i równoważny promień
0,997123. Mie takiej objętości przewiduje−1,6106%scatter wobec−1,6154%
z symulacji. Dla level2:−6,2728%pred vs−6,3081%observed. To wyjaśnia wiodący
bias, ale samo nie kwalifikuje solvera; audit w
`artifacts/m2-dielectric-geometry-audit-20261019.json`.

EXP28 jawny wariant siatki o zachowanej objętości:
`scale=(4*pi/3 / signed_volume(mesh))^(1/3)` przed assembly. Reguła wynika
wyłącznie z geometrii, nie zależy od częstotliwości, ε ani pola. **Referencja
nadal jest kulą r1**, nie zmieniono żadnego progu. Przybliżenie wielościenne
ma część powierzchni na zewnątrz i część wewnątrz sfery; nie twierdzimy,
że ma identyczną fizyczną powierzchnię ani poprawne lokalne near-field.

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/m2-dielectric-new --physics dielectric --level 2 --seconds 120 --volume-preserving
```

| Level / dof | Vertex radius | Czas | Complex field | Scattering | Energy |
| --- | --- | --- | --- | --- | --- |
| 1 / 240 | 1,046133 | 27,318s | 0,1764% | 0,3067% | 1,142e−5 |
| 2 / 960 | 1,011541 | 35,553s | 0,02228% | 0,03856% | 1,286e−7 |

ObaPASS1%, raw≤5,35e−15/noOOM; zbieżność około8×. Wlevel2 matrix14,746MB,
RSS439,14MB, LU0,03674s. Nie potrzeba kolejnego108s runu, by potwierdzić ten
mały far-fieldtest. To nie jest poprawka geometrii PCB/anteny ani tunings.
Artefakty `artifacts/m2-dielectric-{level2,level3,volume-level1,volume-level2}-20261019`.

## Granica i następny krok

58unitPASS obejmuje Mie/objętość/manifestSO oraz wcześniejsze testy. Root
sprawdził SHA wykonanych źródeł, `.so`, terminalstate i wyniki w
`artifacts/m2-native-dielectric-root-analysis-20261019.json`.
Niewykonywany H-matrix module w CPUdielectric nie jest zależnością jego wyniku.
M2 pozostaje aktywny. Kolejne zadanie to **rzeczywisty mały interface H(curl)
FEM–BEM z poprawną orientacją/normalizacją trace**, porównanie z pełnymFEM i
zewnętrznym polem. Osobnej kontroli wymaga assembly bez pełnego dense oraz pamięci/rang przy rozmiarze anteny. Portów,
E/Bprzyfeedzie, skalowania i produkcyjnego speedupu nadal nie zakwalifikowano.
