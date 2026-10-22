# M7.4 — audyt końcowy

Stan: **M7.4 CLOSED / audyt PASS,2026-10-22**. Finalny pakiet, wszystkie
bramki numeryczne, regresje i końcowy docs-garden/root review przeszły. To audyt solvera na jednej RTX 5070 Ti 16 GB
i 96 GB RAM; nie kwalifikacja produkcyjna anteny ani dowód globalnego optimum.

## Decyzja i zmierzony kompromis

Rekomendowany kandydat pamięciowy: operator, wektory robocze, arytmetyka
i oryginalne residuum FP64; bezpośrednia baza GMRES przechowywana w FP32;
skalowane zespolone faktory LU FP32 z **trzema stałymi korekcjami FP64**;
reuse setupu obu portów dla tej samej częstotliwości i odroczone pomiary po
zwolnieniu solvera. RIGHT, K64, Tol=1e-6, medium Order2/PA1 pozostają jawne.
To wybór do ograniczenia pamięci, bez deklaracji użycia Tensor Cores.

| Porównanie | Referencja FP64 | Kandydat fixed3 | Wniosek |
| --- | ---: | ---: | --- |
| Mediana całego zadania, 3,500 GHz / oba porty, trzy pary | 745,458 s | 747,733 s | +0,305%; brak wykazanego przyspieszenia |
| Mediana peak cgroup | 60,684 GB | 46,364 GB | **−23,597%** |
| Suma 15 oddzielnych par W.5 | 10 978,169 s | 11 261,178 s | +2,578%; nie mediana ani monolityczny sweep |
| Największy peak cgroup w W.5 | 61,228 GB | 46,631 GB | −23,840% |
| Nowa geometria directora +2 mm, jedna para | 764,008 s | 755,874 s | pojedynczy pomiar czasu, RAM −23,779% |

GB oznacza 10^9 bajtów. Cgroup obejmuje pamięć procesu/kontenera; nie jest
pomiarem fizycznej rezydencji VRAM. NVML osiągał okolice dostępnych16GB
razem z pulpitem; **nie wykazano redukcji fizycznego peak VRAM**. Zmalał
rozmiar logicznych danych solvera i presja na RAM. Ambicji1,5× czasu oraz
25% peak RAM nie osiągnięto. Cel dopuszcza użyteczny zysk czasu i/lub pamięci.
Nie sumować osobnych historycznych speedupów jako zysku obecnego wariantu.

## Macierz wymagań i źródeł dowodów

Raporty poniżej wskazują konkretne eksperymenty i surowe artefakty. Audyt
sprawdza także kod i zapisane wyniki; sam checkbox nie dowodzi jakości.

