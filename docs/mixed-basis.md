# M3 — bezpośrednie operacje na bazie FP32

Status: **eksperyment opt-in, bez zmiany defaultu**. Najnowsze EXP80–85:
[actual API / W.2 / W.3](mixed-basis-validation.md) PASS, W.3 pamięć−2,87GB;
brak udowodnionego speedupu. M3 nadal ACTIVE (polityka migracji), W.4/W.5 otwarte.

## Implementacja i zakres

`palace/linalg/mixedbasis.hpp`: FP32 odczyt jest konwertowany do double przed
mnożeniem i sumowaniem. Dot zachowuje konwencję Palace `Dot(w,b)=bᴴw`.
`StoredBasisVector::Dot/AddTo` w vector.cpp stosują MFEMforall, FP64 HYPRE sumy
częściowe i MPI GlobalSum. Jeden wspólny workspace na GMRES, max65536 par double
(1MiB), zamiast jednego workspace na każdy wektor. Backend MPI multi-rank nie
jest jeszcze zweryfikowany. Wewnętrzna redukcja standalone CUDA probe jest inna
niż HYPRE; rzeczywiste wrappery przeszły dopiero EXP79 complex coax-tiny.

`PALACE_GMRES_FP32_DIRECT` wymaga `PALACE_GMRES_FP32_BASIS` i MGS GMRES.
Usuwa Unpack z pętli ortogonalizacji i rekonstrukcji rozwiązania. Nadal zostaje
jedno rozpakowanie przed ApplyBA, bo operator używa FP64. **Pełny basis_read
nie został usunięty**, więc oszczędności bufora standalone nie przenoszą się
automatycznie na Palace. Operator/faktory/residual pozostają FP64, reliable
stopping/restarts bez zmian. Tensor Cores nie są używane.

Domyślna ścieżka FP64 i dotychczasowa FP32/unpack są zachowane; runner czyści
odziedziczoną nową flagę, wymusza jawny `--direct-basis` tylko z `--basis fp32`.
Nie zmieniono medium/siatek/fizyki. Wariant native-complex-coarse + FP32 od EXP82 jest dopuszczony tylko z jawnym
DIRECT; nowa kombinacja przeszła W.2/W.3 w EXP83–85. FP32/unpack nadal blokowany.

## EXP77–78 — cache i mały probe

```sh
python3 tools/experiments/mixed_basis_probe.py build
python3 tools/experiments/mixed_basis_probe.py run artifacts/new-mixed-basis --seconds 60
```

Pojedynczy CUDA TU sm120 kompilowany przez ccache, osobny link:1,50s; identyczny
build no-op. Zero rebuild dependencies. Private NumPy/Python jak w M2, 6GiB,
4CPU, swap wyłączony, tmpfs RAM512MiB, deadline60s, brak sieci i chmury.
Przypadki1/1009/131071/1048576, niepełne partycje, n1 z niezerową fazą;
skale1e-30..1e30, błędny n0 odrzucony. Reference longdouble63-bit mantissa na
tych samych danych zaokrąglonych do FP32; osobna kontrola quantization.

Norm-product-scaled dot max4,43e-18, axpy4,40e-17; v2 także relative-to-dot PASS.
FP32 quantization max8,87e-10 w tej normie. To nie jest gwarancja każdego
przypadku utraty cyfr/cancellation ani całego Krylov solve.

Dla N1048576, naprzemienne kolejności i30powtórzeń: EXP77 median0,109695ms direct
vs0,119766ms unpack; EXP78 0,1020/0,11976ms. Timery obejmują jednakowy reset
wektora, wyłączają allocation/H2D/JIT. To porównanie wspólnych własnych kerneli,
nie HYPRE lub całej anteny. Explicit device allocation76,546MB obejmuje obie
ścieżki równocześnie; nie jest pomiarem VRAM peak/drop. Brak profilu migracji.

API vector.hpp wymusiło pierwszą przebudowę solvera:227,712s/jobs2, 9 cachehits,
329 misses; zainstalowane MFEM/libCEED/hypre pozostają bez rebuilda. Obiekty
i cache zachowane. Zweryfikowane poprzednie binaria+manifest11MiB zachowane
w `build/m3-basis/pre-m3-native/` jako fallback, bez nadpisania.

## EXP79 — rzeczywisty Palace / coax-tiny

Ta sama binarka i medium, RIGHT pc,3,55GHz/oba porty,62/64iter. FP64reference
zapisuje pola; oba FP32 warianty używają identycznego odniesienia. TEM positive
volume rules4/6: E≈0,4953%, B≈0,4558% PASS. Raw RHS<1e-6 we wszystkich solve.

| Wariant | max raw | Δcomplex S | ΔE / ΔB L2 | Cały run | cgroup peak |
| --- | --- | --- | --- | --- | --- |
| FP64 | 9,026e-7 | 0 | reference | 18,714s | 610,3MB |
| FP32/unpack | 9,045e-7 | 1,626e-9 | 7,677e-7 /1,045e-8 | 18,723s | 589,8MB |
| FP32/direct | 9,042e-7 | 3,412e-9 | 7,528e-7 /1,004e-8 | 18,709s | 595,1MB |

Direct ΔVSWR6,751e-9, Δport-power-sum6,823e-9. GPU process peak FP64/unpack
4,658GB, direct4,687GB; **brak zmierzonej redukcji GPU peak ani istotnego speedupu**
na tiny. Nie przenosić małych różnic czasu/cgroup peak na dużą antenę.
Wszystkie K field/S/raw kontrole dotyczą tylko wskazanego tiny przypadku,
nie pełnej drabiny W.1–W.3 ani uniwersalnej poprawności FP32.

```sh
python3 tools/dev.py run coax-tiny artifacts/new-tiny-reference --basis fp64 --pc-side right --coax-l2 --save-fields --memory-marks --phase-trace --seconds 60
python3 tools/dev.py run coax-tiny artifacts/new-tiny-direct --basis fp32 --direct-basis --pc-side right --coax-l2 --save-fields --field-reference artifacts/new-tiny-reference --memory-marks --phase-trace --seconds 60
```

Dowody: `artifacts/m3-mixed-basis-cuda{,-v2}-20261019/`,
`artifacts/m3-coax-tiny-{fp64,fp32-unpack,fp32-direct}-20261019/`,
rootverified `artifacts/m3-coax-tiny-root-analysis-20261019.json`.
Historyczne następne kroki EXP79 zrealizowano w EXP80–85;
[aktualne wyniki](mixed-basis-validation.md). Nie zmieniać restartu w tym samym
eksperymencie co reprezentacji.
