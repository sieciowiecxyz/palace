# Szybki kontrolny coax TEM, 2 mm

13 086 tetraedrów, geometry-order2; Order2/Tol1e−6/MaxIts1600/MaxSize240/PA1/MAGMA jak w większym medium. Przekrój i PTFE są identyczne z coax-medium; długość jawnie zmniejszona z20do2 mm. To filtr poprawności kodu, nie reprezentatywny benchmark pamięci anteny.

```sh
python3 tools/dev.py run coax-tiny artifacts/tiny-smoke --seconds 60
python3 tools/dev.py run coax-tiny artifacts/tiny-fields --seconds 60 --coax-fields
python3 tools/dev.py run coax-tiny artifacts/tiny-l2 --seconds 60 --basis fp64 --coax-l2 --pc-side right
python3 tools/coax_fields.py artifacts/tiny-l2
```

Szybki smoke 3freq×2 porty zmierzono na11,25 s. Kwalifikacja L2 obu portów zajęła18,36 s. To pojedyncze runy, nie gwarancja czasu na innym sprzęcie. Błąd L2 pola wobec analitycznego TEM około0,5%; szczegóły i ograniczenia w docs/optimization-baseline.md.

Config/archiwum/mesh są powiązane hashami w fixture.json. geometry.json w każdym nowym coax runie zapisuje rzeczywiste wymiary do analizatora, a command.json zawiera hash konfiguracji po jawnych diagnostycznych zmianach. Parametr --basis zmienia storage, --pc-side normę/preconditioning; nie zmieniają precyzji operatora/faktorów FP64.

Analityczne S21/S12=exp(−jβ·0,002), β=2πf√2,1/c. E_r=V_inc·exp(−jβz)/(r·ln(b/a)) dla portu1; dla portu2 droga2 mm−z, B ma przeciwny kierunek. Pole porównujemy kompleksowo, bez dopasowywania fazy/amplitudy.

Generator opcjonalny: uv run --no-project --with gmsh==4.13.1 python tools/generate_coax_tiny.py --output artifacts/generated-coax-tiny. Zapisuje do osobnego nowego katalogu i odmawia nadpisania istniejącego; nie jest krokiem zwykłego runu. Odtworzenie w artifacts/coax-tiny-reproduced-20261018 dało identyczny SHA siatki. gmsh jest tylko zależnością generowania, zstd służy do przechowywania siatki. Zmiany generatora/geometrii wymagają nowego fixture i walidacji; nie usuwać katalogu automatycznie dla re-meshu.
