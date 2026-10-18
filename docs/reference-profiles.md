# M1 — historyczne profile referencji i coarse solve

2026-10-18. Historyczne eksperymenty EXP15–17; opcje były opt-in i nie
zmieniły defaultów. Medium przestrzenne i równanie A pozostały bez zmian.
Późniejszy native complex coarse EXP18–19 oraz W.3 anteny opisano osobno w
[raporcie native complex](native-complex-coarse.md). M1 nadal otwarty.

## Opcje i granice

- `--cpu-reference`: Device CPU, backend `/cpu/self`, host MFEM,
  8 wątków OMP i 1 BLAS; FP64 baza i cuDSS hybrid **execute**.
  To inny tryb niż hybrid **memory**; ich łączenie jest odrzucane.
  Nie łączymy tego profilu z Q-pool ani complex-coarse.
- W przypiętym cuDSS0.7 host dense vectors w execute wymagają nrhs=1.
  Dlatego realny coarse wrapper wykonuje oddzielne solve real/imag zamiast
  ArrayMult2. Runner wymaga markerów rzeczywistego CPU/backend/execute/serialRHS.
  Pierwsza próba nrhs2 pozostała FAIL/NOT_SUPPORTED, nie jest wynikiem RF.
- `--complex-coarse`: istniejące upstream ComplexCoarseSolve=true,
  PCMatShifted=false. Wrapper rozwiązuje blok `[Ar Ai; Ai −Ar]`
  dla `[xr;−xi]`. Oryginalny operator A i precyzja FP64 pozostają.
- `--release-final-solver`: tylko fixed-mesh uniform sweep; po ostatnim
  rzeczywistym solve i kontroli residuum zapisuje metadata, niszczy solver
  przed A/P/A2/K/C/M. Zachowuje Curl, pola i przestrzenie do postprocess.
  Marker występuje raz, także przy wielu portach/freq; fazy opcjonalne przez
  `--memory-marks`. AMR/adaptive niezakwalifikowane.
- `--phase-trace`: istniejące nested BlockTimer/NVTX, host monotonic intervals,
  bez dodatkowego GPU sync. Czas coarse mieści się w czasie preconditionera.
  To nie jest pomiar samych kerneli.

## Dowody

| Próba | Wynik | Ograniczenie |
|---|---|---|
| CPU RIGHT tiny | 6/6,19,678s,233iteracji; S/pola zgodne z GPU | Wolniej niż mały GPU run |
| CPU TEM | 2/2,19,843s; E/B L2<1% | Nie kwalifikuje anteny |
| CPU full replay | OOM,247,6s,cap60GiB | Brak S/pól, brak promocji |
| Complex-coarse tiny | 153iteracje vs233 (−34,3%),12,534s | Faktory167,9MB vs61,5MB (2,732×) |
| Final release tiny | 6/6,12,567s; E/B różnica≤1,508e−13 | Oddaje258,9MB przed postprocess; wcześniejszy global peak nie spadł |
| Exact real-block complex-coarse full | Host guard,399,828s,iter16 | Faktory30,64GB; brak końcowych raw/S/pól; odrębne od native N×N |

Tiny complex-coarse raw relative względem RHS≤9,101e−7. Root przeliczył
S z dB/stopni na liczby zespolone: |ΔS|≤2,511e−8, ΔVSWR≤2,641e−8,
Δmocy≤2,952e−8; względna różnica energii≤1,277e−7, E/B≤2,286e−7.
Final release zmienił CSV jedynie na poziomie zaokrągleń (nie bitwise).

Full guard: exit137, OOMKilled=false, cgrouppeak61,55GB. Ostatni wypisany
residual1,339e−2 jest rekurencyjny, nie końcowy raw. Managed HWM49,0GB
pochodzi z ostatniego markera **sprzed** GMRES; nie znamy terminalnego
managed peak. CuDSS już zawiera się w managed; nie sumować tych liczników.
Nie uruchomiono ponownie tego samego wariantu ani nie podniesiono limitów.

## Hipoteza zrealizowana później

Propozycja bezpośredniego coarse FP64 complex N×N została zbadana w EXP18–19.
Wyniki probe, coax/TEM, fallback i pełnego W.3 anteny są w
[raporcie native complex coarse](native-complex-coarse.md). Nie przenosić
wyniku tej ścieżki na historyczny real-block wariant ani na domyślną
konfigurację.

Źródła sprawdzone2026-10-18: pinned MFEM4.9 `linalg/cudss.cpp` oraz
`palace/linalg/solver.cpp`, NVIDIA/cuDSS0.7 w archiwum CUDA12.9.1:
[hybrid execute](https://docs.nvidia.com/cuda/archive/12.9.1/cudss/advanced_features.html),
[typy i ograniczenia](https://docs.nvidia.com/cuda/archive/12.9.1/cudss/types.html).
API cuDSS nie należy utożsamiać z najnowszą wersją dokumentacji.

Pamięć robocza wyłącznie RAM/VRAM, bez scratch/offload/swap na dysk.
Cała niezależna kontrola jakości anteny pozostaje otwarta.
