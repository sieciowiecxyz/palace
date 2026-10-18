# M1: profil CUDA z niezależnym zegarem hosta

EXP20/22, 2026-10-18. **PASS krótkiego profilu W.3**. Nie jest to zakończony
solve RF ani pomiar przyspieszenia; referencja bez profilera pozostaje EXP19.

## Odtworzenie i metoda

```sh
python3 tools/nsight_window.py setup
python3 tools/dev.py run tshaped-medium artifacts/new-short-profile --seconds 600 --basis fp64 --native-complex-coarse --hypre-pool-mib 256 --memory-marks --pc-side right --krylov-size 64 --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --nsys-window 2:2
```

Nowy katalog wyniku, gotowy manifest/native oraz wolny RAM są wymagane.
`--nsys-window FIRST:COUNT`: FIRST0..32, COUNT2..8, jeden rank CUDA/FP64.
Native zatrzymuje się po wybranych iteracjach kontrolowanym wyjątkiem;
`complete=false` dla RF jest obowiązkowe, osobne `profile_complete` opisuje ślad.
Bez flagi żaden hook synchronizacji/profilowania nie działa.

CLI Nsight2026.5.1.161 jest przypięty SHA w `tools/nsight_window.py` i zachowuje
cache w build/. Nie zmieniono systemowego CUDA/drivera. Aktualny trace to
`cuda-sw` bez NVTX, `--cuda-trace-all-apis=true`, `--kill=none --wait=all`.
Bezpośredni native target dostaje LD_PRELOAD przez `--env-var`, nie przez env wrapper.
Zbieramy cały ograniczony proces; okno wybieramy offline.

`tools/host_phases.py` łączy fazy BlockTimer i dodatkowe zakresy ortogonalizacji
z CPU launch zapisanym przez CUPTI. Na początku i po każdej wybranej iteracji
hook emituje rozpoznawalną parę CUDA version-query/synchronize oraz niezależny
przedział czasu hosta. Dopasowanie afiniczne używa pierwszego/ostatniego markera;
markery wewnętrzne sprawdzają dopasowanie. Dopuszczona niepewność diagnostyczna
wynosi10µs, odchylenie szybkości zegara maks1000ppm. Launch w pobliżu granicy
fazy pozostaje nieprzypisany. To nie zmienia żadnej tolerancji RF/pól/residuum.
Brakujące markery, błąd większy od marginesu, ostrzeżenie kolektora lub exit/OOM
powodują FAIL. Kompaktowe szczegóły błędu kalibracji pozostają w JSON.

Korelacja używa procesu, wątku i czasu CPU launch. Inne wątki wewnątrz okna,
kerneli spoza okna i nierozstrzygniętych launchów nie łączymy w jedną kategorię.
Przeniesienia w oknie wybieramy po czasie aktywności GPU; granice okna mają
synchronizację urządzenia. Sum czasów kerneli i kopii nie dodajemy do wall time.

Trace/SQLite/temp pozostają w /dev/shm lub kontenerowym tmpfs, cap60GiB,
zero dodatkowego swap, hostguard6GiB/deadline bez zmian. Mały końcowy rep do64MiB
może zostać zwykłym wynikiem; większy jest usuwany po analizie wraz z temp.
Dla dużych raportów zachowujemy JSON/manifest/SHA/logi, nie surowy rep.

## Wynik na właściwej antenie

`artifacts/m1-cuda-affine-antenna-20261018/`:3,50GHz/P2, medium bez zmian,
iteracje2–3, clean native exit0, noOOM/noGuard, brak ostrzeżeń. Kalibracja:
scale1,00000012239, held-out błąd1,127µs, containment error0,667µs.
4939kerneli w oknie, jeden niejednoznaczny przy granicy, pozostałe przypisane.

| Faza hosta | Czas w dwóch iteracjach |
| --- | ---: |
| Całe okno | 17,665s |
| Preconditioner inclusive | 16,278s |
| W tym coarse solve | 5,490s |
| Ortogonalizacja | 0,156s |

Preconditioner to92,15% tego wczesnego okna, coarse jest w nim zawarty.
Nie ekstrapolować kosztu wczesnej ortogonalizacji na późną długą bazę GMRES.
Największe kerneli według elapsed GPU: hcurl QFunction2,890s, cuDSS backward1,984s,
MAGMA interpolation1,640s, MAGMA derivative1,384s, cuDSS triangular solve1,144s.
Elapsed kernela może zawierać stalle UVM; nie jest pomiarem samych FLOP.

| Ruch UVM, enumy z raportu Nsight | Bajty | Suma czasu aktywności |
| --- | ---: | ---: |
| H→D page fault/coherence | 11 549 298 688 | 1,691s |
| H→D speculative prefetch | 136 977 391 616 | 4,289s |
| D→H eviction | 146 945 318 912 | 2,722s |

Razem295,472GB, czyli powtarzane strony i oba kierunki, nie unikatowa pamięć.
Dodatkowo252D2Dkopie/15,186GB/0,504s. Czas kopii może nakładać się na kerneli.
To mocny dowód presji UVM, ale nie kontrolowany dowód zysku konkretnej polityki.

Cały run diagnostyczny269,94s zawiera setup, cleanup i przetwarzanie Nsight.
Cgroup56,856GB, managed49,583GB, sampledGPUprocess2,206GB, minhost8,855GiB.
Sampling nie mierzy całej rezydencji UVM. Raport214MB/SQLite652MB przekraczał
limit zachowania64MiB; pozostały JSON z sumami, SHA wejść/raportów i root-analysis.
Nie używać tego czasu jako benchmarku finalnego solvera.

## Odrzucone próby i granice

Historyczne `m1-nsys-window-tiny*`: NVTX-trigger/SIGTERM, czyste stop/wait,
cudaProfilerAPI, całe procesy, direct-env i wykluczenie CCCL nie dały śladu NVTX
bez ostrzeżenia. Są REJECT. Pierwszy błędny profile_complete pomijał SQL warnings;
root-analysis koryguje go, a walidator już sprawdza SQL severity/loss messages.
Nie ignorowano ostrzeżeń, aby zaliczyć wynik.

CUDA-only tiny z identycznym zegarem przeszedł; pierwszy duży test
`m1-cuda-hostclock-antenna-20261018` obalił założenie ścisłej identyczności zegarów.
Surowy duży raport nie został zachowany przez cap64MiB — nie przypisujemy
mu później ustalonej przyczyny. Ten run dał niezależny aktualny audyt alokacji.
Triggered capture tiny z afinicznym zegarem nadal ostrzegał o CUDA; REJECT.
Dopiero whole-process CUDA-only + trzy markery + jawna niepewność przeszły
na tiny i antenie. Brak zmian progów fizyki, medium i solvera numerycznego.

Źródła: [oficjalny Nsight User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html)
(capture/env/trace) i [kontekst ostrzeżeń procesowych NVIDIA](https://forums.developer.nvidia.com/t/nsight-systems-2026-2-1-windows-scope-of-cuda-nvtx-warnings-associated-with-another-process/384556).
Drugie źródło dotyczy Windows/innego procesu; nie uznano go za dowód niewinności
naszego ostrzeżenia. Fakty projektu potwierdzają własne raporty.
