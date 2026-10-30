# Audyt i plan: odczyt oraz zapis wyników

## Stan bieżący po zamknięciu M2 — 2026-10-30

Ta tabela określa aktualną kolejkę; wcześniejsze wpisy zachowują historyczne etapy próby.
PASS jest zakresowy; nowa optymalizacja wymaga osobnych testów M2/M3.

| ID | Stan i zakres |
|---|---|
| IO-01 | PASS — profil/replay M1; parser wejścia to główny koszt |
| IO-02 | DEFERRED — writer0,85–2,38ms; wrócić przy mierzalnym dużym sweep/output |
| IO-03 | DEFERRED — VTK poza obecnym workloadem |
| IO-04 | DEFERRED — mały reload w replay nie daje sensownego E2E |
| IO-05 | DEFERRED — cleanup nie wyjaśnia kosztu wejścia |
| IO-06 | DEFERRED — strict Gmsh/full-native structural PASS; production parse 19,040→17,000s, cold34,049/HIT0,441s; zwrot ≥22 identycznych loads (E08) |

Status: M0/M1 scoped PASS; M2 IO06 structural i production-parser pair PASS, automatyczny cache DEFERRED. Pełne RF i powtarzane pomiary E2E NOT RUN.
Owner: agent I/O, branch `opt/io-20261029`.
Granica ownership: parser siatki i odczyt wejściowego mesha są współdzielone z preprocessingiem; koordynator wybiera właściciela ewentualnego patcha. Ten branch może audytować output i timery, ale nie zmienia `geodata.cpp`/`meshio.cpp` bez uzgodnienia.

## Co mierzy „Disk IO”

`Timer::IO` w `palace/utils/timer.hpp:35-57, 106-145` to ręcznie zebrany czas ścienny scope’ów nazwanych I/O. Nie czyta liczników dysku, bajtów ani czasu CPU osobno. Dlatego 19,612 s nie dowodzi, że fizyczny dysk pracował 19,612 s. Scope może zawierać formatowanie/serializację CPU, synchronizację/oczekiwanie GPU przez `HostRead`, MPI barrier albo czekanie na filesystem. I odwrotnie, część outputu jest mierzona innymi timerami.

`BlockTimer` stosuje zagnieżdżone exclusive timers (`timer.hpp:241-289`), a `PALACE_PHASE_TRACE` dodatkowo zapisuje inclusive scope. W `geodata.cpp:137-143,153-161` odczyt wejściowego mesh jest podscope’em `IO` wewnątrz preprocessing. CSV zapisywane przez `TableWithCSVFile::WriteFullTableTrunc` nie ma własnego `Timer::IO`; zwykle czas wykonania należy do nadrzędnego timera postprocessingu/solve. Podobnie `WriteParaviewFields` jest pod `POSTPRO_PARAVIEW` (`postoperator.cpp:1133-1202`), mimo że kończy się zapisem plików. `Timer::IO` obejmuje m.in. `EnsureDirectory`, `RemovePreviousOutput`, `WriteRootOutputFile` (`outputdir.hpp:147-205`) oraz przygotowanie katalogu (`:207+`). `WriteRootOutputFile` mierzy cały callback — także generowanie tekstu/binariów i ewentualną synchronizację — nie sam syscall `write`.

W znanym medium runie „Disk IO” wyniósł 19,612 s z 825,783 s, około 2,37%. Ten wynik nie obejmuje z definicji całego zapisu CSV/VTK ani kosztu renderowania pól. Sama optymalizacja `Timer::IO` ma ograniczony potencjalny wpływ E2E; najpierw trzeba ustalić pełny koszt outputu i czy run w ogóle generował te formaty.

## Miejsca w kodzie

| Miejsce | Obserwacja | Kandydat | Status |
|---|---|---|---|
| `palace/utils/timer.hpp:35-57,241-289`; `palace/utils/outputdir.hpp:147-205` | `IO` jest wall timerem nazwanych scope’ów. Timer nie liczy bajtów ani syscalls. `WriteRootOutputFile` obejmuje całą funkcję serializującą. | Ujawnić osobne wall/CPU/bytes/read-write, aby nazwa „Disk IO” nie prowadziła do błędnego wniosku. | `IO-01` TODO |
| `palace/models/postoperatorcsv.cpp:1141-1164` (oraz analogiczne metody tabel) i `palace/utils/tablecsv.cpp:278-308` | Każdy `PrintPortS()` uzupełnia kolumny źródła (także w istniejącym wierszu), po czym `WriteFullTableTrunc()` formatuje i zapisuje całą tabelę od nowa. Dla N częstotliwości może to robić łączny zapis/formatowanie rzędu O(N²) wierszy. | Mierzyć liczbę zapisów, bajty i koszt dla liczby częstotliwości. Sprawdzić append/buforowanie jako osobny prototyp, zachowując bezpieczne wznowienie adaptive/reload. | `IO-02` TODO |
| `palace/models/postoperator.cpp:1133-1202`; `palace/utils/ceedparaviewdatacollection.cpp:200-229` | Paraview zapis wykonuje skalowanie/pole pochodne i `Save`; domenowe pole pobiera `HostRead()` i serializuje dane element po elemencie do bufora/strumienia. `HostRead` może wymagać transferu/synchronizacji. Całość widoczna jako `POSTPRO_PARAVIEW`, niekoniecznie `Disk IO`. | Rozdzielić compute, host transfer, serializację i write; następnie sprawdzić VTK binary/compression/precision oraz batching. | `IO-03` TODO |
| `palace/utils/tablecsv.cpp:278-299` | Przy `load_existing_file` CSV jest wczytywany do `stringstream`, następnie kopiowany do `string` i parsowany przez `Table`. To może powodować duplikaty bufora i peak RAM dla dużych tabel. | Zmierzyć użycie reload w docelowym runie i peak/bajty; rozważyć streaming parser dopiero jeśli ten koszt jest mierzalny. | `IO-04` TODO |
| `palace/utils/outputdir.hpp:163-205,207+` | Startup może usuwać poprzedni katalog rekurencyjnie; tworzenie/usuwanie katalogów i filesystem coordination również zalicza się do IO timerów. | Zmierzyć cold/warm output dir i liczbę plików; nie usuwać sprzątania, dopóki test nie potwierdzi bezpiecznego rozdzielenia starego wyniku. | `IO-05` DEFERRED do raportu IO-01 |

## Rejestr hipotez i testów

Przed próbą agent wyszukuje ID w tym ledgerze i aktualizuje istniejący wpis. Statusy: `TODO_TO_CHECK`, `IN_PROGRESS`, `PASS`, `REJECTED`, `DEFERRED`. Do `PASS`/`REJECTED` zapisać datę, commit i hash builda/fixture, dokładne argv/config, liczby częstotliwości i źródeł, bytes/read/write, czas CPU/wall, peak RAM, wynik poprawności oraz artefakt raportu. `TODO_TO_CHECK` jest hipotezą, nie wykonanym eksperymentem. Zmiana w kodzie nie zalicza testu wydajności.

### IO-01 — pokrycie i narzut timerów (`TODO_TO_CHECK`)

Zweryfikować w reprezentatywnym medium runie, które funkcje wchodzą do każdego timera. Sparować `PALACE_PHASE_TRACE` (inclusive nesting) z `Timer::IO` (exclusive scope) oraz systemowymi licznikami procesu: `read_bytes`, `write_bytes`, CPU time, filesystem call counts/duration jeśli dostępne. Nie sumować inclusive timers. Jawnie zapisać konfigurację `Paraview`, grid functions, probes, farfield, CSV i reload. Jeżeli nie ma dokładnego istniejącego runu, zaplanować jeden kontrolowany test po zatwierdzeniu celu; żadnego nowego EM/GPU runu w samym audycie.

Zaliczenie: rozliczenie największych scope’ów do ±2% ich właściwego nadrzędnego timera, bytes i systemowy czas I/O rozdzielone od CPU/wall, plus opis opóźnień `HostRead` i MPI. Nie zakładać, że `Disk IO` = dysk.

### IO-02 — koszt pełnego przepisu tabel w sweepie (`DEFERRED` dla obecnego operators-only case; patrz IO-01-E03)

Na małej tabeli i potem istniejącym sweepie porównać koszt/bytes przy N i 2N wierszy; rejestrować częstotliwość wywołań `WriteFullTableTrunc`, czas formatowania i zapis, rozmiar finalnego pliku, reload/adaptive restart. Oczekiwanie O(N²) wynika z kodu, ale rzeczywisty udział E2E zależy od liczby częstotliwości i tabel. Prototyp append dopuszczalny dopiero po teście niezmienionej kolejności kolumn, precyzji, kompletności po przerwaniu i możliwości reload.

### IO-03 — VTK/Paraview i GPU→host (`DEFERRED`: brak VTK w referencji M0)

Testować z tym samym mesh/polem włączone/wyłączone Paraview oraz dostępne formaty: zmierzyć `POSTPRO_PARAVIEW`, HostRead/transfer, CPU serializacji, bajty i wall write oddzielnie. Sprawdzić output geometry/field equality oraz możliwość odczytu przez ParaView/MFEM. Asynchroniczne kopiowanie/buffering tylko jeśli profil potwierdzi host transfer lub serializację jako znaczący koszt; zabezpieczyć lifetime bufora, synchronizację i MPI outputu.

### IO-04 — reload tabel (`TODO_TO_CHECK`)

Sprawdzić, czy aktywny antenna workload faktycznie używa `reload_table`; zmierzyć peak dodatkowej pamięci i parse time względem rozmiaru CSV. Streaming parser jest wart pracy tylko gdy reload jest aktywny i pamięć/czas jest istotny. Utrzymać identyczną obsługę brakujących/starych plików, headerów, separatorów, precyzji i duplikatów kolumn.

### IO-05 — cleanup output directory (`DEFERRED`)

