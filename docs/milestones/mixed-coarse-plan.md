# M5.3 — skalowany native complex coarse FP32

Status: **PROTOTYPE PASS W.1–W.3**, EXP98–101, 2026-10-21. W.3 obejmuje
tylko3,50GHz/P2; jedna para pomiarów. Bez globalnej promocji/defaultu.
Cel: zachować jakość falowego coarse solve lepiej niż realny shifted AMS,
zmniejszając dane faktorów cuDSS. Nie powtarzać dawnego blind-cast realnego shim.

## Fakty i nowa hipoteza

Przed EXP99 native używał tylko CUDA_C_64F/GENERAL. Dawny tools/adapter/cudss_fp32.cu
obsługuje realne CUDA_R_64F→R_32F; nie jest implementacją nativecomplex FP32.
Obecny constructor celowo odrzuca PALACE_CUDSS_FP32 dla nativecomplex.
Wcześniejszy sukces lub porażka realnego shim nie kwalifikuje nowego algorytmu.

Hipoteza: float kompleksowe LU po equilibracji + zewnętrzna korekcja residuum
liczona z ORYGINALNEGO FP64 CSR. B=DAD, g=Db, x=Dy dla dodatniego diagonalnego D;
np. Dii≈1/sqrt(|Aii|), z ochroną zer i kontrolą rozkładu współczynników. Dodatnie
D nie robi z A macierzy Hermitowskiej/SPD: cuDSS nadal GENERAL.
Wewnętrzne IR o tym samym dtype nie jest automatycznie korekcją mixed precision.
API matching/scaling/IR ocenić na przypiętym0.7.1, nie zakładać obsługi typu:
https://docs.nvidia.com/cuda/archive/12.9.1/cudss/types.html (research2026-10-21).

## Kolejność przed integracją

1. Cached mały manufactured complex non-Hermitian stencil; dwa RHS i wartości
   zmieniane przy stałym wzorcu. BaselineFP64, rawFP32, scaled+correctedFP32.
2. Oprócz zwykłego układu kontrola celowo źle skalowana; nie mylić złego skalowania
   z nieusuwalnym uwarunkowaniem fizycznego rezonansu. Znane x i niezależne
   FP64 b/Ax/r, relative_solution oraz row/backwarderror; zero-fault/perturbed
   solution test, dtype i cleanup rzeczywiście sprawdzone.
3. Korekcja: r=b−Ax w FP64, δ z FP32 LU dla D*r, x+=D*δ. Przed runem zamrozić
   liczbę korekt i bramkę poprawności; κ(B)*u32<1 jest użyteczną wskazówką,
   nie gwarancją. Przy stagnacji/nonfinite/badpivot przerwać, zachować FP64fallback.
   Zmienna liczba kroków/zmienna jakość PC wymaga oceny FGMRES i wektorów Z;
   nie udawać stałego preconditionera. Żadnego silentprecisionfallback w środkuGMRES.
4. Dopiero API PASS: ograniczony nativeprototype i tiny→medium→W3; logować
   FP64 storage reszty FEM/residual vs FP32 factor/solve, konwersje, korekty,
   kondycję/skalowanie, pamięć także oryginalnegoCSR i cały koszt. Faktor values
   mogą być o połowę mniejsze, ale indeksy/workspace/originalCSR nie muszą.
5. Promocja dopiero frozenK/wholefields/fulltime. Brak użytecznego zysku oznacza
   REJECT, nie redukcję dokładności. Nie deklarować Tensor Cores na podstawie dtype.

## Limit możliwej wygranej

Aktualny ukończony UVM W3P2: Total348,416s (runner350,371s), coarse63,413s,
remainingPC97,153s, Setup87,021s z factor42,965s. Same darmowe coarse solves
mogłyby dać najwyżej około1,22× dla CAŁEGO zadania. Dwukrotnie szybsze coarse
bez innych zmian daje około9,1% oszczędności czasu. To rachunek dla tego runu,
nie krótki profil ekstrapolowany na wszystko. Większa wygrana wymaga zmniejszenia
setup i/lub ruchu pamięci pozostałego PC; EXP96 pokazał regres mimo2×coarse.

