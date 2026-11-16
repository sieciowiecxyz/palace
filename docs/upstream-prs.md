# Lokalny pilot PR do Palace

Ten dokument zachowuje historyczną procedurę pilota. PR [1087](https://github.com/awslabs/palace/pull/1087)
został scalony 2026-11-16 po poprawkach review. Dawny checkout PR usunięto po
weryfikacji; jego commit zachowuje branch `pr/driven-release-workspace` w
kanonicznym repo. Poniższe stare ścieżki i instrukcje publikacji są archiwalne.

Stan 2026-10-23: fork `sieciowiecxyz/palace` i branch pilota są na GitHubie.
PR do `awslabs/palace` nie został otwarty. Opis PR nadal lokalny.
Badawczy fork zachowany; PR zawiera wyłącznie trzy pliki z czystego upstream.

## Co jest do wysłania

- Worktree: `/home/sieciowiec/dev/cpp/palace-pr-driven-release`.
- Branch: `pr/driven-release-workspace`.
- Lokalny commit: `8b5d4a1f87e7ceb5d4fe5fcacb7849aa17dc54b7`.
- Baza: upstream **main**, `29ad351f916e47e005a43730513f155eeb634e3e`.
- Tytuł: **Release final uniform driven solve state before postprocessing**.
- Pliki: `palace/drivers/drivensolver.cpp`, `test/unit/regression/cases.cpp`, `CHANGELOG.md`.
- Diff:47 dodanych /4 usunięte linie; bez eksperymentalnego adaptera, nowych opcji lub zmiany precyzji.
- Pakiet: `/home/sieciowiec/dev/cpp/palace/artifacts/upstream-pr/` — opis `pr-description.md`, patch `pilot.patch`, manifest `manifest.json`, wejścia, harness i logi. Surowe artefakty są ignorowane przez Git, pozostają na tej maszynie.

Patch skraca życie KSP i macierzy po ostatnim rozwiązaniu, zanim finalny postprocessing
alokuje workspace. Nie przyspiesza samego solvera. W trzech parach kontrolowanego
coax peak RSS spadł **15,82%**, mediana czasu wzrosła **1,34%**. Na tiny two-port
zysk RSS bliski0%; brak pomiaru fizycznego VRAM. Szczegóły i wszystkie ograniczenia:
[M2](milestones/M2.md), praktyki maintainerów: [M3](milestones/M3.md).

Testy upstream CPU/CUDA/MPI przechodzą w wyszczególnionym zakresie. Ścisły ekran
restartu FAIL również dla baseline-vs-baseline; AMR różnicuje siatkę również między
powtórzeniami baseline. Nie ogłaszamy pełnej kwalifikacji tych dwóch diagnostyk.
Pełne CI/MFEM 4.10 i inne urządzenia pozostają do sprawdzenia przed merge.

## Opis dla review — korekta 2026-10-23

Opis `pr-description.md` zaczyna się od przyczyny nakładania pamięci, potem podaje
pomiar i nazwane testy. MB oznacza jednostkę dziesiętną. Zachowano wszystkie FAIL,
timeouty i granice toolchaina. Dodano krótką informację o pomocy Codex; nie deklaruje
ona osobistego review użytkownika. Kod/testy i commit `8b5d4a1f8` pozostają bez zmian;
solvera nie uruchamiano ponownie przy edycji tekstu.

Wskazówki: [Ghostty](https://github.com/ghostty-org/ghostty/blob/main/AI_POLICY.md)
(konkret, ograniczenie rozwlekłości), [LLVM](https://llvm.org/docs/AIToolPolicy.html)
(zrozumienie zmiany i otwarte pytania) oraz
[Palace CONTRIBUTING](https://github.com/awslabs/palace/blob/main/CONTRIBUTING.md)
(mały diff, reproducer i testy). Zasady disclosure Ghostty/LLVM dotyczą tych projektów;
nie zakładamy, że są regulaminem Palace. Notatka i poprzedni opis są lokalnie
w `artifacts/upstream-pr/description-review.md` i `pr-description-before-edit-20261023.md`.

## 1. Sprawdź lokalny commit i diff

```sh
cd /home/sieciowiec/dev/cpp/palace-pr-driven-release
git status --short
git log --oneline 29ad351f916e47e005a43730513f155eeb634e3e..HEAD
git diff --stat 29ad351f916e47e005a43730513f155eeb634e3e..HEAD
git diff --check 29ad351f916e47e005a43730513f155eeb634e3e..HEAD
git diff 29ad351f916e47e005a43730513f155eeb634e3e..HEAD
```

Oczekiwany jeden lokalny commit, tylko trzy powyższe pliki i czysty worktree.
Jeśli później edytujesz kod, obejrzyj również `git diff` i `git diff --cached`;
porównanie BASE..HEAD nie pokazuje zmian niezacommitowanych.
Nie wysyłaj brancha badawczego `codex/local-cuda` ani jego historii.

## 2. Jak odtworzyć testy

Zapisane wykonania: `final-regressions.sh`, `median-validation.sh`,
`amr-control-and-restarts.sh` i logi obok nich. Każdy test ma oddzielny wynik;
kod0 z zewnętrznego skryptu nie zastępuje kontroli raportowanych exit codes.

Zachowany lokalny kontener runtime `palace-pr-test` ma `/work` wskazujące artefakty,
`/src/palace` na worktree PR, GPU CDI, limit12GiB i brak swapu. W razie ponowienia
wybierz nowe katalogi wyników. Poniższe polecenia są instrukcją; nie uruchamiają się
przy czytaniu pliku:

```sh
podman start palace-pr-test
podman exec palace-pr-test sh -c '
  export OMP_NUM_THREADS=1
  export LD_LIBRARY_PATH=/work/candidate-v2:/work/deps:/opt/view/lib:/opt/cudss/lib:/usr/local/cuda/lib64
  timeout -k 5 90 /work/candidate-v2/palace-unit-tests coaxial_lumped_wave --skip-benchmarks --palace-linear-solver SuperLU --regression-run-dir /work/recheck-cpu-$(date +%s)
'
podman exec palace-pr-test sh -c '
  export OMP_NUM_THREADS=1
  export LD_LIBRARY_PATH=/work/candidate-v2:/work/deps:/opt/view/lib:/opt/cudss/lib:/usr/local/cuda/lib64
  timeout -k 5 100 /opt/view/bin/mpirun --timeout 90 -np 2 /work/candidate-v2/palace-unit-tests coaxial_lumped_wave --skip-benchmarks --palace-linear-solver SuperLU --regression-run-dir /work/recheck-mpi2-$(date +%s)
'
podman exec palace-pr-test sh -c '
  export OMP_NUM_THREADS=1
  export LD_LIBRARY_PATH=/work/candidate-v2:/work/deps:/opt/view/lib:/opt/cudss/lib:/usr/local/cuda/lib64
  timeout -k 5 180 /work/candidate-v2/palace-unit-tests cpw_lumped_uniform,coaxial_lumped_wave --device cuda --backend /gpu/cuda/magma --palace-linear-solver cuDSS --skip-benchmarks --regression-run-dir /work/recheck-cuda-$(date +%s)
'
podman stop --time 1 palace-pr-test
```

To odtwarza **zamrożony build**, nie dowolny późniejszy kod. Po zmianach/rebase
przebuduj i przetestuj nowy commit; nie przypisuj starych ELF nowemu diffowi.
Przyrostowy build zachowany w `palace-pr-builder:/opt/palace-cudss-build`:

```sh
podman start palace-pr-builder
podman exec palace-pr-builder cmake --build /opt/palace-cudss-build --target palace unit-tests --parallel 2
podman stop --time 1 palace-pr-builder
```

Po buildzie trzeba skopiować nowy binary, `libpalace.so` i testy do **nowego**
katalogu artefaktów, ustawić jego LD_LIBRARY_PATH i zapisać SHA. Nie nadpisuj
zamrożonych `baseline`/`candidate-v2`. Dane toolchaina: `build-environment.json`.
Kontenery/cache pozostają lokalne; nie trzeba wynajmować GPU ani wysyłać3GB.

## 3. Zanim opublikujesz

Przeczytaj `pr-description.md`, szczególnie wyniki negatywne i granice testów.
Licensing statement pochodzi z template projektu — potwierdź go przy wysyłaniu.
[CONTRIBUTING](https://github.com/awslabs/palace/blob/29ad351f916e47e005a43730513f155eeb634e3e/CONTRIBUTING.md)
wymaga aktualnej bazy i sprawdzenia duplikacji. Po czasie sprawdź ponownie otwarte
PR-y; [#793](https://github.com/awslabs/palace/pull/793) pokazuje, dlaczego mały diff
musi mieć mierzalną korzyść. Nie ma gwarancji merge. Żadnej rozmowy nie rozpoczęto.

## 4. Fork i branch wysłane; PR jeszcze nieotwarty

Na polecenie użytkownika 2026-10-23 utworzono
[fork](https://github.com/sieciowiecxyz/palace) i wysłano tylko
`pr/driven-release-workspace`. `origin` wskazuje ten fork; nie dodawaj go ponownie.
GitHub potwierdza **1 commit, 3 pliki, +47/−4**:
[porównanie](https://github.com/awslabs/palace/compare/main...sieciowiecxyz:pr/driven-release-workspace).
Brancha badawczego nie wysłano. Nie utworzono PR, issue ani komentarza.

Podczas przygotowania upstream main przesunął się do `c3c77f83e` (2 nowe commity,
zmiana tabeli opisów timerów). Pilot pozostaje na przetestowanym commicie `8b5d4a1f8`.
Przed PR sprawdź drift, w razie aktualizacji bazy ponów adekwatne testy i odśwież opis.
Rebase zmieni SHA; stare wyniki opisują pierwotny commit. Nie wykonano rebase ani
force-push. Pełny zapis operacji: `artifacts/upstream-pr/fork-publication.json`.

Gdy branch i wyniki będą zaakceptowane, ręczne otwarcie PR wygląda tak
(polecenie **niewykonane**):

```sh
cd /home/sieciowiec/dev/cpp/palace-pr-driven-release
gh pr create --repo awslabs/palace --base main --head sieciowiecxyz:pr/driven-release-workspace --title 'Release final uniform driven solve state before postprocessing' --body-file /home/sieciowiec/dev/cpp/palace/artifacts/upstream-pr/pr-description.md
```

Reuse RHS, GMRES FP32 storage i mixed-cuDSS pozostają w kolejce
[PLAN](../PLAN.md); każdy wymaga osobnej deduplikacji, brancha i dowodów.
