# M2 — ExaFMM build i kontrola operatorów Maxwell

Status: mały CPU operator **PASS**; rozwiązanie PMCHWT, pola i antena **NOT RUN**
w tym backendzie. M2 pozostaje ACTIVE. Wynik nie kwalifikuje nowego solvera.

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

## Co pozostaje

Następny krok: rzeczywisty mały PMCHWT FMM vs dense, sprawdzenie residualu
również niezależnym operatorem oraz wektorów rozwiązania. Sekwencyjne zwalnianie
niezależnych testów **nie rozwiązuje** problemu przechowywania dwóch k dla
jednoczesnego operatora PMCHWT. Najpierw trzeba przygotować jawny budżet tablic
i ich cyklu życia bez dyskowego offloadu; unikać rebuildowania drzew co iterację.
Nie zakładać, że 1e-6 action gate wystarczy do frozen solve/field gates.

Pełna F3 norma, zbieżność referencji, rezonanse, scalable assembly i koszty
anteny pozostają niezaliczone. Ten CPU backend nie daje CUDA/Tensor Cores.
Dowody: `artifacts/m2-fmm-maxwell-o{6-n32,8-n32,8-sequential}-20261019/`
(case/command/container-state), EXP70–73 w PROGRESS.md.
