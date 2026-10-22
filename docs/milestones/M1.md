# M1 — audyt referencji i profilowania

Status: **COMPLETE (2026-10-18)**. Referencja, profil i audyt M1 ukończone; aktywny M2. Kryteria niezmienione
w [MILESTONES](optimization-contract.md). Goal jako całość nieukończony.

| Bramka | Dowód i granica |
| --- | --- |
| M1.1 Referencja | EXP19 W.3medium3,50GHz/P2, meshSHAec56c9a7…, manifesty i residenttight-r2; [native coarse](../native-complex-coarse.md). To fixture, nie najlepsza geometria anteny. |
| M1.2 Normy | Kod GMRES InitialResidual/report_residual, jawne Ax−b, analityczny TEM, RIGHT i ostrzejszy FP64W.3; wyjaśnienie poniżej. |
| M1.3 Jakość |35iter/447,462sbezprofilera, raw8,36e−7; maxΔS6,70e−9/VSWR8,30e−9/E-B9,89e−8 względemtight-r2raw7,28e−10. Zamrożone K.3/K.4PASS. |
| M1.4 Koszt | [DOF i pamięć](../topology-memory.md): wszystkie liczniki zgodne z runtime; [aktualne alokacje](../memory-audit.md):99,616%peaku + jawny remainder; [CUDA profil](../profiling-window.md): pełna siatka, dwie iteracje, kalibracja i brakwarnings, jedna niejednoznaczna granica. Pełny runbezprofileraEXP19 osobno. |
| M1.5 Kierunek | Kompaktowy Maxwell FEM–BEM z kompresją/FMM oraz późniejsza redukcja presji UVM; hipotezy i warunki odrzucenia poniżej. |

## Dlaczego dawne raw0,125/0,808 nie były poprawnym stopping

LEFT mierzy ||B(b−Ax)||/||Bb||. Jawne FP64 zastosowanie A mierzy ||b−Ax||/||b||.
To różne normy; mały pierwszy iloraz nie ogranicza drugiego bez kontroli
warunkowania/ważenia B. To nie błąd samej etykiety ani dowód, że raw jest
procentem błędu E. Historyczne FP64LEFT9,956e−7 przyraw0,125 pokazuje tłumienie
konkretnego kierunku residuum przez preconditioner. FP32storage zwiększyłrawdo0,808;
same bliskie porty nie kwalifikowały pól. [Diagnostyka](../reference-correction.md)
i [kontrole norm](../memory-audit.md) zachowują te odrzucone wyniki.

Kontrola TEM/RIGHT i niezależne ponowne Ax−b usuwają zależność stopping od B.
Dla W.3 nowa referencja RIGHT1e−9/raw7,28e−10 oraz osobny medium solve
RAW8,36e−7 sprawdzają rzeczywiste równanie i całe pola, nie zmieniają nazwy
starego testu. Stary EXP12 nie jest dalej używany jako referencja dokładności;
może być jawnie oznaczonym approximate initial guess. Nie poluzowano progów.

## Decyzje wynikające z M1

- M2: zbadać Maxwell FEM wewnątrz kompaktowej granicy z zewnętrznym skompresowanym
  BEM/FMM/H². AIR-exclusive57,586%DOF to potencjał, nie obiecany speedup;
  pozostały PTFE/feed i gęste bloki mogą zniwelować zysk. Najpierw PECsphere,
  dielektryk i sprzężony interfejs, potem koszt przy porównywalnym błędzie.
  Odrzucić integrację przy błędach fizyki/portów lub braku poprawy pamięci/czasu.
- Późniejsze etapy FEM: redukcja reprezentacji i migracji faktorów/workspace.
  25GBcuDSS i295GBUVMruchu/2iteracje wskazują sens małego testu polityki
  rezydencji/dostępu. Nie zakładać, że migracja do RAM lub CPU-preference
  przyspieszy solver. Wymagane pomiary pełnego czasu i K.3/K.4, bezswap/SSD.
- Wczesna ortogonalizacja0,156s/17,665s nie uzasadnia obietnicy dużego speedupu
  z Tensor Cores. Późna baza może kosztować więcej; jej profil należy do M3.

Aktualne binarium zmienia diagnostykę, nie matematykę zwykłego solve. Końcowy
normal-path tiny6/6 w13,674s przeszedł (rawmax9,10e−7, E3,06e−15/B1,50e−13, ΔS7,81e−16);47tests i docs-gardenPASS. Artefakt m1-cuda-affine-normal-regression-20261018. Potwierdzono brak regresji;
pełnego W.3 nie powtarzamy wyłącznie po zmianie opt-in logów. Ograniczenia:
profil wczesnych iteracji, nie cała częstotliwość/pasma, brak fizycznej walidacji
anteny, stack-path nie oznacza unikatowego właściciela każdej drobnej alokacji.
