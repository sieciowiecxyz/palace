# Audyt i plan: preprocessing siatki

Status audytu: kod przejrzany; pomiary nowych wariantów nieuruchomione.
Owner: agent preprocessing, branch `opt/preprocessing-20261029`.
Koordynator scala plan i wspólny checkpoint. Proponowany zakres kodu: `palace/utils/geodata.cpp`, ewentualnie `palace/utils/meshio.cpp`; nie dotykać solverów, wspólnych plików planu ani I/O outputu.

## Granica fazy i dane bazowe

W logu Palace „Mesh Preprocessing” jest timerem wewnątrz „Initialization”, nie obejmuje generowania geometrii ani meshera zewnętrznego. `palace/driver.cpp:59-79` obejmuje w nadrzędnym `INIT` odczyt i przygotowanie siatki, `solver->Preprocess`, partycjonowanie, równomierne refinement oraz utworzenie obiektu `Mesh`. Sam timer `MESH_PREPROCESS` jest zakładany osobno w `geodata.cpp:130` (`Load`) i `:270` (`Partition`). Część dalszego przygotowania MFEM/FE może zostać przypisana do Initialization lub solverowego Setup; nie należy przypisywać całego INIT do tego milestone’u.

Ostatni porównywalny medium run użył już wygenerowanej, stałej siatki; nie mierzył CAD ani generowania siatki. Wyniki: preprocessing 29,224 s (3,54% całości 825,783 s), operator construction 121,501 s lokalnie; na CMP operator construction 401,9 s. I/O Palace 19,612 s to osobna kategoria. Scope może być zagnieżdżony, ale BlockTimer przerywa naliczanie rodzica: końcowa tabela jest exclusive i jej kategorie można sumować w tym single-rank runie. Nie sumować natomiast inclusive wpisów phase trace. Initialization 6,768 s + Mesh Preprocessing 29,224 s daje 35,992 s przygotowania. Nie ma na dziś profilu, który mówi, ile z 29,224 s przypada na odczyt, walidację, transformacje, partycjonowanie i refinement.

## Miejsca w kodzie do sprawdzenia

| Miejsce | Rola / fakt z kodu | Możliwy kierunek | Status |
|---|---|---|---|
| `palace/utils/geodata.cpp:130-264`, `Load` | Ładuje mesh; sprawdza typy i warunki AMR/periodic; opcjonalnie czyści nieużywane elementy, konwertuje typy, reorderyzuje elementy, finalizuje siatkę, robi region refinement i sprawdza granice/interfejsy. Część ścieżek jest warunkowa. | Najpierw rozbić czas na fazy i ranki, potem optymalizować tylko kosztowną ścieżkę faktycznie używaną przez antenę. | `PRE-01` TODO |
| `palace/utils/geodata.cpp:267-369`, `Partition`; zwłaszcza `:314-367` | Wylicza partycjonowanie i rozdziela siatkę; ścieżka zależy m.in. od conformality, AMR i liczby rang. Przy niekonformalnym AMR są dodatkowe konwersje i broadcast porcjowany. | Odrębnie profilować 1 rank i MPI. Rozważyć zmianę tylko wtedy, gdy koszt partycjonowania/broadcastu istotny dla docelowej konfiguracji. | `PRE-03` DEFERRED dla obecnego single-GPU case |
| `palace/utils/geodata.cpp:208-212`, `ReorderMeshElements`; implementacja `:2743+` | Istnieje opt-in `reorder_elements`, który zmienia kolejność elementów/węzłów dla lokalności cache. | Sparowany benchmark on/off może sprawdzić, czy preprocess kosztuje się późniejszym assembly, pamięcią i solverem. Wliczać koszt reordering do całego runu. | `PRE-02` TODO |
| `palace/utils/geodata.cpp:191-205, 2279+, 2375+` | `CleanMesh`, rozcinanie typów elementów i testy typu mesh występują w opcjonalnych ścieżkach; `CheckElements` bywa wywołane ponownie przez konwersję. | Szukać redundantnych przebiegów siatki dopiero po profilerze; bezpieczny mikrotest atrybutów/topologii może wskazać, czy jeden przebieg można współdzielić. | `PRE-04` TODO |
| `palace/utils/geodata.cpp:2174-2215`; konwersje `meshio.cpp` | `LoadMesh` używa wbudowanego czytnika MFEM dla obsługiwanych formatów; COMSOL/Nastran przechodzą przez konwerter do strumienia Gmsh. | Badać parser/format tylko jeśli profil pokaże dominację odczytu lub konwersji. Nie wprowadzać mmap/cache formatu jako założonego rozwiązania. | `PRE-05` TODO |

## Rejestr hipotez i prób

Każdy agent najpierw sprawdza poniższe ID. Dopisuje datę, commit/build/input hash, dokładne polecenie, wyniki, testy poprawności i decyzję. `TODO_TO_CHECK` oznacza hipotezę bez pomiaru; nie jest wynikiem. Po `PASS`/`REJECTED` nowy agent nie powtarza próby bez zmiany mesh, wersji MFEM, hardware, konfiguracji lub ujawnionego błędu.

### PRE-01 — profil faz wewnątrz przygotowania siatki (`TODO_TO_CHECK`)

Hipoteza: 29,2 s ukrywa jedną lub dwie dominujące funkcje, więc ogólna optymalizacja całej fazy grozi pracą nad małym kosztem. Dodać tymczasowe/niskonarzutowe timery wokół istniejących bloków `Load` i `Partition`, a nie logować każdy element. Rozdzielić CPU time/wall time, rank oraz bajty wejścia; osobno oznaczyć koszt I/O. Najpierw krótki profil bez zmiany kodu, jeśli istniejący profiler i dokładne binary pozwalają rozdzielić te fazy.

