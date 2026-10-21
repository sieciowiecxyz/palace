# Walidacja lokalnego forka

Wykonuj z katalogu głównego repo. Narzędzia wymagają Linux i Python 3.11+; upstream ma szersze platformy, ale lokalny runner nie został na nie przeniesiony.

## Szybkie kontrole

Nowy opt-in `--native-coarse-fp32`: API CUDA/boundary/overflow, W.2 trzy
częstotliwości/oba porty i W.3 jedna para PASS w EXP98–101. Regresje parsera
odrzucają niewłaściwy dtype, brak korekcji i cleanup. Komendy i zakres jakości:
[scaled mixed coarse](milestones/mixed-coarse-plan.md). Nie oznacza W.4/W.5/M7.
EXP102 dopuszcza mixed partialprofile, ale nie pełną RFkwalifikację; nowa
regresja rozdziela1setupdiagnostic od6pełnychsolve. EXP103 cztery testy budżetu
FDTD sprawdzają typy/CFL/HSG/invalidinputs, nie uruchamiają gprMax. Pinned suite139PASS.

```sh
python3 -m unittest discover -s tools/tests -p 'test_*.py' -v
sh .agents/skills/docs-garden/scripts/test.sh
sh .agents/skills/docs-garden/scripts/check.sh
git diff --check
```

Testy narzędzi mają wykrywać uszkodzoną siatkę/konfigurację, niekompletny wynik, stale binaries i błędy cache. Nie są testem matematyki FEM.

## Rzeczywisty build i cache

```sh
python3 tools/dev.py build --jobs 8
python3 tools/dev.py build --jobs 8
```

Drugi build powinien pozostawić bez zmian hashe binariów i ominąć kompilację niezmienionych jednostek. Sprawdzić log/manifest, nie tylko czas. Oddzielny test cache kompilatora polega na odbudowie jednego własnego obiektu przy zachowanym ccache; nie kasować całego cache ani zależności.

## Smoke GPU

```sh
python3 tools/dev.py run coax-medium artifacts/coax-smoke --seconds 180
```

Oczekiwane: exit 0, sześć ukończonych rozwiązań (3,3/3,55/3,8 GHz, dwa porty), prawidłowe sumy wejść, `result.json: complete=true`, niezależne kontrole norm zatrzymania. Osobno porównać S21 do TEM oraz S do zapisanej referencji. Sam status complete nie kwalifikuje dokładności.

Pierwszy smoke migracyjny z 2026-10-18 ukończył sześć rozwiązań, ale runner zapisał `complete=false`, ponieważ regex nie akceptował dwukropka po `PALACE_KSP_CHECK`. Parser poprawiono i dodano regresję z dokładnym formatem emitowanym przez Palace. Powtórzenie w `artifacts/coax-migration-fixed-20261018/` zwróciło `complete=true`, sześć kontroli norm względnych i exit 0. Szczegóły pierwszego błędu, naprawy oraz porównania TEM/S są w [raporcie migracji](migration.md). To kwalifikuje ograniczony coax smoke, nie pełną antenę ani multi-GPU.

## Pełny przykład i testy upstream

Pełny case `tshaped-medium`: 3,50 GHz/P2, P1 zakończony 50 Ω, ten sam mesh medium. Jego wykonanie kosztuje około kilkunastu minut na docelowym komputerze; nie uruchamiać przy każdej zmianie dokumentacji. Po zmianie numeryki stosować bramki z [planu](speedup.md).

Zachowane testy C++/regresje upstream są w `test/` i opisane w dokumentacji upstream. Nie twierdzić, że cała ich kampania przeszła na podstawie lokalnych testów narzędzi lub smoke. Testy wymagające drugiego GPU oznaczać NOT RUN, jeśli go brak.

## Diagnostyka M1

PALACE_VERIFY_RESIDUAL emituje także PALACE_RAW_RESIDUAL: niezależne ponowne zastosowanie A w bieżącej precyzji, normy b/Ax/b−Ax i dwa ilorazy. Dodatkowy matvec i redukcje są kosztem diagnostyki. Norma relative_action nie jest normwise backward error, a status complete nadal oznacza tylko kompletność. Rezultaty nowych coax smoke FP32/FP64 storage i audyt geometrii: [raport M1](optimization-baseline.md). Nie rozstrzygają zgodności pól całej anteny.

