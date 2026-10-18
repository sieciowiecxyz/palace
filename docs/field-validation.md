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

`--initial-fields` i `--field-reference` mają różne role. Ukończony snapshot z poprawnym hash/fizyką może posłużyć jako przybliżenie startowe nawet wtedy, gdy jego wcześniejsze `field_accuracy_passed=false`; metadane nowego runu oznaczają go wtedy jako start only. `--field-reference` odrzuca ukończone runy, które mają `field_accuracy_passed=false`. Obie ścieżki odrzucają niekompletne, uszkodzone lub niezgodne dane. Sam hash nie potwierdza jakości numerycznej.

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

[Raport M1](optimization-baseline.md): tiny FP64/FP32, test referencji B×1,02 oraz historyczne disk/resident runy. FP64-disk i ukończone FP32-disk comparison pozostają **REJECT** jako warianty robocze; resident FP32 attempt przerwał RAM guard bez pól. W.3 native complex coarse ma nową ostrzejszą resident FP64 referencję i medium solve 3,50 GHz/P2, którego ważone pola E/B przeszły próg 1% we wszystkich regionach. Jest to kontrola zgodności numerycznej jednego punktu na tej samej siatce; pomiar fizyczny, zbieżność siatki i kwalifikacja innych pasm/obudowy pozostają poza tym testem. Szczegóły, wartości i limity: [natywny complex coarse](native-complex-coarse.md); pamięć i run: [fazy pamięci](memory-phases.md). Nie deklarować jakości poza zakresem tych bramek ani przyspieszenia z nieporównywalnych prób.
