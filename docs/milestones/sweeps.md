# M6.6 — szybsze sweepy częstotliwości

Status: **ACTIVE, pierwszy filtr PASS**, po M5, w ramach M6;2026-10-21.
Cel: krótszy czas całego zestawu3,3/3,4/3,5/3,6/3,7/3,8/3,9GHz na jednej
RTX5070Ti16GB/96GBRAM, oba porty, bez utraty wiarygodności medium.
To rozszerzenie celu, nie zmiana dotychczasowych progów ani zamknięcie M5.

## Kolejność hipotez

1. **Audyt istniejącego Palace**: SweepUniform, SweepAdaptive i RomOperator;
   ustalić co już reużywa siatkę/spaces/K/C/M, co ponawia assembly/setup i jakie
   PROM/interpolation/error controls są rzeczywiście dostępne. Bez duplikowania
   istniejącego silnika. Obecny opt-in M4 współdzieli faktory tylko przy tym samym f.
2. **Continuation/warm start**: poprzednie E jako start następnego f, przy każdej
   częstotliwości nowe RHS/operatory i niezależnie przeliczone rawresidual.
   Każdy port ma własną historię; nie traktować P1 jako tożsamego rozwiązania P2.
3. **Symbolic reuse**: tylko jeśli identyczny wzorzec CSR potwierdzony, a materiały,
   mesh/porty i konfiguracja reordering się nie zmieniły. Faktory numeryczne
   muszą odpowiadać nowym wartościom A(f); brak ślepego reuse LU między f.
4. **Recycling Krylov/subspace**: oszacować liczbę dodatkowych wektorów/VRAM i
   koszt aktualizacji. Sprawdzić actual residual i stagnację; fallback niezależny
   solve, bez zmiany tolerancji. Nie zakładać, że zwykły GMRES to recycling.
5. **Adaptive sweep/PROM**: pełne solve w wybranych f, tańsza ocena pozostałych.
   Co najmniej jeden punkt kontrolny niewykorzystany do budowy modelu. Błąd pola
   i S oraz residuum oryginalnego układu, nie tylko residuum małego modelu.
   Near-resonance/antyrezonans wymaga osobnej kontroli, nie tylko gładkiej krzywej.

## Eksperymenty i bramka

Najpierw kosztorys i mały analityczny coax, np.3punkty, potem siedem punktów.
Budżet i liczba solve ustalone przed runem; istniejące deadline/caps pozostają.
Jeżeli zestaw nie mieści się w jednym limicie, jawne checkpointy/chunki i suma
całego czasu; nie ukrywać kosztu ponownego setupu ani wrzucać working set na dysk.
Droga antena dopiero po tanim filtrze i realnej prognozie zysku.

Kontrola: niezależne pełne medium solve w tych samych punktach i obu portach,
identyczna geometria/materiały/terminacje. Osobno koszt cold-start, warm setup/JIT,
assembly/analysis/factor/solve, wektory recycling/PROM i dodatkowa pamięć.
Ocena obejmuje cały zestaw, nie samo tańsze wywołanie dla jednego f.
FrozenK dla wszystkich S/VSWR/power/raw, pola w ustalonych kontrolach i punktach
nieużytych przez PROM. Fallback odnotowany i doliczony do kosztu.

Zamknięcie M6.6: porównanie promote/reject z dowodami; lista pomysłów nie wystarcza.
Nie obiecywać zysku przed pomiarem. Wariant promowany przechodzi końcowe M7.

## Audyt źródeł i pierwszy prototyp, EXP120–122

Źródła forka@ef008b0: DrivenSolver::SweepUniform/SweepAdaptive,
RomOperator::SolveHDM/UpdatePROM/SolvePROM, IoData initialguess defaults,
ComplexCuDSSSolver::SetOperator. Lokalne hashe w
artifacts/m6-sweep-source-audit-20261021.json. Nie zmieniono zależności/licencji.

- Uniform już współdzieli K/C/M i używa InitialGuess=true, więc nie ogłaszamy
  ich ponownego wynalezienia. Defaultowa pętla excitation-major przebudowuje
  preconditioner dla każdego portu/f; E przechodzi też przez granicę portów.
- CuDSS SetOperator czyści analizę i faktory. Nie ma obecnie symbolicreuse;
  nie przenosimy żadnej faktoryzacji numerycznej między różnymi f.
- PROM istnieje, z realną bazą (do2realvectors/complexsnapshot). Obecne
  adaptive training fielddiscrepancy nie zastępuje online rawresidual/wholefield
  controls. Nie ma jeszcze naszego bounded wrappera/kwalifikacji tej ścieżki.
  Dla W3 do4samples×2ports:16realvectors≈1,436GB samej bazy, nie peak procesu.

### Implementacja opt-in

Rozszerzono istniejące `--port-setup-reuse`: wiele punktów i dokładnie dwa
lumped excitations → kolejność frequency-major. Nowy A/P/setup przy każdej f,
reuse wyłącznie drugi RHS tej samej f. W pamięci pozostaje tylko aktualny
zestaw faktorów. Poprzednie E każdego portu jest osobnym punktem startowym;
firstf zero, następne restore, ostatnie release. To nie recycling Krylov ani PROM.
Zmiana kolejności i historii są jednym kandydatem, nie izolowana przyczyna
każdej różnicy iteracji. Default pozostaje excitation-major; dotychczasowy
onefreqreuse/deferred path sprawdzony oddzielnie w EXP122.

