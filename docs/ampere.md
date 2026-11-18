# Izolowany build A100 / SM80

Polecenie: `python3 tools/build_ampere.py`. Wyłącznie lokalna kompilacja x86-64;
bez GPU, QEMU, chmury, registry, publikacji i symulacji. Limit buildera:
2 CPU, 6 GiB RAM, swap wyłączony. Aktualny sweep SM120 pozostaje niezależny.

## Źródła i cache

Kompilujemy dokładne źródła zoptymalizowanego pakietu
`artifacts/m7-sm120-bundle-r3-20261022`, a nie dawny bazowy solver A100.
Hash wejść kompilatora musi zgadzać się z jego manifestem. Brakujące w eksporcie
`scripts/` i `test/unit/` są odzyskiwane z lokalnego commita wskazanego w tym
manifeście; ich dodatkowe sumy trafiają do `provenance.json`.

Retained builder SM80 zawiera MFEM 4.9, HYPRE 3.1, MAGMA i cuDSS 0.7.1.4,
CUDA 12.9.1. Nie przebudowujemy tych zależności. Wyjątek: zachowane małe źródła
libCEED kompilujemy z `-march=x86-64-v3`, aby usunąć wcześniejsze host-native CPU
flags. Używamy istniejącej procedury naprawy libCEED z infra projektu anten.
SM80 cache C++/CUDA jest osobny: `.cache/ccache-sm80` i dedykowany kontener.
Każde kolejne wywołanie zachowuje ten kontener i zależności. Cache SM120 i źródłowy
pakiet M7 nie są modyfikowane.

## Zachowane funkcje

- CUDA `sm_80`, Release, przenośny CPU x86-64-v3; bez `-march=native`.
- Partial assembly, CUDA UVM RAM↔VRAM, adapter pamięci i cuDSS.
- FP32 storage bezpośredniej bazy GMRES, rachunek operatora/residuum FP64.
- Native complex coarse FP64; FP32 coarse z korekcjami pozostaje opt-in.
- Jawne zwalnianie danych, audyty i istniejące ograniczone reuse obu portów.
- Brak dyskowej bazy/swapowania solvera, brak automatycznego TF32/BF16.

To przeniesienie implementacji, nie nowa kwalifikacja numeryczna. Opcjonalne
eksperymenty PC/basis nie są promowane. Multi-GPU nie jest objęte tym zadaniem.

## Artefakty i późniejsze uruchomienie

Wyniki: `artifacts/m7-sm80-a100-20261025/`:

- `status.json`, `build.log`, `libceed-build.log`, `static-audit.log`;
- `provenance.json`: dokładne źródła, flagi, limity i obrazy;
- `source-from-commit.patch`: pełna różnica źródeł M7 względem podanego commita;
- `builder-resource-audit.txt`: faktyczne cgroup 6 GiB / swap=0 / 2 CPU,
  bez urządzeń `/dev/nvidia*`;
- `bundle/build/sm80/`: pliki native, manifest i digest runtime;
- `bundle/tools/dev.py`: istniejący runner ze ścieżką buildu SM120→SM80
  i dodatkowym sprawdzeniem hasha dołączonej libCEED.

Gotowy obraz lokalny ma tag `localhost/palace:m7-sm80-a100-20261025`.
Nie został wysłany do registry. Runtime zawiera także właściwe nagłówki JIT,
schemat oraz poprawioną bibliotekę libCEED. Build nie zmienia głównego
`tools/runtime.json` ani rejestru runtime w repo anten.

Przyrostowe przebudowy wykonujemy powyższym `tools/build_ampere.py`, nie
`bundle/tools/dev.py build/package` (te polecenia zachowują oryginalny workflow
SM120). Runner `bundle/tools/dev.py run` używa dostarczonego runtime po digest.
Kontrole statyczne obejmują SM80 cubins Palace/adaptera/MFEM/HYPRE/MAGMA,
hash wszystkich czterech dostarczanych plików i rozwiązywanie zależności loadera.
Brak `libcuda.so.1` w kontenerze bez urządzeń GPU jest oczekiwany; biblioteka
sterownika musi być wstrzyknięta przez runtime NVIDIA na hoście A100.

Po przeniesieniu obrazu i bundle na host A100 z odpowiednim sterownikiem,
CUDA-container tooling i Podmanem, **osobno** wykonać smoke na `coax-tiny`,
następnie porównanie medium z właściwą referencją. Przykładowe flagi zachowania
algorytmu: `--basis fp32 --direct-basis --native-complex-coarse --pc-side right
--krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis
--release-final-solver`. Brak `--native-coarse-fp32` zachowuje coarse FP64.
Używać jawnego `--runtime-image` z digestu `runtime-image.json` i nowego katalogu
wyników. Nie kopiować kwalifikacji RF ani faktorów z SM120. GPU testy i symulacje
w ramach przygotowania tego buildu: **NOT RUN**.