| Wymaganie | Dowód i rozstrzygnięcie |
| --- | --- |
| M0.1 — historia, licencja, patche, wejścia | `tools/import.json`, LICENSE/NOTICE, ancestor `0fb92e08…` w Git; zahashowane trzy fixtures w examples. Źródłowego repo anten nie modyfikowano. |
| M0.2 — cache i uruchomienie z nowego repo | Historie `build/sm120/history/1792324926197084844.json`, `1792325032259811765.json`, `1792325118802135146.json`:2,758/1,975/1,572s. [Migracja](../migration.md), aktualne odtwarzanie R4 w [pakiecie](../runtime-package.md). Cold build całego toolchainu nie był kwalifikowany. |
| M0.3 — granice historii | [Historyczny raport](../local-optimization-results.md) i [migracja](../migration.md); dawnego disk basis/LEFT residual nie użyto jako aktualnej referencji. |
| M1.1–M1.3 — referencja i normy | [M1](M1.md), [korekta](../reference-correction.md), [pola](../field-validation.md). Kod `InitialResidual` i niezależne `A.Mult(x)-b` w iterative.cpp. Aktualne pary mają pełne FP64 odniesienie i raw<=1e-6. |
| M1.4–M1.5 — profil, powietrze i hipotezy | [Pamięć](../memory-audit.md), [topologia](../topology-memory.md), [okno profilu](../profiling-window.md). Rozłączne koszty i zakres pomiarów; potencjał usunięcia air DOF nie jest zmierzonym speedupem BEM. |
| M2.1, M2.4 — research i rzeczywisty prototyp | [Decyzja M2](M2-decision.md), [M2](M2.md), [FMM](../maxwell-fmm.md). Maxwell PEC/Mie i PMCHWT/dielektryk oraz rzeczywisty interfejs ND/RWG zostały wykonane. **Ocena zakończona; integracja REJECT.** |
| M2.2–M2.3 — bramki promocji | **FAIL**, zachowane. Transmisja i zgodność referencji nie spełniły pól/zbieżności. FMM p9 independent raw1,272e-8 przy progu1e-9; 88,396s/240DOF nie stanowi przewagi anteny. Nie promowano nowego solvera ani gęstego BEM dla całej anteny. |
| M3.1–M3.3 — baza i migracje | [M3](M3.md), [walidacja](../mixed-basis-validation.md), [prefetch](../basis-prefetch.md). Actual API CPU/CUDA, hermitowski dot, canaries, MGS/ownership i W.2/W.3. Restart120/240 nie był promowany:35iteracji nie wykorzystuje K64. FP64 fallback pozostaje. |
| M4.1–M4.4 — reuse i pomiary | [M4](M4.md): identyczne A/P i terminacje przy zmianie RHS, jedna faktoryzacja na f, oba porty oraz zwolnienie energii/bazy przed postprocessing. Osobna ocena symbolic reuse i warm start; brak przenoszenia faktorów między różnymi A(f). |
| M5.1–M5.5 — PC/mixed i wersje | [M5](M5.md), [hybrid](../native-hybrid-memory.md), [AMS](../ams-assessment.md), [mixed profile](../mixed-coarse-profile.md). Scaled complex FP32+IR wdrożone i zakwalifikowane; hybrid i pełne AMS REJECT. Profil dwóch iteracji nie jest ruchem całego solve. |
| M5.6 — konkurent FDTD/CUDA | [Budżet gprMax](../fdtd-budget.md): sam lokalny HSG przy0,1mm wymaga36,144GB przed resztą modelu; brak właściwego nested/feed API. Ocena REJECT, port anteny NOT RUN zgodnie z warunkową bramką. |
| M6.1–M6.5 — TC i fuzja | [Decyzja M6](M6-decision.md), [WMMA](../tf32-wmma.md), [cuBLASLt](../cublaslt-assessment.md), [PC FP32](../pc-basis-fp32.md). HMMA i lokalny microgain zmierzone, lecz WMMA W.1 linearity FAIL. Brak promocji TC/TF32/BF16/FP16 do anteny; oryginalny operator zachowany. |
| M6.6 — sweepy | [Sweepy](sweeps.md): reuse per f/RHS działa; history/predictor/PROM ocenione z kosztem przygotowania i held-out. PROM4 +19,77% czasu/+11,77%cgroup wobec best uniform: REJECT. Nie jest to uniwersalna niemożność przyspieszania sweepów. |
| M7.1, W.2–W.5 | Aktualny nativeA6, tiny TEM/L2 i medium3freq/2ports; W.3 dokładnie3,500/P2 w trzech nowych parach; W.5 15f/2ports i210regionalnych wierszy pól. [M7](M7.md). Antyrezonans2,9GHz osobno: [protokół](antiresonance-qualification.md). |
| M7.2 — trzy pełne pary | [Mediany](paired-medians.md); sześć odrębnych uruchomień, własne referencje, bez profilera/seeda, z kontrolą tła. Główny zysk to pamięć, nie czas. |
| M7.3 — pakiet i cykl życia | [Runtime](../runtime-package.md), EXP228–236: przypięty obraz, faktyczne binaria bez host overlays, checksumy, tiny K/TEM, deadline/SIGTERM/cleanup i legacy route. Globalne `numerically_validated=false` nie jest automatycznie przestawiane. |
| M7.5 — inna geometria | [Generalizacja](geometry-generalization.md): osobna siatka i FP64 referencja, unieważnienie starych pól/seedów/faktorów; director+nośnik+2mm, pełne K PASS. Brak twierdzenia o dowolnej paraboli. |
| M7.4, K.4 — dodatkowe lokalne pola/faza | W.3/3,500GHz48rows, pełna W.5/720rows i nowa geometria48rows PASS; metoda poniżej. |
| M7.4 — regresje/przegląd | 198testów Python w repo oraz197 z osobnego pakietu PASS;8shell, image-native tiny K/TEM i lifecycle PASS. Końcowy docs-garden/root review oraz formalne zamknięcie PASS. |

