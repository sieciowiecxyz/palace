# Build i cache — lokalny SM120

## Wymagania i pierwsze uruchomienie

Linux x86-64, Python 3.11+, Podman, zstd. GPU run wymaga NVIDIA driver/CDI (`nvidia.com/gpu=all`). Nie są potrzebne pip ani systemowy CUDA toolkit: kompilatory i zależności są w builderze. Profil: CUDA 12.9.1, cuDSS 0.7.1.4, SM120, Release.

```sh
python3 tools/dev.py build --jobs 8
python3 tools/dev.py prepare tshaped-medium
python3 tools/dev.py run coax-tiny artifacts/coax-check --seconds 60
```

Katalog wyniku musi być nowy. Pełny przykład, po zapewnieniu wolnego RAM:

```sh
python3 tools/dev.py run tshaped-medium artifacts/antenna-check --seconds 1800
```

Kontrolna baza FP64 bez rekompilacji: `python3 tools/dev.py run coax-medium artifacts/coax-fp64-check --seconds 180 --basis fp64`. Zmienia wyłącznie storage GMRES; nie jest to tryb dyskowy. Pełna antena FP64 może przekroczyć budżet pamięci, więc nie używaj tej opcji tam bez rachunku.

Domyślnie: FP64 operator i faktory cuDSS, FP32 storage MGS GMRES, UVM przez adapter, niezależna kontrola normy zatrzymania, MAGMA, estymator wyłączony wyłącznie dla fixed mesh. Nie aktywujemy TF32 ani FP32 faktorów.

## Trzy poziomy cache

1. Przypięty builder zawiera skompilowane zależności i zachowane obiekty solvera. Nowy kontener dziedziczy ten stan.
2. Stały kontener `palace-dev-<hash ścieżki repo>` zachowuje `/opt/palace-cudss-build` między wywołaniami. Zmiana jednego pliku przebudowuje zależne obiekty; solver jest konfigurowany bez superbuilda zależności.
3. `ccache` w `.cache/ccache`, limit 20 GB, kontrola zawartości kompilatora. Cache przeżywa usunięcie kontenera; przy zmianie toolchainu/flag właściwe wpisy są unieważniane. Pierwsze użycie wpisów może być miss.

`build` po zakończeniu zatrzymuje własny builder. Cache pozostaje. Dwa równoczesne buildy tej ścieżki są blokowane lockiem. Build ma limit 1800 s; błąd zachowuje log i cache. Nie używać rutynowo clean ani kasowania kontenera. Nie zmieniać źródeł w trakcie builda.

Wyniki: `build/sm120/native/` (program, biblioteka, adapter), `manifest.json`, `build.log`, `history/*.json`. Manifest zawiera hashe źródeł kompilacji i binariów, obrazy oraz statystyki ccache. Nowy build nie dziedziczy automatycznie kwalifikacji numerycznej.

## Pakowanie i przenoszenie

```sh
python3 tools/dev.py package --tag localhost/palace:local-sm120
podman save -o palace-runtime.tar localhost/palace:local-sm120
```

Runtime zawiera nasze binaria i adapter; `package` korzysta wyłącznie z lokalnego przypiętego obrazu. Runner developerski montuje aktualne binaria z `build/sm120/native`, więc zwykła iteracja nie wymaga pakowania obrazu.

Obrazy są **lokalne, nie w GHCR**. Aby na drugim komputerze działał także build, raz wyeksportuj builder i bazę runtime wskazane w `tools/runtime.json`:

```sh
podman save -o palace-builder.tar localhost/palace:sm120-dev-builder-20261018
podman save -o palace-runtime-base.tar localhost/palace:cuDSS-sm120-20260917
# Na drugim komputerze:
podman load -i palace-builder.tar
podman load -i palace-runtime-base.tar
```