Audyt siatki: `python3 tools/mesh_cost.py examples/tshaped-medium/mesh/pcb.msh --output artifacts/mesh-cost.json`. Regresje sprawdzają różnicę udziału elementów/objętości, zamkniętą powierzchnię i odrzucenie nieobsługiwanych danych. Metoda używa geometrii narożników, nie dokładnej kwadratury zakrzywionych elementów.

## Filtr pola TEM i L2

Pierwszy szybki test: `python3 tools/dev.py run coax-tiny artifacts/tiny-smoke --seconds 60`. Większy coax i antena pozostają odrębnymi poziomami drabiny walidacji. Dla pola: --coax-fields, dla całości domeny: --coax-l2; analizator tools/coax_fields.py porównuje do analitycznego TEM, próbki nie są mylone z całką L2. Dane diagnostyczne nie kwalifikują dowolnego modelu anteny.

L2 pochodzi z MFEM ComputeL2Error, oddzielne real/imag, dwie kwadratury4/6. Testy parsera używają faktycznych jednostek CSV Wb/m² i sprawdzają, że błędny znak B/NaN nie przechodzą niezauważone. Diagnostyka CPU ma osobne czasy i nie jest włączona w rutynowym pomiarze szybkości.

Pierwszy 20 mm run q6/10 nie zmieścił się w 180 s i pozostaje FAIL, chociaż jeden port dał użyteczne L2. Pełne tiny runy spełniły z góry ustalony filtr. Dokładne wyniki: [M1](optimization-baseline.md). Aktualna kontrola: 95 unittestów narzędzi PASS w przypiętym środowisku oracle (systemowy Python: 79 PASS/16 SKIP); pełna kampania testów C++ upstream nadal NOT RUN.

## Snapshoty i porównanie masowe

Regresje snapshotów pokrywają SHA/format/nieukończone referencje, inną fizykę i pokrycie regionów oraz NaN/duplikaty. Rzeczywiste tiny testy: snapshot FP64→FP32, historyczne porównanie disk→resident (storage disk jest wycofany), domyślny background worker i kontrolowane B×1,02 (oczekiwany FAIL jakości). Native pliki E/B single-rank little-endian są chronione sprawdzaniem źródłowego config i zależności. Szczegóły: [kontrola pól](field-validation.md).

Historyczne referencje/porównania dużej anteny z disk basis są **REJECT** według wymogu RAM/VRAM. Wcześniejszy resident FP32 attempt zatrzymał guard. Resident FP64 EXP12 ukończył jeden punkt, lecz raw relative residual≈0,1253 i nie był zakwalifikowaną referencją dokładności. Korekty EXP13/14 zakończyły się limitem 1800 s; ich puste `field-comparison.json` oznaczają brak pomiaru błędu, nie przekroczenie progu. Późniejsza W.3 native complex coarse ma ostrzejszą resident FP64 referencję oraz niezależny 35-iteracyjny solve, który przeszedł zamrożone kontrole raw/S/pól/energii dla 3,50 GHz/P2. To nie jest fizyczna walidacja ani wynik całego pasma. Szczegóły: [natywny complex coarse](native-complex-coarse.md). M1 zakończony po aktualnym CUDA-only profilu i audycie alokacji; dowody i granice w [M1](milestones/M1.md). Nie promowano defaultu. Fazy mierzą logiczne managed allocations, nie fizyczną rezydencję. Zobacz też [audyt pamięci](memory-audit.md), [pomiar faz](memory-phases.md) i [korektę referencji](reference-correction.md).

Opt-in profile CPU/cuDSS, real-block `ComplexCoarseSolve` i zwalniania finalnego solvera są w [profilach referencji](reference-profiles.md); eksperymentalny natywny complex FP64 coarse ma osobny [raport](native-complex-coarse.md). CPU tiny/fallback/native coarse tiny i TEM przeszły filtry. Full CPU oraz historyczny exact real-block full zatrzymały się OOM/host guardem; natywny W.3 full przeszedł kontrolę numeryczną dla jednego punktu, bez promocji defaultu. Nie jest to walidacja produkcyjna całej anteny.