## Tożsamość i zakres aktualnej kwalifikacji

Native source SHA:
`a6ec732f11cc7fe920365ba2aae354b68fe97e81f732d5afd4659ed5187c3338`.
Trzy pliki natywne w `build/sm120/native` są sprawdzane względem pełnego
manifestu. Obraz runtime:
`43ac46f6430cf44d7a2da0a618a0f5c67c6965cca2fde510f2a96116333e6d76`.
CUDA12.9.1/cuDSS0.7.1.4/MFEM4.9/SM120, jedna ranga, jeden OpenMP thread
w pomiarach anteny. Warianty sterowane jawnymi flagami; żaden globalny default
nie zostaje po cichu zmieniony na fixed3. Nie jest to hardware attestation.

K.1/K.2: `config.json`, `fixture.json`, `build-manifest.json`, argv/environment,
telemetry i native timers zachowane dla każdej pary. Zapis background GPU/RAM
jest pomiarem tła; nie zastępuje precyzyjnego pomiaru residency. Nie było
nowej instalacji drivera/toolchainu w tej kwalifikacji; brak odrębnego
poświadczenia sprzętu i drivera dla każdego historycznego procesu ogranicza
twierdzenia o powtarzalności na innym hoście. Czas pochodzi z pełnych zadań,
nie z sumy nakładających się kerneli. Pinned środowisko nie oznacza cold builda.

K.3/K.4: każde zaakceptowane rozwiązanie ma oryginalny raw residual<=1e-6,
complex S/VSWR/power/energy i ważone complex L2 E/B względem własnej
referencji. `tools/qualify_antenna.py` wiąże referencję z rzeczywistymi
bajtami native mount, także przy ponownym odczycie dawnych artefaktów.
Kontrola fazy nie dopasowuje fazy rozwiązania do referencji.

Główne ponownie sprawdzone artefakty:

- `artifacts/m7-final-W5-reference-binding-qualification-20261022.json`;
- `artifacts/m7-final-paired-medians-reference-binding-20261022.json`;
- `artifacts/m7-final-newgeometry-reference-binding-20261022.json`;
- `artifacts/m7-final-antiresonance-reference-binding-20261022.json`;
- `artifacts/m7-final-W2-medium-reference-binding-20261022.json`;
- `artifacts/m7-package-r4-root-qualification-20261022.json`.

## Dodatkowa kontrola lokalnych pól

`tools/experiments/field_roi.{py,cpp}` odczytuje zachowane FP64 snapshots.
Używa **tego samego, podlinkowanego loadera Palace**: crack/preprocessing,
nondimensionalization, partition i ND2/RT1. CPU, bez assembly/faktoryzacji/
nowego solve. Mały control zgadza się z native normą w granicy3,582e-8
względnie; optymalizacja tablic baz/Piola daje identyczne metryki z MFEM
GetVectorValue na controlu. W antenie PCB/feed zgadzają się z native normami.

ROIs ustalone przed odczytem: PTFE feed3, PCB2, cztery sektory x/y PCB przy
promieniu>=6mm. Obejmują dielektryk obok szczelin; nie dowodzą punktowej
zbieżności osobliwości na końcówkach szczelin. W każdym ROI/porcie/polu:
complex L2<=1%, reference-weighted lokalna faza RMS<=asin(0,01)=0,572968°,
udział referencyjnej energii z niezdefiniowaną fazą<=1e-6. Dodatnie reguły
Duffy4/6, zgodność L2 między nimi<=5e-4; żadnego phase fit. Przy stałym
materiale danego ROI epsilon/mu jest wspólnym czynnikiem i skraca się w normie.

