# M7.2 — trzy pary przy 3,500 GHz

EXP215–220, 2026-10-22. **PASS pomiarów i kontraktu K**; użyteczny zysk dotyczy
pamięci. Medium T-Shaped, oba porty, jedna RTX5070Ti16GB/96GBRAM.
Native SHA `a6ec732f11cc7fe920365ba2aae354b68fe97e81f732d5afd4659ed5187c3338`.

## Procedura ustalona przed pomiarami

Prereg był w M7.md/commicie `fa78284`: R1→C1→R2→C2→R3→C3, trzy nowe
procesy i własna referencja pól dla każdej pary. R: full FP64/fresh2setup.
C: direct FP32 basis storage/FP64 arithmetic, scaled complex FP32 LU,
trzy stałe korekcje FP64, port setup reuse. Oba: RIGHT/K64/Tol1e-6,
defer/energy/solver release/snapshots,1800s/60GiB/no swap/hostguard.
Bez profilera, zewnętrznych seedów/PROM/TF, czyszczenia cache lub wyłączania
aplikacji. Zachowano wszystkie próby, żadna nie wymagała ponowienia.

## Wyniki całych zadań — oba porty

|Para|FP64 [s]|Fixed3 [s]|Zmiana czasu|FP64 peak cgroup [GB]|Fixed3 peak cgroup [GB]|
|---:|---:|---:|---:|---:|---:|
|1|743.976|747.515|+0.476%|60.682|46.364|
|2|746.261|752.608|+0.850%|60.689|46.370|
|3|745.458|747.733|+0.305%|60.684|46.361|
|Mediana|745.458|747.733|+0.305% z ilorazu median|60.684|46.364|

Zakresy czasu R743.976–746.261s, C747.515–752.608s. **Mediana sparowanych
zmian czasu wynosi +0.476%**, a sparowanych speed ratios0.99527×. Iloraz
median czasu wynosi0.99696×. To różne statystyki; narzędzie zapisuje obie.
Nie ma wykazanego speedupu całego zadania w tych próbach.

Redukcja mediany peak cgroup: **23.5966%**. Ambicji1.5× czasu/25% peak RAM
nie osiągnięto; do25% RAM brakuje1.4034punktu procentowego. Kryterium celu
dopuszcza użyteczny zysk czasu i/lub pamięci z jawnym kompromisem.

## Gdzie zmienił się czas

Mediany drukowanych timerów native, sekundy:

|Faza|FP64|Fixed3|
|---|---:|---:|
|Setup|166.680|50.159|
|Preconditioner poza coarse|256.687|253.330|
|Coarse Solve|160.074|292.581|
|Linear Solve poza osobno mierzonym PC|79.247|62.916|
|Postprocessing|8.297|15.418|
|Disk IO|19.219|19.160|

`BlockTimer` w timer.hpp przerywa licznik rodzica przy wejściu w zagnieżdżony
blok; te drukowane czasy różnią się od inclusive ranges profilera. Nie
sumować niezależnych median faz, by odtworzyć medianę całego procesu.
Setup i operacje bazy są tańsze, koszt coarse z korekcjami rośnie. To
lokalizuje kompromis; nie dowodzi udziału samych migracji w każdym timerze.

## Pamięć i warunki pomiaru

### Tabela Pareto — zakres obecnego pomiaru

|Profil|Mediana obu portów [s]|Mediana peak cgroup [GB]|Peak managed allocations [GB]|Peak cuDSS allocations [GB]|Globalny peak NVML [MiB]|
|---|---:|---:|---:|---:|---:|
|FP64|745.458|60.684|56.943|25.008|15844–15845|
|Fixed3|747.733|46.364|41.950|13.348|15828–15843|

