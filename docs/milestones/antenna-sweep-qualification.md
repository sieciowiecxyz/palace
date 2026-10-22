# M6.6 — kwalifikacja siedmiu punktów rzeczywistej anteny

Status: **7/7 PASS, ocena M6.6 zakończona**;2026-10-21. Medium/frozen fixture T-Shaped, nie produkcyjna
najlepsza geometria z repo anten. [Bramki](optimization-contract.md),
[historia sweepów](sweeps.md). Nie zamyka M6/M7 przed wymaganymi dowodami.

## Protokół

Siedem częstotliwości3,3..3,9GHz/0,1, oba porty. Bounded chunks po jednej f,
żeby każda para mieściła się w limicie1800s/run. Suma czasów obejmuje wszystkie
powtórne setupy, wejścia/wyniki i cleanup; nie jest czasem monolitycznego sweepu
ani dowodem cross-chunk continuation. Per-port/history proof dla2f istnieje
osobno w EXP130. Nie ukrywać narzutu chunków.

Referencja: pełna baza FP64, arytmetyka FP64, native complexFP64 coarse,
RIGHT/K64/Tol1e-6, coldstart, bez portreuse. Kandydat: directFP32 storage przy
FP64 arithmetic, scaledcomplexFP32LU/default2fixedFP64corrections i reuse
setupu między dwoma RHS tego samego f. To ocena całej wybranej kombinacji,
nie izolowany efekt jednej flagi. W obu wariantach ten sam build/config/mesh/
terminacje, defer/releasepostprocess/finalsolver i zwykłe snapshoty.
60GiB cap/noSwap/6GiB available guard; brak płatnego compute/zamykania aplikacji.

Referencja musi ukończyć oba RHS/raw≤1e-6 i inventory+config/source checks.
Dopiero wtedy kandydat z --field-reference do tej prawdziwej referencji.
FrozenK: maxΔcomplexS≤1e-3, ΔVSWR≤.01, power≤1e-3, relativeenergy≤1e-3,
E/B energy-norm≤1%, originalraw≤1e-6, mixedcoarseraw≤1e-3. Błędy/timeouty
pozostają FAIL, bez automatycznego retry lub luźniejszych progów.

## Wyniki

Czas end-to-end, pamięć cgroup w dziesiętnychGB; GPUprocesscounter nie mierzy
pełnej fizycznej rezydencji UVM. Jedna para, nie mediana/statystyczna promocja.

| GHz | Referencja s / GB | Kandydat s / GB | K | Status |
| --- | --- | --- | --- | --- |
| 3,300 | 752,534 / 60,692 | 549,512 / 46,357 | PASS | EXP153–154 |
| 3,400 | 696,169 / 60,687 | 507,593 / 46,359 | PASS | EXP155–156 |
| 3,500 | 736,489 / 60,703 | 594,697 / 46,358 | PASS | EXP157–158 |
| 3,600 | 738,779 / 60,870 | 664,138 / 46,460 | PASS | EXP159–160 |
| 3,700 | 739,628 / 60,865 | 687,162 / 46,454 | PASS | EXP161–162 |
| 3,800 | 736,468 / 61,048 | 524,307 / 46,548 | PASS | EXP163–164 |
| 3,900 | 723,949 / 61,224 | 515,685 / 46,637 | PASS | EXP165–166 |

3,3GHz:87→89outeriter (43/44→44/45),2→1faktoryzacja,
czas−26,98%,cgroup−23,62%. Rawcandidate≤8,19e-7, coarse≤1,30e-4.
14regionalfieldrows E/B≤1,298e-7/1,137e-7;
ΔS≤1,186e-8/ΔVSWR≤3,888e-8/relativeenergy≤5,925e-8/power≤5,024e-9.
Więcej iteracji nie przekreśliło zysku całego runu; nie sumować procentów
z wcześniejszymi osobnymi eksperymentami.

## Odtworzenie pierwszej pary

Każdy output nowy, ta sama native rewizja dla obu uruchomień.