Próby238/240/242 oraz batche247–249 osiągnęły limity i pozostają **FAIL**.
Pełne,48-wierszowe checkpointy pojedynczej częstotliwości z batcha są oceniane
osobno, tylko gdy oryginalne RF solves są ukończone i pełne pokrycie/gates
przechodzą. Częściowego zestawu częstotliwości nie uznaje się za W.5 PASS.
Braki uzupełniają pojedyncze, ograniczone zadania EXP250–259. Nie zalicza to
niedokończonej symulacji RF jako zakończonej ani timeoutu jako sukcesu.

### Wynik pełnego odczytu

- W.5:720rows, max complex L2=6,094289e-7, lokalna faza RMS<=1,531814e-5°,
  undefined phase0, q4/q6 delta L2<=1,501e-9. PCB/feed normy zgadzają się
  z natywną kontrolą do1,622e-5 względnie.
- Nowa geometria:48rows, max L2=6,382824e-7, phase RMS<=1,642138e-5°,
  undefined phase0; zgodność native norm do1,134e-7 względnie.
- Dodatkowa konserwatywna kontrola antyrezonansu: lokalny kąt zespolonej
  korelacji spełnia |theta|<=pi*||c-r||/||r||. Stąd RMS fazy ważony energią
  referencji<=pi*relativeComplexL2, z najgorszą fazą pi przy zerowej korelacji.
  Dla zapisanych dodatnich norm w2,9GHz daje to <=8,079e-5° we wszystkich
  regionach/portach E/B. To granica dyskretnej normy, nie pointwise phase plot.

Dowody: `artifacts/m7-final-W5-local-fields-phase-20261022.json`,
`artifacts/m7-final-newgeometry-local-fields-phase-20261022.json`,
`artifacts/m7-final-antiresonance-phase-bound-20261022.json`. Wszystkie15
oryginalnych par RF ponownie przeszły aktualny kwalifikator z referencją
związaną bajtowo: `m7-final-W5-reference-binding-current-20261022.json`.
Żaden timeout nie został przepisany jako ukończony batch.

## Zalecane uruchomienie i fallback

Z zachowanego pakietu albo repo użyj `tools/dev.py`. Jawny pełny przykład
dla nowej konfiguracji/siatki, obydwa porty:

```sh
python3 tools/dev.py run tshaped-medium artifacts/NEW-FP64 --seconds 1800 --basis fp64 --pc-side right --krylov-size 64 --native-complex-coarse --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --setup-audit --save-fields --both-ports --frequencies 3.5 --release-postprocess-energy --defer-postprocessing
python3 tools/dev.py run tshaped-medium artifacts/NEW-MEMORY --seconds 1800 --basis fp32 --direct-basis --pc-side right --krylov-size 64 --native-complex-coarse --native-coarse-fp32 --native-coarse-corrections 3 --port-setup-reuse --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --setup-audit --save-fields --both-ports --frequencies 3.5 --release-postprocess-energy --defer-postprocessing --field-reference artifacts/NEW-FP64
python3 tools/qualify_antenna.py artifacts/NEW-FP64 artifacts/NEW-MEMORY --corrections 3 --output artifacts/NEW-QUALIFICATION.json
```

Pełny run maksymalnie1800s; na co dzień najpierw mały odtwarzalny coax.
Przy `--runtime-image` wymagany jest dokładny zweryfikowany obraz. Zmiana
geometrii korzysta z jawnego `--fixture-dir` i nowej zgodnej referencji;
stare czynniki i seedy nie przechodzą jako zgodne. Nowy przypadek ma przejść
K przed uznaniem redukcji pamięci za zakwalifikowaną. Fallback to powyższa
pełna FP64 referencja. Nie używać fixed2 do całej W.5: odrzucony przy1,71GHz.

