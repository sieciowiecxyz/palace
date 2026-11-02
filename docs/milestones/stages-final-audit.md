# M6 — audyt i rekomendacja profilu

Stan: COMPLETE_SCOPED — niezależny przegląd PASS. Cel dotyczy optymalizacji przygotowania medium na jednej
5070 Ti, a nie kwalifikacji wszystkich funkcji Palace lub projektu anteny do produkcji.

## Rozliczenie bramek

| Wymagania | Wynik i dowody |
|---|---|
| M0.1–M0.4 | PASS zakresowo: źródła/native/obraz/wejścia, tiny i diagnostyki, ograniczenia pamięci/czasu/LLM. `M0.md`, workflow, per-run plany. |
| M1.1–M1.3 | Profilowanie i wybór PASS. Pokrycie99,80%; ON/OFF narzut+0,0385% w jednej parze, nie gwarancja statystyczna. GSLIBSetup104,52s głównym kosztem. |
| M2.1–M2.2 | PRE/OP PASS do kwalifikacji. 55 986 i749 asercji, krzywe elementy, akcja operatora, fallback i invalidation; syntetyczne pola CUDA~1e-13. |
| M2.3 | IO-06 DEFER: strict readback PASS, konwersja34,049s, zwrot od~22 identycznych wczytań; cache nie został wdrożony. |
| M2.4 | Oddzielne branche i cache. Tylko zakwalifikowane OP/PRE w integracji, bez zmiany zależności ani medium. |
| M3.1–M3.3 | Testy małe i po trzy pary OP/PRE PASS. Residuum, zespolone S, VSWR, próbki E/B, FF i moc w progach. PRE:3nativepary,2cleanwall; osobny dowód odzysku po błędzie monitora. |
| M3.4 | Pamięć/czasy rozdzielone: cgroup, globalne GPU, logiczne UVM. Fizyczne migracje i rezydencja VRAM NOT RUN. Nie twierdzić o redukcji fizycznego VRAM. |
| M4.1–M4.2 | PASS zakresowo: scalone patche, źródła95822, build8,43s bez dependency rebuild; bazowy/combined/OP-only RF PASS. |
| M5.1 | PASS:3pary całego medium1,92GHz/oba porty, mediana738,280→630,324s; RAM66,056→57,029GiB. Wszystkie próbki uwzględnione. |
| M5.2 | RF PASS1,71/2,69/3,80GHz i inna geometria. CSVreadback i guardy konfiguracji PASS. Restart sprawdzony: FAIL odziedziczonego CSV, nie regression OP/PRE. Kwalifikacja ograniczona do wcześniej zdefiniowanego Restart1. |
| M5.3 | CPU/MPI2 fallback PASS, nativeexit0. Inne GPU i wydajność wielu GPU NOT RUN. |
| M6.1 | Ledgery i negatywne wyniki zachowane; decyzje OP/PRE promować do profilu, IO cache DEFER, legacy restart poza kwalifikacją. |
| M6.2 | Źródła scalone lokalnie, ten sam hash co build; manifest profilu i poniższe komendy, rollback i niezależny przegląd PASS; lokalny commit zamykający zawiera ten dokument. |

Pełna macierz22numerowanych punktów i14niezależnych replayów znajduje się w
`artifacts/optimization-stages/M6-final-audit-20261030/full-audit.json`.
Podsumowanie liczb i ograniczeń: [wyniki](../optimization-stages/results.md).

## Build i profil

- Native: `build/optimization-stages-m4-integration-20261030/native/` (trzy pliki;
  nie kopiować samego executable bez biblioteki i adaptera).
- Source SHA: `95822ec5a0874bf0ede47c8725aa278192440ef20af7f1cd59a6416eebb67ed5`.
- Biblioteka: `048fbfc26f723813ac64dbb8af4f170009cab706c2e165445b510b782583da84`.
- Pinned runtime: `43ac46f6430cf44d7a2da0a618a0f5c67c6965cca2fde510f2a96116333e6d76`.
- Kandydat do zatwierdzenia: `build/optimization-stages-m4-integration-20261030/qualification-candidate.json`.
  Po przeglądzie root zapisał nowy `scopedqualification.json` w tym samym katalogu.
  Oryginalny manifest buildu pozostaje niezmieniony i ma `numerically_validated=false`;
  sidecar potwierdza wyłącznie konkretny profil20flag, oba porty, Restart1 i testowane przypadki.
