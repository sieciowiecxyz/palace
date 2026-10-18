# Palace na RTX 5070 Ti — wynik badania

## Wybrany wariant

**FP64 operator i faktory cuDSS, baza GMRES przechowywana w FP32, CUDA Unified
Memory, backend MAGMA.** Po rekonstrukcji rozwiązania solver niezależnie
przelicza normę residualu używaną w kryterium zatrzymania. W razie rozbieżności
wykonuje restart. To nie jest implementacja Tensor Cores.

Siatka i parametry pozostają: medium, P2, Tol=1e-6, MaxIts=1600, K=240,
PartialAssemblyOrder=1. Pominięcie estymatora jest jawne i dozwolone tylko przy
stałej siatce bez AMR; usuwa diagnostykę błędu siatki, nie zmienia równań.

Obraz: `localhost/palace:sm120-local-medium-20261018`.
ID: `65d1cc1edab73425469a47a0265e390ec4f7952c95694cd4633d31ba7315a283`.
Zawiera solver i adapter; nie wymaga montowania ich z hosta.

## Pomiary czasu

### Rzeczywista antena, 3,50 GHz, P2

Identyczny mesh: 1 601 320 tetrahedrów, 11 218 724 DOF. Trzy pary pomiarów,
bez Nsight, po 151 iteracji, bez OOM i przerwań przez próg pamięci hosta.
Oba warianty używają faktorów FP64 i niezależnej kontroli normy zatrzymania.

| Powtórzenie | Baza FP64 na SSD | Baza FP32 w pamięci |
|---|---:|---:|
| 1 | 1194,812 s | 955,176 s |
| 2 | 1201,648 s | 965,910 s |
| 3 | 1165,538 s | 948,517 s |
| **Mediana** | **19,91 min** | **15,92 min** |

**Czas krótszy o 20,06%; przepustowość większa o 25,09%.** Referencja przechowuje
bazę FP64 na SSD: to wynik dla tego komputera, nie porównanie z GPU mającym dość
VRAM na całe FP64. Natywne FP64/UVM nie ukończyło wcześniejszych prób przy
bezpiecznym limicie RAM. Nie podajemy jego hipotetycznego czasu.

Maksimum zaobserwowane dla finalisty: RAM kontenera 45,36 GiB, zajętość całego
GPU około 15,5 GiB (obejmuje pulpit/inne aplikacje). Referencja potrzebowała do
27,28 GB tymczasowej bazy na SSD; pliki zostały usunięte po obliczeniach.

### Kontrolny coax, 3 częstotliwości × oba porty

| Wariant | Mediana czasu Palace | Powtórzenia |
|---|---:|---:|
| FP64 z estymatorem | 36,849 s | 3 |
| FP64 bez estymatora | 29,653 s | 3 |
| FP32 cuDSS/UVM/cold CSR, bez estymatora | 30,811 s | 3 |

Na tej małej kontroli największy zysk pochodzi z pominięcia estymatora
(**19,53%**). Nie należy przypisywać go niższej precyzji faktorów.

## Poprawność i jej zakres

Wszystkie trzy pary dużej anteny przeszły z góry ustalone progi:

| Wielkość | Największa zaobserwowana różnica | Próg |
|---|---:|---:|
| Complex S | 4,15e-6 | 1e-3 |
| VSWR | 1,33e-5 | 0,01 |
| Suma mocy wychodzących portów | 1,76e-6 | 1e-3 |

Niezależnie przeliczona względna norma zatrzymania: około 9,96e-7 w obu
wariantach. Zintegrowana energia elektryczna różni się o około 1e-5 względnie,
magnetyczna o 4e-6, a strumień mocy o 1,5e-5.

**Ważne ograniczenie:** solver używa LEFT preconditioning. Surowy
`||Ax-b||/||b||` to inna miara: około 0,125 dla referencji i 0,808 dla bazy FP32.
Nie twierdzimy, że surowy residual osiągnął 1e-6. Zgodność S, energii i mocy jest
zmierzona; nie certyfikuje punktowej zgodności pola/prądów. Przy zadaniach
wymagających takiej zgodności trzeba ją zweryfikować osobno.

Oszacowany budżet mocy (porty + zewnętrzny strumień + straty dielektryczne z
LossTan i energii) ma błąd zamknięcia około 0,36% również w referencji FP64;
zmiana między wariantami to około 1e-5 W przy pobudzeniu 1 W. Zachowana siatka
medium nie jest badaniem zbieżności ani potwierdzeniem fizycznego projektu.

## Co zajmuje czas

Jeden zespolony wektor tej anteny zajmuje w FP64 około 171 MiB. Baza K=240
może sama zająć około 40 GiB; zapis FP32 zmniejsza tę część o połowę.
Oryginalny CSR przenoszony przez opcję cold-CSR miał tylko około 246 MiB.

Profil wybranego wariantu, celowo zakończony po 240 s, zapisał:

- około 29,1 s czasu kernela libCEED H(curl), 14,9 s MAGMA interpolation,
  14,0 s H(div) mass i 12,6 s MAGMA derivative;
