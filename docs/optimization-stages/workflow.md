# Trzy ścieżki: umowa pracy i pamięć eksperymentów

## Stan i dowody początkowe

2026-10-29: użytkownik uruchomił wykonanie; Mode goal / Active none; Status complete_scoped; M0–M6 rozliczone dla profilu Restart1 2026-10-30.
Wykonawcy: GPT-6.1 Sol high. Strata była zatrzymana za zgodą użytkownika na czas pomiarów; po zakończeniu kampanii przywrócona.
Panel systemowy: get_goal 2026-10-30 potwierdził active objective
„kontynułuj. Monitoringsub agentów i dokoń optymalizacje zgodnie z planem”.
Wcześniejsza odmowa create_goal dotyczyła historycznego stanu panelu.
Root checkout: `/home/sieciowiec/dev/cpp/palace`, branch `codex/local-cuda`,
początkowo audytowane HEAD `e288fe1639cef892b4cbfae0d98046a0afa62ae1` (stan przed M0).
Zgodność źródeł/runtime zamknięto w M0; bieżący prototyp OP używa compiler-source
`b834…`/native `bc7…`, a PRE ma osobne manifesty. Nie utożsamiać historycznego HEAD
z aktualnym wykonywanym buildem; każdy plan sprawdza własną pełną tożsamość.
Referencja: `/home/sieciowiec/dev/python/anteny/artifacts/tshaped/port-repair-20261028/rear-route-sma-only/run-local-stages-20261029/`.
Czytaj `STAGES.md`, `stage-report.json`, config/manifest i log; runtime:
`/home/sieciowiec/dev/cpp/palace/artifacts/m7-sm120-bundle-r3-20261022`,
obraz ostatniego runu `43ac46f6430cf44d7a2da0a618a0f5c67c6965cca2fde510f2a96116333e6d76`.
Nie zastępować go automatycznie starszym obrazem z runtime.json.

| Exclusive kategoria Palace | s | Udział |
|---|---:|---:|
| Initialization + Mesh Preprocessing | 35,992 | 4,36% |
| Operator Construction | 121,501 | 14,71% |
| Disk IO | 19,612 | 2,37% |
| Pozostałe | 648,678 | 78,55% |
| Total | 825,783 | 100% |

Te trzy kategorie to 21,45% całości. Nawet usunięcie całego ich kosztu daje najwyżej
około 1,27× E2E przy niezmienionej reszcie. To rachunek graniczny dla tego runu,
nie prognoza; zmiana lokalności może także wpłynąć na solve. Serializacja CSV/VTK
może być poza Timer::IO, więc najpierw uzgodnić rzeczywiste granice.
Na CMP construction ≈402 s; JIT ≈24,3 s w osobnym profilu. Wniosek: mierzyć
host-side assembly, nie zakładać automatycznie wolnego NVMe/JIT/PCIe.

## Przydział i izolacja

| Rola | Worktree / branch | Własność |
|---|---|---|
| Agent preprocessing | `/home/sieciowiec/dev/cpp/palace-opt-preprocessing` / `opt/preprocessing-20261029` | geodata/meshio, testy topologii, preprocessing.md |
| Agent operatory | `/home/sieciowiec/dev/cpp/palace-opt-operators` / `opt/operators-20261029` | spaceoperator, bilinearform, wąskie CEED assembly, operators.md |
| Agent I/O | `/home/sieciowiec/dev/cpp/palace-opt-io` / `opt/io-20261029` | outputdir/tablecsv/postoperatorcsv/serialization, io.md |
| Koordynator | root; później `opt/stages-integration-20261029` | timery, runner, manifesty, build glue, PLAN/MILESTONES/PROGRESS/INDEX, integracja |

Wspólny mesh parser jest własnością preprocessing, I/O zgłasza potrzebny patch.
Zmiany postoperator/timer/build przechodzą przez koordynatora, żeby uniknąć konfliktu.
Nie modyfikować anteny, .env, .toolchain ani gotowych bundle. Istniejące cudze zmiany
(root docs/INDEX.md, docs/ampere.md, tools/build_ampere.py) pozostają zachowane.
Branche powstały z czystego HEAD; po zamknięciu planu koordynator synchronizuje
własne dokumenty, następnie M0 ustala wspólną bazę kodu dla implementacji.

Trzech agentów może równolegle analizować/pisać kod/testy lekkie. Jeśli limit sesji
na to nie pozwala: odnotować limit i użyć istniejącego wykonawcy kolejno, nie udawać
trzech aktywnych sesji. W tym audycie preprocessing i operatory były równoległe;
I/O wykonał ponownie pierwszy agent po zakończeniu swojego audytu.

## Kontrakt wpisu — obowiązkowy przed i po każdym eksperymencie

Agent aktualizuje swój plik po każdej próbie i przed oddaniem pracy/utratą kontekstu.
Nie tworzy nowego ledgeru na każdą sesję; dopisuje wynik do stabilnego ID hipotezy.

