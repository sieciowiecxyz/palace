# M2 — ExaFMM build i kontrola operatorów Maxwell

Status: mały CPU operator **PASS**; rzeczywiste PMCHWTsolve EXP74–76 **FAIL**
niezależnego residuum. Ocena M2 zamknięta decyzją REJECT integracji:
[decyzja](milestones/M2-decision.md). Wynik nie kwalifikuje nowego solvera.

## Odtwarzanie i cache

`python3 tools/experiments/exafmm_build.py build` buduje wyłącznie prywatny addon
ExaFMM, bez przebudowy Palace/MFEM. `check` sprawdza manifest i sumy artefaktów.
Źródło exafmm-t v0.1.1: commit `78b7d56f988b3843ba502faf4ac60b0c013aa206`,
licencja BSD-3-Clause według LICENSE (metadata setup.py mówi MIT).
Prywatne nagłówki pybind11 2.13.6; venv i Bempp pozostają bez zmian.
Przypięty mały builder Ubuntu24.04/FFTW/OpenBLAS, ccache, osobny compile/link;
FP64/complex128, bez fastmath. Manifest obejmuje receptę, źródła, ABI,
obrazy i prywatne biblioteki. EXP70: build21,455s, EXP71 repeat cache-no-op0,105s.
Nie usuwać cache ani zastępować tego pełnym rebuildem zależności.

Duży historyczny builder nie wystartował w próbach cap6GiB; tekst OCI
„OOM-killed?” nie potwierdza host OOM. Nowy mały builder działa w tym limicie.

## Eksperymenty EXP71–73

120 RWG DOF na tej samej geometrii B2, 480 punktów źródeł i celów,
73 węzły/głębokość2. Maxwell T/K, k=1 i sqrt(2,94), regular/singular quad4,
ncrit32; trzy deterministyczne wektory complex128. Dense weak form jest małym
oracle. FMM stosuje operator do wektorów bez pobierania `.A` i bez dense fallback.
Zamrożona bramka względnego błędu akcji: **1e-6**.

| Run | p | max T error | max K error | Wynik |
| --- | --- | --- | --- | --- |
| EXP71 | 6 | 2,24e-6 | 1,95e-5 | FAIL dokładności |
| EXP72 | 8 | 0,2765 | 0,8360 | INVALID: tmpfs pełny |
| EXP73 | 8 | 4,67e-8 | 5,55e-7 | PASS akcji operatora |

EXP72: dwa zestawy tablic zapełniły512MiB RAM tmpfs; drugi plik został
ucięty. Pinned `include/fmm.h::precompute` nie sprawdza błędu zapisu strumienia,
więc exit0 nie wykrył niewiarygodnego wyniku. Nie jest to błąd SSD ani dowód,
że p8 matematycznie zawodzi.

EXP73 zwalnia drzewo/cache oraz runtime plik po każdym **niezależnym** k,
używając upstream clear_fmm_cache/cleanup_fmm_tmp. Kontrola przed działaniem
operatora odrzuca pełny tmpfs. Nie kasuje source/build/JIT cache. Każda tabela
ma302215176B; szczyt obserwowanego użycia tmpfs302219264B, koniec0B.
Nie zwiększono512MiB limitu. Czas28,331s, wspólny RSS624742400B obejmuje dense
oracle i FMM; nie jest pomiarem samego backendu ani zyskiem anteny.

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-maxwell-o8-sequential-20261019 --physics fmm-control --level 2 --fmm-order 8 --fmm-ncrit 32 --seconds 120
```

Run6GiB/4CPU, swap wyłączony, sieć wyłączona, bez GPU/płatnego compute.
Robocze pliki ExaFMM wyłącznie w `/scratch` tmpfs; na dysku tylko zwykłe
małe wyniki i osobne cache software. Biblioteki FFTW/OpenBLAS są sprawdzane
w mapach procesu jako prywatne pliki przypiętego dodatku.

## PMCHWTsolve i granice

EXP74–76 wykonują prawdziwy FMM LinearOperator/GMRES vs niezależny dense solve.
Dwa k są zachowane jednocześnie: po jednej tablicy w istniejących512MiB RAM
mountach `/scratch` i `/tmp`, bez rebuildowania drzew co iterację. Na obu
wymagany tmpfs; preflight budżetu i dokładna długość tablic według pinned fmm.h.
P8depth2 tabela302215176B, p9 tabela453578504B, p10 przewidywane654602248B
przekracza512MiB i nie był uruchamiany. Oba mounty po runach puste.

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/new-fmm-pmchwt --physics fmm-solve --level 2 --fmm-order 9 --fmm-ncrit 32 --fmm-preconditioner near-ilu --seconds 120
```

Bez PC32iter daje raw0,018. NearILU z exact sparse adjacent-panel singular_part
skraca do26iter w jednym cyklu, lecz info1 nadal wskazuje nieosiągnięte rtol1e-10.
P8 niezależnyraw1,302e-7, p9 1,272e-8, oba FAIL frozen1e-9. Małe błędy
współczynników3,85e-7/3,00e-8 nie zastępują raw ani fizycznych pól.
Dokładne czasy/bytes/tabela porównań: [decyzja M2](milestones/M2-decision.md).

Kontrole pełnej F3 normy, zbieżności referencji, rezonanse, scalable assembly
oraz koszty anteny pozostają niezaliczone/NOT RUN. Ten CPU backend nie daje CUDA
ani Tensor Cores. Nie integrujemy go z anteną; źródła/cache/prototyp zachowane.

Dowody: `artifacts/m2-fmm-maxwell-o{6-n32,8-n32,8-sequential}-20261019/`,
`artifacts/m2-fmm-pmchwt-{o8,near-ilu,o9-near-ilu}-20261019/`
(case/command/container-state), EXP70–76 w PROGRESS.md. Historyczne SHA helpera
EXP71–75 są zachowane; kolejne dodane tryby/guards nie zmieniają ich manifestów.