## Analiza alokacji bez GPU

`tools/allocation_audit.py` czyta zachowany trace ≥16MiB; nie uruchamia solvera. Regresje w tools/tests/test_allocation_audit.py obejmują peak w tej samej chwili, pointer reuse, przypisanie późniejszych ramek stosu, interleaved stdout oraz odrzucanie uszkodzonego/starego formatu. Reprodukcja i ograniczenia: [audyt pamięci](memory-audit.md).

## M2 — niezależny Maxwell

Aktualny suite:112testsPASS w `build/m2-oracle/venv/bin/python -m unittest discover -s tools/tests`;
systemowo96PASS/16SKIP z brakuSciPy. Testy parowania obejmują kwadraturę
trójkąta, rank/diagonalnąskalęGram i użycieobuDOFtransformwcałcefizycznej.
Testy obejmują własne PEC/dielectricMie/optical theorem/Rayleigh/topologia,
mount aliasu Python i complex H-matrix/coverage/exact overlapping support.
Testy H-matrix są opcjonalne przy braku NumPy; przypięty oracle ma je zawsze.
Rzeczywiste PECruny trzech siatek wykazały zbieżność i1%PASS dla1920RWGDOF;
CPUcomplexSVDfar/near-exact+CUDAapply przeszły osobne błędy względne/rawOriginal.
Per-block CUDAapply wolny i niepromowany; native2kernel/manifestSO/CPU-basis
GMRES i dielectricPMCHWT przetestowane w [EXP25–29](maxwell-native-dielectric.md).
Regułaobjętości jawna, staregeometrieFAIL zachowane. ActualMFEMND1interface
w[EXP30–31](maxwell-coupling.md) ma map/pair/energyPASS i całkowity1%fieldgateFAIL.
EXP32 ma3prawdziweCPUrunyparowania, odrzuca inwersjęGprimal i wskazujeGdualRBC;
niejest rozwiązywaniemMaxwella aniND2mortar. [EXP33](maxwell-nd2.md) sprawdza
actualglobalND2/faceorientations/physicalquadrature i sparseDirichletreference:
1%pólPASS0,151/0,332%, samainterpolacjaH1,468%FAIL. Regresje wejść/topologii/
referencepoints/closedhandle i cacheglobalCpp są w suite. Nie jest to coupledND2,
dielectricFEMtransmission aniantena. [EXP34](maxwell-nd2-coupling.md) wykonuje
coupledND2/BC-RBC i sparseSchur: mortar/localmap/nativeT-K/tinydense/energyPASS,
wholefieldFAIL17,74/15,22→10,07/5,64%. Dwa nowe unitSchur testują niezależny
complexblock i chunking/immutability; rzeczywiste MFEM/Bempp są w runach, nie w mockach.
[EXP35–37](maxwell-trace-duality.md): trace hierarchy i obie dualności, independent BEM refinement oraz fixed-BEM FEM control; transparent E/H<1% na dwóch siatkach. Nowe regresje sprawdzają projekcję/q-order, parent lookup i odrzucanie niepoprawnych flag przed alokacją. Dielectric FEM transmission wykonany jako niezaliczony centroidscreening w EXP38–41; nie kwalifikacja całego pola.
[EXP38–41](maxwell-transmission.md): eps1/2,94 coupled vs same-geometry PMCHWT, niezależne reference-only q/mesh calibration i bez powtarzania coupled solve. ScreeningFAIL zachowany; testy walidują eps/reference-only przed alokacją, weightedcomplexerror oraz płaską refinementB4/closededges/volume/outwardorientation.
EXP42–43:80unitPASS obejmuje dokładność wszystkich jednomianów dodatnich reguł2/5 oraz inputstate/role/level/material/basis guards replay. Dwa realne bounded volume runy są executionPASS, qualityFAIL; root niezależnie przelicza wszystkie normy z NPZ. Korekcja paneli wykonana w EXP44–47 poniżej.
[EXP44–47](maxwell-near-panels.md): nativeT/K i niezależny solid-angle control, ratio2/4, subset i full2240point fineB4correction. Adaptive/cutoffPASS, polescreenFAIL zachowany. Unit85: rotation/translation,childarea/depth/target guards,solidangleoctant/orientation/scale, CLI/fullreplay i inputgeometryrole safeguards. EXP48–53: coarsecorrection wykonane, volume/reference convergence nadal FAIL.
NumBa actualnopython/native/NumPy parity wEXP50; EXP51–53 fullsavedreplay.
88unit w pinned env obejmuje jawne pętle kernela/DFS, ale używa identitynjit
w unitach: to nie test LLVM; dowód rzeczywistego JIT jest wyłącznie wEXP50.
[EXP54–58](maxwell-fem-refinement.md): epsilondefaults/invalidflags unit,
locator strictowner/face/outside/NaN/chunking unit; actualanalyticF2/F3 i defaultregression,
coupledF3 oraz fixedpointreplay. Fieldnorm/referenceconvergence nadal niezaliczone.
[EXP59–69](maxwell-stream.md): stream NumBa actualnopython vsnative/cache/incremental,
matched3queries, własnaF3volume degree2/5, radius/near/farcontrolsdegree2.
Unit porównuje pętle/DFSstats z NumPy i odrzuca nieużywane flagi przedalokacją;
nie kompiluje LLVM. Degree5near/farvariants i FMMNOTRUN, field/reference/degreeFAIL.
Nie testowano pełnegoGPUsolveraanianteny nowym silnikiem. Źródła/limity w
[oracle](maxwell-oracle.md). Palace nie był zmieniany/przebudowywany.