## Implementacja i zabezpieczenia

`tools/dev.py run … --native-complex-coarse --native-coarse-fp32` wybiera
complex FP32 GENERAL LU. Oryginalny CSR, FEM, residuum i akumulacja pozostają
FP64; baza GMRES może oddzielnie używać zakwalifikowanego storage FP32/direct.
Nie jest to TF32/BF16 ani dowód wykorzystania Tensor Cores.

`palace/linalg/mixedcoarse.hpp` zawiera współdzielone kernele DAD, Db, r=b−Ax
i x+=Dδ. Dokładnie dwa kroki korekcji, bez adaptacyjnej zmiany liczby kroków
i bez zmiany typu/fallbacku w środku GMRES. Wbudowane cuDSS IR wyłączone.
Domyślny native FP64 pozostaje dostępny po pominięciu nowej flagi.

Skala to 1/sqrt(|Aii|); dla brakującej/zerowej diagonali używany jest maksimum
modułu wiersza. Pusty/niefinitywny wiersz, overflow macierzy/RHS lub błąd
faktoryzacji przerywa próbę. Oryginalne coarse residuum musi być skończone
i ≤1e−3 przy każdym apply. Jest to osobny bezpiecznik preconditionera;
zewnętrzny próg1e−6 i bramki K pozostają niezmienione.

Stała liczba kroków ogranicza zmienność algorytmu PC, lecz nie usuwa błędów
zaokrągleń. W coax kandydat wymagał istniejących reliable restarts: pierwsze
testy true residual nie przeszły, dopiero poprawione rozwiązania spełniły próg.
Nie ukryto tych zdarzeń. Zmienna liczba korekt/adaptacyjny fallback wymaga
osobnej oceny FGMRES i kosztu dodatkowych wektorów Z.

Runner odrzuca mixed bez native oraz z hybrid/CPU/AMS. EXP102 dopuścił kontrolowany
partial profile, który zawsze ma RFcomplete=false; [pomiar](../mixed-coarse-profile.md).
Sprawdza actual
dtype, podsumowanie korekcji, skalę i cleanup. Adapter raportuje prawdziwe FP32
faktory; stary realny shim jest wyłączony. Dodatkowe CSR FP32, oryginalny CSR FP64,
skala i wektory korekcji są uwzględnione w pomiarach całego procesu.

## Mały test numeryczny EXP98

Polecenia: `python3 tools/experiments/complex_coarse.py build --variant mixed`,
następnie `python3 tools/experiments/complex_coarse.py run OUTPUT --variant mixed`.
Cached compile około1,5s, run około2,3s; 2GiB/no swap/2CPU/60s +75s watchdog.
Macierz512×512, dwa RHS i dwa zestawy wartości tego samego CSR; regularna
oraz A=ΓA0Γ z Γmax/Γmin=1e6. To test złego skalowania, nie gwarancja dla
źle uwarunkowanego fizycznego rezonansu.

- v1 przerwał na oczekiwanym złym rawFP32; refined ill-scaled NOT RUN.
- v2 uruchamiał korekcję na CPU; nie jest dowodem ścieżki CUDA.
- GPU-v3/v4: oryginalne FP64 residuum/korekcja na GPU, końcowa niezależna
  kontrola CPU. v4 refined ill-scaled: solution5,38e−12/backward6,90e−16,
  oba poniżej zamrożonego1e−10. Raw FP32 około20% błędu pozostaje FAILED
  kontrolą negatywną, mimo globalnego RHS residual około1e−7.
- Współdzielone kernele sprawdzone dla n=0/1/509/1009, dwóch RHS, canaries,
  invalid dimensions, assign/add, overflow FP32 oraz scale fallback/invalid row.
  celowa perturbacja rozwiązania wykrywana; cuDSS live_after_destroy=0.

Artefakty: `artifacts/m5-mixed-coarse-api-gpu-v4-20261021/` i zachowane wcześniejsze
wersje. Czasy FP64/FP32 tego małego probe są obciążone rozgrzewką/JIT; nie
używamy ich do deklarowania przyspieszenia faktorów ani anteny.

