# M2 — transmisja przez dielektryk: screening i kalibracja referencji

EXP38–41, 2026-10-19. **Wykonane, próg jakości niezaliczony.** M2 ACTIVE.
To lokalne testy CPU/RAM na wielościanie, nie promocja anteny ani pomiar
przyspieszenia na RTX. Nie zmieniono Palace/MFEM/medium i nie było rebuilda.

## Dwie niezależne dyskretyzacje tej samej fizyki

`bempp_transmission.py` stosuje eps=1 lub 2,94, mu=k=1, exp(−iwt).
Geometria to ten sam płaski wielościan co w [EXP35–37](maxwell-trace-duality.md).
Nie porównujemy jego pól z Mie dla innej, kulistej powierzchni.

- Sprzężenie: rzeczywisty MFEM ND2, A=curlcurl−eps*M, sparse Schur,
  magnetic-dual BC/RWG/SNC i zewnętrzny Calderón bez zmiany.
- Odniesienie: niezależny PMCHWT, dwa RWG ślady, operatory wnętrza/zewnętrza;
  bez FEM, mortaru i Schura. Dzieli przypięte kernele Bempp z prototypem,
  więc niezależność dotyczy układu i dyskretyzacji, nie całej biblioteki.
- Wnętrze PMCHWT: E=K*t+T*h/rho, H=K*h−rho*T*t, rho=sqrt(eps),
  t=E×n, h=H×n. Kontrola eps=1 porównuje je z analityczną falą płaską.
- B4 referencji powstaje przez płaskie 1→4 subdivision B3, bez projekcji
  radialnej. Test sprawdza płaszczyzny, outward normals, objętość 4π/3,
  1280 trójkątów i 1920 krawędzi o dwóch incydencjach.

Pierwotne źródła: przypięty Bempp-cl
`a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0`,
[`examples/maxwell/maxwell_dielectric.py`](https://github.com/bempp/bempp-cl/blob/a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0/examples/maxwell/maxwell_dielectric.py)
oraz [`potential/maxwell.py`](https://github.com/bempp/bempp-cl/blob/a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0/bempp_cl/api/operators/potential/maxwell.py).
Publiczny fetch nie działał; sprawdzono te pliki w istniejącym przypiętym checkout.

## Co rzeczywiście mierzymy

160 centroidów tetraedrów FEM2, wagi równe objętościom (suma 4π/3).
Zespolony ważony błąd próbek to sqrt(sum w|u−v|² / sum w|v|²).
**Nie jest to całka L2 całego pola.** Raport zawsze ustawia
`analytic_target_passed=false`; osobne `screening_passed` nie zalicza M2.
Bez dodatkowego swap, 6 GiB/4 CPU, tmpfs dla temp/cwd, limit 180 s.

## Wyniki

| Eksperyment | Czas z runnerem | RSS | Wynik |
| --- | ---: | ---: | --- |
| EXP38, eps1, coupled F2/B2 + PMCHWT B1/B2 | 51,407 s | 0,761 GB | screening FAIL |
| EXP39, eps1, tylko PMCHWT B2/B3, q4/q8 | 34,290 s | 0,456 GB | kalibracja, bez FEM solve |
| EXP40, eps2,94, coupled F2/B3 + PMCHWT B2/B3 | 112,166 s | 1,309 GB | screening FAIL |
| EXP41, eps2,94, tylko PMCHWT B3/B4, q8/q12 | 126,619 s | 1,145 GB | referencja nadal niezbieżna do 0,3% dla E |

EXP38 eps1: coupled centroid E/H 0,616/1,327% względem fali analitycznej,
PMCHWT B2 q4 aż 2,621/2,636%. Małe raw≈1e−14 nie gwarantuje dokładnego pola.
EXP39 rozdziela siatkę od kwadratury potencjałów (boundary assembly nadal q4):

| Referencja eps1 | E/H q4, % | E/H q8, % |
| --- | ---: | ---: |
| B2 | 2,621 / 2,636 | 1,824 / 1,830 |
| B3 | 0,216 / 0,217 | 0,158 / 0,158 |

Oba czynniki wpływają na wynik; znaki/skalowanie dają zgodność z analitycznym
polem w badanych punktach. Nie dowodzi to jeszcze poprawności dielektryka.

EXP40 eps2,94: coupled vs PMCHWT B3/q8 E/H **0,885/1,360%**, far-field
0,1116%, raw5,14e−14, energy error/π1,02e−7. Referencja B2→B3 zmienia się
o3,202/1,975%, więc nie wolno przypisać całej różnicy sprzężeniu/FEM.

EXP41 zachowuje kandydata; zwiększa tylko referencję. PMCHWT B3→B4/q12
zmiana E/H **0,408/0,166%**. Potencjał B4 q8→q12 zmienia się jedynie
o **0,000083/0,000084%**. Teraz kwadratura potencjału ma mały wpływ na
te próbki, lecz zbieżność siatki referencyjnej E nie spełnia 0,3% screeningu.

Root porównał zachowane rozwiązanie EXP40 z B4/q12 bez powtarzania solve:
E/H **1,092/1,320%** — oba ponad 1%. Drobne far-field i energy errors
nie wystarczają do kwalifikacji pól bliskich. Nie obniżono żadnego progu.

## Pamięć, cache wyników i dalsza decyzja

PMCHWT B4 ma 3840 niewiadomych (po1920 na ślad) i gęsty blok235,930MB.
Coupled B3 ma480 powierzchniowych DOF na ślad, ale największe local BC assembly
530,842MB. Same liczby DOF nie dowodzą mniejszej pamięci ani krótszego czasu.
Nie porównywać tych czasów z FEM mającym inne warunki brzegowe/błąd.

Zapisy `coupled-solution.npz`, `pmchwt-level*.npz`, `fields-level*-q*.npz`
i `probes.npz` to małe zwykłe wyniki do ponownego postprocessingu.
Nie są basis/scratch/offloadem solvera. EXP41 nie powtarzał coupled solve.

Najbliższy krok: wykorzystać te rozwiązania do kontroli pola na wspólnej
kwadraturze objętościowej oraz ocenić niezależnie zmianę FEM. Nie zwiększać
w ciemno referencji do B5 i nie uruchamiać sweepu anteny. M2.2/M2.3 pozostają
otwarte; późniejsza decyzja integrate/reject wymaga również oceny rezonansów
i kosztu przy zgodnym błędzie. Bez promocji solvera ani nowych defaultów.

## Odtworzenie i audyt

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/new-transmission --physics transmission --level 2 --surface-level 3 --epsilon-r 2.94 --seconds 180
python3 tools/experiments/bempp_oracle.py run artifacts/new-reference --physics transmission --level 2 --surface-level 4 --epsilon-r 2.94 --reference-only --seconds 180
```

Reference-only eps1 używa q4/q8, eps2,94 używa q8/q12; ordinary run potentialq8.
Surface-level4 jest dozwolony wyłącznie dla reference-only, bez FEM solve.
Jawne eps obowiązuje tylko dla transmission; wadliwe kombinacje odrzucane
przed sprawdzeniem/alokacją host memory. Główny coupled probe nadal max B3.

Dowody: `artifacts/m2-transmission-root-analysis-20261019.json` oraz
`artifacts/m2-transmission-refinement-analysis-20261019.json`. Root sprawdził
stany terminalne/noOOM, applicable helper/SO/case SHA i niezależnie przeliczył
zespolone błędy z NPZ. Historyczne EXP38/39 pochodzą ze wcześniejszych wersji
skryptu; manifesty zachowują ich SHA, nie przypisujemy im aktualnego hasha.
