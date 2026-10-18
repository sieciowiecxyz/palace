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

## Pamięć robocza i dłuższy run

Dostępne są wyłącznie --basis fp32/fp64, oba przechowują bazę w RAM/VRAM. Mechanizm disk basis usunięto na polecenie użytkownika; stare zmienne środowiska są odrzucane przez solver. Nie odtwarzać dawnych argv ze storage dyskowym, nie zastępować go swapem ani plikowym mmap. UVM może migrować GPU↔RAM.

Zapisane fields.json/E/B są zwykłym wynikiem diagnostycznym, a --field-reference odczytuje dane referencyjne do porównania; nie stanowią bazy roboczej GMRES. Są opcjonalne; rutynowy run ich nie włącza. Referencję historyczną wolno wykorzystać jako zachowane dane, ale jej czas i pamięć z disk basis nie kwalifikują wydajności dopuszczalnego wariantu. Nie przeliczać jej starym poleceniem.

Nie ponawiać pełnej anteny bez jawnej hipotezy i kontroli dostępnej pamięci. Przed dużą próbą domyślny coax-tiny trwał około 11–14s w pojedynczych smoke'ach; to filtr poprawności uruchomienia bez offloadu, a nie benchmark czasu.

--background odłącza proces od sesji narzędzia i zapisuje sąsiednie *.job.json/*.launcher.log. Monitoruj konkretny PID wraz z jego /proc start_ticks i stanem; sam jobfile nie dowodzi działania. Po terminalnym PID sprawdź result.json i log; brak wyniku nie oznacza sukcesu i nie autoryzuje restartu. Deadline≤1800s, guardRAM6GiB i cleanup pozostają aktywne. SIGINT/SIGTERM są zapisywane w interrupted_signal.

## Dowody

[Raport M1](optimization-baseline.md): tiny FP64/FP32, test referencji B×1,02, historyczne disk/resident kontrole i runy anteny. Referencja FP64-disk oraz ukończony field comparison FP32-disk są zachowane, lecz odrzucone jako warianty robocze; resident FP32 antenna attempt został przerwany i nie ma pól. Natywny snapshot trwał w historycznej dużej referencji 0,215s. Nie deklarować jakości antenowej ani przyspieszenia z prób, które nie spełniają wymogu RAM/VRAM.
