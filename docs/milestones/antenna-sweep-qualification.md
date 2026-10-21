# M6.6 — kwalifikacja siedmiu punktów rzeczywistej anteny

Status: ACTIVE;2026-10-21. Medium/frozen fixture T-Shaped, nie produkcyjna
najlepsza geometria z repo anten. [Bramki](../../MILESTONES.md),
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
| 3,30 | 752,534 / 60,692 | 549,512 / 46,357 | PASS | EXP153–154 |
| 3,40 | — | — | NOT RUN | następna para |
| 3,50 | — | — | NOT RUN | wcześniejsze scopedW3 nie zastępuje tej pary |
| 3,60 | — | — | NOT RUN | — |
| 3,70 | — | — | NOT RUN | projection3IR timeout nie jest tym wariantem |
| 3,80 | — | — | NOT RUN | — |
| 3,90 | — | — | NOT RUN | poza n78, punkt benchmarku |

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
