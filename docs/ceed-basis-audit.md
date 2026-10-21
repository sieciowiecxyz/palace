# M6.1 — rzeczywiste wymiary baz libCEED

EXP105–106, 2026-10-21. Metadane z rzeczywistych wywołań, nie benchmark TF32.
Native source SHA `a217334ae31f5df0a51953bc9e78bbc42cd4f3abab42121c95d0ecc59e4203ae`.

## Mechanizm i ograniczenia

`tools/adapter/ceed_audit.cpp` w istniejącym adapterze przechwytuje publiczne
CeedBasisApply/ApplyAdd. Sam opt-in `--basis-audit` **wywołuje oryginał**;
od EXP112 osobna flaga PC-forward może jawnie zastąpić wybrane działania
([oddzielny eksperyment](pc-basis-fp32.md)). Opt-in `--basis-audit`
ustawia PALACE_CEED_BASIS_AUDIT=1; bez flagi tylko przekazanie wywołania.
Po apply odczytuje host metadata: topology/space/P/Q/components/q_components,
elementy, eval/transpose/add i długości obu wektorów. Brak kopiowania pól,
CUDA calls/synchronizacji ani zmiany arytmetyki. FP64 ABI sprawdzane przy kompilacji.

Host map do 2048 grup; liczniki i jeden raport przy zakończeniu. Parser
`tools/ceed_basis_audit.py` wymaga jednego footer, zgodnych grup/calls, braku
błędów/przepełnienia, znanych enumów i dostatecznych długości buforów.
Błąd audytu unieważnia kompletność RF/profilu; brak cichej kwalifikacji.

To liczności **API**, bez przypisania do PC/A, czasu kerneli, unikalnych alokacji
czy fizycznej rezydencji. API może wywoływać inne publiczne API. Długość wektora
nie jest liczbą odczytanych elementów: współdzielony workspace bywa większy
od działania. Parser oddziela input/output_bytes od required_input/output_bytes.
Te ostatnie są logicznym rozmiarem akcji, nie zmierzonym ruchem pamięci.

## Wykonane kontrole

| Przypadek | Czas | Iteracje | Audyt |
| --- | --- | --- | --- |
| Tiny kontrola OFF | 16,526 s | 40/42 | wyłączony |
| Tiny ON, ten sam build/oba porty | 16,606 s | 40/42 | 46 grup / 18 882 calls |
| W.3 ON, 3,50 GHz/P2 | 272,718 s | 35 | 108 grup / 14 627 calls |

Wszędzie complete/exit0; w audytach errors=overflow=0. Tiny max delta complexS
3,340e-10, VSWR6,483e-10, relative energy7,206e-10; całe pola PASS.
W.3 vs niezależny same-mesh FP64-coarse control EXP100: deltaS7,029e-10,
deltaVSWR2,486e-9, relative energy3,548e-10, port power3,113e-10,
weighted E/B ≤1,470e-8/1,307e-9, raw RHS residual8,3571e-7.
Frozen tolerances niezmienione. Jedna para tiny i jeden W.3 to kontrola audytu,
**nie nowa kwalifikacja speedupu ani mediana**. W.3 cgroup peak45 172 092 928 B;
licznik GPU process nie jest fizyczną rezydencją UVM.

Audyt tiny: JSON24 075 B / 47 tag lines9 844 B. W.3: JSON55 809 B /
109 tag lines22 789 B. Zwykłe małe wyniki, brak dyskowego workspace/swap.
Pliki JSON z runów poprzedzają dodanie pól required_* do parsera; ponowna
analiza zachowanego logu jest w root receipt, oryginalnych wyników nie nadpisano.

## Wymiary i następna hipoteza

Największe częste działania: tet Hcurl P20/Q14/q_components3/N1 601 320,
interp forward/transpose po1974 APIcalls, curl forward966, transpose966
(888 add,78 overwrite). H1 grad P10/Q14/q_components3/N1 601 320 po1376
forward/transpose. Hdiv interp P15/Q14/q_components3 ma po42 calls.
Aktywne są też poziomy Q6, triangle Hcurl P3/P8/Q6, H1 P6/Q6 oraz line
helper bases. Liczba components może być większa niż1; nie zakładać tego
na podstawie jednej grupy. Pełna tabela metadanych w basis-audit.json;
derived required_* bytes w m6-basis-audit-antenna-root-analysis-20261021.json.

Hcurl forward to logicznie 2,690 GFLOP i co najmniej794,255 MB odczytu/zapisu
FP64 (3,387 FLOP/B, bez ApplyAdd i współczynników). Natomiast zgłoszona długość
wektora wejściowego ma1,973 GB; wymagane wejście tej akcji tylko256,211 MB.
Nie wolno sumować długości workspace jako ruchu każdego wywołania ani usuwać
jego nadmiaru bez sprawdzenia innych użytkowników/lifetime.

Prosty wariant FP64 caller → FP32 bufor → biblioteczny GEMM → FP64 caller
ma optymistyczny logiczny ruch1,589 GB i dodatkowy float workspace397,127 MB
(pomija małą bazę; rzeczywisty packing/scatter/transpose może kosztować więcej).
To rachunek, nie pomiar czasu/transferu ani odrzucenie TC. TF32 nie zmniejsza
FP32 storage. Następny filtr M6.2: rzeczywiste kształty/baza, FP64 vs FP32/TF32,
transpose/ApplyAdd/curl/div, cały koszt konwersji i bounded batches, canary,
niezależny known-vector/FP64 oracle. Najpierw backend biblioteczny, potem
ewentualna fuzja; nie globalna zmiana oryginalnego A i kontrolnego residuum.

## Odtworzenie i dowody

Build `python3 tools/dev.py build --jobs 2`:8,455s, adapter + main.cpp/link,
bez rebuilda zależności. palace/CMakeLists.txt osadza git_describe w main.cpp;
zmiana rewizji może wymusić ten jeden TU. Ccache totals są skumulowane.
Fallback sprzed audytu: build/m6-basis-audit/pre-audit-native i manifest.

```sh
python3 tools/dev.py run tshaped-medium artifacts/NEW-basis-audit \
  --seconds 900 --basis fp32 --direct-basis --pc-side right --krylov-size 64 \
  --native-complex-coarse --native-coarse-fp32 --hypre-pool-mib 256 \
  --memory-marks --release-gmres-basis --release-final-solver --setup-audit \
  --basis-audit --save-fields \
  --field-reference artifacts/m5-mixed-antenna-p2-control-20261021 \
  --initial-fields artifacts/m1-antenna-resident-fp64-20261018
```

Domyślny fixture tego runu: istniejący3,50GHz/P2, P1 terminated50Ω;
seed tylko przybliżeniem początkowym, nie referencją dokładności.
60GiB/no swap i hostguard pozostają. W.3 audit nie kwalifikuje innych pasm/geometrii.

Lokalne dowody (ignorowane w Git):
artifacts/m6-basis-audit-tiny-{control,on}-20261021,
artifacts/m6-basis-audit-antenna-p2-20261021 oraz
artifacts/m6-basis-audit-{tiny,antenna}-root-analysis-20261021.json.
142 pinned tests PASS; aktualne następne kroki w [M6](milestones/M6.md).
