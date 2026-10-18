# Porównanie całych pól na tej samej siatce

Czytaj przed kwalifikacją zmiany precyzji lub pamięci. Test dotyczy różnicy wyniku numerycznego względem jawnej referencji medium, nie fizycznej poprawności anteny ani zbieżności siatki.

## Szybka ścieżka

```sh
python3 tools/dev.py run coax-tiny artifacts/ref --seconds 60 --basis fp64 --save-fields
python3 tools/dev.py run coax-tiny artifacts/candidate --seconds 60 --basis fp32 --save-fields --field-reference artifacts/ref
```

Domyślne runy nie zapisują pól ani nie wykonują porównania. --save-fields zapisuje FP64 real/imag grid functions E/B (nie samych true DOF w innym układzie). --field-reference odczytuje referencję przez mount read-only, bez zmiany rozwiązania; --save-fields można połączyć z porównaniem. Koszt I/O i norm jest jawnie mierzony, wyłączyć diagnostykę w zwykłym benchmarku finalisty i raportować jej koszt osobno.

## Kontrakt zgodności

fields.json powstaje tylko po ukończonym runie i zawiera SHA wszystkich plików oraz identity. Przed GPU sprawdzane są: ukończenie źródła, rzeczywisty config źródła/command hash, mesh/fizyka/materiały/porty/samples/Order/PA i przypięte builder/runtime. Pliki muszą mieć poprawny nagłówek PALF64V1, liczbę DOF, długość, SHA i pełne pokrycie excitation×frequency×E/B. Zmienione bajty/inny mesh lub niedokończona referencja są odrzucane.

Identity pozwala jawnie porównywać Linear/precision/backend/device i diagnostyczne postprocessing; te wybory pozostają zapisane w manifestach i argv. Nie dopuszcza innej fizyki ani zmiany zależności mogącej przestawić DOF. Format jest native little-endian FP64, **single-rank x86-64**, przy identycznej lokalnej kolejności DOF. Nie obsługuje zmiany siatki/metody FEM→BEM ani multi-GPU.

## Norma i status

Dla E: sqrt((deltaEᴴ M_epsilon deltaE)/(E_refᴴ M_epsilon E_ref)); analogicznie B z M_mu_inverse. Stosowane są istniejące dodatnie operatory energii, bez dodatkowej faktoryzacji. Liczona jest rzeczywista różnica zespolonych pól, bez dopasowywania fazy. Oceniane są cała domena (region−1) i zdefiniowane domeny; w antenie osobno dodawany PTFEfeed3, w coaxie domain1.

Próg przed eksperymentami: względne E/B≤0,01 w każdym regionie i solve. Brak wpisu, duplikat, NaN/Inf, ujemny wynik lub brak ukończenia nie przechodzi. field-comparison.json zapisuje pokrycie i wartości. complete oznacza kompletność solve, field_accuracy_passed osobno ocenę tej normy. CLI kończy się błędem również przy ukończonym solve, jeżeli jakość nie przechodzi. Nie zastępuje to kontroli S/VSWR/energii/raw residual.

## FP64 na dysku i dłuższy run

--basis fp64-disk utrzymuje dokładny storage bazy na SSD, zachowując FP64 obliczenia. Runner tworzy własny /work/basis, czyści go po zakończeniu/przerwaniu; nie zmienia geometrycznej dokładności medium. Nie mylić z FP64 device-resident.

```sh
python3 tools/dev.py run tshaped-medium artifacts/new-candidate --seconds 1800 --basis fp32 --save-fields --field-reference artifacts/m1-antenna-fields-reference-r2-20261018 --background
```

Przed dużym kandydatem sprawdź aktualne RAM/GPU i checkpoint — powyższa historyczna próba FP32 została zatrzymana guardem, więc nie ponawiać jej bez rozwiązania presji pamięci. Referencja jest lokalnym artefaktem (nie Git); po utracie danych trzeba odtworzyć ją na właściwym buildzie.

--background odłącza proces od sesji narzędzia i zapisuje sąsiednie *.job.json/*.launcher.log. Monitoruj konkretny PID wraz z jego /proc start_ticks i stanem; sam jobfile nie dowodzi działania. Po terminalnym PID sprawdź result.json i log; brak wyniku nie oznacza sukcesu i nie autoryzuje restartu. Deadline≤1800s, guardRAM6GiB i cleanup pozostają aktywne. SIGINT/SIGTERM są zapisywane w interrupted_signal.

## Dowody

[Raport M1](optimization-baseline.md): tiny FP64/FP32, test referencji B×1,02, disk/resident, background worker oraz ukończona referencja anteny i guard kandydata. Natywny snapshot trwał w dużej referencji0,215s. Niepromowany FP32 kandydat nie ma pól, więc żaden raport nie powinien deklarować jego błędu antenowego ani przyspieszenia.
