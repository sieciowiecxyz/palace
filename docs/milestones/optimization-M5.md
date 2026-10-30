# M5 — mniejszy i tańszy preconditioner

Status: **COMPLETE ASSESSMENT**, EXP95–104,2026-10-21. Mixed coarse zachowany
jako obiecujący opt-in; bez globalnej promocji. Następny etap: [M6](M6.md).
Bramki M5.1–M5.6 w [MILESTONES](optimization-contract.md).
Dodatkowy zakres algorytmów: [research](M5-research.md).

## Punkt wyjścia

M4 pełna antena602,944s/oba porty; jeden setup,44/35iter, peak managed53,084GB,
cgroup56,833GB. To jedna para, nie mediana. cuDSS FP64 nadal25,008GB i przekracza
16GB VRAM; dotychczasowe profile wskazują koszt apply PC i ruchu UVM.
Profil wczesnego/late okna nie jest rozkładem całego zadania.

## Następna kolejność

1. Odczytać przypięte cuDSS0.7.1.4/API i istniejące AMS/GMG w Palace;
   audyt trybów hybrid memory/execute vs UVM. Bez nowej zależności/rebuilda deps.
2. Zbudować rachunek czasu i working set. Rozdzielić analizę/factor/apply,
   iteracje, migracje i pomiary; nie sumować nakładających się aktywności.
3. Wybrać jedną nową hipotezę zmniejszającą working set PC. Najpierw malutki
   rzeczywisty API/operator probe, potem tiny/medium/full po gate. Nie powtarzać
   odrzuconych FP32 faktorów bez scaling/korekcji/stagnation guard/fallback.
4. Ocenić AMS na właściwym operatorze pomocniczym; nie zakładać SPD zespolonego
   Maxwella. Jeśli potrzebny zmienny PC/FGMRES, sprawdzić pamięć wektorów Z.
5. Ograniczona ocena FDTD/CUDA według M5-research; najpierw koszt siatki/CFL.

Tylko lokalna5070Ti16GB/96GBRAM, medium i frozenK, te same limity/cache.
Bez Rust/FieldCraft/GUI/CAD, płatnego compute ani zamykania aplikacji.
Obecny FP64 coarse zachowany jako fallback; żadnych nowych defaultów bez M7.
EXP95–96: actual hybrid memory prototype i dwa budżety PASS API/medium/W.3P2,
ale nie ma net speedupu: UVM350,371s vs4GiB363,872s/6GiB511,069s. REJECT
jako aktualna optymalizacja; referencja/fallback bez zmian. Coarse63,41→31,44s,
PC poza coarse97,15→139,71/248,49s. Podejrzenie presji rezydencji wymaga profilu,
nie dowodzi go samo ustawienie budżetu. [Pełny raport](../native-hybrid-memory.md).
Był to pierwszy wynik M5, po którym oceniono AMS i mixed precision zamiast
dalszego losowego strojenia budżetów hybrid.

EXP97: istniejący GPU AMS na realnym shifted PC, fixed2cycles, actualCUDAprofile
PASS. Tiny/medium jakośćPASS, lecz W3P2 nie ukończył się w900s (iter264,
recurrence1,501e−3; brak końcowego raw/pól). REJECT obecnej konfiguracji; nie
kwalifikować partial29,32GB jako zysku anteny. [Ocena](../ams-assessment.md).
Kolejna próba po AMS: [skalowany complexFP32 z FP64korekcją](mixed-coarse-plan.md).
EXP98–101: nowy native complex FP32/scaling/dwie FP64 CUDA korekcje przeszedł
API, W.2 trzy częstotliwości/oba porty i W.3 3,50GHz/P2. Jedna para W.3:
339,362→273,843s,35/35iter; cgroup56,027→45,376GB, pola/S/VSWR/raw PASS.
Zachować jako opt-in, bez globalnej promocji. Nie jest to dawny realny shim.
EXP102 M5.5: actual late30:2 CUDA/UVM profile PASS,251,125→186,635GB transferów
w obu kierunkach (−25,68%), okno12,944→10,530s. Pełny koszt pozostaje EXP100;
[metoda i granice](../mixed-coarse-profile.md). M5.5 ocenione, nie nowa RFwalidacja.
EXP103–104 M5.6: [source-based budżet i API gprMax](../fdtd-budget.md). Nowy
eksport bbox powiązany hashami z mesh: już podzbiór PCB/feed wymaga36,144GB
GPUbase w HSG0,1mm. Nesting public API odrzucony; brak zweryfikowanego direct
fine-fine łączenia siblingROI dla cienkiego ciągłego coaxu. REJECT bezpośredniej
integracji na16GB; mały CUDA test NOT RUN po nieprzejściu resource/API gate.
Nie jest to uniwersalna negatywna ocena FDTD. M6/M7/W.4/W.5/mediana pozostają.

## Audyt zamknięcia według kryteriów

| Kryterium | Dowód i rozstrzygnięcie |
|---|---|
| M5.1 zgodność/tryby/budżet | Przypięte CUDA12.9.1/cuDSS0.7.1.4/MFEM4.9, native UVM vs hybrid-memory/execute; actual min/query/limit i dwa wykonane budżety w EXP95–96. Hybrid netperformance REJECT, default bez zmian. |
| M5.2 uzasadniony PC/AMS/GPU | Realny shifted pomocniczy PC, fixed2 GPU AMS; tiny/medium i actualCUDA profile PASS. W.3 timeout900s FAIL, jawny REJECT; partialpeak nie jest oszczędnością. |
| M5.3 nowy mixed mechanism | Skalowany complex GENERAL FP32 LU,2fixed FP64 CUDA korekcje, overflow/finite/residual guards i FP64 fallback; independent knownsolution/negativecontrol, bez adaptivePC. EXP98–101. |
| M5.4 W.2/W.3/K/koszt | W.2 trzyfreq/oba porty +W.3P2, pełne zakończenia/fields/S/VSWR/energy/raw PASS;339,362→273,843s, cgroup56,027→45,376GB. Jedna para, opt-in; W.4/W.5 i globalpromocja niezaliczone. |
| M5.5 profil/Amdahl | Pełne exclusive timery EXP100 i strict selectiveCUDA/UVM EXP102, source clock/overlap/enumy sprawdzone.251,125→186,635GB w dwóch późnych iteracjach; bez ekstrapolacji na pełne transfery. |
| M5.6 FDTD/CUDA research | Pin gprMax/licencja/sourceCUDA/ports, actualgeometry bounds, fields/IDs/PMLpadding/CFL/window/bothports budżet i publicHSGAPI. Direct port REJECT na resource/API gate; solverbenchmark NOT RUN. Custom multiROI/subcell poza wykazaną wykonalnością, nie ukryty PASS. |

Root receipts i odtwarzanie są w powiązanych raportach; brak nowej zmiany
mesh/medium/Tol, płatnego compute, swap/SSDworkspace i rebuilda dependencies.
Zamknięto **ocenę M5**, nie cały goal ani fizyczną walidację anteny.
