# Walidacja lokalnego forka

Wykonuj z katalogu głównego repo. Narzędzia wymagają Linux i Python 3.11+; upstream ma szersze platformy, ale lokalny runner nie został na nie przeniesiony.

## Szybkie kontrole

```sh
python3 -m unittest discover -s tools/tests -p 'test_*.py' -v
sh .agents/skills/docs-garden/scripts/test.sh
sh .agents/skills/docs-garden/scripts/check.sh
git diff --check
```

Testy narzędzi mają wykrywać uszkodzoną siatkę/konfigurację, niekompletny wynik, stale binaries i błędy cache. Nie są testem matematyki FEM.

## Rzeczywisty build i cache

```sh
python3 tools/dev.py build --jobs 8
python3 tools/dev.py build --jobs 8
```

Drugi build powinien pozostawić bez zmian hashe binariów i ominąć kompilację niezmienionych jednostek. Sprawdzić log/manifest, nie tylko czas. Oddzielny test cache kompilatora polega na odbudowie jednego własnego obiektu przy zachowanym ccache; nie kasować całego cache ani zależności.

## Smoke GPU

```sh
python3 tools/dev.py run coax-medium artifacts/coax-smoke --seconds 180
```

Oczekiwane: exit 0, sześć ukończonych rozwiązań (3,3/3,55/3,8 GHz, dwa porty), prawidłowe sumy wejść, `result.json: complete=true`, niezależne kontrole norm zatrzymania. Osobno porównać S21 do TEM oraz S do zapisanej referencji. Sam status complete nie kwalifikuje dokładności.

Pierwszy smoke migracyjny z 2026-10-18 ukończył sześć rozwiązań, ale runner zapisał `complete=false`, ponieważ regex nie akceptował dwukropka po `PALACE_KSP_CHECK`. Parser poprawiono i dodano regresję z dokładnym formatem emitowanym przez Palace. Powtórzenie w `artifacts/coax-migration-fixed-20261018/` zwróciło `complete=true`, sześć kontroli norm względnych i exit 0. Szczegóły pierwszego błędu, naprawy oraz porównania TEM/S są w [raporcie migracji](migration.md). To kwalifikuje ograniczony coax smoke, nie pełną antenę ani multi-GPU.

## Pełny przykład i testy upstream

Pełny case `tshaped-medium`: 3,50 GHz/P2, P1 zakończony 50 Ω, ten sam mesh medium. Jego wykonanie kosztuje około kilkunastu minut na docelowym komputerze; nie uruchamiać przy każdej zmianie dokumentacji. Po zmianie numeryki stosować bramki z [planu](speedup.md).

Zachowane testy C++/regresje upstream są w `test/` i opisane w dokumentacji upstream. Nie twierdzić, że cała ich kampania przeszła na podstawie lokalnych testów narzędzi lub smoke. Testy wymagające drugiego GPU oznaczać NOT RUN, jeśli go brak.

## Diagnostyka M1

PALACE_VERIFY_RESIDUAL emituje także PALACE_RAW_RESIDUAL: niezależne ponowne zastosowanie A w bieżącej precyzji, normy b/Ax/b−Ax i dwa ilorazy. Dodatkowy matvec i redukcje są kosztem diagnostyki. Norma relative_action nie jest normwise backward error, a status complete nadal oznacza tylko kompletność. Rezultaty nowych coax smoke FP32/FP64 storage i audyt geometrii: [raport M1](optimization-baseline.md). Nie rozstrzygają zgodności pól całej anteny.

Audyt siatki: `python3 tools/mesh_cost.py examples/tshaped-medium/mesh/pcb.msh --output artifacts/mesh-cost.json`. Regresje sprawdzają różnicę udziału elementów/objętości, zamkniętą powierzchnię i odrzucenie nieobsługiwanych danych. Metoda używa geometrii narożników, nie dokładnej kwadratury zakrzywionych elementów.

## Filtr pola TEM i L2