## Granice i koszt badań

UVM oznacza RAM↔VRAM. Kontenery mają `memory.swap.max=0`; baza/workspace nie
są strumieniowane na SSD. Zwykłe siatki, snapshoty, logi i cache są I/O;
same30zadań W.5 zapisały35,305GB artefaktów. Dodatkowy replay czyta istniejące
wyniki i zapisuje małe checkpointy; zapisane artefakty mają892727B, a konserwatywna granica wszystkich nadpisań
JSON wynosi5923264B (bez zwykłego cache kompilacji). Suma czasu procesów
replay to7924,609s; nie jest to walltime, bo część zadań działała równolegle.
Dowód: `artifacts/m7-final-offline-audit-cost-20261022.json`. Odczyty dużych
snapshotów nie były mierzone jako fizyczne SSD I/O; nie twierdzimy, że ich nie było.
Pomiarów czasu offline audytu nie doliczać do produkcyjnego czasu solve,
ale nie ukrywać ich jako kosztu badań. Zużycia energii nie zmierzono.

Nie zakwalifikowano multi-GPU/NVLink, ARM/Spark, innych GPU, pełnych testów
upstream ani zdalnego CI, fizycznej anteny/mesh convergence, dowolnej paraboli,
ciągłego pasma, Tensor Cores w produkcyjnym solve, Rust lub CAD/GUI. Są poza
tym celem albo jawnie odrzuconymi gałęziami. Pozostaje lokalny Git; jedyny
remote to upstream AWS, bez publikowania tam prywatnych zmian.


## Finalny pakiet i regresje

`artifacts/m7-sm120-bundle-final-20261022`, ten sam nativeA6 i runtime43ac.
EXP260–263: profil memory18,498s, FP6418,408s end-to-end; oba complete,
39/42iteracji i wszystkie K/TEM/volumeL2/reference-byte/image-native checks
PASS. Deadline i SIGTERM dają oczekiwane incomplete oraz brak kontenerów;
nie są wynikami RF. To mały test odtwarzania, bez wniosku o zysku czasu/RAM.
Root receipt: `artifacts/m7-package-final-root-qualification-20261022.json`.
198testów Python PASS osobno w repo i z pakietu uruchomionego z `/tmp`;
8testów shell, checker dokumentów oraz diffcheck PASS. Nie ma aktywnych
kontenerów pomiarowych. Po końcowym przeglądzie dołączana jest kompaktowa,
zakresowa `QUALIFICATION.json`; nie zmienia globalnego manifestu native.


### Jawny krok oceny ROI

`field_roi.py run/batch` zapisuje `complete=true` wyłącznie dla ukończonego
odczytu. Nie oznacza to jakości ROI ani zaliczenia RF. Osobna funkcja
`assess()` jest wystawiona jako CLI; wymaga pełnego, unikalnego pokrycia,
sprawdza L2/fazę/zera/NaN oraz zgodność q4/q6. Przykład odtworzenia końcowej
oceny W.5 (na zapisanym scalonym zbiorze wierszy):

```sh
python3 tools/experiments/field_roi.py assess artifacts/m7-final-W5-local-fields-phase-20261022.json --frequencies 1.71 1.785 1.805 1.88 1.92 1.98 2.11 2.17 2.5 2.57 2.62 2.69 3.3 3.55 3.8 --output artifacts/NEW-ROI-ASSESSMENT.json
```

CLI nie poświadcza pochodzenia wierszy. Root osobno sprawdził pełne RF solves,
reference-byte binding, manifesty oraz zgodność PCB/feed z native normą.
Scalony zbiór zachowuje źródła; częściowe częstotliwości nie weszły do niego.
Rzeczywiste ponowienie jawnego CLI dla720W.5 i48nowej geometrii PASS:
`m7-final-W5-ROI-cli-assessment-20261022.json` i
`m7-final-newgeometry-ROI-cli-assessment-20261022.json` w artifacts.
