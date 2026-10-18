# Postępy optymalizacji

Aktualizacja: 2026-10-18. Mode: goal, Active: M1. [PLAN](PLAN.md), [MILESTONES](MILESTONES.md), [raport M1](docs/optimization-baseline.md), [kontrola pól](docs/field-validation.md).

## Wymóg użytkownika

**Dane robocze solvera wyłącznie w RAM/VRAM.** Bez SSD/NVMe scratch, disk basis, out-of-core, plikowego mmap ani swap jako sposobu na zmieszczenie obliczeń. UVM może migrować GPU↔RAM. Nie zamykać aplikacji użytkownika. Cache kompilacji oraz zwykłe wejścia i wyniki pozostają osobną funkcją. Usunięto disk basis; legacy env są odrzucane przed inicjalizacją MPI/CUDA.

## Bieżący checkpoint

- M0 zamknięty, M1 otwarty; brak promowanej optymalizacji pełnej anteny. Lokalny sprzęt: jedna RTX 5070 Ti 16 GB + 96 GB RAM, tryb medium, bez płatnego compute.
- Pełna antena FP64-disk reference oraz FP32-disk candidate z porównaniem pól są zachowane historycznie i oznaczone **REJECT**. Nie są dopuszczalnym baseline ani wynikiem dla wymaganego storage RAM/VRAM; nie odtwarzać starych poleceń.
- Wcześniejszy resident FP32 run anteny przerwał RAM guard około 141 iteracji/1087,70 s; brak S/pól. Globalna pamięć obejmowała aplikacje użytkownika, więc ten wynik nie dowodzi, że antena nie mieści się na sprzęcie.
- Po usunięciu disk basis wykonano resident-only coax-tiny: 6/6 solve'ów w 14,06 s, iteracje 24/13/14/25/13/13, zweryfikowane stopping relative ≤1e−6, cgroup peak 0,68 GiB. Log potwierdza `FP32 RAM/VRAM`; bez zapisu pól ani referencji. To smoke ścieżki solvera, nie kwalifikacja anteny.
- Trace alokacji dużej anteny pozostaje materiałem audytowym. Ostatni disk run miał cgroup peak 49,24 GiB, logical managed high-water ~45,17 GiB i cuDSS peak 7,52 GiB; telemetry obejmowała także globalny desktop. Nie traktować tych danych jako budżetu resident wariantu ani czystego benchmarku.
- Otwarta kwestia jakości: raw residual ~0,125 różni się od stopping norm LEFT. Kontrole TEM i całych pól na małym coaxie przechodzą, ale nie dowodzą poprawności fizycznej ani błędu pełnej anteny.

## Rejestr eksperymentów

| ID | Wynik i decyzja | Artefakty / ograniczenia |
| --- | --- | --- |
| EXP01 | Coax FP32/FP64: porty zgodne; raw residual nie znika z FP64, sam storage nie wyjaśnia norm. | `artifacts/m1-coax-{raw-residual,fp64-raw-residual}-20261018/` |
| EXP02 | Audyt anteny: AIR 61,71% elementów, PTFE 30,03%; dense BEM block ~11,90 GiB to rachunek ilustracyjny, nie pomiar oszczędności. | `artifacts/m1-mesh-audit-20261018.json` |
| EXP03 | Probes TEM E/B/energia PASS; LEFT vs RIGHT pokazuje różnicę raw/stopping, RIGHT wymaga więcej iteracji. | `artifacts/m1-tem-fields-*` |
| EXP04 | Tiny natywne L2 PASS <1% obu portów; wcześniejszy 20 mm L2 FAIL/deadline 180 s zachowany. | `artifacts/m1-tem-validation-20261018.json` |
| EXP05 | Całe pola tiny FP32 vs FP64 PASS (E≤1,14e−7, B≤6,09e−5); sztuczne B×1,02 prawidłowo FAIL; disk/resident tiny PASS, lecz disk storage odrzucony wymogiem. | `artifacts/m1-fields-tiny-*` |
| EXP06 | Pierwszy antenna run przerwany sygnałem, przyczyna nieustalona; background tiny potwierdził live PID. FP64-disk ref ukończona; wcześniejszy resident FP32 antenna run FAIL/host guard. | `artifacts/m1-antenna-field-attempt-20261018.json`, `artifacts/m1-background-smoke-20261018/`, dalsze dane w raporcie M1 |
| EXP07 | FP32-disk antenna zakończona po 151 iteracjach/1563,128 s; 7 porównań pól PASS (max E 2,75e−5/B 3,66e−3). **REJECT** — storage dyskowy zabroniony; scratch usunięty. | `artifacts/m1-antenna-fields-fp32-disk-20261018/`; szczegóły w raporcie M1 |
| EXP08 | Po usunięciu disk basis resident coax-tiny: 6/6 PASS, 14,06 s, cgroup peak 0,68 GiB; brak pól, anteny i kwalifikacji RF. | `artifacts/m1-no-disk-basis-resident-20261018/` |

