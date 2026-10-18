# M1: fazy pamięci i zwalnianie bazy GMRES

2026-10-18. Jeden GPU, jeden rank. Ten raport opisuje historyczny EXP12,
referencję **wykonania** FP64 w RAM/VRAM. Późniejsza silniejsza referencja
i numeryczna kwalifikacja W.3 są w [native complex coarse](native-complex-coarse.md).
Ten raport powstał przed zamknięciem M1 i zachowuje wyniki faz historycznego EXP12. Aktualny status bramki oraz granice kwalifikacji są w [checkpoint M1](milestones/M1.md). Raport nie promuje mixed precision.

## Mechanizm i odtwarzanie

`--memory-marks` włącza opcjonalny weak C hook `PalaceMemoryMark` z lokalnego
adaptera CUDA. Raportuje monotoniczne interwały hosta i live/peak logicznych
alokacji managed między markerami. Nie synchronizuje GPU. Brak adaptera nie
dodaje zależności do upstreamowego solvera; żądane przez runner markery muszą
jednak wystąpić, inaczej kontrola kompletności zwraca FAIL.

`--release-gmres-basis` zwalnia owning wektory V po rekonstrukcji rozwiązania,
kontroli residuum i zapisaniu statystyk, przed postprocessingiem. Domyślnie
wyłączone. Nie zmienia K, tolerancji ani E. Kolejny solve ponownie inicjalizuje
wektory; sześć solve'ów małego fixture sprawdza także tę ścieżkę. Runner dopuszcza
opcję tylko dla GMRES; FGMRES ani MPI nie są zakwalifikowane.

```sh
python3 tools/dev.py build --jobs 8
python3 tools/dev.py run coax-tiny artifacts/new-release-tiny --seconds 60 --basis fp64 --hypre-pool-mib 256 --release-gmres-basis --memory-marks --save-fields
python3 tools/dev.py run coax-tiny artifacts/new-release-tem --seconds 120 --basis fp64 --hypre-pool-mib 256 --release-gmres-basis --memory-marks --coax-l2
```

Każdy katalog musi być nowy. Pełny run wykonany po filtrach:

```sh
python3 tools/dev.py run tshaped-medium artifacts/new-resident-reference --seconds 1800 --basis fp64 --hypre-pool-mib 256 --release-gmres-basis --memory-marks --save-fields --background
```

To jedna 3,50 GHz/P2, P1 zakończony 50 Ω, nie sweep. Zachowane medium i mesh;
bez Q-pool, scratch, swap i alokacji roboczych na SSD. Obowiązują cgroup
60 GiB oraz hostguard 6 GiB. Flaga `--hypre-pool-mib` zmienia początkowy seed, nie cap.

## Dowody EXP12

- Dwie pierwsze próby tiny zakończyły solve, ale pozostały **FAIL kompletności
  diagnostyki**: scalanie stdout/stderr przecięło release, a następnie KSP check.
  Nie osłabiono parserów ani nie nadpisano tych artefaktów.
- Runner przechwytuje osobno `palace.stdout.log` i `palace.stderr.log`.
  Po zakończeniu składa `palace.log` jako stdout, potem stderr. To **nie jest
  globalna chronologia zdarzeń**; fazy mają własny zegar. Podczas runu czytaj
  surowe strumienie i `telemetry.jsonl`. Regresja celowo przerywa komunikat
  stdout wpisem stderr i sprawdza integralność zachowanych linii.
- `artifacts/m1-gmres-release-tiny-r3-20261018/`: 10,517 s, 6/6 solve,
  iteracje 24/13/14/25/13/13; sześć pełnych stopping checks, release i faz.
  Względem EXP11 seed256: max |ΔS| 3,88e−15, ΔVSWR 6,66e−15,
  względna zmiana wspólnych energii 2,07e−13. Nie porównywano dodatkowych
  kolumn energii regionalnej nieobecnych w starszym wyniku.
