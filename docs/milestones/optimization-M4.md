# M4 — reuse setup i czas życia pomiarów

Status: **COMPLETE — ocena EXP91–94**, 2026-10-20. Bez globalnej zmiany defaultów.
Poprzedni etap: [prefetch](../basis-prefetch.md). Następny: [M5](optimization-M5.md).

## Dowody zamknięcia

- **M4.1:** audyt źródeł wykazał, że na stałej częstotliwości porty zmieniają
  RHS, a A/P i fizyczne terminacje pozostają. Kontrola pełnej anteny ma dwa
  identyczne wewnątrz procesu fingerprinty CSR; kandydat jeden build i reuse.
  Fingerprint FNV to diagnostyka, nie kryptograficzny dowód; wartości między
  osobnymi procesami mogą różnić się przez kolejność sumowania assembly.
- **M4.2:** obecny build, identyczna konfiguracja/mesh i starty, oba porty
  3,50 GHz: 681,698 → 602,944 s, 44/35 iteracji w obu runach. Jedna para:
  −11,55% czasu, bez statystycznej promocji; trzy powtórzenia dopiero w M7.
  Niezależnie przeliczone ||Ax−b||/||b|| ≤8,357e−7. Max Δcomplex S2,367e−8,
  ΔVSWR5,139e−8, Δsumy mocy portów7,078e−9, względna różnica energii1,816e−8.
  Ważone pola E/B ≤2,141e−7/1,783e−8, bez dopasowania fazy, 14 wpisów norm
  (cała domena i sześć regionów dla obu portów). Obecna kontrola również
  porównana z ukończonym EXP93, E/B ≤2,108e−7/1,500e−8.
- **M4.3:** starty oceniono osobno: jawne zero P1, ten sam zweryfikowany seed P2
  z EXP18 w obu ramionach porównania. Brak przypisania zysku reuse do warm start.
  Reuse faktorów między częstotliwościami jest zabroniony przez guard, bo A(f)
  się zmienia. Symbolic reuse między częstotliwościami NOT RUN: obecny shard
  ma jeden f; po usunięciu drugiego setupu jedyna analiza17,35s to najwyżej
  2,88% z602,94s. To dolny priorytet wobec większego working set/apply PC w M5.
- **M4.4:** EXP93 release/rebuild operatorów energii zwalnia15 275 324 488B
  managed na antenie; tiny/medium potwierdzają lifecycle, nie skalę anteny.
  EXP94 pomiary po obu solve i zwolnieniu solvera eliminują nakładanie faktorów
  cuDSS i operatorów energii. Dodatkowy cache tylko pierwszego E:179 499 584B
  w RAM/VRAM, nie na dysku. Peak managed65 353 018 230→53 084 415 322B
  (−18,77%); porównanie stary/nowy postprocess, nie sam efekt reuse.
  Cgroup60 525 092 864→56 829 792 256B (−6,11%) dla kontroli; kandydat
  56 832 888 832B. Managed allocation, cgroup RAM i fizyczny VRAM to różne miary.

## Implementacja i ograniczenia

`--port-setup-reuse`: jedna częstotliwość, jeden rank, fixed mesh, osobne
lumped excitations, restart1, bez wave/Floquet. A2/A/P żyją dłużej niż ksp;
faktory nie są przenoszone między różnymi A(f).

`--defer-postprocessing`: dokładnie dwa porty/jeden f, fixed mesh/rank1/restart1,
bez wizualizacji/wave/Floquet, wymaga `--release-final-solver`. Najpierw solve
obu portów, potem zwykłe pomiary w pierwotnej kolejności. B powstaje z tego
samego Curl i omega. Zachowany RHS norm dla logów; energie/S/fields bez zmian.
`--release-postprocess-energy` usuwa i odtwarza wyłącznie operatory energii;
nie kasuje rozwiązania ani CSV cache. Wszystkie opcje opt-in, audyt w result.json.

W.2: tiny oraz coax-medium3,30/3,55/3,80GHz, oba porty, TEM i ważone pola PASS.
Normalna ścieżka bez defer także tiny PASS. Regresje narzędzi124PASS.
Build EXP94:9,215s, cache istniejących zależności; zachowany fallback
`build/m4-reuse/pre-exp94-native` i starszy `pre-m4-native`.
Limity bez zmian: tiny60s/medium180s/full1800s,60GiB/no swap/hostguard6GiB.

## Artefakty i odrzucenia

- `artifacts/m4-deferred-antenna-{control,on}-20261020/`: obecna pełna para.
- `artifacts/m4-deferred-antenna-root-analysis-20261020.json`: niezależne S,
  VSWR, energia, moc portów, residua i pamięć, porównanie tożsamości wejść.
- `artifacts/m4-deferred-medium-{330,380}-20261020/`,
  `artifacts/m4-deferred-medium-on-20261020/`, `m4-default-tiny-20261020/`.
- EXP92 control OOM podczas P2: FAIL. EXP93 release-only fullcontrol ukończony,
  lecz reuse+inline reference OOM podczas P1 field diagnostics: FAIL, nie powtarzano
  bez nowej hipotezy. EXP94 rozwiązuje nakładanie pamięci, nie zwiększa limitu.
- W.3 to fixture solvera3,50GHz, nie najlepszy projekt produkcyjny anteny.
  W.4/W.5, trzy powtórzenia i końcowy pakiet M7 pozostają NOT RUN.
