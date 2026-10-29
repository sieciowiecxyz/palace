# Audyt i plan: odczyt oraz zapis wyników

Status: przegląd źródeł ukończony; brak nowych pomiarów.
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
| `palace/models/postoperatorcsv.cpp:1141-1164` (oraz analogiczne metody tabel) i `palace/utils/tablecsv.cpp:278-308` | Każdy `PrintPortS()` dopisuje wiersz do tabeli w pamięci, po czym `WriteFullTableTrunc()` formatuje i zapisuje całą tabelę od nowa. Dla N częstotliwości może to robić łączny zapis/formatowanie rzędu O(N²) wierszy. | Mierzyć liczbę zapisów, bajty i koszt dla liczby częstotliwości. Sprawdzić append/buforowanie jako osobny prototyp, zachowując bezpieczne wznowienie adaptive/reload. | `IO-02` TODO |
| `palace/models/postoperator.cpp:1133-1202`; `palace/utils/ceedparaviewdatacollection.cpp:200-229` | Paraview zapis wykonuje skalowanie/pole pochodne i `Save`; domenowe pole pobiera `HostRead()` i serializuje dane element po elemencie do bufora/strumienia. `HostRead` może wymagać transferu/synchronizacji. Całość widoczna jako `POSTPRO_PARAVIEW`, niekoniecznie `Disk IO`. | Rozdzielić compute, host transfer, serializację i write; następnie sprawdzić VTK binary/compression/precision oraz batching. | `IO-03` TODO |
| `palace/utils/tablecsv.cpp:278-299` | Przy `load_existing_file` CSV jest wczytywany do `stringstream`, następnie kopiowany do `string` i parsowany przez `Table`. To może powodować duplikaty bufora i peak RAM dla dużych tabel. | Zmierzyć użycie reload w docelowym runie i peak/bajty; rozważyć streaming parser dopiero jeśli ten koszt jest mierzalny. | `IO-04` TODO |
| `palace/utils/outputdir.hpp:163-205,207+` | Startup może usuwać poprzedni katalog rekurencyjnie; tworzenie/usuwanie katalogów i filesystem coordination również zalicza się do IO timerów. | Zmierzyć cold/warm output dir i liczbę plików; nie usuwać sprzątania, dopóki test nie potwierdzi bezpiecznego rozdzielenia starego wyniku. | `IO-05` DEFERRED do raportu IO-01 |

## Rejestr hipotez i testów

Przed próbą agent wyszukuje ID w tym ledgerze i aktualizuje istniejący wpis. Statusy: `TODO_TO_CHECK`, `IN_PROGRESS`, `PASS`, `REJECTED`, `DEFERRED`. Do `PASS`/`REJECTED` zapisać datę, commit i hash builda/fixture, dokładne argv/config, liczby częstotliwości i źródeł, bytes/read/write, czas CPU/wall, peak RAM, wynik poprawności oraz artefakt raportu. `TODO_TO_CHECK` jest hipotezą, nie wykonanym eksperymentem. Zmiana w kodzie nie zalicza testu wydajności.

### IO-01 — pokrycie i narzut timerów (`TODO_TO_CHECK`)

Zweryfikować w reprezentatywnym medium runie, które funkcje wchodzą do każdego timera. Sparować `PALACE_PHASE_TRACE` (inclusive nesting) z `Timer::IO` (exclusive scope) oraz systemowymi licznikami procesu: `read_bytes`, `write_bytes`, CPU time, filesystem call counts/duration jeśli dostępne. Nie sumować inclusive timers. Jawnie zapisać konfigurację `Paraview`, grid functions, probes, farfield, CSV i reload. Jeżeli nie ma dokładnego istniejącego runu, zaplanować jeden kontrolowany test po zatwierdzeniu celu; żadnego nowego EM/GPU runu w samym audycie.

Zaliczenie: rozliczenie największych scope’ów do ±2% ich właściwego nadrzędnego timera, bytes i systemowy czas I/O rozdzielone od CPU/wall, plus opis opóźnień `HostRead` i MPI. Nie zakładać, że `Disk IO` = dysk.

### IO-02 — koszt pełnego przepisu tabel w sweepie (`TODO_TO_CHECK`)

Na małej tabeli i potem istniejącym sweepie porównać koszt/bytes przy N i 2N wierszy; rejestrować częstotliwość wywołań `WriteFullTableTrunc`, czas formatowania i zapis, rozmiar finalnego pliku, reload/adaptive restart. Oczekiwanie O(N²) wynika z kodu, ale rzeczywisty udział E2E zależy od liczby częstotliwości i tabel. Prototyp append dopuszczalny dopiero po teście niezmienionej kolejności kolumn, precyzji, kompletności po przerwaniu i możliwości reload.

### IO-03 — VTK/Paraview i GPU→host (`TODO_TO_CHECK`)

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

Brak — wykonano tylko audyt źródeł. Przed pierwszą próbą uzupełnij wpis według [workflow](workflow.md). Nie oznaczać hipotezy PASS za samo przeczytanie kodu.
