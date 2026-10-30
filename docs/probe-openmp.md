# OpenMP w wyszukiwaniu sond

Opcja `PALACE_PROBE_THREADS=4` równolegli wybór kandydatów dla sond, których
pierwsze wyszukiwanie MFEM nie znalazło. Domyślna wartość pozostaje **1**.
Nie zmienia globalnego `OMP_NUM_THREADS`, metody FEM, siatki ani precyzji.

## Włączenie

W istniejącym poleceniu `tools/stage_probe_run.py prepare`, uruchamianym z głównego
repo, wskaż nowy build i odpowiadający mu worktree źródeł:

```sh
--source /home/sieciowiec/dev/cpp/palace-opt-probe-openmp \
--build /home/sieciowiec/dev/cpp/palace/build/probe-openmp-20261030 \
--probe-locator mfem --probe-threads 4
```

Odpowiednikiem w natywnym procesie są `PALACE_PROBE_LOCATOR=mfem` i
`PALACE_PROBE_THREADS=4`, przy zachowaniu `OMP_NUM_THREADS=1` dla MFEM.
Zakres opcji to 1..64; liczba pracowników jest ograniczona liczbą nierozwiązanych
punktów. Runtime może dodatkowo ograniczyć zespół; log podaje rzeczywiste
`threads_used`, nie tylko żądanie. Build bez OpenMP odrzuca żądanie większe niż 1.
Kontroler wymaga jawnego MFEM locatora i zgodnego nowego source/native.

## Bezpieczeństwo

- MFEM wyznacza centra elementów sekwencyjnie. Ich snapshot jest tylko do odczytu.
- Wątki wykonują wyłącznie obliczenia na tablicach C++ i własnych kopcach top128.
  Bufory są alokowane przed wejściem do zespołu. Brak MFEM, CUDA i alokatora
  Umpire wewnątrz workerów; nie włączamy globalnego OMP2 znanego z błędu puli.
- Kolejność kandydatów rozstrzyga odległość oraz ID elementu. Wyniki dla 1/2/4/8
  wątków są deterministyczne. Odwrotne transformacje i kontrole wnętrza/residuum
  nadal wykonuje oryginalna ścieżka sekwencyjna. GSLIB pozostaje fallbackiem.
- Jeśli wszystkie punkty znalazł już MFEM, dodatkowa praca nie jest wykonywana.

## Pomiary na tej maszynie

Rzeczywista siatka medium: 1,7 mln elementów, 164 sondy, 23 do wyszukania pomocniczego;
trzy zbalansowane rundy, jeden odczyt siatki, produkcyjny konstruktor lokalizatora:

| Lokalne wątki | Mediana całego konstruktora |
|---:|---:|
| 1 | 1,624826 s |
| 2 | 1,583256 s |
| 4 | 1,564537 s |
| 8 | 1,564552 s |

Zysk przy 4 wątkach to **60,3 ms / 3,71% konstruktora**. Nie oznacza 3,71% całego solve.
Pozostała część MFEM jest sekwencyjna, dlatego 8 wątków nie pomogło bardziej.
Snapshot współrzędnych ma 40 816 392 B; dochodzi maska poprawności ok. 1,7 MB
oraz małe kopce. Z tego powodu nie promujemy automatycznie większej liczby wątków.
Syntetyczny test samej pętli dał 64,0→10,1 ms przy 8 wątkach, lecz nie jest benchmarkiem FEM.

## Walidacja i ograniczenia

- Standalone: 23 736 sprawdzeń OpenMP oraz 5 928 bez OpenMP; niezależny full-sort oracle,
  remisy/cap/nonfinite/empty, identyczność bitowa między zespołami i globalne OMP1.
- Native CPU: 925 asercji OP, w tym zespolone ND/RT/H1 przy żądaniu 1/2/4/8,
  oraz 55 986 PRE. Dwie sondy tiny ograniczają rzeczywisty zespół do 1/2;
  zespoły 4/8 potwierdza osobny konstruktor medium i standalone.
- Produkcyjny konstruktor: 12 prób, wszystkie 164 punkty znalezione, zespoły 1/2/4/8
  rzeczywiście użyte, globalne OMP1 zachowane. Nie składano K/C/M ani nie liczono RF.
- GPU replay przy 4 wątkach: prawdziwe zapisy CUDA/managed i wszystkie 164 punkty;
  zespolone relL2 E=4,91e-14, B=9,53e-14 względem GSLIB. To pola syntetyczne,
  nie pełny solve Maxwella. Pełny RF nowej wersji i pomiar CMP pozostają NOT RUN.
- 101 testów Python PASS. Bez nowej zależności, bez zmiany globalnych ustawień OMP.

Natywny build z cache trwał 5,32 s, kompilował 2 jednostki C++, bez przebudowy MFEM/HYPRE/libCEED.
Artefakty: `build/probe-openmp-20261030/`, `artifacts/probe-openmp-medium-20261030/`,
`artifacts/probe-openmp-gpu-fields-20261030/`. Nie nadpisano poprzedniej kwalifikacji.
Rollback opcji: `--probe-threads 1` albo pominięcie opcji. Poprzedni pełny profil
M6 i jego wyniki dotyczą źródeł 95822/native 048f; ich źródła zachowano w worktree
`/home/sieciowiec/dev/cpp/palace-opt-integration`. Nowy build jest odrębny i nie
otrzymał przez kopiowanie kwalifikacji RF ani wyników wydajności poprzednika.
