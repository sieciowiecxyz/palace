# Kampania optymalizacji faz — zakończona zakresowo, 2026-10-30

OP/PRE scalone lokalnie w130c7819c. Źródła zamkniętej kampanii odpowiadają testowanej binarce:
`95822ec5...`; biblioteka `048fbfc2...`. Brak ponownej kompilacji identycznych źródeł.

Wynik trzech pełnych par medium1,92GHz/oba porty:
738,280→630,324s (−14,62%), cgroup66,056→57,029GiB (−13,67%).
14par RF niezależnie ponownie sprawdzonych; sweep1,71/2,69/3,80 i inna geometriaPASS.
99testów Python, tiny749OP/55986PRE, CPU/MPI2 fallbackiPASS.

Rekomendowany build: `build/optimization-stages-m4-integration-20261030/native/`.
`scopedqualification.json` potwierdza tylko exact20flags i5testowanych wejść:
Restart1/rank1/OMP1, jeden Point na run. Oryginalny buildmanifestfalse zachowany.
IOcacheDEFER; fizyczny VRAM/UVM transfer niezmierzony; brak globalnegoGPU/MPIclaim.

NativeRestart2smokeFAIL odziedziczonego CSVidxmap; nie poprawiono ani nie ukryto.
Profil odrzuca ten restart. Oryginalne monitorFAIL/recovery i USER_INTERRUPTED2690
zachowano; restartowano tylko przerwany job w nowym katalogu na polecenie użytkownika.

Brak aktywnych symulacji; Strata przywrócona active/running, /health200.
Bez cloud/push. Cudze niezapisane pliki Ampere pozostawiono nietknięte.
Dalszej pracy nie uruchamiać automatycznie: kampania zamknięta.

[Wyniki](docs/optimization-stages/results.md),
[audyt/reprodukcja/rollback](docs/milestones/stages-final-audit.md).
Artefakty audytu: `artifacts/optimization-stages/M6-final-audit-20261030/final-audit.json`.
Pełny poprzedni checkpoint w `progress-before-finalization.md` tego katalogu i historii Git.

## Dodatek: lokalne OpenMP sond — 2026-10-30

Nowe zadanie użytkownika po zakończeniu kampanii; nie otwiera ponownie goal.
Zaimplementowano opcjonalne `PALACE_PROBE_THREADS` / `--probe-threads` (domyślnie 1).
Równolegli wyłącznie wybór kandydatów; MFEM i inverse transforms pozostają serial.

Medium, trzy rundy: konstruktor 1,624826 → 1,564537 s przy 4 wątkach (−3,71%,
60,3 ms). 8 wątków nie poprawia mediany; snapshot 40 816 392 B + maska ok. 1,7 MB.
To nie jest przyspieszenie całego solve ani dowód wydajności na CMP.

Walidacja: standalone 23 736 OMP / 5 928 serial; native 925 OP + 55 986 PRE;
101 testów Python; rzeczywisty konstruktor 12 prób; GPU synthetic E/B relL2
4,91e-14 / 9,53e-14 vs GSLIB, actual team4, globalOMP1. Niezależny przegląd PASS.
Nowy source `1d2f7624...`, lib `41075c4d...`, build `build/probe-openmp-20261030/`.
Pełny RF nowego buildu i CMP: NOT RUN. Stara kwalifikacja M6 nie jest dziedziczona.
Źródła poprzedniej kwalifikacji zachowano w `../palace-opt-integration`.

Dokumentacja i włączenie: [probe-openmp](docs/probe-openmp.md).
Artefakty review: `artifacts/probe-openmp-review-20261030/review.json`.