- Nowe flagi: `PALACE_PROBE_LOCATOR=mfem`, `PALACE_SINGLE_RANK_DIRECT_MESH=1`.
  Pozostałe18flag oraz precyzje są przypięte w sidecar. Zmiana modelu/flag wymaga własnej referencji.
  Każdy kwalifikowany run miał jeden jawny Point; testy kilku częstotliwości to
  osobne runy. Ten profil nie kwalifikuje wieloczęstotliwościowego batch ani warm startu.

## Odtworzenie uruchomienia

Z katalogu `/home/sieciowiec/dev/cpp/palace`, przy wyłączonym serwerze inference:

```sh
python tools/stage_probe_run.py prepare \
  --source "$PWD/../palace-opt-integration" \
  --build "$PWD/build/optimization-stages-m4-integration-20261030" \
  --run "$PWD/artifacts/optimization-stages/M5-inputs-20261030/freq-1710" \
  --output "$PWD/artifacts/my-new-run" \
  --driver-record "$PWD/build/optimization-stages-m0-20261030/driver-injection/host-driver.json" \
  --stage full --seconds 1800 --memory-gib 70 --threads 1 \
  --probe-locator mfem --direct-mesh 1
python tools/stage_probe_run.py execute "$PWD/artifacts/my-new-run/plan.json"
```

Przygotowanie nie liczy symulacji; execute wymaga wolnego GPU/pamięci i wyłączonej
Straty. Używać świeżego output. Aktualizacja sterownika unieważnia stary driver record;
nie omijać walidacji. Przykład przygotowania z aktualnego root został sprawdzony bez
ponawiania pełnej symulacji: `M6-final-audit-20261030/recommended-run-prepared-only/`.

Rollback: nowy plan z `--probe-locator gslib --direct-mesh 0`, ta sama binarka.
Pełny poprzedni pakiet pozostaje w `artifacts/m7-sm120-bundle-r3-20261022/`.
Nie nadpisywać zakończonych planów, przerwanego2690B ani dowodów recovery.

## Znane ograniczenie CSV restartu

Natywny tiny A(gslib/direct0) ukończył6solves, lecz Restart2 po legalnym checkpoint
prefix zawiódł przy lookup `idx`. Insert/lookup/reload/PrintDomainE są identyczne
z frozen a6: mapa nazw nie jest odświeżana po rename. Bez fixu produktu, bez retry,
Bsmoke NOT RUN. Raport: `M5-restart-smoke-20261030/failure-analysis.json` i
`M6-final-audit-20261030/restart-source-review.json`.

Nie kwalifikujemy Restart>1 ani restartu volumetric snapshots. Wrapper odrzuca
Restart!=1 od czasu sprzed tej próby. Profile reuse/defer również wymagają Restart1;
nie rozszerzać ich na restart przez obchodzenie guardów. To pozostawiony jawnie
błąd bazowej ścieżki, a nie poluzowany próg RF czy poprawiony wynik eksperymentu.

Końcowe rozliczenie22punktów: `M6-final-audit-20261030/final-audit.json`.
Nie ma nierozstrzygniętego eksperymentu tej kampanii; jawny legacyCSVbug pozostaje
poza kwalifikowanym profilem. Nie wysyłano kodu ani wiadomości na GitHub.

Po dodaniu opcjonalnego OpenMP do głównego kodu, źródła source95822 pozostały
w worktree `palace-opt-integration`. Stąd powyższe `--source` wskazuje snapshot,
nie aktualny root. Przykład zapisany w M6 powstał przed tą zmianą; dawnych planów
z `source=root` nie wykonywać ponownie po zmianie źródeł. Nową opcję opisuje
[OpenMP](../probe-openmp.md); jej build/zakres walidacji są osobne.

## Explicit mixed-coarse admission (2026-11-02)

The prepared runner accepts `--native-coarse-fp32` with an explicit fixed
FP64-correction count of `2` or `3`; when the correction option is omitted,
the opt-in defaults to `2`. Both feature flags must be paired. The default
FP64-coarse profile is unchanged. This exposes the already compiled solver
path without rebuilding dependencies or changing FEM physics.

The runner admits mixed coarse only for a full CUDA run with the explicit
native-complex baseline. Completion requires log evidence of complex-FP32
coarse factors and the requested number of original-FP64 corrections, a
finite relative coarse residual no greater than `1e-3`, and the independent
outer raw-residual gate no greater than `1e-6`. Partial/CPU runs, unpaired
flags, unsupported correction counts, or missing/mismatched execution markers
fail.

Tiny agreement does not qualify a larger antenna: the current C20 cases fail
this coarse gate. Keep campaign evidence in the antenna workspace's
`docs/research/ap06-local-memory.md`; these controls do not promote that profile.
Do not relax either residual gate or increase the count without a separate
reviewed experiment.
