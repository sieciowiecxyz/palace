# Audyt i plan: odczyt oraz zapis wyników

## Stan bieżący po zamknięciu M1 — 2026-10-30

Ta tabela określa aktualną kolejkę; wcześniejsze wpisy zachowują historyczne etapy próby.
PASS jest zakresowy; nowa optymalizacja wymaga osobnych testów M2/M3.

| ID | Stan i zakres |
|---|---|
| IO-01 | PASS — profil/replay M1; parser wejścia to główny koszt |
| IO-02 | DEFERRED — writer0,85–2,38ms; wrócić przy mierzalnym dużym sweep/output |
| IO-03 | DEFERRED — VTK poza obecnym workloadem |
| IO-04 | DEFERRED — mały reload w replay nie daje sensownego E2E |
| IO-05 | DEFERRED — cleanup nie wyjaśnia kosztu wejścia |
| IO-06 | TODO_TO_CHECK — M2 native binary/cache inputmesh z kontrolą cold/warm |

Status: M0 archived/native CSV PASS; M1 native I/O replay i trace parser PASS; representative overhead/RF NOT RUN.
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