Wymagane: rank1/fixedmesh/Restart1, rosnące unikalne Point frequencies,
2lumpedports dla wielu f, nativecoarse. Brak wave/Floquet/AMR/adaptive,
externalfieldseed i visualizationwrites. W historycznym EXP120–122 NF>1 +deferredpostprocessing było nadal
jawnie odrzucane; to prototyp przed kontrolą pamięci pełnej anteny.
Runner usuwa odziedziczone env i zapisuje jawny mode. Native final-history
assert, strictaudit sekwencji build/reuse, realnych CSR/factorcounts i per-port
zero/restore/store/release; osobne raw/frozenK/fieldgates. Brak cichego staleLU.

### Pierwsze wyniki, jedna para tego samego buildu

3,30/3,55/3,80GHz, oba porty, medium/Tol1e-6/K64/right/directFP32storage/
M5scaledmixedcoarse. Bez nowych kernelów/TF32 i bez zmiany mesh. Nativebuild
8,727s, cache/dependencies zachowane; sourceSHA
`31c23ac6147564cc90a28356d8a4e0d63a04559b5cf3f070b4f3b74aa7a24cac`.

| Case | Kontrola | Reuse | Native faktoryzacje | Cgroup peak control → reuse |
| --- | --- | --- | --- | --- |
| Tiny | 12,544s | 11,501s | 6 → 3 | patrz result.json |
| Medium | 53,570s | 45,344s | 6 → 3 | 2,255 → 2,304GB |

Około8,3%/15,4% krótszy cały run, **nie mediana M7 ani promocja anteny**.
Tiny iteracje P1/P2 control40,31,30/42,31,30; candidate frequency-major
40,40/31,31/30,30. Medium48,38,38/50,38,38 →48,48/38,38/38,38.
Tych list nie porównywać bez mapowania (port,f). Extra history logicznie
2,851MB/tiny,26,526MB/medium; W3 rachunkowo359MB, nie measuredpeak. ProcessGPU
631,243MB obu dróg nie jest fizyczną rezydencją UVM. Nie wykazano oszczędności RAM.

Root K tiny: maxΔS4,345e-9/VSWR8,652e-9/relativeenergy1,118e-8/
portpower8,346e-9, fieldsE/B≤8,408e-7/2,290e-7. Medium3,198e-10/1,176e-10/
1,933e-10/2,989e-10, fields≤5,643e-8/9,511e-8. TEM RMS samples wszystkich
f/portów≤0,4497% tiny/0,4253% medium, energy≤1,764e-5/1,506e-5. To nie
nowy analityczny volumeL2: kosztowny podwójny L2 quadrature pominięty jawnie
w obu drogach; pełne pola porównane z kontrolą normą energii.
`coax_fields.py` obsługuje teraz wyrównane wieloczęstotliwościowe CSV;
testy exactTEM/wrongBsign/frequencyphase/missingrow/misalignment/NaN.

CSR structure zgadza się, trzy różne valueshashes potwierdzone; bitowe
valuesfingerprints między control/candidate różnią się. **Nie twierdzimy, że
zmierzono rozmiar różnicy CSR lub dowiedziono wyłącznie roundoff przyczyny.**
Source/build/config identity, źródłowa granica reuse i frozenRF/raw/fields
przechodzą; same hashe nie są normą błędu macierzy.

Przykład odtworzenia:

```sh
python3 tools/dev.py run coax-tiny artifacts/NEW-sweep \
  --seconds 60 --basis fp32 --direct-basis --pc-side right --krylov-size 64 \
  --native-complex-coarse --native-coarse-fp32 --hypre-pool-mib 256 \
  --memory-marks --release-gmres-basis --release-final-solver --setup-audit \
  --release-postprocess-energy --coax-fields --coax-sweep --save-fields \
  --port-setup-reuse --field-reference artifacts/CONTROL-SAME-SWEEP
```

Kontrola pomija dwie ostatnie opcje; coax-medium limit180s. Fieldreference ma
te same mesh/freq/porty/terminacje; żadnego ładowania seedów z SSD.
Snapshoty są zwykłym wynikiem walidacji,22,56MB/tiny i212,40MB/medium na run,
hot history wyłącznie RAM/VRAM. Fallback: pominąć flagę; wcześniejsze binarki
build/m6-sweep/pre-sweep-native +pre-sweep-manifest.json.
Dowody: artifacts/m6-sweep-{tiny,medium}-{control,on}-20261021,
m6-sweep-{tiny,medium}-root-analysis-20261021.json i replay m6-sweep-root-analysis.py.
EXP122 singlefreqreuse/deferred regression:9,445s/40,42iter/wholefieldsPASS,
1build+1reuse, raw-check retry zachowany, nie zaostrzono/nie poluzowano tolerancji.

