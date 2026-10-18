# M1 — pierwsze pomiary i audyt

Data: 2026-10-18. Status: M1 ACTIVE, referencja pełnej anteny i kontrola pól nadal otwarte. To pomiary diagnostyczne, nie nowa kwalifikacja projektu ani przyspieszenia.

## Co wykonano

1. Sprawdzono kod InitialResidual i warunek zatrzymania GMRES w palace/linalg/iterative.cpp: LEFT używa ||B(b−Ax)||, nie surowego ||b−Ax||. Nowy PALACE_RAW_RESIDUAL pod PALACE_VERIFY_RESIDUAL przelicza Ax−b w FP64 operatora, korzystając z istniejących scratch vectors. Zapisuje normy b, Ax, b−Ax, relative_rhs oraz relative_action. Ostatnia miara ||b−Ax||/(||Ax||+||b||) nie jest normwise backward error i nie zastępuje kryterium M1.3.
2. Przyrostowy build z zachowanymi dependencies/ccache: 7.354 s fazy build/export, nie pomiar cold build. Manifest: build/sm120/manifest.json; log: build/sm120/build.log. Zmiana runnera/Markdown nie wymagała ponownej kompilacji solvera.
3. Dwa gotowe lokalne coax smoke uruchomiła ta sama Luna high: FP32 storage i FP64 storage. Medium, operator/faktory FP64, terminacje, UVM i MAGMA bez zmian. Każdy run miał limit 180 s; nie uruchamiano pełnej anteny.

| Metryka | FP32 basis | FP64 basis |
| --- | --- | --- |
| Czas całego runnera | 33.573 s | 33.579 s |
| Rozwiązania | 6/6, exit 0 | 6/6, exit 0 |
| Iteracje | 20/15/16/23/14/16 | 20/15/16/23/14/16 |
| raw relative_rhs | 0.019434–0.061139 | 0.019407–0.058655 |

Max |Δcomplex S| FP32 vs FP64 storage = 8.9643e-09. FP32 smoke vs historyczny coax: 1,00e−8; max błąd transmisji względem TEM = 1,8713e−4. To zgodność portów kontrolnego coaxa; zgodność pól i duża antena nie są z tego wywnioskowane. Pojedynczych czasów 33,6 s nie interpretujemy jako benchmarku przewagi precyzji.

Artefakty: artifacts/m1-coax-raw-residual-20261018/ i artifacts/m1-coax-fp64-raw-residual-20261018/ — command.json, build-manifest.json, palace.log, result.json, telemetry i port-S.csv; porównanie: artifacts/m1-basis-comparison-20261018.json. Żadna próba nie miała OOM ani przerwania.

Wniosek: rozbieżność między normami występuje również z bazą FP64. Samo wyłączenie kompresji bazy nie rozwiązuje problemu na tym coaxie. Nie dowodzi to poprawności pola ani rozstrzygnięcia historycznego przypadku antenowego. Następny krok: mały kontrolny problem ze znanym polem/rozwiązaniem i pomiar błędu niezależnego od preconditionera, zanim dopuścimy dalsze obniżanie precyzji.

## Audyt kosztu geometrii anteny

Polecenie: python3 tools/mesh_cost.py examples/tshaped-medium/mesh/pcb.msh --output artifacts/m1-mesh-audit-20261018.json. SHA mesh: ec56c9a7de3e9cdc9618b87a2029975d474d6d5621f9fd08b35f24501b6f161e. Odczytano 2,579,954 węzłów i 1,601,320 tetraedrów.

| Domena | Tetraedry | Udział elementów |
| --- | ---: | ---: |
| AIR | 988,203 | 61.712% |
| ZYF300CA-C | 27,999 | 1.748% |
| PTFE | 480,858 | 30.029% |
| NP140F_assumed_screen | 9,048 | 0.565% |
| PETG_ASSUMED_MOUNT_SCREEN | 49,844 | 3.113% |
| PA66_ASSUMED_MOUNT_SCREEN | 24,203 | 1.511% |
| PETG_ASSUMED_RADOME_SCREEN | 21,165 | 1.322% |

Powietrze stanowi około 99,21% objętości wyznaczonej z narożników, lecz 61,71% elementów. PTFE zasilania: 30,03% elementów przy około 0,00113% tej objętości. Jest to wskazówka do audytu drobnej siatki feedu, a nie pozwolenie na zmianę jego fizyki. Udział elementów nie jest udziałem globalnych DOF ani pamięci faktorów.

Istniejąca zewnętrzna granica ABSORBING ma 18 840 trójkątów i 28 260 krawędzi; każda krawędź należy do dwóch trójkątów. Jeden gęsty blok complex128 rozmiaru 28 260² wymaga 12 778 041 600 B = około 11,90 GiB. Pełny operator z dwiema rodzinami śladów może wymagać kilku bloków oraz workspace. To rachunek ilustracyjny dla obecnej granicy, nie przewidywanie zoptymalizowanego interfejsu BEM.

Wniosek: FEM–BEM ma realny kierunek oszczędności dzięki usunięciu części powietrza, lecz trzeba zmierzyć liczbę śladów i koszt FMM/kompresji. Nie zakładamy, że usunięcie 61,7% elementów zmniejszy RAM/VRAM o taki sam procent. Geometria kwadratowych elementów jest liczona tylko z narożników; objętości/pola powierzchni są przybliżeniem.

## Źródła do przygotowania prototypu M2

Odczyt online: 2026-10-18; gałąź main jest zmienna, przed prototypem przypiąć commit. To wstępna identyfikacja kandydatów M1.5, a nie zaliczenie M2.1.

- [Bempp-cl](https://github.com/bempp/bempp-cl) implementuje operatory Maxwell i kernele OpenCL/Numba. Może być kontrolną implementacją elektromagnetyki; nie przypisujemy mu natywnego CUDA ani Tensor Cores.
- [Kod FMM Maxwell](https://github.com/bempp/bempp-cl/blob/main/bempp_cl/api/fmm/fmm_assembler.py) zawiera gałęzie operatorów Maxwell. Przed wyborem sprawdzić obsługę konkretnych przestrzeni, preconditionera i wykonanie GPU całej ścieżki.
- [Oficjalne tutoriale](https://bempp.com/documentation/tutorials.html) obejmują Maxwell i oddzielnie sprzężenie FEM–BEM dla Helmholtza. Przykład Helmholtz nie jest gotowym dowodem poprawności sprzężenia Maxwell/Palace.

Nie instalowano jeszcze biblioteki BEM i nie uruchomiono prototypu. Licencja, interfejs H(curl), konwencje fazy oraz dokładna ścieżka CUDA/FMM są otwartymi kontrolami M2.
