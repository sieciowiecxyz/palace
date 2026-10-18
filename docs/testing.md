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
