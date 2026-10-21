# M6.4 — eksperymentalny forward FP32 tylko w preconditionerze

EXP112–113,2026-10-21. **Tiny i jeden mediumpunkt poprawne, brak wykazanego
zysku czasu; HOLD przed W.3.** Default nadal oryginalny FP64 basis.
150pinnedtestsPASS. Native source SHA
`4e2fa56ff6e4e69342ad302d3ec288bc35e4a5d6a23c237cb806b3f05a4dc611`.

## Implementacja i powrót

Opt-in `--pc-basis-fp32-forward`, wymaga native coarse/rightPC/final solver
release, bez CPU/profilera/Qpool/AMS/hybrid. Dotychczasowy mixed coarse
i directFP32 GMRES storage to osobne flagi. Wyłączenie nowej flagi zachowuje
dotychczasową arytmetykę. Binarki sprzed integracji z manifestem w
build/m6-pc-basis/pre-integration-native i pre-integration-manifest.json.
Cached build jobs2 trwał13,698s; bez rebuilda dependencies.

RAII guard ograniczony do ApplyB/B->Mult w iterative.cpp, z weak adapter hook.
Oryginalne A*x i kontrolne Ax−b poza nim. Adapter tools/adapter/pc_basis.cu:
tylko nonTensor forward, znane P/Q/qcomp, N≥8192; transpose/ApplyAdd i wszystkie
wywołania poza scope używają oryginalnego libCEED. Tensor/małe/unsupported/
nieprzedstawialne współczynniki/cachecapacity/alias wracają do oryginału przed
zmianą danych. Błąd API/CUDA przerywa; brak cichego fallbacku po błędzie kernela.
Pre/post device synchronization zapewnia konserwatywne zależności streamów.

Wspólny kernel tools/adapter/ceed_fused.cuh jest używany również przez wcześniej
sprawdzony action probe; jego hash dodany do probe recipe. FP64 caller x/y,
FP32 register FMA; bez pośrednich wektorów. Dokładny cache key to wymiary i treść
FP64 tablicy, nie adres CeedBasis; sprawdzone finite/float range. Maksymalnie256
małych tablic. Cache zwalniany po ostatnim solve przed końcowym pomiarem pól;
nie odwołuje się później do zniszczonych FE/basis handles. Po release PC scope
zabroniony. Bufory robocze RAM/VRAM, brak SSD workspace/swap.

Strict tools/pc_basis_audit.py wymaga jednego raportu, enters=exits/active0,
dodatnich rzeczywistych mixed/outside-original/transpose-original calls,
FP64callerABI, minN8192 i allocated=freed/live0/finalrelease1. To audyt hostAPI/
scope/cleanup, nie fizyczna rezydencja ani zastępnik bramek RF. Błąd unieważnia
kompletność; prawdziwe residuum i pola oceniane niezależnie.

## Wyniki tego samego buildu

Oba porty,3,55GHz,K64/right,directbasis/native scaledmixedcoarse,reuse/deferred
postprocessing/zwolnienia. Oryginalne medium/tolerancje bez zmian.

| Model | Kontrola | Kandydat | Iteracje control → candidate |
| --- | --- | --- | --- |
| coax-tiny | 16,512s | 16,617s | 40/42 → 45/45 |
| coax-medium | 99,580s | 99,592s | 48/49 → 55/57 |

Jedna para każdego typu, nie mediana M7. Medium brak wykazanego speedupu;
nie ogłaszać poprawy z małej różnicy pamięci/czasu. Cgroup1,919→1,926GB,
licznik GPU process631,243MB nie jest physical UVM residency.

Tiny niezależne CSV: max deltaS1,638e-9/VSWR3,163e-9/relative energy9,784e-9/
port power2,921e-9; weighted E/B≤7,372e-7/2,420e-7. Medium deltaS1,027e-10/
VSWR5,341e-11/energy1,002e-10/power1,234e-10, weighted E/B≤9,361e-8/1,109e-7.
Frozen K tych filtrów PASS. Same CSR fingerprint/build/reuse markers.

