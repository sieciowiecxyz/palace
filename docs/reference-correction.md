# M1: próby niezależnej kontroli referencji

2026-10-18. Status: **otwarta jakość pełnej anteny**. EXP13/14 nie zamykają
M1.2/M1.3. Medium przestrzenne, materiały i mesh pozostają bez zmian.

## Wznowienie i kontrolowane parametry

- `--initial-fields <completed-run>` sprawdza fizykę/mesh/zależności,
  SHA/header/coverage snapshotów oraz ukończenie wejściowego runu.
  Montuje pola read-only i ustawia `Linear.InitialGuess=true`.
  Native czyta E raz przed każdym solve, przelicza local grid function
  na true DOF i wymaga jednego ranka. Potwierdzenie: `PALACE_FIELD_RESTART`.
  Wejściowy wynik jest przybliżeniem startowym, nie certyfikatem dokładności.
- `--krylov-size 1..240` jawnie zmienia restart GMRES w kopii konfiguracji.
  Nie zmienia zamrożonego fixture. Mniejsza baza oszczędza pamięć, ale może
  pogarszać zbieżność. Żaden nowy default nie jest promowany.
- `--linear-tol` jest tylko ostrzejszą diagnostyką referencji:
  zakres od1e−14 do tolerancji fixture, bez NaN/inf/bool i bez osłabiania
  kryterium. Zmienia solver, nie siatkę/Order/PA ani równanie.
- Przy początkowym E już spełniającym tolerancję GMRES raportuje również
  zerowe iteracje i stopping check. Weryfikowany FP64 solve reaguje teraz
  także reliable restartem na rozbieżność recurrence i ponownego zastosowania
  operatora. Bez weryfikacji zwykła ścieżka FP64 pozostaje bez zmian.
- Baza, macierze i workspace pozostają RAM/VRAM. Snapshot jest zwykłym
  wejściem/wyjściem; nie ma disk basis, mmap, scratch ani swap.

Przykład krótkiego filtra (wymaga istniejących, zweryfikowanych snapshotów):

```sh
python3 tools/dev.py run coax-tiny artifacts/new-reference-check --seconds 120 --basis fp64 --hypre-pool-mib 256 --release-gmres-basis --memory-marks --pc-side left --krylov-size 96 --linear-tol 1e-12 --initial-fields artifacts/m1-gmres-release-tiny-r3-20261018 --field-reference artifacts/m1-restart-right-tiny-20261018 --save-fields
```

## Wyniki i granice

| Próba | Wynik | Dowód |
| --- | --- | --- |
| LEFT replay, tiny, Tol1e−6 | PASS, 6×0iter, dokładnie te same pola, 10,562 s; raw do8,7e−3 nadal za duże | `artifacts/m1-restart-left-tiny-20261018/` |
| RIGHT/K64 warm, tiny | PASS, 37–41iter, 12,468 s, raw≤9,781e−7 | `artifacts/m1-restart-right-tiny-20261018/` |
| RIGHT/K64 warm, antena | **FAIL/deadline1800 s**; bez pełnego S, pól i finalnego raw; cgroup43,69 GiB | `artifacts/m1-antenna-right-correction-20261018/` |
| LEFT/K96/Tol1e−12 warm, tiny | PASS, 71–74iter, 15,553 s, raw≤8,990e−9 | `artifacts/m1-restart-left-tight-tiny-20261018/` |
| LEFT/K128/Tol1e−12 warm, antena | **FAIL/deadline1800 s**; bez pełnego S/pól/finalnego raw; cgroup53,94 GiB | `artifacts/m1-antenna-left-tight-correction-20261018/` |

W RIGHT tiny względem wcześniejszego LEFT:
max |ΔS|9,947e−6, ΔVSWR3,282e−6, zmiana sumy znormalizowanych mocy
portów6,958e−6, względna energia1,750e−4; ważone E≤9,368e−6,
B≤0,003112 (0,311%). Wszystkie zamrożone progi małego filtra spełnione.

Ostrzejszy LEFT tiny względem RIGHT tiny:
max |ΔS|2,469e−8, ΔVSWR3,179e−8, względna energia1,293e−7;
ważone E≤2,238e−7, B≤3,375e−7. Dwa sposoby preconditioningu zgadzają się
na tym małym przypadku i mają małe raw. To nie dowód jakości dużej anteny.

Pełne próby nie miały OOM ani RAM guard. Pole `field_accuracy_passed=false`
przy pustym porównaniu oznacza brak ukończonej kontroli, nie zmierzony błąd
pól >1%. Nie porównywać ich czasów z ukończoną referencją jako speedup.

Oba stare timeouty mają ostatnią częściową linię iteracji140.
**Rzeczywista końcowa iteracja jest nieznana**, ponieważ stdout był
buforowany. Ostatnia pełna linia139 pokazuje tylko dawny widoczny stan:
RIGHT recurrence≈0,37005; LEFT tight≈9,78791e−4. To nie finalne,
niezależnie przeliczone residua. Nie wyliczać iteracji/s z tych danych.

## Wiarygodność bieżących logów

Lokalny runner jawnie ustawia `PALACE_LINE_BUFFERED_LOG=1`.
`main` włącza line buffering stdout przed MPI i emituje
`PALACE_LOG_BUFFERING: stdout=line`; runner wymaga potwierdzenia.
Oddzielne stdout/stderr nadal zapobiegają przecinaniu diagnostyki.
Końcowy `palace.log` nadal jest konkatenacją, nie wspólną chronologią.

Historyczny replay build8,298 s; wówczas 25 unittestów PASS. Bieżący
checkpoint raportuje 33 unittesty narzędzi PASS. Replay
`artifacts/m1-line-buffered-replay-tiny-20261018/`: complete=true,
11,437 s, sześć zerowych iteracji i pełne checks/coverage/porównania pól.
Potwierdza nowe logowanie i wznowienie; nie ustanawia nowego benchmarku anteny.

## Decyzja

Nie zmniejszać progu raw1e−6, aby zaliczyć próbę. EXP12 pozostaje historyczną
referencją wykonania, nie dokładności (raw≈0,125). Późniejszy W.3 native
complex coarse wyznaczył resident FP64 RIGHT referencję Tol1e−9 i osobny
medium run przeszedł bramki numeryczne przy tej samej geometrii i siatce;
szczegóły są w [raporcie native complex coarse](native-complex-coarse.md).
To nie zamyka M1: profilowanie kerneli/UVM, pamięć i szersza kwalifikacja
anteny nadal są otwarte.

Historyczne profile CPU/cuDSS, dokładnego real-block coarse solve i zwalniania
finalnego solvera są w [reference-profiles.md](reference-profiles.md).
CPU full replay zakończył się OOM; real-block full zatrzymał host guard.
Nowszy W.3 native complex coarse przeszedł dla jednego punktu anteny, ale
nie kwalifikuje innych częstotliwości, obudowy ani prototypu i nie zmienia
domyślnego solvera. Nie pomijać wymaganej ścieżki M2 FEM–BEM ani nie promować
TF32/FP32/BF16 na podstawie małych przypadków.
