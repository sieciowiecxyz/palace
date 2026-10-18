# Stan i dowody optymalizacji

Aktualizacja: 2026-10-18. Checkpoint do wznowienia; checklisty są wyłącznie w [PLAN](PLAN.md), kryteria w [MILESTONES](MILESTONES.md).

## Bieżący checkpoint

- Tryb: goal aktywny na polecenie użytkownika; Active: M1.
- Ostatni zamknięty etap: M0, research i migracja lokalnego forka.
- Następny krok: przygotować porównanie całych E/B w fizycznej normie masowej na tym samym mesh anteny, z zachowaniem plików referencji i preflight pamięci; potem jedna para bounded runów benchmarku, bez sweepa. Kontrolny test znanego pola TEM i L2 już wykonano. Audyt i oba krótkie runy opisane w docs/optimization-baseline.md.
- Najlepszy zakwalifikowany wariant całej anteny na nowym forku: **jeszcze nie ustalony**. Istnieje ograniczony coax smoke; historyczne wyniki nie kwalifikują automatycznie aktualnego buildu.
- Otwarte ryzyko: raw residual ~0,125/0,808 przy bliskich S; pełna zgodność pól i niezależne kryterium rozwiązania wymagają wyjaśnienia.
- Sprzęt: plan pod RTX 5070 Ti 16 GB + 96 GB RAM. Jedna karta jest docelowym sprzętem. Multi-GPU poza celem; bez płatnego compute.
- Dodano raw residual, pola/probes, całki L2, audyt siatki i szybszy filtr tiny. Diagnostyka TEM przeszła na obu portach; M1 nadal otwarty, żadnej optymalizacji antenowego solvera jeszcze nie promowano.

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

### EXP-20261018-03 — pole TEM, niezależnie od normy solvera

- Kryteria M1.2/M1.3; wszystkie trzy warianty medium przeszły filtr próbek/energii, patrz raport. FP64 LEFT: RMS E ~0,42%, B ~0,65–0,67%, max punkt B ~1,48%, energie <1,38e−4. Brak jeszcze kwalifikacji L2 całej domeny/anteny.
- Bez rekompilacji: diagnostyczny wycinek 3,55 GHz, oba porty, 18 punktów wewnętrznych (różne z/r/kąt), ten sam mesh/Order/Tol. Najpierw FP64 storage, LEFT, limit 180 s.
- Przed runem: filtr diagnostyczny E/B sample relative RMS ≤1%, maksymalny błąd punktowy ≤2%, energia względnie ≤1e−3. Nie jest to L2 po całej domenie; próg L2 kontraktu pozostaje osobnym wymaganiem.
- Analityczny model TEM z amplitudą incident voltage i znaną geometrią; nie dopasowywać amplitudy/fazy do wyniku. Odbicie/efekty dyskretyzacji raportować jako błąd, nie usuwać fitowaniem.
- Polecenie: python3 tools/dev.py run coax-medium artifacts/m1-tem-fields-left-fp64-20261018 --seconds 180 --basis fp64 --coax-fields --pc-side left .
- Gotowy analizator: tools/coax_fields.py, uruchamiany przez agenta głównego po odbiorze danych. Po odczycie pierwszego wyniku zaplanowano FP32 LEFT oraz FP64 RIGHT: każdy 180 s, te same punkty/mesh/medium. Hipotezy: storage FP32 zachowuje próbki pól; RIGHT wiąże stopping z raw residual i daje porównywalne pola/energię. To diagnostyka M1, nie promocja zmiany domyślnego solvera.

### EXP-20261018-04 — objętościowy L2 pola TEM

- M1.3, tiny PASS; medium20mm FAIL kompletności po deadline. Ponieważ 18 próbek nie kwalifikuje całej domeny, dodano opt-in PALACE_COAX_TEM_DIAGNOSTIC: MFEM ComputeL2Error na wszystkich tetraedrach, real+imag, analityczny TEM bez fitowania, dwie kwadratury stopnia 6/10.
- Przed runem: względne L2 E/B ≤1%, zmiana L2 pomiędzy kwadraturami ≤5e−4 bezwzględnie. Energie i próbki według wcześniejszego filtra. Runtime flag włącza wyłącznie zweryfikowany fixture coax-medium; to nie diagnostyka dowolnej anteny.
- Build przyrostowy po dodaniu nowej diagnostyki: 8,564 s. Bez przebudowy zależności. Najpierw FP64/RIGHT z limitem 180 s, potem FP32/LEFT jeżeli pierwszy ukończy się i diagnostyka będzie poprawna.

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

### Uzupełnienie EXP-20261018-04: skrócenie filtra

Pierwsza pełna całka q6/q10 przerwała limit180s po porcie1 (L2 E~0,4939%, B~0,4561%); cały run FAIL/niekompletny. Nie zwiększono deadline. Wydzielono --coax-l2 z szybkiego --coax-fields i przygotowano osobny analityczny fixture coax-tiny długości2mm, z tą samą poprzeczną geometrią, PTFE, siatką geometry-order2 oraz Order2/Tol1e−6/MaxSize240. Ma filtrować kod, nie zastępować anteny/20mm odniesienia. Plan: L2 q4/q6 na tiny (180s), po wcześniejszej zgodności q6/q10 na ukończonym porcie20mm. Reguły jakości bez zmian.

Tiny FP64 RIGHT ukończył oba porty w18,32s. Całkowite L2 q6: E~0,4953%, B~0,4558%, zmiana q4→q6 ~2e−6; raw residual <1e−6. Nie interpretować tego jako przyspieszenia tej samej anteny: to mniejszy oddzielny filtr. Następna kontrola: tiny FP32 LEFT z takim samym opt-in L2, limit180s. Progi z EXP-04 bez zmian.

### Podsumowanie EXP-20261018-04

- Pełny mały test zakończony: tiny RIGHT/FP64 18,36s i LEFT/FP32 17,33s, L2 E/B <1%, q4→q6 <2,2e−6. Finalny build po korekcie etykiety logu sprawdzony rzeczywistym L2 runem obu portów.
- Szybki tiny smoke: 11,25s, 6/6 rozwiązań; analityczne TEM i zakresy w docs/optimization-baseline.md i artifacts/m1-tem-validation-20261018.json.
- Decyzja: promujemy tiny jako pierwszy filtr developmentu, nie jako zamiennik kwalifikacji anteny. Native L2 zostaje opcjonalne. M1.1/M1.3/M1.4 dla anteny nadal otwarte.
- Najbliższy eksperyment: snapshot/porównanie mass-weighted E/B pomiędzy referencją i kandydatem przy identycznych wejściach, najpierw tiny, potem tylko 3,50GHz/P2 anteny. Bez zmiany precyzji lub fizyki, dopóki nie zadziała kontrola jakości.
