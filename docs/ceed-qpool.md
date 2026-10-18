# Eksperyment M1: aktywne Q-wektory libCEED

Status 2026-10-18: **prototyp, niezakwalifikowany dla Palace/anteny**. Mały test operatorów przechodzi; porównanie solvera nie doszło do solve przez brak wolnej pamięci w systemie. M1 pozostaje otwarty, obowiązkowy M2 FEM–BEM/MoM nadal przed nami. Wymaganie RAM/VRAM bez dyskowego working storage obowiązuje także ten eksperyment.

## Co dokładnie zmieniono

`tools/experiments/ceed_qpool.py` tworzy alternatywną bibliotekę ze źródła libCEED `cbd49027b0ae891f0c8efd9d9cf05bc82385a388`. Sprawdza SHA oryginalnego cuda-ref operatora i wstrzykuje helper `ceed_qpool.h` wyłącznie do zwykłego `CeedOperatorApplyAdd_Cuda`.

- Aktywne Q-wektory z INTERP/GRAD/DIV/CURL pożyczane z istniejącego `CeedGetWorkVector`, zwracane przez `CeedRestoreWorkVector`.
- Pasywne pola, EVAL_NONE, AtPoints i oryginalne wektory potrzebne dla assembly pozostają. Oryginalne uchwyty wracają przed końcem ApplyAdd; nie usuwamy pamięci, do której mogą wskazywać cached `qf_active_in`.
- FP64, baza, quadratura i algebra bez zmiany. Konserwatywnie `cudaDeviceSynchronize` przed pożyczeniem i przed oddaniem; koszt synchronizacji może zniwelować korzyść. Wariant nie obiecuje speedup.
- Nakładające się ApplyAdd są odrzucane; prototyp nie jest kwalifikowany dla współbieżności, MPI, AtPoints ani ścieżek błędów z częściowo pobranymi wektorami. Przy błędzie proces ma zakończyć próbę; nie kontynuować pracy na takim operatorze.

Nie usuwa to wszystkich kosztów QFunction assembly ani biernych pól. Pool libCEED może zatrzymywać większe wektory do kolejnych użyć. Zysk, stagnacja i ewentualny wzrost pamięci wymagają pomiaru. [Audyt pamięci](memory-audit.md) wskazuje koszt do zbadania, nie oczekiwaną liczbę odzyskanych GiB.

## Build z cache i zachowanie bazy

```sh
python3 tools/experiments/ceed_qpool.py
```

Natywny Palace musi mieć poprawny bieżący manifest. Helper blokuje ten sam build.lock, raz kopiuje istniejące drzewo libCEED (~41 MB) do osobnej lokalizacji w builderze i zachowuje pozostałe obiekty. Kompiluje jeden zmieniony plik C, linkuje z oryginalnymi obiektami/flagami oraz buduje mały probe. Oryginalne zainstalowane libCEED, MFEM i hypre pozostają nietknięte. Zwykły runner używa bazy.

Wykonany build trwał **1,51 s**, kolejne wywołanie zachowało gotowe artefakty bez kompilacji. Wynik `build/ceed-qpool/` zawiera bibliotekę, probe, logi, wygenerowane źródło i manifest z receptą/SHA oraz argv. To cache kompilacji, nie pamięć robocza solvera. Wcześniejszy pomysł interposera odrzucono jeszcze przed GPU ze względu na prywatne symbole libCEED.

## Opt-in w istniejącym runnerze

```sh
python3 tools/dev.py run coax-tiny artifacts/new-qpool --seconds 60 --basis fp64 --allocation-trace --ceed-qpool
```

Runner sprawdza hashe recepty/biblioteki, builder/runtime i docelową ścieżkę libCEED. Tylko ten kontener montuje zamienną bibliotekę; manifest jest kopiowany do wyniku. Log musi potwierdzić dodatnie `PALACE_CEED_QPOOL: calls=... borrowed_vectors=...`, inaczej run nie przechodzi kompletności. Nie używamy LD_PRELOAD do podmiany prywatnych funkcji backendu.

