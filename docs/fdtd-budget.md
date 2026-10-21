# M5.6 — koszt gprMax przed portem anteny

EXP103,2026-10-21. **Ocena częściowa**, solver gprMax NOT RUN. Nie jest to
benchmark szybkości ani dowód błędu FDTD. Uniform grid ma konkretny problem
zasobów/geometrii; wieloregionowe HSG wymaga dalszej oceny, więc M5.6 pozostaje
otwarte. Nie instalujemy zależności ani nie przepisujemy CAD przed tym filtrem.

## Źródła, możliwości i granice

Sprawdzony upstream `gprMax/gprMax`, master commit
`d068a023265c1337982940efb41ef05a04f064a7`, GPLv3. Źródła są pobrane wyłącznie
do ignorowanego `build/gprmax-research`, nie importowane do Palace.

- [CUDAGrid](https://github.com/gprMax/gprMax/blob/d068a023265c1337982940efb41ef05a04f064a7/gprMax/grid/cuda_grid.py):
  rzeczywiste PyCUDA, tablice pól i IDs przesyłane na GPU. Nie zakładamy
  automatycznej obsługi UVM ani zgodności konkretnego buildu z sm120 bez testu.
- [FDTDGrid](https://github.com/gprMax/gprMax/blob/d068a023265c1337982940efb41ef05a04f064a7/gprMax/grid/fdtd_grid.py):
  sześć pól rzeczywistych i sześć IDs uint32 na węzłach (nx+1)(ny+1)(nz+1).
  To48B/węzeł przy FP32 i72B przy FP64, przed PML/DFT/współczynnikami.
  Host buduje dodatkowo solid uint32 i18 tablic int8 na komórkę; są to logiczne
  alokacje, nie zmierzony RSS (demand paging/zwalnianie mogą go zmieniać).
- [config](https://github.com/gprMax/gprMax/blob/d068a023265c1337982940efb41ef05a04f064a7/gprMax/config.py)
  i [HSG padding](https://github.com/gprMax/gprMax/blob/d068a023265c1337982940efb41ef05a04f064a7/gprMax/subgrids/grid.py):
  CUDA refining HSG istnieje, ale wymusza FP64 także main grid. Ratio jest
  nieparzyste; padding na stronę przy domyślnych ustawieniach to3r+r//2+2+6.
  Nie opieramy decyzji na starym założeniu, że CUDA subgridów nie ma.
- [Porty i normalizacja](https://github.com/gprMax/gprMax/blob/d068a023265c1337982940efb41ef05a04f064a7/docs/source/sources_ports.rst):
  skończona rezystancja napięciowego źródła ustala Z0, ale terminal S11 wymaga
  korekcji równoległej admitancji Yee gap. Vgenerator nie jest Vincident.
  Prądy/napięcia mają różne chwile Yee; transmisja napięciowa nie jest z automatu
  power-wave S21. Do porównania z Palace potrzebne te same fizyczne terminacje,
  płaszczyzny odniesienia, konwencja fazy i test TEM obu portów.

CUDA i subgridy są zatem możliwościami potwierdzonymi źródłowo; poprawność
sprzętowa na5070Ti i jakość naszej anteny nie zostały przetestowane.

## Rzeczywisty fixture

Mesh SHAec56c9a7de3e9cdc9618b87a2029975d474d6d5621f9fd08b35f24501b6f161e.
Streaming read w3,04s potwierdził bbox299,943×299,953×300mm, L0=0,001.
To obwiednia istniejącej domeny FEM, nie zoptymalizowany prostopadłościan FDTD/PML.
Przy zmianie domeny należy osobno sprawdzić granice i zbieżność.

Odczytane archiwalne parametry tej samej geometrii: PCB55mm, laminat0,762mm,
miedź0,035mm, launch gap0,2mm, coax pin radius0,14351mm, dielectric radius0,4699mm,
coax body do z=−40,303mm, barrel wall0,04mm. To benchmark z kablem/obudową,
nie najlepszy model produkcyjny. Źródło parametrów i jego SHA są w receipt.
Nie używać najmniejszej krawędzi tetra jako automatycznego wymogu dla FDTD.

## Odtwarzalny rachunek

`tools/fdtd_budget.py` liczy storage z faktycznych typów tablic i
dt=1/(c sqrt(dx⁻²+dy⁻²+dz⁻²)). Nie wywołuje solvera ani GPU. Testy sprawdzają
FP64 fields z nadal32-bitowymi IDs, padding, CFL i błędne wejścia. Przykłady:

```sh
python3 tools/fdtd_budget.py --length-mm 300 300 300 --step-mm 0.1 0.1 0.1
python3 tools/fdtd_budget.py --length-mm 300 300 300 --step-mm 1.1 1.1 1.1 \
  --hsg-box-mm 55 55 55 --hsg-ratio 11
```

| Scenariusz dla zmierzonego bbox | Same GPU fields+IDs | Idealny streaming pól, 100ns ×2 porty |
|---|---:|---:|
| uniform1mm/FP32 |1,31GB|152s|
| uniform0,5mm/FP32 |10,42GB|2415s|
| uniform0,2mm/FP32 |162,32GB|94071s|
| uniform0,1mm/FP32 |1297,30GB|1503636s|
| HSG main1,1mm/fine0,1mm, working55³mm |20,62GB|29789s|
| HSG main1,1mm/fine0,1mm, requested55×55×2mm |4,90GB|5499s|
| HSG main1,05mm/fine0,05mm, requested55×55×2mm |25,73GB|74528s|

To **dolne oszacowania storage** przed dodatkowymi tablicami. HSG padding jest
uwzględniony, jego pomocnicze pola PML/interfejsu nie. Wymiar working region
zaokrąglamy w górę do pełnych komórek main grid, by objąć żądany obszar.
Scenariusze pudełek HSG
nie są zweryfikowanym rozmieszczeniem ani konwersją geometrii.

Model czasu zakłada idealne czytanie/zapis samych sześciu pól przy katalogowej
[przepustowości896GB/s](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5070-family/).
Pomija ruch IDs, stencil/PML, FLOP FP64, DFT, źródła i synchronizacje; nie jest
zmierzonym runtime ani ogólną granicą dla dowolnego algorytmu z temporal blocking.
Jedna symulacja czasowa portu może zbierać wszystkie częstotliwości — nie
mnożymy jej czasu przez15. Kompletna para nadal wymaga obu pobudzeń.

100ns jest założeniem, nie ustalonym czasem wygaszania. Czas skaluje się liniowo
dla20/100/200ns. Dla modelowego rezonatora amplituda exp(−πft/Q) spada do1e−4
przy1,71GHz po około17/86/171ns dla Q10/50/100. Q naszej anteny/antyrezonansu
i poprawne okno czasowe trzeba zmierzyć. Wartość1/T nie jest dowodem dokładności
DFT ani wymaganiem odstępu między ocenianymi częstotliwościami.

Full-field DFT również kosztuje pamięć: jedna częstotliwość z sześcioma
zespolonymi składowymi dodaje2× storage pól. Same portowe przebiegi są małe;
nie doliczamy niepotrzebnych full-field DFT15freq jako wymuszonego kosztu.

## Decyzja i następna bramka

Nie uruchamiać pełnego uniform gprMax: rozdzielczość0,2mm już przekracza VRAM
i RAM, a0,5–1mm daje mniej niż jedną komórkę na0,2mm launch gap bez modelu
subcell. Nie kwalifikujemy tak uproszczonego feedu. Pudełko HSG0,1mm obejmujące
PCB i długi feed55³mm przekracza16GiB już samymi tablicami. Cienki HSG slab
mieści tablice, ale nie rozwiązuje geometrii coaxu poza slabem; nie jest gotowym
zamiennikiem badanego modelu. Drobniejszy slab0,05mm znów przekracza VRAM.

M5.6 **pozostaje otwarte**: sprawdzić ograniczenia styku/rozłączności/nestingu
HSG i czy da się zachować ciągły feed przez kilka małych ROI. Jeśli da się
zmieścić wiarygodny model wraz z kontrolą rozdzielczości, wykonać mały rzeczywisty
CUDA/TEM test przed portowaniem anteny. Jeśli nie, zamknąć ocenę konkretną
przeszkodą zasobów/API. Brak twierdzenia, że wszelkie FDTD jest niemożliwe
lub zawsze wolniejsze. Nie zmieniono fizyki/mesh/Tol referencji Palace.

Dowody: `artifacts/m5-fdtd-domain-20261021.json`,
`artifacts/m5-fdtd-budget-20261021.json`, pinned source cache/sources.json.
