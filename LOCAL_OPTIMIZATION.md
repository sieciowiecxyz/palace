# Goal — lokalny Palace na RTX 5070 Ti

Cel: przyspieszyć rzeczywiste medium na 16 GB VRAM + 96 GB RAM, zachowując
ustalone kryteria poprawności. Etapy wykonywano kolejno; bez płatnego compute.
Wyniki i ograniczenia: [LOCAL_OPTIMIZATION_RESULTS.md](docs/local-optimization-results.md).

- [x] **M1 — sprzęt, źródła i referencje.**
  - Zbadano FP32/FP64, BF16/FP16/TF32 oraz możliwości Tensor Cores.
  - TechPowerUp: 403; oficjalne dane NVIDIA i dokumentacja bibliotek jako fallback.
  - Zamrożono mesh/config: P2/Tol1e-6/MaxIts1600/K240/PA1.
  - Kontrola: 3,3/3,55/3,8 GHz × oba porty; duża antena: 3,50 GHz/P2.
- [x] **M2 — pomiar kosztów.**
  - Timery etapów, NVTX/JSON, CUDA/CPU/RAM/VRAM, alokacje i UVM.
  - Odróżniono timery exclusive od inclusive oraz profil od benchmarku.
  - Profile małego modelu i wybranego dużego wariantu; narzut/zagubione zdarzenia
    Nsight jawnie opisane. Pełny page-fault tracing przekraczał bezpieczny RAM.
- [x] **M3 — buildy i hipotezy oparte na pomiarach.**
  - Opt-in pominięcie estymatora bez AMR; domyślne zachowanie zachowane.
  - FP32 cuDSS/UVM/hybrid/cold CSR, scalar FP32 basis arithmetic.
  - FP32 storage GMRES z FP64 arithmetic i reliable restart.
  - Dokładna baza FP64 na SSD jako lokalna referencja przy ograniczonym RAM.
  - Brak deklaracji użycia Tensor Cores bez dowodu instrukcji.
- [x] **M4 — poprawność i powtarzalność.**
  - Mały coax: zgodność z TEM, S i mocą; 3 powtórzenia kluczowych wariantów.
  - Duża antena: 3 pary zakończonych runów, identyczny native/image/mesh/config.
  - Root ponownie sprawdził surowe manifesty/results/complex S.
  - Każda para: deltaS≤1e-3, deltaVSWR≤0.01, delta outgoing power≤1e-3.
  - Każdy finalny solve: niezależnie przeliczona norma zatrzymania≤1e-6;
    brak OOM/hostguard abort. Surowa norma Ax-b raportowana oddzielnie.
  - Mediany 1194.812 s (FP64 basis SSD) / 955.176 s (FP32 basis).
  - Energie i strumień mocy zgodne; absolutny błąd budżetu~0.36% także w FP64.
  - FP32 faktory cuDSS na antenie odrzucone mimo dobrego małego testu.
- [x] **M5 — wariant, odtworzenie i dokumentacja.**
  - Wybrano FP64 faktory/operator + FP32 basis, MAGMA, UVM, no-estimator.
  - Przypięty obraz zawiera native solver i adapter; hashe sprawdzone w obrazie.
  - Test obrazu: 6/6 solve, TEM/S/power/residual PASS; tylko mount danych /work.
  - Reprodukowalne CLI/build/package, manifesty i qualification.json.
  - Deadline Podmana niezależny od launchera, guard dostępnego RAM i cleanup.
  - Raport rozróżnia FP64 SSD od all-GPU, cyfrowe S od walidacji fizycznej,
    zintegrowane energie od punktowej dokładności pól, logical UVM od rezydencji.

## Dowody

`artifacts/infra/local-optimization-20261018/`:
`final-antenna-campaign.json`, `m4-root-audit.json`, `qualification.json`,
`campaign-summary.json`, `antenna-energy-consistency.json`,
`antenna-power-budget.json`, `disk-repro-build/build.json`,
`disk-repro-build/runtime-image.json`, `packaged-image-coax-smoke/`,
`antenna-fast-nsight-light-240s/` i surowe pliki poszczególnych runów.

Nie zmieniono `.toolchain`, `.env`, geometrii anteny ani WNIOSKI.md.
Zachowano niezwiązane zmiany Vast i wcześniejszy build V100.