Audyt tiny:94enters/exits,4888mixed,3714outside-original,8460transpose-original;
3cache entries/8400B allocated=freed. Medium:116/116,8352mixed,4258outside,
10440transpose,4entries/8784B allocated=freed. Live0/release1/closed w obu.
To koszt małych własnych tablic, bez twierdzenia o redukcji VRAM całego modelu.
AuditJSON576/579B, jeden raport przy zakończeniu, brak per-call dyskowych logów.

## Dlaczego nie uruchamiamy jeszcze W.3

Prawdziwe residuum zadziałało jako zabezpieczenie: tiny pierwsze recurrence
stopy miały rawrelative2,736e-3/3,629e-4; po restarcie8,491e-7/7,504e-7.
Medium kandydat9,222e-3/1,011e-2, po restarcie7,872e-7/8,860e-7.
Kontrola medium również miała mniejszy gap1,518e-5/1,288e-5 przed restartem,
potem8,037e-7/9,239e-7. Nie zaakceptowano niskiej recurrence norm jako wyniku.

Hipoteza zgodna ze źródłem, jeszcze bez oddzielnego pomiaru defect B:
classic rightGMRES rekonstruuje x przy pomocy B(sum y_j v_j), natomiast Arnoldi
używa osobnych A*B(v_j). Dla dokładnie liniowego B te działania są równoważne.
FP32 input/accumulation zwiększa błąd liniowości numerycznej, a źle uwarunkowany
układ może go wzmocnić. To może tłumaczyć większy gap i dodatkowe iteracje;
nie dowód, że każda strata pochodzi wyłącznie z tego mechanizmu.

FGMRES zachowuje Z_j=B(v_j), ale obecna implementacja odrzuca FP32stored basis.
Dla W.3 ND11218724 jeden FP64 complexvector179499584B. Pojemność K64:
65V FP32≈5,834GB vs65V+65Z FP64≈23,335GB (+17,501GB). To rachunek pełnej
pojemności, nie zmierzony peak (alokacja jest stopniowa). Nie przełączamy
solvera bez testu pamięci i całego czasu; rozwiązanie problemu arytmetycznego
kosztem kilkunastu GB nie jest automatyczną optymalizacją na16GBGPU.

Decyzja: obecny wariant niepromowany, W.2 3,30/3,80 i W.3 NOT RUN po tanim
filtrze kosztu. Nie ma wniosku o speedupie/stracie pełnej anteny. Następny mały
prototyp: test homogeneity/superposition i **dokładniejszy mixed/compensated
FP32 dot** z referencją FP64 oraz całym kosztem, bez nowych dużych wektorów.
Samo obniżenie precyzji do TF32/BF16 raczej zwiększy tę trudność; to hipoteza,
nie zastępuje testu. Dopiero użyteczny filtr uzasadni kolejne K/W.2/W.3.

## Odtwarzanie

```sh
python3 tools/dev.py run coax-medium artifacts/NEW-pc-forward \
  --seconds 180 --basis fp32 --direct-basis --pc-side right --krylov-size 64 \
  --native-complex-coarse --native-coarse-fp32 --hypre-pool-mib 256 \
  --memory-marks --release-gmres-basis --release-final-solver --setup-audit \
  --port-setup-reuse --release-postprocess-energy --defer-postprocessing \
  --coax-fields --coax-l2 --save-fields \
  --field-reference artifacts/m6-pc-basis-medium-control-20261021 \
  --pc-basis-fp32-forward
```

Kontrola pomija ostatnią flagę; najpierw zweryfikowany same-build control.
Referencje dokładności i seed to różne role. Lokalne dowody:
artifacts/m6-pc-basis-{tiny,medium}-{control,on}-20261021 i
artifacts/m6-pc-basis-{tiny,medium}-root-analysis-20261021.json.
Goal/M6/M7 pozostają aktywne; te filtry nie kwalifikują produkcyjnej anteny.