## Eksperymentalne Q-workspace

Probe dwóch operatorów i późniejszy pełny coax-tiny/TEML2 przeszły; Q-pool nie jest promowany z powodu braku oszczędności na tiny. Pierwszy baseline zakończony OOM/hostguard pozostaje FAIL. Regresje Pythona sprawdzają preflight RAM, sourceSHA, stale/tampered manifest, granice HYPREseed i jednostki/filtrowaniePID w pomiarze GPU. Odtworzenie oraz scope: [Q-pool](ceed-qpool.md), [pula HYPRE](hypre-pool.md). Nowa pełna antena FP64 jest wyłącznie resident execution reference; antena z Q-pool ani kandydat mixed precision pozostają NOT RUN.

### ExaFMM addon / Maxwell control

Instrukcja i frozen actiongate1e-6: [maxwell-fmm.md](maxwell-fmm.md).
`python3 tools/experiments/exafmm_build.py build` zachowuje cache, `check`
weryfikuje receipt; numeryczny `--physics fmm-control --fmm-order 8 --fmm-ncrit 32`
ma120DOF/6GiB/120s i512MiB RAM tmpfs, bez GPU. EXP73 actionPASS nie zastępuje
PMCHWTsolve/field qualification. Regresje stdlib sprawdzają cache/tampering,
walidację flag i odrzucenie pełnego tmpfs; nie importują ExaFMM w testach systemowych.

PMCHWT `--physics fmm-solve` pilot B2/p8..9/ncrit32; opcjonalny
`--fmm-preconditioner near-ilu` bierze sparse singular_part. EXP74–76 executionPASS,
ale solveFAIL independentraw1e-9; nie kwalifikować na podstawie samego residualu
FMM lub Δcoeff. Dwa512MiB RAM tmpfs bez capincrease, exact filesize/preflight
guards; p10NOTRUN ponadcap. [Decyzja M2](milestones/M2-decision.md).

### M3 direct FP32 basis

[EXP77–79](mixed-basis.md): cached shared-header CUDA probe + samebuild
coax-tiny FP64/FP32unpack/FP32direct, actualraw/fields/TEM/S PASS.
`--direct-basis` wymaga FP32 i jest czyszczony z odziedziczonego środowiska;
default/fallback zachowane. Na etapie EXP79 MGSorthogonality/realpath/largercoax/W.3 były NOT RUN;
aktualizacja EXP80–85 poniżej. Nie promować na podstawie samego builda/probe. Cache and binarytamper/deadline
regresje w test_mixed_basis_probe.py, guard FP64/direct w test_dev.py.