Sprawdź IDs względem `tools/runtime.json`; tag nie jest dowodem zgodności. Builder zawiera zależności, więc eksport może mieć wiele GB, ale odbywa się raz. `tools/containers/Containerfile.builder` odtwarza warstwę ccache na istniejącym seedzie; nie jest przepisem od zera na wszystkie zależności. Cold build, ARM/Spark i inne GPU nie zostały objęte migracją.

## Runner i ograniczenia

Runner tworzy własny kontener i własny snapshot wejść. Limit 60 GiB RAM bez dodatkowego swap, 8 CPU, deadline Podmana oraz host-guard po dwóch próbkach poniżej 6 GiB dostępnego RAM. Kończy/usuwa tylko własny kontener, pozostawia logi, telemetrię i wynik. Brak wyników lub niezerowe wyjście to FAIL, nie rekord szybkości.

Przy `--background` podczas działania procesu śledź PID i `start_ticks` z jobfile oraz czytaj osobno `palace.stdout.log`, `palace.stderr.log` i `telemetry.jsonl`. Runner dopiero po zakończeniu składa `palace.log` przez dopisanie stdout, a następnie stderr; plik końcowy **nie zachowuje globalnej chronologii między strumieniami**. Nie używaj go do odtwarzania kolejności zdarzeń pomiędzy stdout/stderr. Status i kompletność sprawdzaj po terminalnym stanie procesu.

Nie porównywać ślepo historycznych czasów z nowym buildem. Szczegóły zgodności i nierozstrzygniętej surowej reszty: [raport historyczny](local-optimization-results.md). To nadal benchmark 3,5 GHz/P2, nie nowy baseline produkcyjny anteny.

## Szybka diagnostyka bez kompilacji

coax-tiny to osobny2 mm filtr; większy coax-medium zachowuje20 mm odniesienie. --basis fp32/fp64 wybiera storage, --pc-side left/right jawnie zmienia stronę preconditionera. --coax-fields wybiera3,55 GHz i18 probes, --coax-l2 dodatkowo uruchamia kosztowniejszą całkę po wszystkich tetraedrach. Oba wymagają zweryfikowanej geometrii coaxa. Domyślne runy nie włączają tych diagnostyk.

Nowe coax runy zapisują geometry.json i actual_config_sha256 po jawnych zmianach; nie nadpisują config fixture. Przykłady i generator: examples/coax-tiny/README.md. Zmiana tych opcji/runnera nie wymaga rekompilacji solvera.

## Zachowanie referencji i dłuższy run

--save-fields/--field-reference są opisane w [kontroli pól](field-validation.md). Gorące dane pozostają w RAM/VRAM, --basis dopuszcza tylko fp32/fp64. Dawny disk basis jest usunięty; dopuszczenie sporadycznego odczytu SSD nie przywraca tej implementacji. Cache, zwykłe wejścia/wyniki i niewielkie mierzone I/O są dozwolone zgodnie z PLAN.md. UVM to GPU↔RAM, nie SSD. Kontener ma memory.swap.max=0 przez równy limit --memory/--memory-swap; nie zmieniamy globalnej konfiguracji swap użytkownika.

--allocation-trace opcjonalnie zapisuje duże (≥16MiB) alloc/free UVM ze stosami. To diagnostyka, nie profil wszystkich drobnych alokacji; koszt trzeba oddzielić od benchmarku. Telemetria ma scope globalny host/GPU oraz memory.current/peak/anon/file/shmem konkretnego cgroup, gdy dostępne. Nie sumować szczytów z różnych chwil ani nie utożsamiać nativeRSS z całym UVM. Hostguard zapisuje stop_reason=host_memory_guard, deadline runnera=runner_deadline.

Diagnostyka faz pamięci jest opt-in: `--memory-marks` zapisuje monotoniczne znaczniki faz i logiczne live/peak alokacji managed; nie synchronizuje GPU i nie mierzy fizycznej rezydencji. `--release-gmres-basis` zwalnia wektory V dopiero po rekonstrukcji rozwiązania, niezależnym stopping check i zapisaniu statystyk, przed postprocessingiem. Opcja jest domyślnie wyłączona i dopuszczona przez runner tylko dla GMRES; FGMRES/MPI nie są zakwalifikowane. Szczegóły oraz ograniczenia: [fazy pamięci](memory-phases.md).

