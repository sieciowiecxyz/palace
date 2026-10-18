# Początkowa pula HYPRE/Umpire — EXP11

Status 2026-10-18: **pozytywny filtr coax-tiny**, pełna antena NOT RUN. Ustawienie jest opcjonalne; nie zmieniono globalnego defaultu ani medium. M1 pozostaje otwarty.

## Mechanizm

Przypięty HYPRE 3.1.0 domyślnie inicjalizuje parametr device pool na 4 GiB. Umpire tworzy pulę leniwie, przy pierwszej alokacji. To rezerwacja startowa, nie wymagana wielkość konkretnej macierzy. `HYPRE_SetUmpireDevicePoolSize` pozwala ustawić mniejszy seed przed powstaniem puli; pula nadal może rosnąć.

`palace/main.cpp::ConfigureHypreMemoryPool` działa po `hypre::Initialize`, przed tworzeniem hierarchii FEM. Nie zmienia solvera, preconditionera, precyzji ani tolerancji. Zmienia tylko seed urządzenia; pozostałe pule Umpire nie są ustawiane tą opcją.

```sh
python3 tools/dev.py run coax-tiny artifacts/new-pool-test --seconds 60 --basis fp64 --hypre-pool-mib 256
```

Opcja `--hypre-pool-mib` ustawia `PALACE_HYPRE_DEVICE_POOL_MIB`; dozwolone wartości całkowite to 16–4096 MiB. Brak opcji zachowuje bazę. Runner czyści odziedziczoną zmienną i zapisuje wartość w `command.json`. Native odrzuca niepoprawną wartość oraz żądanie na buildzie bez Umpire. Dla 256 MiB sukces wymaga logu `PALACE_HYPRE_POOL: initial_device_bytes=268435456` i `result.hypre_pool_applied=true`. Brak logu oznacza niepoprawny run wariantu.

Dane robocze nadal RAM/VRAM. To nie offload ani cap całego HYPRE. Nie obiecywać takiej samej redukcji dla macierzy, które potrzebują większej puli.

## Wyniki tej samej pary z pomiarem procesu

Mesh/order 2/PA 1/Tol 1e−6/K 240, 3 częstotliwości (3,30/3,55/3,80 GHz), oba porty, FP64 baza/operator/faktory, MAGMA i UVM. Q-pool wyłączony w obu przypadkach. Każdy run miał deadline 60 s. Source/build/command/telemetry zachowane lokalnie.

| Metryka | Default4GiB | Seed256MiB |
| --- | ---: | ---: |
| Ukończone solve | 6/6 | 6/6 |
| Iteracje | 24/13/14/25/13/13 | identyczne |
| Czas runnera | 10,475s | 10,388s |
| Maks. próbkowane VRAM procesu | 4 657 774 592 B (4,338 GiB) | 631 242 752 B (0,588 GiB) |
| Cgroup peak | 528 257 024 B | 523 051 008 B |
| Próbki VRAM procesu | 9/10 | 9/10 |

Różnica próbkowanego VRAM procesu: **4 026 531 840 B = 3,75 GiB**. To zmierzona oszczędność dla małego przypadku, zgodna z różnicą seedów. Czas pozostał podobny; ta jedna para nie dowodzi speedup. Brak istotnej redukcji RAM hosta w kontrolowanej parze; nie używać pierwszej, zimnej pary do takiego twierdzenia.

Root porównał wszystkie complex S obu portów i wszystkie zapisywane energie: maxΔS=3,3755e−15, maxΔVSWR=5,7732e−15, względnaΔenergii=0. Zbieżność i raw/stopping norms zgodne do błędów zaokrągleń. Sama norma LEFT nadal nie jest niezależną normą błędu rozwiązania.

Osobny known-TEM test 256 MiB / 3,55 GHz / oba porty ukończył się po 17,658 s. Całe objętościowe L2 względem analitycznego pola: E ~0,4953%, B ~0,5211–0,5363%, kwadratury 4/6; wszystkie poniżej 1%. Nie wnioskować z tego o polach pełnej anteny.

Artefakty: `artifacts/m1-hypre-pool-{default-pid,256-pid,256-tem}-20261018/`, analiza `artifacts/m1-pool-analysis-20261018.json` (SHA logów, ΔS/VSWR/energii i normy). Pierwsza para bez pomiaru procesu również przeszła; jej globalnego GPU peak nie należy traktować jako izolowanego pomiaru Palace.

## Telemetria i granice pomiaru

Runner odpytuje `nvidia-smi --query-compute-apps=pid,used_gpu_memory` dla hostowego PID bezpośredniego entrypointu. Wartości MiB przelicza na B. To pojedyncza karta i jeden rank; nie agreguje MPI dzieci. Brak/N/A/timeout oznacza `None`, nie zero. `gpu_process_memory_peak_bytes` jest **maksimum z próbek ~1s**, a nie gwarantowanym maksimum każdego chwilowego bufora. Globalny odczyt GPU pozostaje osobno, podobnie cgroup oraz logical UVM.

## Decyzja

256 MiB jest użyteczną opcją do kolejnych małych filtrów. Pełna antena, zmiana liczby iteracji/czasu pod presją UVM i rzeczywisty wzrost puli nadal wymagają pomiaru. Nie zmieniać globalnego defaultu na podstawie tiny. Przed ewentualnym pełnym runem należy oszacować pamięć, zachować guard i deadline oraz rozdzielić koszt solve od diagnostyki pól.
