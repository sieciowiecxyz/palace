# M2 — fused T/K apply i własna kwadratura FEM3

EXP59–69, 2026-10-19. Przyspieszone narzędzie CPU do kontroli referencji,
**bez zysku zmierzonego dla solvera anteny**. Pole E, zbieżność referencji
i reguły objętości nadal FAIL. M2 ACTIVE; medium/defaulty Palace bez zmian.

## Metoda i źródłowe ograniczenie twierdzeń

`maxwell_stream.py` łączy Tt/Kt/Th/Kh w jednym przejściu przez panele,
używając niezmienionych `maxwell_near_jit.py` FP64/complex128/no fastmath.
Kolejność paneli stała dla punktu; równoległe punkty pod dotychczasowym limitem
NumBa2threads. Bliskie panele: adaptiveDuffyq8/ratio2; far: triangleGaussq12;
selectionradius4. `near6`, `radius2`, `far16` zmieniają jeden parametr.

**Natywna NumBa Bempp także nie tworzy pełnej macierzy punkt×DOF.** Sprawdzono
pinned [`numba_assemblers.py`](https://github.com/bempp/bempp-cl/blob/a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0/bempp_cl/core/numba_assemblers.py)
i [`numba_kernels.py`](https://github.com/bempp/bempp-cl/blob/a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0/bempp_cl/core/numba_kernels.py):
bezpośrednio stosują potencjał do prądów. Mają jednak bufory global_points/tmp/diff
wielkości panel×quad i osobne aplikacje T/K dla dwóch prądów. Nowy wariant
scala te operacje i trzyma mniejsze bufory perpanel. Nie ogłaszać usunięcia
nieistniejącej natywnej macierzy ani peakmemorydelta bez pomiaru.

## EXP59/68–69 — zgodność i porównywalny koszt

32identyczne saveddegree2points, PMCHWTB4currents, q12+adaptiveq8/r4.
Weryfikacja rzeczywistego native q12 względem cache daje E/H0/0;
fused regular/incremental mają błąd≤8,88e−15. Nopython i zeroexhaustion PASS.
W testach jednostkowych identitynjit sprawdza tylko matematykę pętli, nie LLVM.

EXP69, po warmup, trzy native queries2,8344/2,8550/2,8697s i fused
0,05931/0,05892/0,05861s. Te same prądy, punkty i kontrolowana dokładność:

| Faza | Native q12 + incremental correction | Fused |
| --- | ---: | ---: |
| Przygotowanie fizycznych paneli, potrzebne obu | 1,778s | 1,778s |
| Query, mediana native plus czas korekcji | 2,931s | 0,0589s |
| Suma z przygotowaniem paneli | 4,709s | 1,837s |

Około2,56× w tej małej procedurze z przygotowaniem; około49,7× dla query po
amortyzacji paneli. Nie przenosić tych ilorazów na pełną antenę, cuda/UVM ani VRAM.
Wyłączone z tabeli: startup/framework oraz native warmup/load9,034s i fusedJIT
load0,0156s. RSS całego wspólnego controlrun292MB; nie osobny peak każdej metody.

## EXP60–67 — rzeczywista reguła na siatce F3

SavedF3u zEXP56 i savedPMCHWTB3/B4 zEXP41. Nie ma nowego solve/BEMmatrixassembly.
GlobalND konstruktor nadal tworzy małe mass/curl forms, potem obliczamy pole
na każdej komórce z jej własną dodatnią kwadraturą. Biaspilot32points poprzedził
fullrun i wyznaczył koszt. `--near-count 0` jawnie wybiera wszystkie punkty.

| Reguła F3 | Punkty | FineB4 E/H | B3→B4 E/H | Czas case fine/coarse | RSS fine/coarse |
| --- | ---: | ---: | ---: | ---: | ---: |
| degree2 | 5120 | 1,463 / 0,865% | 1,555 / 0,752% | 14,417 / 10,107s | 431 / 430MB |
| degree5 | 17920 | 1,683 / 0,972% | 1,725 / 0,876% | 37,210 / 22,216s | 442 / 440MB |

Fine apply9,248/31,985s, coarse4,928/17,035s, bez depthhits. Wszystkie wagi
pozytywne, sumują się4pi/3. Własna norma² H_FEM dla degree2/5 identyczna,
zgodnie z degree1curl ND2 i degree2|H|². Pole/refnormy są liczone zespolenie.

Degree2 controls: near6vs8≤1,42e−12, radius2vs4≤2,21e−14,
far12vs16≤1,42e−15. Degree5near/farvariants **NOT RUN**; nie przypisywać im
kontroli1e−6 na podstawie samego degree2. FieldE1%FAIL, referencechange0,3%FAIL,
relativeerror-estimate degree2→5 E/H13,08/11,01%FAIL1e−6. To nie jest
zbieżny L2 ani powód do ponawiania solve czy dalszego samego FEMrefinement.

Dalsza referencja wymaga lepszej dyskretyzacji powierzchni, ze sprawdzonym
kosztem operatora. Obecny PMCHWTB5:7680DOF na prąd; cztery denseoperatory oraz
15360²complex128system to≥7,550GB przedLU, ponad6GiBcap. Nie uruchamiać denseB5.

## Następny backend: FMM

EXP70–73: przypięty ExaFMM addon z cached build działa. Mała kontrola
MaxwellT/K p8 przechodzi1e-6 po naprawie cyklu życia tablic w RAM tmpfs.
PMCHWTsolve EXP74–76 nie przechodzi niezależnego residuum; większa referencja NOT RUN. Szczegóły i ograniczenia:
[maxwell-fmm.md](maxwell-fmm.md). To CPU oracle, bez promocji CUDA/anteny.

## Odtworzenie i dowody

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/new-stream-control --physics stream-control --level 2 --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120
python3 tools/experiments/bempp_oracle.py run artifacts/new-f3-stream --physics stream-volume --level 3 --near-count 0 --volume-degree 5 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120
```

Streamcontrol jest ograniczony do32savedtargets i wariantubase, streamvolume
ma defaultpilot32. Guardy zapisanych wejść/sourcehelperów/nativeABI/SHA bez zmian.
Varianty `--stream-variant base|near6|radius2|far16`, strona `--near-side fine|coarse`.
Cache JIT zachowany, zero rebuild Palace/GPU/chmury, 6GiB/4CPU/noadditionalSwap.
Dane robocze RAM; NPZ input/results i code cache są osobnymi funkcjami.

Dowody w `artifacts/m2-stream-{control,repeat,f3-volume}-root-analysis-20261019.json`
oraz `m2-stream-f3-degree2-root-analysis-20261019.json`. Historyczne manifesty
EXP59–67 zachowują sourceSHA sprzed dodania benchmarktimerów; kernelfizyczny,
geometryhelpers i currents nie były zmienione. Aktualny controlEXP69 sprawdzony
przez root wraz z bieżącymi source/inputSHA i stanami terminalnymi.
