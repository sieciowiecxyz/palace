# M2 — decyzja po ocenie prototypów

**Ocena zamknięta: REJECT integracji obecnych prototypów.** Nie jest to zaliczenie
ich bramek numerycznych. Działającym solverem anteny pozostaje referencyjny FEM.
M3 można rozpocząć zgodnie z istniejącą zasadą PLAN: negatywna ocena z dowodami
zamyka hipotezę, bez wymuszania integracji. Cel całego projektu nadal otwarty.

## Audyt zakresu M2

| Wymaganie | Dowód i rezultat | Decyzja |
| --- | --- | --- |
| M2.1 implementacje/backends | Przypięty Bempp0.4.2/ExaFMM0.1.1, audyt H2Opus real-only, native CUDA Maxwell apply; raporty oracle/native/coupling | Research wykonany; brak gotowej kwalifikowanej CUDA FEM–BEM dla tego feedu |
| M2.2 fizyka i sprzężenie | PEC/Mie0,564% PASS, dielectric PMCHWT/Mie0,0223% PASS; transparentne ND2 F2/B3 E/H0,560/0,751% PASS | Częściowe kontrole PASS, pełna transmisja niezakwalifikowana |
| M2.2 pełna norma/zbieżność | F3degree5 E/H1,683/0,972%, zmiana referencji1,725/0,876%; degreeagreement FAIL | FAIL pozostaje FAIL; brak promocji |
| M2.3 koszt/rozmiar | Dense trace94200DOF≈132GiB; dense B5≥7,55GB przedLU ponad6GiBcap; GPU H-matrix −17,31% matrixdata, nie peak; per-block/native apply bez korzyści całej anteny | Oszacowania i lokalne pomiary wystarczają do odrzucenia; brak kwalifikowanego speedup przy zgodnym błędzie |
| M2.3 FMM solve | EXP74–76: rzeczywisty matrixfree PMCHWT/GMRES, niezależny dense residual; poniżej | Frozen residual gate FAIL, nawet przy większym koszcie p9 |
| M2.4 integracja/odrzucenie | Kontrole jakości niekompletne/FAIL, brak zmierzonej korzyści anteny, porty/cienkie PCB metale niezaimplementowane w prototypie | REJECT obecnej integracji, zachować kod i FEM fallback |

Negatywna decyzja **nie** twierdzi, że FEM–BEM/MoM jest niemożliwe lub ogólnie
wolniejsze. Nie wykonano kosztowego benchmarku całej anteny przy zgodnym błędzie,
bo kandydat wcześniej nie przeszedł jakości. Nie wykonywać takiego benchmarku
tylko po to, by mieć czas mimo niewiarygodnego wyniku.

## Pełne małe rozwiązania FMM

B2,240 niewiadomych PMCHWT, εr2,94,quad4,complex128. Każdy run ma niezależną
gęstą referencję o raw2,47e-15. GMRES rtol1e-10, jeden cykl32; frozen raw<1e-9,
różnica współczynników<1e-6. Bez GPU/płatnego compute/przebudowy Palace.

| Run | Wariant | Iteracje/info | Raw FMM | Raw niezależne | Δcoeff | Solve / cały run |
| --- | --- | --- | --- | --- | --- | --- |
| EXP74 | p8, bez PC | 32/1 | 1,802e-2 | 1,802e-2 | 6,484e-2 | 52,868 /81,259s |
| EXP75 | p8, near-ILU | 26/1 | 9,464e-10 | 1,302e-7 | 3,850e-7 | 43,060 /71,560s |
| EXP76 | p9, near-ILU | 26/1 | 9,464e-10 | 1,272e-8 | 3,004e-8 | 59,005 /88,396s |

Info1 oznacza brak osiągnięcia zadanego stopping criterion; dodatkowo niezależny
residual nie przechodzi1e-9. Nie raportować skrócenia EXP75 jako speedupu poprawnego
solve. PC bierze tylko exact adjacent-panel singular_part, bez wpisów gęstej
referencji i bez odwracania osobliwej macierzy Gram RWG/SNC. Macierz PC260164B,
ILU793488B; nie jest to budżet pełnego procesu ani dużej anteny.

Obie fale mają osobne istniejące512MiB tmpfs RAM (`/scratch`,`/tmp`), bez swapu
i SSD scratch. P8 tabela302215176B; p9 tabela453578504B; stan końcowy obu0B.
RSS wspólny z dense oracle:718/721/901MB dla EXP74/75/76. Nie obejmuje
pełnego kosztu tmpfs/page cache ani nie zastępuje szczytu cgroup; nie zmierzono
tutaj osobnego całkowitego FMM-only peak. P10 przewidywane
654602248B na tabelę przekracza limit pojedynczego tmpfs: **NOT RUN**.
Preflight budget i dokładna kontrola długości pliku zapobiegają powtórce EXP72.

## Co zachowujemy i co dalej

Źródła, licencje, cached addon, referencje i wyniki zostają. Zamrożone bramki
M2.2/M2.3 nadal obowiązują, jeśli wrócimy do kandydata; żaden FAIL nie został
przeklasyfikowany na PASS. Szczegóły: [FMM](../maxwell-fmm.md),
[stream/volume](../maxwell-stream.md), [coupling](../maxwell-nd2-coupling.md).

Aktywny M3: bezpośrednie operacje na bazie FP32 w istniejącym solverze FEM,
FP64 redukcje/residual i wariant referencyjny. To lokalna zmiana bez rozbudowy
modelu fizycznego i bez zależności od niezakwalifikowanego backendu BEM.