- skumulowane transfery UVM około 1,12 TB D→H oraz 1,15 TB H→D,
  mimo znacznie mniejszej pojemności samego modelu.

W tym profilu przypisanie kerneli według czasu uruchomienia na CPU wskazało
około 90,3 s w preconditionerze, 12,7 s w coarse solve i 20,0 s w setup.
To częściowe okno profilu, nie rozkład całego zakończonego runu.

To pokazuje ponowne przenoszenie danych. Czasów kerneli nie należy sumować jako
rozłącznych części wall time. Nsight ostrzegł o utraconych zdarzeniach i użyciu
starszych bibliotek śledzenia dla nowszego sterownika: liczby transferów są
niepełne. Szczegółowy zapis każdego page faultu miał zbyt duży narzut RAM;
lżejszy profil ukończył się i zachował raport oraz SQLite. Czasy profilowane
nie weszły do powyższego benchmarku.

## Odrzucone ścieżki

- **FP32 faktory cuDSS na dużej antenie:** niezależne przeliczenie wykryło duży
  błąd normy zatrzymania i wymusiło restart; po 1800 s brak poprawnego wyniku.
  Mały coax nie wystarczał do zakwalifikowania tego wariantu.
- **Skalarne FP32 w bazach libCEED gen:** kontrola numeryczna przeszła, ale
  czas był gorszy od MAGMA. Nie wybrano tej zmiany.
- **BF16/FP16/TF32:** brak prostego przełącznika zachowującego wymaganą
  dokładność i przyspieszającego te custom sparse/FEM kernels. Publiczne API
  naszej wersji cuDSS przyjmuje FP32/FP64. Nie wykazano użycia Tensor Cores.
- **FP64 emulowane na Tensor Cores:** nowszy cuBLAS dokumentuje taką ścieżkę,
  ale wymaga nowszego stosu i odpowiednich wywołań GEMM. Nie jest to ustawienie,
  które automatycznie przyspiesza aktualne kernele libCEED.

## Użycie

Z katalogu repo, dla przygotowanego modelu medium zgodnego z powyższymi
ustawieniami i nowego katalogu wyniku:

```bash
# Polecenia historyczne, z repo anteny:
python3 -m infra.palace.local_profile CASE NEW_OUTPUT \
  --image localhost/palace:sm120-local-medium-20261018 --bundled-native \
  --backend magma --precision fp64 --uvm --fp32-basis \
  --skip-estimator --verify-residual --seconds 1800
```

`--precision fp64` dotyczy faktorów; `--fp32-basis` wyłącznie przechowywania bazy.
Kontener ma limit 60 GiB, niezależny deadline Podmana i próg bezpieczeństwa
6 GiB dostępnego RAM hosta. Ten duży model wymaga dużo wolnego RAM również z UVM.
Timeout/OOM nie jest wynikiem RF. Wariant pozostaje opt-in; innych częstotliwości,
portów i modeli nie uznajemy automatycznie za zwalidowane.

Odtworzenie buildu z istniejącego przypiętego buildera i czystego checkoutu
`.toolchain/palace-cudss-src` (bez zmieniania go):

```bash
python3 -m infra.palace.precision_benchmark build NEW_ADAPTER
python3 -m infra.palace.experimental_build NEW_BUILD --jobs 8
python3 -m infra.palace.experimental_build NEW_BUILD --package-image \
  --adapter NEW_ADAPTER/libcudss_fp32.so --image-tag localhost/palace:local-medium
```

Pakowanie sprawdza hashe binariów; samo zbudowanie nowego obrazu nie nadaje mu
kwalifikacji numerycznej. Zapisuje image ID, źródła, patche i sumy SHA256.
Spakowany bieżący obraz przeszedł kontrolę 6 solve'ów bez zewnętrznych mountów
solvera/adaptera, z kontrolą S, TEM, residualu i rzeczywistych hashy plików.

## Dowody

W `artifacts/infra/local-optimization-20261018/`:

- `final-antenna-campaign.json`, `m4-root-audit.json`, surowe runy `final-antenna-*`;
- `campaign-summary.json`, `noest-validation-report.json` — mała kontrola;
- `antenna-energy-consistency.json`, `antenna-power-budget.json`;
- `antenna-fast-nsight-light-240s/` — profil i jego ograniczenia;
- `disk-repro-build/build.json`, `runtime-image.json` — pochodzenie buildu;
- `packaged-image-coax-smoke/packaged-control-report.json` — końcowy test obrazu;
- `container-deadline-smoke.json` — deadline działa niezależnie od launchera.

Źródła badania: [NVIDIA RTX 5070](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5070-family/),
[cuDSS hybrid memory](https://docs.nvidia.com/cuda/cudss/advanced_features.html),
[cuBLAS emulation](https://docs.nvidia.com/cuda/archive/13.0.3/cublas/index.html#floating-point-emulation),
[compressed-basis GMRES](https://arxiv.org/abs/2009.12101).
TechPowerUp wskazany przez użytkownika zwracał 403; nie traktowano jego
marketingowych parametrów jako benchmarku Palace.
