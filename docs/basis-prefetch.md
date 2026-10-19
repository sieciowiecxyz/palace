# M3 — ocena prefetchu bazy GMRES

EXP86–90, 2026-10-19. Etap M3 zakończony; bez zmiany globalnych defaultów.
Zmierzona korzyść pamięci FP32direct pozostaje około 2,87 GB cgroup w W.3.
Prefetch ma mały wpływ na późną ortogonalizację, nie usuwa presji 25 GB cuDSS.

## Implementacja i odtwarzanie

`--basis-prefetch` wymaga `--basis fp32 --direct-basis` i CUDA.
`StoredBasisVector::Dot` zleca `cudaMemPrefetchAsync` dla źródłowych części FP32
na strumieniu 0, przed kernelem MFEM. AddTo korzysta z tych samych danych po Dot.
Weryfikujemy managed pointer oraz concurrent managed access; błędy CUDA przerywają.
Nie ma dodatkowej synchronizacji ani trwałych porad preferred/readmostly.
FP64 arithmetic/partials, operator, MGS i reliable stopping pozostają.

`PALACE_GMRES_BASIS_PREFETCH` jest opt-in; runner usuwa odziedziczoną wartość.
`PALACE_BASIS_PREFETCH` raportuje wywołania i żądane bajty, nie transfery ani rezydencję.
Runner wymaga dodatnich liczników dla każdego pełnego solve. Ścieżka CPU/FP64/unpack
odrzuca tę opcję przed alokacją zasobów. Zero iteracji nie kwalifikuje działania opcji.

Dokładne argv EXP86–90 są w PROGRESS.md. W.3 używa warm start, 3,50 GHz/P2,
K64/RIGHT, native complex coarse FP64 i pool256MiB. Limity: 1800s/60GiB/noswap,
guard6GiB; zwykłe wejścia/wyniki i cache są oddzielone od pamięci roboczej.
Fallbacki native+manifest: `build/m3-basis/pre-prefetch-native` oraz
`pre-selective-profile-native`. Dane robocze wyłącznie RAM/VRAM.

## Wyniki jakości i pamięci

| Kontrola | Wynik |
| --- | --- |
| EXP86 tiny, 3,55 GHz/oba porty | PASS, 62/64 iteracje, raw≤9,045e-7 |
| EXP89 W.2, 3,30/3,55/3,80 GHz/oba porty | PASS, 45/47 iteracji, raw≤8,334e-7 |
| W.2 vs niezależna referencja FP64 | maxΔS5,666e-9, ΔVSWR4,794e-9, E/B≤7,555e-7/9,423e-9 |
| EXP90 W.3 na aktualnym native | PASS, 35 iteracji, raw8,357e-7, E/B≤6,684e-9/4,860e-10 |
| W.3 vs świeży EXP86 control | ΔS2,946e-10, ΔVSWR(P2)2,865e-10 |
| Actual API CPU/CUDA na aktualnym native | po10 przypadków oraz real/complex MGS PASS |

W.2 zachowuje TEM q4/q6 dla obu portów: E<0,495%, B<0,457%.
W.3 porównuje wszystkie7regionów całych pól bez dopasowania fazy; nie jest to mapa
punktowej fazy szczelin ani kwalifikacja W.4/W.5. Probe API bada domyślną ścieżkę
bez prefetchu, który wymaga managed storage; prefetch sprawdzono w rzeczywistych runach.

EXP86 porównanie tego samego buildu: 408,622s bez / 396,526s z prefetch;
EXP90 zintegrowany kandydat399,446s. Jedna para nie dowodzi speedupu.
Managed peak pozostaje52,277GB, cuDSS25,008GB; cgroup około56,02GB.
Licznik GPU procesu nie obejmuje całej rezydencji UVM. W.3 włączony prefetch
raportuje1260 wywołań/56,542GB żądanych danych.

## Rzeczywiste transfery — późne iteracje30/31

EXP88, oba profile tego samego buildu/config przechodzą kalibrację, pokrycie
iteracji i kontrolę ostrzeżeń. Czasy faz są inclusive i mogą się nakładać.

| Pomiar okna dwóch iteracji | Bez prefetchu | Z prefetchem |
| --- | ---: | ---: |
| Okno hosta | 15,192s | 14,761s |
| Preconditioner, w tym coarse | 13,567s | 13,505s |
| Sam coarse | 4,869s | 4,879s |
| Ortogonalizacja | 0,706s | 0,330s |
| UVM H→D + D→H | 274,732GB | 272,984GB |
| UVM na iterację | 137,366GB | 136,492GB |

Ruch zmalał o0,6363%; obejmuje wielokrotne migracje stron. Jawny prefetch H→D
5,654GB częściowo zastąpił page faults/speculative prefetch. Nie dodawać czasów
kopii i kerneli, aby wyznaczyć procent czasu transferów: mogą się nakładać.
Wniosek: lokalna poprawa ortogonalizacji, mały wpływ na dominujący koszt PC.

## Naprawa pomiaru i decyzja

EXP87 zbierał cały proces do późnego okna: FAIL/OOM przy60GiB, bez podnoszenia limitu.
EXP88 pierwszy mały capture z końcem `stop` miał ostrzeżenie o możliwej utracie
zdarzeń: FAIL. Aktualny profiler zaczyna zbieranie przez cudaProfilerStart przy
wybranym oknie, `--capture-range-end=none` pozwala na czyste wyjście i cleanup.
Ścisłe bramki ostrzeżeń/kalibracji pozostają; tinyv2 i oba profile W.3 PASS.
Trace/SQLite powstają w RAM `/dev/shm`; zapisany raport to zwykły wynik diagnostyczny.

Prefetch pozostaje opcją eksperymentalną, bez promocji czasu/defaultu. Porównanie
restartów120/240 nie było testowane:35 iteracji mieści się już w K64, więc oba
większe K nie zmniejszą dotkniętej bazy. Zejście poniżej35 wymaga osobnej hipotezy
zbieżności, a główny koszt pozostaje w PC. M4 sprawdzi reuse setup przed M5.

Dowody: `artifacts/m3-prefetch-{tiny,antenna,profile,final}-root-analysis-20261019.json`,
`m3-prefetch-api-{cpu,cuda}-20261019`, terminal receipts/config/native SHA w runach.
Globalna kwalifikacja i powtórzenia czasowe pozostają w M7.

Źródła pierwotne, odczyt2026-10-19: [CUDA12.9 memory API](https://docs.nvidia.com/cuda/archive/12.9.0/cuda-runtime-api/group__CUDART__MEMORY.html)
(prefetch może wypchnąć inne managed pages),
[Nsight Systems User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html)
(capture-range), [wyjaśnienie NVIDIA o forced flush](https://forums.developer.nvidia.com/t/nsight-systems-2026-5-1-produced-112-collected-100-warning-despite-complete-coverage-of-32-kernels/384749)
(nie uzasadnia ignorowania ostrzeżenia w naszym runie).
