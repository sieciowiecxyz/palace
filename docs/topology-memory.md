# M1: rzeczywiste DOF i bilans pamięci

EXP21, 2026-10-18. Audyt offline obecnego medium W.3; bez uruchamiania GPU,
zmiany modelu i dyskowego workspace. Audyt był częścią M1; po EXP22 M1 zamknięty, dowody w [M1](milestones/optimization-M1.md).

## Odtworzenie i kontrola

```sh
python3 tools/mesh_cost.py examples/tshaped-medium/mesh/pcb.msh --dofs --output artifacts/mesh-dofs.json
```

Raport lokalny `artifacts/m1-mesh-dofs-20261018.json`: 17,349 s, max RSS
663 875 584 B. Ta próba miała limit adresowy 4 GiB i deadline 120 s.
Pakowane klucze i maski materiałów pozostają w RAM. Stare wywołanie bez
`--dofs` zachowuje tańszy audyt elementów i objętości.

Mesh SHA `ec56c9a7de3e9cdc9618b87a2029975d474d6d5621f9fd08b35f24501b6f161e`.
Wyniki porównano z rzeczywistym logiem EXP19 qualified, nie tylko z wzorami.
Zgodne są wszystkie cztery liczby topologiczne i trzy przestrzenie:

| Wielkość | Liczba |
| --- | ---: |
| Wierzchołki V | 383 949 |
| Krawędzie E | 2 196 005 |
| Ściany F | 3 413 357 |
| Tetraedry T | 1 601 320 |
| H1 P2: V+E | 2 579 954 |
| ND P2: 2E+2F | 11 218 724 |
| RT degree1: 3F+3T | 15 044 031 |

Są to DOF przed eliminacją essential BC, dla konforemnej siatki tetra bez
periodycznych identyfikacji/hanging nodes. Węzły krzywizny geometrii P2 nie
tworzą dodatkowych wierzchołków topologicznych. Palace dla Order2 tworzy
RT_FECollection z argumentem `order-1`, mimo etykiety RT(p=2) w logu.
Wzory odpowiadają [implementacji MFEM 4.9](https://docs.mfem.org/4.9/fe__coll_8cpp_source.html).
Regresja dwóch tetra dzielących ścianę sprawdza wspólne DOF i orientację.

## Ile kosztuje powietrze

Każda krawędź i ściana ma maskę wszystkich przyległych materiałów; wspólnych
DOF nie dodajemy osobno obu domenom. Dokładnie **6 460 374 ND2 DOF (57,586%)**
należy wyłącznie do AIR. Pozostałe **4 758 350** należą do materiałów lub
wspólnych interfejsów. PTFE-exclusive zajmuje 3 808 772 DOF: usunięcie
powietrza nie usuwa drobnej siatki dielektryka kabli.

Jeden complex128 wektor pełnej przestrzeni: 179 499 584 B (171,18 MiB).
Odpowiednik non-air/shared: 76 133 600 B (72,61 MiB). To rachunek danych
wektora, **nie prognoza pamięci faktorów, kosztu BEM ani przyspieszenia**.
FEM–BEM zwykle zachowuje też część powietrza wewnątrz wybranej granicy.

Obecna zamknięta powierzchnia zewnętrzna ma 18 840 trójkątów i 28 260
krawędzi. Przykładowy ślad ND2 to 94 200 DOF. Jeden gęsty blok complex128
kosztowałby **141 978 240 000 B (132,23 GiB)**. Starsze 11,90 GiB dotyczyło
jednego DOF na krawędź, np. innej dyskretyzacji RWG; te oszacowania nie są
zamienne. Maxwell może wymagać więcej bloków oraz workspace.

Hipoteza do M2: Maxwell FEM wewnątrz kompaktowej granicy obejmującej
PCB/dielektryki/feed oraz skompresowany operator zewnętrzny BEM/FMM/H².
Najpierw mały PEC/dielectric/interface test. Odrzucić, jeśli dla porównywalnego
błędu koszt setup+solve lub całkowita pamięć nie poprawiają FEM. Nie usuwać
po cichu kabla, portów, reflektora ani warunków promieniowania.

## Bilans tego samego stanu managed

Źródło: `artifacts/m1-native-complex-coarse-antenna-qualified-20261018/`.
W chwili `gmres.basis_release.begin` mamy 55 147 611 962 B managed i
25 008 217 684 B żywych alokacji cuDSS. Kolejne znaczniki zwalniania dają:

| Składnik bilansu netto | B | GiB |
| --- | ---: | ---: |
| cuDSS live, już zawarte w managed | 25 008 217 684 | 23,29 |
| Spadek po V.clear() | 6 461 985 024 | 6,02 |
| Pozostały spadek po zwolnieniu linear solvera, bez cuDSS | 14 390 057 060 | 13,40 |
| Pozostaje po zwolnieniu solvera | 9 287 352 194 | 8,65 |
| Razem | 55 147 611 962 | 51,36 |

Suma zgadza się dokładnie; to algebraiczne rozliczenie kolejnych zwolnień,
**nie semantyczny opis wszystkich operatorów/workspace**. Szczyt cuDSS nie
jest dodatkową pamięcią poza managed. Cgroup peak 58 898 771 968 B to inna
miara, z innym zakresem i chwilą pomiaru; sampled VRAM nie pokazuje całego UVM.

Spadek po V.clear() to dokładnie 36 rozmiarów wektora complex ND2. Log
pojemności zgłasza 45 wektorów i 8 077 481 280 logicznych B; nie każdy taki
wektor musiał mieć tę samą materializację urządzenia. Do ustalenia dokładnego
host/device ownership potrzebny jest aktualny audyt alokacji. Nie odejmować
całej logicznej pojemności od fizycznej rezydencji.

`artifacts/m1-topology-memory-balance-20261018.json` zawiera wartości,
porównania runtime, sprawdzenie sumy oraz SHA źródłowych raportów/logów.
Późniejszy EXP22 dostarczył aktualną atrybucję ścieżek alokacji i wiarygodny
[profil kerneli/transferów](profiling-window.md). Aktywny M2; TF32 ani nowa metoda nie są promowane.
