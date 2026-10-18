# M1: krótki profil CUDA i jego ograniczenia

EXP20, 2026-10-18. Status: **REJECT kwalifikacji profilu**. Nie zmieniono
referencji RF ani progów jakości. Nie wykonano dużego profilu anteny.

## Mechanizm

`tools/nsight_window.py setup` pobiera i weryfikuje oficjalny CLI Nsight
Systems 2026.5.1.161. SHA pakietu:
`61829db6392e5c293ada1319df86a97c3356bc810335a1975cb551fcfe3eca08`.
Cache w `build/nsight-2026.5.1`, bez instalacji systemowej lub zmiany CUDA.
Ponowne `check/setup` sprawdza manifest/binarium i zachowuje cache.

`tools/dev.py run ... --nsys-window FIRST:COUNT` jest diagnostyką jednego
ranku CUDA/FP64. FIRST=0..32, COUNT=1..8. Native synchronizuje CUDA, otwiera
NVTX `Krylov sample`, wykonuje wybrane iteracje, synchronizuje, zamyka zakres
i kończy kontrolowanym wyjątkiem przechwyconym w main. Nie przechodzi do
postprocessingu niepełnego rozwiązania. Bez tej flagi ścieżka jest nieaktywna.

Obecny wariant zbiera cały ograniczony proces przez `--trace=cuda-sw,nvtx`, bez
triggered capture, z `--kill=none --wait=all`. Software tracing jest jawnie
wybrane; początkowy test bez cuda-sw miał ostrzeżenie o fallbacku z hardware.
Offline wybiera zagnieżdżone
zakresy iteracji. Kernel przypisuje przez czas CPU launch, proces i wątek,
nie przez czas startu GPU; poza oknem zachowuje osobną kategorię. Sumy kerneli
i kopii dotyczą całego ograniczonego procesu i nie są czasem wall ani
automatycznie pomiarem migracji UVM. Enumy typów kopii pochodzą z raportu.

Wszystkie trace/SQLite/temp są w `/dev/shm` lub kontenerowym tmpfs.
Zachowywany mały `.nsys-rep` (do64MiB) i JSON to zwykłe wyniki diagnostyczne;
nie są storage solvera. Runner usuwa temp również po przerwanym uruchomieniu.
Stosuje dotychczasowe cap60GiB, zero dodatkowego swap, hostguard6GiB i deadline.
Telemetria znajduje rzeczywisty Palace PID w poddrzewie kolektora, również
gdy dziecko uruchomił pomocniczy wątek Nsight. Nie mierzy innych aplikacji.

## Próby i decyzje

Artefakty: `artifacts/m1-nsys-window-tiny[-r2/-r3/-r4/-r5]-20261018/`.
Każda próba była małym coaxem i kończyła obliczenia po kilku iteracjach.

| Próba | Zmiana | Wynik |
| --- | --- | --- |
| Pierwsza | NVTX trigger, stop-shutdown/SIGTERM | 9,36s; CUDA+NVTX warning; exit143 |
| r2 | Software trace, native sync/unwind | 8,44s; stop-shutdown kończy sesję przed potwierdzeniem cleanup; warnings |
| r3 | Stop capture, czekanie na aplikację | 8,55s; clean-stop PASS, CUDA+NVTX warnings |
| r4 | cudaProfilerStart/Stop i flush | 8,44s; clean-stop PASS, warnings pozostają |
| r5 | Cały bounded proces, bez triggera | 9,41s; CUDA warning znika; NVTX warning pozostaje |

Pierwotny walidator pomijał ostrzeżenia SQL i błędnie zwrócił
`profile_complete=true`. Oryginał zachowano; `root-analysis.json` pierwszej
próby jawnie koryguje kwalifikację. Teraz kontrola obejmuje SQL diagnostics,
markery, clean-stop i dokładnie jedno okno z oczekiwaną liczbą faz. Wszystkie
próby pozostają REJECT. `complete=false` dla RF jest zawsze wymagane w tym trybie.

r5: 9 364 kernel records i 2 302 copy records całego procesu, w wybranym
oknie po dwie fazy Preconditioner/Coarse Solve/orthogonalization. Dane są
zachowane do diagnozy, nie stanowią dowodu kompletnej atrybucji. Proces GPU
widziany w telemetrii: peak689 963 008B, cgroup1 152 438 272B. Poprawiony PID
działa; nie oznacza to kwalifikacji profilu dużej anteny.

Nie powtarzać tych samych wariantów ani pełnego profilu z tym ostrzeżeniem.
Następnie ustalić zakres brakujących NVTX events i zgodność kolektora albo
zastosować niezależną metodę pomiaru. Nie uznawać synchronizacji CUDA za
dowód opróżnienia wszystkich buforów Nsight. Wymagania capture/flush i
ograniczenia opisuje [oficjalny User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html).
Użyto driver615.78.08, CLI2026.5.1 i jego CUPTI13.4; zależności solvera bez zmian.

Regresje narzędzia sprawdzają granice okna, PID dzieci wątków, korelację
launch/process/thread, selekcję NVTX, odrzucenie SQL warning i brakującego
clean-stop. Pozostały [bilans DOF/pamięci](topology-memory.md) jest niezależnym
audytem offline i nie dziedziczy kwalifikacji Nsight.