Koszt wynajmu compute tych lokalnych prób: **0 USD**; koszt energii elektrycznej
nie był mierzony. Czas obejmuje zapis pól i kontrolę jakości. Managed/cuDSS
oznaczają logiczne alokacje, cgroup pamięć hosta, a NVML cały GPU z pulpitem;
kolumny nie są zamienne ani nie dowodzą redukcji fizycznego peak VRAM.

- Początkowe globalne zajęcie GPU2366–2373MiB, host available84.08–84.86GB.
  Tło jest zapisane w telemetry.jsonl; nie badano tu zegarów/temperatur jako
  osobnych zmiennych i nie wyciąga się przyczyn z niewielkich różnic czasu.
- CUDA managed allocation peak56.943→41.950GB, około−26.33%. To rozmiar
  alokacji, **nie fizyczna rezydencja VRAM**.
- Maksimum żywych alokacji cuDSS25.008→13.348GB, około−46.63%, osobna miara
  od cgroup/całego procesu i od samego rozmiaru matematycznych L/U.
- Globalne NVML GPU maksimum: R15844–15845MiB, C15828–15843MiB; obejmuje
  pulpit. Raport per-process2GiB nie obejmuje wiarygodnie całego UVM.
  **Zmniejszenia fizycznego peak VRAM Palace nie udowodniono.**
- Zapisano około7.061GB zwykłych artefaktów sześciu runów, bez swapu lub
  dyskowego workspace solvera. Cache i pliki wejściowe pozostały zachowane.

## Jakość i exact W.3/P2

Wszystkie3pary K PASS,42regionalne wpisy pól. MaxΔcomplexS2.394e-8,
ΔVSWR4.620e-8, względna Δenergii4.963e-8, Δpower5.185e-9.
Max względne E/B4.089e-7/8.734e-8. Każdy kandydat wykonał92coarseapply,
3stałe korekcje, maxcoarseresidual<=9.493e-5. P2 wymagał kontynuacji po
kontroli oryginalnego residuum; finalne raw obu portów<=1e-6, koszt wliczony.
Nie poluzowano tolerancji. Każdy R miał44/44iteracji, C44/45.

W3 numerical coverage pochodzi z wpisów **P2 przy dokładnie3.500GHz**:
7regionów P2 w każdej parze, pełne E/B i originalraw; identyczne fizyczne
terminacje50Ω/config/mesh w obrębie pary. Dane P1 są osobnym pobudzeniem.
W3 nie jest tu zastępowane3.55GHz; raportowane czasy obejmują oba porty,
nie single-P2. Proof: `artifacts/m7-w3-P2-in-paired-benchmark-20261022.json`.

## Odtworzenie analizy

```sh
python3 tools/qualify_antenna.py --paired-medians artifacts/m7-median-3500-pair-r1-qualification-20261022.json artifacts/m7-median-3500-pair-r2-qualification-20261022.json artifacts/m7-median-3500-pair-r3-qualification-20261022.json --corrections 3 --output NEW-MEDIAN-RECHECK.json
```

CLI ponownie kwalifikuje prawdziwe pary, nie ufa zapisanemu PASS. Wymaga3par,
identycznego f/config/build/precisionpolicy oraz6różnych ścieżek i nazw
kontenerów. Odrzuca duplikaty, inne częstotliwości/county, FAIL/NaN i mieszanie
z protokołem antyrezonansu. Nie jest to attestation sprzętu po samych nazwach;
w tej sesji sprzęt i wykonanie obserwowano bezpośrednio. Kontrole179Python PASS.

Statystyki: `artifacts/m7-median-3500-three-pairs-qualification-20261022.json`.
Timery/tło/alokacje: `artifacts/m7-median-3500-phases-background-20261022.json`.
Źródła: `m7-median-3500-{reference,candidate3}-r{1,2,3}-20261022`.
W.5 pozostaje osobną kwalifikacją15punktów; geometria/pakiet i końcowy audyt
są nadal otwarte. To nie jest wynik TC ani walidacja fizycznej anteny pomiarem.
