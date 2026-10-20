# M5 — GPU AMS, EXP97

Status2026-10-21: tiny/medium PASS, **W.3P2 FAIL/deadline**. Obecny wariant
AMS C2 nie jest kandydatem produkcyjnym. FP64/native cuDSS pozostaje fallbackiem.

## Poprawny operator pomocniczy

Właściwe A=K+iωC−ω²M, mesh medium i tolerancje bez zmian. Istniejący Palace
buduje PC z realną dodatnią aproksymacją: curl-curl +ω*conductivity +|ω²|*mass,
port/absorbing terms. `PCMatReal=true`, `PCMatShifted=true`,
`ComplexCoarseSolve=false`. Nie stosujemy AMS/CG bezpośrednio do nieokreślonego A.
P1-coarse dostaje HypreAmsSolver, P2 geometryczny multigrid; outer GMRES RIGHT/K64.
AMSMaxIts2/MGCycleIts1, scalar Pi/cycle14, singular=false, opcje GPU z upstream.
Opt-in ustawia AMS tolerance0, więc liczba cykli stała; nie ukrywa zmiennego PC
pod zwykłym GMRES. Nie wymaga nowej biblioteki ani zmiany precyzji operatora.

Źródła: ksp.cpp/spaceoperator.cpp/ams.cpp i actual HYPRE3.1.0 headers.
[AMS](https://hypre.readthedocs.io/en/latest/solvers-ams.html) i
[GPU support](https://github.com/hypre-space/hypre/wiki/GPUs), sprawdzone2026-10-21;
aktualne docs3.2 nie zastępują kontroli przypiętych API. Dodatni helper pasuje
założeniom AMS, ale nie musi dobrze przybliżać rezonansowego Maxwella.

## Wyniki

| Case | Czas s | Iteracje | Status |
|---|---:|---|---|
| Tiny3,55GHz/oba porty |23,816|244/239|raw/fields/TEM PASS|
| Medium3,55GHz/oba porty |146,825|433/397|raw/fields/TEM PASS|
| Antena3,50GHz/P2 |901,727|ostatnia widoczna264/restart4|FAIL limit900s|

Tiny maxΔS1,822e−8/energyrelative9,871e−8/weightedE3,160e−5/B4,392e−7;
medium maxΔS5,655e−7/energyrelative7,025e−7/E9,032e−6/B6,288e−7.
TEM q4/q6≤0,496%E/0,457%B. Oba spełniają frozenK. Mediumcgroup1,822GB,
managedpeak1,841GB; wcześniejszy UVMmedium101,893s/cgroup2,598GB.
To kompromis na coax, nie dowód oszczędności w ukończonej antenie.

Pełny run ma complete=false/exit255, brak końcowego raw/pól, brak solver/basis
release. Ostatnia norma rekurencji1,501266e−3 nie jest zweryfikowanym residuum
końcowym. Cgrouppeak29,320GB dotyczy nieukończonego runu. Managed16,111GB to
ostatni markedpeak przy końcu setupu, nie pełny szczyt solvera. Nie porównywać
tego jako qualifiedmemorysaving z zakończonym FP64 runem56GB.

## Dowód GPU i koszt

Audyt actualHYPRE memory/execution=device i CUDA_MASK, zapisany dimension/type.
Osobny tiny Nsight0:2 strictPASS, bez warnings, poprawne zegary/coverage/cleanup:
CoarseSolve6978kerneli/14,894ms, w tym HYPREspgemm/IVAXPY i cuSPARSESpMV;
Preconditioner1212/12,036ms. Source branch coarse=HypreAms plus obserwowane CUDA
w tej fazie potwierdzają pracę GPU. CPU setup/control też istnieje; nie deklarować
100%GPU. Ślad umyślnie częściowy, nie kwalifikuje RF ani kosztu pełnej anteny.

Klucz: brak25GBLU zmniejsza working set, lecz słabszy helper mnoży iteracje.
Mniejszy PC nie wystarcza do przyspieszenia falowej anteny. Nie ponawiać pełnego
C2 bez nowej hipotezy ani nie podnosić Tol/deadline dla uzyskania PASS.

## Odtworzenie i następny krok

`tools/dev.py run ... --ams-cycles 2 --basis fp32 --direct-basis --pc-side right
--krylov-size 64`. 1..4 to zakres jawnej konfiguracji, przetestowano tylko2.
Nie łączyć native/complex coarse, hybrid, CPU, Qpool, setupaudit/reuse. Audyt
konfiguracji w result nie jest sukcesem całego runu; complete/raw/field gates osobno.
Nowy env PALACE_AMS_FIXED_GPU jest czyszczony dla zwykłych runów.
Cached build7,2s/1TU, fallback build/m5-ams/pre-ams-native. Bez nowych dependencies,
paidcompute/SSDworkspace/appsclosing,60GiB/noswap/hostguard6GiB.

Receipts: artifacts/m5-ams-root-analysis-20261021.json; poszczególne
m5-ams-{tiny-c2,tiny-profile-c2,medium-c2,antenna-p2-c2}-20261021/.
Następny kierunek: [scaled mixed coarse](milestones/mixed-coarse-plan.md), nadal
PLANNED. M5 i finalne W.4/W.5/M7 pozostają otwarte.