```text
ID: PRE-xx / OP-xx / IO-xx; eksperyment: <ID>-E01
Status: TODO_TO_CHECK | IN_PROGRESS | PASS | REJECTED | DEFERRED
Owner / branch / data:
Pytanie i spodziewany mechanizm:
Źródło: plik:symbol:linia + SHA / link do dokumentacji konkretnej wersji
Sprawdzona historia: ID wcześniejszych prób / dlaczego to nowy test
Fingerprint: source+diff, binary+adapter+image, dependency versions,
 mesh/config/output hashes, sprzęt/sterownik, threads/ranks,
 precision/backend/UVM, cache cold/warm, argv, input fields hash dla replay
Referencja i zmieniana jedna rzecz:
Kryteria poprawności / korzyści / timeout / RAM / I/O budget:
Polecenie i stan zasobów:
Wynik: exit, wall/faza/CPU, bytes/read/write, RAM/VRAM,
 raw residual/complex S/pola/power; NOT RUN gdy brak pomiaru
Dowody: logi + raport ścieżki/SHA, commit patcha
Decyzja: dlaczego PASS/REJECTED/DEFERRED; ograniczenia
Następna akcja / warunek ponowienia:
```

Przed runem wyszukać ID i fingerprint we wszystkich trzech ledgerach oraz
`PROGRESS.md`, `docs/milestones/final-audit.md`. Ta sama próba z rozstrzygnięciem
nie wraca do kolejki bez jawnej nowej przyczyny. Planowane powtórzenia A/B do
statystyki należą do jednego eksperymentu, nie są zakazaną duplikacją.
FAIL/timeout zapisuje się jako wynik próby; niekonkluzywny timeout daje DEFERRED,
nie dowodzi, że hipoteza jest błędna. PASS musi wskazywać zakres (micro/medium/
combined); micro PASS nie promuje kodu. Historyczne odrzucone WMMA/TF32/AMS/FEM–BEM
nie są ponawiane pod inną nazwą w tej kampanii.

## Koszt pomiarów i wykonanie

Budować przyrostowo zgodnie z docs/build.md: cache zachować, tylko potrzebne TU,
osobne output dirs i manifesty; nie rebuild całego MFEM/HYPRE bez zmiany dependency.
Koordynator ustala jeden slot build/benchmark na hoście. Rezerwacja musi obejmować
cały pomiar i cleanup; nie polegać wyłącznie na deklaracji agenta, użyć wspólnego
host lock w runnerze po sprawdzeniu jego istniejącego API (wdrożenie M0).

Drabina: replay/micro ≤60 s → tiny smoke ≤120 s → same-mesh assembly-only ≤300 s
→ pełny medium początkowo ≤1200 s; sweep ≤3600 s, zawsze osobny limit total i zasobów.
W M3 koordynator jawnie zatwierdził pełny runner do1800s/case (GPU/OMP1/traceOFF);
to limit dla przygotowanych planów, bez automatycznego wydłużenia lub retry.
To początkowe limity lokalne, nie obietnica czasu. Przekroczenie: zatrzymać własne
zadanie, zapisać fazę i powód; nie automatycznie wydłużać/runować ponownie.
Mały test nie musi generować/rozwiązywać całej anteny. Gdy nie ma gotowego
assembly-only harness, przygotować go jako opt-in test bez zmiany produkcyjnego flow.
Każdy benchmark ma identyczny zestaw outputów; test output on/off to diagnostyka,
nie dowód równoważnego przyspieszenia.

Autor ścieżki przygotowuje patch i proponuje test, główny agent zatwierdza case,
komendy i manifest. Jeden z trzech Sol high w tej kampanii wykonuje już przygotowany run,
czeka i zbiera dowody (nowsze polecenie użytkownika zastępuje tu dawną Lunę).
Wykonawca runu nie zmienia zatwierdzonego projektu solvera. Nie uruchamiać
trzech benchmarków jednocześnie. Strata/inference musi być nieaktywna;
wyłączenie wymaga bieżącej zgody. Zero swap/solver spill na SSD. Cache i zwykły
zapis wyników dozwolone; zmierzyć bajty i unikać sztucznego wielkiego stress-write.
Cloud pozostaje wyłączony. Po badaniu koordynator weryfikuje logi, a nie tylko raport.

## Gotowy prompt dla każdego wykonawcy

Przeczytaj AGENTS, PLAN, MILESTONES, ten workflow i ledger przydzielonej ścieżki.
Sprawdź stan i wcześniejsze próby. Realizuj tylko zadania aktywnego wspólnego etapu
w swoim zakresie i branchu. Najpierw zapisz hipotezę, fingerprint, bramkę i limit.
Nie zmieniaj medium/fizyki/precyzji ani cudzego kodu dla speedupu. Mały test przed
drogim runem. Nie uruchamiaj GPU ani ciężkiego buildu bez slotu koordynatora.
Po każdej próbie zapisz dowody i decyzję w istniejącym ID, także negatywną.
Oddaj mały diff, komendy reprodukcji, wyniki i ograniczenia; bez push.
Nie merguj samodzielnie. Gdy ścieżka nie ma opłacalnej zmiany, zapisz to zamiast
produkować optymalizację na siłę.
