# Architektura lokalnego forka Palace

## Zasady

Najprostszy czytelny kod, małe zmiany i jawne granice odpowiedzialności. Reużywaj infrastruktury upstream i bibliotek. Testuj realne ścieżki i regresje; nie dodawaj warstw ani zależności na zapas. Zmiana reprezentacji/precyzji nie może ukrywać zmiany równań.

## Mapa

- `palace/`, `cmake/`, `test/`: źródła i testy upstream. Zaimportowane rozszerzenia są w zwykłym kodzie C++, nie stosowane ponownie jako patche.
- `tools/dev.py`: lokalny przyrostowy build, manifesty, rozpakowanie fixtures, ograniczony runner i pakowanie. Python stdlib, Podman, zstd; Linux x86-64.
- `tools/adapter/`: dotychczasowy adapter CUDA UVM/cuDSS; FP32 faktory są opcjonalne, runner używa faktorów FP64.
- `tools/runtime.json`: przypięte lokalne obrazy zależności i wersje; `tools/import.json`: pochodzenie zaimportowanych źródeł i zasad vibecoding.
- `tools/containers/`: cienka warstwa ccache na gotowym builderze i runtime z binariami forka.
- `palace/utils/fieldcomparison.hpp`: opcjonalne lokalne snapshoty FP64 i różnica E/B ważona istniejącymi operatorami energii; bez modyfikacji rozwiązania. Runner wiąże referencje hashami fizyki/mesh/dependencies.
- `tools/coax_fields.py`: analityczne porównanie E/B/energii; opt-in native L2 w `palace/utils/coaxdiagnostic.hpp`, tylko znane jednorodne fixtures.
- `tools/generate_coax_tiny.py`: jednorazowe generowanie mniejszego filtra przez opcjonalny gmsh, nie część runtime.
- `tools/mesh_cost.py`: audyt domen Gmsh 2.2 i orientacyjnego kosztu powierzchniowego, bez bibliotek FEM/GPU.
- `tools/tests/`: regresje narzędzi i mały natywny probe cuDSS.
- `examples/tshaped-medium/`, `examples/coax-medium/`, `examples/coax-tiny/`: kompletne wejścia z archiwami siatek i sumami kontrolnymi.
- `build/sm120/`, `.cache/`, `artifacts/`: ignorowane buildy, ccache i wyniki. Obiekty CMake są dodatkowo zachowane w dedykowanym kontenerze buildera.
- `docs/`: instrukcje lokalne i zachowana dokumentacja upstream w `docs/src/`. INDEX prowadzi do obu.

## Granice

Środowisko zależności pochodzi z istniejącego, przypiętego obrazu lokalnego. Zwykły build nie pobiera ani nie buduje ponownie MFEM/libCEED/hypre. Przeniesienie środowiska wymaga eksportu/importu obrazów; nie ma jeszcze rejestru obrazów ani zweryfikowanego cold builda wszystkich zależności.

Nowy eksport ma `numerically_validated=false`. Historyczna kwalifikacja dotyczy wskazanych starych binariów i przypadków. Runner sprawdza kompletność wykonania; osobna analiza sprawdza S, energię, residuum i pola. Obecny cel dotyczy jednej 5070 Ti. Obsługa podziału na 2 GPU pozostaje poza jego kryteriami i nie została zakwalifikowana.
