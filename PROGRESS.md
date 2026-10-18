# Stan i dowody optymalizacji

Aktualizacja: 2026-10-18. Checkpoint do wznowienia; checklisty są wyłącznie w [PLAN](PLAN.md), kryteria w [MILESTONES](MILESTONES.md).

## Bieżący checkpoint

- Tryb: goal aktywny na polecenie użytkownika; Active: M1.
- Ostatni zamknięty etap: M0, research i migracja lokalnego forka.
- Następny krok: M1.2/M1.3 — zaprojektować mały test ze znanym polem, rozstrzygnąć niezależną kontrolę rozwiązania i dopiero potem uzupełnić referencję pełnej anteny. Audyt i oba krótkie runy opisane w docs/optimization-baseline.md.
- Najlepszy zakwalifikowany wariant całej anteny na nowym forku: **jeszcze nie ustalony**. Istnieje ograniczony coax smoke; historyczne wyniki nie kwalifikują automatycznie aktualnego buildu.
- Otwarte ryzyko: raw residual ~0,125/0,808 przy bliskich S; pełna zgodność pól i niezależne kryterium rozwiązania wymagają wyjaśnienia.
- Sprzęt: plan pod RTX 5070 Ti 16 GB + 96 GB RAM. Jedna karta jest docelowym sprzętem. Multi-GPU poza celem; bez płatnego compute.
- Dodano diagnostykę raw residual i audyt siatki; wykonano dwa coax smoke po około 34 s. M1 pozostaje otwarty, żadnej optymalizacji solvera jeszcze nie promowano.

## Dowody istniejące przed tym planem

| Dowód | Wynik / zakres | Źródło |
| --- | --- | --- |
| Migracja źródeł, przykłady, cache | Zakończona; pełna antena na nowym buildzie nie była kwalifikowana | [Raport migracji](docs/migration.md) |
| Coax nowego forka | Smoke ukończony, parser poprawiony; zakres TEM/complex S opisany w raporcie | [Walidacja](docs/testing.md), artifacts/coax-migration-fixed-20261018/ |
| Poprzedni eksperyment antenowy | Historycznie 955,176 s FP32 basis vs 1194,812 s FP64 basis na SSD; nie porównanie z resident FP64 | [Wyniki historyczne](docs/local-optimization-results.md) |
| Dotychczasowy research | Hipotezy i źródła, nie dowód nowych przyspieszeń | [Speedup](docs/speedup.md) |

Przed użyciem dowodu sprawdź rewizję, manifest i zakres. Surowe wyniki w ignorowanym artifacts/ mogą być dostępne tylko lokalnie; raport w Git ma zachować liczby i ograniczenia potrzebne do decyzji.

## Rejestr eksperymentów

Wykonano diagnostykę M1 poniżej; nie są to próby nowego solvera ani przyspieszenia. Dodawaj krótkie wpisy w poniższym formacie; osobny raport twórz tylko dla dużego badania i linkuj go tutaj. Udane i nieudane próby są równie istotne.

### EXP-20261018-01 — residuum i FP32/FP64 storage

- Kryteria M1.1/M1.2; PASS wykonania i kontroli portów coaxa, NOT QUALIFIED pola/antena.
- Hipoteza: skompresowana baza sama wywołuje duże raw relative residual. Ten sam mały coax, różni się wyłącznie storage bazy.
- Zapis przed runem: gotowe polecenia do Luny, 180 s deadline, lokalnie, bez pełnej anteny; build i argv zachowane w artefaktach.
- Wynik: oba runy ~33,6 s, 6/6 solve i identyczne liczby iteracji. Raw relative residual jest rzędu 0,02–0,06 również dla FP64; zgodność portów i TEM opisana w [raporcie](docs/optimization-baseline.md).
- Decyzja: odrzucamy kompresję jako jedyną przyczynę na tym coaxie; potrzebny test niezależnego błędu pola. Bez deklaracji rozstrzygnięcia anteny i bez promocji numeryki.

### EXP-20261018-02 — udział powietrza i koszt potencjalnego BEM

- Kryteria M1.4/M1.5, audyt geometrii wykonany; globalne DOF/czas/pamięć wymagają dalszego pomiaru.
- Wynik: AIR 61,71% tetraedrów, PTFE 30,03%; obecny zewnętrzny blok dense complex128 miałby ~11,90 GiB. Dane/hash/ograniczenia w [raporcie](docs/optimization-baseline.md).
- Decyzja: w M2 badać kompresję/FMM i położenie interfejsu, a w FEM koszt drobnej siatki feedu. Nie ekstrapolować oszczędności pamięci z samej objętości powietrza.

### Szablon EXP-YYYYMMDD-NN — krótka hipoteza

- Milestone / kryteria: Mx.y; status PLANNED / RUNNING / PASS / FAIL / NOT RUN / BLOCKED.
- Hipoteza i uzasadnienie: co zmieniamy, jaki profil/źródło ją wspiera; oczekiwany efekt i warunek odrzucenia zapisane przed runem.
- Referencja i kandydat: commit/diff, build/image hash, case/mesh/config hash, porty/frequency, hardware, memory/precision/restart; dokładne argv i limity w artefakcie.
- Dowody: artifacts/<id>/ — manifest, log, telemetry, wynik, porównanie S/pól/residuum; link do małego raportu w Git.
- Wynik: czas faz i całości, RAM/VRAM, iteracje/transfery, max ΔS/ΔVSWR, niezależny błąd rozwiązania/pól; brakujące metryki oznacz NOT MEASURED.
- Interpretacja: obserwacje vs hipotezy, zakres wiarygodności i ograniczenia pomiaru.
- Decyzja: PROMOTE / REJECT / REPEAT WITH CHANGE / BLOCKED; wybrany wariant i konkretny następny krok. PASS techniczny nie oznacza automatycznie PROMOTE.

## Trwałe decyzje

- 2026-10-18: sekwencja M1–M7 z bramkami; medium i fizyka pozostają częścią kontraktu. Najpierw referencja/residuum, potem pamięć GMRES. Research techniczny i projektowanie prowadzi agent główny; uruchamianie/oczekiwanie/odbiór gotowych symulacji delegowane tej samej GPT-6 Luna high.
- 2026-10-18: C++/CUDA w obecnym Palace/MFEM/libCEED; Python stdlib do narzędzi. Rust tylko po odrębnym uzasadnieniu. FEM–BEM/MoM stały się obowiązkowym kierunkiem M2 po korekcie celu przez użytkownika. Nowy FP32 cuDSS wymaga nowej hipotezy; nie powtarzać znanej porażki.

- 2026-10-18, korekta celu: zastąpiono obowiązkowe multi-GPU przez research/prototyp Maxwell FEM–BEM/MoM. Główny cel: pamięć i czas na jednej 5070 Ti przy kontrolowanej jakości; zakończona ocena nowej metody wymagana, integracja tylko po wykazaniu przewagi.
