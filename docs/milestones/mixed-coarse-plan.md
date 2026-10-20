# M5.3 — plan skalowanego native complex coarse FP32

Status: **PLANNED/NOT RUN**, po EXP97,2026-10-21. Bez nowej promocji/defaultu.
Cel: zachować jakość falowego coarse solve lepiej niż realny shifted AMS,
zmniejszając dane faktorów cuDSS. Nie powtarzać dawnego blind-cast realnego shim.

## Fakty i nowa hipoteza

Actual native obecnie CUDA_C_64F/GENERAL. Dawny tools/adapter/cudss_fp32.cu
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

Bufory tylkoRAM/VRAM, cache i normalne artefakty dozwolone, limity niezmienione.
Najpierw test sekundowy; nie zaczynać od900santeny. Agentgłównyprojektuje,
ta samaLuna uruchamia gotoweargv. Ta lista nie jest wykonanym eksperymentem.