Zaliczenie: fazy pokrywają się do tolerancji 2% z timerem nadrzędnym, MPI max-rank/wall jest jawny, brak zmian wejścia, topologii lub wyniku. Jeżeli preprocess <5% reprezentatywnego E2E i żaden subetap nie jest istotny przy oczekiwanej liczbie eksperymentów, oznaczyć dalszą optymalizację CPU-preprocess jako `DEFERRED`, nie sztucznie wymuszać speedup.

### PRE-02 — `reorder_elements` end-to-end (`TODO_TO_CHECK`)

Hipoteza: cache locality może obniżyć późniejsze operatory/solver, ale może się nie zwrócić przez koszt reordering albo już dobry ordering wejściowy. Porównać config on/off na identycznym medium mesh i buildzie; preprocess, operators, setup, solve, E2E i peak RAM raportować oddzielnie. Wyników samych operatorów nie używać do decyzji, jeśli reordering dodaje koszt.

Zaliczenie: topologia, materiały/atrybuty, boundary IDs, DOF dimensions i liczby elementów zachowane; rozwiązanie porównane przez normę pola / residuum / S-parametry w zatwierdzonych tolerancjach. Wariant promować tylko przy powtarzalnym E2E zysku ponad szum bez nieakceptowalnego wzrostu pamięci.

### PRE-03 — koszt `Partition` przy docelowym modelu równoległym (`DEFERRED`)

Single-GPU nie oznacza automatycznie single MPI rank, ale brak osobnego pomiaru nie pozwala wnioskować o zysku z nowego partitionera. Najpierw zapisać `MPI size`, `OMP threads`, czas `GetMeshPartitioning`, dystrybucji i rozmiary per-rank. Wrócić do testu tylko dla faktycznej konfiguracji multi-rank albo gdy etap przekroczy 10% E2E. Zachować obecne ścieżki nonconforming AMR i chunked broadcast; nie upraszczać na podstawie konfigu anteny.

### PRE-04 — ograniczenie powtórnych skanów siatki (`TODO_TO_CHECK`)

Hipoteza: opcjonalne clean/split/validation ścieżki mogą wykonywać wielokrotne globalne skany. Profil wywołań i konfiguracji ma wykazać, że dana para skanów wykonuje się w tym samym runie i koszt jest mierzalny. Dopiero potem prototypować współdzielenie już policzonych cech. Nie cache'ować bez jawnej reguły unieważnienia po modyfikacji/refinement; nie zmieniać walidacji dla przyspieszenia.

Zaliczenie: testy tetra/hex/prism/pyramid, curved/linear, conforming/nonconforming oraz region refine odpowiednie do zmienionej ścieżki; identyczne atrybuty i connectivity; brak regresji na MPI jeśli dotknięto partycjonowania.

### PRE-05 — parser/konwersja wejścia (`TODO_TO_CHECK`)

Hipoteza: koszt może zależeć od formatu; COMSOL/Nastran mają koszt konwersji do Gmsh, lecz obecny antenowy fixture może już być Gmsh. Zmierzyć format na fixture reprezentatywnym i porównać tylko równoważne mesh, nie różne eksporty. Nie zmieniać formatu plików projektu ani nie dodawać stałego cache, dopóki oszczędność odczytu nie uzasadni miejsca, walidacji hashy i kosztu zapisu.

## Bramki wykonania tej gałęzi

- P0: odczytać bieżące ustawienia testowego medium fixture i ustalić baseline wejścia/builda oraz czy benchmark liczy preprocess od zimnego procesu.
- P1: zakończyć PRE-01; wybrać jeden kosztowny, faktycznie aktywny podetap. Jeśli profiling unavailable, zapisać narzędzie i powód, nie zgadywać hotspotu.
- P2: wykonać tylko najtańszy pomiar rozstrzygający z PRE-02/04/05. Nie uruchamiać jednocześnie CPU benchmarków na hostach, jeśli wpływają na wynik; nie uruchamiać EM/GPU bez autoryzacji właściwego celu.
- P3: jeśli wynik obiecuje, implementować pojedynczą zmianę i dodać minimalny test regresyjny. Jeśli brak zysku, oznaczyć hipotezę `REJECTED` z liczbami i zatrzymać tę gałąź.
- P4: na integracji odtworzyć krótki medium test przez ustalony workflow, raportując poprawność fizyczną niezależnie od czasu. Aktualizację shared plan/checkpoint robi koordynator.

## Kontrakt poprawności

Każda zmiana mesh preprocessing musi zachować geometryczne położenia w tolerancji wejściowego formatu, orientację elementów, connectivity, geometry/boundary/material attributes, periodic/crack interfaces, jakość/Jacobian, true-DOF constraints i partition ownership. Porównania wymagają tych samych mesh/materials/source/boundary/config oraz wersji MFEM i Palace. Przy zmianie kolejności lokalnych indeksów porównywać pola po dof-to-physical mapowaniu i fizyczne obserwable; nie wymagać identycznych bajtów macierzy o zmienionej numeracji.


## Wyniki nowych eksperymentów

Brak — wykonano tylko audyt źródeł. Przed pierwszą próbą uzupełnij wpis według [workflow](workflow.md). Nie oznaczać hipotezy PASS za samo przeczytanie kodu.