Kontrola pól tej samej siatki nadal wymaga przypiętego MFEM/runtime i układu DOF. Ta biblioteka zmienia workspace operatora, nie przestrzeń ani kolejność DOF; override jest jawnie zapisany obok natywnego manifestu. Nie oznaczać bazowego buildu jako globalnie zakwalifikowanego po testach tego wariantu.

## Wykonane kontrole

Probe `tools/experiments/ceed_qpool_probe.c/.h`: dwa operatory masowe o znanych działaniach, naprzemienne wywołania, zmiana pasywnego współczynnika, diagonal i ApplyAdd po assembly. 6 DOF, oczekiwane wartości sprawdzane z tolerancją absolutną 1e−11.

| Próba | Wynik | Zakres |
| --- | --- | --- |
| Probe baza | PASS, exit0, 1,90 s | Dwa operatory, dane kontrolne |
| Probe Q-pool | PASS, exit0, 0,63 s | 16 ApplyAdd / 32 pożyczone wektory |
| Coax-tiny baza, 3freq/2porty | FAIL przed solve, 2,89 s | CUDA OOM + host guard; bez Q-pool |
| Coax-tiny Q-pool i TEM L2 | NOT RUN | Przerwano drabinę po FAIL bazy |
| Pełna antena | NOT RUN | Nie uruchamiać przed filtrami |

Artefakty: `artifacts/m1-qpool-probe-20261018/`, `artifacts/m1-qpool-tiny-baseline-20261018/`. Różnica 1,90/0,63 s nie jest benchmarkiem: kolejność zimny/ciepły JIT i bardzo mały problem. Nie mamy zmierzonego zysku pamięci ani błędu Maxwella z tego prototypu.

Po nieudanym baseline telemetry pokazała MemAvailable 5,34→4,84 GB (4,97→4,51 GiB), a GPU telemetry wskazała około 15/16 GiB zajęte przez inne obciążenie. Nie zamykano aplikacji użytkownika ani nie obniżano guard. Runner dostał preflight odrzucający start GPU, gdy host RAM jest poniżej 6 GiB; guard nadal działa podczas runu. Brak pamięci zatrzymał próbę bazową i nie jest oceną Q-pool.

## Osobny trop: początkowa pula HYPRE/Umpire

Źródło przypiętego hypre3.1.0 `src/utilities/memory.c`, funkcja `hypre_UmpireInit`, ustawia cztery pule (device/UM/host/pinned) po **4 GiB**. `hypre_umpire_device_pooled_allocate` tworzy pulę leniwie przy pierwszej alokacji; to nie cztery alokacje wykonane od razu. Failed baseline zgłosił `cudaMalloc(bytes=4294967312)` w tej ścieżce przy tworzeniu hierarchii FEM, przed libCEED Apply.

Publiczne `HYPRE_SetUmpireDevicePoolSize(size_t)` może zmienić rozmiar przed utworzeniem puli. Następna osobna hipoteza: opcjonalny mniejszy seed (np.256 MiB), z logiem i dokładnym testem FP64; nie mylić z limitem całego HYPRE i nie ogłaszać stałej oszczędności dla dużej anteny. Najpierw trzeba wdrożyć flagę i sprawdzić inicjalizację/obsługę błędów; **jeszcze tego nie zmieniono ani nie zmierzono**. Nie łączyć w jednym porównaniu zmiany Umpire i Q-pool.

[Źródło hypre3.1.0](https://github.com/hypre-space/hypre/blob/v3.1.0/src/utilities/memory.c). W builderze odczytano faktycznie użyty stage `hypre-3.1.0-b4in3qr6dr5kzmer3qgvad2uuhrnvfvh`; brak katalogu Git w tym tarballu, więc nie przypisujemy mu nieustalonego SHA commita.