Pierwszy szybki test: `python3 tools/dev.py run coax-tiny artifacts/tiny-smoke --seconds 60`. Większy coax i antena pozostają odrębnymi poziomami drabiny walidacji. Dla pola: --coax-fields, dla całości domeny: --coax-l2; analizator tools/coax_fields.py porównuje do analitycznego TEM, próbki nie są mylone z całką L2. Dane diagnostyczne nie kwalifikują dowolnego modelu anteny.

L2 pochodzi z MFEM ComputeL2Error, oddzielne real/imag, dwie kwadratury4/6. Testy parsera używają faktycznych jednostek CSV Wb/m² i sprawdzają, że błędny znak B/NaN nie przechodzą niezauważone. Diagnostyka CPU ma osobne czasy i nie jest włączona w rutynowym pomiarze szybkości.

Pierwszy 20 mm run q6/10 nie zmieścił się w 180 s i pozostaje FAIL, chociaż jeden port dał użyteczne L2. Pełne tiny runy spełniły z góry ustalony filtr. Dokładne wyniki: [M1](optimization-baseline.md). Według bieżącego checkpointu 25 unittestów narzędzi PASS; pełna kampania testów C++ upstream nadal NOT RUN.

## Snapshoty i porównanie masowe

Regresje snapshotów pokrywają SHA/format/nieukończone referencje, inną fizykę i pokrycie regionów oraz NaN/duplikaty. Rzeczywiste tiny testy: snapshot FP64→FP32, historyczne porównanie disk→resident (storage disk jest wycofany), domyślny background worker i kontrolowane B×1,02 (oczekiwany FAIL jakości). Native pliki E/B single-rank little-endian są chronione sprawdzaniem źródłowego config i zależności. Szczegóły: [kontrola pól](field-validation.md).

Historyczne referencje/porównania dużej anteny z disk basis są **REJECT** według wymogu RAM/VRAM. Wcześniejszy resident FP32 attempt zatrzymał guard. Resident FP64 EXP12 ukończył jeden punkt i zapisał snapshoty, lecz raw relative residual wyniósł około 0,1253 i nie ma niezależnej referencji pól. Dwie późniejsze korekty full antenna EXP13/14 zakończyły się limitem 1800 s: brak kompletnego solve, S i kontroli pól. Ich niepełne `field-comparison.json` oznaczają brak pomiaru błędu, nie przekroczenie progu. Ostatni log z buforowanych runów nie potwierdza faktycznej końcowej iteracji; widoczna niepełna linia 140 nie jest licznikiem iteracji. Line-buffered replay na tiny przeszedł, ale nie jest wynikiem anteny. Nie zgłaszać zielonej kampanii ani promocji precyzji. Fazy mierzą logiczne managed allocations, nie fizyczną rezydencję. M1 pozostaje otwarty; szczegóły [audytu pamięci](memory-audit.md), [pomiaru faz](memory-phases.md) i [korekty referencji](reference-correction.md).

## Analiza alokacji bez GPU

`tools/allocation_audit.py` czyta zachowany trace ≥16MiB; nie uruchamia solvera. Regresje w tools/tests/test_allocation_audit.py obejmują peak w tej samej chwili, pointer reuse, przypisanie późniejszych ramek stosu, interleaved stdout oraz odrzucanie uszkodzonego/starego formatu. Reprodukcja i ograniczenia: [audyt pamięci](memory-audit.md).

## Eksperymentalne Q-workspace

Probe dwóch operatorów i późniejszy pełny coax-tiny/TEML2 przeszły; Q-pool nie jest promowany z powodu braku oszczędności na tiny. Pierwszy baseline zakończony OOM/hostguard pozostaje FAIL. Regresje Pythona sprawdzają preflight RAM, sourceSHA, stale/tampered manifest, granice HYPREseed i jednostki/filtrowaniePID w pomiarze GPU. Odtworzenie oraz scope: [Q-pool](ceed-qpool.md), [pula HYPRE](hypre-pool.md). Nowa pełna antena FP64 jest wyłącznie resident execution reference; antena z Q-pool ani kandydat mixed precision pozostają NOT RUN.