## Pomiar na jednej 5070 Ti

| Model / częstotliwość | Control FP64 | Mixed | Iteracje control → mixed |
|---|---:|---:|---|
| coax-tiny3,55GHz, oba porty |16,625s|16,606s|39/42 →40/42|
| coax-medium3,30GHz, oba porty |101,640s|96,486s|45/47 →48/50|
| coax-medium3,55GHz, oba porty |101,531s|97,503s|45/47 →47/49|
| coax-medium3,80GHz, oba porty |101,659s|97,634s|45/47 →47/49|
| T-Shaped medium3,50GHz/P2 |339,362s|273,843s|35 →35|

W.3 jedna para: **−19,31% czasu (1,239×)** i **−19,01% cgroup peak**:
56,027→45,376GB. Managed peak52,277→40,963GB; actual cuDSS allocations
25,008→13,348GB. To nie jest pomiar fizycznej rezydencji VRAM. GPUprocess
telemetry UVM nie obejmuje całej rezydencji; nie deklarujemy zejścia do16GB.

Wyłączne czasy W.3: setup83,600→48,390s, w tym faktor40,528→4,823s;
coarse apply61,613→32,038s, pozostały PC96,235→95,123s. Nie sumować faktora
drugi raz z setupem. Nowy pomiar migracji UVM FP32 NOT RUN; spadek alokacji
sam nie dowodzi określonej liczby zaoszczędzonych transferów.

## Jakość i odtwarzanie

Root porównał bezpośrednio complex S, VSWR, moce i energie z obu runów.
W.2 trzy częstotliwości: maxΔS7,04e−9, ΔVSWR1,39e−8, energia1,29e−8;
TEM E/B<0,5%, pola vs zgodne referencje PASS. W.3 ΔS6,71e−10,
ΔVSWR5,93e−10, energia1,85e−9; siedem regionów E≤1,469e−8/B≤1,558e−9
względem tej samej zapisanej referencji. Oryginalne outer residual
control8,35661e−7 / mixed8,35698e−7. Coarse safety max2,32445e−5.
Żadnej zmiany mesh/medium/fizyki/Tol dla uzyskania PASS.

Reprodukcja W.3 (lokalne referencje/seed muszą istnieć i przejść kontrolę hasha):

```sh
python3 tools/dev.py build --jobs 2
python3 tools/dev.py run tshaped-medium artifacts/mixed-example --seconds 900 \
  --basis fp32 --direct-basis --pc-side right --krylov-size 64 \
  --native-complex-coarse --native-coarse-fp32 --hypre-pool-mib 256 \
  --memory-marks --release-gmres-basis --release-final-solver --setup-audit \
  --save-fields --field-reference artifacts/m3-antenna-native-direct-20261019 \
  --initial-fields artifacts/m1-antenna-resident-fp64-20261018
```

Seed jest tylko przybliżeniem startowym, nie referencją jakości. Control pomija
wyłącznie `--native-coarse-fp32` i ma osobny katalog. Całe argv, config, mesh SHA,
manifest i tło są w artefaktach `m5-mixed-antenna-p2-{control,on}-20261021/`.
Build sourceSHA8692e80d926a58a74f38bff9c643b578810a94d35d4d534a2c027215fd11607f;
runtime CUDA12.9.1/cuDSS0.7.1.4/MFEM4.9/arch120. Cached native build18,615s,
bez przebudowy dependencies. Fallback: `build/m5-mixed/pre-mixed-native`.

Root receipts: `artifacts/m5-mixed-filters-root-analysis-20261021.json`,
`artifacts/m5-mixed-antenna-root-analysis-20261021.json`. Artefakty są lokalne,
nie commitowane; pakiet przenośny i odtwarzanie referencji należą do M7.

**Decyzja:** zachować obiecujący opt-in. W.4/W.5, trzy powtórzenia/mediana,
drugi port pełnej anteny, nowa geometria i M6 sweep/TC nadal NOT RUN.
M5.5 zmierzone później w EXP102; M5.6 FDTD nadal otwarte, M5 nie jest zakończony.
Bufory RAM/VRAM, bez swap/SSD workspace; limity i cache zachowane.