Najpierw IO-01. Wrócić tylko, gdy startup cleanup jest mierzalny albo poprzedni output jest duży. Nie zachowywać starych wyników przez przypadek i nie usuwać ich przed potwierdzeniem ścieżki. Wyniki solvera nie mogą być cachem/ramem do offloadu.

## Bramki gałęzi

- Odczytać docelowy fixture i dokładnie ustalić output/reload config, liczbę częstotliwości i plików.
- Rozstrzygnąć IO-01; oddzielić read/write syscalls, serializację, GPU host transfer i MPI wait.
- Wybrać najwyżej jeden wynikający z profilu kandydat spośród IO-02/03/04. Uzasadnić go spodziewanym zyskiem E2E.
- Wykonać test na małym kontrolnym output, potem na tym samym medium fixture, jeśli wynik uzasadnia pełniejszy run. Porównywać dokładnie te same wejścia/config/build.
- Każda implementacja wymaga kompletności/odczytywalności outputu i poprawności obserwabli RF/field; na koniec agent główny ponownie waliduje zintegrowaną zmianę. Wspólne PLAN/MILESTONES/PROGRESS aktualizuje tylko koordynator.

## Niezmienniki i ograniczenia

Zwykły cache wejść/wyników oraz sporadyczne odczyty i niewielkie zapisy SSD są dozwolone. Nie implementować solver spill, disk basis ani RAM/VRAM offloadu do SSD. Nie ograniczać pól/CSV domyślnie w celu poprawienia timera. Każda redukcja lub zmiana precyzji outputu musi być jawna, opt-in i sprawdzić, czy zachowuje analizę i formaty używane przez użytkownika. Far-field obliczeniowy jest liczony w `POSTPRO_FARFIELD`; część jego tabel/plików może być poza `Timer::IO`.


## Wyniki nowych eksperymentów

### IO-01-E01 — M0: odczyt archiwum i kontrakt replay (`PASS`, zakres: archived readback)

Owner: GPT-6.1 Sol high I/O; branch `opt/io-20261029`; baza `ab4b3a6dbd`; 2026-10-29.
Historia: IO-01/02 źródła przejrzane wcześniej; brak wcześniejszego native replay.
Nie jest to pomiar kosztu natywnego writera ani zaliczenie IO-01/02 performance.
Źródła: `tablecsv.cpp:164–179` formatuje wszystkie wiersze; `:301–308`
usuwa poprzedni plik i pisze pełną tabelę. `postoperatorcsv.cpp:1143–1164`
wywołuje pełny zapis po każdej aktualizacji S; `:341–355` pozwala ponownie
wypełnić ten sam index częstotliwości dla kolejnego źródła. `:376–445`
waliduje zgodność nagłówków i długości grup kolumn przy restart/reload.

Kluczowy niezmiennik: drugi port uzupełnia istniejący wiersz. Przy source-major
sweepie może uzupełniać wcześniejsze wiersze tabeli, podczas gdy późniejsze już
istnieją dla pierwszego źródła. Zwykłe append-row jest niepoprawne. Native reader
pomija NULL i odbudowuje prefixy kolumn; nie wolno zmieniać semantyki częściowych
kolumn, kolejności nagłówków, precyzji oraz restart/adaptive cursor.

Dodano read-only `tools/stage_io_reference.py` oraz 4 testy w
`tools/tests/test_stage_io_reference.py`. Helper sprawdza rzeczywiste małe outputy:
shape, finite values, trailing NULL bez dziur wewnętrznych, final newline,
pełny schemat S dla obu portów i kolejność częstotliwości. Zapisuje hashe
metadata/CSV/źródeł I/O, źródłowy build manifest i dokładny image z argv.
Hash mesh jest odczytany z istniejącego fixture, nie przeliczany ponownie;
zgodność mesh/source/binary należy także do wspólnego M0.1/M0.2.

Polecenia wykonane bez GPU, builda, zmian usług lub cloud:

```sh
python -m unittest discover -s tools/tests -p test_stage_io_reference.py
python tools/stage_io_reference.py /home/sieciowiec/dev/python/anteny/artifacts/tshaped/port-repair-20261028/rear-route-sma-only/run-local-stages-20261029 --output artifacts/optimization-stages/io-m0/archive-readback.json
```

Wynik: 4/4 Python PASS, archiwum readback PASS; 10 output files,
2 828 843 B ogółem, 8 CSV / 2 723 651 B, S 480 B / 1 wiersz / 9 kolumn / 0 NULL.
Brak VTK w tym runie. Odczyt inspekcyjny Python ≈0,032 s, **nie czas natywnego I/O**.
Jedyny zapis to JSON raportu 193 844 B poza Git. Nie mierzono peak RAM,
systemowych read/write bytes ani wydajności funkcji C++; wszystkie te pomiary NOT RUN.
Referencja nadal O2/PA1, GPU/UVM, FP32 basis/FP64 arithmetic, cuDSS native complex
coarse, 1,92 GHz / oba źródła; helper nie zmienia konfiguracji.

Artefakt: `artifacts/optimization-stages/io-m0/archive-readback.json`.
Źródłowy manifest SHA a6ec732f11cc7fe920365ba2aae354b68fe97e81f732d5afd4659ed5187c3338;
image faktycznego runu 43ac46f6430cf44d7a2da0a618a0f5c67c6965cca2fde510f2a96116333e6d76.
Port-S SHA b4e4fcdf9dfdbc3f6b9499a9b0ee9b5dd7f34011be701a40c99f4a90ff3677ee.
Pozostałe hashe i native build fingerprints w raporcie.

### IO-02-E01 — M0: natywny micro bez solve (`TODO_TO_CHECK`; test przygotowany)

Istniejący target `unit-tests` / binarka `palace-unit-tests` obejmuje
`test/unit/test-tablecsv.cpp` i `test-postoperatorcsv.cpp`. Native table tests
sprawdzają format/parse/reload; PostOperatorCSV ma dokładne regresje restartów
jednego i dwóch źródeł, niezgodne nagłówki, liczbę i wyrównanie kolumn.
Nie tworzyć drugiego silnika tabel w Pythonie do porównania wydajności.

Dopisano native regression `TableCSV_WriteFullTableTrunc_PartialExcitations`
do istniejącego `test-tablecsv.cpp`: po cztery małe snapshoty source-major i frequency-major
(zapełnianie NULL w poprzednich lub bieżących wierszach), byte-for-byte porównanie writera
z natywnym formatterem i reload wszystkich kolumn po każdym zapisie.
Istniejący fixture PerRankTempDir zapewnia cleanup; output < kilka kB. To zachowuje obecną
semantykę, nie zmienia kodu produkcyjnego. **Test C++ nie zbudowany i NOT RUN**.

Prośba do koordynatora o slot/build-cache: uruchomić istniejący cached
`palace-unit-tests` (jeśli obejmuje tę rewizję testu), albo przyrostowo
przebudować tylko test TU/target po uzgodnieniu Catch2 i native dependencies.
Nie dotykać wspólnego build dir/cache bez przydzielonego slotu.
Przygotowana komenda (ścieżkę ustala koordynator):

```sh
timeout 60s <cached-build>/palace-unit-tests '[tablecsv],[postoperatorcsv]' --device cpu --backend /cpu/self
```

Jeśli GPU-enabled build inicjalizuje HYPRE/CUDA nawet dla tego wyboru,
koordynator musi zastosować ustalony guard i zgodę na usługę przed wykonaniem;
worker nie uruchamiał binarki. Nie wykonywać testów `[Regression]`/pełnej anteny.
Po tym mierzyć native N vs 2N małych snapshotów, liczby bytes/calls i formatting
oddzielnie. Obecny pojedynczy punkt S ma tylko 480 B; wzrost O(N²) w sweepie to
hipoteza opłacalności, nie dowód, że to istotne 19,6 s z logu.

Ponowienie: zmiana schema/output schedule/native writer lub wejść; identycznego
archive readback nie powtarzać bez powodu. IO-01 performance i IO-02 speedup
pozostają TODO_TO_CHECK; IO-03 bez aktywnego VTK DEFERRED do realnego profilu.
Dalsze wykonanie po zintegrowaniu M0/M1 i przydzieleniu slotu przez root.


### IO-02-E02 — M0 light review / minimal Catch main (`PASS`, scope: review; native NOT RUN)

Na polecenie root ponownie sprawdzono semantykę NULL: `Column::format_row` daje
tekst NULL dla indeksu poza `data.size()`, a parser nie dopisuje żadnego elementu.
To brak wartości/prefix kolumny, nie NaN. Finite wartości całkowite w regression
pozwalają dokładnie porównać wektory; dodano jawne porównanie długości prefixów
oraz kontrolę obecności NULL w niekompletnej kolumnie. Test obejmuje teraz oba
porządki source-major i frequency-major. Cleanup zastąpiono istniejącą konwencją
`palace::test::PerRankTempDir` z test/unit/fixtures.cpp; bez nowego API tempdir.

Przygotowany `tools/stage_io_unit_main.cpp` to Catch Session + MPI Init/Finalize.
Nie inicjalizuje Device/HYPRE/CEED; odpowiada filtrowi `[tablecsv]` (8 test cases
z nowym testem) bez całej regresji/EM. Nie zastępuje pełnego PostOperatorCSV
restart testu: ten wymaga istniejącego normalnego unit-tests targetu lub później
wspólnego operator-aware main przygotowanego przez koordynatora.

Po przydzieleniu slotu/root środowiska: skompilować tylko nowy main,
test/unit/test-tablecsv.cpp i test/unit/fixtures.cpp, z bieżącymi headerami
Palace + dokładnie obecne MFEM/fmt/scn/MPI ABI oraz Catch2. Linkować z obecną
biblioteką M7, nie z historycznymi bibliotekami/headers PR60. Ustawić istniejącą
makrościeżkę PALACE_TEST_DATA_DIR na test/data tej rewizji. Nie rebuild dependency.
Nie skopiowano operator main ani nie zmodyfikowano wspólnych ustawień buildu.