Artefakty lokalne zawierają dokładne argv/config/build manifesty, wyniki, telemetry i logi tam, gdzie dany test je generował. FAIL kompletności nie jest wynikiem RF; nie wyprowadzać błędu anteny z nieukończonej próby.

## Następny krok

1. Agent główny analizuje zachowany trace alokacji, rozdzielając operator/q-data/preconditioner/basis/workspace od cgroup, UVM i globalnej pamięci hosta.
2. Zaprojektować ewentualne oszczędności wyłącznie w RAM/VRAM i najpierw kontrolować je na małych fixture'ach. Nie obniżać medium, jakości ani RAM guard.
3. Wrócić do pełnej anteny dopiero po konkretnej hipotezie, znanej dostępnej pamięci i kontroli jakości; poprzednie disk wyniki nie są baseline.
4. Zamknąć bramki M1 przed wymaganym prototypem FEM–BEM/MoM w M2. Nie odhaczać etapu na podstawie pojedynczego smoke.

## Reguły pracy

Jedna próba = hipoteza, dokładne argv/hash, limit, wynik i decyzja; FAIL nie jest speedup. Nie powtarzać referencji/sweepów bez potrzeby. Zachować cache CMake/ccache/dependencies. Ta sama Luna high wykonuje wyłącznie gotowe uruchomienia/babysitting i docs-garden; projekt i interpretacja należą do agenta głównego. Cel pozostaje aktywny i nieukończony.

Dodatkowa kontrola guard: aktualny natywny binary w kontenerze odrzucił oba legacy env PALACE_GMRES_FP64_DISK_BASIS/PALACE_GMRES_FP32_DISK_BASIS (exit1, komunikat RAM/VRAM) przed MPI/CUDA. Dowód: artifacts/m1-no-disk-basis-resident-20261018/legacy-rejection.json. Build63,11s; resident tiny14,06sPASS. Następnie 16 regresji narzędzi PASS, w tym dwa przypadki nowego audytu alokacji; szczegóły w [docs/testing](docs/testing.md). HostSwapTotal=0; nie zmieniano konfiguracji systemu.

## EXP09 — audyt bez nowej symulacji

PASS analizy: tools/allocation_audit.py odtworzył duże alloc/free ze stosami, odzyskał 3 zdarzenia doklejone do stdout i przypisał 99,50% logicznego peak 45,18 GiB. W tej samej chwili 48 buforów po 538 043 520 B = 24,05 GiB, ścieżki libCEED QFunction/basis/assembly. To nie fizyczna rezydencja i nie obietnica odzyskania 24 GiB. Źródła przypiętego libCEED cbd4902 potwierdzają per-operator Q-vectors oraz brak fused curl/div w cuda/gen, dlatego nie uruchamiano ślepego benchmarku nowego backendu. Audyt i hipoteza workspace: [docs/memory-audit](docs/memory-audit.md); dane `artifacts/m1-antenna-allocation-audit-20261018.json`. Nie zmieniano kodu numerycznego ani zależności, cache/build bez rekompilacji. M1 nadal otwarty.