Pozostałe profile referencji są diagnostyczne i nie zmieniają domyślnego CUDA baseline: `--cpu-reference` wybiera host FEM/GMRES i cuDSS hybrid execute, `--complex-coarse` używa istniejącej reprezentacji realnego bloku `2N×2N`, `--native-complex-coarse` jest osobną opcjonalną ścieżką CUDA FP64 complex `N×N`, a `--release-final-solver` zwalnia końcowy solver dla fixed-mesh uniform sweep przed postprocessingiem. Pełny CPU test i historyczny real-block complex-coarse zatrzymały się odpowiednio OOM i host guardem. Natywny wariant uzyskał numeryczną kwalifikację jednego punktu anteny, lecz pozostaje poza defaultem; profil UVM/kerneli i audyt pamięci domknięto później w M1; zobacz [profil](profiling-window.md) i [bilans](topology-memory.md). Parametry, ograniczenia i wyniki: [profile referencji](reference-profiles.md) oraz [natywny complex coarse](native-complex-coarse.md). Nie uruchamiać pełnych wariantów bez nowego rachunku pamięci i planu.

--background uruchamia ten sam bounded runner w nowej sesji procesu, zapisuje PID+birth i launcherlog; nie zmienia dokładności ani limitów. To opcja dla długiej anteny, nie dodatkowy serwis/kolejka. Domyślny szybki run działa dalej na pierwszym planie.

## Osobny eksperyment libCEED

[Q-pool](ceed-qpool.md) buduje jeden backend C z istniejącymi obiektami, nie cały toolchain. Opt-in --ceed-qpool ma osobny manifest i nie jest zawarty w normalnym package; brak kwalifikacji Maxwella. Domyślny runtime pozostaje bazowy. Preflight host RAM odrzuca start GPU poniżej6GiB, aktywny guard nadal działa podczas obliczeń.

## Opcjonalny seed HYPRE i scope GPU

`--hypre-pool-mib 256` ogranicza początkową rezerwację urządzenia, nie całą pamięć macierzy; [wyniki i walidacja](hypre-pool.md). Brak flagi zachowuje bazę. Telemetria ma dodatkowo sampled `gpu_process_memory_bytes` dla PID bezpośredniego single-rank entrypointu. N/A i brak procesu pozostają null; nie utożsamiać z globalnym GPU ani totalmanaged.

## Opt-in M4: dwa RHS przed pomiarami

Do standardowych FP32direct/nativecoarse/K64/pool256 można dodać
`--setup-audit --both-ports --port-setup-reuse --defer-postprocessing
--release-postprocess-energy --release-gmres-basis --release-final-solver`.
Defer zachowuje tylko pierwszy wektor E w RAM/VRAM i wykonuje pomiary obu
portów po zwolnieniu solvera. Wymaga dokładnie2LP/1f/rank1/fixedmesh/restart1,
bez wizualizacji/wave/Floquet. Snapshoty kontrolne nadal normalnymi plikami.
Każdy run zapisuje audyty, rawresidual i manifest; pełne argv w PROGRESS EXP94.
To opcje runtime bez przebudowy; nie globalny default. [Zakres](milestones/M4.md).

## Badawczy cuDSS hybrid memory — M5

`--native-complex-coarse --cudss-hybrid-mib N` to jawny budżet urządzenia cuDSS;
inne dane FEM nadal UVM. Query minimum po analysis, limit zweryfikowany przed
factor; infeasible oznacza przerwanie, nie automatyczne zwiększenie budżetu.
256..16384MiB to zakres parsera, nie gwarancja dopasowania do wolnej pamięci.
Nie łączyć CPU/hybridexecute/profiler. Obecnie niepromowany: większy budżet
spowolnił W.3 mimo poprawnych pól. [Dane i ograniczenia](native-hybrid-memory.md).
