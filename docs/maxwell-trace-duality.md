# M2 — przestrzenie śladów i niezależne siatki FEM/BEM

EXP35–37, 2026-10-19. **PASS małego transparentnego interfejsu ND2**.
M2 pozostaje ACTIVE: brak jeszcze sprzężonego testu transmisji przez dielektryk,
kontroli rezonansów oraz porównania kosztu z FEM przy zgodnym błędzie.
Nie zmieniono Palace, medium ani ustawień produkcyjnych anteny.

## Hipoteza i implementacja

Historyczny [EXP34](maxwell-nd2-coupling.md) nie przeszedł 1% pól.
Rozdzielono błąd reprezentacji powierzchniowej od błędu objętościowego:

- `bempp_trace_spaces.py` porównuje dualną i najlepszą projekcję L2 RWG/BC.
- `bempp_nd2_coupling.py --duality magnetic` stosuje przypięty upstream
  magnetic-dual: ślad E w BC, H w RWG, test SNC. Electric-dual pozostaje
  kontrolą: E w RWG, H w BC, test RBC. Zmienia się cały zestaw parowań;
  nie przypisujemy poprawy wyłącznie jednej przestrzeni.
- Fizyczne B=<v_ND2,h_basis> i D=<test,v_ND2×n> spełniają D=−Bᵀ.
  Wewnętrzny helper mortaru ma historyczne nazwy argumentów `bc/rbc`, lecz
  wariant magnetic przekazuje barycentryczne RWG/SNC. Operator FEM i sparse
  Schur pozostają w complex128; nie powstaje pełna gęsta macierz FEM.
- `--surface-level` pozwala zagęścić sam BEM. `boundary_parents` sprawdza
  centroid i wszystkie trzy wierzchołki trójkąta względem jednej ściany FEM.
  Powierzchnia przecinająca ściany FEM jest odrzucana, nie całkowana na skróty.

Źródło konwencji: przypięty Bempp-cl commit
`a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0`,
[`maxwell.py`](https://github.com/bempp/bempp-cl/blob/a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0/bempp_cl/api/operators/boundary/maxwell.py).
MFEM v4.9 release; źródłowego Git SHA zainstalowana biblioteka nie ujawnia.

## EXP35 — tani test reprezentacji śladu

18,643 s z runnerem, max RSS 347 MB. Bez nonlocal assembly i solve Maxwella.

| Powierzchnia: 20 / 80 / 320 trójkątów | Błąd L2 śladu E, % |
| --- | --- |
| RWG, dualna projekcja | 20,994 / 10,433 / 5,157 |
| RWG, najlepsza L2 | 19,633 / 10,024 / 5,064 |
| BC, dualna projekcja | 48,942 / 31,244 / 20,868 |
| BC, najlepsza L2 | 46,787 / 30,143 / 20,090 |

RWG odtwarza stały ślad do ~1e−15, BC ma błąd 46,87→20,57%.
Nie świadczy to o nieważności BC w normie H(div)^−1/2. Raportujemy rzeczywisty
błąd punktowy BC; nie wymagamy fikcyjnego zera. Kontrole weak residual≤1e−12,
q4/q6≤1e−6 i best-L2 PASS. Próg 1% pól Maxwella pozostaje bez zmian.

## EXP36–37 — wyniki sprzężenia

Ta sama geometria: stały wielościan o objętości 4π/3, eps=mu=k=1,
analityczne E_x=exp(iz), H_y=exp(iz). F/B oznaczają poziom FEM/BEM.
Czasy obejmują runner; RSS jest szczytem procesu, nie pomiarem VRAM.

| Wariant | FEM / BEM DOF | E L2, % | H L2, % | Czas, s | RSS, GB | 1% pól |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| electric F2/B2, kontrola | 1228 / 120 | 10,072 | 5,645 | 43,925 | 0,722 | FAIL |
| magnetic F2/B2 | 1228 / 120 | 1,424 | 2,884 | 40,861 | 0,708 | FAIL |
| magnetic F2/B3 | 1228 / 480 | 0,560 | 0,751 | 91,437 | 1,323 | PASS |
| magnetic F3/B3 | 8936 / 480 | 0,358 | 0,904 | 95,902 | 1,345 | PASS |

Przy stałym FEM2 zagęszczenie B2→B3 poprawia oba pola. Przy stałym B3
FEM2→FEM3 poprawia E, ale pogarsza H. **Nie dowodzi to monotonicznej
zbieżności obu pól.** F2/B3 jest lepszy pod względem najgorszego błędu i kosztu;
F3/B3 jest dodatkową kontrolą, nie zwycięzcą we wszystkich metrykach.

W czterech końcowych runach mortar≤1,55e−15, weak constant≤5,87e−16,
raw≤2,32e−13, q6/q8≤1,72e−13. F2/B3 i F3/B3 mają spurious far-field
≤6,47e−5 i bezwzględny energy error/π≤3,34e−8. Mała ujemna extinction
F2/B3 (−9,47e−8) jest błędem przy dokładnym zerze, nie dowodem ścisłej dodatniości.

## Koszt i decyzja

B3: końcowy Schur 3,686 MB, ale największy lokalny operator przed redukcją
ma **530,842 MB**. Schur solve trwa 0,117 s (F2) / 2,430 s (F3), podczas gdy
assembly dominuje w ~90 s zadania. Nie porównywać tych czasów z pełną anteną.
Gęste lokalne assembly nie kwalifikuje się do skalowania na antenę.

Decyzja: zachować prototyp jako poprawny mały test transparentnego interfejsu.
Brak promocji do Palace. Następne: transmisja eps=2,94 z niezależnym odniesieniem
na tej samej geometrii, potem koszt przy porównywalnym błędzie i decyzja M2.4.
Sam wcześniejszy PMCHWT/Mie dielektryka nie testował interfejsu FEM–BEM.

## Odtworzenie i dowody

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/new-traces --physics traces --level 3 --seconds 120
python3 tools/experiments/bempp_oracle.py run artifacts/new-f2-b3 --physics nd2-coupling --duality magnetic --level 2 --surface-level 3 --seconds 180
```

F2/B2: obie wartości `--duality`, poziomy 2/2. F3/B3: poziomy 3/3.
Runner ogranicza RAM do 6 GiB, 4 CPU, bez dodatkowego swap; cwd i temp to tmpfs.
Niezmieniony cached MFEM SO; bez rebuilda Palace/zależności i bez płatnego compute.
Regresje obejmują kwadraturę projekcji, nested parent lookup z odrzucaniem
przecinających trójkątów oraz walidację flag przed alokacją.

`artifacts/m2-trace-duality-root-analysis-20261019.json` weryfikuje rzeczywiste
terminalne stany/noOOM, SHA aktualnych źródeł/helperów/SO oraz powyższe progi.
Utrwala pięć katalogów runów i hashe ich manifestów/wyników. Końcowe F2/B2
odtwarzają wcześniejszy kod przed parent lookup z Δpól<1e−12.