EXP80–85 aktualizacja M3: actual libpalace API CPU/CUDA/MGS/faultdetector i W.2
trzyfreq/oba porty PASS, W.3 pojedynczy3,50GHz/P2 PASS/peakcgroup−2,87GB.
[Dowody i scope](mixed-basis-validation.md). W.2 pełnyTEMsweep przekracza180s;
`--coax-frequency` dzieli istniejące punkty bez pomijania portów/kwadratury.
`--coax-sweep` jawnie zachowuje wszystkiefreq z diagnostyką. Testy test_dev.py
kontrolują częstotliwości/mutualexclusion/boundaries oraz jawną kombinację
nativeFP64coarse+directFP32. Realny driverCDI również dla CPUAPIprobe (GPU-built
libceed); buildstub nigdy na runtimeRPATH. Nie kwalifikuje to M7/W.4/W.5.

## M3 — prefetch i selektywny profil, EXP86–90

Aktualny suite115PASS w pinned oracle env; system99PASS/16SKIP. Regresje
obejmują wymaganie direct/CUDA, dodatnie markery per solve i profiler jako
niekwalifikujący RF, capture markers, brak utraty zdarzeń i naturalny cleanup.
ActualAPI CPU/CUDA relink currentnative PASS; prefetch jakościowo sprawdzony
w tiny,3mediumcoaxshards/bothports i aktualnym W.3. [Wyniki/argv](basis-prefetch.md),
[M4](milestones/M4.md) oceniony w EXP94; aktywny [M5](milestones/M5.md). Upstreamfullsuite i W.4/W.5 nadal NOT RUN.

## M4 — reuse i kolejność pomiarów, EXP91–94

Pinned suite124PASS, currentbuild tiny oraz medium3,30/3,55/3,80GHz/oba porty
TEM/wholefields PASS. Pełna antena3,50GHz/bothports control/candidate PASS
raw/S/VSWR/energy/power/wholefields; jedna para681,698→602,944s, nie M7median.
`--defer-postprocessing` ma testy ograniczeń i kolejności store/solver-release/
measure1/measure2; requires --release-final-solver, dokładnie2LP/1f/rank1/fixedmesh,
bez visualization/wave/Floquet. `--port-setup-reuse` liczy faktyczne setupy i CSR.
`--partial-initial-fields` nie rozluźnia rygoru accuracyreference; źródło jest
zweryfikowanym seedem, brakujący port jawnie zerowany. [Dowody](milestones/M4.md).

## M5 hybrid — EXP95–96

127 pinned regressions PASS. Actual512DOF native/realblock2N,2RHS/2updates,
UVM/256/512MiB PASS accuracy≤1,251e−13/cleanup0. Native tiny/medium i W.3P2
4/6GiB raw/wholefields/S/energy PASS; jawne256MiB feasibilityFAIL przedfactor.
SamebuildUVMcontrol wymagany; spadek coarse kernelcost nie wystarcza do promocji,
bo całe zadanie4/6GiB wolniejsze. [Raport](native-hybrid-memory.md).
Siedemfreqsweep/generalizacja nowej geometrii są dodanymi bramkami M6.6/M7.5,
jeszcze NOT RUN; nie zmieniają kwalifikacji starszych artefaktów.

## M5 AMS — EXP97

Tiny/mediumC2 raw/fields/TEMPASS; source i testy pilnują PCMatReal/Shifted,
niezmienionej fizyki/outertol, jawnych2cycles/tol0/devicepolicy i brakuCuDSS.
Tinyprofile0:2 actualHYPRE/cuSPARSE CUDA wcoarsephase/strictPASS, umyślniepartial.
AntenaW3P2deadline900sFAIL; nie ma końcowego residuum ani porównania pól.
Nie podnosić deadline/Tol, by zmienić status. [Dane](ams-assessment.md).
