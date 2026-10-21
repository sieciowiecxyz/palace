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

## EXP117–119: compensated forward, osobny opt-in

2026-10-21, **quality PASS tiny/medium3,55; brak wykazanego netzysku, HOLD**.
To kolejny eksperyment po historycznym SHA EXP112–113 powyżej, nie ponowna
kwalifikacja tamtej binarki. Obecny sourceSHA
`76f1edfc309e73b993d9f17e2faf987e849a1ac493847976659dd71d87c775d7`.

Nowy `--pc-basis-compensated-forward` jest rozłączny z poprzednią flagą.
Ten sam RAII scope/cache/release, jednak tylko P20/Q14/QC3 nonTensorforward,
N≥8192; pozostałe kształty, transpose/Add i outsidePC oryginalne. Minimum
odziedziczone z poprzedniego adaptera; tinyN13086 testuje obszar między punktami
4099/16383 drabinki, nie dowód uniwersalnego crossoveru. Kernela z
[EXP115–116](ceed-tensor-probe.md) używa zarówno adapter, jak i actionprobe:
`tools/adapter/ceed_compensated.cuh`. FP32hi/lo coeff/input/accumulation,
guarded bit-split oraz FP64 fallback dla wejść poza zakresem i recombine;
nie pełne FP64, nie Tensor Cores. Oryginalne A/rawresidual FP64.

Exact-content cache dwie tablice/shape, mode raportowany w audycie, cap256.
Dla rzeczywistego testu2entries/13440Ballocated=freed/live0/release1. Nie dodaje
wielkich wektorów ani nie przełącza na FGMRES. Przywrócenie: pominąć nową flagę;
fallback sprzed zmian w build/m6-pc-compensated/pre-compensated-native oraz
pre-compensated-manifest.json. Cached nativebuild8,582s, bez rebuilda dependencies.

EXP117 wykrył błąd integracji: adapter znał nową flagę, ale native ApplyB i
finalrelease sprawdzały tylko starą. Candidate fields PASS, lecz0scope/mixedcalls
unieważniło run — **FAIL**, nie dowód jakości ani speedupu. Poprawiono obie
bramki, dodano regresje, EXP118 wykonał rzeczywistą ścieżkę. Przypadek FAIL
pozostaje w artifacts/m6-pc-compensated-tiny-on-20261021.

| Same-build oba porty | Kontrola | Compensated | Iteracje |
| --- | --- | --- | --- |
| Tiny, EXP118 | 16,533s | 16,629s | 40/42 → 40/42 |
| Medium3,55, EXP119 | 98,577s | 98,546s | 47/49 → 47/49 |

Jedna para, nie mediana; różnica medium0,03s nie dowodzi speedupu. Native
exclusive PCtimer5,412→5,347s, coarse1,756→1,761s. Nie sumować PC/coarse ponownie
z Total. Około70s tego filtra pochłania dodatkowa analityczna kwadratura L2;
wykonano ją identycznie dla obu ścieżek, bez ukrywania kosztu walidacji. Nie
przenosić udziałów tego coax na antenę/UVM. Nie wykazano redukcji pamięci:
cgroup tiny577,671→586,834MB/medium1910,899→1919,173MB, processGPU631,243MB
w obu — ten licznik nie jest fizyczną rezydencją UVM.

Root niezależny CSV: tiny maxΔS1,708e-9/ΔVSWR3,321e-9/relativeenergy3,322e-9/
power3,305e-9, fieldsE/B≤1,040e-6/1,672e-8. Medium1,228e-10/1,484e-10/
1,308e-10/1,243e-10, fields≤1,242e-7/6,889e-8. Rawfinal tiny8,46e-7/7,74e-7,
medium9,57e-7/9,12e-7. Wcześniejsze raw-recurrencegaps medium~1,2–1,3e-5
zbliżone do kontroli~1,3e-5, bez wcześniejszego~1e-2. To zgodne z hipotezą
liniowości, nie izolowany dowód przyczyny: zmieniono także selekcję baz.

Audyt actualtiny85/85scope/mixed3400 i medium100/100/mixed4000,
outsideoriginal3582/4066, transposeoriginal7650/9000, cachecleanup PASS.
153pinnedtestsPASS. Wszystkie hotbuffers RAM/VRAM, noSwap. Zwykłe zapisane
wyniki candidate tiny8,982MB/medium85,317MB (w tym pola6,737/63,490MB),
jednorazowe snapshoty do porównania; brak zapisu workspace w pętli.

Odtwarzanie: komenda powyżej, ale zastąpić ostatnią flagę przez
`--pc-basis-compensated-forward`; nowe katalogi wyników. Kontrola bez obu flag.
Dowody: artifacts/m6-pc-compensated-tiny-{control-v2,on-v2}-20261021 i
m6-pc-compensated-medium-{control,on}-20261021, root-analysis JSON dla obu.

Decyzja: nie promować i nie wykonywać automatycznie drogiego W.3 dla obecnego
~12% microzysku bez wykazanego netzysku. W.2 pozostałefreq/W.3 NOTRUN; brak
kwalifikacji pełnej anteny. W M6 priorytet następny to audyt istniejącego sweep/
PROM/reuse (M6.6) i rachunek całkowitego kosztu. Dotychczasowy FP64 basis
+M5mixedcoarse pozostają wariantem odniesienia. M6/M7/goal nadal otwarte.
