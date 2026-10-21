# M6.3 — TF32 WMMA bez pośrednich wektorów

Stan 2026-10-21: **wykazana ścieżka instrukcji Tensor Cores i zysk jednej
operacji; brak kwalifikacji preconditionera/całej symulacji**. Native solver,
medium, frozen K i dotychczasowy wariant referencyjny bez zmian.

## Hipoteza i implementacja

Po [ocenie biblioteki](cublaslt-assessment.md) EXP167–170: Lt nie usunął kosztu
pack/GEMM/unpack i był wolniejszy od FP32 we wszystkich6 actual-size akcjach.
Eksperymentalne `--wmma` korzysta z istniejącego CUDA WMMA API, bez CUTLASS
jako nowej zależności. Wymaga `--lt --fused`, żeby zachować porównania.

`tools/experiments/ceed_tensor_probe.cu`:

- Forward basis P20/Q14/QC3, dowolne dodatnie N w jawnym limicie indeksowania;
  nie zakłada geometrii, częstotliwości ani materiału anteny.
- x/y nadal FP64; baza FP32, shared tiles ręcznie zaokrąglone do TF32,
  akumulacja FP32. Nie jest to arytmetyka FP64 ani skompensowany TF32.
-64elementy/block,128threads/4warps, zerowe dopełnienie wymiarów i końcówki N.
  Stałe pętle MMA dla wszystkich lane; brak wcześniejszego return w kernelu.
- FP64→TF32 konwersja i FP32→FP64 zapis wewnątrz jednej operacji CUDA;
  żadnych globalnych pośrednich wektorów FP32. Staticbasis3360B i
  shared18432B/block. Transpose/ApplyAdd pozostają osobnymi porównaniami,
  bez nowego wariantu WMMA. Unsupported shape jawnie odrzucany.

To izolowany probe. Proces porównawczy nadal alokuje bufory innych metod;
nie utożsamiać reprezentacji WMMA z pomiarem spadku całego VRAM/RAM.

## Wyniki i powtarzalność

EXP171:12akcji screen,4WMMAforward,9.23s. EXP172:42akcje ladder,
14WMMAforward,20.83s;7rozmiarów257…1601320. CPU longdouble, oryginalna
libCEED, FP64 layout, canaries, perturbation controls i wszystkie filtry
błędu działań PASS. WMMAmaxrelativeL2 przyactualN: INTERP2.223e-4,
CURL3.304e-4; FP32fused około6e-8. Filtr2e-3 to wyłącznie bramka mikrooperacji,
nie zgoda na taki błąd pól/RF lub zmianę frozen tolerancji solvera.

EXP174–175 powtórzyły cały ladder w dwóch niezależnych procesach, bez
rebuilda. Poniżej mediana trzech procesowych median pełnego apply (każda
z3czasów wall, razem9próbek/metoda/wiersz), actualN1601320:

| Forward | Original MAGMA FP64 | Fused FP32 | Fused WMMA/TF32 | Oszczędność vs fused FP32 |
| --- | ---: | ---: | ---: | ---: |
| INTERP |3.4740ms|1.3360ms|1.2043ms|9.86%|
| CURL |3.4754ms|1.3377ms|1.2011ms|10.22%|

Zakres WMMA między procesami: INTERP1.2027–1.2043ms,
CURL1.1972–1.2050ms. Około2.89× vs original dotyczy tylko tej akcji,
nie pełnego PC/GMRES/FEM. Małe N mogą być wolniejsze. Nie mieszać wyników
z profilowanych runów z tymi medianami.

Dowody (ignored artifacts):

- `artifacts/m6-wmma-screen-20261021`
- `artifacts/m6-wmma-scale-20261021`
- `artifacts/m6-wmma-scale-repeat2-20261021`
- `artifacts/m6-wmma-scale-repeat3-20261021`
- `artifacts/m6-wmma-root-analysis-20261021.json`

## Dowód instrukcji, nie sama flaga TF32

EXP173: osobny NsightSystems trace tego samego zweryfikowanego binarium,
23.41s/exit0/complete,70uruchomień dokładnego symbolu
`_Z25palace_probe_wmma_forwardPKfPKdPdi`. Bez ostrzeżeń/utraty zdarzeń.
Ślad obejmuje wszystkie metody probe; własny symbol rozdziela WMMA od cuBLAS.

`cuobjdump --gpu-architecture sm_120 --function <dokładny symbol> --dump-sass`
na identycznym binarySHA:48statycznych instrukcji `HMMA.1684.F32.TF32`.
Analiza źródła i sterowania: przed pierwszą HMMA nie ma EXIT, wcześniejsze
BRA to pętle ładowania shared, wszystkie HMMA niepredykowane. Zestawienie
wykonanego symbolu, identycznej binarki i tej ścieżki stanowi dowód użycia
instrukcji Tensor Cores w tym kernelu. Nie jest licznikiem wykonanych
instrukcji, procentem wykorzystania TC ani dowodem ich użycia przez główny
solver. `RmProfilingAdminOnly` pozostaje niezmienione, ncu nie użyto.

Receipts: `artifacts/m6-wmma-trace-20261021/{profile,result}.json`,
`artifacts/m6-wmma-instructions-20261021/{result,root-proof}.json` i
`kernel.sass`, SHA binarki/tool/trace/SASS. cuobjdump13.4 tylko analizuje
wytworzone CUDA12.9.1/SM120; runtime/dependencies nie aktualizowano.
FinaltraceSQLite~2.45MB/nsys~0.99MB, hotcapture wRAM i usunięty po odbiorze.

## Następna bramka — nadal HOLD

1. W.1: niezależna liniowość/homogeniczność i zakres wartości przed
   integracją. TF32 ma tu znacznie większy błąd niż FP32; testować jawnie
   under/overflow i fallback, nie ukrywać ich za przejściem luźnego filtra.
2. Dopiero uzasadniony opt-in do istniejącego RAII PC scope, bez zmiany
   oryginalnego operatora A i kontrolnego Ax−b. K.1–K.5: mały coax,
   frozen medium, pola/S/VSWR/energia/raw i liczba iteracji. Dotychczasowy
   FP32 PC nie wykazał netgain, więc szybszy kernel nie jest wystarczający.
3. W.3 tylko jeśli mały pełny run wykaże korzyść. Uwzględnić ewentualny
   FGMRES i jego pamięć, UVM, wszystkie konwersje/setup i czas całego zadania.
   Przy negatywnym filtrze odrzucić tę integrację z raportem.

BF16/FP16 pozostają odrębnymi, niezakwalifikowanymi hipotezami.

## Odtworzenie małego testu

```sh
python3 tools/experiments/ceed_tensor_probe.py build
python3 tools/experiments/ceed_tensor_probe.py run NEW_SCREEN --lt --fused --wmma --seconds 120
python3 tools/experiments/ceed_tensor_probe.py run NEW_SCALE --lt --fused --wmma --scale --seconds 120
python3 tools/experiments/ceed_tensor_probe.py run NEW_TRACE --lt --fused --wmma --scale --profile-lt --seconds 120
```

Nowe katalogi, wolny GPU/minimum2048MiB,6GiB cgroup/no swap. Zwykły build
probe to cached2TUs; nie budować Palace/MFEM dla zmiany samego runnera/docs.