## Per-frequency release i siedem punktów, EXP123–127

Native source SHA: `037574a7a055fc873dfb372b88e6d9dc4df93b21d44b2f42998edc4f15bfc92c`.
Cached build32,409s (zależne TU po zmianie nagłówka, bez rebuild dependencies).
Aktualne NF>1 deferred wymaga frequency-major reuse, energy release i final
solver release. Po obu RHS każdej f niszczymy ksp przed A/P/A2, a pomiary
wykonujemy bez faktorów. K/C/M pozostają do ostatniej f. Zapisujemy sumę
liczników wszystkich zniszczonych solverów; metadata nie zawiera tylko ostatnich
2 solve. Dwie historie E plus jeden przejściowy deferred E:3E niezależnie od NF;
na W3 rachunkowo538,5MB dodatkowej pojemności, nie zmierzony peak.

| Test | Kontrola → kandydat [s] | Cgroup peak [GB] | Zakres |
| --- | ---: | ---: | --- |
| EXP123 tiny3freq |11,508→11,538|0,609→0,609|plain reuse → reuse+deferred|
| EXP124 medium3freq |45,373→45,250|2,307→2,264|plain reuse → reuse+deferred|
| EXP125 tiny7freq |18,675→15,598|0,646→0,639|normal → reuse+deferred|
| EXP126 medium7freq |93,540→75,664|2,515→2,535|normal → reuse+deferred|

Każdy wiersz to jedna para, nie mediana. EXP126 **−19,1% czasu**, bez redukcji
pamięci całego runu (+20,4MB cgroup). ProcessGPU660,603→631,243MB nie mierzy
fizycznej rezydencji UVM. Dla EXP124 managed-live przy początku postprocessingu
pierwszych2f spadło2,63–2,74→0,918–1,015GB: okno życia buforów, nie globalpeak.

Siedem punktów3,3..3,9GHz co0,1: wszystkie14 pełnych HDM solve,14→7 faktoryzacji,
bez interpolacji ani pomijania próbek. Wszystkie rawresidual, wholefield, frozenK,
TEM oraz audyty kolejności/release/history/metadata PASS. Medium maxΔS8,951e-9,
ΔVSWR8,180e-10, relativeenergy1,373e-8, portpower1,043e-8, E/B≤5,945e-8/9,565e-8.
CPU TEM RMS≤0,42530%, energy≤1,506e-5 we wszystkich f/portach. Native całe pola
porównane normą energii; nie wykonywano podwójnej kwadratury coax volumeL2.
Struktura CSR zgodna, fingerprints wartości między runami różne: nadal brak
pomiaru normy różnicy CSR i dowodu przyczyny wyłącznie roundoff.

Odtwarzanie: w komendzie powyżej użyj `--coax-sweep n78` i dodaj
`--defer-postprocessing` dla kandydata. Kontrola7freq pomija reuse/deferred/ref,
kandydat wskazuje kontrolę tych samych7freq. Tiny60s/medium180s. Preset jest
wyłącznie nadpisaniem runtime Samples; nie zmienia mesh, Tol ani portów.
Nazwa n78 jest identyfikatorem presetu; punkt3,9GHz wykracza poza pasmo n78.

Dowody i replay:
- `artifacts/m6-sweep-deferred-{tiny,medium}-{control,on}-20261021`;
- `artifacts/m6-sweep-deferred-root-analysis.py` i odpowiednie root-analysis JSON;
- `artifacts/m6-sweep7-{tiny,medium}-{control,on}-20261021`;
- `artifacts/m6-sweep7-root-analysis.py` i odpowiednie root-analysis JSON;
- EXP127 `artifacts/m6-sweep-deferred-single-regression-20261021`:
  stary singlefreq9,473s/40,42iter, fields/raw/audyty i metadata2/82 PASS.

Zwykłe snapshot outputs:49,74MB/tiny7 i466,60MB/medium7 na run; historia robocza
pozostaje w RAM/VRAM. Fallback: pominąć opt-in; wcześniejszy native/manifest
`build/m6-sweep-deferred/pre-deferred-{native,manifest.json}`. Defaulty bez zmian.

### Następne bramki

1. Przed W3 przygotować kontrolę, która też zwalnia solver przed pomiarem;
   uniknąć ponownego OOM dużego monolitycznego wariantu. Rozdzielić harmonogram
   frequency-major od reuse, aby porównać świeże faktory/reuse z identyczną
   polityką pamięci. Najpierw tani filtr, potem2f właściwej anteny po resourcegate.
2. Zmierzyć rzeczywisty cały koszt anteny/UVM, cold start i peak; nie przenosić
   automatycznie wyniku coax na antenę. Wszystkie punkty zachowują frozenK.
3. Odrębna ocena adaptive/PROM z held-out point i oryginalnym residual, symbolic
   reuse i recycling z policzonym workspace. Obecne filtry nie zaliczają ich.
4. Antena/W4/W5/nowa geometria/repeats/finalpackage w M7 pozostają otwarte.

M6.6, M6 i goal nadal otwarte. Nie generalizować dwóch coax na każdą geometrię.