- `artifacts/m1-gmres-release-tem-r3-20261018/`: 17,586 s, oba porty,
  E L2≈0,495%, B≈0,521–0,536%, kwadratury4/6. To niezależny mały filtr
  analityczny, nie potwierdzenie pełnej anteny.
- `artifacts/m1-antenna-resident-fp64-20261018/`: natural exit0, bez OOM,
  complete=true, 151 iteracji, 1089,964 s. `root-analysis.json` przechowuje
  analizę z SHA logów, pól, faz i port-S; `fields.json` potwierdza snapshoty.
  To historyczny pomiar wykonania, nie kwalifikacja dokładności. Późniejsze
  próby korekty EXP13/14 nie ukończyły solve; ich końcowe iteracje są nieznane.
  Szczegóły: [korekta referencji](reference-correction.md).

| Faza pełnej anteny | Interwał hosta | Peak logicznych alokacji managed |
| --- | ---: | ---: |
| Setup przestrzeni | 7,52 s | 0,50 GiB |
| Początek operatorów do preconditionera | 5,24 s | 7,92 GiB |
| Przygotowanie preconditionera | 54,85 s | 23,52 GiB |
| GMRES do zwolnienia bazy, z diagnostyką residuum | 950,96 s | 54,74 GiB |
| Zwalnianie bazy | 0,181 s | live spada 54,67→29,26 GiB |
| Postprocessing przed snapshotem | 7,84 s | 44,79 GiB |
| Zapis snapshotu | 0,070 s | 44,62 GiB |

Same wektory V mają raportowany logiczny rozmiar 27 822 435 520 B
(155 wektorów). Spadek liczników managed wynosi 27 283 936 768 B; nie należy
utożsamiać tych liczników z fizyczną rezydencją lub automatycznie uznawać ich
za identyczne kategorie alokacji. Zwalnianie usuwa nakładanie V z postprocessingiem,
ale nie zmniejsza szczytu **wewnątrz** GMRES.

Cgroup peak 57,72 GiB, sampled VRAM procesu 4,89 GiB, min. host available 11,98 GiB.
cuDSS peak 7,52 GiB już zawiera się w managed: nie dodawać tych peaków.
Mały sampled VRAM nie oznacza, że całe obliczenie mieści się w 5 GiB:
UVM migruje dane, a pomiar okresowy nie łapie każdego krótkiego szczytu.
Native RSS 6,4 GB również nie obejmuje całego kosztu UVM.

Timery Palace w tym runie: KSP268,35 s, preconditioner603,23 s,
coarse79,57 s. Są rozdzielane przez stos `BlockTimer`, nie należy dodawać
ich do obejmującego je interwału GMRES 950,96 s. Sama akceleracja coarse solve
nie rozwiąże większości kosztu. `Disk IO` 21,50 s jest kategorią wejść/wyjść
Palace (m.in. mesh i diagnostyka), **nie bazą solvera na dysku**.

## Granica jakości i następny krok

VSWR P2=1,672123. Jawne ponowne zastosowanie A daje raw
||b−Ax||/||b|| = 0,1252666005. LEFT sprawdza ||P(b−Ax)||/||Pb|| = 9,956397e−7;
oba pomiary używają FP64. Ich iloraz≈125815 pokazuje, dlaczego stopping
norm nie wystarcza do oceny pierwotnego równania. Raw nie jest bezpośrednio
procentem błędu pola, ale również nie można go zignorować przez zgodność VSWR.

W chwili tego historycznego runu pozostawały M1.2/M1.3: kontrola niezależna
od preconditionera i porównanie całych pól względem lepiej rozstrzygniętego
rozwiązania. Późniejsza referencja RIGHT i kwalifikowany solve W.3 zamknęły M1
w zakresie [checkpointu](milestones/M1.md). Nie promować FP32/TF32 na podstawie
samej kompletności dawnego runu ani nie pomijać aktywnego M2 FEM–BEM.

Nie wyliczać speedup względem historycznych disk runów: inne polityki
pamięci i tracing nie tworzą pary porównawczej. Pełny wynik jest pierwszym
dopuszczalnym punktem wykonania FP64 po wycofaniu disk basis.