```sh
python3 tools/dev.py run tshaped-medium artifacts/NEW-330-reference \
  --seconds 1800 --basis fp64 --pc-side right --krylov-size 64 \
  --native-complex-coarse --hypre-pool-mib 256 --memory-marks \
  --release-gmres-basis --release-final-solver --setup-audit --save-fields \
  --both-ports --frequencies 3.3 --release-postprocess-energy --defer-postprocessing
python3 tools/dev.py run tshaped-medium artifacts/NEW-330-candidate \
  --seconds 1800 --basis fp32 --direct-basis --pc-side right --krylov-size 64 \
  --native-complex-coarse --native-coarse-fp32 --hypre-pool-mib 256 --memory-marks \
  --release-gmres-basis --release-final-solver --setup-audit --save-fields \
  --both-ports --frequencies 3.3 --release-postprocess-energy --defer-postprocessing \
  --port-setup-reuse --field-reference artifacts/NEW-330-reference
```

Artefakty EXP153–154 `artifacts/m6-qualified-330-{reference,candidate}-20261021`,
root-reference-check i rootreceipt`artifacts/m6-qualified-330-root-analysis-20261021.json`;
replay`artifacts/m6-qualified-root-analysis.py 330` (lokalny zachowany skrypt).
SourceSHAa6ec732f11cc7fe920365ba2aae354b68fe97e81f732d5afd4659ed5187c3338.
W.4/W.5/trzy mediany/istotnie inna geometria/pakiet M7 nadal wymagane.

## Suma siedmiu chunków i granice

Referencje5124,017s (85,4min), kandydaci4043,095s (67,4min): **−21,095% czasu,
1,267×** w tym wykonanym zestawie. Maksymalny cgroup61,224→46,637GB
(**−23,825%**, około14,59GB mniej). Nie sumować peaków ani średniej procentów;
czas to suma całych zadań, pamięć to maksimum. 625→635outeriter,14→7setupów.
98regionalfieldrowsPASS, max E/B5,678e-7/1,597e-7,
maxΔS3,255e-8/ΔVSWR9,189e-8/relativeenergy8,011e-8/power9,416e-9.
Wszystkie originalraw≤1e-6 i coarse≤1e-3; reliable corrections są w czasie,
nie ignorowano pierwszych nieudanych stopping checks w3,6/3,7/3,8.

To porównanie całej kombinacji przeciw fullFP64, jeden pomiar per f/strategię.
Nie dowodzi median, ciągłego pasma, monolitycznego sweepu, jakości fizycznej
projektu ani generalizacji na nową geometrię. 3,9GHz jest poza n78.
Zapisane artefakty~16,48GB łącznie (inputmesh/snapshoty/wyniki do walidacji),
jednorazowo na run; brak roboczej bazy/macierzowego workspace na SSD.

Wersjonowany `tools/qualify_antenna.py` ponownie sprawdza surowe logi, inventory,
source/config/nativeprecision/reuse/raw oraz complexS/VSWR/power/energy/fields.
Summary odtwarza każdy pair z jego rzeczywistych inputpaths, nie ufa cached
passed=true. Odrzuca duplikaty/braki, różne buildy/mesh/config poza częstotliwością.
Nie uruchamia symulacji ani nie promuje defaultów.

```sh
python3 tools/qualify_antenna.py \
  artifacts/m6-qualified-340-reference-20261021 \
  artifacts/m6-qualified-340-candidate-20261021 \
  --output artifacts/NEW-340-check.json
python3 tools/qualify_antenna.py --summary \
  artifacts/m6-qualified-330-check-20261021.json \
  artifacts/m6-qualified-340-root-analysis-20261021.json \
  artifacts/m6-qualified-350-root-analysis-20261021.json \
  artifacts/m6-qualified-360-root-analysis-20261021.json \
  artifacts/m6-qualified-370-root-analysis-20261021.json \
  artifacts/m6-qualified-380-root-analysis-20261021.json \
  artifacts/m6-qualified-390-root-analysis-20261021.json \
  --expected-frequencies 3.3 3.4 3.5 3.6 3.7 3.8 3.9 \
  --output artifacts/NEW-seven-summary.json
```

Dowód zbiorczy`artifacts/m6-qualified-seven-summary-20261021.json`,
per-point receipts i pełne źródłowe runyEXP153–166.170Python testsPASS, w tym
kontrole niewłaściwych jednostek/kolejności, NaN, uszkodzonego coverage, fazy
±360°, zera energii i błędnych sum/peaków. Standardowe benchmarki małe są
oddzielne od tej kosztownej końcowej kwalifikacji.
M6assessment zakończonyEXP176, scopedWMMA TCproofPASS/directPCfilterFAIL; goal nieukończony. AktywnyM7: docs/milestones/M7.md. Powyższe wyniki tofixed2IR; explicit --corrections3 ma osobną kwalifikację i nie może być mieszany wsummary2IR.
