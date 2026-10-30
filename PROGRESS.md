# Kampania optymalizacji faz — zakończona zakresowo, 2026-10-30

OP/PRE scalone lokalnie w130c7819c. Source root odpowiada testowanej binarce:
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