Komenda po zbudowaniu: `timeout 60s <io-native-tests> '[tablecsv]'`.
Bez `--device`/`--backend`, bo ten minimalny main nie rejestruje takich opcji.
Sam build i native test nadal **NOT RUN**, brak slotu i celowo brak kompilacji.
Python 4/4 PASS oraz diff/docs check ponowione po zmianie testu/ledgeru.

### IO-02-E03 — M0 root integration review (`PASS`, scope: review; native NOT RUN)

2026-10-30, Sol high: docs-garden i source review integracji w root Palace.
Sprawdzono opt-in PALACE_STAGE_STOP, guard single-rank, fixed-mesh/uniform Driven
operator case i stop przed ComplexKspSolver; sidecar/marker jawnie wykluczają RF.
Sprawdzono native CSV regression (prefixy NULL i oba harmonogramy) oraz minimalne
mains. Nie znaleziono blokującego błędu C++; normal flow nadal wymaga runtime smoke.
21 lekkich Python testów w root, docs checker i diff check PASS; build/native NOT RUN
w zakresie tego review. Źródła wspólne nietknięte podczas równoległego slotu buildu.
Root otrzymał konkretną usterkę dokumentacji: INDEX nadal opisywał wykonanie
jako nieaktywne, mimo Mode goal / Active M0. Naprawa wspólnego pliku należy do root.
Guard diagnostyki operatorów odrzuca liczniki LinearSolve/EigenvalueSolve; waveport
normalization może w przyszłości wymagać osobnego zakresu. Obecna kwalifikacja
jest planowana dla znanego lumped-only fixture; nie twierdzić ogólnej obsługi waveport.

### IO-02-E04 — M0 natywne CSV testy (`PASS`, scope: parser/writer/readback correctness)

2026-10-30, root udzielił osobnego slotu build/test. Wykonanie w root checkout
`/home/sieciowiec/dev/cpp/palace`, bez rebuild libpalace/dependencies i bez solve.
Nowe source fingerprint **131d5da3bf54eea5375ce41dfcf718aa9d2e466b8bf6a2abedcb60e152e2d8eb**;
aktualna libpalace **d1887e64cbd7a0045475b8f84b220f3b8d49666bb3edbf5503ae4987a9002f1b**.
Image **219cb96c3b3956f78beaf037f3ebb52bd02ab014765ab3918c9d21a72dae7e9e**.
Pełne hashe main/test-tablecsv/fixtures/Catch2/current native w `inputs-before.json`;
sprawdzone ponownie po kompilacji i teście: bez zmiany source/native/test inputs.

Zachowany M7 CXX flags + bieżące Palace/MFEM4.9/fmt11/scn4/MPI headers,
wyłącznie Catch2 z stage/deps. Przebudowano trzy TU: `stage_io_unit_main.cpp`,
`test-tablecsv.cpp`, `fixtures.cpp`; link jawnie z `/stage/native/libpalace.so`.
Nie zbudowano ani nie uruchomiono starej binarki PR. Macro danych to rzeczywiste
`PALACE_TEST_DATA_DIR="/src/palace/test/data"` (nie test/unit/data).

Izolowany kontener `palace-stage-m0-io-20261030`: network none, CDI NVIDIA bez
szerokiego host bind, OMP1/OpenBLAS1, cpus2, memory8GiB=memorySwap8GiB,
core0. Loader: `libcuda.so.1` → `/usr/lib/libcuda.so.615.78.08`, 112 668 520 B;
ldd potwierdza current `/stage/native/libpalace.so`, fmt11/scn4/MFEM4.9.
Nie inicjalizowano MFEM Device/HYPRE/CEED, nie wywołano EM/GMRES.
Przed startem: usługa inactive/dead/MainPID0, actual inference guard [].

Wykonane native argv wewnątrz kontenera:

```sh
env LD_LIBRARY_PATH=/stage/native:/opt/view/lib:/opt/cudss/lib:/usr/local/cuda/lib64 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 timeout -k 3 60 /stage/io-native/io-unit-tests '[tablecsv]'
```

**8 test cases / 182 assertions PASS, exit0**, w tym nowa regresja obu harmonogramów
z trailing NULL i ponownym wypełnianiem wcześniejszych wierszy. Runtime testu
0,214 s; łączna kompilacja/link 7,231 s (limit120s, jobs1); cały slot10,172 s.
To czasy smoke, **nie benchmark natywnego I/O ani speedup anteny**.
Native test EXE SHA **9bed794345c19cfec664571dbcec2f4b85ed1fc81e99926e2c730859b1bf03b6**.
Zwykłe małe snapshoty CSV; osobnego systemowego pomiaru bytes/read/write/peak
RAM nie wykonano. Pełne PostOperatorCSV restart tests nadal NOT RUN w tym slocie.

Dowody: `/home/sieciowiec/dev/cpp/palace/build/optimization-stages-m0-20261030/io-native/`:
`commands.jsonl`, `events.jsonl`, `compile-result.json`, `test-results.json`,
`resource-policy.json`, `io-unit-test.log`, `io-unit-ldd.log`, `loader-proof.log`,
`inputs-before.json`, `cleanup.json`. Kontener po slocie exited; żaden Palace
container nie pozostał aktywny. Oryginalne cache/buildery pozostawiono zatrzymane.

Pierwszy preflight przed utworzeniem kontenera miał błąd wrappera `check_output`
dla oczekiwanego systemctl inactive/exit3; nie rozpoczęto wtedy kompilacji/testu.
Zapisano `preflight-attempt1.json`, poprawiono jawne sprawdzanie statusu oraz
inference guard, root potwierdził kontynuację tego samego slotu. To korekta harnessu,
nie negatywny wynik performance i nie fallback na inne biblioteki.

Decyzja: natywna semantyka table/partial rows zakwalifikowana w CPU smoke,
M0 I/O gotowe do integracji. IO-01 profiling, IO-02 opłacalność/speedup i pełne RF
pozostają TODO_TO_CHECK. Następny etap dopiero po zatwierdzeniu M0 przez root.

### IO-01-E02 — M1 source-only instrumentacja i bounded replay (`PASS`, przygotowanie; wykonanie w E03)

2026-10-30, GPT-6.1 Sol high; branch `opt/io-20261029`, baza febdc6eb9.
Historia: M0 potwierdził native table correctness (182 assertions), ale nie koszt I/O.
Root medium operators-only ma IO18,6966 s bez jakichkolwiek CSV. Zatem CSV nie
wyjaśnia tego czasu; preprocess worker instrumentuje rzeczywisty mesh input/parser.
Nie promować IO-02 append ani header-wide zmian tylko dlatego, że są łatwe.

Patch obejmuje wyłącznie produkcyjny `palace/utils/tablecsv.cpp` (jedna TU) oraz
hidden native replay w istniejącym test/unit/test-tablecsv.cpp. Nie zmieniono
outputdir.hpp, serializerów VTK, parsera mesh, formatów lub kolejności operacji.
Root posiada wspólny nowy utils/stageprofile.hpp; wywołania StageProfile wymagają
zintegrowania tego headera przed buildem. Brak kopii/zmiany headera w tym branchu.
Defaulty, wyjątki i lifetime buforów pozostają takie same; brak CUDA synchronizacji.

| Label (PALACE_STAGE_TRACE=1) | Zakres |
|---|---|
| io.csv.format_table | Całe istniejące formatowanie nagłówka i wierszy do string; jedna para eventów na tabelę |
| io.csv.parse_table | Cały natywny parser CSV; brak eventów per cell/element |
| io.csv.reload | Existing-file constructor: exists/open/read/copy/parse; tylko gdy load_existing_file=true |
| io.csv.read_buffer | Istniejący odczyt ifstream do stringstream oraz close; koszt CPU+page-cache/syscall, nie sam fizyczny dysk |
| io.csv.rewrite | Istniejące remove/open/format/print/destrukcja fmt::ostream (w tym flush); obejmuje nested format_table |

Są to host-wall/process-CPU **inclusive** scopes. Nie sumować rodzica z dzieckiem.
Różnica rewrite minus format to remove/open/print/flush/pozostałe koszty, nie czysty
pomiar fizycznego write. Reload minus nested read_buffer/parse zawiera open/check/
kopię stringstream.str i inne koszty. Root agregator musi zachować zagnieżdżenie.
Nie dodano wymuszonego flush/close, dodatkowych kopii ani nowej tabeli pośredniej.

Przygotowany hidden test `TableCSV bounded native I/O replay`, tag
`[.stage_io_replay][Serial]`: 16 i32syntetycznepunkty, 2źródła, 9kolumn,
32 i64snapshoty, reload po każdym zapisie z porównaniem wartości/nagłówków.
Domyślny filtr `[tablecsv]` nadal wybiera osiem zwykłych testów, bez replay.
Replay używa istniejącego C++ writera/parsera; nie jest Pythonem udającym benchmark.
Wejścia to skończone wartości całkowite/binarnie dokładne ćwiartki, aby nie maskować
błędów tolerancją formatowania. PerRankTempDir sprząta dwa małe pliki.

Raport PALACE_IO_REPLAY podaje rzeczywiste logical_bytes_written (suma długości
snapshotów), final_file_bytes oraz wall write/reload. Logical bytes nie są licznikiem
fizycznych zapisów SSD. Twardy limit sumy snapshotów <2MiB na serię; przy 16/32
punktach oczekiwane małe setki kB, brak stress-write. Runtime zewnętrznie ≤60s.
Nie mierzy tego samego, co pełna antena, nie jest podstawą do claimu E2E speedup.

Proponowane argv po przydzieleniu jednego wspólnego cached build slotu:

```sh
timeout 60s <fresh-io-native-tests> '[tablecsv]'
env PALACE_STAGE_TRACE=1 timeout 60s <fresh-io-native-tests> 'TableCSV bounded native I/O replay'
timeout 60s <fresh-io-native-tests> 'TableCSV bounded native I/O replay'
```

