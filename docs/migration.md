# Pochodzenie i stan migracji

Fork przeniesiono z lokalnego środowiska `anteny` do `~/dev/cpp/palace`, zachowując historię Git i licencje Palace. Bazowy Palace: `0fb92e08e6c8c28488c393cef3f738c4b5e8c4bc`. Własne zmiany są w źródłach, nie należy nakładać patchy ponownie.

Zaimportowano pięć zestawów zmian z ukończonego badania: phase trace, fixed-mesh estimator opt-out, skompresowana baza, reliable stopping check i baza FP64 na SSD. SHA plików importu i patchy zachowuje `tools/import.json`. Adapter UVM/cuDSS przeniesiono do `tools/adapter`.

Repo antenowe i jego dirty changes pozostawiono nietknięte. Pełne stare logi/profil Nsight zostają tam w artefaktach; nowe repo ma samodzielne wejścia dwóch fixtures i historyczny raport. Dokument speedup przeniesiono jako plan, a zawarte w nim ścieżki `infra/palace` odnoszą się do repo sprzed migracji; aktualne komendy są w `docs/build.md`.

Instrukcje dostosowano do prywatnego `sieciowiecxyz/vibecoding`; jego rewizja jest w `tools/import.json`. Zachowano skill docs-garden i jego skrypty. Root AGENTS jest instrukcją dla tego forka, a nie kopią zasad projektu antenowego.

Migracja nie dodaje Tensor Cores, nowych solverów BEM ani kwalifikacji multi-GPU. Obecny cel optymalizacji i nierozwiązane kwestie numeryczne zachowuje [speedup](speedup.md). Nowe wykonanie i cache sprawdzono na nowej lokalizacji, jak opisano poniżej; wyników historycznych nie zalicza się jako testu migracji.

## Kontrola coax medium z nowego repo — 2026-10-18

Pierwsze uruchomienie `python3 tools/dev.py run coax-medium artifacts/coax-migration-20261018 --seconds 180` zakończyło proces Palace z exit 0 po 33,58 s. Sześć rozwiązań dla 3,30/3,55/3,80 GHz i obu portów zbiegło, lecz `result.json` zapisał `complete=false` i pustą listę kontroli. Powodem był parser `tools/dev.py`, który oczekiwał prefiksu `PALACE_KSP_CHECK ` bez dwukropka, podczas gdy solver emituje `PALACE_KSP_CHECK:`.

Parser poprawiono, dodając też test regresyjny dla rzeczywistego prefiksu. Dokładne powtórzenie w `artifacts/coax-migration-fixed-20261018/` zakończyło się exit 0 po 33,68 s, `complete=true`, sześcioma solve’ami i sześcioma kontrolami względnej normy 8,21e-7–9,78e-7; bez OOM i przerwania. Historia pierwszego błędnego statusu została zachowana w `artifacts/coax-migration-20261018/`.

Osobna kontrola w `artifacts/migration-validation.json` raportuje maksymalny błąd analitycznego TEM 1,871285e-4 i maksymalną deltę zespolonego S równą 3,36394e-9 wobec historycznego, zakwalifikowanego coax smoke; te progi przeszły. Ograniczony coax smoke na zmigrowanym buildzie jest PASS. Później ukończono też jeden resident FP64 run pełnej anteny w tym repo: execution PASS, lecz niezależna jakość anteny pozostaje otwarta; szczegóły są w [raporcie faz](memory-phases.md). Multi-GPU i symulacja z nowego spakowanego obrazu pozostają NOT RUN. Dane coax smoke nie kwalifikują pełnej anteny ani produkcyjnej fizyki.

## Build, cache i pakowanie

PASS: ponowny build/export 2,758 s, odbudowa jednego usuniętego obiektu z trafieniem ccache 1,975 s, kolejny no-op 1,572 s. To czas faz build/export, bez zatrzymywania kontenera; pierwszy cold build nie został zmierzony. Zależności MFEM/libCEED/hypre pozostały zachowane. Pliki i historie: `build/sm120/manifest.json`, `build.log`, `history/`.

PASS: `localhost/palace:fork-sm120-20261018`, ID `8d4dfc4e7bb05ee426b6a80c4c11492b784d20684ef8b7a5c1df77650291b994`. Hashe programu, libpalace i adaptera sprawdzono wewnątrz obrazu względem manifestu. Smoke korzystał z tych samych plików natywnych montowanych do bazowego runtime; osobnej symulacji uruchomionej z nowego spakowanego obrazu nie wykonano.

PASS: 6 testów narzędzi, 8 testów audytu shell, docs-garden wykonany przez GPT-6 Luna high oraz rootowy przegląd. Pełna kampania testów C++ upstream i zdalne CI: NOT RUN.

Repo zachowuje historię upstream i gałąź `codex/local-cuda`. Remote `upstream` wskazuje awslabs/palace; osobnego `origin` jeszcze nie utworzono i nie wysyłano zmian do upstream. Aktywne CI to lekki read-only `local-docs.yml`; oryginalne workflowy są zachowane w `.github/upstream-workflows/` i nie uruchamiają automatycznych buildów, publikacji ani cleanupów w tym forku.
