# M2 — niezależny Maxwell i próba kompresji

2026-10-19: **PEC oracle PASS; prosty H-matrix CUDA apply niepromowany**.
M2 otwarty: brak dielektryka, interfejsu FEM–BEM i kosztu anteny. Palace,
medium i kontrakt K bez zmian. Te wyniki nie dotyczą portów anteny.

## Źródła i wybór

Audyt przypiętych lokalnych źródeł upstream, 2026-10-19:

| Implementacja / rewizja / licencja | Dowód i decyzja |
| --- | --- |
| [Bempp-cl](https://github.com/bempp/bempp-cl/tree/a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0), `a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0`, 0.4.2, MIT | `api/operators/boundary/maxwell.py`: EFIE/MFIE/multitrace; `core/numba_kernels.py`: singular/far-field kernels; `api/space/maxwell_spaces.py`: RWG/SNC/BC. Numba CPU/OpenCL, nie native CUDA. Wybrany jako CPU oracle, bez zależności w Palace. `examples/maxwell/maxwell_dielectric.py` dostępny, ale NOT RUN; MFEM trace/porty niepotwierdzone. |
| [H2Opus](https://github.com/ecrc/h2opus/tree/cbc7985d9716e015c019003073a6f1f5c53dd2fc), `cbc7985d9716e015c019003073a6f1f5c53dd2fc`, BSD-3-Clause | `include/h2opus/core/h2opus_defs.h:21–26`: H2Opus_Real double/float, CUDA/MAGMA/KBLAS. Nie znaleziono gotowego zespolonego Maxwell. Potrzebna reprezentacja zespolona lub osobne real/imag; nie zakładać drop-in complex/TF32 i nie budować pełnego stosu przed wykazaniem sensu. |

**RAM-only:** `bempp_cl/api/fmm/exafmm.py` tworzy `cwd/.exafmm/*.tmp`
i przekazuje filename do ExaFMM. Domyślne użycie na dysku zabronione.
Oracle jawnie `assembler='dense'`, bez ExaFMM; cwd i `/tmp` są tmpfs,
root read-only. Przyszły FMM wymaga audytu całego backendu.

## Odtworzenie

```sh
python3 tools/experiments/bempp_oracle.py setup
python3 tools/experiments/bempp_oracle.py check
python3 tools/experiments/bempp_oracle.py run artifacts/m2-pec-new --level 3 --seconds 120
python3 tools/experiments/bempp_oracle.py run artifacts/m2-compressed-new --level 3 --seconds 180 --compression
```

Nowe katalogi wyników. Prywatny Python3.12.15 `build/m2-oracle/venv`,
wersje w `tools/experiments/bempp-requirements.txt`; manifest weryfikuje rewizję,
wersje, SHA kodu Bempp/interpretera i przypięty runtime CUDA12.9.1.
Cache uv/wheels/Numba i checkouty `.cache/m2-sources` zachowane. Kod kompilowany
to cache; macierze/wektory wyłącznie RAM/VRAM, bez dumpów jako mostu między
etapami. Brak przebudowy Palace/zależności.
Kontener:4CPU/6GiB/no additional swap/network none, limit≤180s, read-only root,
tmpfs512MiB osobno `/tmp` i `/scratch`, cleanup także przy błędzie.
GPU tylko `--compression`, bez zamykania aplikacji.

Pierwszy `m2-pec-sphere-level1-cold-20261018`: FAIL launch0,19s/exit127/Pid0.
Mount realnego Pythona nie obejmował aliasu uv używanego przez venv;
naprawiony mount+regresja. Nie był to wynik numeryczny.

## PEC i niezależne odniesienie

EFIE RWG/SNC complex128, CPU Numba dense, quadrature regular/singular4.
Kula ka=1; exp(−iωt), Einc=x̂exp(ikz), outgoing exp(ikr)/r. Ślad Einc×n
i minus przed scattered potential według przypiętego `examples/maxwell/maxwell_screen.py`.
**Bez dopasowania fazy/amplitudy.** `tools/maxwell_reference.py`: niezależny Mie
i seria Bessela; cross-check SciPy dla ka0,1/1/2,5 daje max4,28e−16.
Testy Rayleigh/optical theorem/orientacji/zamknięcia siatki. Pole complex L2
ważone16×24 kierunkami, przekrój rozpraszania i bilans energii: próg1%;
algebraiczne raw≤1e−10. Execution i analytic target raportowane osobno.

| Level / DOF | Czas runnera | Pole complex L2 | Przekrój rozpraszania | Bilans energii | Próg1% |
| --- | --- | --- | --- | --- | --- |
| 1 / 120 | 19,32s | 8,899% | 14,855% | 3,51e−8 | FAIL |
| 2 / 480 | 19,81s | 2,254% | 3,838% | 4,42e−10 | FAIL |
| 3 / 1920 | 33,89s | 0,5643% | 0,96565% | 5,65e−12 | PASS |

Artefakty pod `artifacts/`: `m2-pec-sphere-level1-cold-r2-20261019`,
`m2-pec-sphere-level2-20261019`, `m2-pec-sphere-level3-20261019`.
Exit0/noOOM; raw2,02e−15/3,92e−15/8,77e−15. Zbieżność około4× przy podziale
krawędzi na pół. Nie obniżono progów. Level3 matrix58,9824MB/RSS452,096MB,
LU0,2256s. Czas runnera obejmuje start/importy/JIT/wyniki, nie jest benchmarkiem
anteny ani kontrolowanym cold/warm porównaniem.

## Kompresja i prawdziwy CUDA apply

`tools/experiments/maxwell_hmatrix.py`: binary cluster tree z bounding boxes
**całego wsparcia RWG**, dokładny nearfield, complex SVD tylko rozdzielonych
wsparć. Leaf64/eta2/lokalny Frobenius tail≤1e−6. Prosty H-matrix, nie H²/FMM.
Pełna macierz CPU nadal powstaje i pozostaje w RAM.

Artefakt `artifacts/m2-pec-hmatrix-cuda-level3-20261019`:

| Pomiar | Wynik |
| --- | --- |
| Execution / analytic base / relative compression quality | PASS/PASS/PASS,40,868s,noOOM |
| Bloki / skompresowane | 984 / 248 |
| Matrix dense → compressed | 58,9824 → 53,5795MB (**−9,16%**) |
| Compression / CPU compressed GMRES | 0,1556s / 0,6423s,170iter |
| Max matvec error (solution+3random vectors) | 1,586e−9 |
| Raw w **oryginalnym** układzie / Δsolution | 1,591e−9 / 2,275e−8 |
| Δfar-field / błąd względem Miego | 1,096e−11 / 0,5643% |
| CUDA explicit allocation dense → compressed | 59,0439 → 53,6414MB |
| CUDA mean apply round-trip dense → compressed | 0,1010 → 5,3194ms (**52,68×wolniej**) |
| RSS procesu z kopiami/oracle/CUDA | 1,404GB; brak oszczędności peak RAM |

Progi ustalone przed runem: action1e−5/rawOriginal1e−6/Δsolution1e−3/
Δfar-field1e−4; spełnione. CPUoracle osobno sprawdza1%Mie/energię.
CUDA: `cudaMalloc`, complex128 `cublasZgemv_v2`, bezUVM/TC. Alokacje zwalniane
między wariantami,4wektory kontrolne+8timed apply tego samego x. Czas obejmuje
Python dispatch/PCIe/sync, nie tylko kernele; explicit bytes nie obejmują
kontekstu ani wewnętrznego workspace cuBLAS. GPU służy **apply**, GMRES był CPU.
API/layout: [cuBLAS](https://docs.nvidia.com/cuda/archive/12.9.1/cublas/index.html#cublas-t-gemv),
column-major, host scalars, default stream. Brak zmiany precyzji.

**Decyzja:** nie integrować per-block dispatch jako speedupu. Mała kompresja
i setki wywołań przegrywają z dense. Nie odrzuca to dużego skompresowanego BEM;
nie ekstrapolować9%/53×na antenę. Następne: grupowane/natywne CUDA apply,
skalowanie rang/kosztów, dielectric Mie i mały FEM–BEM interface. Następnie
assembly bez pełnego dense, pamięć/workspace i porównywalny błąd anteny.
PEC PASS nie zamyka M2.2, nie uprawnia do promocji ani przejścia doM3.