Ostatnia para to trace on/off w oddzielnych procesach, ponieważ Enabled cache jest
inicjalizowany raz na proces. Mierzyć narzut; kilka powtórzeń tylko gdy koszt próby
uzasadniony. Zamrozić source/header/binary/ABI i bounds jak w M0. Replay bytes/timing
zostaną dopisane dopiero po runie. Obecnie C++ nowego patcha **NOT BUILT / NOT RUN**.
Readback Python4/4 i diff/docs checker PASS po edycji; nic nie uruchomiono na GPU,
nie zmieniano usług/cloud ani wspólnego build cache. Żaden kandydat M2 nie wybrany.
IO-03 VTK pozostaje DEFERRED, bo referencja go nie generuje i instrumentacja szerokich
nieużywanych ścieżek nie uzasadnia dodatkowego buildu.

### IO-01-E03 — M1 native micro / trace OFF→ON (`PASS`, scope: bounded replay)

2026-10-30; root przydzielił slot, pozostały agent tylko edytował child tree.
Root source **3bae7f768d18d24545c110e0f8bf8d46e7467cbb5ce07879ba37da014a2eb2c3**,
libpalace **30747059009a6f0cc3c52b4662d7a67d255f4b4c678667faf340608d37435714**,
image **4a314d49b81c31ef6b99fde45a12ceb1ad823083ba68d3eb3cb1feb51e5aba19**.
Żadnego rebuild libpalace/deps. Same flags/ABI i Catch2 z M0; trzy małe TU
(main/cases/fixtures) + link7,282 s, całe provision/compile/test/cleanup10,729 s.
Native test EXE **d8f3a0938be8712d9d180512a9c002189bf044c2dcc3069d738e5392974f7f01**.
Full source/native/test-input fingerprints przed/po zgodne.

Guard service inactive/dead/MainPID0 + inference[], CDI only, 8GiB/noSwap,
core0, OMP1/OpenBLAS1, cpus2, jobs1. Root/mount source read-only,
jedynie świeży test output RW. Loader aktualny libcuda, bieżące fmt11/scn4/MFEM4.9,
bez PR libraries. Normalny `[tablecsv]`: **182 assertions / 8 cases PASS**, exit0.
Hidden replay osobno OFF iON: **1920 assertions / 1 case PASS każdy**, exit0.
OFF jawnie env -u PALACE_STAGE_TRACE; ON tylko PALACE_STAGE_TRACE=1.
Pozostałe env/inputy identyczne. Case64-bit values/readback bez tolerancji.

| Punkty / snapshoty | Logical bytes written (OFF=ON) | Final bytes | Write OFF ms | Reload OFF ms | Write ON ms | Reload ON ms |
|---|---:|---:|---:|---:|---:|---:|
| 16 / 32 | 76 608 | 4 284 | 0,853 | 0,480 | 1,255 | 0,685 |
| 32 / 64 | 282 240 | 8 316 | 2,380 | 1,398 | 2,470 | 1,557 |

Podwojenie N dało3,684× logical bytes, zgodnie z full-rewrite narzutem; czasu nie
utożsamiać z idealną asymptotyką (jedna para i koszty syscall/cache). Cały zmierzony
write+reload OFF5,112 ms vsON5,967 ms, około+16,7% w tym mikro. **Nie zaliczono
progu ≤1% narzutu reprezentatywnego profilowania**; overhead kilku eventów na małą
tabelę może dominować i wymaga osobnego reprezentatywnego pomiaru M1.2. To nie
speedup i nie wpływa automatycznie na koszt medium operators-only bez CSV.

Root `tools/stage_profile_report.py` sparsował trace bez niedomkniętych zakresów:
480 scopes =96×5. Exclusive czasy: format2,175 ms, parse1,659 ms,
rewrite poza format1,465 ms, reload poza dziećmi0,367 ms, read_buffer0,146 ms.
Sum exclusive5,812 ms; nie sumowano inclusive rodziców z dziećmi.

Dodatkowo odczytano końcowe `/proc/PID/io` natywnego childa w stanie zombie
przed reaping (`waitid WNOWAIT`), potem normalne wait. Oba runy miały
write_bytes548 864 i cancelled_write_bytes548 864; OFFread_bytes0,
ONread_bytes8192. To cały proces z loaderem/trace/page-cache, nie sam CSV i nie
pomiar zużycia SSD; nie wyciągać twierdzenia o fizycznym zero zapisów.
Wszystkie snapshoty <2MiB/serię, małe zwykłe pliki wyniku, bez solver offload.

Dowody w root `/home/sieciowiec/dev/cpp/palace/build/optimization-stages-m1-20261030/io-native/`:
`io-build-test.py` jest w katalogu nadrzędnym; dokładne argv w `commands.jsonl`,
`inputs-before.json`, `final-inputs.json`, `compile-result.json`, `test-results.json`,
`replay-results.json`, `replay-{off,on}.log`, `replay-{off,on}-proc.json`,
`replay-on-profile.json`, `resource-policy.json`, `io-unit-ldd.log`, `loader-proof.log`,
`cleanup.json`. Kontener palace-stage-m1-io-20261030 exited, brak aktywnych
Palace containers; slot zwolniony. Nie zmieniano usług ani zależności.

Decyzja: IO-01 instrumentation/readback scope PASS. IO-02 optymalizowanie małego
port-S CSV jest **DEFERRED dla obecnego operators-only workload**, który nie tworzy
CSV: nie wyjaśnia18,7 s IO. Full-rewrite koszt potwierdzony w syntetycznym małym
sweepie, ale few-ms koszt i zero takich wywołań w diagnozowanym runie nie uzasadniają
M2 writer patcha. Wracać dopiero przy profilu realnego pełnego sweepu/dużych tabel
pokazującym mierzalny udział E2E, zachowując prefixy obu źródeł i restart. IO-03
VTK nadal DEFERRED (brak VTK). Wniosek priorytetowy: profil mesh ASCII input CPU
od preprocessing, nie zmiana dysku/wyłączanie outputu. M1/M2 zamyka koordynator.

## IO-06 — lossless native/binary mesh input (`IN_PROGRESS`, M2 feasibility)

2026-10-30, Sol high, branch opt/io-20261029 base ff97f08bc. New evidence:
R2 native MFEM ASCII read18,7523 s wall/18,7095 s CPU, no CSV; current IO-02 writer
DEFERRED. Hypothesis: existing supported binary2.2 reader or native input cache
can remove text parsing on later runs. Before code: inspect exact pinned MFEM4.9
reader/format/API and existing Gmsh/converters, no dependency installs.
Owner geodata/meshio remains PRE; this track owns only converter/preflight tools,
tests and ledger. Root/preprocessing receive any parser patch request.

Limits: source files from stopped builder read-only, Python tiny/replay≤60s and
small ordinary outputs; no medium conversion/build/EM/services/cloud. Cache must
preserve all curved P2 node coordinates, tetra orientation/connectivity, physical
and boundary IDs and port mapping, not just counts. Cold conversion/bytes/writes
are charged; warmload comparison later with same fixture/flags. Reject unsupported
binary before custom parsing; compression alone does not eliminate CPU parser.
Fingerprint of current production reference: R2 source0341e500..., lib0546c1cf...;
exact audited MFEM source hashes/tool versions are to be recorded per attempt.
M3 still requires native topology/orientation/operator-action/fields qualification.

### IO-06-E01 — source/API audit + tiny binary cache prototype (`PASS`, scope: feasibility/Gmsh roundtrip)

Pinned source odczytany przez `podman cp` z **już zatrzymanego buildera**
`palace-stage-m1-r2-build-20261030`, senza start/build/run:
`/tmp/root/spack-stage/spack-stage-mfem-4.9.0-nucrpyipn2tktie6vyzz2hakdcgklpd6/spack-src/mesh/mesh_readers.cpp`.
SHA **b8083d734225a92815ba6d288172b94a85a1efecae520b2f41d8e1828524ed7a**,
Kopia z licencją w ignored artifacts/optimization-stages/io06-feasibility, poza Git.

Fatti del reader MFEM4.9:
- ReadGmshMesh1515+: legge versione/binary/dsize; binary marker int1 a1530–1538.
- Nodes1589–1593: node tag int +3double via `input.read` perbinary, versus formatted
  numeric extraction perASCII. È supportata la MSH2.2 binaria, non serve parser Palace nuovo.
- Elements2167–2215: header tipo/count/n_tags e connectivity via input.read; primo tag
  è phys_domain, secondo elementary domain. Il percorso ASCII è il ramo successivo.
- Entrambi chiamano lo stesso AddElement e HO maps (tipo9 triangleP2, tipo11tetP2,
  mapping a2437): non si deve abbassare order/curvature per usare il binary.
- Baseline reale letto solo nell'header: `$MeshFormat / 2.2 0 8`, 355 110 567 B;
  confermata necessità/opportunità di conversione, non era già binary.

Tool disponibile senza installazioni: antenna `.toolchain/gmsh-venv/bin/python`,
Gmsh **4.15.2**, libgmsh SHA **9db3090d3b720c57b76bcbfa01d13854823ae2698c91343c20bdd4c2b81f6317**.
API standard Gmsh open/write e getNodes/getElements/getPhysicalGroups usate; nessun
custom parser completo. Nuovo `tools/stage_mesh_binary.py`: default input/output≤4MiB,
accetta solo ASCII2.2 FP64 con sections MeshFormat/PhysicalNames/Nodes/Elements,
P2 tet/tri/segment e physicalpoints, unpartitioned e singolo positivephysicalgroup
per entity. Unsupported metadata/multiphysical/partition viene rifiutata.

