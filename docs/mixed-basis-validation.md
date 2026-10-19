# M3 — actual API, większy coax i T-Shaped medium

Status: **W.1/W.2/W.3 PASS dla wskazanego wariantu**, M3 nadal ACTIVE.
Zmierzona korzyść: około2,87GB mniej szczytowej pamięci hosta/cgroup w W.3.
Brak wykazanego statystycznie przyspieszenia; brak kwalifikacji W.4/W.5.
Prototyp i implementacja: [mixed-basis](mixed-basis.md).

## EXP80–81 — rzeczywiste metody biblioteki Palace

`stored_basis_probe.py` kompiluje jeden C++ TU przez ccache i linkuje aktualne,
zweryfikowane libpalace/MFEM/HYPRE. Nie kopiuje kerneli ani nie przebudowuje solvera.
EXP80: compile PASS, link FAIL — driverless builder nie miał libcuda.so.1
wymaganej przez GPU-built libCEED. Poprawka: toolkit driver stub tylko podczas
linkowania, bez stub rpath. Runtime CDI dostarcza realny driver również dla
procesu z MFEM Device(cpu); obliczenia tego procesu nadal wykonuje backend CPU.

EXP81 build1,494s, cache repeat no-op. Rzeczywiste CPU/CUDA Dot/AddTo/Pack/Unpack:
10 przypadków0/1/1009/65537/131071, real+complex, źródło nadpisane po Pack
(brak aliasu), błędna koniugacja31+i odrzucona wobec poprawnego31-i. Wektory
zerowe i końcówki partycji przechodzą. Relative dot max1,09e-13 CPU/2,17e-14 CUDA,
axpy0 względem legacy na tych samych quantized danych. Bramka1e-12.

Rzeczywisty MGS16wektorów/4097DOF: Gram max2,724e-9, projekcje po normalizacji
max6,309e-11, Δwektor legacy/direct CPU<=2,475e-16,CUDA<=9,015e-17. Bramka
Gram/orth2e-7, Δvector1e-12. Jedna ranga; nie dowodzi niemal liniowej zależności,
obsługi wielorangowej ani dowolnych skal. CPU0,191s/RSS309MB,CUDA0,595s/RSS511MB;
GPU HYPRE initial pool256MiB, runtime6GiB/4CPU/60s/noSwap, wyłącznie RAM/VRAM.

```sh
python3 tools/experiments/stored_basis_probe.py build
python3 tools/experiments/stored_basis_probe.py run artifacts/new-stored-api --device cuda --seconds 60
```

## EXP82–83 — W.2 pełny coax-medium

Native complex **FP64** coarse w obu wariantach. FP32 jest dopuszczone wyłącznie
z jawnym `--direct-basis`; stary FP32/unpack nadal nie kwalifikuje tej kombinacji.
3,3/3,55/3,8GHz, oba porty, siatka medium bez zmian, RIGHT, tol1e-6, K240.

EXP82 cały sweep nie zmieścił się w180s:4/6solve, **TIMEOUT pozostaje FAIL**.
TEM q4~13,7s+q6~23,2s na solve: pełna kontrola wymaga ponad222s bez solvera.
`native_complex_coarse_applied=false` oznaczał brak wszystkich6markerów;
cztery faktycznie wykonane solve miały prawidłowe native coarse.

EXP83 dzieli pracę na trzy istniejące punkty przez `--coax-frequency`.
W każdym jobie nadal oba porty i wszystkie TEMq4/q6/pola/S, limit180s.
Nie zmniejszono dokładności ani zakresu; `--coax-sweep` zachowuje domyślny sweep
z diagnostyką, lecz nie łączy się z wyborem pojedynczej częstotliwości.

Wszystkie6jobów PASS:45/47iter, raw<=8,335e-7, maxΔE/B7,554e-7/8,503e-9,
TEM E≈0,494%,B≈0,456%. MaxΔS4,420e-9,ΔVSWR4,732e-9,Δportpower5,948e-9.
Allocation managed peak4,800→4,218GB (−12,1%), lecz cgroup/GPU process peak
nie spadły. Referencje≈114,3s, kandydaci115,3–116,4s: **brak speedupu**.

## EXP84–85 — W.3 T-Shaped medium

Ten sam build, frozen mesh ec56c9a7…, Order2/PA,3,50GHz/P2, P1 terminacja50Ω,
ND11218724/RT15044031. Native complex coarse FP64, RIGHT, K64,tol1e-6,
pool256MiB, releasebasis/finalsolver. Same zapisane pole startowe z M1:
benchmark jest **warm start**, nie cold start; przybliżenie startowe nie jest
referencją jakości. Świeży FP64 dodatkowo porównany z niezależną ostrzejszą
referencją M1 raw7,28e-10: E/B<=6,996e-8/9,886e-8 PASS.

| Wariant | Iteracje | Raw RHS | Czas całego runu | cgroup peak | managed peak |
| --- | --- | --- | --- | --- | --- |
| Świeży FP64 | 35 | 8,35543e-7 | 414,164s | 58,890GB | 55,148GB |
| FP32 direct | 35 | 8,35625e-7 | 409,715s | 56,019GB | 52,277GB |

Kandydat bez restartów. Całe pola/no phase fit: maxΔE/B1,133e-8/1,595e-9,
7regionów (norma obejmuje fazę bez jej dopasowywania; nie jest osobną
mapą punktowych faz w szczelinach). ΔcomplexS3,447e-10,ΔVSWR(P2)6,777e-10,Δportpower5,123e-11,
maxΔenergii1,388e-9; wszystkie frozen K PASS. Różnica impedancji wyliczonej
z S22 przy50Ω:1,832e-8Ω. To kontrola numeryczna, nie nowe dopasowanie anteny.

Szczyt cgroup mniejszy o2870759424B (≈4,87%), managed o2870944768B (≈5,21%).
Model zmiennych buforów:36materializowanych wektorówFP64 vs36packedFP32+
2FP64 workvectors+1MiBpartials daje dokładnie obserwowaną różnicę managed.
Logiczna pojemność V wynosi45wektorów, część nie ma materializowanej alokacji
device; nie utożsamiać jej z36wektorami rozliczonymi przez markery release.
cuDSS peak25,008GB identyczny, zatem to nie zmiana faktorów.

GPU process counter2,147→2,177GB **nie mierzy całej rezydencji UVM**; nie twierdzimy,
że fizyczny VRAM spadł. Min dostępnego hostRAM17,85→20,61GB, guard6GiB zachowany.
Różnica czasu≈1,1% przy jednej parze nie dowodzi przyspieszenia. W.3 pamięć
i jakość są potwierdzone, całe pasma/oba porty anteny nadal niezakwalifikowane.

## Dowody i następne zadanie

Prerejestracje/exact argv EXP80–85 w PROGRESS. Root-verified analizy:
`artifacts/m3-stored-api-root-analysis-20261019.json`,
`m3-coax-medium-sweep-root-analysis-20261019.json`,
`m3-antenna-root-analysis-20261019.json`. Każdy run ma source/native/config/mesh,
command, terminal state, raw i pola. Poprzednie binaria/cache zachowane.

Następne M3: osobna ocena polityki migracji/prefetch dla bazy, bez zmiany
reprezentacji/restartu. Oczekiwany wpływ na czas może być mały: faktor25GB nadal
przekracza16GBVRAM. Restart≥35 nie zmniejsza faktycznie dotkniętej bazy tego
runu; mniejszy restart wymaga osobnego eksperymentu i może zwiększyć koszt PC.
Nie promować globalnego defaultu przed dalszą kwalifikacją M7/W.4/W.5.
