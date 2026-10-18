# Stan i dowody optymalizacji

Aktualizacja: 2026-10-18. Checkpoint do wznowienia; checklisty są wyłącznie w [PLAN](PLAN.md), kryteria w [MILESTONES](MILESTONES.md).

## Bieżący checkpoint

- Tryb: planowanie zakończone, badania nieuruchomione; Active: none.
- Ostatni zamknięty etap: M0, research i migracja lokalnego forka.
- Następny krok po rozpoczęciu pracy: M1.1 — sprawdzić Git/build manifesty oraz przykłady i ustalić dokładne wejścia referencji. Następnie prześledzić Ax−b/scaling/LEFT preconditioning w kodzie dla M1.2, przed obniżaniem precyzji.
- Najlepszy zakwalifikowany wariant całej anteny na nowym forku: **jeszcze nie ustalony**. Istnieje ograniczony coax smoke; historyczne wyniki nie kwalifikują automatycznie aktualnego buildu.
- Otwarte ryzyko: raw residual ~0,125/0,808 przy bliskich S; pełna zgodność pól i niezależne kryterium rozwiązania wymagają wyjaśnienia.
- Sprzęt: plan pod RTX 5070 Ti 16 GB + 96 GB RAM. Dostępność drugiego GPU i budżet chmury sprawdzić dopiero przed M6; niczego teraz nie wynajęto.
- W tej zmianie: wyłącznie dokumenty workflow. Nowe pomiary wydajności i symulacje: NOT RUN.

## Dowody istniejące przed tym planem

| Dowód | Wynik / zakres | Źródło |
| --- | --- | --- |
| Migracja źródeł, przykłady, cache | Zakończona; pełna antena na nowym buildzie nie była kwalifikowana | [Raport migracji](docs/migration.md) |
| Coax nowego forka | Smoke ukończony, parser poprawiony; zakres TEM/complex S opisany w raporcie | [Walidacja](docs/testing.md), artifacts/coax-migration-fixed-20261018/ |
| Poprzedni eksperyment antenowy | Historycznie 955,176 s FP32 basis vs 1194,812 s FP64 basis na SSD; nie porównanie z resident FP64 | [Wyniki historyczne](docs/local-optimization-results.md) |
| Dotychczasowy research | Hipotezy i źródła, nie dowód nowych przyspieszeń | [Speedup](docs/speedup.md) |

Przed użyciem dowodu sprawdź rewizję, manifest i zakres. Surowe wyniki w ignorowanym artifacts/ mogą być dostępne tylko lokalnie; raport w Git ma zachować liczby i ograniczenia potrzebne do decyzji.

## Rejestr eksperymentów

Nowych eksperymentów optymalizacyjnych w tym workflow jeszcze nie ma. Dodawaj krótkie wpisy w poniższym formacie; osobny raport twórz tylko dla dużego badania i linkuj go tutaj. Udane i nieudane próby są równie istotne.

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
- 2026-10-18: C++/CUDA w obecnym Palace/MFEM/libCEED; Python stdlib do narzędzi. Rust i FEM–BEM tylko po odrębnym uzasadnieniu. Nowy FP32 cuDSS wymaga nowej hipotezy; nie powtarzać znanej porażki.