Export options: MshFileVersion2.2/Binary1/SaveAll0/**Renumber0**. SaveAll1 può perdere
physical tags inMSH2; Renumber0 evita cambi di ID. Si confronta input vs riapertura
binary: bits delle coordinate via float.hex, tutte le connettività high-order
nell'ordine locale (orientazione), element/node ID, physical ID/names e membership
entity. Count da soli non bastano. Questo confronto è **Gmsh-API semantic**, non
ancora prova che MFEM produca gli stessi DOF/operatori/campi.

Cache key: source content SHA, converter SHA, gmsh versione/library SHA, pinned
MFEM reader source SHA e options. Manifest: source/binarybytes+SHA e semantic
witness; HIT ricontrolla hash/header senza inizializzare Gmsh. Corruzione/identity
mismatch non sovrascrivono cache. Cold candidate in directory temporanea propria,
rename solo dopo roundtrip, cleanup su errore. È raw input untransformed cache:
materiali/config vengono applicati normalmente dopo MFEM Load, non sono dati di
solver/factorization cached. Geometry change modifica source SHA e richiede nuovo key.

Eseguiti 7 test Python stdlib (0,001s): inputbudget/formato/metadata, cachecorruption,
source/reader invalidation, e same-count perturbations di coordinate P2, localnode
orientation e portattribute. Gli ultimi test chiamano semantic_snapshot su API stub,
non sostituiscono prova del reader o qualifica geometrica native.

PoC concreto: creata piccola sfera con Gmsh esistente, meshcurvaP2 (130nodes,
100surface+volumeelements, tipi9/11), physicalvolume1 e boundary21. ASCII11 896 B →
**binary9 403 B**, roundtrip semantic completo PASS e secondo lookup **HIT**.
Cold conversion0,0864s / HIT lookup0,0401s / intero tiny generation+PoC0,1556s.
Sono tempi di API/cachesetup su tiny, **non warm-load MFEM né speedup antena**.
Nessuna lettura completa/conversione del 355MB mesh, nessun build/EM/service/cloud.

Riproduzione eseguita con timeout60s:

```sh
python -m unittest discover -s tools/tests -p test_stage_mesh_binary.py
/home/sieciowiec/dev/python/anteny/.toolchain/gmsh-venv/bin/python artifacts/optimization-stages/io06-feasibility/tiny-poc.py
```

Artefatti in `artifacts/optimization-stages/io06-feasibility/`: pinnedreader source,
`curved-p2-sphere-ascii.msh`, `tiny-poc-result.json`, `cache/<key>/mesh.msh` +manifest.
SourceASCII SHA0917bc9fd61fd1c907d66edd45c5abab28010013ba71acdb2d31d2da1d8bf301;
converter SHAf7c8f1e56740f54f218418c919ae8735076639cf6230e163d20996408e946d90.
Poc script wymaga nowego katalogu cache do powtórzenia cold assertion; HIT nie
jest błędem, ponowienie cold bez nowego pytania nie jest potrzebne.

**Wybrany prototyp IO-06**: istniejący binary2.2 input cache; bez zmiany Palace
geodata/meshio. Cold conversion i hash/readback potraktować jako dodatkowy koszt,
na HIT także hashvalidation ma koszt. Na zmieniającym się mesh cold cache może
nie dać korzyści; ROI wyznacza Ccold/(Tascii−Tbinary), nie sam rozmiar pliku.
Bezpośredni binary export z generatora mógłby uniknąć konwersji, lecz obecne
antena preprocessy modyfikują tekstowe MSH (m.in. metal_boundaries.py); najpierw
zakończyć te poprawki i dopiero cache. Repo anten pozostało read-only.

Następne po root slot: native MFEM tiny ASCII↔binary preprocess (ta sama curvature,
attrs, raw geometric nodes/connectivity/mesh inventories), potem operator-action
oraz pola w M3. Dopiero przy PASS jednorazowy medium conversion/warm-load trial
z jawnym zwiększeniem małego limitu/budżetu; 4MiB CLI celowo blokuje pełny mesh.
Test native MFEM **NOT RUN**, medium performance/quality **NOT RUN**. Integracja
z PRE03 konieczna później: usuwa inne serialize/reparse w Partition, podczas gdy
IO06 dotyczy początkowego parsera. Oszczędności nie sumować bez pomiaru combined.

### IO-06-E02 — native MFEM tiny equivalence (`PASS`, tiny CPU geometry/operator/field scope)

Root udzielił native slotu: compile≤120s/jobs≤2, runtime≤60s, tiny input only,
CPUOMP1/cpuself/8GiB/noSwap/core0/CDI + wspólny ROOT host lock. Źródła i dane tylko
read-only; użyć istniejącej M1R2 lib0546c1cf/source0341e500 i tych samych publicheaders,
bez build Palace/libMFEM. Plan: nowy mały Catch testcase + istniejący root main.
Porównać dokładnie Nodes FPbits, vertices/connectivity/orientation/attrs/names/P2,
transform/Jacobian/quadrature, signed ND DOFs, oddzielne mass/curl operator actions
relL2≤1e-12 dla stałych seedów oraz physicalND/curlfield values. Jeśli native fails:
stop, bez poluzowania progu lub niejawnej permutacji. Ten etap nie obejmuje 355MB
ani antenowej kwalifikacji RF. Dowody do ROOT build/optimization-stages-m2-io-20261030.

IO-06-E02 wynik rzeczywisty: **22 986 assertions / 1 case PASS**, exit0,
0,529s native test; 2TU+link5,199s, cały slot8,451s. Nowy testcase
`tools/stage_mesh_binary_test.cpp` z istniejącym root stage_operator_unit_main;
żadnego rebuild Palace/MFEM. Użyta M1R2 source
0341e50051ac29e585c3b211d73fd44e89beb1fb583280541bae743589e3372b,
lib0546c1cf8855d26a656a9c5791a03bb3882201095104ac0a7b04436fc213fcf9,
image7d6096526275f2f56de270768a3ad29f8d774f9efa5a4f756b0cc6799063ea9e.
Test CPP SHA12e4f67f369f121537da8933ced441976c9213a53441cbf64cbd334d038969ed;
EXE SHAb1327c951dde68418634c1a30d89ebdb6776eea2bddfc337a1386208435c91c5.

Actual MFEM decoding: NV28 / NE50 tetra / NBE50triangles / P2nodevalues390
(130Gmsh high-order nodes). W obu mesh dokładne bitwise vertex coordinates
oraz całe GetNodes, ta sama kolejność i bez permutation fallback. Zgodne lokale
corner IDs, types, attributes, physicalname sets (`dielectric`=1,
`port_boundary`=21), boundary winding i zerowa liczba błędnych orientations.
Wszystkie domain/boundary quadrature order5: transformed positions i Jacobian
entries **dokładnie równe**, dodatnie volume determinants / weights i zgodne
integrated volume/area. Signed ND2localDOF arrays zgodne; global ND454DOFs.

Oddzielne assembly/multiply mass i curlcurl, trzy stałe seedy42/314159/271828:
**każde relativeL2=0** (bramka≤1e-12). PhysicalND i curlfield values dla ustalonej
arbitralnej funkcji po wszystkich volumequadraturepoints: **maxabsoluteL2=0**.
To field interpolation/geometry/action equivalence bez GMRES i nie drivenRFsolve.
Żadnego zmniejszania tolerancji, zmiany probes ani niewykazanej permutacji.

Pełne provenance/argv/flags/source-native-main-Catch2-input hashes, ldd/driverloader,
containerresourcepolicy i raport w ROOT
`/home/sieciowiec/dev/cpp/palace/build/optimization-stages-m2-io-20261030/`:
`build-test.py`, `result.json`, `inputs-before.json`, `inputs-after.json`,
`compile-result.json`, `commands.jsonl`, `events.jsonl`, `native-test.log`,
`resource-policy.json`, `ldd.log`, `driver-loader.log`, `inference-guard.json`,
`cleanup.json`. Rootsource/native/testinputs przed/po bez zmian; binary9403B,
ASCII11896B SHA zgodne z E01. C++ input paths ustawione przez kontroler env
PALACE_IO06_ASCII/BINARY, oba pod readonly mount; kontroler wymaga≤4MiB każdego.

Kanoniczny ROOT host_lock_path blokowany przez cały slot; guard service
inactive/dead/MainPID0 + inference[], OMP1/cpuself/cpus2/8GiB/noSwap/core0,
CDI libcuda615.78.08, Catch2 tylko z M0/deps, aktualne M7 headers/MFEM/fmt11.
Nie zmieniono .toolchain lub rootcompilerinputs. Kontener
palace-stage-m2-io-tiny-20261030 exited/OOMfalse, żaden Palace nie został aktywny;
lock zwolniony przy wyjściu kontrolera. Parent otrzymał raport i slot zwrócony.

Decyzja: IO06tiny native equivalence bramka PASS, prototyp gotowy do oceny root.
Native medium/cold-vs-warm performance oraz driven complexS/fields/energy nadal
**NOT RUN**. Nie uruchamiać tego tiny assembled-matrix testcase na 355MB mesh:
jego full sparse ND forms są celowo tylko dla małego testu. Medium będzie wymagało
osobnego bounded preprocess/operators-only recipe i pomiaru amortyzacji konwersji;
pełna kwalifikacja i integracja z PRE03 należą do M3/M4. Poza tym slotem nie
konwertowano pełnej anteny i niczego nie uruchomiono na cloud.

### IO-06-E03 — full ASCII source metadata preflight (`PASS`, one read-only metadata/hash pass)

Root udzielił jednego wolnego slotu wyłącznie na streaming metadata/hash źródła
355110567B / SHA2af1b2ac..., limit≤400MiB/30s/mały RAM. Bez Gmsh fullmodel,
konwersji, binarywrite i bez parsowania współrzędnych do floats. Zliczyć sections,
nodes/elements/types/nTags/int32 i grupyphysicaltags per(dim,geometricentity), aby
wykryć mixed linear triangles lub multiplephys zanim drogi converter straci dane.
ROOT host_lock i exactservice0/noinference obowiązują. Native tiny scope E02
pozostaje bez zmian. Planowany nowy tools/stage_mesh_preflight.py, mały JSON.
Header validator w converterze zostanie przerobiony na streaming, bez zwiększania
limitu 4MiB lub zmiany binary export options; nie powtarzać natywnego readera.

E03 zakończony jednym streaming read355110567B, exactSHA
**2af1b2ac9dfd0d785ac7e0a865f26eb2dac447ec9f90ea40d85056c5491452b3**,
**5,349s / maxRSS25092KiB**. Rootsharedlock held; serviceinactive/deadPID0 i
noinferenceguard. Zero Gmsh fullmodel, zero konwersji, zero native/EM/GPU, zero
modyfikacji wejścia. Output2598B w child
`artifacts/optimization-stages/io06-feasibility/full-source-preflight.json`.

Fakty: nodes2721015, elements2130744 = triangleP2type9 **430084** +tetP2type11
**1700660**; wszystkie nTags2. Node tags strictlyincreasing1..2721015,
elementtagrange1..2130744, nodeRefRange1..2721015; int32/nonpositive-ID/widtherrors0.
669(dim,geometricentity) groups; **0 multiplephysical entities**, brak unsupported
sections/types. Currentconverter type/entity gates przechodzą. Rawsource ma tylko
bdrIDs10/20/21/22, volumes1..8. Nativebdr510048 z E01/E02 referencji obejmuje dalsze
przygotowanie boundary; różnica wobec430084 rawsurfaces nie oznacza utraty danych
przez converter (nie wykonano go). Nie policzono duplikatów elementtagów lub pełnej
nodeRef membership, nie parsowano współrzędnych; nie jest to native kwalifikacja.

Szacunkowy bodybinary =2721015×28 +430084×36 +1700660×52 =180105764B plus małe
headers/blocks/physicalnames; **to tylko estimate**, nie zmierzony plik/czas/peak.
Wcześniejsze obawy o linearboundarytriangles lub multiphysical-perentity nie
potwierdziły się na tym konkretnym źródle. Nie wyłączono walidacji, nie zmieniono
physicaltags i nadal brak pozwolenia na pełną konwersję. Parent dostał fakty.

Zmiana tools/stage_mesh_binary.py/check_source: streaming line iterator zamiast
read_bytes().splitlines() przy sprawdzaniu sections; nadal default4MiB i te same
exportoptions/semantic guards. New converterSHA
**e2053c179d686c3642071b671ab702868970a22af81afadaa5160e417b5a597d**;
zmienia key dla przyszłych cache, stare tinybinary/nativeproof pozostają historyczne
z ich starym helperSHA i niezmienionymi danymi. Bez regeneracji tiny lub native retry.
Nowy metadatahelper tools/stage_mesh_preflight.py SHA
**14b568713faaf87f9e9a65e865a27b79bb00172a30835b998fa1417759775491**.

9 lekkich Python PASS (7 converterguards/digest +2 preflightgate/hash/budget),
diff/docs check PASS. Dokładna komenda wykonana raz:

```sh
timeout -k 2 32s python tools/stage_mesh_preflight.py /home/sieciowiec/dev/python/anteny/artifacts/tshaped/port-repair-20261028/rear-route-sma-only/run-local-stages-20261029/mesh/pcb.msh --expected-sha256 2af1b2ac9dfd0d785ac7e0a865f26eb2dac447ec9f90ea40d85056c5491452b3 --expected-bytes 355110567 --output artifacts/optimization-stages/io06-feasibility/full-source-preflight.json
```

Root decyduje o dalszym budżecie cold fullconversion/warmload. MediumPerf i RF
nadal NOT RUN; nie powtarzać355MB scan bez zmiany źródła/błędnego guardu.

### IO-06-E04 — full cold conversion (`REJECTED` qualification: semantic witness mismatch; HIT NOT RUN)

Root powtórzył autoryzację po model-capacity failure, który nastąpił przed execution.
Sprawdzono: docelowy ROOT artifacts/optimization-stages/M2-IO06-20261030 nie istnieje,
brak unitów palace-io06-*, zero wcześniejszej pełnej konwersji. Jeden cold≤180s,
jeden HIT≤30s, input≤400MiB/output≤256MiB, systemd-user transient32GiB/noSwap,
CPUquota2/OMP1/core0, sharedROOTlock i hostfree/inference guards. Bez MFEMmediumrun.
CLI ma jawne --max-input-bytes/--max-output-bytes; defaulty pozostają4MiB,
nowy test args/defaults/negativebudget. Zachować APIcalls, source/reader/tool/Gmsh
fingerprints, semantic digest equality, memory.peak i cold/HIT koszty; nie przyjmować
ROI zanim nie ma measured nativebinaryload. Na błędzie stop i cleanup tylko własnego
nowego .candidate/cache prefix; żadnych dodatkowych pełnych konwersji/retry.

E04 wykonano **dokładnie jeden** cold, potem STOP. Gmsh openASCII → writebinary →
clear → reopenbinary → strict semantic_snapshot comparison **FAIL**:
`ValueError('Gmsh readback changed node bits/connectivity/physical metadata')`.
APIcount: initialize1/open2/write1/clear1/finalize1. **HIT nie uruchomiono**,
żadnego dodatkowego cold/conversion/MFEMrun ani retry/poluzowania walidacji.
To dowód niezgodności z obecnym witness, nie jeszcze wskazanie konkretnego
zmienionego pola lub potwierdzenie błędu fizyki.

Nativeboundscold potwierdzone przed releasegate: user systemd transient
palace-io06-cold-20261030.service, actual memory.max34359738368/swap.max0,
cpu.max quota/period=2, LimitCORE0, RuntimeMax180s/TimeoutStop3s, OMP1/OpenBLAS1,
CPU-only, sharedROOT host lock. Cgrouppeak **2572705792B ≈2,40GiB**,
processmaxRSS2338864KiB; **nie OOM/deadline**, serviceResult exit-code/ExecMainStatus1.
Actor33,768s/unit34,236s. Fullmodel API started once, binarywrite at17,472s,
clear at18,237s, secondopen18,372s, failure/finalize33,712s.
Nie jest to użyteczny native speedup pomiar ani completedcachecoldtime.

Binary był zapisany raz i przeszedł sprawdzenie limitu≤256MiB, potem converter
finally usunął własny niepromowany .candidate. **Dokładny rozmiar/hash binary nie
został utrwalony przed exception/cleanup**; nie podawać estimate180MB jako pomiaru.
Nie ma poprawnego cachetarget ani danych HIT/nativewarmload/ROI. Wcześniejsza
sfera tiny/E02 nadal PASS w swoim zakresie, lecz nie kwalifikuje tego full case.

Ważne ograniczenie failure diagnostics: generic exception nie zapisał `before`
i `after` witness, więc dokładna różnica nodebits/connectivity/names/entitymapping
nie jest znana. Nie rekonstruowano jej nową pełną konwersją. Przed przyszłym nowym
pytaniem badawczym trzeba utrwalać różniące się witness keys i rozmiar binary
**przed cleanup**. Root dostał tę lukę wprost. Możliwy tani kolejny test po nowym
zleceniu: unnamedphysicalvolume (rawsource ma volume4 bez PhysicalName), wiele
entities i nieciągłe ID. To tylko hipotezy; żadnej nie sprawdzono automatycznie.

Dowody ROOT `/home/sieciowiec/dev/cpp/palace/artifacts/optimization-stages/M2-IO06-20261030/`:
`actor.py`, `supervisor.py`, `before.json`, `cold-plan.json`,
`cold-resource-policy.json`, `cold-telemetry.jsonl`, `cold-unit-result.json`,
`cold-actor-failure.json`, `cold.stdout.log`, `cold.stderr.log`, `commands.jsonl`,
`failure.json`, `cleanup.json`, `source-after-failure-stat.json`.
HelperSHA użyty w próbie **1e3b5e5f25d54a6b527139bacb9329acb3acdc1cb99ef784472863124d583c3a**.
Source start size355110567/SHAexpected2af1... oparty na E03, cold tool dodatkowo
hashował go dla identity; brak returnedmanifest po failure. Source size/mtime/inode
po failure identyczne z before. Nie wykonywano kolejnego355MBhash tylko dla
kosmetycznego after pola; sha-after-failure jawnie NOT RECOMPUTED.

Kontenerów nie uruchamiano; unit cold zatrzymany/reset-failed, list-units
palace-io06-* puste, lock zwolniony. Converter sam usunął jedyny własny tmp,
cachepozostał pusty; żadnego starego cache nie usuwano. Źródło/antena/.toolchain
nie były zapisywane; tylko zatwierdzony outputcache oraz małe logi/JSON. Nie ma
weryfikacji zużycia fizycznego SSD i nie formułuje się wearclaim.

CLI explicitbudgets4MiBdefault/positiveargs pokryte nowym testem; wszystkie
10 lekkich testów converter+preflight PASS przed próbą. Fingerprintsemantics/MFEM
konwersji nie zostały osłabione. Decyzja: Gmsh-based converter NIEPROMOWANY dla
full anteny. Parent wybiera dalszy zakres/negative assessment; bez kolejnych runów.

### IO-06-E05 — sparse-ID tiny numbering repro + failure witness (`PASS`, causal tiny-only)

Root podal nową konkretną hipotezę z pinned Gmsh4.15.2: niezależna opcja
Mesh.PreserveNumberingMsh2 domyślnie0, Mesh.Renumber0 nie zastępuje jej semantyki.
Official docs https://gmsh.info/doc/texinfo/gmsh.html#Mesh-options, entry
Mesh.PreserveNumberingMsh2: preserve numbering; ostrzeżenie multiphysicalentity
(prawdziwy source preflight miał0). Zgoda wyłącznie tiny≤4MiB/60s, sharedlock,
cgroup/core0/noSwap/CPUOMP1, bez kolejnego pełnego source/model/conversion.
Plan: sparse/permuted node+element IDs w wcześniej qualified curvedP2tiny,
old Preserve0 expected strictFAIL, Preserve1 expected strictPASS przy identycznych
pozostałych options i bez permutacji/tolerance relaxation. Dodać durablebounded
SemanticMismatch witness przed cleanup i meaningful unittest. To nie potwierdza
przyczyny wcześniejszego fullFAIL, dopóki nie ma nowego pełnego witness za zgodą root.

E05 rzeczywiście wykonany w osobnym transient userunit
palace-io06-numbering-tiny-20261030.service: MemoryMax8GiB/Swap0/CPUquota2,
OMP1/OpenBLAS1, core0, RuntimeMax60s, sharedROOTlock i exactinactive/deadPID0/noinference.
Sparse/permuted source **14930B**, poprzedni curvedP2sphere130nodes/100elements,
zmieniono tylko node/element ID i odpowiadające im references, nie współrzędne,
physicalgroups lub lokalne pozycje w connectivity.

**BEFORE old PreserveNumberingMsh2=0**, przy nadal Renumber0 i tych samych pozostałych
options, strict semanticFAIL odtworzony. NodeIDs10101/10202/10303… zostały zapisane
jako1/2/3…, elementIDs500037/500074/500111… jako1/2/3… . Dokładnie dwa zmienione
witness keys: node_bits_sha256 i oriented_connectivity_sha256. To expected test
failure, nie złagodzenie validatora. Physicalmetadata/order/type i counts zgodne.

**AFTER explicit PreserveNumberingMsh2=1**: wszystkie strict witness fields
identyczne, rzeczywiste sparseID obu klas zachowane, binary9403B. Nie wprowadzono
permutation tolerance, sortowania lokalnej connectivity lub rozluźnienia dokładności.
Testactor0,0868s, unit0,2094s, peakcharge14 680 064B; rootresource/timebounds
potwierdzone. Unit zatrzymany/reset, slot+lock zwrócone. **Żadnego full355MBread,
Gmshfullmodel, fullconversionretry lub MFEMrun** w tym zadaniu.

OPTIONS default teraz ma Mesh.PreserveNumberingMsh2=1 i key uwzględnia nową flagę
oraz helperSHA **a2490f7d6cbb3dc61e9712e40898c267fa3b77cfccdc54deb941c974067fc805**.
Recipe options kopiowane do identity, aby kolejny tryb w tym samym procesie nie
mutował wcześniejszego failuremanifest. Writer używa dokładnie tej kopii.

Naprawiono lukę diagnostyczną: SemanticMismatch zapisuje **przed cleanup** trwały
mały sidecar w sibling <cache>-failures, z compact before/after field summaries,
zmienionymi keys, pierwszym differing scalarpath i binarybytes+SHA. Nie wypisuje
nodearrays/elementarrays; hashe containers liczone streaming JSON encoder.
Rzeczywisty oldtinyfailure sidecar **2845B** pozostał po skasowaniu własnego tmp.
Nowy unittest sprawdza dokładne attrpath21→22 i boundedJSON przy dużej metadataliście.
Łącznie11 testów Python converter/preflight PASS, diff/docs check PASS.

Dowody ROOT `artifacts/optimization-stages/M2-IO06-numbering-tiny-20261030/`:
`actor.py`, `supervisor.py`, `result.json`, `unit-result.json`, `stdout.log`,
`stderr.log`, `curved-p2-sparse-ids.msh`, cache-old-default-failures/*.json,
cache-preserve-one/<key>/mesh.msh +manifest, `commands.jsonl`, `cleanup.json`.
Przyczynowość IDrenumbering potwierdzona dla tego tiny, **nie** jeszcze przyczyna
wcześniejszego pełnego FAIL (tam before/after witness nie istniał). Full failure
33,77s i logi pozostają historyczne bez edycji; dla pełnej reprodukowalności
odtworzono poprzedni helper i sprawdzono dokładny hash1e3b5e5f… przed zapisaniem
`M2-IO06-20261030/failed-converter-1e3.py` w ignored evidence. Nie wymyślono witness
dla starej próby. Kolejna pełna próba wymaga nowego jawnego root budget/slotu.

### IO-06-E06 — corrected full Preserve1 cold + HIT (`PASS`, Gmsh serialization/cache scope)

Root przyjął causal tiny witness i jawnie udzielił **jednej nowej** pełnej próby:
nowy prefix ROOT artifacts/optimization-stages/M2-IO06-preserve-numbering-20261030,
oryginalny E04FAIL nietknięty. Same bounds400MiBinput/256MiBoutput/180scold/30sHIT,
32GiB/noSwap/CPU2/OMP1/core0, sharedlock/freeRAM/inference0. Tylko dodatkowa opcja
Mesh.PreserveNumberingMsh2=1 wpływa na export; reszta semanticpredicate dokładnie
zachowana. Helpera2490f7d... ma już bounded failurewitness przed cleanup.
Na dalszym FAIL STOP bezHIT/retry, na PASS jeden HIT z zerowym GmshmodelAPI i bez
binaryrewrite. Jeszcze żadnego MFEMmediumrun lub obietnicy speedup/amortyzacji.

E06 ukończony: **jeden corrected cold PASS +jeden HIT PASS**, bez żadnego
MFEMmediumrun. SourceSHA przed cold i po (ponownie z HIT identity) dokładnie
2af1b2ac9dfd0d785ac7e0a865f26eb2dac447ec9f90ea40d85056c5491452b3.
Strict przed/poGmsh witness równy dla2721015nodes/2130744elements, wszystkich
P2coordinatebits+ID, orientedconnectivity, entity/physicalgroups/names. Nie
znormalizowano ani nie pominięto żadnego pola. Preserve1 rozwiązał obserwowaną
niezgodność tego fullroundtrip; E04 dokładne różniące się keys nadal historycznie
nieznane, bo wtedy nie zapisano witness. Zmieniono tylko tę opcję exportu,
diagnostykę i immutable kopię recipe, bez tolerancji/permutationfallback.

Actual binary **205675032B (~196,15MiB)**, SHA
**d91077f8b46140264db0e4fc68e223ddd1a9ee5622cc8a7355b22a6b433c0239**;
cachemanifest63100B, razem205738132B zwykłego cacheinput. To zmierzony rozmiar,
nie wcześniejsze estimate180MB. Różnica25,57MB odpowiada w przybliżeniu12B na
element; nie policzono bloków binary parserem i nie twierdzi się ich rozkładu.

| Wykonanie | Converter/lookup wall | Actor wall | Process CPUuser+system | Systemd CPU | Cgrouppeak | MaxRSS |
|---|---:|---:|---:|---:|---:|---:|
| Cold | 34,049s | 34,063s | 33,1608+0,8387s | 34,0416CPU-s | 2573684736B | 2339964KiB |
| HIT | 0,441s | 0,454s | 0,4155+0,0591s | 0,4826CPU-s | 4575232B | 42840KiB |

Cgrouppeak i processRSS mają odmienny scope/share accounting; nie sumować i nie
interpretować jako VRAM. Obie usługi miały actualMemoryMax32GiB/Swap0/CPUquota2,
core0/OMP1/OpenBLAS1, RuntimeMax180/30s, sharedlock i freeRAM/inferenceguards;
bez OOM/deadline/stopretry. Cała seria34,918s, unitCold34,236s/unitHIT0,510s.

Gmsh APIcountcold init1/open2/write1/clear1/finalize1; **HIT wszystko0**. NodeModel
nie został na HIT utworzony/odczytany ani zapisany. Cachebinary i manifest mają
identyczne rozmiary i mtime_ns po cold/HIT. W mierzonym oknie lookup przed zapisem
własnego raportu, `/proc/self/io` HIT wchar/syscw/write_bytes=0, rchar≈1,010GB
(sourcevalidator+contentSHA+librarySHA+binarySHA), read_bytes=0 w tej warmcache
próbie. Instrumentacyjne JSON/logi nadal mają niewielkie zwykłe zapisy; nie jest
to twierdzenie o braku całego I/O, wear lub zachowaniu coldstorage.
Cold operation rchar1,570614105GB, wchar205738664B/write_bytes205754368B,
read_bytes0 w obecnym pagecache. Tylko jeden binarywrite, HIT go nie przepisał.

Fingerprint: helpera2490f7d..., Gmsh4.15.2/lib9db3090d..., pinnedreaderb8083d...,
optionsMsh2.2/Binary1/SaveAll0/Renumber0/**PreserveNumberingMsh2=1**. Wszystkie
identities/hashedwitness/ostatnie sourceStats zapisane w outcomeJSON. OriginalE04
artifacts oraz jego failedsource1e3 kopia zachowane, bez ich edycji/usuwania.

Dowody ROOT `artifacts/optimization-stages/M2-IO06-preserve-numbering-20261030/`:
`summary.json`, `cold-result.json`, `hit-result.json`, `*-unit-result.json`,
`*-resource-policy.json`, `*-telemetry.jsonl`, `*-plan.json`, `*-cache-stat.json`,
`before.json`, `actor.py`, `supervisor.py`, stdout/stderrlogi, commands/cleanup.
Validcachepod ROOT `cache/<key>/mesh.msh` +manifest pozostawiono do osobnej native
kwalifikacji; `native_mfem_qualified=false` celowo zachowane. Unitsstop/reset,
listunits preserve-* puste, hostlockzwolniony. Nie zmieniano CPP/anteny/.toolchain.

ROI **jeszcze niezmierzone**: nie znamy rzeczywistego nativebinaryload B. Przy
Nrunach, A≈18,752s referencyjnego ASCIIload, C≈34,048s coldconversion i H≈0,441s
HITchecks: N(A−B−H)>C−H. Jeśli A≤B+H, cache nie ma warm-timeamortyzacji;
nie podstawiać samego HITtime za B. Nawet optymistyczne B=0 wymaga co najmniej
dwóch użyć; rzeczywiste N może być większe. Zmiana mesh daje nowy key i nowy
coldcost. Następny etap tylko po root: measured nativebinaryload oraz geometry/
operator/fields equivalence na pełnej antenie, potem combinedPRE03. NoRF/realE2E
speedup claim z samej konwersji/HIT. Slot zwrócono parent.

### IO-06-E07 — full native structural proof (`PASS`), production loader timing still `TODO`

Root przydzielił świeżą2TUkompilację≤120s, tinyregression≤60s i jeden full
structuralrun≤180s bez NDassembly/Maxwell. Dodano opt-in env
`PALACE_IO06_STRUCTURAL_ONLY=1`; bez tej jawnej wartości pliki>4MiB są odrzucane
**przed** konstrukcją mesh. Wartość inna niż1 także jest błędem. Dotychczasowy
tiny path pozostaje taki sam, w tym wszystkie22986assertions/operatoractions.
Full path używa aggregate exactmemcmp+firstdifferencewitness zamiast milionów
CHECK; brak tolerancji/permutationnormalization, brak całych sparseNDmatrices.

Dowody ROOT `build/optimization-stages-m2-io-full-20261030/`: build-test.py,
continue-full.py, commands/events, inputs-before/after-full, compile-result,
result.json(tiny), full-result.json, large-guard-test.log oraz correctedresult,
actual-cgroup/driver-loader/memory-outcome, roi-limited.json, cleanup-full.
NativeR2 source0341e500…/lib0546c1cf…/image7d609652…; Catch2only, publicheaders
sprawdzone fingerprints. CaseCPP iEXE SHA są w inputs/compile-result, bez builda
biblioteki Palace. Compiler≤2jobs(actualsequential), core0/OMP1/OpenBLAS1,
CDIloader615.78.08, cpus2/32GiBmemory/Swap0, sharedrootlock/inference0,
freeRAM≥40GiBprzed/>8GiBwtrakcie. Wszystkie source/native/input hashes przed i
po identyczne, binary/manifest read-only. Nie wywołano Gmsh ani binaryrewrite.

Compile+link **5,608s**, tiny **22986assertionsPASS**, wszystkie6 mass/curl actions
relativeL2=0 i P2field checks zachowane. Expectednegative largeguard zwrócił
Catch2exit42 i dokładną wiadomość przed jakimkolwiek PALACE_IO06_LOAD. Pierwszy
supervisor błędnie oczekiwał exit1 i zapisał failure, bez fullrun. Poprawiono
wyłącznie interpretację istniejącego logu (alltestcasesfailed=42); zachowano
oryginalny failure, bez powtarzania kompilacji/tiny/negativeguard. Kontynuacja
użyła tego samego EXE i dopiero raz uruchomiła fullstructural.

Full native **165aggregateassertionsPASS**, actual126,088swall, input355110567B
ASCII i205675032Bbinary; cgrouppeak2693058560B (~2,508GiB), memory.events
low/high/max/OOM/oomkill=0. Native counts402647vertices/1700660tet/430084boundary.
Wyczerpująco bitowo/porządkowo zgodne:

- wszystkie1207941vertexcoordinatevalues i **8163045P2nodalcoordinatevalues**;
- wszystkie8092892orderedvertexIDs, typygeometrii i physicalattributes;
- wszystkie **19587104scalar i58761312vector P2nodalDOFIDs**, także signedIDs,
  dla każdego tetra i każdego elementu brzegowego;
- wszystkie **17436684edge/face/boundaryorientationIDs** oraz powiązane
  nativeedge/faceIDs, liczbyedges/faces i FEC/order2/vectorordering;
- wszystkie nativephysicalnames/attributesets/memberships.

24stałe physicalmap/Jacobian spotchecks dodatkowo bitexact i positiveweights;
nie zastępują powyższych pełnych pętli. Nie sprawdzono fullNDoperatoraction,
residual/Sparam/farfield. TinyNDkwalifikacja nie jest takim pełnym dowodem RF.

**Ważne ograniczenie czasowe odkryte w E07:** odziedziczony tinyharness używa
`mfem::Mesh(filename,0,0,true)`, a pinnedMFEMmesh.cpp4718 otwiera
`named_ifgzstream`. Produkcyjny geodata.cpp2230 tworzy `std::ifstream` i
`mfem::Mesh(stream,0,0,true)`. Same formatreader/structuralflags są zgodne, ale
wrapperstream jest inny. E07 measuredASCII62,008805272sCPU61,874791s i binary
61,300850821sCPU61,169556s to **filenameharness**, nie produkcyjny parse18,75s.
Nie znamy przyczyny całej różnicy i nie przypisujemy jej z góry gzstreamowi.
Pinned mesh.cpp skopiowano read-only ze stoppedcontainer do evidence.

W tym jednym filenamepair grossdifference0,707954451s, HIT0,441062782s zostawia
zaledwie0,266891669s/use; z cold34,049037636s matematyczna amortyzacja to126użyć
przy utrzymaniu tych samych czasów. To **nie** stabilny/performancequalified ROI:
ASCII zawsze pierwszy, binarydrugi, dwa meshe współistnieją, warmOSpagecache i
allocator, pojedynczy pomiar bez statystyki. Nie wolno mieszać historycznego
produkcyjnego A18,752s z tym B61,301s lub traktować samego HIT jako binaryload.
Nie ma jeszcze dowodu, że IO06 przyspiesza właściwy Palace run.

Owncontainer zatrzymany(stateexited/OOMfalse), hostlock zwolniony; brak zmiany
produkcyjnego CPP lub antenna/.toolchain. Parent dostał PASSstructural i jawny
request osobnego slotu na **std::ifstreammatchedloader**; bez takiego slotu
nie powtarzać fulltestu. Następna bramka po streamtiming: combinedPRE/OP M3
operators/fields/RF, jeśli ROI uzasadni. Cachemanifest nadal nie ogłasza RF.

### IO-06-E08 — production `std::ifstream` pair (`PASS`, cache default `DEFER`)

Root przygotował dwa plan.json w ROOT artifacts/optimization-stages/
M2-IO06-production-20261030/{ascii,binary}-medium; wykonano sekwencyjnie dokładnie
`python tools/stage_probe_run.py execute <plan.json>` (binary po ASCII PASS).
Żadnych nowych buildów/źródłowych zmian/ponownej konwersji. To prawdziwy driver
PalaceR2 source0341e500…/lib0546c1cf…, std::ifstream+Mesh(stream,0,0,true),
CUDA-MAGMA, wszystkie18baselineflags, traceON w obu. Limity180s/case, OMP1/CPU8,
64GiB/Swap0/core0, sharedlock/Strata inactive/dead/PID0 i freeRAMguard runnera.

**Tylko reprezentacja wejściowej siatki różna**: źródłowy ASCII2af1…355110567B vs
binaryd910…205675032B z read-onlycache. FixtureSHA zmienione celowo; zestaw
różniących się identitykeys dokładnie mesh/mesh_sha256/fixture_sha256. Config9f068…,
resolvedconfig i environment identyczne, native/source/driverhash przed i po
sprawdzone runnerem. Dokładny rawrepresentationproof to E07/full-result.json.

| Zakres | ASCII | Binary |
|---|---:|---:|
| preprocess.load_mesh.mfem_parse wall | 19,039717886s | 16,999603543s |
| ten sam parse CPU | 18,997930s | 16,960728s |
| Native DiskIO(manualtimer) | 19,040s | 17,000s |
| Native MeshPreprocessing | 27,805s | 27,550s |
| Native Initialization | 6,510s | 6,560s |
| Native Total | 53,411s | 51,166s |
| Controller elapsed | 54,6605s | 52,4533s |
| Recorded cgrouppeak | 2307915776B | 2305720320B |

Każdy trace ma12zbilansowanych scopes. Oba wyniki diagnostic-only/preprocess,
solve_executed=false/rf_result=false; nie budują pełnych operatorów/GSLIB/GMRES.
Curvature2, native402647vertices/1700660tet/510048boundary (w tym79964dodane
materialinterfacebdr), wszystkie volume/boundaryattributes identyczne. Globalny
sampledGPUpeak2230MiB w obu obejmuje także desktop, **nie** task-exclusiveVRAM.
DiskIO tu nadal manualny timer CPUparse, nie dowód physicaldiskbottleneck.

Matched production parse daje **2,040114343s (~10,715%)** mniej na warmload.
Po HITvalidation0,441062782s zostaje1,599051561s/use. Cold34,049037636s daje
N(A−B−H)>C−H, czyli **co najmniej22użycia identycznej siatki** w tym jednympair.
Pierwsze użycie C+B=51,048641179s vsA19,039717886s: +32,008923293s. Historyczne
A18,752279465 zamiast obecnego A oznacza26użyć; to sensitivity, nie kolejnyrun.
Brak repeats/reorderedpair/statystycznego progu; warmcache/allocator i fixedorder
ASCII→binary. NativeTotal−2,245s zawiera także zwykły drift pozostałych faz,
więc korzyść przypisywana inputowi to przede wszystkim matchedparse−2,040s.
Nie wyjaśniamy automatycznie wcześniejszego filenameharness62s; zmienił się też
runtime/devicecontext. **Do produkcyjnego ROI używać E08, nie E07loaderów.**

DecyzjaIO06: strict native representationprototype poprawny; **DEFER automatyczne
cachepromote dla geometryfinetuningu**, bo każda zmiana siatki płaci ponownie cold,
a częstotliwości w jednym runie nie ładują od nowa mesha. Warto rozważyć dla
udowodnionych≥22loads tej samej geometrii lub taniego bezpośredniego exportu
binary przy meshingu (osobne TODO, nie zmieniano repo anten). Obecny warmgain jest
realnym obserwowanym wynikiem, ale mały wobec PRE/OP i nie uzasadnia wymuszania
cache w standardowym workflow. Pełne NDoperator/fields/RF nadal bramkaM3.

Artifact `pair-result.json` zachowuje cały matchedfingerprint, intentionaldiff,
phasesCPU/wall, timers, counts, ROI i ograniczenia. Osobne stage-profile-report,
stdout/stderr, diagnostic-result, container-state i telemetry w obu katalogach.
Oba kontenery usunięte, exit0/OOMfalse, lockzwolniony; sourcecache/antenna/
.toolchain bez zmian i bez dodatkowego205MBzapisu. Nie uruchomiono retry.
