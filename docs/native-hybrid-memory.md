# M5 — cuDSS hybrid memory, EXP95–96

Stan2026-10-21: implementacja opt-in poprawna numerycznie, **REJECT jako obecny
wariant przyspieszający**. UVM/FP64 pozostaje referencją. Aktualne zamknięcie
oceny M5 i późniejszy mixed opt-in opisuje docs/milestones/M5.md.
Wyniki to benchmark obecnej geometrii na5070Ti, nie uniwersalny ranking trybów.

## Przypięty stos i tryby

CUDA12.9.1, cuDSS0.7.1.4 (actual cudss.h0.7.1), MFEM4.9, jeden rank/GPU.
Źródła: `tools/runtime.json`, `complexcudss.cpp`, `cuda_memory.cpp` i actual API.
[Archiwalna dokumentacja NVIDIA](https://docs.nvidia.com/cuda/archive/12.9.1/cudss/advanced_features.html),
sprawdzona2026-10-21: hybrid memory przenosi część faktorów do hostRAM, compute
zostaje na GPU; hybrid execute dopuszcza CPU i jest osobnym trybem. W tej wersji
nie łączymy ich. Hybryda ma synchronizacje i ograniczenia algorytmów reordering.
Nie używamy MGMN ani nie zmieniamy biblioteki/formatu faktorów.

| Tryb | FEM/GMRES | cuDSS workspace | Compute coarse | Status |
|---|---|---|---|---|
| UVM/nativeFP64 | managed GPU↔RAM | managed | GPU FP64 | fallback |
| native hybrid memory | managed GPU↔RAM | device cudaMalloc + host factors | GPU FP64 | EXP96, niepromowany |
| hybrid execute | osobny stary CPU reference | osobna polityka | CPU/GPU | niełączony z native memory |
| FP32 faktory/TF32/BF16 | brak w tej próbie | nie zmieniano precyzji | brak dowodu TC | nadal osobna hipoteza |

## API i minimalny budżet

Actual512DOF known-solution probe: native complexGENERAL i realny2N/SYMMETRIC,
2RHS/2updates. UVM,256/512MiB: independenthosterror≤1,251e−13, cleanup0B.
To mała walidacja API; faktory mieściły się w obu budżetach, nie benchmarkoffload.

Pierwszy native medium256MiB FAIL/error3 przed minmarker. Wersja v2 ustawia
HYBRID_MODE przed analizą, ale limit dopiero po odczycie MIN/MEMORY_ESTIMATES
(przed factor). Sprawdza actualconfigGet, limit, query sizes i dtypeFP64.
- Medium minimum716326660B, hostestimate3499154496B:256MiB odrzucone przedfactor.
- Antena minimum3901173764B, hostestimate32714788656B:diagnostic95,310s,
  256MiB odrzucone przedfactor. To oszacowania biblioteki, nie pomiar szczytu RAM.
- Bez silentfallback/budgetraise. Nieukończone runy mają complete=false i nie są RFref.

## Zmierzone pełne zadania

Ten sam build/config,35iter, antena3,50GHz/P2, to samo zweryfikowane E startowe.
Jeden pomiar na tryb, nie mediana ani kwalifikacja obu portów/pasma.

| Polityka | Czas s | Peak cgroup GB | Śledzony cuDSS peak GB | Gdzie cuDSS |
|---|---:|---:|---:|---|
| UVM |350,371|56,023|25,008|managed, nie pełna rezydencja GPU|
| Hybrid4GiB |363,872|55,449|4,295|device; host dodatkowo|
| Hybrid6GiB |511,069|55,435|6,442|device; host dodatkowo|

Wszystkie raw||Ax−b||/||b||≤8,357e−7, wholefields7regionsPASS,
maxΔS4,777e−10/energyrelative9,266e−10. Brak fizycznej walidacji anteny.
Coax-medium3,55GHz/oba porty:768/1024MiB108,160/108,881s vsUVM101,893s,
45/47iter; pola/TEM/S/energiaPASS, cgroup4,223/4,240 vs2,598GB.

Exclusive block timers W3P2 (nie dodawać ponownie do całego czasu):

| Polityka | Setup s | PC poza coarse s | Coarse s | Pozostały LinearSolve s |
|---|---:|---:|---:|---:|
| UVM |87,021|97,153|63,413|23,871|
| 4GiB |90,368|139,709|31,437|22,201|
| 6GiB |125,485|248,494|31,445|26,034|

Coarse wywołania przyspieszyły około2×, lecz pozostały PC zwolnił; brak całkowitego
zysku. Suma rozłącznych timerów zgadza się z Total do około0,1s; runner obejmuje
też narzut uruchomienia. Wypieranie innych danych przez stały deviceworkspace
jest hipotezą przyczyny, nie zmierzonym tutaj wolumenem migracji. Nie twierdzić,
że większy limit GPU zawsze pomaga ani że spadek managed oznacza spadek RAM.

## Używanie i granice

`tools/dev.py run ... --native-complex-coarse --cudss-hybrid-mib 4096`;
budżet256..16384MiB, ale rzeczywista wykonalność zależy od minimum i wolnegoGPU.
Nie łączyć CPU/hybridexecute/profiler/FP32factors. Marker REQUIREMENT to nie APPLIED;
runner wymaga actualconfig/countperbuild i allocatorlive0. Domyślnie flaga wyłączona.
Deadline i no swap bez zmian; brak SSDworkspace i zamykania aplikacji.
Buildy: cached1TU+adapter około11s, bez depsrebuild. Fallback
`build/m5-hybrid/pre-hybrid-native`. Płatny compute nieużywany.

Receipts: `artifacts/m5-hybrid-{medium,antenna}-root-analysis-20261021.json`;
API `m5-hybrid-api-{uvm,256,512}-20261021/`; actualjobs
`m5-hybrid-antenna-p2-{uvm,4096,6144}-20261021/`. Rejected256/v1 preserved.
Następny kierunek M5: źródłowo sprawdzone AMS/iterativecoarse lub nowa polityka
pamięci z profilem. Bez kolejnych losowych budżetów; W.4/W.5/M7 nadalNOTRUN.
