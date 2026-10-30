## M4 PASS zakresowo / M5 ACTIVE (2026-10-30)

Combined95822/lib048f zkwalifikowaneOP+PRE: cachedbuild8,43s,749+55986tinyPASS.
PełneM4A/B/C iRFgatesPASS: base737,913s→combined631,171s; OPonly637,483s,
cgroup66,056/57,054/57,041GiB. Nie przedstawiaćjednejpróbkijakomediany.
CPU/MPI2fallbackiPASS (OP38+38/PRE11657+11653), parser-onlybłędyzachowane,
bezpowtórzeńnative. TerazM5prepared12plans:4runydokończeniatrzechpar1,92GHz
+8runów(pary1,71/2,69/3,80GHz+osobnageometria). Input/schemaaudytprzedexecute.
Nowageometria oldM7+2mm zachowujeFR4director, nowesondyzknownP2interiors/FF;
walidacjaalgorytmu, nie zmiana produkcyjnejanteny/reprezentatywnybenchmarksond.
Root nadal referencja0341;integrationcode osobnyworktree, wszystkiepłatneźródłanietknięte.
StrataOFFexplicituser; po pomiarachprzywrócić. M6jeszczenieauditowane.

## M3 CLOSED zakresowo / M4 ACTIVE (2026-10-30)

OP3pary:738,559→637,773s,65,713→57,030GiB, RF PASS. PRE3nativepary:
739,008→731,570s, Mesh−24%, fullpeakRAM flat, RF PASS. PREjednaodzyskananative
completion z zachowanymcontrollerFAIL/events/proof; 2cleanwallpary, nie3.
IODEFER. Source/nativeaktoryniezmienione, ścieżkistatystyk w M3 i ledgerach.
Strata ponownie OFF na jawnepolecenieużytkownika; GPUnativerunszakończone.
NextM4 osobnyintegrationworktree/codecommitsOP+PRE/cachedbuild/regresje;
combined vs base i OP, potem M5 sweep/drugageometria i M6 rekomendacja.
FizyczneUVMtransfery/residency niezmierzone: nie twierdzićoVRAMsavingzsamegocgroup.

## GPU ponownie zwolnione; M3 PRE ostatnia para przygotowana (2026-10-30)

Użytkownik jawnie polecił wyłączyć Stratę i kontynuować; service inactive/dead0,
80GiB RAM available, bezswap. Nie obowiązuje już poprzednia blokada StrataON.
Monitor end-race poprawiony failclosed; 91 testów PASS i niezależny review PASS.
PREpair2 nativeexit0 udowodniony events/metadata; jawny offline supplemental
completion-recovery.json + pair2-rf.json PASS, pierwotny FAILf543... zachowany.
Wall tego kontrolera nie jest clean wall sample; nativePalaceczas739,007857s ważny.
Żadnego powtórzenia obliczeń. PREma2paryRF PASS,6plannedoriginaltylko4nativewykonane.
Świeże pair3r2 A→B po fixie, stare pair3plany NIE wykonywać (runnerSHAinvalid).
Źródła/native/config/mesh bez zmiany, nowy prereg opisuje wersje monitora.
M4/M5 pending, OP3pary zakwalifikowane. Po pomiarach przywrócić Stratę.

## Użytkownik włączył Stratę — GPU zarezerwowane dla inference (2026-10-30)

Na jawne polecenie użytkownika uruchomiono localai-nvfp4.service:
active/running, PID2369460; http://127.0.0.1:8081/health HTTP200.
Nie uruchamiać kolejnych symulacji ani samodzielnie ponownie zatrzymywać Straty.
IO może dokończyć wyłącznie Python/CPU fix monitora i przygotowanie offline recovery.
PRE zatrzymane po pair2-A-off monitoring-only FileNotFound cgroup po nativeexit0;
authoritative Podman diedexit0 i pierwotny FAIL zachowane. Nie ponawiać native.
Pair3 PRE i M4/M5 czekają na ponowne zwolnienie GPU przez użytkownika.
Cel optymalizacji pozostaje aktywny; gotowe trzy pary OP RF/PERF PASS zachowane.

## M3 — RF checker i przegląd OP zamknięte (2026-10-30)

81 Python testów PASS. Root+niezależny OP review RFcheckera i source-unitproof PASS;
wszystkie3pary RF ponownie przeliczone read-only PASS. Doc-onlyOPcommit abef4eb09.
Unit-test isolation correction: initialmockfulltest przy aktywnym PREtrafił na live
hostlock (właściwa odmowa), test-onlyhostlock w /dev/shm; realexclusiveflockregression
zostaje. Brak zmiany runner/helper/solver podczas aktywnych runów.
PREpowtarzanepary w toku, M4/M5 pending. Patrz operators-m3.md dla tabel i ograniczeń.

## M3 — OP trzy pełne pary PASS; PRE w trakcie (2026-10-30)

OP mediana Palace738,559→637,773s, cgroup65,713→57,030GiB;
trzy sparowane redukcje czasu12,04/13,65/13,64%, wszystkie RFgates PASS,
6runów po85iteracji. Pełne próbki i rozrzut w M3-OP06-full-20261030/repeated-performance.json.
To lokalny rank1CUDA/UVM medium1,92GHz, nie uniwersalnyGPU/MPIclaim.
PRE pair1 PASS:738,250→731,226s (−7,024s), Mesh28,121→21,375s,
fullpeakRAM praktycznie identyczny; RF PASS. Przerejestrowane dwie kolejne pary
wykonuje PREagent. RootRFchecker/testy nowe, runner/helper niezmienione w czasie jobów.
System get_goal potwierdził active prawidłowyobjective; stare paused wpisy historyczne.
M4 integracja i M5 sweep/drugageometria wciąż NOT RUN, rootCPP nadal0341.

## M3 — pierwsza pełna para OP PASS, powtarzalność jeszcze NOT RUN (2026-10-30)

Matched b834/bc7 medium1,92GHz/oba porty, kolejność B→A, beztrace:
Palace738,7508→649,8348s (−12,04%); cgroup65,709→57,027GiB.
85iteracji w obu; rawrelative≤8,34e-7. RootRFchecker PASS:
maxΔcomplexS1,736e-8, maxΔVSWR3,128e-8; pola/probes i FF PASS,
bilansmocyresidual≤0,000216W i FF/fluxerror≤1,259%. Exactconfig/mesh/outputs.
CoarseCSRpatternidentical, valueshashdifferent: brak deklaracji bitwiseequivalence.
Dwa dalsze sparowane runy przygotowane AB/BA; żadnego promote po jednej parze.
Artefakty M3-OP06-full-20261030/pair1-{rf,execution-summary}.json.
Root source nadal0341, prototypyoddzielne; PREfull NOTRUN; M4/M5 pending.

## Bieżący checkpoint — M2 CLOSED / M3 ACTIVE (2026-10-30)

OP `15045a30a`, PRE `2ab140620`, IO `2e1150c7e`: trzy lokalne commity,
własne worktree czyste; C++ prototypy nadal NIE zmergowane do root.
Matched OP source b834/libbc7: operatory 113,196→12,166 s; przygotowanie
166,716→65,568 s; peak cgroup 12,742→3,633 GiB. Jedna para, bez solve.
GPU replay E/B 164 sond i 492 complex składowe/pole PASS: relL2
4,9133e-14 / 9,5320e-14; CUDA witness1200/managedtype3, exact strided
patterns, firstHostRead15,117/19,852 ms. To syntetyczne FE, nie RF.
PRE singlepair 53,361→46,025 s /55986tiny PASS.
IO actual production parser19,040→17,000 s; cold34,049/warm0,441 s;
≥22 identycznych loads do zwrotu: DEFER auto cache. Strict representation PASS.

Nowy bounded full stage istniejącego runnera: 61 testów Python PASS + archived
REF completion PASS (2 solves/85its/maxrawrelative8,334129e-7). Rootreview PASS;
checker nie zastępuje A/B RF. Następny krok nieprofilowany OP 1,92 GHz/oba porty,
exact same build i output, później PRE, powtarzane pary i M4. Actual fullRF NOT RUN. Dwa dokładne plany pair1 B→A przygotowane w M3-OP06-full-20261030.
Strata inactive/dead0, brak cloud. System goal zachowuje rzeczywisty stan panelu;
repo Mode goal/Active M3. Nie sumować niezależnych oszczędności przed combined test.

## Bieżący M2 — rzeczywiste zyski przygotowania, RF jeszcze NOT RUN (2026-10-30)

OP06 po negatywnym141/164 i3nieudanychinitialguess: boundedK128/ONEcenterpass
odnalazł23braki w0,61s, wszystkiepozapierwotnymMFEMsąsiedztwem—udowodnionaprzyczyna.
Nowysharedhelper/prototype tylkoactorbranch: sourceb834/libbc7a,749assertions/10casesPASS
(old664+85adversarial:128distractorscap/fallback,ties,outside,boundary,ND/RT/H1complex).
ACTUALproductionmediumoperators-only:164/164selectedmfem,141+23rescue72trials,
locator1,623s bezGSLIB, Ops12,166s, Total65,568s. Cgrouppeak3,63GiB (constructoronly),
GlobalGPUmax7952MiB nieprocesspeak. History115s/169s innybuild; nowySAMEBUILDcontrol
przygotowanybaseline-medium i oczekuje. PełnyRF/actualfields/speedupfullsimNOTRUN.

PRE03actualsinglewarmOFF/ONpair: Total53,3609→46,0250s(-13,75%),
Mesh27,7696→21,1045s, cgroup2,3077→1,8349GB(-20,49%);55986tinychecksPASS.
NiefullRFpromotion. Native493d/source02dd, opt-inrank1directonlyactorbranch.

IO06 pierwszafullcoldstrictFAIL33,77s zachowany. RootznalazłoficjalneMesh.PreserveNumberingMsh2
(Gmsh4.15.2default0); sparse/permutedtinyreprooldFAIL→explicit1strictPASS, bez poluzowania.
NowydurableSemanticMismatch witness przedcleanup. CorrectedONEfullcoldPASS:
source355110567B→binary205675032B hashd91077...; wszystkieIDS/P2conn/nodebits/groupssame,
cold34,049s peak2,40GiB; ONEHIT0,441s bezGmshAPI/bezwrite. Cachetylkoordinaryinput,
noSSDsolveroffload. ActualMFEMmediumspeed/equivalencepending; tiny22986assertionsPASS.

Rootcommonhostlockfixedperuser(/run/user/<uid>) cross-worktreeexclusiveflocktestPASS;
Featureflagsrecordedcanonicalsource/build/config. Metadata-mtime alignment helpersource
hashverified400unchangedfiles avoids110needlessTUs, nativebuildrescue1CPP4,62s.
ROOTCPP nadalM1reference0341, prototypyNIEzmergowane. Strataoffforcampaign/userconsent,
allownedjobscontainersstoppedatsnapshot, nocloud. NextSAMEBUILDOPcontrol, IOnativemedium,
independentsourcereview thenM3fullRF+unprofiled pairs. Nie zaliczaćM2/M3 za samczasfazy.

## Bieżący M2 — trzy odrębne prototypy, 2026-10-30

OP06: freshnative8854/libfb3d,664assertions/5casesPASS. Actual164probe medium
kandydat NIE daje speedupu: MFEMFindPoints~0,995s nie znajduje wszystkich punktów,
więcbezpiecznywholebatchfallbackGSLIB104,33s; Total169,13s. Niepromowany.
Następna falsyfikowalnapróba: osobnygeometry-onlytool zsameproductionloader,
missingIDs i3istniejąceinitialguessmetody wjednymwczytaniu; bez104sfallback.

PRE03: native02dd/lib493d,1rankdirectParMesh+Finalize bezASCIIroundtrip i bez
GeneratePartitioning(1) adjacency.55,986assertionsPASS/0,71s. Pierwszytest29,826
miałjedenFAIL: błędnezałożenie CheckRefinementFlags poUniformRefinement;
referencealsofalse0/0, rawperTetflagsidentical. Test-onlycorrection zachowuje
wszystkietolerancje i dodaje reFinalizebothvalid1/1. Produkcyjnykod bez zmian.
Nativebuild8,07s. Przygotowane rootdokładne2plany mediumpreprocessOFF/ON; wykonaniepending.

IO06: pinnedMFEMreader supportsbinaryMSH2.2; tinyGmshP2semanticsbits/connectivity
physicalnamesPASS130nodes100elements (ASCII11896→binary9403B),7testsguardPASS.
NativeMFEMequivalence/medium/timeNOTRUN. Limitdefault4MiB, żadnej dużejkonwersji.

Naprawaharnessu: jedenniezależny odworktree hostlock /run/user/<uid>/,
regresjarzeczywistegoflockdlasourcesA/BPASS. Dwa jawneprototypefeatureflags
wspólnyrunnerwithcanonicalfingerprints. Cache metadatarepairunchangedsources
110→15TU,42,76sbuildOP; nowyhelperstage_align_mtimes.py2testsPASS i docs/build.
Nie ma nowychRFkwalifikacji ani promowanego speedupu. ROOTniezawieraprototypów
actorCPP, tylko narzędzia i dowody. Strata nieaktywna za zgodąnakampanię; cloudwyłączony.

## Aktywny checkpoint — M1 CLOSED / M2 ACTIVE (2026-10-30)

M1 Solhighdocs-garden i rootreview PASS po doprecyzowaniu IO06gate, zamknięciu stanówPRE E08/E09 i czasachR2; pokrycie99,80%, operatorgap0,024%; ta sama binarkaR2 traceON/OFF
169,0445/168,9795s(+0,0385% w jednej parze, nie statisticalguarantee).
Przyczyna104,52s: GSLIBSetup (CPU104,31s). FindPoints0,0019s. Curvature2,
1,700,660tet i164sondy → conditional183,67Msampledpoints/4,11GiB coords logical,
nie zmierzony peakVRAM. NadalFEM objętościowy; to locator geometrii, nie nowy wavesolver.

PRE Partition19,42s i MFEMparse18,64s prawie1CPU; IOtimer obejmuje parser,
nie dowodzi wolnegoSSD. CSV nativeN16/N32 write0,85/2,38ms, 76,6/282,2kB,
1920assertionsOFF iONPASS, normal182PASS; writer opt odłożona. Microtrace narzut~16,7%
małego3msworkloadu; profiler nie jest włączony do pomiarów wydajności prototypów.

M2wybór: OP06 tańszy dokładny locator; PRE03/04 potwierdzić możliwośćrank1fastpath;
IO06 binarny/cacheinput zachowujący order2/topologię/attrs (cold conversion liczony).
Każdy zaczyna od API/source i cheaptest; brak sensownego patcha dozwolony REJECT/DEFER.
NowyR2native0546c1cf/source0341e500, CPUtiny48PASS, stageonlymediumPASS; RFNOTRUN.
Strata zatrzymana za zgodą na kampanię, wszystkie Palacekontenery posprzątane.
Następnie trzySol6.1high na osobnychbranchach z aktualną wspólnąbazą; buildslotyroot.

## Aktywny checkpoint — M0 CLOSED, M1 ACTIVE (2026-10-30)

Root sprawdził natywne raporty i zamknął M0.1–M0.4 w jawnym zakresie.
Solhighdocs-garden PASS po korekcie historycznegoM1 i jawnego timergap0,0561s.
35 Python PASS w root po finalnym rozszerzeniu runnera, native
operator CPUOMP1 48assertions, CSV182assertions/8cases. Tiny2stops i pełna siatka
mediumGPUoperators-onlyPASS: elapsed167,685s, Palace166,2728s,
Init6,4594/Mesh27,7484/Ops113,3123/IO18,6966; Setup/GMRES/PC/FF/post0.
Sourcemanifest131d5da3..., libd1887e64..., config9f068..., mesh2af1...;
18bazowychflagśrodowiska preserved, OMP1/nativeFP64complex/pool256, brakRFclaim.
323próbkiGPU mean0,1269% median0 max9%, globalpeak6276MiB (nie processUVMpeak),
cgrouppeak13657325568B, hostfree>=70,97GB. Wszystkie kontenery posprzątane.

Rootreviewknownpre-exec harnessfailures zachowane: libcuda stub, OCIbind/CDIconflict,
globalLDpreload; poprawione scopedpreload/CDIonly z regresjami. OMP2allocatorcrash
obecny także frozenM7r3: OP05TODO, bez zmiany productionthreads lub solverprecision.
Nowy diagnostic build nie zastępuje zamrożonego RFbaseline.
ActiveM1: podfazy hostmesh/FE/assembly/serializacja, bez profilowania całego solve.
Następnie pomiar narzutu, wybór konkretnego kandydata dla 3ścieżek. Dotychczas brak
nowej optymalizacji ani zmierzonego speedupu; wyłącznie szybsze narzędzia badań.
Strata zatrzymana za zgodą użytkownika na czas kampanii; po pomiarach przywrócić.
System goalpanel nadalstarypaused; repo goalaktywny na jawne polecenie użytkownika.

## M0 — review i pierwszy slot cachedbuild (2026-10-30)

Trzyśrodowiskowe kontrole root21PythonPASS w0,026s; docscheckerPASS.
SolhighI/O wykonał docs-garden: bez blokującego błęduC++; wskazane nieaktywneINDEX
poprawione. Weryfikator stopuoperators ma zakres obecnego fixture lumpedports;
waveport setup może legalnie wykonywać Linear/EigenvalueSolve i wymaga osobnegocase.
Slotnative przydzielony operatorworker: snapshot cachedr3builder, max2jobs,
32GiB/noSwap/600sbuild/900stotal; żadnego MFEM/HYPRE/libCEEDrebuild.
Nowebuild/native i krótkie CPUtesty oczekują na wynik; brak nowegospeedupclaim.

## M0 — gotowe patche diagnostyczne i lekkie kontrole (2026-10-30)

Wszyscy trzej wykonawcy jawnie GPT-6.1 Sol high. Limit równoczesnych sesji
wymusił start I/O po pierwszym raporcie operatorów; zachowano trzy osobne branche.
Root odebrał i przejrzał ich patche. Jeszcze żadnego speedupu ani native RF PASS.
Source400plików baseline == frozenSM120r3 == a6ec732f...c3338; source/native/settings/
image43ac/config provenance11PASS. Po dodaniu driverhooków hash zmienia się celowo.
Przypięty aktualny MaxSize64, nie fixture240. ArchivedIO readback10plików2,828,843B
PASS; dwa źródła mogą uzupełniać już zapisane wiersze, więc naiveCSVappend niedopuszczalne.

M0 diagnostyka: PALACE_STAGE_STOP=preprocess/operators, explicitnoRF sidecar/marker,
shared stageprobe.hpp i single-rank guard. Python testy13+4+4PASS w worktree;
natywny parser5wariantówPASS. Pełna kompilacja, nativeoperatoraction i nativeCSVregression
NOT RUN. Stary PRunitbinary jest ABI-niezgodną niewykazaną referencją (60różnychheaderów,
innefmt); wolno odzyskać sam Catch2 do świeżej kompilacji. Zachowany devbuilder ma
identyczne nativeM7r3, więc sklonować cache i rebuild tylko zmienionych TU.
Następny krok: izolowany bounded cachedbuild i tiny native harnessy w jednym slocie.
M0 pozostaje aktywny; M1/optimizacje jeszcze nierozpoczęte.

## Aktywny checkpoint — kampania faz, M0 (2026-10-29)

Użytkownik uruchomił wykonanie: trzy GPT-6.1 Sol high, osobne branche,
koordynator zbiera wyniki i zamyka bramki. PLAN Mode goal / Active M0.
System create_goal odrzucony: poprzedni paused goal nadal unfinished;
nie zamykano go fikcyjnie. Nowa kampania działa według repo workflow.
Użytkownik zatwierdził zatrzymanie Straty dla tej kampanii. Root wykonał stop;
localai-nvfp4.service inactive/dead MainPID0, GPU tylko Zed182MiB, RAM78GiB dostępne.
Po zakończeniu pomiarów przywrócić usługę; kontrolować guard przed każdym runem. Cloud i publikacja niedozwolone.
M0: uzgodnić source-runtime, fixture i tanie harnessy; nie przechodzić do M1
bez dowodów M0.1–M0.4. Badawcze patche pozostają izolowane.

## 2026-10-29 — nowy plan optymalizacji faz (planowanie zakończone)

PLAN/MILESTONES zastąpione planem M0–M6; dawny plan PR i checkpoint M0
zachowane w docs/optimization-stages/previous-pr-plan.md. Goal obliczeniowy
pozostaje wstrzymany (Mode normal / Active none). Żadnej nowej symulacji,
kompilacji, zmiany solvera lub cloud w tym zadaniu.

Źródła e288fe163 przejrzane przez wykonawców preprocessing i operators równolegle;
limit sesji uniemożliwił trzeci równoległy agent, I/O wykonał ponownie pierwszy.
Trzy worktree/branche i 15 hipotez PRE/OP/IO; stan TODO_TO_CHECK lub DEFERRED,
nie wyniki optymalizacji. Root zweryfikował exclusive BlockTimer i rewrite CSV,
poprawił błędne ostrzeżenie audytu o dodawaniu kategorii timerów.

Dowody czasów: run-local-stages-20261029/STAGES.md (pełna ścieżka w workflow).
Operator construction 121,501 s lokalnie; preprocessing35,992; IO19,612,
łącznie21,45% z825,783 s. Najpierw uzgodnienie build-source M0 i subphase profiling M1.
Najciekawsze hipotezy: współdzielenie rzeczywiście powtórnego setupu operatorów,
redukcja przebiegów/reordering mesh, pełny rewrite CSV po każdej aktualizacji.
Hotspot kodu nieudowodniony; przyspieszenie niezmierzone. Frozen bundle nietknięty.
Docs-garden (ta sama Luna high): wykryto błędne linki relatywne archiwum, root poprawił; check.sh i kontrola linków ponowione.
Dokumenty per-track są pamięcią agenta; shared docs tylko root. Pomiary sprzętowe
sekwencyjnie, cache przyrostowych buildów zachować. Strata nie została wyłączona.


## Historia — lokalny pilot PR ukończony (2026-10-22)

M0–M4 zakończone w jawnym zakresie. Branch `pr/driven-release-workspace`, commit
`8b5d4a1f87e7ceb5d4fe5fcacb7849aa17dc54b7`, baza main29ad351f9, czysty worktree.
Tylko3pliki: final uniform solve workspace, regresja metadata, changelog.
Trzy pary: peak RSS−15,82%, czas+1,34%; brak speedup/VRAM claim.
Standardowe testy CPU/MPI2/CUDA PASS według [M2](docs/milestones/M2.md).
Strict restart FAIL także baseline-vs-baseline; AMR ma zmienne siatki;
pełne CI/MFEM4.10 niezakwalifikowane. Niczego nie pushowano, nie utworzono PR/forka
ani nie kontaktowano maintainerów. Manifest, patch, opis i logi w artifacts/upstream-pr.
Docs-garden i review wykonane; runtime/builder zatrzymane, cache zachowany.
[Instrukcja sprawdzenia i ręcznej publikacji](docs/upstream-prs.md).
Kolejne kandydaty pozostają w PLAN jako kolejka, bez aktywacji nowych badań.

### Korekta opisu PR — 2026-10-23

Opis uproszczony po przeglądzie zasad Ghostty/LLVM/Palace. Metryki, named tests,
FAIL i ograniczenia zachowane; disclosure pomocy Codex. Kod/testy i commit pilota
bez zmian. Bez nowego buildu/runu i bez publikacji. Poprzedni opis oraz review notes
w artifacts/upstream-pr; manifest z aktualnymi SHA. [Szczegóły](docs/upstream-prs.md).

### Fork i branch pilota — 2026-10-23

Użytkownik autoryzował przygotowanie GitHuba. Fork `sieciowiecxyz/palace` utworzony;
branch `pr/driven-release-workspace` wysłany. Server-side compare potwierdza1commit,
3pliki/+47−4, SHA8b5d4a1f8. Żadnej historii badawczej nie wysłano, PR nieotwarty.
Upstream dostał2nowe commity (timer descriptions constexpr table); pilot świadomie
pozostaje na przetestowanym SHA. Przed upstream PR: przegląd driftu/ewentualny
rebase+retest. Manifest i `fork-publication.json` uaktualnione, testy bez zmian.
[Porównanie](https://github.com/awslabs/palace/compare/main...sieciowiecxyz:pr/driven-release-workspace).

## Historia zakończonych badań M0–M7

Wszystkie statusy, instrukcje kolejnego kroku i oznaczenia goal poniżej są zapisami historycznymi. Obecny tryb i kolejka: PLAN.md.

### Historyczny checkpoint — M7.3 PASS / następny M7.4

Końcowy pakiet artifacts/m7-sm120-bundle-r3-20261022, image43ac46f6…/
nativeA6. EXP228/229image-native bez hostnative overlays: tiny3.55GHz/
2ports/medium FP64i fixed3K/TEMPASS,17.412/18.414s (nie antenabenchmark).
EXP230deadline+SIGTERMcleanupPASS z vendorsemanticscontrol; EXP231legacy
3nativehostmountsKPASS.191Python/8shellPASS, docs/runtime-package.md.
Globalne defaulty/native numerically_validatedbez zmian. M7.1/2/3/5zakresy
zaliczone, goalaktywny. NastępnyM7.4: audytwszystkichwymagań i dowodów,
automatycznebindingnativefield-referenceinventorydopodanejR, rekwalifikacja
15W5/3median/newgeometrynanajnowszymkwalifikatorze, beznowychdużychGPUrunów
jeślinativebez zmian. Historycznecheckpointyponiżej sąchronologią.

### Historyczny checkpoint — M7.5 PASS / następny M7.3

EXP221–222 nowa geometria directora+2mm/3.500GHz/bothports/medium i pełneK
PASS. FreshFP64reference764.008s/61.139GBcgroup, fixed3candidate755.874s/
46.601GB (RAM−23.779%, czas−1.065%, tylkojednapara). NativeA6 bezrebuilda.
NowameshSHA c66c6f55…; starefieldref/seedrejected i noweCSR/faktory sprawdzone.
Audyt1601320curvedtets/37996protectednodesPASS; radom/feed/PCB/reflektor
bez zmian. Raport docs/milestones/geometry-generalization.md. Następny M7.3
odtwarzalny pakiet z pinneddeps i boundedexample; potem M7.4pełnyaudyt.
Goalaktywny/defaultybezpromocji. Historycznecheckpointyponiżej sąchronologią.

# Postępy optymalizacji

Aktualizacja: 2026-10-22. Mode: goal, Active: M7 (M6 assessment complete EXP176: directWMMA W.1FAIL/REJECT, not RFpromotion). [PLAN](PLAN.md), [MILESTONES](MILESTONES.md), [M7](docs/milestones/M7.md).

## Wymóg użytkownika

**Gorące dane solvera w RAM/VRAM.** Cache, wejścia/wyniki i sporadyczne odczyty SSD dozwolone; niewielkie zapisy mierzyć. Bez swapowania zadania i intensywnego dyskowego workspace. UVM GPU↔RAM. Nie zamykać aplikacji użytkownika. Disk basis pozostaje usunięty; polityka I/O w PLAN.md.

### Historyczny checkpoint

- Active **M7**. Fixed3 wybrany do dalszej kwalifikacji pamięciowej po fixed2 FAIL przy1.71GHz. W.4 i W.5 **15/15**freq/oba porty PASS,210regionalnychwierszy pól; suma czasu+2.58%, maxcgroup−23.84%. Jeden pomiar perpara, nie mediana/ciągłe pasmo/produkcja. Receipt artifacts/m7-full-W5-fixed3-summary-20261022.json.
- EXP215–220 **M7.2 PASS**:3nowe pary3.500GHz/oba porty, własne referencje, wszystkieKPASS/42regionalne wpisy pól. Mediany R745.458s/C747.733s (+0.305%); mediana sparowanego wzrostu+0.476%; peakcgroupmedian60.684→46.364GB (−23.597%). P2exactW.3 ma osobno sprawdzone7regionów/rawperpara, czasy2ports. Raport docs/milestones/paired-medians.md. Fizyczna redukcja peak VRAM nieudowodniona; logicalmanaged−26.33% i cuDSSallocated−46.63% to oddzielne miary.
- EXP183/184: współczesny2IR→3IR przy3.3GHz +10.74%całego czasu; koszt wcoarse, wpływ tła GPU confounds starsze dane. Dwa krótkie profile PASS, nie RFkwalifikacja. UVM migruje wielokrotnie w badanym oknie; bez deklaracji unikalnego wolumenu lub fizycznej rezydencji zGPUprocesspeak.
- EXP186–187: osobny prereg 2.900GHz S/Z/pola/raw/energy bez VSWRgate, para PASS, maxΔS7.753e-8/maxΔZ3.001e-6Ω; czas+4.00%/cgroup−24.41%. Domyślne matched-band K bez zmian. EXP191SIGTERM zachowany/retryEXP193 PASS. EXP211–214current-buildW.2 PASS. **Następne M7.5:** istotna zmiana directora/reflektora, nowy mesh/hash/reference i te sameK/cacheinvalidation; potem pakiet/M7.3 i pełny audyt/M7.4. Goal nadalaktywny.
- Native SHAa6ec732f…187c3338 bez zmian, cache zachowany; Python qualifier i docs nie wymagają rebuilda. Bez płatnego compute, swapu lub hotworkspace SSD. Globalne defaulty niepromowane.

## Wcześniejsze etapy — historia wyników

- M0–M6 ocenione; M2 integracja REJECT, M3 użyteczny zysk pamięci, M4 pełna para EXP94 PASS, M5 mixed opt-in PASS/directgprMax REJECT; M6 directWMMA W.1FAIL/REJECT. Bez zmiany globalnych defaultów.
- EXP94 T-Shaped medium3,50GHz/oba porty, samebuild/config: control681,698s → reuse602,944s,44/35iter. Jedna para −11,55%, nie mediana/promocja M7. Raw ||Ax−b||/||b|| ≤8,357e−7.
- Deferred postprocessing: managedpeak65,353→53,084GB (−18,77%) i controlcgroup60,525→56,830GB (−6,11%); reuse sam nie zmienia tego peaku. Jeden dodatkowy E179,5MB w RAM/VRAM. Fizycznej rezydencji VRAM nie utożsamiać z alokacjami.
- Wholefields/S/VSWR/power/energy PASS, W.2 trzyfreq/oba porty i tiny normalpathPASS. EXP92 OOM i EXP93 inline-reference OOM pozostają FAIL. Receipt artifacts/m4-deferred-antenna-root-analysis-20261020.json; dowody docs/milestones/M4.md.
- Regresje124PASS, cachedbuild9,215s, zachowane native/cache i fallback build/m4-reuse/pre-exp94-native. Gorące dane RAM/VRAM; SSDpolicy w PLAN. Bez płatnego compute/zamykania aplikacji.
- M5/EXP95–96: hybrid cuDSS API/tiny/medium/W.3P2 PASS, ale REJECT jako net speedup: UVM350,371s vs4GiB363,872s/6GiB511,069s. Coarse około2× szybciej, pozostały PC wolniej; nowy profil potrzebny do dowodu przyczyny. DefaultUVM/fallback zachowane.
- EXP97 AMS: tiny/mediumquality i CUDAprofilePASS, W3P2deadline900sFAIL (iter264/recurrence1,501e−3, brak rawfinal/pól); REJECT obecnegoC2. Partialcgroup29,32GB nie kwalifikuje oszczędności anteny.
- EXP98–101 scaled native complexFP32/dwie FP64 CUDA korekcje: API/W.2 trzyfreq/oba porty i W.3P2 PASS. Jedna para W.3 339,362→273,843s (−19,31%),35/35iter; cgroup56,027→45,376GB (−19,01%). Pola/S/VSWR/energia/raw PASS; opt-in bez nowego defaultu. Raport docs/milestones/mixed-coarse-plan.md; build18,615s, fallback build/m5-mixed/pre-mixed-native.
- EXP102 M5.5 strict late30:2 profile PASS: UVM251,125→186,635GB (−25,68%) w dwóch iteracjach; okno12,944→10,530s. To nie pełny migrationtotal ani nowy RFsolve; docs/mixed-coarse-profile.md.
- EXP104: actual exportSHA powiązany z mesh audit; PCBbbox72mm, wybrany PCB/feedsubset91,676×72×47,750mm. SingleHSG0,1mm wymaga36,144GBbase. Publicnesting odrzucony; directportgprMaxREJECT bez nowego sprzęgania/subcell. SolverNOTRUN po resource/API gate, nie blanketFDTDrejection. Audyt M5.1–M5.6 w docs/milestones/M5.md.
- EXP105–106 M6.1 PASS: host audit tiny i pełny W.3,108grup/14627calls/zeroerrors; raw/pola/S/energy PASS. W.3 272,718s/35iter (kontrola audytu, nie nowy speedup). Actual Hcurl P20/Q14/qcomp3/N1601320; wymagane bytes osobno od długości workspace. docs/ceed-basis-audit.md.
- EXP107–108 M6.2 filtrPASS:96screen+42size-ladder (tylko6actualN1601320), FP32actionerror≤1,054e-7, TF32requested≤4,973e-4. ActualN FP32+konwersje2,598–3,223ms vsoriginal3,473–3,744ms; TF32wolniejszyodFP32, małeNmixedwolniejsze. To nie UVM/solver/RF/TCproof. docs/ceed-tensor-probe.md.
- EXP109–110 fusedFP32 filterPASS: 96screen/42ladder, error≤1,148e-7; actualNforward1,334–1,342ms vs3,474–3,478ms, transpose tylko2–5%zysku. Fused per-path FP32basis3360B, alecomparisonprocessnadaltrzymalibraryscratch, brakmeasuredpeak/RF/UVM/solverclaim.
- EXP112–113 PCforward integration tiny/medium3,55K+scope/cachecleanupPASS, lecz iteracje40/42→45/45 i48/49→55/57, medium99,580→99,592s bez wykazanego zysku. Większy rawgap skorygowany restartem; HOLD, niepromowany, W3 NOTRUN. docs/pc-basis-fp32.md.
- EXP114–116: compensateddot+bit-split actionfilter PASS (CPU/linearity/range1e-300..1e300). ActualND20/Q14/N1601320 forward3,474–3,482→3,035–3,048ms; error~6e-15. Pierwszywariantbyłwolniejszy; scalar/trace nieprzyspieszone. Nie solver/RF/UVM/TCclaim; nativebez zmian. docs/ceed-tensor-probe.md.
- EXP117–119 compensatedPC tiny/medium3,55 quality/scope/cachePASS po naprawie envguard (pierwszy candidateFAILzachowany). Iteracje40/42 i47/49 bez wzrostu, lecz16,533→16,629s i98,577→98,546s bez netgain, HOLD/W3NOTRUN. docs/pc-basis-fp32.md.
- EXP120–122 M6.6 sourceaudit+frequency-major2portreuse/per-portRAMhistory: tiny12,544→11,501s i medium53,570→45,344s/6→3factorbuilds, frozenRF/raw/wholefields/TEMPASS. Jedna para, nie antena/mediana/promocja. Cgroupmedium2,255→2,304GB, nie oszczędnośćpamięci. Singlefreqreuse/deferred regressionPASS. docs/milestones/sweeps.md.
- EXP123–127: per-f deferred release i skumulowane metadata PASS; 7freq coax medium 93,540→75,664s (jedna para −19,1%), wszystkie14 pól/raw/K PASS. Cgroup2,515→2,535GB: bez oszczędności RAM całego runu. Stary singlefreq regression9,473sPASS.
- EXP128–130: fresh-factor i reuse mają identyczny harmonogram/historię/deferred release. W3medium3,5/3,6GHz oba porty996,519→915,924s (−8,09%, jedna para), cgroup48,720→47,660GB. Pola/raw/frozenK PASS; bez mediana/defaultpromotion.
- EXP131–133 linear predictor: coax7freq czas −6,45%/−9,54%, ale W3 1312,606→1317,834s, obie próby fallback. Quality PASS, antena speedup REJECT/default OFF. Ten sam memory/precision scope, bez promocji z małego modelu.
- EXP135–138 complex projection: math96/coax7freq PASS, lecz W3 mixed coarse2IR FAIL przyP2/3,7GHz (1,460e-3>1e-3). Tylko5/6solve, nie speedup/pełnaRFkwalifikacja; nowy wariant defaultOFF/HOLD.
- EXP153–166 actual7freq3,3..3,9/oba porty fullFP64vscombinedFP32storage/mixed2IR/reuse: wszystkie frozenS/VSWR/power/energy/raw/98fieldsPASS. Suma5124,017→4043,095s (−21,095%), maxcgroup61,224→46,637GB (−23,825%). Jeden pomiar per f wbounded chunks, nie mediana/monolithic/physicalproof. M6.6 assessment complete; następne cuBLASLt i M6.3TC-proof, potem M7; docs/milestones/antenna-sweep-qualification.md.
- EXP139–142: verified history single-f/coax+legacy PASS; antena odtwarza klasę coarse2IR failure w121s zamiast1159s, nie identyczny bitowo RHS. EXP143–147: fixed3 coax PASS/singleP2 executionPASS, pełny sweep deadlineFAIL5/6, niepromowany. EXP148–152: PROM4 held-outPASS, lecz +19,77%czasu/+11,77%cgroup vsbestuniform; REJECT promocji. Symbolic upperbound~2,2%, full recycling niepromowany. Po tym wykonano7f anteny EXP153–166; następneM6.3/cuBLASLt, potem końcowa kwalifikacja. Bez ponawiania drogiej pary bez nowej informacji. M6.3TCproof/M7.5geometria NOTRUN; M6/M7/W4/W5/mediany otwarte.

## Historyczny skrót M1/M2

- M1 COMPLETE: referencja/normy/topologia/bieżącealokacje/krótkiprofil i końcowy normalpathPASS; M2 był wtedy ACTIVE. Goal pozostaje aktywny, bez promocji nowych defaultów.
- EXP18–19: W.3FP64nativecomplex kwalifikacja35iter/447,462sbezprofilera, raw8,36e−7, maxΔS6,70e−9/E-B9,89e−8 względemtight-r2. To3,50GHz/P2fixturemedium, nie najlepsza geometria produkcyjna. docs/native-complex-coarse.md.
- EXP21: rzeczywiste DOF zgodne z Palace, AIR-exclusive57,586%ND2. Pełny net-release bilans55,148GBmanaged. docs/topology-memory.md.
- EXP22: aktualny residentallocaudit49,583GBpeak,99,616%przypisane dościeżek; cuDSS25,008GB, libCEEDduże bufory18,495GB. docs/memory-audit.md. Nieutożsamiać wczesnegopeaku4iter z35iterpełnego solve.
- CUDA-only+afinicznyhostclock krótki profil W.3PASS, bezwarnings:2iteracje17,665s, P16,278sinclusive,295,472GBUVMmigrations. Held-out1,127µs<10µsmarginesu;1/4939kerneli nieprzypisany przygranicy. docs/profiling-window.md. Historyczne NVTX i failedclock zachowaneREJECT.
- EXP23: PEC Maxwell/Mie zbieżność i1%PASS na1920RWGDOF/33,89s; Bempp/H2Opus przypięte, izolowany Python/JITcache. docs/maxwell-oracle.md.
- EXP24: rzeczywisty H-matrix exact-near/complexSVDfar iCUDAapply jakościowoPASS; macierz−9,16%, ale52,68×wolniejszy apply na małej kuli. Niepromowany; brak peakRAMoszczędności, dielektryka/interfejsu ianteny.
- EXP25–29: native2kernel/H-matrixeta4 −17,31%matrixdata i poprawnyGPUoperator/CPUbasisGMRES. DielectricPMCHWT/Mie far-fieldPASS0,0223% zregułąobjętości i zbieżnością; stareinscribedmeshscatterFAIL. docs/maxwell-native-dielectric.md.
- EXP30–31: actualMFEM4.9ND1/Bemppcoupling ze zbieżnością, trace/pair~1e−15/energyPASS. Całkowity1%E/HFAIL:6,12/5,79%, comparatorFEM6,18/5,82%; Δcoupled–FEM0,57/0,76% niekwalifikujeND2/anteny. docs/maxwell-coupling.md.
- EXP32: primalRWG/SNCGramtracirank90/120,330/480; odrzucićinwersjędoprowadzeniaND2projection. DualRWG/RBCfullrank/κscaled≤2,93, physicalpairing/transforms/constanttracePASS. Plane-traceRWG0błąd20,99→10,43→5,16%, nadalnieND2mortar. docs/maxwell-coupling.md.
- EXP33: actualglobalMFEMND2/faceDOFtransforms/physicalbasis/CSR, Dirichletplane-waveE/H0,1505/0,3317%PASS na8936DOF/1280tet.5,514s/433MB/CSR8,79MB; interpolacjaH1,468%FAIL. BrakcoupledBEM/antenna speedup; docs/maxwell-nd2.md.
- EXP34: actualND2/BC-RBCmortar/localbasisassembler/sparseSchurPASS, currentwholefieldFAIL17,74/15,22→10,07/5,64% mimo raw/far/energyPASS. NativeT/K≤1,22e−16, tinydenseSchur≤1,94e−14; brakpromocjianteny. docs/maxwell-nd2-coupling.md.
- EXP35–37: duality/trace diagnostics i niezależny brzeg. Magnetic F2/B3 E/H0,560/0,751% PASS, F3/B3 0,358/0,904% PASS (H gorsze). Root source/SO/state/quality verification PASS; docs/maxwell-trace-duality.md. Dielectric transmission/rezonanse/scalable assembly/koszt pozostają otwarte.
- EXP38–41: dielectric eps2,94 wykonany, centroidscreening FAIL E/H1,092/1,320% względem PMCHWTB4/q12. RefEchange0,408%>0,3%; potentialB4q8/q12<1e−6. Raw/far/energy małe nie kwalifikują pola. Zachowane NPZ do dalszej analizy bez solve; docs/maxwell-transmission.md.
- EXP42–43: saved-solution volume replay640/2240pts. Degree5 E/H2,888/1,612%, refchange1,945/1,158%, potentialqdelta~7,4e−4 FAIL. Root SHA/state/complexintegral verificationPASS; H_FEM własnanorma q2/q5 zgadza się2,11e−15. Następna hipoteza adaptive near-panel correction; niepromować i nie skalować ślepo referencji.
- EXP44–47: RWGpanel/native i niezależny static-normalcontrolPASS, ratio2 czterokrotnie mniejliści. FullfineB4nearcorrection117,617s/217MB adaptive/cutoffPASS, E/H2,888/1,611% nadal FAIL. Root allpoint/weights/input/sourceSHA/complexnorm/subsetregression PASS. Dalsze EXP48–53 poniżej, docs/maxwell-near-panels.md.
- EXP48–53: cached NumBa native/parityPASS, pełny coarse replay18,089s/RSS217MB (NumPyTIMEOUT180s). Obie strony adaptivePASS; correctedreferencechange degree5E/H1,647/0,781%FAIL0,3%, volume2/5agreementFAIL, brakpromocjianteny. docs/maxwell-near-panels.md.
- EXP54–58: epsilon2,94 analyticF3 E/H.443/.717%PASS, actualcoupledF3/B3 i fixed640probes.664/.597% vsB4. Nie pełnyL2; reference/volume convergence nadalFAIL. DefaultND2eps1 regressionPASS. docs/maxwell-fem-refinement.md.
- EXP59–69: fusedT/K matchedCPU32query~2,56×zprzygotowaniem, nieantenna speedup; native teżmatrixfree. OwnF3degree5E/H1,683/.972%, reference/degreeFAIL. DenseB5>cap; następny małyFMMcandidate NOTRUN. docs/maxwell-stream.md.
- Praca RAM/VRAM. FEMcap60GiB/guard6GiB; nowe małe oraclecap6GiB/noadditionalSwap, noOOM. Bezpaidcompute/closedapps; cachekompilacji osobno.95testsPASSwpinnedenv; systemowo79PASS/16SKIP(SciPy). Kod Palace/medium bez zmian.

## Rejestr eksperymentów

| ID | Wynik i decyzja | Artefakty / ograniczenia |
| --- | --- | --- |
| EXP01 | Coax FP32/FP64: porty zgodne; raw residual nie znika z FP64, sam storage nie wyjaśnia norm. | `artifacts/m1-coax-{raw-residual,fp64-raw-residual}-20261018/` |
| EXP02 | Audyt anteny: AIR 61,71% elementów, PTFE 30,03%; dense BEM block ~11,90 GiB to rachunek ilustracyjny, nie pomiar oszczędności. | `artifacts/m1-mesh-audit-20261018.json` |
| EXP03 | Probes TEM E/B/energia PASS; LEFT vs RIGHT pokazuje różnicę raw/stopping, RIGHT wymaga więcej iteracji. | `artifacts/m1-tem-fields-*` |
| EXP04 | Tiny natywne L2 PASS <1% obu portów; wcześniejszy 20 mm L2 FAIL/deadline 180 s zachowany. | `artifacts/m1-tem-validation-20261018.json` |
| EXP05 | Całe pola tiny FP32 vs FP64 PASS (E≤1,14e−7, B≤6,09e−5); sztuczne B×1,02 prawidłowo FAIL; disk/resident tiny PASS, lecz disk storage odrzucony wymogiem. | `artifacts/m1-fields-tiny-*` |
| EXP06 | Pierwszy antenna run przerwany sygnałem, przyczyna nieustalona; background tiny potwierdził live PID. FP64-disk ref ukończona; wcześniejszy resident FP32 antenna run FAIL/host guard. | `artifacts/m1-antenna-field-attempt-20261018.json`, `artifacts/m1-background-smoke-20261018/`, dalsze dane w raporcie M1 |
| EXP07 | FP32-disk antenna zakończona po 151 iteracjach/1563,128 s; 7 porównań pól PASS (max E 2,75e−5/B 3,66e−3). **REJECT** — storage dyskowy zabroniony; scratch usunięty. | `artifacts/m1-antenna-fields-fp32-disk-20261018/`; szczegóły w raporcie M1 |
| EXP08 | Po usunięciu disk basis resident coax-tiny: 6/6 PASS, 14,06 s, cgroup peak 0,68 GiB; brak pól, anteny i kwalifikacji RF. | `artifacts/m1-no-disk-basis-resident-20261018/` |

Artefakty lokalne zawierają dokładne argv/config/build manifesty, wyniki, telemetry i logi tam, gdzie dany test je generował. FAIL kompletności nie jest wynikiem RF; nie wyprowadzać błędu anteny z nieukończonej próby.

## Następny krok

M6.6: rozszerzyć per-frequency ksp/factor release i deferredpostprocess dla
frequency-major2port batch, aby nie nakładać peaku solve i pomiarów. Tani
lifetime/order/K filter, potem7freqcoax/resourcegate iantena. EXP120–122
3freqcoaxPASS/medium15,4%singlepair, niepromowane. PROM/heldout/symbolic/recycling
wciążOPEN; zachować oryginalnyFP64basis iM5mixedcoarse, wszystkie K.

## Reguły pracy

Jedna próba = hipoteza, dokładne argv/hash, limit, wynik i decyzja; FAIL nie jest speedup. Nie powtarzać referencji/sweepów bez potrzeby. Zachować cache CMake/ccache/dependencies. Ta sama Luna high wykonuje wyłącznie gotowe uruchomienia/babysitting i docs-garden; projekt i interpretacja należą do agenta głównego. Cel pozostaje aktywny i nieukończony.

Dodatkowa kontrola guard: aktualny natywny binary w kontenerze odrzucił oba legacy env PALACE_GMRES_FP64_DISK_BASIS/PALACE_GMRES_FP32_DISK_BASIS (exit1, komunikat RAM/VRAM) przed MPI/CUDA. Dowód: artifacts/m1-no-disk-basis-resident-20261018/legacy-rejection.json. Build 63,11 s; resident tiny 14,06 s PASS. Następnie 19 regresji narzędzi PASS, w tym przypadki audytu alokacji i Q-pool; szczegóły w [docs/testing](docs/testing.md). HostSwapTotal=0; nie zmieniano konfiguracji systemu.

## EXP09 — audyt bez nowej symulacji

PASS analizy: tools/allocation_audit.py odtworzył duże alloc/free ze stosami, odzyskał 3 zdarzenia doklejone do stdout i przypisał 99,50% logicznego peak 45,18 GiB. W tej samej chwili 48 buforów po 538 043 520 B = 24,05 GiB, ścieżki libCEED QFunction/basis/assembly. To nie fizyczna rezydencja i nie obietnica odzyskania 24 GiB. Źródła przypiętego libCEED cbd4902 potwierdzają per-operator Q-vectors oraz brak fused curl/div w cuda/gen, dlatego nie uruchamiano ślepego benchmarku nowego backendu. Audyt i hipoteza workspace: [docs/memory-audit](docs/memory-audit.md); dane `artifacts/m1-antenna-allocation-audit-20261018.json`. Nie zmieniano kodu numerycznego ani zależności, cache/build bez rekompilacji. M1 nadal otwarty.

## EXP10 — pilotaż współdzielenia aktywnych Q-wektorów (PARTIAL / NOT QUALIFIED)

Hipoteza: aktywne Q-wektory per operator mogą używać istniejących `CeedGetWorkVector/Restore`, zachowując trwałe i bierne pola oraz oryginalne buforowanie assembly. Prototyp ograniczono do `ApplyAdd`; `EVAL_NONE` i `AtPoints` bez zmian. Pełna `cudaDeviceSynchronize` przed pożyczeniem i przed zwrotem daje konserwatywny porządek, ale może kosztować tyle, że wariant nie będzie wart promocji. Nakładające się `ApplyAdd` są odrzucane. FP64 i algebra pozostają bez zmian. Alternatywna biblioteka libCEED ma przypięte źródło i manifest; build zmienił jeden plik C i użył cache pozostałych obiektów. Build trwał 1,51 s. Odrzucono wcześniejszy pomysł interposera przed GPU z powodu prywatnych symboli libCEED; użyto osobnego pełnego SO, bez modyfikacji bazowych bibliotek/obrazu. Szczegóły: [docs/ceed-qpool.md](docs/ceed-qpool.md).

Probe 6 DOF PASS w bazie i Q-pool: dwa operatory naprzemiennie, aktualizacje danych pasywnych, diagonal i `ApplyAdd`. Q-pool: 16 wywołań/32 pożyczone wektory; czas 0,63 s vs 1,90 s nie jest benchmarkiem (zimny/ciepły JIT). Artefakty: `artifacts/m1-qpool-probe-20261018/`.

Następny filtr to coax-tiny 3 częstotliwości × 2 porty, FP64 i allocation trace; dopiero potem Q-pool TEM L2 przy 3,55 GHz/2 portach. Jednak baza coax-tiny zakończyła się przed solve po 2,8878 s: `cudaMalloc(4294967312)` OOM w lazy 4 GiB HYPRE/Umpire device pool, równolegle z host guard. MemAvailable spadła z 5,34 do 4,84 GB; w tej chwili zaobserwowano też około 15/16 GiB VRAM zajęte przez inne obciążenie. Dwa dalsze runy i pełna antena pozostały NOT RUN, bez retry i bez zamykania aplikacji użytkownika. Błąd baseline nie kwalifikuje ani nie odrzuca numeryki Q-pool. Dodano preflight, który nie uruchamia kontenera GPU przy dostępnej pamięci hosta poniżej 6 GiB; właściwy guard nadal działa podczas runu.

Przypięte źródło hypre 3.1.0 potwierdza leniwie tworzoną pulę device 4 GiB i publiczny setter `HYPRE_SetUmpireDevicePoolSize`. Zmniejszenie jej rozmiaru to osobna, jeszcze niewdrożona i niezmierzona hipoteza; nie łączyć jej z porównaniem Q-pool. Mały probe nie stanowi dowodu zysku pamięci/szybkości dla Maxwella. M1 otwarty, obowiązkowe M2 FEM–BEM/MoM niepominięte.

Root końcowy przegląd: 19 regresji PASS; generator cache kontroluje także runtime ID. Odświeżenie recepty trwało 1,61 s, kolejne wywołanie trafiło w cache bez kompilacji. SHA biblioteki i probe odpowiadają artefaktom PASS 6 DOF. Natywny Palace nie wymagał rekompilacji, a domyślny backend pozostał bez zmian. Następny krok to niezależny test początkowego seedu HYPRE/Umpire, nie retry OOM.

## EXP11 — początkowa pula HYPRE (TINY PASS / ANTENNA NOT RUN)

Zmiana jest opcjonalna: `PALACE_HYPRE_DEVICE_POOL_MIB` / `--hypre-pool-mib 256` ustawia seed po inicjalizacji HYPRE, przed utworzeniem hierarchii FEM. Domyślne 4 GiB pozostaje bez zmian; seed nie jest limitem, a pula może rosnąć. Wszystkie testy zachowały FP64 i średnią dokładność.

Pierwsza para coax-tiny (3 częstotliwości × 2 porty) ukończyła 6 solve z tymi samymi iteracjami [24, 13, 14, 25, 13, 13]. Max Δcomplex S = 8,56e−15, ΔVSWR = 1,34e−14; UVM peak obu runów 322 588 630 B. Te wstępne runy nie izolowały zużycia procesu: globalny GPU to także obciążenie pulpitu. Późniejszy pomiar PID wykazał dla defaultu 4 GiB peak 4 657 774 592 B, a dla seedu 256 MiB 631 242 752 B — różnicę 3,75 GiB w próbkowanym VRAM procesu. Próbowano około raz na sekundę (9/10 próbek); to wynik małego fixture, nie gwarancja dla pełnej anteny. Czasy 10,475 s i 10,388 s są zbliżone, bez wykazanego speedup.

Known-TEM 256 MiB, 3,55 GHz, oba porty: L2 pola E 0,4953%, B 0,5211–0,5363% przy kwadraturach 4/6; wszystkie wartości poniżej 1%. To nie kwalifikuje pól pełnej anteny.

Q-pool sprawdzono osobno względem seedu 256 MiB. Coax-tiny: 11,437 s, sampled VRAM procesu 631 242 752 B, logical UVM peak 341 345 926 B wobec 322 588 630 B w seed-only (+5,8%). TEM L2 ukończył się w 17,561 s. Porty pozostały numerycznie zgodne, ale filtr nie wykazał oszczędności pamięci; Q-pool nie jest promowany i nie ma podstaw do kolejnego pełnego runu.

Audyt historycznego peak 45,18 GiB przypisuje zdarzenie wyzwalające `CompareFieldSnapshots` / `GetMagneticFieldEnergy`, zgodnie ze stosem `peak_trigger_event`. To koszt diagnostyki pól, a nie dowód, że sam GMRES osiąga taki peak. Nie sumować wszystkich buforów ze snapshotu z całą bazą GMRES ani nie wyciągać właściciela z kolejności tekstów stdout/stderr. Następny krok M1 to jawne znaczniki faz i pomiar peaków w solve oraz postprocessingu, po czym ocena budżetu dla referencji FP64 rezydującej wyłącznie w RAM/VRAM.

Pełna antena z Q-pool pozostaje NOT RUN; seed256 MiB bez Q-pool został później użyty w ukończonym EXP12 poniżej. Domyślny seed 4 GiB nie zmienił się. M1 pozostaje otwarty, a obowiązkowy prototyp M2 FEM–BEM/MoM nie jest pominięty.

## Stan walidacji repozytorium

Aktualny build przyrostowy native ukończył się w 8,298 s; 25 testów jednostkowych PASS. Te kontrole walidują narzędzia i małe fixture, nie kwalifikują pełnej anteny. Pełna antena EXP12 ma execution PASS, lecz niezależna jakość pozostaje otwarta; multi-GPU i zbieżność produkcyjna pozostają NOT RUN. Wymóg RAM/VRAM bez SSD/swap pozostaje obowiązujący.

## EXP12 — fazy pamięci i lifetime bazy (filtry i pełny run ukończone)

Kod GMRES potwierdza, że zwykła baza FP64 V jest polem solvera i zostaje po Mult. Opcja release czyści V dopiero po rekonstrukcji i wszystkich checkach; nie zmienia E, statystyk, restartu ani tolerancji. Kolejne Initialize odtwarza V. Markery adaptera emitują monotoniczne czasy i live/peak pomiędzy fazami, bez deviceSync. Domyślne zachowanie pozostaje bez zmian. Walidacja: tiny 6 solve'ów, known-TEM, następnie jedna pełna referencja wykonania FP64; wyniki poniżej. Samo ukończenie nie zamyka M1.


Pierwszy filtr `artifacts/m1-gmres-release-tiny-20261018/`: exit 0 i 6/6 solve w 11,515 s, lecz **FAIL kompletności diagnostyki** (`complete=false`). Ostatni komunikat zwolnienia bazy został rozdzielony przez zmieszanie stdout/stderr; rozpoznano tylko 5/6 pełnych prefiksów. Nie uruchomiono kolejnego TEM. Zmieniono emisję release na pojedynczy wpis stderr, jak markery faz; wymaganie sześciu pełnych komunikatów pozostaje bez zmian. Cached rebuild 7,388 s, 22 unittesty PASS. Powtórzenie z nowym hashem źródeł otrzymuje osobny sufiks `r2`; pierwotnego FAIL nie nadpisujemy.

Retry r2: release i fazy 6/6 PASS, ale kolejny **FAIL kompletności** (5/6 `PALACE_KSP_CHECK`). Interleaving przeciął tym razem stdout z residuum, więc samo przeniesienie release na stderr nie wystarcza. Runner zapisuje teraz stdout/stderr osobno, a dopiero po zakończeniu składa `palace.log` z jawną informacją o braku globalnej chronologii strumieni. Zachowuje surowe logi; test z celowo przerwanym stdout potwierdza integralność komunikatu. 23 unittesty PASS. Kolejny filtr r3 używa tego samego native builda (zmiana wyłącznie Python/logging).


EXP12 r3 filtry **PASS**: tiny save-fields 10,517 s, 6/6 solve (24/13/14/25/13/13), wszystkie stopping checks ≤1e−6, markery i release 6/6. Względem EXP11 seed256 max |ΔS|=3,88e−15, ΔVSWR=6,66e−15, względna zmiana wspólnych energii=2,07e−13 (`artifacts/m1-gmres-release-analysis-20261018.json`). Sampled GPU procesu 631242752 B; cgroup peak506884096 B; logical UVM peak308538406 B. To kontrola numeryczna małego fixture, nie dowód speedup ani kwalifikacja anteny.

TEM r3: 17,586 s, 2/2 solve, pełne coverage; E L2 q4/q6 około0,495%, B0,521–0,536%, oba porty <1%. Logical UVM peak290950486 B, sampled process GPU631242752 B. Baza znika po sprawdzeniu rozwiązania, przed postprocessingiem; liczniki liczą lifetimes, nie rezydencję GPU.

Wykonane polecenie pełnego runu: `python3 tools/dev.py run tshaped-medium artifacts/m1-antenna-resident-fp64-20261018 --seconds 1800 --basis fp64 --hypre-pool-mib 256 --release-gmres-basis --memory-marks --save-fields --background`. Jedna3,50GHz/P2, identyczny mesh medium, bez Q-pool i porównania starej referencji, bez dyskowej pamięci roboczej. Cgroup60GiB, hostguard6GiB, przed uruchomieniem około68,7GiB MemAvailable; GPU miał obciążenie aplikacji użytkownika (około4,8GiB), nie zamykamy ich. Guard/OOM/deadline nadal oznaczają FAIL; ten konkretny run ukończył się naturalnie. M1.2/M1.3 niezależnej jakości nadal otwarte.


Pełny run EXP12 **execution PASS**, 1089,964 s, 151 iteracji, 3,50GHz/P2; bez OOM/guard/deadline. Wszystkie markery faz i release1/1. Zwalnianie V po solve zmniejszyło logical managed58,706→31,422 GB (25,41GiB), koszt0,181 s. Maksymalny logical managed58,779 GB (54,74GiB) nastąpił w GMRES; postprocessing48,090 GB (44,79GiB). Cgroup peak57,72GiB, sampled GPU4,89GiB, min hostavailable11,98GiB. Peaki nie są addytywne ani dowodem konkretnej rezydencji alokacji. Snapshot E/B ma179499600/240704512 B i SHA w fields.json; pełna analiza root w `root-analysis.json`.

VSWR P2=1,672123; raw ||b−Ax||/||b||=0,1252666005 przy independently recomputed LEFT stopping9,956397e−7. Raw/stopping ratio≈125815; nie wynika to z FP32, bo aktualny solve jest FP64. **Jakość anteny M1.2/M1.3 pozostaje nierozstrzygnięta**; nie promować dalszej precyzji na podstawie samego S lub ukończenia. Ten run zastępuje odrzucone dyskowe wykonanie jako dopuszczalny punkt diagnostyczny, ale nie stanowi jeszcze kwalifikowanej referencji fizycznej. Nie wyliczać speedup względem historycznego disk runu z innym tracingiem/polityką pamięci. [Interpretacja i odtwarzanie](docs/memory-phases.md).


## EXP13 — korekta RIGHT (tiny PASS, pełna antena FAIL/deadline)

Hipoteza M1: LEFT ogranicza ||P r||, więc małe stopping nie kontroluje raw. Wznowienie z pola E nowego resident FP64 jako jednorazowego wejścia pozwoli sprawdzić korektę RIGHT bez ponownego liczenia LEFT. Źródło InitialResidual przy InitialGuess=true skaluje stopping przez ||b|| dla RIGHT, nie przez małe początkowe residuum. Limit bazy64 zamiast240 daje do około11,7GB FP64 V, a nie do43,3GB przy pełnym240; medium/mesh/Tol1e−6 pozostają. To jawna diagnostyczna zmiana solvera, nie zmiana zamrożonego fixture ani promowany default.

Nowe opcje --initial-fields i --krylov-size. Wejście snapshot ma weryfikowane SHA/header, fizykę/mesh/dependencies/coverage oraz completed result, montowane read-only. Jednorazowe wczytanie E przed każdym solve, bez dyskowej bazy/scratch/swap. Naprawiono raportowanie checka dla zerowej liczby iteracji po już zbieżnym initial guess; zwykła reguła zatrzymania bez zmian. Cached rebuild9,808s,24 unittesty PASS.

Filtry przed pełnym runem: (1) tiny LEFT replay6solve, oczekiwane0iter i identyczne pola; (2) tiny RIGHT warm6solve, raw≤1e−6, max|ΔS|≤1e−3, ΔVSWR≤0,01, względna zmiana energii≤1e−3 i ważone różnice E/B≤1% do resident tiny LEFT. Każdy limit90s, FP64/seed256/release/marks, brak płatnego compute. Pierwszy FAIL zatrzymuje sekwencję.

Dopiero po filtrach jedna pełna korekta 3,50GHz/P2 z `artifacts/m1-antenna-resident-fp64-20261018` jako input i diagnostyczne porównanie pól; RIGHT/K64/FP64/Tol1e−6, limit1800s/cgroup60GiB/guard6GiB. Cel raw≤1e−6 (niezależny od preconditionera); pełny finalny raport oddziela algebraiczne residuum od fizyki/discretization error. Porównanie do starego LEFT jest kontrolą wrażliwości na rozwiązanie, nie niezależnym modelem fizycznym. Jeśli budżet lub zbieżność nie wystarczy, FAIL zachować i dobrać kolejny krok na podstawie wyniku.


EXP13 filtry PASS: LEFT replay10,562s, 6×0iter, różnica pól0; odtworzenie initialE nie zmienia wyniku. RIGHT warm12,468s, iteracje40/38/37/41/39/38. Raw max9,7804e−7, max|ΔS|9,947e−6, ΔVSWR3,282e−6, zmiana sumy mocy portów6,958e−6, względna energia1,750e−4. Ważona różnica E9,368e−6, B0,0031115 (0,311%), wszystko w zamrożonych progach. Oba runy: complete/restart/field_accuracy=true i pełne coverage. Root analiza `artifacts/m1-restart-analysis-20261018.json`. LEFT nadal raw do0,0087; jego zerowe iteracje to test replay, nie jakości raw.

Przygotowany pełny run: `python3 tools/dev.py run tshaped-medium artifacts/m1-antenna-right-correction-20261018 --seconds 1800 --basis fp64 --hypre-pool-mib 256 --release-gmres-basis --memory-marks --pc-side right --krylov-size 64 --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m1-antenna-resident-fp64-20261018 --save-fields --background`. Wyłącznie diagnostyka jakości, bez zmiany mesh/Order/PA/Tol. Baza ograniczona64; przewidywany logical solve working set około40–45GiB (hipoteza, nie gwarancja), postprocessing około45–50GiB. MemAvailable przed startem około71,9GiB, GPUbackground około2,7GiB. Same limity i twardy FAIL na guard/deadline. Weryfikacja inputu/referencji dzieli ten sam SHA check zamiast czytać dwa razy identyczny snapshot. Nie porównywać czasu warm correction do solve od zera jako speedup.


EXP13 pełna RIGHT/K64 korekta **FAIL/deadline**, elapsed1800,806s, exit255, bez OOM/hostguard. Ostatnia widoczna, niepełna linia zaczyna się od140 (restart2); ostatnia pełna linia to139, recurrence0,37005. Rzeczywista końcowa iteracja nieznana, bo stdout był buforowany; brak kompletnego solve/S/pól/checka raw. Cgroup peak43,69GiB i min hostavailable27,24GiB potwierdzają, że ograniczenie pamięci zadziałało, lecz zbieżność/czas nie wystarczyły. Nie traktować częściowego recurrence jako certyfikatu raw. Zatrzymano bez retry. Szczegóły i SHA w artifact/root-analysis.json. Ten wariant nie jest promowany.

## EXP14 — ostrzejszy LEFT (tiny PASS, pełna antena FAIL/deadline)

Nowa hipoteza po FAIL RIGHT: zachować LEFT, który skuteczniej minimalizował ważone residuum, ale skorygować zapisany wynik z Tol1e−12 zamiast1e−6. To jawnie ostrzejsza diagnostyka referencyjna, a nie zmiana domyślnego medium ani deklaracja speedup. Siatka/Order2/PA1/fizyka bez zmian. Dotychczasowy raw/stopping ratio≈1,26e5 sugeruje docelowe raw rzędu1e−7 przy LEFT1e−12, lecz NIE jest ograniczeniem błędu ani gwarancją: finalnie wymagamy jawnego raw≤1e−6 i zachowujemy progi pól/RF/energii.

K96 ogranicza do97 wektorów×179499584B≈17,42GB, mniej od27,82GB w referencji151iter. Domyślny restart240 bez zmian. Włączona w runnerze weryfikacja recomputed stopping teraz odrzuca/ponawia także FP64 recurrence gap zamiast tylko wypisywać niezgodny check; bez PALACE_VERIFY_RESIDUAL zwykła ścieżka FP64 niezmieniona. Tolerancja diagnostyczna nie może osłabić progu fixture i musi należeć do[1e−14,Tol fixture]. 25 unittestów PASS.

Najpierw tiny6solve LEFT/K96/FP64/Tol1e−12, input z resident LEFT, porównanie pól do nowego RIGHT tiny, limit120s. Wymagamy raw≤1e−6, pełne checks/coverage, max|ΔS|≤1e−3, ΔVSWR≤0,01, względna energia≤1e−3 i E/B≤1%. Dopiero po PASS pełna antena jako korekta poprzedniej FP64 referencji, limit1800s i identyczne guardy; bez dalszych restartów po FAIL.

EXP14 tiny PASS:15,553s, iteracje73/71/71/74/72/72, verifiedLEFT≤9,904e−13, raw≤8,990e−9. Względem RIGHT tiny ważone E≤2,238e−7/B≤3,375e−7; bez reliable restarts. Root RF/energia z root-analysis.json: {"max_complex_delta_S": 2.468937017680457e-08, "max_delta_VSWR": 3.1780726050811836e-08, "max_relative_energy_delta": 1.29200241662808e-07, "max_raw": 8.989300235472e-09, "max_E": 2.237693287963e-07, "max_B": 3.374143447481e-07} .

Pełny EXP14 przygotowany z K128 zamiast96: mały filtr kończy przed74iter, więc oba K nie wywołują tam restartu; większy K w dużej antenie ogranicza utratę podprzestrzeni obserwowaną przy RIGHT64. Rachunek129×179499584B≈23,16GB basis, około4,67GB mniej od FP64 resident151iter; przewidywany cgroup około53–55GiB, bez gwarancji, guard pozostaje. Pozostałe parametry: LEFT/FP64/Tol1e−12, wejście i field-reference resident FP64 z EXP12, save-fields, seed256/release/marks, limit1800s. Nie zmieniamy raw gate1e−6 ani progów pól/RF/energii. Nowy artifact m1-antenna-left-tight-correction-20261018. Po FAIL żadnego retry bez nowej diagnozy.


EXP14 pełna LEFT/Tol1e−12/K128 korekta **FAIL/deadline** po1800s, bez OOM/hostguard. Cgroup peak57 916 420 096B (~53,94GiB); brak kompletnego solve, S i porównania pól. Widoczne recurrence przy139iter/restart1 to9,78791e−4 wobec celu około1,67e−8. Ostatnia linia140 jest urwana; ze względu na block-buffered stdout NIE znamy faktycznej ostatniej iteracji. Nie interpretować jej jako wykonanych140iter ani porównania iter/s z innymi runami. Root analiza i SHA logu w artifact/root-analysis.json. Bez automatycznego retry i bez obniżania raw gate.

W obu pełnych korektach brak porównania pól wynika z nieukończenia solvera, nie ze zmierzonego przekroczenia1%. `field_accuracy_passed=false` bez entries nie jest numerycznym błędem pól. Ukończona pozostaje wyłącznie wcześniejsza FP64 LEFT1e−6 referencja wykonania (raw0,125), a niezależna jakość pełnej anteny nadal jest otwarta.

Dodano jawny PALACE_LINE_BUFFERED_LOG w lokalnym runnerze: native main ustawia line buffering przed MPI i emituje marker potwierdzenia; runner wymaga go dla complete. Osobne stdout/stderr pozostają. To usuwa wielokilobajtowe opóźnienie postępu, nie zmienia solvera. Cached build8,298s,25 unittestów PASS. Ostatni krótki replay na tym buildzie ma sprawdzić także0iter oraz nowy marker.

Dalszy kierunek M1: bez kolejnych30-minutowych prób w ciemno. Krótki profil preconditioner/CEED/orthogonalizacja przy wczesnych iteracjach z wiarygodnym logiem; sprawdzić w źródłach, czy niezależna referencja FP64 na CPU RAM może uniknąć thrashingu UVM i jaki jest koszt transferu do cuDSS. Osobno sprawdzić liniowość/złożenie preconditionera oraz rozkład residuum (w tym gradient/charge), zanim dobierzemy korektę. To hipotezy NOT RUN, nie przyczyny potwierdzone. M1 nadal blokuje promocję precyzji i M2, ale nie pomijamy obowiązkowego FEM–BEM.

Końcowa regresja logów/replay PASS: `artifacts/m1-line-buffered-replay-tiny-20261018/`,11,437s,6×0iter, markerlinebuffer/restart/pola/fazy wszystkie true. Żadna pełna symulacja obecnie nie działa. [Wyniki EXP13/14 i ograniczenia](docs/reference-correction.md).


## EXP15 — źródłowo potwierdzony CPU/RAM reference + cuDSS hybrid execute (PLANNED)

Przegląd przypiętego MFEM4.9.0 `linalg/cudss.cpp`: CuDSSSolver::ArrayMult przekazuje RHS.Read()/SOL.Write(), więc ich miejsce zależy od MFEM Device. Dokumentacja odpowiadająca CUDA12.9.1 potwierdza host pointers dla CUDSS_CONFIG_HYBRID_EXECUTE_MODE, odróżniając go od HYBRID_MODE przechowującego faktory w RAM: https://docs.nvidia.com/cuda/archive/12.9.1/cudss/types.html . Sprawdzony kod GMG zeruje initial guess przy pierwszym presmooth; nie dowodzi to pełnej liniowości, ale nie ma podstaw do twierdzenia, że carryover jest potwierdzoną przyczyną.

Nowa hipoteza przed rozbudową mikrobenchmarku: CPU libCEED i FP64 GMRES w RAM + coarse cuDSS hybrid execute mogą uniknąć GPU-UVM working set wielokrotnie większego od16GiB. To wariant REFERENCYJNY M1, nie porzucenie celu CUDA ani promocja produkcyjna. Dodano opt-in --cpu-reference: DeviceCPU,Backend/cpu/self,MFEM_MEMORYhost,8OMP/1OpenBLAS thread, FP64basis, cuDSS execute1. GPU default bez zmian. Niedozwolone FP32basis i GPUQpool wtymtrybie; hybridexecute i hybridmemory nie łączymy. Runner wymaga rzeczywistych markerów CPU backendu i cuDSSexecute, nie ufa samej fladze. --phase-trace włącza istniejący BlockTimer/NVTX trace; osobne logi i linebuffer pozostają. Pamięć robocza wyłącznie RAM/VRAM, CUDAalokacje cuDSS nadal śledzone, brak offloadu/swap.

Cached build8,973s,27unittestów PASS. Najpierw CPU tiny RIGHT warm z LEFTinput i GPU RIGHTfield-reference,6solve, limit120s; raw≤1e−6 i te same progi K.4. Następnie tylko poPASS CPU knownTEM RIGHT/L2,2solve,limit120s,analityczneE/B≤1%. Te krótkie próby jednocześnie sprawdzają zgodność cuDSS0.7.1.4 i hostpointer, zanim wydamy czas na pełną antenę. Dopiero po rootanalizie dobrać jedną dużą kontrolę. Osobny pomiar A/P i liniowości pozostaje dalszą możliwością, nie został zaimplementowany ani uznany za wykonany.


EXP15 pierwszy tiny **FAIL** po3,245s,code4=NOT_SUPPORTED na coarseSOLVE,beziteracji. CPU/backend/execute markery były obecne; nie mylić poprawnego wybrania trybu z ukończeniem solve. Przyczyna źródłowo ustalona: `MfemWrapperSolver<ComplexOperator>::Mult` wysyła nrhs=2 (real+imag), a archiwalna dokumentacja odpowiadająca cuDSS0.7 pozwala hostowe dense vectors tylko dla nrhs=1 (https://docs.nvidia.com/cuda/archive/12.9.1/cudss/advanced_features.html). To nie ogólny brak obsługi CPU ani OOM.

Konkretna poprawka przed retry: tylko gdy PALACE_CUDSS_HYBRID_EXECUTE=1 i wrapper używa mfem::CuDSSSolver o rozmiarzeN dla zespolonegoN, wykonujemy dwa niezależne Mult po1RHS. Realny preconditioner algebraicznie działa osobno na real/imag; default ArrayMult2 na CUDA pozostaje. Runner wymaga markera faktycznego przejścia serialRHS. Nie patchujemy/rebudujemy zależnego MFEM. Filtr z nowym sufiksemr2 i znanym patchem, potemTEMwyłączniepoPASS;brakpełnegoGPUretry. 27unittestówPASS.


EXP15 r2 oba filtry PASS po serialRHS fix. CPU RIGHT warm tiny19,678s,40/38/37/41/39/38iter; actual raw RELATIVEmax9,7803867e−7 (wartość2,3343e−7 to ABSOLUTE, nie relative). Względem GPU RIGHT max|ΔS|9,156e−16,ΔVSWR1,333e−15,energia0; polaE≤1,934e−14/B≤1,508e−13. Rootanaliza i SHA w `artifacts/m1-cpu-right-tiny-r2-20261018/root-analysis.json`. TEM CPU19,843s,62/64iter; rawrelative8,5273e−7/9,0263e−7, E_L2q6≈0,49531%,B≈0,45578%,oba<1%. Konfiguracjaaktualniefaktycznieomp,cpu/host-std/cpuavx,execute1/serialRHS1. TinyCPU nie jest szybsze od dawnego GPUtiny; to walidacja alternatywnej referencji, nie speedup. Cgroup756/821MB i sampledGPU245MB to mały przypadek, nie budżet pełnej anteny.

Następny POMIAR workset z limitem300s: `python3 tools/dev.py run tshaped-medium artifacts/m1-cpu-antenna-replay-20261018 --seconds 300 --basis fp64 --cpu-reference --hypre-pool-mib 256 --release-gmres-basis --memory-marks --phase-trace --pc-side left --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m1-antenna-resident-fp64-20261018 --background`. Oczekiwanie0iter jak przy replaytiny, oryginalneTol1e−6 iK240,beznowejreferencjidokładności. Porównaniepól/RFdozaładowanegowynikupotwierdza przeliczenietego samegoFEM,nierozstrzygaraw0,125. PomiarbaseworksetitimerówpierwszychA/P pozwoli dobraćK dlawiarygodnejkontroliprzednastępnąpełnąkorektą. Cgroup60GiB/guard6GiB bez zmian,poFAILstop. Brakpaidcompute/offloadu/swap,niezmieniamyźródełwczasierunu.


EXP15 CPU large replay **FAIL/cgroup OOM** po247,6s, exit137 iOOMKilled=true, nie deadline ani hostguard. Osiągnięto0iter i rawRELATIVE0,1252666005, lecz brakS/pólkońcowych;niekwalifikować. Ostatni zaobserwowany cgroupHWM63,102GB(~58,77GiB), próbkowanie może nie uchwycić chwilowego szczytu przedOOM przycap60GiB; minhostavail7,47GiB>guard6. Managedpeak8,901GB nie obejmuje CPUheap; nie sumować z cgroup. Telemetria: około30GiB przedGMRES, około40GiB po pierwszych aplikacjachP, szybkiwzrost>58GiB przy postprocess. To mierzalnie wyklucza prostąCPUreferencję wtymprofilubezmodyfikacjipamięci.

Krótki profile trace dał dwie inkluzywne aplikacjeP13,616/12,464s;coarse1,182/0,133s zawiera się wP. PozostałyczasP≈12,43/12,33s,jednak dwa różneinputy i warmupnie są benchmarkiemmedianowym. CPU nie promować: fullOOM i brakprzewagiczasu. Napotkaneproblemy nieuzasadniają zwiększaniacap/guard ani powtarzaniapełnychrunów. Rootanaliza+SHAw artifact/root-analysis.json. OsobnytestliniowościA/P nadalNOTRUN.

## EXP16 — dokładny zespolony coarse solve (TINY FILTER PASS)

Kod currentMfemWrapperSolver<ComplexOperator>::SetOperator przy ComplexCoarseSolve=false tworzy realAr+Ai; przytrue tworzy równoważny rzeczywisty blok [Ar Ai;Ai −Ar] i odtwarza znak imag. To istniejąceAPIupstream, nie nowysolverani zmianarównaniaA. Hipoteza: lepsza reprezentacja fazy coarse zmniejszy liczbę iteracji RIGHT do wiarygodnego raw, kosztemwiększychfaktorów. Nowyopt-in --complex-coarse wymusza ComplexCoarseSolvetrue/PCMatShiftedfalse,inneparametrymediumbez zmian. Na razieniełączymyCPUprofile (niekwalifikowanekombinacje),GPUdefault bez zmian.

Najpierwten sam GPUtinyRIGHTwarm6solve coEXP13/K128,limit120s,FP64/seed256/release/marks/trace,inputLEFTold,referenceGPURIGHT. Qualitygates:raw≤1e−6,complexS≤1e−3,VSWR≤0,01,energia/power≤1e−3,polaE/B≤1%. Promisingfilterprzedjakąkolwiekpełnąpróbą: suma iteracji≤70% z233w zwykłymRIGHTwarm i faktorpeak≤3×tinydefault. To filtrkosztu, nie gwarancja skalowania dużejanteny. Jeśli nieprzejdzie, zapisaćodrzuceniei nie uruchamiać dużej. 28unittestówPASS,zmianyrunnera nie wymagająprzebudowynative.


EXP16 tiny RIGHT **PASS filtr**, nie promocja anteny: 153 iteracje vs233 (−34,3%), 12,534s; raw relative≤9,101e−7. Root sprawdził S z prawidłowym przeliczeniem dB/stopnie→complex (nie Re/Im): max|ΔS|2,511e−8, ΔVSWR2,641e−8, Δpower2,952e−8, względna energia1,277e−7. PolaE≤2,240e−7/B≤2,286e−7. FaktorycuDSS167934380B vs61473620B, 2,732×: mieści filtr≤3×, ale większa antena może mieć inny fill. Rootanaliza+SHA w artifacts/m1-complex-coarse-right-tiny-20261018/root-analysis.json.

## EXP17 — zwolnienie finalnego solvera (TINY PASS, FULL GUARD)

Opt-in --release-final-solver tylko fixed-mesh uniform sweep. Po ostatnim rzeczywistym porcie/freq i kompletnych kontrolach GMRES zapisuje metadata, niszczy KSP (z faktorami) przed A/P/A2/K/C/M; zachowuje Curl, E/B, RHS, przestrzenie i materiały potrzebne pomiarom. Default bez zmiany matematyki/lifetime; brak AMR/adaptive qualification. Marker dokładnie1× i opcjonalne fazy linear_workspace_release.begin/end. Cel: nie trzymać martwych faktorów podczas dużych buforów pomiaru pól. Nie ograniczamy jakości, nie wyłączamy walidacji pól. Pamięć wyłącznie RAM/VRAM, bez dyskowego workspace/swap.

Build cached9,635s,29unittestówPASS. Pierwszy filtr: ten samtiny6solveRIGHT/FP64/K128/complexcoarse, dodane release-final-solver; reference pola z EXP16. Tolerancje RF jakEXP16; identyczne iteracje i S/energie oczekiwane, tylko zmiana lifetime. Jeśli FAIL stop. Dopiero poPASS jeden full GPU RIGHT/complexcoarse/K64,1800s,cap60GiB/guard6GiB,initial/referenceEXP12. Warmstart nie dowodzi jakości referencji; raw≤1e−6 i pola/RF pozostają wymagane. Szacunek pamięci nie jest dowodem dopasowania pełnego przypadku.


EXP17 tiny **PASS**: identyczne153iteracje,12,567s, raw≤9,101e−7. Pola względemEXP16 E≤3,069e−15/B≤1,508e−13. Root CSV: max zmiana S w jednostkach dB/stopnie2,501e−10, I4,801e−18A,V2,411e−16V, energia0; zgodność do zaokrągleń, nie bitwise. Final release dokładnie1×: managed386820886→127942182B (−258878704B); cuDSS167934380→0B. Peak tiny nie zmniejszył się (występuje wcześniej), więc nie obiecywać redukcji globalpeak. Cgroup578367488B/GPU631242752B. Rootanaliza w artifact. Następny full zgodnie z predeclared1800s/K64; bez zmian źródeł podczasrunu.


EXP17 full complex-coarse RIGHT/K64 **FAIL host_memory_guard** po399,828s,exit137,OOMKilled=false. ContainerExited/PID0potwierdzone. Ostatnia rzeczywista wypisana iteracja16/restart0, recurrence1,339219e−2; brak końcowego raw/S/pól. Zbieżność częściowa silniejsza niż realcoarse EXP13, ale nie jest PASS ani porównaniem czasu do wyniku. Cgroup61550936064B(~57,33GiB), GPU-process5280628736B. Przy preconditioner.end cuDSS live30641370420B, setup110,957s. Ostatni zaraportowany logical managed HWM48998044042B pochodzi sprzedGMRES, nie z końca runu; nie sumować faktorów (są wewnątrz managed). Nie podnosimycap/guard, nie zamykamyaplikacjiużytkownika i nie retry tego samegokonfigu. Rootanaliza+SHA w artifact.

Następny najmniejszy krok M1: zbadać bezpośredni FP64 complex-coarseN×N zamiast obecnego realnego bloku2N×2N; najpierw mały, wytworzony układ/probe API pinnedcuDSS0.7 i pomiar, następnie coax/TEM tylko poPASS. Archiwum dokumentacji12.9.1 types opisuje SYMMETRIC jako realny, HERMITIAN nie jest właściwy dla ogólnego kompleksowo-symetrycznego Maxwell; dla prototypu zacząć od poprawnego GENERAL/CUDA_C_64F, nie narzucać Hermitian ani obiecywać 2×oszczędności. Źródło wrappera palace/linalg/solver.cpp tworzy[Ar Ai;Ai−Ar]. To hipoteza zmniejszenia faktorów bez obniżenia precyzji, nie wykonany eksperyment. FP32coarse/TCnadalniepromowane; M1otwarty.


Checkpoint integracji EXP15–17: docs-garden LunaPASS, rootdiffreviewPASS,29unittestówPASS,docscheckerPASS (istniejące miękkie591tokAGENTS),gitdiffcheckPASS,manifest source/native/depsPASS. Cachednativebuild9,635s. Zmianywyłącznieopt-in; fullqualityM1nadalOPEN. Żadnej symulacji pozostawionej live; bezcloud/paidcompute. Commitlokalny, niepushupstream. Następnie przygotować mały nativecomplex FP64probe; nie ponawiaćfullblokowego wariantu.


## EXP18 — native complex FP64 API probe (PLANNED)

Cel M1: uniknąć realnego bloku2N×2N dla dokładnego coarse solve, bez redukcji precyzji. Najpierw samodzielny known-solution probe pinnedcuDSS0.7: ten sam kompleksowo-symetryczny, nie-Hermitowski stencil3D, dwa RHS i refaktoryzacja zmienionych wartości przy stałym wzorcu. Porównać CUDA_C_64F/GENERAL N z równoważnym realnym blokiem2N/SYMMETRIC; sprawdzić x/rawrelative i cleanup. Dane i faktory wyłącznie managedRAM/VRAM; żadnych zależności rebuild. Limit60s/2GiB,noextraswap. Kryteria przedrunem:relative_solution i raw_rhs_relative≤1e−10, zero live cuDSSallocatorbytes poDestroy i poprawna liczba case/update. Pomiar małychpeak/time jest filtremAPI/reprezentacji, nie prognozą pełnegoantennafill ani speedup. Integracja coarse w Palace dopiero poPASS. Źródło API: archiwum CUDA12.9.1/cuDSS functions i types (sprawdzone2026-10-18); licencja kodu własnego taka jakforkApache2.0.


EXP18 **PASS**:512complexGENERAL i1024realSYMMETRIC, nrhs2×2aktualizacje. Relative_solution/native6,96e−16,block1,24e−13; raw_rhs/native2,67e−16,block5,47e−14. CuDSSpeak2637284B vs4920228B (−46,4%),live0poDestroy. Build2,049s,run2,985s,31unittestówPASS. Czasy faz mocno cold/order-biased (complex pierwszy1,1sfactor,realpóźniej~0,002s),nie uznajemy za benchmark szybkości. FilterAPI nieprognozuje fillpełnejanteny. Rootanaliza+SHA w artifact. Następnie mała opt-in integracja nativecomplexcoarse dla jednegoMPIranku w Palace; FP64operator/tolerancje bez zmian.


## EXP19 — opt-in native complex coarse integracja (PLANNED)

PoPASS EXP18 integrować ComplexCuDSSSolver<Solver<ComplexOperator>> dla rank1GPU; bez realbloku2N, FP64GENERAL. Konstruować CSR unionAr/Ai, wyłącznie RAM/VRAM. Domyślny solver iMGM/CPUbez zmian, profileCPU/hybrid/FP32adapterzabronione. Pierwsza wersja jawnie refaktoryzuje i wykonuje analysis przy każdymSetOperator (reuseM4później); pakujevec przezistniejąceComplexVector.Get/SetGPU, synchronizuje dla poprawności. To koszt prototypu, niepromocja. Filtrtiny6solveRIGHT/K128/Tol1e−6,porównanieEXP16complexblock: raw≤1e−6,|ΔS|≤1e−3,ΔVSWR≤0,01,energia/power≤1e−3,E/B≤1%; potemTEM<1%. Rachunek dużegoRAM dopiero po rzeczywistychpeak/timefiltrów. BrakwiększejantenyprzedPASS,limitybez zmian.


EXP19 pierwsze tinyFAILsegfault5,294s,nieOOM,przedsolve. StackClearGPUSparse→cusparseDestroySpMat zSetOperator. Źródło pinnedMFEM4.9: SparseMatrix ma CUDA_VERSION-zależny layout, GetDiag tworzy/wymienia wrapper i defaultkonstruktor inline wołaInitGPUSparse. Nowycomplexcudss.cpp był błędnie kompilowany jako hostCXX przy późnym includeCUDA; istniejącycudss.cpp jest wTARGET_SOURCES_DEVICE. Konkretna poprawka: dodaćnativeplik do tej samej listyCUDA i compile-time#error gdy wróci dohostCXX wMFEMCUDA. Dodatkowo jawneClear po skopiowaniu CSR przed zwolnieniemassembly, kontrola wymiarów. Retrytinywyłączniepo tej poprawce, nowy suffixr2; bez zmiany fizyki/progów.


EXP19 r2 **PASS** po CUDAcompilefix:6×native17146/260044nnz, te same26/25/24/27/26/25iteracje co exactblock,12,529s. Rawmax9,101e−7, polaE≤3,270e−15/B≤1,506e−13 względem EXP16. CuDSSpeak113329412B vs167934380B (−32,5%), cgroup529842176B vs578367488B (−8,4%w tejparze), sampledGPU631242752B bez zmiany. To redukcja małego przypadku,nie oszacowaniepełnego fill. Nativephase30% mniejfaktorów daje podstawędoTEM, nie promocję. RootRFanaliza+SHA w artifact. NastępnyfiltrTEM3,55GHz/2porty FP64RIGHT,natywneL2kwadratury4/6,limit120s; progiE/B<1%,raw≤1e−6. No pełnyrun przedPASS.


EXP19 TEM **PASS**:3,55GHz2ports,39/42iter,18,729s,raw_rhs≤9,594e−7. NatywneL2q6E≈0,49531%,B≈0,45578%,oba<1%; q4zgodne. Native17146/260044nnz dwukrotnie, cuDSS113329412B,live0porelease. Cgroup597676032B/GPU631242752B. RootsprawdziłlogdokładnychL2/raw; bezpromocji pełnej anteny.

Następny jeden fullGPU RIGHT/K64/nativecomplex FP64,1800s,initial/referenceEXP12, savefields,seed256,obarelease,trace/marks. PreflightbieżącegoRAM;cap60GiB/guard6GiBbez zmian. Orientacyjnybudżet: dotychczasnonfactor~18GB +nativefactor~21GB (tylkoekstrapolacja ztiny,niegwarancja) + do12GBbazy + ok7GBworkingMG i cgroupdelta. Ryzykofill/hostguardjawne; niepowtarzać poFAIL bezdiagnozy. Raw1e−6,E/B1%,complexS1e−3,VSWR0,01/energy-power1e−3; staryEXP12zraw0,125 niejestdowodem prawdziwościreferencji,każdąrozbieżnośćinterpretować bezpoluzowaniaprogów. Brakpaidcompute/diskworkspace/swap.


EXP19 full native **solver COMPLETE/quality NOT PROMOTED**:419,08s,35iter,rawRHSrelative8,35543e−7 (RIGHTniezależnieponownieAx−b),VSWRP2@3,5GHz≈1,668. NativecoarseN2196005,nnz32284067,cuDSSpeak25008217684B (~23,29GiB),managedpeak55147611962B,cgroup58895593472B (~54,85GiB),sampledGPU2GiB. Finalsolver/basisreleasePASS,45vectors8077481280B,allocatorlive0. OOMfalse,guardnietrigger,minhostavailable11,82GB. ZreferencjąEXP12:globalE0,1774%,B0,5910%,ale regionalB2=1,1656%/B4=1,2094% >1%. KryteriumK4FAILvsstaryniekwalifikowanyref; nie promować ani nie podnosićtolerancji. Wynik może być dokładniejszym rozwiązaniem starych równań,ale wymaga kontroli. Czasy419vs1089s nie są kontrolowanym speedup:innePC,stronaiwarmstart. Rootanaliza+SHAwartifact.

Następny testreferencjiFP64: ten samnativerightK64,mediumbez zmian, --linear-tol1e−9,warmstart z nowegoEXP19full,porównaniepóldoEXP19full;1800s/cap60GiB/guard6GiB. To3rzędyostrzejszyraw cel,niepoluzowanie. Oczekujemy małej korekty,raw≤1e−9 i pola≤1%/S≤1e−3/VSWR≤0,01/energy-power≤1e−3. Jeśli nieprzejdzie, niepromować i nie retry bezdiagnozy. Nowyinput jest ukończonym solve,niecertyfikatemdokładnościpól. Celem jest stabilność numeryczna i diagnostyka niekwalifikowanejstarejreferencji,nieomijanieM1.


Tightcheck pierwszypreflight **NOTRUN**: obecnyverifierodrzuciłEXP19także jako input zpowodufield_accuracy_passed=false. Nie uruchomiłGPU. Naprawasemantyki: --field-reference nadalBEZWZGLĘDNIEodrzuca takąreferencję (regresjapozostaje), --initial-fields osobnoprzyjmujeukończone,bajtowozweryfikowane snapshoty zgodnejfizyki jako PRZYBLIŻENIEstartowe. Wciążodrzuca niekompletność,zmienionefizyki,uszkodzenia/deps. command.json jawniezapisujesourceaccuracyfalse orazscopeinitialonly.33testsPASSwtymrolereference-vs-initial; bezrebuildnativeboPythononly. To niezmianaprogów/zaakceptowanierejectedaccuracyjako wzorca.

Konkretne nowe argv tight-r2: bez --field-reference, z --initial-fields EXP19full iTol1e−9,savefields. Najpierw strictejszesamodzielneFP64rozwiązaniezraw≤1e−9,zapisane jako kandydatreferencjiM1. Potem dopierorozwiązaniemediummożebyćporównanezTIGHTjako referencją (nie odwrotnie); progiK4pozostają1%/1e−3/0,01. Do tego czasuM1otwarty,żadnejpromocji. RóżnicezEXP12takżewS=0,0011899>1e−3,zachowaneFAIL. Limit1800/cap60GiB/guard6GiBbez zmian.


Tight-r2 **COMPLETE**:360,946s,24iter,niezależnyrawRHS7,28157336e−10 (threshold3,00779933e−8absolute),FP64nativeN2196005/32284067nnz. No fieldcomparison wtymrunnie,niezaliczaćjeszczeK4. CuDSS25,008GB/live0,managed53,173GB,cgroup56,916GB(~53GiB),GPU-processsample2GiB;hostmin11,782GB. SnapshotyE/Bkompletne/SHA. RootporównałS/energie docandidatemediumnative: bardzo mała różnica,zachowana w root-analysis.json. To silniejszykandydatreferencjiM1,niepromocjainnychoptymalizacji.

Następnyjeden W3fullbezszczegółowegoBlockTimertrace: nativeRIGHT/FP64/K64/Tol1e−6, initial=oryginalnyEXP12 (ten samstart coEXP19traced35iter), field-reference=tight-r2,savefields. Limit900s,cap60GiB/guard6GiB,seed256/obarelease/marks,bez--phase-trace. Oczekujemy35iteriK3/K4PASS; nie używamy0iterreplay jako benchmarkusolve. Tenrun ma wykazaćstabilnośćpólwzględemostrzejszejreferencji i pełnykosztbeztrace. Warunki tła i warmstart podane; nadalnieporównywać419/1089jako czystegospeedupu względemzimnegoLEFT. PrzyFAILstop.


EXP19 fullqualified **W3/K3/K4PASS**:bezphase-trace,447,462s,35iter,rawRHS8,35543267e−7. VSWRP2@3,5GHz=1,6684235. Porównanie do tight-r2raw7,282e−10: E/Bwszystkichregionów≤9,886e−8 (relative), dużo poniżej1%; rootRF/S/VSWR/energia/powerPASS, dokładneliczby+SHAwroot-analysis.json. Nieprzestawionoprogów;staryEXP12 pozostaje niekwalifikowanąrefwykonaniazraw0,125,anowąreferencjąM1jestściślejszeFP64solve. NativeFULL1055alloc/CUDSS47alloc/live0;faktorpeak25,008GB,UVM55,148GB,cgroup58,899GB,GPU-processsample2GiB,minhostavail9,908GB;bezOOM/guard. To jeden punkt/portbenchmarkFEM,niekwalifikacja całejantenyprodukcyjnej ani precyzjiTF32/FP32.

Phase-table fullbeztrace:setup93,545s,GMRES259,460s(zawieraP/coarse),post7,610s+field4,286s. Nativebeforefinalrelease45,342GiBmanaged→8,650GiB (−36,69GiB),cuDSS0porelease;postmanaged24,009GiB,nieutrzymujefaktorów. Stdtableexclusive:LinearSolve29,165s+Preconditioner158,248s+Coarse72,105s≈259,52s,niesumowaćdoGMRESinclusive. UVMtransfers/kernelattribution nadalNOTMEASURED wtejwersji; historyczneNsightlosteventsopisane. M1.4 orazpełnabilansDOF/pamięciM1 pozostająotwarte; nieprzeskakiwaćM2dopóki całabramkaM1niespełniona.


Fallbackregression nowego binarium **PASS**:6solve233iter,13,650s,rawmax9,781e−7,polaE≤3,467e−15/B≤1,502e−13,marker native nieobecny. CuDSS61473620B/live0,UVM331344422B. Regressions33PASS. Brak aktywnych runów po kwalifikacji. Native11,682s cachedbuild; osobnyprobe2,049s/drugibuildcachehit; brakrebuilddeps. M1referencjaW.3uzyskana,profilkerneli/transferów i pełnybilanspamięci nadalotwarte. Po docs-garden/rootdiffreview lokalnycommit (upstreamniepushować).


Domknięcie docs/codeEXP18–19: docs-gardenLuna33testsPASS,rootpoprawiłstareopisyINDEX/M1 i dodałhistorycznepointeryw memory-phases/optimization-baseline. Dodatkowycorelimit0: devrunner+probe --ulimitcore=0:0; prawdziwy pinnedruntime /bin/sh ulimit-c zwrócił0, coredumpctl dla pierwszegopalacesegfaultunieznalazłdumpu. To lokalnylimitkontenera,bezglobalnychzmianOS. Przebudowanywyłącznieten samprobe1,932s,hashbinariumidentyczny; nativemanifestf35d5d0a26e23ec88b4237854bb0a17f41770cbe7a6f1d2fa2832827ba213f86zweryfikowany. Brakfullretry zpowodudokumentacji.


Checkpoint przed commitemEXP18–19: końcowy docs-gardenLunaPASS,rootdiffreviewPASS,33unittestyPASS,docscheckerPASS (istniejące miękkieAGENTS591~tok),gitdiffcheckPASS,source/native/depsmanifestPASS. Wszystkie przygotowane symulacje terminalne, brakpalace-run kontenerów. WorkingstoragewyłącznieRAM/VRAM,corelimit0zweryfikowany;bezpaidcompute. Lokalnycommit,niepushupstream. DalejM1.4krótkiprofildanych/kerneli/UVM i pamięci; nieaktywowaćM2ani nieukończyćgoal bezpozostałychdowodów.


## EXP20 — krótkie okno kerneli/UVM (ACTIVE)

M1.4: Nsight2026.5.1CLI z oficjalnegoNVIDIA225594886B, SHA61829db6392e5c293ada1319df86a97c3356bc810335a1975cb551fcfe3eca08. Wyodrębniony lokalnie bez zmianCUDA/OS; runtime--versionpotwierdza2026.5.1.161. Poprzedni2025profilmiałlostevents; nieliczyć naobecne wyniki. Nowyprofil ma nativeNVTXokno FIRST:COUNT zregisteredrange Krylov sample@palace, a natywny solver synchronizuje CUDA i kończy kontrolowanym wyjątkiem po kilku iteracjach; main przechwytuje go przed niepełnym RF postprocessingiem. Nsight używa --trace=cuda-sw,nvtx oraz --kill=none. Profile jest świadomieczęściowy,nieRFcompletion/PASSsolution.

Najpierwcoax-tinyFP64nativeFIRST1:COUNT2,limit120s,cap60GiB/guard6GiB; potem pełnasiatkaFIRST2:COUNT2,limit600s poAPIprofilePASS,bezpowtarzania całego solve. Tracecuda,nvtx,CPU sampling/contextswitch/off,UMperpagefaultsoff; zliczyćmigracjebytes/kerneliinadzór nadutraconymizdarzeniami. Temp/logbuforyprofilera wtmpfsRAM; zachowaćmałyreportjakozwykływynik(max64MiB),podsumowanieSQLitewstdlib. DaneFEM/baza/macierz nadalRAM/VRAM,corelimit0. Progi przedprofilem:obaNVTXmarkery i2pełneiteracje,niezerowekernel/transferrecordygdyobecne,braklost/mismatch/nieobsługiwanejwersji; liczbęnieznanychprzypisańraportowaćnieukrywać. Nieinterpretowaćczęściowego okna jako całego benchmarku ani sumyGPUtimejako walltime.


EXP20 pierwszy tiny: 9,36s, exit143, 1409 kerneli, ale SQL DIAGNOSTIC_EVENT zawiera ostrzeżenia o możliwie niepełnych CUDA/NVTX events i fallback HW→software. **REJECT dla wiążącej atrybucji**. Pierwotny profile_complete=true był błędem walidatora (sprawdzał stdout, nie SQL). Zachowano oryginalny wynik i osobny root-analysis.json z korektą. Poprawka: SQL warning gate, wymagany clean-stop marker, jawne software tracing, sync+kontrolowane unwind bez SIGTERM, PID celu z dzieci wszystkich wątków. 38 regresji PASS; następny jeden tiny r2, przed full krótkim oknem. Żadnego disk workspace ani zmiany tolerancji.


EXP20 dalsze małe filtry: r2 8,438s clean-stopFAIL (stop-shutdown kończył sesję przed cleanupem celu); r3 8,55s clean-stopPASS po stop/waitall, CUDA+NVTXwarnings; r4 8,44s cudaProfilerAPI+flush nie usunęływarnings; r5 9,41s cały boundedproces bez triggeredcapture: CUDAwarning zniknął, NVTXwarning pozostał. **Wszystkie REJECT profilowania**, brak RF i brak full antena retry. Obecny kod zachowuje prostszy wariant r5: sync+nativeunwind, wholeprocesscapture, okno iteracji wybierane po NVTX offline. TargetPIDtelemetry poprawiona i zmierzona; wszystkie temptrace/SQLite w/dev/shm, final małe raporty zwykłe wyniki. Buildy przyrostowe8,6–8,9s, brak dependencyrebuild. NieaktywowaćM2 na podstawie tych profili.

## EXP21 — rzeczywiste DOF i bilans resident pamięci (PASS zakresu audytu)

`tools/mesh_cost.py --dofs` liczy unikatowe wierzchołki/krawędzie/ściany tetra i materialincidence wRAM, bez plików roboczych; 17,349s, maxRSS663875584B. SHAmesh identyczne W3. 383949vertices/2196005edges/3413357faces/1601320tet; ND2=11218724,H1p2=2579954,RTdegree1=15044031 — wszystkie zgodne z runtime. AIRexclusive6460374DOF=57,586%; pozostaje4758350nonair/shared, nie jest to dowód speedupu. Obecny exteriorsurface94200ND2traceDOF: jeden densecomplex128blok141978240000B (~132,23GiB), vs wcześniejszy RWG-edge estimate11,90GiB dla innej przestrzeni. FEM–BEM wymaga kompresji/FMM lub odpowiednio dobranej mniejszej powierzchni i jawnej kwalifikacji dyskretyzacji.

Bilans na tym samymEXP19gmrespeak55147611962B: cuDSS25008217684 + netVrelease6461985024 + inne linear-solvernetrelease14390057060 + pozostaje9287352194 = dokładniepeak. Vnet odpowiada36complexNDwektorom, podczasgdycapacitylog45; nieutożsamiać host/device/mirrors. Netrelease nie rozstrzyga właściciela każdego bufora, a cuDSS już zawarty wmanaged. Źródła/SHA/checks w artifacts/m1-topology-memory-balance-20261018.json oraz m1-mesh-dofs-20261018.json; docs/topology-memory.md. 41regresjiPASS. M1 nadalotwarty, brakpromocjidefaultów.


EXP20 normalpath regression (profiling OFF):6/6coaxsolvePASS,12,545s,rawmax9,10045e−7; maxΔcomplexS9,09e−16,E3,18e−15/B1,51e−13względemnativetiny-r2. Profilemarkerynieobecne; releasememorygatesPASS. Artefakty artifacts/m1-nsys-normal-regression-20261018 oraz root-analysis.json. 41testsPASS; docs-gardenLuna/rootreview: przywrócono właściwy opis --trace=cuda-sw,nvtx (r5jawnysoftwaretrace, niehistorycznyHWfallback). Dodano gateexit0/noOOM i cleanupRAMtakże przy wyjątkach runnera. M1/goal pozostająaktywne.


## EXP22 — domknięcie bieżącego profilu i alokacji

Directenvr6 i filtrCCCLr7 nieusunęłyNVTXwarning; hipotezy odrzucone. CUDA-only+hostclocktiny r8PASS, ale fullshort z identycznymczasem w hostclockcallee FAILkalibracji; jegoRAMreport216MB/SQLite660MB zostały usunięte zgodnie z limitemretencji64MiB. Nie rekonstruowaćprzyczyny bez surowychdanych. Run267,39s dostarczył aktualnytracealloc,któryniezależyodNsightclock: peak49583124858B,duże49392771376B,unknownsmall190353482B. TriggerComplexParOperatorMult/GMRES,20buforów538043520B; tabelawdocs/memory-audit.md, raportartifactm1-native-current-allocation-audit-20261018.json.

Nativecached8,813s/9,851s/8,619s bezdependencyrebuild. Dodanohostscopes i3labeledCUDAmarkers. Affinefitendpoints/held-outmid+10µsexplicituncertainty, ambiguitymarked zamiastwymuszonejatrybucji. CaptureCUDAProfilerAPIr9tinywarning→REJECT; wholeprocessCUDA-onlyr10tinyPASS9,43s, heldout553ns,6boundarykernels.47testówPASS obejmuje offset/niezgodnyczas/nieliniowymarker i uncertaintyboundaries; progifizyki bez zmian.

Fullshort `artifacts/m1-cuda-affine-antenna-20261018` **profilePASS**: nativeexit0/noOOM/noGuard, cleanpartial4iter, scope2:2@3,50GHz/P2. Clockscale1,00000012239,heldout1127,2ns,containment667,25ns,margines10000ns;4939ROIkernele/1ambiguous/0unmatched,25hostranges. P16,278s(coarse5,490s),orthog0,156s,window17,665s. UVMHtoDpagefault11,549GB,prefetch136,977GB,DtoHeviction146,945GB;D2D15,186GB. Migracjesum295472009216B,nieunikatowepages;czasówGPU/UM/hostniesumować. Reports214MB/SQLite652MBRAMonly,JSON+SHAzachowane. Całyprofil269,94s niejestbenchmarkiemRFspeedup;managed49,583GB,cgroup56,856GB,minhost8,855GiB. Rootanaliza/SHAwm1-cuda-affine-antenna.../root-analysis.json.


DomknięcieM1: normalpath m1-cuda-affine-normal-regression-20261018 complete/fields/releasePASS,6solve13,674s,raw9,10045e−7,E3,0631e−15/B1,5036e−13,ΔS7,813e−16.47tests/docschecker/diffcheckPASS; docs-gardenLuna i rootreview. Brakpromocjidefaultów, brakpełnegosweepa. M1gates zestawione wdocs/milestones/M1.md; aktywnyM2, goalcałośćnieukończony.

## EXP23 — niezależny Maxwell PEC/Mie oracle

Przypięto Bempp-cl a1eaaef9…/MIT i H2Opus cbc7985d…/BSD3; API i granice w docs/maxwell-oracle.md. BemppCPUoracle, nie nativeCUDA; H2Opusreal-onlytypedef, complexintegracja niepotwierdzona. ExaFMMwrapper używa.tmp — nieaktywny, przyszłybackend wymagaRAMaudytu. Prywatny Python3.12.15/uv/JITcache, braknative/dependencyrebuild.

Pierwszylaunch m2-pec-sphere-level1-cold-20261018 FAILexit127/Pid0/0,19s: brakmountaliasuuvPython, fizykaNOTRUN. Rootnaprawiłmount+regresję. Luna wykonała3CPUruny120/480/1920RWGDOF,19,32/19,81/33,89s,exit0/noOOM. PoleMiecomplex8,899/2,254/0,5643%;scatter14,855/3,838/0,96565%;raw≤8,77e−15. Level1/2analyticFAIL,level3PASS, niezmienny1%próg, bezfitufazy/amplitudy. Phase/opticaltheorem/Rayleigh/BesselSciPychecks. Level3RSS452MB/matrix58,98MB; wzorzecCPU, nieantena/ports/interface.

## EXP24 — complex H-matrix i CUDA apply (jakośćPASS, bezpromocji)

Root: geometricalcluster wsparćRWG/exactnear/complexSVDfar, Frobenius1e−6/leaf64/eta2. Przedrunem progiaction1e−5/rawOriginal1e−6/Δsolution1e−3/Δfar-field1e−4. Pierwszargv z kropką kończącą zdanie: argparseFAIL, nicnieuruchomione. Jawnaargvlista→m2-pec-hmatrix-cuda-level3-20261019 ukończony40,868s/noOOM.984bloki/248compressed, compression0,1556s, CPUGMRES170iter/0,6423s. Matrix58,9824→53,5795MB(−9,16%), originalraw1,591e−9/Δsolution2,275e−8/Δfar-field1,096e−11, analyticfield0,5643%; qualitygatesPASS.

CUDAcomplex128cublasZgemvapplyonly: explicitalloc59,0439→53,6414MB;8warmroundtrips0,1010→5,3194ms,52,68×wolniej. Python/PCIe/sync+CUDA, niekernel-only; brakTC/UVM. Denseoracle/kopiepozostająwRAM,RSS1,404GB; brakpeakRAMsaving. Nieintegrowaćper-blockdispatch jako speedupu i nieekstrapolowaćnaantenę. Dalej batch/nativeapply, kompresja/scalableassembly, dielectricMie/FEM–BEMinterface. M2.1–M2.4 nadalniepełne,M3nieaktywny.55unitPASS, bezpaidcompute/closedapps/diskworkspace; Palace/mediumdefaultsbez zmian. Docs-gardenLuna/checker/diffcheckPASS; rootpoprawiłstarylicznik47→55 wtesting i sprawdziłkod/źródła/SHAartefaktów. Lokalnycommitbezpush; goal/M2aktywne.


## EXP25 — plan i wynik

EXP25 plan przed runem (2026-10-19): izolować koszt dispatch od matematyki
EXP24. Ta sama H-matrix FP64/leaf64/eta2/tolerancje; native packing i dwa
kernele CUDA zamiast984Python/cuBLAScall. Porównać exactdense/cuBLASperblock/
native w jednym procesie, action≤1e−5 i dotychczasowe raw/fieldbez zmian;
zmierzyć wszystkie jawne alokacje wraz z metadanymi i round-trip osobno od
GPUeventtime. CachedjednoTUbuild≤120s, oracle≤180s/6GiB/noSwap, RAM/VRAMonly.
Brak promocji anteny na podstawie małego operatora; wynik i decyzja poniżej.

Native2kernelkompilacja1,752s/cachehit; max180soracle40,565s/noOOM. Ta samaeta2: nativeapply0,2114ms vsper-block5,2371ms i dense0,1220ms. HybridGPUoperator/CPUbasisGMRES170iter/0,07770s, rawOriginal1,591e−9/Δsolution2,275e−8. Bezpromocjianteny; niepełnyGPUsolver.


## EXP26 — plan i wynik

EXP26 planprzedrunem: po udanym EXP25native sprawdzić jedną zmianę eta2→4
(szersza dopuszczalność kompresji wyłącznie rozłącznych supports). Leaf64,
SVD1e−6, cała geometria i qualitygatesbez zmian. Sprawdzić dane/meta/workspace,
nativeapply/cublasdense/CPU iGPUoperatorGMRES. Limit180s/6GiB/noextraswap;
budżet natywnej biblioteki bezrebuilda, bezpromocjianteny zmałegotestu.

Eta4PASS/noOOM/40,819s. Matrixdata58,9824→48,7699MB(−17,31%); nativealloc49,5404MBwrazmetadata/workspace. Nativeapply0,1875ms vsdense0,1016ms, więc nadalwolniej. Hybrid0,07494s/170iter/raw3,218e−9; farfielddelta2,681e−11. PeakRAMniespadł, fullassemblydensepozostaje.


## EXP27 — plan i wynik

EXP27 planprzedrunem: kontrola dielektryka PMCHWT/Maxwell na kuli ka1/εr2,94/μr1,
według scaledmultitrace przypiętego Bemppdielectricexample, allRWG/SNC.
Nowy niezależny dielectricMie (transparent/Rayleigh/opticaltheorem/passivity
unitchecks). Najpierwlevel2/960DOF podwójnegośladu, potemlevel3jeśliznaki/faza/
energiapoprawne. Zamrożonypróg1%complexfield/scattering/energy i raw1e−10,
bezfitufazy. CPUonly/6GiB/noextraswap/≤180s, braknativebuildów.

ObaCPUruny technicallycomplete/noOOM:level2/3 35,285/108,849s. Complexfield3,354→0,8495%, scattering6,308→1,6154%: obaanalyticFAILpróg1%, energiapoprawna/raw≤9,08e−15. Geometryauditbezfituprzewiduje−6,2728/−1,6106%scatter; stareFAILzachowane. Danepełnewdocs/maxwell-native-dielectric.md.


## EXP28 — plan i wynik

EXP28 planprzedrunem: EXP27level3pole0,8495%PASS,scatter1,6154%FAIL. Geometryczny
audyt daje Vmesh/Vsphere0,991394, aeq0,997123; Mieaeq przewiduje−1,6106%scatter,
bezfitu. Testować jawną siatkę volume-preserving: skala=(Vsphere/Vmesh)^(1/3),
niezależnaodε/freq/pól, target nadal kula r1 i te sameprogi1%/raw1e−10.
NieprzemianowywaćstaregoFAIL. Najpierwlevel1potem2, każda≤120s/6GiB CPUonly,
sprawdzićzbieżnośćpolazespolonego/energii. Nie jest to zmiana fizykianteny.

Jawnyvolume-preservingflatmeshPASSdlaobu siatek, niezmienionyMier1/progi1%. Level1/2 27,318/35,553s,field0,1764→0,02228%,scatter0,3067→0,03856%,energy1,142e−5→1,286e−7;raw≤5,35e−15/noOOM. Radiusvertex1,046133/1,011541wyłączniezobjętości. Niekwalifikuje near-fieldaniPCB/anteny.


## EXP29 — plan i wynik

EXP29 planprzedrunem: końcowa kontrola integracyjna PECnativeeta4 po dodaniu
dielectricmode/sharedMiehelper/geometryflag. Nie zmieniać matematykiPEC ani
progów. Jeden level3run≤180s/6GiB, cachedSO, kontrolaactualsourcesSHA/native
manifest, raw/complexFF i noOOM. Nie jest to nowy benchmarkanteny.

KońcowaintegracjaactualcodePASS/noOOM/40,784s, field0,5643%/scatter0,96565%. Nativeeta4apply0,2242ms vsdense0,1035ms; residentGPUevent0,1498ms. CPUcompressedGMRES0,5986s vsGPUoperator+CPUbasis0,07777s/170iter/rawOriginal3,218e−9. Rootsprawdziłsource/binarySHA i terminalstate w m2-native-dielectric-root-analysis-20261019.json.58unitPASS; M2/goalaktywne, brakFEMinterface/scalableassembly/antenna speedup. Docs-gardenLuna/checker/diffcheckPASS; rootreview kodu/manifestów/wykonanychźródeł zakończony. Nativecache i referencjaPalace zachowane, brakpushdo upstream. Goal/M2nadalaktywne.


## EXP30 — plan i wynik

EXP30 planprzedrunem: rzeczywisty mały MaxwellFEM–BEM transparent ε=μ=1/ka1.
Instalowany MFEM4.9 ND1 integratorymasy/curlcurl, niezależnyWhitneycheck,
punktowe mapowanie E×n→RWG ze znakami i1/edgeLength, osobny check
FEMboundarypairing=R^TGramSNC/RWG. Nonsymmetric1rowCalderon+FEMGreen, CPUdense.
Pierwszylevel1(20tet/20boundarytri), potemrefinebez zmianywielościanu.
Analytic1%E/H_L2, absfar<0,01, raw1e−10, map/pair1e−12,q4vs6delta1e−6.
CoarseFAILnieoznaczaPASS; osobnyFEMzexactDirichlet pozwalaoddzielićFEerrorodcoupling.
ND1wyłącznieprobe, produkcyjnymediumND2bez zmian; nieGPU/ports/antennaqualification.
Limit180s/6GiB/noextraswap/RAMonly, bridgeTU2,597s+cachehit, bezPalacerebuild.
PierwszybridgebuildFAILbrakcudss.h; dodanoistniejącyinclude/opt/cudss/include,
niebudowano zależności.61unitPASS. Research: Bemppfenicsnc1trace i Maxwell
multitraceexample, MFEMheaders/notes, Hiptmair2007stabilizedcoupling (doocenystability).

Bridge2,597s/cachehit,MFEMv4.9release/GetGitStrpusty. Level1/2CPUruny30,793/31,800s,noOOM/exit0.20/160tet,20/80tri,FEM42/254,BEM30/120. MFEM↔Whitney/trace/pair≤1,35e−15, raw1,14e−15/8,34e−15. CoupledE/H20,45/21,73→11,74/11,44%; comparatorFEM21,36/21,92→12,00/11,56%. Zbieżnośćpoprawna, oba1%analyticFAIL. Poziom2far6dir0,006323PASS. Niepromować.


## EXP31 — plan i wynik

EXP31planprzedrunem: poEXP30level1/2map1e−15 i zbieżnościE/H20/22→11,7/11,4%
(FEMDirichlet21/22→12,0/11,6%) uruchomić refinement2wtejsamejgeometrii.
1%E/Hnadalobowiązuje, niepromowaćND1 przezsamrawPASS. Dodaćpełniejszyfar-field
16×24+6kierunków i optycznybilansenergii względemπincpower (gate1e−3), nadal
absfar0,01. DrugiCalderonrowosobno zexactanalyticweakRHS+staryinterpolatedRHS.
CPUdense6GiB/max180s; mainmatrix/FEMmediumproductionbez zmian.

Level3CPUrun37,742s/1280tet/320tri,FEM1748/BEM480, matrix79,424MB/RSS827MB. Map/pair/MFEMmatrix≤1,46e−15, raw4,74e−14; actualE/H6,116/5,785%vsDirichlet6,177/5,823%: 1%fieldFAIL. Δcoupled–FEM0,5691/0,7571%normalizowanedoexactincident, nieboundcałkowitegobłędu. q4vs6delta2,58e−10; niewymuszonyCalderonrow0,7126%interpH/0,6752%exactweakH. Far384+6max0,001622, σscat7,479e−6/σext9,450e−6,energyerror/π6,275e−7PASS. NoOOM/exit0. RootactiveSource/binarySHA/terminalstate wlevel3/root-analysis.json; dalszeND2globalspace/mortar/stabilnośći kosztanteny.62unitPASS; docs-gardenLuna/rootreview/checker/diffcheckPASS. Lokalnycommitbezpush. Goal/M2aktywne.

### EXP32 — Gram RWG/SNC vs RWG/RBC, prerejestracja i wynik

Hipoteza: nie odwracać Gprimal bez małego testu rank/condition; sprawdzić dualRBC
przed ND2mortar. Ten samwielościan, poziomy1→2→3 poPASS, bezFEMsolve/GPU/build.
Dokładneargv wcommand.json: `bempp_oracle.py run artifacts/m2-dual-pairing-level1-20261019
--physics pairing --level 1 --seconds 120`, potem level1-fixed/2/3 do nowychkatalogów.
Cap6GiB/4CPU/memory-swap=memory/rootRO/networknone/tmpfs, istniejącyJITcache.
Przerejestrowanechecks: independentphysicalquad+BCtransforms/dualskewadjoint≤1e−12,
Gdualfullrank/κmassdiag<100, constanttrace/residual≤1e−12. Plane-tracediagnostic,
analytic_targetfalse, niezmienioneM2gates.

Pierwszylevel1FAIL23,311s/exit1/noOOM: brak() dla metodybarycentric_representation.
Błądroota poprawiony bezzmianbackendu/tolerancji; braknumerykidla failedrunu.
Poprawione3runy25,512/25,345/25,919s,RSS419/420/442MB,exit0/noOOM/interfacePASS.
Gprimalrank30/30→90/120→330/480, κraw2,25e17/2,85e17 na wyższychpoziomach:
**REJECT osobnejinwersjiGprimal dla ND2projection**. Nieunieważnia toND1bloku,
który nieodwracaGprimal. Gdualrank30/30,120/120,480/480 iκmassdiag2,154/2,720/2,922.
Weakvsphysicalquadrature≤1,32e−15, Gdual=-Greverse^T≤1,81e−16, exactconstanttrace
L2≤1,13e−15; plane-traceRWG0błąd20,994→10,433→5,157%. To ograniczeniereprezentacji,
nie kontrolaND2/pólMaxwella. Rootpotwierdziłcase/fem/referenceSHA/terminalstate
w artifacts/m2-dual-pairing-root-analysis-20261019.json. NastępneactualglobalMFEMND2,
plane-waveDirichletkontrola, fizyczneB/Rmortar i rozdzieleniebłęduFEM/powierzchni.
65testsPASSwpinnedenv,systemowo62PASS/3SKIP(SciPy); docs-gardenLuna/rootreviewPASS,
historycznylicznik62wEXP30–31doprecyzowany. Checker/diffcheckPASS, lokalnycommitbezpush.
Brakpromocji/natywnegorebuilda/płatnegocompute; M2/goalaktywne.

### EXP33 — prerejestracja: actual global MFEM ND2

ZachowaćprodukcyjnymediumND2, nieprzedłużaćND1refinement. Nowy małyCAPI
`mfem_global.cpp` używa istniejącego MFEM4.9/ND_FECollection(2), globalFESpace,
rzadkichBilinearForms oraz GetElementDofs/InvTransformPrimal dlafaceDOFs.
BuildtylkodwaTUs/ccache i linkSO, limit120s, bezrebuildazależności/Palace.
Nowycase `--physics nd2`: ten samzamkniętywielościan, k1/eps=mu1,
exactplanewaveEx=exp(iz),Hy=exp(iz), DirichletzprojectedanalyticboundaryDOFs.
Poziom1→2→3 poexecutionPASS; cap6GiB/4CPU/tmpfs/noaddedSwap/deadline120s.
Gatephysicalbasis/globalmatrixquad/constant/linear/GridFunction≤1e−11,
musząwystąpićnonidentityface transforms. CałepolaE/H≤1%, rawinterior≤1e−10,
q4vs6delta≤1e−6. SparseCSR/lokalnebasiswektorywRAM; brakdenseglobalFEM.
Rzeczywisteargv `python3 tools/experiments/mfem_bridge.py build`, potem
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-global-nd2-level1-20261019
--physics nd2 --level 1 --seconds 120`. Wyższepoziomydonowychkatalogówpoanalizieroota.
Level1takżeregresja staregoND1CAPI. To odniesieniedlapóźniejszegoBCmortar,
nie FEM–BEMsolve/exterior/ports aniantenna speedup. M2/goalaktywne.

EXP33pierwszybuildPASS3,361s, nowySO35dea8a9…; level1containerexit0/noOOM,
runnercompletefalse0,527s. ND2184DOF/20tet, checks≤4,44e−15 iND1legacyPASS;
E/HDirichlet2,204/3,342% (projekcjanie-solve2,451/5,315%). Raw6,83e−16,
aleq4vs6delta3,19e−6>1e−6: diagnostycznyfiltrFAIL, nie wolnopromować.
Korekta: wliczaniu błędu pól użyć dokładniejszejkwadraturyq6 z niezależnymq8,
prógdelta1e−6 bez zmian, poprzedniąróżnicęq4vs6 nadalraportować; niezmienia
toND2/siatki/operatora ani tolerancji pól. Dokładniejszyaudyt licznika
faceorientations: MFEMIsIdentity dotyczyklasytransformacji, nie danegoelementu;
liczyć faktyczne InvTransformPrimal(I) != I. To wymaga jednegoprzyrostowego
rebuilda wyłącznie małegoCAPI. Nowyrun `artifacts/m2-global-nd2-level1-q6-20261019`.

EXP33q6: rebuild3,310s/nowySO1abaa83a…; level1/2/3exit0/noOOM/executionPASS,
runner0,536/1,051/5,514s, RSS281/288/433MB. DOF184/1228/8936,boundary100/400/1600;
actualnonidentitycells19/147/1167, matrixquad≤8,86e−16, polynomials≤3,56e−14.
DirichletE/H2,2046/3,3413→0,5910/1,0541→0,1505/0,3317%: level3analyticPASS.
Oddzielna interpolacjaE/Hlevel3=0,1860/1,4681% (HFAIL), nie ta samareferencja.
Raw6,83e−16/1,73e−15/4,09e−15,q6vs8≤6,94e−12. M/KCSR148552/1128424/8793480B,
sparseLU0,000327/0,005876/0,5362s. Rootzweryfikowałaktywnesource/binarySHA/
terminalstate w artifacts/m2-global-nd2-root-analysis-20261019.json.
69testsPASSwpinnedenv,systemowo63PASS/6SKIP. DalejB/Dmortar/Schur/coupledND2,
bezprzenoszeniażądań1%na samąinterpolację ani deklaracjiantenna speedup.
Docs-gardenLuna/rootreview/checker/diffcheckPASS; dodatkowycachecheck
`MFEM bridge unchanged: cached library retained` bezrekompilacji.
Lokalnycommitbezpush, goal/M2aktywne.

### EXP34 — prerejestracja: actual ND2/BC-RBC mortar i sparseSchur

Rootprojektuje `bempp_nd2_coupling.py`: B=<vND2,BC> i niezależnie
D=<RBC,vND2×n>, pełnefaceDOF/barycentrictransforms. Gate D=−B^T,
normal/coordinates/interiortangentleak≤1e−12; exactconstanttrace≤1e−12,
lineartraceerrorraportowany (RWG0nieND2trace). GdualR=D zamiastGprimalinverse.
FEM A=K−M pozostajesparse; [A,−ikB; C*R,T][u,h]=[0,rhs], C=G/2+Kbem.
Schur=T+ik*C*Gdual^-1*D*A^-1*B; RHSbloki16, nie alokowaćdenseglobalFEM.
Tylko≤512FEMDOF sprawdzićcałyfullcoupled układ≤1e−10. Na większymreference
boundedDirichlet zEXP33+independentwholeE/Hplane-wave. TargetE/H≤1%, raw≤1e−10,
q6vs8≤1e−6, absolutezero-scatterfarfield≤0,01 i energyerror/π≤1e−3.
PrzypiętyBempp `electric_dual` używa RWG/BC i RBC/SNC, kontrolaAPIwsource.
Limit180s/6GiB/4CPU/tmpfs/noaddedSwap, cachedMFEM/JIT, brakbuilda/GPU/paidcompute.
Dokładnyargv: `python3 tools/experiments/bempp_oracle.py run
artifacts/m2-nd2-bc-coupling-level1-20261019 --physics nd2-coupling --level 1 --seconds 180`.
Level2/3 dopiero po rootanalizie. BrakCFIE/stabilizacji/transmission/ports;
to transparentprobe, nie promocja solveraanteny ani zamknięcieM2.

EXP34pierwszylevel1FAIL15,625s/exit1/noOOM. Mortarvalidated12,261s, ale
standardowyBemppDenseAssembler odrzuca requires_dof_transformation dlaBC/RBC.
Brakcoupledfields/Schur/farfieldwyników. Źródłoprzypiętegoassemblera potwierdza
tenbrak, niezmieniaćupstreamenv/nieomijaćchecku. Korekta: lokalnycustomassembler
używa tychsamychregular/singularMaxwellkernels wmake_localised_space, potem
Qtest^T*A_local*Qtrial, gdzieQ=map_to_localised*dof_transformation. Kontrola
punktowalocal/globalbasis≤1e−12, dodatkowo publicznyMaxwellRWG/SNC vs ta ścieżka
dla obuT/K≤1e−12 wlevel1. To kosztownylocaldense tylko małyprototyp, nie scalableBEM.
Poprawionyrun `artifacts/m2-nd2-bc-coupling-level1-local-20261019`, te samebramki/limity.

EXP34locallevel1exit0/noOOM/executionPASS35,789s/RSS680MB. Mortaradjoint1,79e−16,
constanttrace8,74e−16, lineartrace34,055%. CustomMaxwellvsnativeT/K≤1,22e−16,
pointwisemaps≤3,37e−16. Schurraw3,37e−15, tinyfullcrosscheck1,93e−14;
FEM184/BEM30, lokalneBEM360²complex128=2,074MB, reducedSchur14,4KB.
CoupledE/H17,743/15,224%FAIL vs boundedDirichlet2,205/3,341%; q6vs8≤8,06e−13.
Spuriousfar0,005935/energy3,26e−7PASS — far/residuum niekwalifikującałychpól.
Następnylevel2 przytejsamejfizyce/180s/6GiB do
`artifacts/m2-nd2-bc-coupling-level2-local-20261019`; zbieżnośćdecydujeolevel3.

EXP34level2exit0/noOOM/executionPASS43,671s/RSS718MB. CoupledE/H10,072/5,645%FAIL,
Dirichlet0,591/1,054%, deltaE/H10,111/5,827%. Adjoint/interiortangent/normal≤8,28e−16,
constant9,79e−16, linear16,634%, raw1,14e−14, qdelta9,80e−15. Far0,002338/energy7,20e−7PASS.
FEM1228/BEM120, Schur230,4KB, lokalneBEM1440²=33,178MB/operator (144×finaldata).
Do mortaru12,33s/T27,92s/C38,40s/Schur38,43s/pola38,84s; setup/JIT/assembly
dominują, nieLU0,03005s. Nieekstrapolowaćczystegokernelczasu z 2poziomów/JIT.
Rootaktywnesource/helper/binarySHA/terminal/FAILsprawdzone w
artifacts/m2-nd2-bc-coupling-root-analysis-20261019.json. Level3NOTRUN: następne
rozdzieleniesamejgranicyprzyustalonymFEM, najpierwcheaptrace-spaceprobe.
71testsPASSwpinnedenv,systemowo63PASS/8SKIP; docs-gardenLuna/rootreview/checker/diffcheckPASS.
Wynikizapisane w lokalnymcommicie, bezpushdo upstream.
Brakmatched-errorporównania/promocjianteny/M2closure; goalaktywny.

### EXP35 — prerejestracja: trace spaces bez nonlocalBEMsolve

Jednymprocesem1→3surfacehierarchy: RWG/RBC iBC/SNC dualprojection vs bestL2
massprojection w tychsamychprzestrzeniach. ConstantEx i planeEx/Hyexp(iz).
NiezakładaćBCconstantreproduction; zmierzyćosobnobestapproxerror i wpływtestduality.
Gateweakresidual≤1e−12/q4vs6≤1e−6, RWGconstant≤1e−12, massSPD i bestL2
niegorszeoddual o>1e−9. Błędy powierzchniowenieMaxwell1%gate/nieHdivstability.
`trace_load/projection_error` otrzymują orderarg default4 (stare wywołaniabez zmian),
nowypolynomialtest wunit. TylkoCPU6GiB/4CPU/tmpfs/noaddedSwap, limit120s,
cachedBempp/JIT, bezMFEMCAPI/buildów/GPU/paidcompute. Dokładnyargv
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-trace-space-hierarchy-20261019
--physics traces --level 3 --seconds 120`. Wynikwybierzenastępnąprzestrzeń/mortar,
niezmieniaM2gates/medium/productiondefaultów.

EXP35exit0/noOOM/executionPASS18,643s/RSS347MB. Poziomy1/2/3planeE/Htrace:
RWGdual≈20,99/21,02→10,43/10,41→5,16/5,16%, bestL2≈19,63→10,02→5,06%.
BCdual≈48,94→31,24→20,87%, bestL2≈46,79→30,14→20,09%. ConstantBCdual46,87→30,35→20,57%,
bestL245,33→29,44→19,81%, RWGconstant≈1e−15. Weakresidual≤1,97e−16/qdelta≤5,17e−11.
BCdualitytestniejestgłównympowodemdużegobłęduL2: bestL2pozostajedużo gorszeniżRWG.
ToniedowódHdivstability/coupledcausality. WEXP34h=BC, więc następnyizolowanykontrafakt:

### EXP36 — prerejestracja: magnetic_dual przy stałymFEMlevel2

Ten sam ND2/FEM1228/160tet i BEM120/80tri coEXP34level2. Zmiana tylko spaces:
upstreammaxwell.py `magnetic_dual`: t=BC,h=RWG,testSNC (zamiastRWG/BC/RBC).
G=<SNC,BC>fullrankzEXP32, physicalB=<v,RWG>, D=<SNC,v×n>=−B^T,
G*R=D. C/T/Green/Schur/eps/mu/k/medium/1%E-H/raw/far/energyprogi bez zmian.
BCnieodtwarzaconstanttracepunktowo(EXP35), więc raportowaćerrorbezzerowania;
sprawdzić exactconstantweakloadG*R*u0=<SNC,E0×n>≤1e−12. Dla defaultowegoelectric
nadalwymagać także exactconstantpointwise≤1e−12. Brakpoluzowaniawholefieldgate.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-magnetic-dual-level2-20261019
--physics nd2-coupling --duality magnetic --level 2 --seconds 180`.
CPU6GiB/4CPU/tmpfs/noaddedSwap/cache, bezbuild/GPU/paid. Wynikiwybierajądalszy
testpowierzchniprzyustalonymzakwalifikowanymFEM, niepromocjęanteny.

EXP36pairedlevel2exit0/noOOM. MagneticdualE/H1,424/2,884%FAIL vs electriccontrol
10,072/5,645%FAIL, Dirichletwobydwu0,591/1,054%. Magnetic40,540s/RSS706MB vs
electric43,659s/RSS718MB. Mortar/constantweak≤6,88e−16, raw3,05e−14,
far4,586e−4/energy3,606e−7PASS. BCconstantpointwise30,351% jawne, niezerowane.
T_RWGSNC240²=0,922MB zamiast1440²=33,178MB; K_BCSNCnadal33,178MB. Przestrzeń
hRWG mocnopomaga przytej samej objętości, lecz wholefield1%nadalnieosiągnięte.

### EXP37 — prerejestracja: tylko powierzchnia przy stałymFEM

MagneticdualFEMlevel2/1228DOF/160tet bez zmian; surface2→3, BEM120→480DOF,
80→320tri. Nowygeometryparentlookup po centroids i kontrolawszystkich3vertices
finerBEMface wFEMboundarytriangle. NieintegrujeBEMfaceprzecinającejFEboundaryface:
wymaga nestedrefinement, przeciwny/coarsersurface odrzucany. Unit4childperface,
wronggeometry/crossedfacesrejection. CałkiB/Dnadal≤1e−12; niezmienioneprogi/fizyka.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-magnetic-f2-b3-20261019
--physics nd2-coupling --duality magnetic --level 2 --surface-level 3 --seconds 180`.
CPU6GiB/4CPU/tmpfs/noaddedSwap/cache; brakbuild/GPU/paid. To izolujebłądgranicy;
FEM2DirichletH1,054%samnieprzechodzi1%, więc całościowypromisingrun wymaganastępnie
kwalifikowanegoFEM3 i takiej samejpowierzchni. Nieobniżać1%gate.

EXP37F2/B3exit0/noOOM/execution+analyticPASS91,437s/RSS1,323GB.
CoupledE/H0,5603/0,7512%, samFEMDirichlet0,5910/1,0541%, delta0,2906/0,8702%.
AnalitycznepolaPASSniezależnieodgorszegointerpolowanegoDirichletH; nieodrzucać
poprawnegorozwiązaniadlatego, żeten comparator ma1,054%. Mortar≤1,50e−15,
constantweak5,86e−16, raw5,88e−14, qdelta1,72e−13; far6,46e−5/energy3,33e−8PASS.
LocalE14,746MB, localK530,842MB, Schur3,686MB; nieoszczędnośćpeakRAManteny.
Następnykontrafakt przyUSTALONEJBEMB3: zmienićwyłącznieFEM2→3,
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-magnetic-f3-b3-20261019
--physics nd2-coupling --duality magnetic --level 3 --surface-level 3 --seconds 180`.
Te sameprogi/eps/mu/k/6GiB/4CPU/tmpfs/noaddedSwap; tokwalifikuje zbieżnośćobjętości,
nieporty/dielektryk/antennaspeedup. Nieluzować1% i niezamykaćM2na1transparentprobe.


EXP37 F3/B3: exit0/noOOM, analytic+execution PASS, 95,902s/RSS1,345GB.
E/H0,3577/0,9042%; raw2,312e−13, qdelta2,758e−16. E lepsze niż F2/B3,
H gorsze (0,7512→0,9042%); nie ogłaszać monotonicznej poprawy obu pól.
Final paired F2/B2 na tym samym aktualnym kodzie: electric10,072/5,645% FAIL
43,925s/RSS722MB; magnetic1,424/2,884% FAIL40,861s/RSS708MB. Wyniki zgodne
z kodem sprzed parent lookup (Δpól<1e−12). Wszystkie stany terminalne i SHA
case/helperów/MFEM SO, mortar/raw/quad/energy i rozdzielenie PASS/FAIL sprawdzone
przez root w artifacts/m2-trace-duality-root-analysis-20261019.json.
Pierwszy verifier odrzucił intencjonalne null nd_api_sha256 w traces (brak NDbridge);
poprawiono sprawdzanie stosowalnych hashy, bez zmiany progów fizycznych.
Dokumentacja EXP35–37: docs-garden read-only tej samej Luny i root review PASS;
74testsPASS w pinnedenv, system64PASS/10SKIP, checker/diffcheckPASS.
Bez rebuilda Palace/deps, zmian medium i promocji; lokalny commit bez push.


### EXP38 — prerejestracja: transmisja, niezależny PMCHWT na tym samym wielościanie

Nowy izolowany bempp_transmission.py, bez zmian Palace/MFEM/medium. eps=1 najpierw
sprawdza konwencję exp(-iwt), E=K*t+T*h/rho i H=K*h-rho*T*t przez porównanie
z analityczną falą. Potem eps=2,94: FEM A=curlcurl-eps*M i ten sam zewnętrzny
Calderon; niezależny PMCHWT ma dwa operatory wnętrza/zewnętrza oraz brak mortaru.
Pierwotne źródło: pinned Bempp examples/maxwell/maxwell_dielectric.py i
bempp_cl/api/operators/potential/maxwell.py (commit a1eaaef9...). Publiczne fetch
przez web niedostępne; zweryfikowano istniejący przypięty lokalny checkout.
Kontrola centroidów wszystkich tetra z wagami objętości to screening, NIE pełne
L2 pól. Raport ma analytic_target_passed=false bez względu na screening, żeby
nie zaliczyć M2 samymi próbkami. PMCHWT B1/B2 pozwala zmierzyć niepewność
referencji; screening wymaga <1% probe error, <0,3% zmiany referencji, raw<1e-10,
energy/pi<1e-3, farfield<1% (dla eps1 kontrola analityczna). Nie luzować K.

Pierwszy dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-transparent-f2-b2-20261019 --physics transmission --level 2 --surface-level 2 --epsilon-r 1 --seconds 180`.
6GiB/4CPU, bez dodatkowego swap, temp/cwd tmpfs, bez GPU/płatnego compute.
Niezmieniony cached MFEM SO. Unit76PASS; nowa walidacja eps/siatki przed alokacją
oraz zespolonego weighted probe error. Jeśli znaki/reference nie przejdą,
nie uruchamiać eps2,94 przed analizą; nie przechodzić doM3.


EXP38: exit0/noOOM51,407s/RSS761MB, raw3,05e-14 ienergy/pi3,61e-7.
ScreeningFAIL: coupled analytic centroidE/H0,6156/1,3266%, PMCHWT B2analytic
E/H2,6213/2,6363%, refB1→B2change13,678/13,651%. Nie traktować tej referencji
jako dokładnej. Przed eps2,94 oddzielić niedokładność prądów BEM od potencjałów.

### EXP39 — prerejestracja: tylko referencja, bez powtarzania coupled solve

Ten sam zestaw160tetcentroidów (FEMsampling2), PMCHWT B2/B3 i te same solved
currents oceniane potential quadrature4/8. Nie zmieniać boundaryassembly q4,
fizyki eps=1 ani punktów. Zmiana jednej kwadratury po solve rozdziela jej wpływ
od zmiany siatki. Jeśli q4→8 mocno poprawi pole, trzeba osobno zakwalifikować
kwadraturę; jeśli nie, dominuje błąd discretization/reference. Bez promocji.
Zapis małych wyników pmchwt-level*.npz pozwoli uniknąć ponownego assembly przy
następnej diagnostyce. To zwykły artefakt wyniku, nie roboczy offload solvera.

`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-reference-q4-q8-20261019 --physics transmission --level 2 --surface-level 3 --epsilon-r 1 --reference-only --seconds 180`.
6GiB/4CPU/tmpfs/noadditionalSwap, bezGPU/build/płatnego compute.


EXP39: executionPASS34,290s/RSS456MB/noOOM. B2 q4E/H2,621/2,636%,
q8 1,824/1,830%; B3 q4 0,216/0,217%, q8 0,158/0,158%. Oba czynniki
siatka oraz potentialquadrature wpływają na pole. PMCHWT raw≤4,72e-15.
Root sprawdził stany i błędy B3<0,3%; nie jest to globalL2 ani kwalifikacja
transmisji. Użyj potentialq8 dla kolejnego porównania, boundaryassemblyq4 bez zmian.

### EXP40 — prerejestracja: właściwy kontrast eps=2,94

FEM2/BEM3, zmiana A=curlcurl-eps*M, zewnętrzny Calderon bez zmian. Independent
PMCHWT na tym samym wielościanie, B2/B3 i potentialq8. Porównać kompleksowe
E/H w160tetcentroidach oraz farfield i bilans energii. Raw<1e-10/mortar<1e-12;
screen1% probes/far, refchange0,3%, energy/pi1e-3; pełneL2 i kwadratury nadal
osobną bramką, analytic_target_passed=false. Nie promować tylko za zgodnośćS.
Zapisz mały wynik coupled-solution i prądy PMCHWT do ponownej analizy bez solve.

`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-eps294-f2-b3-20261019 --physics transmission --level 2 --surface-level 3 --epsilon-r 2.94 --seconds 180`.
6GiB4CPU/tmpfs/noaddedSwap, bezGPU/cloud/build. Jeśli nieprzejdzie, ustalić czy
referencja, FEM czy sprzężenie; bez ślepego podnoszenia obu siatek.


EXP40: exit0/noOOM/executionPASS112,166s/RSS1,309GB. ScreeningFAIL: E/Hweighted
centroids0,8851/1,3597%, farrelative0,1116%, raw5,14e-14, energy/pi1,02e-7.
RefB2→B3E/H3,2015/1,9748% — referenceuncertainty ponad0,3%. Root independently
recomputed complex probe differences from npz, positive volumeweights4pi/3 and
state/helper/SO/current-case hashes in artifacts/m2-transmission-root-analysis-20261019.json.
Nie przypisywać różnicy wyłącznie FEM i nie promować. Eksperyment nie kwalifikuje
pełnegoL2/anteny. Zapisane rozwiązania nie wymagają ponownego coupled solve.

### EXP41 — prerejestracja: zwiększyć tylko niezależną referencję

Reference-only eps2,94, te same160centroidów, B3/B4, potentialq8/q12 na tych samych
prądach. B4 uzyskane przez płaskie1→4 subdivisionB3, bez radialprojection; unit
sprawdza1280tri/1920edges, closed2incidence, volume4pi/3 i outward normals/planes.
Nie zmieniać FEM2/BEM3 kandydata, nie powtarzać jego assembly/solve. Po runie
root porówna zachowane probes z nową referencją i sprawdzi jej zbieżność.
Łączny PMCHWTB4ma3840currentDOF, denseblock235,93MB; limit6GiB/180s utrzymany.
77unitPASS. To koszt jednego rozstrzygającego referencecheck, nie większy medium.

`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-reference-b3-b4-20261019 --physics transmission --level 2 --surface-level 4 --epsilon-r 2.94 --reference-only --seconds 180`.
BezFEMsolve/nativebuild/GPU/cloud/swap. Jeśli referencechange nadal>0,3%,
raportować niezbieżność; nie luzować progu ani na ślepo zagęszczać doB5.


EXP41: exit0/noOOM126,619s/RSS1,145GB. PMCHWTB4 3840DOF/235,93MBblock,
raw8,39e-15; B3→B4E/Hreferencechange0,4076/0,1657%. B4q8→q12delta
0,0000830/0,0000837% (<1e-6 względnie); potentialquadrature mały wpływ,
referenceE nadal>0,3%screen. Root independentweightedcomparison zachowanych
EXP40probes vs B4/q12: E/H1,0923/1,3205%FAIL1%, bez nowego coupled solve.
Stan/SHA/helpery i błędy zweryfikowane w artifacts/m2-transmission-refinement-analysis-20261019.json.
To centroiddiagnostic, nie globalL2 i nie measuredantenna memory/speedgain.
77unitPASS w pinnedenv, system65PASS/12SKIP. Docs-garden read-only tej samej
Luny, root review, checker i diffcheck PASS. Lokalny commit bez push.
Bez rebuilda/deps/paidcompute/GPU. M2 ACTIVE, bez promocji solvera.


### EXP42 — prerejestracja: volume replay bez nowego solve

Poprzedni goalturn był PROGRESS: zapisano EXP38–41 i commit c240a7c. Teraz
bempp_volume.py odtwarza savedF2/B3 i PMCHWT B3/B4 bez nowego BEMassembly/LU.
Obecny MFEMhandle przytworzeniu montuje małe serialmass/curl; nie eksportujemy
ich ani nie faktoryzujemy. Nie twierdzić, że cały postprocessing nie ma assembly.
Reguły dodatnie degree2(4pts/tet) i degree5(14pts/tet), dane z MFEMv4.9
fem/intrules.cpp; primarysource pobrano urllib do istniejącego sourcecache
(webfetch niedostępny). Unit sprawdza wszystkie barycentricmonomials do stopnia.
Pierwszy tani filtr degree2:160tet*4=640points, weights sum4pi/3. Te same punkty
obejmują całą domenę. Reference B3q12, B4q12 i B4q16: osobno meshchange i
potentialquad. Chunk128points ogranicza pamięć, nic nie migruje do SSD/swap.

Zamrożone screening1%volumeE/H,0,3%referencechange,1e-6potentialquad, a następnie
osobno degree2/5agreement1e-6. analytic_target_passed=false; volume quadrature
nie jest jeszcze zbieżną całką, brakpromocji. Runner wiąże wszystkieinputSHA,
state/noOOM/role/material/unchangedFEMhelpers/SO przed uruchomieniem.
80unitPASS. Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-volume-degree2-20261019 --physics volume --level 2 --volume-degree 2 --volume-inputs artifacts/m2-transmission-eps294-f2-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.
6GiB4CPU/noaddedSwap/tmpfs, bezGPU/cloud/rebuild. Jeśli timeout, zachowaćdiag,
nie ponawiać bezdiagnozy. Degree5 tylko po informacji o koszcie/kompletności.


EXP42 exit0/noOOM52,526s/RSS493MB,640positivevolumepts/4pi3. Root independently
recomputed volume E/H2,1518/0,8630% from npz. RefB3→B4 E/H1,0746/0,4374%
FAIL0,3%. Potentialq12/q16 E/H7,37e-7/7,67e-7 PASS1e-6 at these points.
ScreeningFAIL: centroid1,09%E underestimated volumequadratureE; don't promote.
Phases: MFEMfields0,062s,B3q12 13,219s(includesinitialJIT),B4q12 14,876s,
B4q16 23,233s. Retained caches, no BEMassembly/solve.

### EXP43 — prerejestracja: oddzielna kontrola degree5

Te same zapisane wektory/material/geometry, zmienić tylko volume_degree2→5.
2240points(14/tet), symetrycznepositiveMFEMruledegree5; sourceURL
https://raw.githubusercontent.com/mfem/mfem/v4.9/fem/intrules.cpp i lokalnycache.
Prognoza~150–180s (steadyPotentialcost*3,5 + initialJIT), limit nadal180s,
6GiB4CPU/noadditionalSwap/tmpfs. Nie zwiększać deadline automatycznie.
Porównać normy/errors względemEXP42 i potential/referencegates bezluzowania.
Nie jest to zmiana medium ani nowy solve. Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-volume-degree5-20261019 --physics volume --level 2 --volume-degree 5 --volume-inputs artifacts/m2-transmission-eps294-f2-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.
Jeśli timeout, zachować dokładnystage, następny run dopiero z diagnozą/pracy
podziałem; nie wyciągać fullfieldwniosku z niedokończonej całki.


EXP43 exit0/noOOM159,317s/RSS494MB,2240positivevolumepts. Degree5 E/H
2,8884/1,6116%; refB3/B4 1,9455/1,1580%; potentialq12/q16 7,38e-4/7,47e-4
FAIL1e-6. Degree2/5error zmiana0,7367/0,7486punktuproc. Nie ogłaszać dokładnego
fullL2; oba oszacowania niespójne. H_FEMsquarednormdelta2,11e-15: te same
wektory i prawidłowe regułycałkujące jego stopień2. Root wszystkiecomplexnormy,
actualsource/helper/SO/inputSHA/noOOM/stany w artifacts/m2-volume-replay-root-analysis-20261019.json.
80unitPASS; bez BEMassembly/LU/rebuild/cloud/GPU/swap, małe MFEMforms nadal
montowane z handle. Docs EXP42–43 i sourceaudit pinned potentialkernels zapisane.
Następna hipoteza: fixed regulartrianglequadrature nie adaptuje się do point-panel
separation. Kontrola własnego panelintegral przeciw pinned kernel na tej samej
regule, potem near correction (subtract regular + add adaptive), bez powtarzania
solve. Jeszcze NOTRUN; bez twierdzenia że usunie cały błąd referencji.
Docs-garden read-only tej samej Luny: jeden wordingissue — rozróżnić standalone
degree2/5agreement od potentialq12/q16. Root poprawił dokument i dodał osobny
preregistered1e-6volume-degreegate FAIL do rootanalysis; casequalityflag nie
obejmuje pary reguł i opis teraz mówi to jawnie. Pozostałe source/artifacts PASS.
80unitPASS pinned, system67PASS/13SKIP; checker/diffcheckPASS. Lokalnycommit bezpush.


### EXP44 — prerejestracja: fizyczny panelkernel i adaptacja przy bliskich punktach

Poprzedni goalturn PROGRESS: commit e5a85ce, volume replaydegree2/5FAIL zachowany.
Nowy maxwell_near.py rekonstruuje affineRWG J oraz div_Gamma z rzeczywistego
space.evaluate/DOFtransform i physicalJacobian. T=ik intGJ-intgradGdiv/(ik),
K=intgradGcrossJ; bez modyfikacji installedBempp. Porównać każdy zTt/Kt/Th/Kh
na identycznej triangle_gauss.rule(8) przeciw pinnedpotentialkernel, relative<1e-12.
Kontrola openonepanel(include_boundary_dofs) i closed20trianglepolyhedron,
syntheticcomplexcurrents, k=sqrt2.94. To operatorcheck, nie fizyczne rozwiązanie.

Adaptive test: singlepanel,6targets wtym distance0,002/0,02/0,2 z obu stron.
DuffyGauss6 vs8 na tej samej distance-subdivisiontree (ratio4,maxdepth12),
każdy point/operatorrelative<1e-6, brakdepth_hits. Raport regularvsadaptive
bez przypisywania exacterror samemu porównaniu. Gdy regular nativecheckFAIL,
nie uruchamiać dalszych poprawekvolume; zdiagnozować normalizację/div/orientację.
Unit84PASS: rigidrotation/translation,area childmap, exhaustion/errorguards i
preallocationflaglimits. Brak BEM/FEM solve/build/GPU/cloud.6GiB4CPU/tmpfs/noSwap.

`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-panel-control-20261019 --physics near-control --level 1 --seconds 120`.
Niepromowaćanteny, niezaliczaćM2 z operatorcontrol. Następne ewentualnie korekcja
savedvolume (subtract regularnear + addadaptive), tylko po tym filtrze i pomiarzekosztu.


EXP44 execution/operatorcontrolPASS15,028s/RSS272MB/noOOM. Regularphysical T/K
vs native peroperator≤1,97e-15, adaptiveq6/q8worst1,96e-15,10140leaves/order,
maxdepth12 alezeroexhaustion. Regularq8 vs adaptive1,627relative na nearpoints;
to nie świadczy samo o złej adaptive ani o jej exactaccuracy. Potrzebny niezależny
kontroler, nie tylko dwa warianty tej samej adaptacji.

### EXP45 — prerejestracja: niezależny solid-angle oracle + koszt ratio

KonwencjaLaplace: normalcomponent intgrad(1/(4piR)) = orientedOmega/(4pi).
Reference z istniejącej SciPy1.15.3 calculate_solid_angles (VanOosterom/Strackee,
DOI10.1109/TBME.1983.325207, bibliografiaCrossref/PubMedzweryfikowana; kodpinnedSciPy
odczytanylokalnie). Nie kopiowaćkernelnear jako oracle. Nowy helper diagnostyczny
nie jest używany przezintegrate/adaptive. Unit octantOmega=pi/2/orientation/scalePASS.
ConstantJx/Jy,div0,k=1e-5 daje normalgrad z (K[Jx]_y-K[Jy]_x)/2. Różnica
Helmholtz–Laplace ograniczona≤(1+maxkr)k²Area/(8pi)≈2e-12, gateabsolute1e-8,
bezdepthhits. To niezależny staticnormalcontrol, nie pełnyphysicalFEMsolve.

ZachowajnativeT/Kgate1e-12 iadaptiveq6/q8worstpointoperator1e-6. Porównaj
ratio2vs4 na tych samych6targets/currents/rules, mierząc czas/leaves/hits.
Fasterratio2dopuszczalne dopiero po obukontrolach.85unitPASS. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-solid-angle-control-20261019 --physics near-control --level 1 --seconds 120`.
6GiB4CPU/noadditionalSwap/tmpfs/noGPU/cloud/build. Nie powtarzaćfullvolume,
niepromowaćanteny. Przyfailnajpierwdiagnoza, bez automatycznejzmianyprogu.


EXP45 operatorcontrolPASS15,781s/RSS279MB/noOOM. Native T/Kmax1,97e-15;
ratio2worstq6/q8pointoperator1,97e-11,2550leaves,0,196/0,210s vs ratio4
10140leaves,0,783/0,865s. Independentconstant-normalstaticerror1,929e-12 ≤
Helmholtz–Laplacebound1,989e-12 ≪1e-8gate,zeroexhaustion. Root actualstate/
currentcase+nearSHA/peroperator and ratioNPZrecompute/regressionvsEXP44 in
artifacts/m2-near-control-root-analysis-20261019.json. Nie twierdzić że to
fullMaxwell/volumequality. Ratio2wybrany do małej następnej korekcji, nieanteny.

### EXP46 — prerejestracja: korekcja32savedpoints bez assembly/solve

bempp_near_correction.py: finePMCHWTB4 currents, cachedvolume degree5.
16worst q12/q16targets +16spanningpoints (wybórtendencyjny, NIE fullL2).
Odtwórzregularq12przezwłasnepanele na3punktach vs cacheE/H<1e-12; potem
odejmijregularnear i dodajadaptive6/8 (distance ratio2, maxdepth12).
Osobno selectionradius2vs4 przyadaptive8/ratio2 bada niekorygowane dalsze panele.
Gates adaptive6/8relative<1e-6 i cutoff2/4relative<1e-6,zeroexhaustion,
bezpromocji/analytic_target=false. Zmierzczas/leaves/RSS przed pełnymreplay.

Runner wiąże volume-output/currents/meta/state/material/referencelevel/SO,
reference.py i helperSHA; inputsread-only. Ref sourceSHA i volumegeometryhelper
wymagają zgodności. Unit85PASS, actualinputcheckPASS. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-subset-20261019 --physics near-correction --level 2 --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
6GiB4CPU/noadditionalSwap/tmpfs/noGPU/cloud/build/solves. Jeśli regularcache
niezgodny, stopdiagnose. Nie utożsamiać subsetcontrol z volumeconvergence.


EXP46 correctioncontrolPASS8,555s/RSS217MB/noOOM,32biasedpoints. Nativecachedq12
vs reconstructed E/H6,58e-15/4,47e-15. Adaptive6/8E/H1,01e-12/1,18e-12;
selectionradius2/4E/H1,76e-14/1,84e-14. Oldq16vs corrected0,1115/0,1189%.
q6r2 .600s/6897leaves, q8r2 .631s/6897, q8r4 1,118s/10200;zeroexhaustion.
Root source/input/state/npzcomplexnorm verification in artifacts/m2-near-correction-root-analysis-20261019.json.
Subset niejest globalL2 ani convergedphysicalreference. Reconstructedcurrents
zachowane; nic nie zmieniło fizycznego rozwiązania.

### EXP47 — prerejestracja: pełnyfine-reference replay ze wszystkimi kontrolami

Zmienić tylko count32→all2240savedpoints, reuse tych samychFEMcurrents/basis/refs.
Korekcje q6/q8radius2 i q8radius4; gateeachglobalE/Hdelta<1e-6, brakdepthhits;
nativeq12 vs3savedpoints<1e-12. Raport correctedvolumeestimate vs savedFEM,
nie qualifiedL2: nadal otwarty coarse-reference i degree2/5convergence.
Prognoza<180s (pilot2,35s/32dla3passes; celowanysubset jest kosztowniejszy niż
przeciętnepunkty). Bezprzedłużania deadline. Limit6GiB4CPU/noaddedSwap/tmpfs.
85unitPASS, bezGPU/cloud/build/assembly/solve. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-volume-b4-20261019 --physics near-correction --level 2 --near-count 0 --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.
Jeśli timeout, zachowaćstage; nie uruchamiaćponownie bez diagnozy. Nie podwyższać
medium ani progu błędów. To korekcjareferencjipostprocessingu, nie optymalizacja
productionPalace ani measuredantenna speedup.


EXP47 exit0/noOOM117,617s/RSS217MB, all2240positiveweights/4pi3. FineB4correction
adaptiveq6/q8E/H8,17e-13/8,34e-13, cutoff2/4 1,88e-14/1,86e-14,zerohits.
Correctedvolumeestimate E/H2,88847/1,61091%FAIL1%; oldq16vs corrected0,0311/0,0316%.
q6r2 279180leaves/25,068s,q8r2 279180/26,719s,q8r4 502040/59,561s.
Root independentlyrecomputedallcomplexnorms,input/source/helper/SHA andstates,
fullindices/weights,subset32regression<1e-13 in artifacts/m2-near-full-root-analysis-20261019.json.
Korekcja finepotential nie usuwa głównej rozbieżności pola. Nie rozstrzyga jeszcze
coarse-reference mesherror vs FEM/coupling; degreeagreement nadalotwarty.
Bez assembly/solve/build/GPU/cloud/swap/offload, zwykłe NPZinput/results wRAM.
85unitPASS pinned, system71PASS/14SKIP. Docs-garden read-only tej samej Luny
i rootreview PASS; root doprecyzował brak assembly operatorów FEM/BEM oraz
usunął dodatkowy nieaktualny licznik71unit z docs/testing. Checker/diffcheckPASS.
Lokalny commit bezpush; M2 ACTIVE, zero productionpromotion.


### EXP48 — prerejestracja: coarseB3subset i koszt przed pełnym replay

Poprzedni goalturn PROGRESS: commit5dbb3f2 fineB4nearcontrolPASS, polaFAIL.
Teraz nowy explicit--near-side coarse wybiera savedPMCHWTB3currents i cached
coarse_E/Hq12 na tych samychdegree5points. FineB4niezmienione, zeroassembly/solve.
Najpierw32targets(samefine q12/q16biasedselection +span), nie normafullvolume.
Nativecachedq12control3points<1e-12, adaptive6/8 i selectionradius2/4 E/H<1e-6,
zeroexhaustion. Zapiszold_q12vs corrected; old_q16=None bo brakcoarseq16cache.
Prądów/kandydataniezmieniać. Pomiar czasu/leaves przedall2240,deadline120s.
85unitPASS.6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-coarse-subset-20261019 --physics near-correction --level 2 --near-side coarse --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Przyfailzdiagnozowaćcache/side/normalization, bez zmianyprogów. Niepromować.


EXP48 coarse32pilot execution/correctionPASS9,268s/RSS216MB/noOOM. Nativeq12
vs rebuiltE/H3,83e-15/5,04e-15, adaptive6/8~1,4e-12,cutoff2/4~3,7e-14,
zeroexhaustion. Coarseoldq12→correctedE/H2,0627/2,2191% na biasedsubset;
niepełnanorma. q6r2 .874s/10104leaves,q8r2 .950s/10104,q8r4 1,437s/13854.
Rootstaty i weightedq12delta niezależnie przeliczone. Oldq16None zgodnie z cache.

### EXP49 — prerejestracja: all2240coarseB3 i porównanie ze skorygowanymB4

Zmienić tylko32→all, ten sam degree5/innyrefside już kontrolowany wEXP48.
KandydatFEM2/BEM3 i oba PMCHWTcurrents pozostająniezmienne. Każdyadaptive6/8 i
cutoff2/4globalE/H<1e-6,native3points<1e-12,zeroexhaustion. Dopiero po pełnym
runie rootporówna coarse/fine corrected na identycznychpointach/weights.
Prognoza~155–180s z pilotem i biasem; cap6GiB4CPU/tmpfs/noaddedSwap,deadline180s
bez przedłużania. Zeroassembly/solve/GPU/cloud/build. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-volume-b3-20261019 --physics near-correction --level 2 --near-count 0 --near-side coarse --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.
Nadal niepromowaćM2/FEM–BEM; field/volume-rule/mesh controls dopiero rozstrzygane.


EXP49 terminalny TIMEOUT 180 s, exit255, RunningFalse/OOMKilledFalse.
Ostatni etap q8/r4:1950/2240 punktów przy179,338s; brak case.json i pełnych pól.
Czasy z logów: nativecontrol4,987s; q6/r2 pełne44,564s; q8/r2 pełne48,028s;
q8/r4 częściowe81,759s. Nie jest to wynik jakościowy ani powód przedłużenia limitu.

### EXP50 — prerejestracja: cached Numba tych samych całek

Poprzedni turn odpowiedział na pytanie o UVM i sprawdził stan; NO PROGRESS
w implementacji. Następna bezpieczna akcja to kontrola gotowego JIT, nie restart EXP49.
Nowy opcjonalny backend numba FP64/complex128, bez fastmath; bounded DFS,
te same całki i kolejność dzieci, cache kodu /jit-cache, dane robocze RAM.
Default NumPy bez zmian. 88 unit PASS w pinned env; testy stubnjit nie dowodzą
kompilacji LLVM. Teraz rzeczywisty mały control: native/operator i NumPy/JIT<1e-12,
adaptiveq6/q8<1e-6, solid-angle abs<1e-8, zero depth exhaustion, podpis nopython.
Osobno czas compile/load i ciepłych kerneli. 6GiB/4CPU/tmpfs/noaddedSwap,
120s, bez GPU/chmury/Palace rebuild. Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-numba-control-20261019 --physics near-control --level 1 --near-backend numba --seconds 120`.
Tylko po PASS rozważyć pełny coarse replay z nowym backendem. M2 ACTIVE.

EXP50 PASS exit0/noOOM16,184s runner,14,873s case,RSS296MB. Actualnopython
signature,compile/load1,337s. JITvsNumPyregular<=4,11e-16/adaptive<=1,05e-15,
native<=1,92e-15,static1,929e-12,zerohits. Warmq8ratio2 .0103s vsNumPy.2093s;
ratio4 .0390s vs.8492s: microkernel~20x, not solver/antenna speedup.
Root terminal/sourceSHA/gates audit: artifacts/m2-near-numba-root-analysis-20261019.json.

### EXP51 — prerejestracja: pełny coarse replay z kontrolowanym JIT

Nowa hipoteza względem EXP49TIMEOUT: tylko backendNumPy→Numba, identyczne
2240point/weights/currents/FP64complex128/q6q8/radii2,4. Nativecontrol<1e-12,
adaptive/cutoffE/H<1e-6,zeroexhaustion. Porównać32savedsubsetEXP48 i pełny
fineB4EXP47; żadnej zmianyprogów. 180s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build.
Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-volume-b3-numba-20261019 --physics near-correction --level 2 --near-count 0 --near-side coarse --near-backend numba --volume-inputs artifacts/m2-transmission-volume-degree5-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 180`.

EXP51 PASS exit0/noOOM18,089s/RSS217MB,all2240points. CoarsecorrectedE/H
2,8260/1,7906%FAIL1%; native<=5,19e-15,adaptive<=1,44e-12,cutoff<=2,85e-14.
Zeroexhaustion. Q6r2/q8r2/q8r4:2,151/3,183/6,850s vsNumPy44,564/48,028/partial81,759s.
Paired32EXP48regression<3e-16. CorrectedB3→B4E/H1,6474/0,7806%: mesh-reference
stillnotconverged, nearquadraturewasnotsolecause. Rootanalysis artifact
m2-near-coarse-full-root-analysis-20261019.json; sources/inputSHA/gates audited.

### EXP52–53 — prerejestracja: degree2 reference replay

Same saved FEM2coefficients and PMCHWTB3/B4currents; change only saved volume
rule degree5→degree2(640positivepoints). Qualified NumBa backend, allpoints;
first fineB4, then coarseB3. Nativecontrol<1e-12,adaptive/cutoff<1e-6,zerohits.
Root compares correcteddegree2/5 whole-volume estimates AND reference change;
no looser tolerances or new solve. 120s EACH/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build.
Exact argv52:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-degree2-b4-numba-20261019 --physics near-correction --level 2 --near-count 0 --near-side fine --near-backend numba --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Exact argv53 (only after52 terminal):
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-near-correction-degree2-b3-numba-20261019 --physics near-correction --level 2 --near-count 0 --near-side coarse --near-backend numba --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.

EXP52/53 PASS exit0/noOOM7,981/9,165s,RSS217/216MB; all640points,
native<=9,82e-15/adaptive/cutoff<=1,28e-12/zeroexhaustion. FineE/H2,15175/.86299%;
coarse1,75728/.88825%; correctedreferencechange1,08557/.44227%FAIL0,3%.
Degree5fine2,88847/1,61091%; error-estimate degree2→5 relativechange25,5/46,4%
FAIL1e-6. Root verified weightedcomplexnorms/points/weights and terminal gates:
artifacts/m2-near-volume-degree-root-analysis-20261019.json. Bothreference sides
nearquadraturecontrolled, volume/reference discretization still notqualified.
Next: controlled volume/reference convergence before FEMperturbation; no blindB5/q.
Docs updated; no Palacechanges/build/GPU/cloud/productionpromotion. M2 ACTIVE.

Walidacja końcowa:88unitPASS pinned/system74PASS14SKIP, docschecker i diffcheckPASS.
Ta sama Luna wykonała read-only docs-garden: zgodność wyniku/kodu/scopePASS;
wskazała trzy nieaktualne bieżące liczniki, root poprawił je i checkpoint/nextstep.
Historyczne liczniki EXP zachowano. Lokalne źródła/cache, bezpush.


### EXP54–55 — prerejestracja: niezależny analityczny FEM dla epsilon2,94

Poprzedni turn PROGRESS: commit410a854, cached nearJIT i corrected B3/B4/degree2/5;
niepromowany prototyp. Root teraz rozłożył zapisane błędy wg odległości od20planes
tej samej bryły (modelunits): degree5distance>.2 ma E/H1,791/1,539%, ale
B3→B4change tylko.101/.048%; distance<.05: E/H5,032/1,932%, refchange3,506/1,665%.
Artifact m2-near-boundary-error-analysis-20261019.json; emptybins=null, niepełnenormy.
Hipoteza: FEMresolution jest istotna niezależnie od brzegowego błędu referencji.
Nie rozstrzygać po dopasowaniu trendu: sprawdzić tę samą ND2bryłę F2/F3
z dokładnym Ex=exp(i*sqrt(eps)*z), physicalHy=sqrt(eps)*Ex i Dirichletdata.
Operator curlcurl-eps*M; helper raportuje H/sqrt(eps), względny błąd fizycznegoH
jest taki sam. Eps1 default ND2 i eps2,94 default transmission bez zmian.
Nowy parametr jedynie w analyticND2probe; stare guardedgeometryhelpers bez zmian.
Każdy run raw<1e-10,basis<1e-11,quad6/8delta<1e-6; fieldtarget1% unchanged.
Test nie jest transmisją przez interfejs ani pełną kwalifikacjąM2. 89unitPASS.
120s EACH/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build; exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-eps294-f2-20261019 --physics nd2 --level 2 --epsilon-r 2.94 --seconds 120`.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-eps294-f3-20261019 --physics nd2 --level 3 --epsilon-r 2.94 --seconds 120`.
Run55 only after54 terminal; failureexecution stops sequence, fieldFAIL retained.

EXP54/55 executionPASS noOOM1,071/5,572s,RSS287/432MB. F2DirichletE/H
1,7363/2,4894%FAIL1%; F3 .4431/.7171%PASS1%. Raw<=5,73e-15,q6/8delta<=1,22e-11.
Root checked terminal/currentcaseSHA/eps/k² and normalizations; artifact
m2-nd2-eps294-root-analysis-20261019.json. F3 analytic pass motivates actual
coupledrefinement, not dielectrictransmission qualification or memoryspeedup.

### EXP56 — prerejestracja: dielectric coupled F2→F3 z BEM3 fixed

Jedyna zmiana względem EXP40: FEM2(160tet/1228DOF)→FEM3(1280tet/8936DOF).
Ten sam epsilon2,94, surfaceB3, paramsq4, BC/RWGmortar/Schur; zachować savedu/t/h.
Nativecoupling/transmission helpers unchanged. Existing run robi centroidscreening
vs PMCHWTB2/B3; to nie pełny L2 i nie zastępuje volumeB4reference.
Hipoteza na podstawie EXP54/55: FEM error maleje, ale reference/coarsemesh
nadal ogranicza kwalifikację. Raw<1e-9 i mortar<1e-12; dotychczasowe field/energy
thresholds unchanged, FAIL retained. 180s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build.
Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-transmission-eps294-f3-b3-20261019 --physics transmission --level 3 --surface-level 3 --epsilon-r 2.94 --seconds 180`.
Po solve bez ślepego ponawiania; ocenić cachedvolume z samą referencjąB4 zEXP41.

EXP56 executionPASS115,0s/RSS1,325GB/noOOM, screeningFAIL zachowany. Centroid1280
E/H1,4988/1,0847%, referenceB2→B3change7,968/7,643%: not comparable to EXP40
centroid160sample. Farrelative.04498%, energy/pi1,28e-7/raw1,97e-13 PASS.
Savedcoupled-solution.npz preserved. Root terminal/sourceSHA checked.

### EXP57 — prerejestracja: stałe640punkty, bez nowego BEMsolve/potential

Aby nie powtarzać kosztownych potencjałów, nowy bounded `fem-replay` bierze
F3savedu zEXP56 i dokładnie640degree2points/weights zEXP42; referenceB4 currents
zEXP41 służą guardom fizyki. Root porówna replay z correctedB4EXP52 iF2EXP42
na identycznych punktach oraz osobno wnętrzu distance>.2 (modelunits).
Strictbarycentricowner>1e-10 eliminuje niejednoznaczność normalnegoE na faces;
reject zamiast wybierania wartości arbitralnie. Ten zbiór nie jest zbieżną
normąFEM3: żadnej kwalifikacji całego pola na podstawie tego screenu.
Walidacja inputów: terminal/noOOM/sourcehelper/nativeABI/npzSHA/eps/degree2.
Nie eksportować nowych macierzy, nie solve/BEMassembly; mały GlobalNDconstructor
nadal assembles mass/curlforms. 92unitPASS.120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build.
Dokładny argv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fem3-fixed-probes-20261019 --physics fem-replay --level 3 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --probe-input artifacts/m2-transmission-volume-degree2-20261019 --seconds 120`.

EXP57 executionPASS0,761s/RSS296MB/noOOM; all640strictowners,minlambda.1708204.
Root independently compared identicalpoints/weights/current/sourceSHA andallinputSHA.
F2→F3 vs correctedB4: E2,15175→.66355%,H.86299→.59717% onall640probes.
Core distance>.2(modelunits),300points/46,875%vol: E1,19656→.18592%,H.75174→.25188%;
refB3→B4change.05517/.04366%. Near340points: F3E/H.93207/.81265%, refchange1,55555/.62954%.
Rootanalysis m2-fem3-fixed-probes-root-analysis-20261019.json. RefinedFEM helps,
but coarseprobes don't establish fullF3L2 or reference/volumeconvergence.

### EXP58 — prerejestracja: domyślny ND2epsilon1 regression

Zmiana parametruepsilon nie może zmienić defaultuND2. Powtórzyć tani F3analytic
bez flagiepsilon i porównać z zachowanym EXP33 po samejgranicypól/kodunormy.
Expectedepsilon1,k1,Dirichlet E/H.1505/.3317%, raw/quad/basis gates unchanged.
120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build. Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-nd2-eps1-default-regression-20261019 --physics nd2 --level 3 --seconds 120`.

EXP58 execution/analyticPASS5,520s/RSS432MB/noOOM,epsilon1/k1. Dirichlet E/H
.150508/.331747% identyczne z EXP33(m2-global-nd2-level3-q6-20261019/case.json).
Root ponadto odtworzył physicalprobe coordinates z cell/localmap do<1e-13
w EXP57; savedinput/sourceSHA/terminalnoOOM verified. Aktualny docs/wyniki i
nextstep zapisane. Niepromowane: M2volume/reference/rezonanse/koszt nadalotwarte.

Walidacja robocza:92unitPASS pinned; system76PASS16SKIP. Docschecker/diffcheckPASS.

Docs-garden read-only tej samej Luny: PASS, brak sprzeczności scope/kodu/artefaktów.
Rootreview: physicalpointreconstruction i epsilon1default exactregression sprawdzone;
żadnego utożsamienia fixedpointów z convergedL2. Checker/diffcheckPASS.
Lokalny commit bezpush. M2ACTIVE, goal nieukończony; brak zmiany medium/anteny.


### EXP59 — prerejestracja: streaming potential, bez macierzy punkt×DOF

Poprzedni turn PROGRESS: commit91b7f5f, rzeczywistyFEM3solve i identical640probes
poprawiają E/H. Nowa bezpieczna akcja: mała kontrola pełnej sumy potencjałów,
aby później obliczyć właściwą F3volume rule bez kosztownego nativepotentialmatrix.
maxwell_stream.py: existing cached nearjit FP64/complex128/no fastmath,
NumBa parallel over targets (existing threadlimit2), stała kolejność paneli.
Każdy farpanel liczy regularq12, bliski adaptiveq8/ratio2; selectionradius4.
Kontrola32saveddegree2points vs cachednativeq12(radius0) i osobno incremental
qualifiednearcorrection(q8/r4). GatekażdeE/H<1e-12, finite,zeroexhaustion,
actualnopythonsignature; compile/load i ciepłyapply osobno. 95unitPASS; stubnjit
wunitach nie jest dowodem LLVM. Zero nowego solve/BEMassembly/GPU/cloud/build.
120s/6GiB4CPU/tmpfs/noaddedSwap. DaneRAM, cache kodu osobno. Dokładnyargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-control-20261019 --physics stream-control --level 2 --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Po PASS dopiero pilot32na realnej reguleF3degree2; nie uruchamiać full bez oceny kosztu.

EXP59 operator/executionPASS9,157s/RSS250MB/noOOM. Actualnopython,threads2,
compile/load2,900s. Full32point potentialapply .0582s, native/incremental
E/H<=8,88e-15, zeroexhaustion. Pilotfieldestimate2,887/.942% biased, not norm.
Rootauditedallinput/sourceSHA and terminalstates; artifact
m2-stream-control-root-analysis-20261019.json. No potentialmatrix/solve.

### EXP60 — prerejestracja: kosztowy pilot na własnej reguleF3degree2

SavedF3u(EXP56), PMCHWTB4currents(EXP41), 5120positivecellquadraturepoints;
wybrać32(16closest20planes+16spanning), bez nowego solve. Ten pilot nie jest
normąobjętości. Basefarq12/nearquad8/radius4, samequalifiedkernel. Sprawdzić
finite/nopython/zerodepthhits i czas cieplegoapply/leaves przedfull5120.
120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build. Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-pilot-20261019 --physics stream-volume --level 3 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.

EXP60 executionPASS5,241scase/RSS430MB/noOOM.5120original/32biasedpoints,
apply.0599s,setup.0160s,maxdepth4,zerohits. PilotE/H3,327/1,596% niepełnanorma.
Conservativeapply estimate .06*5120/32~9,6s plus setup<10s; supports fullrun
without extending120s caps. No potentialmatrix/solve.

### EXP61–62 — prerejestracja: własna pełna regułaF3degree2 i nearquadrature

Change only32→all5120points/weights, savedu/currents unchanged. EXP61base:
farq12/nearquad8/radius4. EXP62near6: farq12/nearquad6/radius4. Root porówna
weightedcomplexE/Hdelta<1e-6, samepoint/weights/SHA, zeroexhaustion. Wyniknormy
nadal wymaga radius/far, degree i reference mesh controls; niepromować samychminimów.
120s EACH/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build. Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-base-20261019 --physics stream-volume --level 3 --near-count 0 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-near6-20261019 --physics stream-volume --level 3 --near-count 0 --stream-variant near6 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
EXP62 po terminalnym executionPASS61; bez retry/extension.

EXP61/62 executionPASS all5120points,case14,417/13,311s,RSS431/433MB,noOOM.
BaseE/H1,463205/.864503%: EFAIL1%, HscreenPASS; notconvergedvolume.
Apply9,248/8,166s,zeroexhaustion,maxdepth4,1,101,292leaves.
Rootweightednear6vs8delta E/H=1.41677e-12/1.41611e-12PASS1e-6,samepointsweights.

### EXP63–65 — prerejestracja: radius/far i reference mesh na tej samej regule

SavedF3coefficients/currentinputs unchanged, all5120degree2. Finevariants radius2
(qfar12/qnear8/r2) i far16(qfar16/qnear8/r4) porównać zbase weightedE/H<1e-6.
CoarseB3base vsfineB4 mierzyreferencechange, frozen0,3% niezmieniony.
120s EACH/6GiB4CPU/tmpfs/noaddedSwap/noGPU/cloud/build, bezretry.
Exactargv63:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-radius2-20261019 --physics stream-volume --level 3 --near-count 0 --stream-variant radius2 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Exactargv64:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-far16-20261019 --physics stream-volume --level 3 --near-count 0 --stream-variant far16 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Exactargv65:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree2-coarse-20261019 --physics stream-volume --level 3 --near-count 0 --near-side coarse --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Sequential after terminalexecutionPASS, interpretation root only. No fieldqualification yet.

EXP63–65 all5120 executionPASS/noOOM,RSS<=434MB. Fine radius2/far16E/H
1,463205/.864503%; coarse1,583615/.860008%. Case13,864/17,838/10,107s,
apply8,697/12,668/4,928s,zerohits. Rootweightedbase deltasradius2<=2,21e-14,
far16<=1,42e-15; near6<=1,42e-12PASS1e-6. ReferenceB3→B4 E/H1,55485/.75206%
FAIL0,3%; fieldEFAIL1%. Artifact m2-stream-f3-degree2-root-analysis-20261019.json.
No densepotentialmatrix/solve; notantenna speedup or convergednorm.

### EXP66–67 — prerejestracja: własna regułaF3degree5

Change onlydegree2→5:5120→17920positivepoints, savedF3u andPMCHWTcurrents unchanged.
FineB4base then coarseB3base. Hypothesis: resolve volumequadrature sensitivity
and reference mesh change before claiming trueL2. Near/far controls qualified
on degree2; degree5control remains separate if field/reference promising.
Costestimate3,5×apply9,25s plus setup~5s, allow~2×extra nearwork<120s; no capraise.
Frozen field1%/reference.3%/volumeagreement1e-6 unchanged. No solve/GPU/build/cloud.
120s EACH/6GiB4CPU/tmpfs/noaddedSwap. Exactargv66:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree5-base-20261019 --physics stream-volume --level 3 --near-count 0 --volume-degree 5 --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Exactargv67:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-f3-degree5-coarse-20261019 --physics stream-volume --level 3 --near-count 0 --volume-degree 5 --near-side coarse --volume-inputs artifacts/m2-transmission-eps294-f3-b3-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.
Next only after terminalexecutionPASS, no autoretry. Rootanalysis only.

EXP66/67 executionPASS all17920degree5points,noOOM,RSS442/440MB,case37,210/22,216s,
apply31,985/17,035s,zeroexhaustion,maxdepth5/6. FineE/H1,68335/.97150%,
coarse1,75075/1,04841%. Rootcorrectedreferencechange1,72451/.87598%FAIL0,3%;
relative degree2→5 fieldestimatechange13,0779/11,0139%FAIL1e-6.
FEM_Hsquarednorm q2/q5 exactlysame: expected curlND2degree1, |H|²degree2.
Root allinput/sourceSHA/state, positiveweights4pi/3, pilotfullregression audited;
artifact m2-stream-f3-volume-root-analysis-20261019.json. Degree5near/farcontrols
NOTRUN, niepromować. Nie ponawiać tego samego solve/ślepego volumeq.

Źródłowa korekta hipotezy: native Bempp NumBa potential NIE tworzy pełnej
macierzy punkt×DOF. Pinned core/numba_assemblers.py i numba_kernels.py
maxwell_efield_potential/maxwell_mfield_potential liczą bezpośrednią aplikację,
ale mają global_points/tmp/diff w rozmiarze panel×quad i osobne T/K/currents.
Nowy stream fuses cztery T/K dla2currents i ogranicza pertarget temporary do
panelu. Wcześniejsze słowa 'nativepotentialmatrix' w EXP59/roadmap były błędną
hipotezą, nie zmierzoną alokacją. Nie raportować oszczędności macierzy ani
przyspieszenia względem native bez matchedmeasurement.

### EXP68 — prerejestracja: matched native+correction vs fused apply

Ten sam32pointcontrol/currents/q12+adaptiveq8radius4, dokładność<1e-12.
Dodać rzeczywistą native q12evaluation (warmup1point/cachetime osobno),
porównać z cached q12; osobno panelpreparation, fusedapply i incrementalcorrection.
Native NumBa również matrixfree. Test nie mierzy peakmemorydelta/antenna speed.
120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build; źródła geometry/nearjit bez zmian.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-native-comparison-20261019 --physics stream-control --level 2 --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.

FMM feasibility audit only, NOTRUN/notinstalled: pinned Bempp0.4.2 fmm_assembler.py
supports MaxwellT/K; Dockerfile pins exafmm-t0.1.1. Official Bempp handbook confirms
assembler='fmm', https://bempp.com/handbook/api/boundary_operators.html and
https://bempp.com/handbook/core/assembling_operators.html . Local exafmm=None.
ExafmmInterface creates cwd/.exafmm/*.tmp; must stay /scratch tmpfs under existing
caps, never disk. Dense referenceB5N7680 has4operators+15360²block≥7,550GB beforeLU,
over6GiBcap, so no denseB5 attempt. Nextcandidate independent PMCHWT-FMM reference
with small denseT/K/action/solution controls beforehighermesh; no guarantee of benefit.

EXP68 operatorPASS17,072s/RSS292MB/noOOM. Actualnativeq12 exactlycached,
othercontrols<=8,88e-15. Nativewarm/load9,064s, first32evaluation2,837s;
fusedpanelsetup1,758s/apply.05955s, incremental.07555s. Single native32timing
is not robust warmed benchmark: add3repeats, report samples/median andsetup
rather than applying microkernelratio to end-to-end. No peakmemorydelta claim.

### EXP69 — prerejestracja: repeat matched warmed potential query

Same32points/currentinputs/numerics asEXP68, only3warmmeasurements permethod,
withnativewarmup1point andexplicit panelssetup/JITcost. Median/samples reported;
includesnativeq12+incremental vsfusedpanelsetup+apply; sourcewithoutpointmatrixclaim.
120s/6GiB4CPU/tmpfs/noaddedSwap/noGPU/build, no retries. Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-stream-native-repeat-20261019 --physics stream-control --level 2 --volume-inputs artifacts/m2-transmission-volume-degree2-20261019 artifacts/m2-transmission-reference-b3-b4-20261019 --seconds 120`.

EXP69 PASS22,897s/RSS292MB/noOOM, nativeactualq12exactcached i pozostałe
controls<=8,88e-15. Nativequeries2,8344/2,8550/2,8697s,fused.05931/.05892/.05861s;
incremental.07567s,wspólnepanelprep1,77788s. Matched pojedynczequeryzprep:
4,70855→1,83680s (~2,56x); amortizedquery2,93067→.05892s(~49,7x), tylkoCPU32points.
Root allinput/sourceSHA/terminalgatesaudited w m2-stream-repeat-root-analysis-20261019.json.
Nie mierzonodeltapeakRAM aniantenna speedup. Nativealreadymatrixfree fact corrected.
Docs/INDEX/ARCH/PLAN i nextstep zaktualizowane; nadalM2ACTIVE i nierozwiązane
field/volume/reference gates. FMMaudytkandydataNOTRUN, bezinstalacjideps.

Walidacja historycznego commitu e57ba76:95unitPASS pinned/system79PASS16SKIP, checker/diffcheckPASS.
Ta sama Luna: read-only docs-gardenPASS, bez sprzeczności i bez edycji.
Rootreview: native-no-pointmatrix correction, matchingcost z commonpanelprep,
frozenFAILgates i FMM/tmpfsNOTRUN sprawdzone. Commit lokalny, bezpush.
Następne M2FMMsource/małyMaxwelloracle; brak nowej antena/medium/defaultpromotion.


### EXP70 — prerejestracja: izolowany cached ExaFMM addon

Poprzedni turn PROGRESS: commite57ba76 fusedpotential i własnaF3volume/refFAIL;
nextreferenceFMMcandidate. Root przypiął exafmm-t v0.1.1 do commit
78b7d56f988b3843ba502faf4ac60b0c013aa206; LICENSE BSD3Clause (setup metadataMIT
nie jest źródłem licencji). Sourcecheckoutclean bez modyfikacji upstream.
Pybind11headers2.13.6 prywatnytarget .cache/m2-build-deps, bez zmian venv/Bempp.

Read-only dependencyprobes dużego PalacebuilderImage(25,4GB) nie wystartowały
z cap6GiB: OCIinit 'OOM-killed?' lubparentreset, także z Luny. Nie dowodzi
hostOOM: MemAvailable~69GiB,parentcgroup memoryevents oom0, runtimeimage /bin/true
startuje pod tym samymcap. Nie podniesiono limitów ani zamknięto aplikacji.
Zamiast kolejnych prób nowy mały cached builder frompinnedUbuntu24.04 digest
68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac,
tylko g++/ccache/FFTW/OpenBLAS, bez Palace/dependencyrebuild i bez kasowaniacache.

exafmm_build.py: namedimageprovision max180s/6GiB4CPU, cached image byrecipe;
compile1TU przezccache -c, osobnylink, max120s/6GiB4CPU/tmpfs/noaddedSwap/networknone.
Headers/PythonbinaryABI/source/builder/runtimeimage/flags i prywatneFFTW/BLAS
librarySHA wmanifest. Tworzone obrazy/cache są softwarecache, nie solveroffload.
NumericalsolverNOTRUN; successfulbuild nie kwalifikuje importu/FMM/Maxwell.
Root przygotował kod; Luna tylkoexactbuildargv i terminalmonitoring, bez decyzji.
Exactargv:
`python3 tools/experiments/exafmm_build.py build`.
Po PASS osobny runtimeimport i małyMaxwellFMMvsdense przedB5. NofullPalacebuild/GPU/paidcompute.

EXP70 buildPASS21,455s, imageprovision/compile terminalexit0/noOOM.
BinarySHA7bb42c3049da13405d4c2a604352af6b89b14ed54466c4c51243b56b660c6e48.
Rootrecipe/artifactfingerprintverified; no runtime/numericalpass yet. Imagesmall
Ubuntu+FFTW/BLAS+g++ solves provisioning path without changing Palacebuildercache.

### EXP71 — prerejestracja: cached rebuild + runtime MaxwellFMMvsdense

First repeat samebuildargv: expectverifiedno-op/noC++compile, preservesbinarySHA.
Then runtimeimportprivateCPython3.12module+libs on originaloracleruntime, no newvenvdeps.
SurfaceB2RWG120, k=1/sqrt(2,94), quadregular/singular4, FMMorder6/ncrit32.
Three deterministic complexvectors eachT/K; weightedgeometry same asdense,
relativeactiongate1e-6, dtypecomplex128, nohiddenGLOBALdensefallback. Require
nontrivialtree depth>=2 andallFMMtmp under /scratchtmpfs512MiB; privatelibsfromreceipt.
No transmission solve/Mie/antenna or scalabilityqualification on operatorpass.
99systemtests:83PASS16SKIP. Numericalrun120s/6GiB4CPU/noaddedSwap/noGPU/paidcompute.
Exactargvs sequential:
`python3 tools/experiments/exafmm_build.py build`.
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-maxwell-o6-n32-20261019 --physics fmm-control --level 2 --fmm-order 6 --fmm-ncrit 32 --seconds 120`.
OnlyaftercachedbuildterminalPASS; no retries or limit changes.

EXP71 terminal exit0/noOOM, executionPASS but operator_controlFAIL. Root checked
case/command/container-state: p6/ncrit32, complex128,120DOF,480sources/targets,
two73node depth2trees. T relative action error2.15e-6/2.24e-6; K1.95e-5/1.66e-5
at k1/sqrt2.94, exceeding frozen1e-6. Elapsed26.331s/sharedRSS497680384B.
Build repeat cache no-op0.105s. No numerical qualification or speedup promotion.

### EXP72 — prerejestracja: MaxwellFMM order8, unchanged action gate

Previous goal response was an explanation/plan (no progress); EXP71 is terminal,
so next safe action is p6→p8 only. Same geometry/B2, ncrit32, quad4, k/vectors,
complex128 and1e-6gate. Added report-only actual FMM tempfile bytes and tmpfs
occupancy/capacity; cwd remains512MiB RAM tmpfs,6GiB/4CPU/noaddedSwap/networknone.
No source/Palace rebuild, no paidcompute/GPU, max120s. A pass qualifies small
operator actions only; then actual PMCHWTsolution control before higher reference.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-maxwell-o8-n32-20261019 --physics fmm-control --level 2 --fmm-order 8 --fmm-ncrit 32 --seconds 120`.

EXP72 terminalexit0/noOOM28.036s/RSS708407296B, operatorFAIL. k1T/K4.14e-8/
5.55e-7 meetgate, ksqrt2.94 T/K.27650/.83602 invalid. Root found scratch_used
536870912==capacity; firstfile302215176B, second234651648B truncated atcap.
Pinned ExaFMM fmm.h precompute closes ofstream without checking errors, and
evaluate rereads its tables. Runtimeexit0 is not numericalvalidity. This is
tmpfs/RAM exhaustion, NOT SSD scratch or proof highorder mathematicalfailure.

### EXP73 — prerejestracja: sequential-wave cache lifetime, same512MiBcap

Independent k1/kdielectric controls don't need coexistence. Snapshot receipts,
release each tree via upstream clear_fmm_cache, delete only its runtime tmpfiles
via upstream cleanup_fmm_tmp; preserve source/JIT/build caches. New failfast check
before numericalaction rejects exhausted tmpfs. Same p8/ncrit32/q4/vectors/gate,
120s/6GiB4CPU, no capincrease, no SSD fallback. Not yet PMCHWT simultaneous2k.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-maxwell-o8-sequential-20261019 --physics fmm-control --level 2 --fmm-order 8 --fmm-ncrit 32 --seconds 120`.

EXP73 terminalexit0/noOOM, execution/operatorPASS, analyticFalse. Root inspected
case/state:28.331s/RSS624742400B, Terrors4.14e-8/4.67e-8, K5.55e-7/4.71e-7.
Both tables302215176B individually, peakRAMtmpfs302219264B/end0/cap536870912B.
This removes spurious corruption by sequential independent-wave lifetime, not
a solution for simultaneousPMCHWT or proof antenna memory/speed improvement.
Next: budget true PMCHWT2k storage and solve-vs-dense, no change to frozen gates.
Docs maxwell-fmm/stream, PLAN/M2/INDEX/ARCH/testing updated; M2 remainsACTIVE.

EXP73 finalvalidation:101testsPASS pinned; system85PASS/16SKIP. SameLuna
read-only docs-garden reviewed code/untracked/report: no numerical/scope
contradictions; stale current-suite95 corrected to101 (historical e57ba76 count
retained with explicitlabel). Checker/diffcheckPASS. Root verified currentcaseSHA
match EXP73command and terminalstate exit0/noOOM. No antenna/promotion/M3 claim.
Local commit only, no push to public upstream.

### EXP74 — prerejestracja: actual PMCHWT FMM vs independent dense solve

Previous turn progress: f41aeca, cachedaddon/MaxwellactionPASS after RAM-lifetime
fix. Next full small PMCHWT at sameB2/p8/ncrit32/q4/k1/sqrt2.94/complex128.
Each wave retains its302MBtable on one existing RAMtmpfs mount: /scratch or/tmp,
512MiB each, same total6GiB/4CPU/noswap cap. No table/tree rebuild per iteration,
noSSDscratch. Root prepared exact matrix blocks from frozen transmission helper
without editing it; bothdense andFMM share geometry/RWG-SNC/projections. Dense
is independent tiny oracle only, not a scalable preconditioner or FMMfallback.
Actual LinearOperator GMRES rtol1e-10, restart32/onecycle, max120s. Report raw
FMM and independentdense residuals, coefficientdifference, iterations/matvec/setup
cost and sharedRSS. Gates raw<1e-9, coefficientrel<1e-6; no field/Miequalification
from small solve. Nonconvergence/frozenindependentrawFAIL remainsfailure.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-pmchwt-o8-20261019 --physics fmm-solve --level 2 --fmm-order 8 --fmm-ncrit 32 --seconds 120`.

EXP74 terminalexit0/noOOM, sourceSHA/terminal verified byroot before edits.
GMRES32/info1, FMMraw.018024085 vs independentraw.018024085, coefficienterr6.484%.
Dense raw2.467e-15. Solve52.868s,34matvec54.398s(include finalcheck), total81.259s,
RSS717533184B. Both RAMtmpfs302219264B peak/end0, no overflow/rebuild.
FAIL is nonconvergence, not evidence that converged FMM solution meets gates.

### EXP75 — prerejestracja: sparse adjacent-panel near-ILU for M2 solve control

One change: leftpreconditioner from existing exact singular_part sparse matrices
of fourMaxwelloperators, no dense oracle entries, no singularRWGGram inversion.
Same PMCHWTblocksigns; spilu drop_tol1e-3/fill_factor5. Report actual sparse/factor
nnz/bytes and setup. Same p8/quad4/B2/32GMRESsteps/rtol1e-10/raw1e-9/coeff1e-6.
Still M2 solver feasibility (not moving to M3/M5 or promoting preconditioner).
No cache/dependency rebuild, unchanged6GiB4CPU/tmpfs512MiBeach/noSwap/120s.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-pmchwt-near-ilu-20261019 --physics fmm-solve --level 2 --fmm-order 8 --fmm-ncrit 32 --fmm-preconditioner near-ilu --seconds 120`.

EXP75 terminalexit0/noOOM71.560s/RSS721100800B, solveFAIL. NearILU matrix12960nnz/
260164B, factors39578nnz/793488B, setup.00960s. GMRES26/info1 stoppedcycle before
rtol; rawFMM9.464e-10 meets1e-9gate but notrequested1e-10 stopping, independent
raw1.302e-7 FAIL, coeffrel3.850e-7 PASS. Solve43.060s vs52.868s unpreconditioned
(bothincomplete, not qualifiedspeedup). Error floor now operatoraccuracy, not
simply iterationcap. No promotion/relaxedgates.

### EXP76 — prerejestracja: p9 precision step with predicted RAM table budget

One change fromEXP75: order8→9. Pinned fmm.h filelayout predicts complex128
table:20*nsurf²*(depth+1)*16+26*(2*(2*p)^3*8*8)*depth*8+8,nsurf=6*(p-1)^2+2.
Geometry.h gives8M2M/26M2Lpositions. Atactualdepth2 p8=302215176B(exactobserved),
p9=453578504B(fits512MiB); p10=654602248B DOESNOTFIT, do not blindlyrunp10.
Added preflight budget and exactpostbuildfile-sizeguard, nohighercaps. Same
nearILU/32steps/rtol/raw/coeffgates, allFP64complex128,120s/6GiB4CPU/noSwap.
Exactargv:
`python3 tools/experiments/bempp_oracle.py run artifacts/m2-fmm-pmchwt-o9-near-ilu-20261019 --physics fmm-solve --level 2 --fmm-order 9 --fmm-ncrit 32 --fmm-preconditioner near-ilu --seconds 120`.

EXP76 terminalexit0/noOOM, rootverifiedsourceSHA/state. p9independentraw1.272e-8
stillFAIL1e-9, coeff3.004e-8 PASS; info1/26iter, FMMraw9.464e-10 notrtol1e-10.
Solve59.005s,total88.396s,RSS900726784B. Bothtables453578504B equalpredicted,
tmpfs453578752B each/end0. p9highercost reducesoperatorfloor but doesnotqualify.

### M2 decision — assessment CLOSED / integration REJECT, M3 ACTIVE

Existing PLAN already allows negative hypothesis closure with evidence; after
actual CUDA/H-matrix/coupled/transmission/FMM assessments, reject current
productionintegration. M2.2wholefield/convergence andM2.3matchedqualitycost remain
FAIL/incomplete, NOTPASS. No gates relaxed and no antenna/BEM promotion.
Decision audit docs/milestones/M2-decision.md links scope/results and unsupported
feed/thinmetals; avoid endless p increases without qualified speed/memory.
ActiveM3 direct FP32basis/FP64 operations in existing FEM, baseline preserved.
Sourceaudit: iterative.cpp Unpacks StoredBasisVector forbasisread/MGS; vector.cpp
Pack/Unpack; optin existing but NOTqualified on currentM1reference. NextsmallCUDA
probe→cachedincrementalbuild→W.1 thenW.2/W.3. PLAN/MILESTONES/INDEX/M2/M3 synced.

Rootcostcaveat: reported RSS includes dense oracle but is not wholecgrouppeak;
tmpfs pages separate. No claim totalprocessmemory reduced based only onRSS.
Sourceaudit confirms unpack in everycompressed MGS k-loop and beforeApplyBA;
direct mixed dot/axpy is intended firstM3 prototype, no newprecision runyet.

Final EXP74–76 validation:102unitPASS pinned; system86PASS/16SKIP. SameLuna
read-only docs-gardenPASS: M2negativeassessment vs failednumericalgates explicit,
M3ACTIVE, tmpfs/RSS/p10limits agree withsource/artifacts. Checker/diffcheckPASS.
Rootreview complete; localcommit only/no push. No fullantenna/speedup promotion.

### EXP77 — prerejestracja M3: shared FP32-storage/FP64 arithmetic CUDA probe

Previous turn progress f58d028: M2assessmentCLOSED/productionREJECT, M3ACTIVE.
Root audited compressed MGS: iterative.cpp unpacks basis insideeachk and before
ApplyBA. LocalDot(w,b)=sum(w*conj(b)), linear firstargument. New pure header
mixedbasis.hpp defines partialdot/complexaxpy with floatloads castdouble BEFORE
products/accumulation. Not wired into GMRES yet. Header shared with isolated
CUDA probe; no ABIcasts, fastmath, FP32accum or TensorCoreclaim.

Compile only oneCUDA TU sm120 via existingbuilder/ccache, separatelink,120s;
no Palace/dependencies rebuild. Subsequent identicalbuild expects cache no-op.
Numerics same pinnedPython/NumPy environment andruntime;6GiB4CPU/noSwap,
RAMtmpfs512MiBeach/networknone, localGPUfree>=768MiB,60sdeadline. Largest
vector2^20, explicitdevicealloc~77MB plusCUDAcontext (not fullprocesspeak).
Reference longdouble math on SAME quantizedfloatstorage; gate normalizeddot/
axpy1e-12, separate FP32quantization norm-product-scaled gate2e-7.
Casesn1(nontrivialcomplexsign),1009,131071(dynamicrange1e-30..1e30),1048576;
rejectn0 beforeallocation. Two-stage FP64reduction, partialcount<=65536.
Compare direct dot+axpy vs unpack→sameFP64kernels, identicalworkvectorreset.
Alternate executionorder acrosspairedtrials; eventtimers excludealloc/H2D/JIT,
includecommonDtoDresets. NOT HYPRE/GMRES/fullantenna benchmark or UVMprofile.
105systemtests89PASS16SKIP. Rootdesign; sameLunaexactargv/babysitting only.
Exactargvs sequential, later only afterprior terminalPASS:
`python3 tools/experiments/mixed_basis_probe.py build`.
`python3 tools/experiments/mixed_basis_probe.py build` (cache repeat).
`python3 tools/experiments/mixed_basis_probe.py run artifacts/m3-mixed-basis-cuda-20261019 --seconds 60`.

EXP77 allterminalPASS/rootverifiedsource/header/worker receipts andstateexit0/noOOM.
First build1.503s(manifest), repeatno-op; noMFEM/Palace rebuild. Sharedheader
complexarithPASS atall4sizes; maxnormalizeddot4.43e-18,axpy4.40e-17,
FP32quantizationnorm-scaled8.87e-10. LargestN1048576 median.109695msdirect vs
.119766msunpack(~8.4%lowerprobeeventtime, NOTGMRES/HYPRE/antenna gain).
Explicitdevicealloc76546064B includesbothpaths, reductionworkspace1048592B,
baselineunpack16777216B; no peakVRAMdelta measured. Probeelapsed.501s/RSS476MB.

### EXP78 — prerejestracja: opt-in Palace direct basis and cached incremental build

Root wired StoredBasisVector::Dot/AddTo with shared1MiBmaxpartials perGMRES,
floatloads→FP64products/accumulation, MFEMforall+HYPREFP64sums/MPIcomplexreduce.
Real path added separately (not yetGPUqualified); complexconventionmatches
LocalDot(w,b). PALACE_GMRES_FP32_DIRECT requires FP32storage and existingMGS;
defaultFP64 and FP32unpack path preserved. OneUnpack beforeApplyBA remains
because operator expectsFP64; innerMGS/update avoidrepeatedfullvectorconversion.
Reliable residual/restarts unchanged. No newFMM/no model/mesh/Order changes.

Before incrementalbuild root copied verified11MiBpre-M3nativebinaries+manifest
to build/m3-basis/pre-m3-native (cache/fallback, not solverdata). Firstcoreheader
APIchange may invalidate Palace TUs, but installeddependencies untouched; jobs2,
existingccache/CMakeobjects retained. Tinycodeprobe recompiles afternewrealhelper,
worker adds relative-to-dot control besidesnormproductgate. Numericgates unchanged.
Next afterterminalbuild: separateFP64 /FP32unpack /FP32direct coax-tiny W.1 with
samebuild/reference/RIGHTpc, wholefields/residual/TEM checks before largercase.
Exactargv sequential:
`python3 tools/experiments/mixed_basis_probe.py build`.
`python3 tools/experiments/mixed_basis_probe.py run artifacts/m3-mixed-basis-cuda-v2-20261019 --seconds 60`.
`python3 tools/dev.py build --jobs 2` (onlyifprobeexecution/arithmeticPASS).

EXP78 allterminalPASS. Probe refreshedrecipe afterrealhelper and extra relative
dotcheck, complexdata allPASS; nativePalacebuild227.712s, installeddependencies
unchanged. Corevectorheader change invalidatedsolverTUs: ccache9hits/329misses,
83buildsteps. NofullMFEM/hypre rebuild. Subsequentimplementation.cpp-only edits
should use retainedobjects; don't deletecaches. Native libpalaceSHA3893de4b66aa9543
6f98958a9057df3f5a61b27c2dd5efdc292c8cee9be12b41. BuildsuccessNOTnumericalPASS.

### EXP79 — prerejestracja: actual Palace coax-tiny three storage paths

Samecurrentnativebuild/mesh/physics, RIGHTpc, defaultFP64operators/factors,
onecoaxdiagnostic3.55GHz, explicitTEMvolumeL2 andsavedfullfields. BaselineFP64,
existingFP32unpack, thennewFP32direct; bothcandidatesreferenceidenticalFP64fields.
No nativecomplexcoarse combination yet (existingrunnerguardFP64onlypreserved).
SamefrozenK field/raw/TEM/S gates; compare actualmarkers/directflag plus residual
and wholefields, not justexecution. Threecheap<=60sruns, localGPU/noappsclose,
existingRAM/VRAMonlyrunnercaps. These are W.2tinyfilters; W.1orthogonality/realpath
and largerW.2/W.3 stillpending, no speedup/promotion fromtiny alone.
Exactargvs sequential (next onlyafterprevious terminalexecutionPASS):
`python3 tools/dev.py run coax-tiny artifacts/m3-coax-tiny-fp64-20261019 --basis fp64 --pc-side right --coax-l2 --save-fields --memory-marks --phase-trace --seconds 60`.
`python3 tools/dev.py run coax-tiny artifacts/m3-coax-tiny-fp32-unpack-20261019 --basis fp32 --pc-side right --coax-l2 --save-fields --field-reference artifacts/m3-coax-tiny-fp64-20261019 --memory-marks --phase-trace --seconds 60`.
`python3 tools/dev.py run coax-tiny artifacts/m3-coax-tiny-fp32-direct-20261019 --basis fp32 --direct-basis --pc-side right --coax-l2 --save-fields --field-reference artifacts/m3-coax-tiny-fp64-20261019 --memory-marks --phase-trace --seconds 60`.

EXP79 three terminalexit0/noOOM, rootverifiedsamecurrentnativeSHA/config/fields
and rawmarkers. FP64/unpack/direct62/64iter, maxraw9.026e-7/9.045e-7/9.042e-7.
DirectfieldE/B7.528e-7/1.004e-8,ΔS3.412e-9,ΔVSWR6.751e-9,Δportpower6.823e-9.
TEMq4/6PASS~.4953%E/.4558%B. Times18.714/18.723/18.709s, no speedupclaim.
Cgroup610.3/589.8/595.1MB; GPUprocess4.658/4.658/4.687GB, no GPUpeakreduction.
Rootanalysis artifacts/m3-coax-tiny-root-analysis-20261019.json.
Docs mixed-basis/ARCH/INDEX/PLAN/M3/testing updated. M3stillACTIVE; W.1actual
orthogonality/realpath/faultdetector and largerW.2/W.3pending. No promotion.

Finalvalidation EXP77–79:106unitPASS pinned/system90PASS16SKIP. SameLuna
read-only docs-gardenPASS, no scope/source/metric contradictions. Checker and
diffcheckPASS. Rootreview numerical receipts/rootanalysis/currentnative match.
M3ACTIVE; commitlocalonly, no publicpush/defaultpromotion/goalcompletion.

### EXP80 — prerejestracja: actual exported Palace vector API / MGS CPU + CUDA

Previous turn progress cb40b75: complexcoax-tiny/raw/TEM/S/fieldPASS; W.1real/
orthogonality/faultdetector pending. New oneTU probe links verified libpalace.so
StoredBasisVector methods (not copiedCUDAkernels); native/sourceSHA pinned.
No Palace/dependency rebuild, cachedmpicxx/link max120s, repeat expectsno-op.
CPU andCUDA separate one-rankprocesses, vectors n0/1/1009/65537/131071, floatdata
owned independently: originalsource overwritten afterPack while savedUnpack
reference retained. Compare directDot/AddTo vs legacyFP64Dot/Add on samequantized
data; scaled+relative dot/axpy gates1e-12. Complexn1: expected31-i, deliberately
wrong31+i must exceed gate. Real/complexMGS16vectors4097DOF, storedGram/normalized
orthog<2e-7, directvslegacy normalizedvector<1e-12. No near-dependentbasis or
multi-rank guarantee. SameFP32storage/FP64arithmetic/reduction, noTCclaim.
Runtime6GiB4CPU/noSwap/RAMtmpfs512MiBeach/networknone,60s each; CUDA initial
HYPREUmpirepool256MiB via existingpublicAPI; no appsclose/paidcompute. No solver
performancepromotion from APIprobe. 109systemtests93PASS16SKIP.
Exactargvs sequential, nextonlyafterprior terminalPASS:
`python3 tools/experiments/stored_basis_probe.py build`.
`python3 tools/experiments/stored_basis_probe.py build` (cache).
`python3 tools/experiments/stored_basis_probe.py run artifacts/m3-stored-api-cpu-20261019 --device cpu --seconds 60`.
`python3 tools/experiments/stored_basis_probe.py run artifacts/m3-stored-api-cuda-20261019 --device cuda --seconds 60`.

EXP80 stopped atbuildlinkexit1 after7.385s, no numericalrun. CPPcompile passed;
GPU-built libceed requires libcuda.so.1 missing in driverlessbuilder. Unresolved
cu* fromlibceed; not arithmeticfailure. No retries/limits/dependencychanges.

### EXP81 — prerejestracja: link-time driver stub, real runtime driver

Onlylink/provisionfix: explicitCUDAtoolkit driverstub -lcuda atbuildtime,
--no-as-needed; NEVER stubrpath. Runtime CDI realNVIDIAdriver injected forboth
CPU andCUDA processes, like existingPalaceCPUreference runner. CPU still uses
mfem::Device(cpu)/HYPREhostarithmetic, not GPUtiming. CUDA256MiBpoolunchanged.
Same oneTU/cache, exactEXP80inputs/gates/caps/deadlines, noPalacerebuild.
Exactargvs same four asEXP80, samefreshartifactpaths (no numericalrun existed).
Nextonlyafterprior terminalPASS; no autosourcefix/retry delegated.

EXP81 allterminalPASS/rootverifiedsource/native/binary/state. ActualprobeSHA
3fae204af9c819e6a5da3b1b35860d752469418e836e772b421bf5c51dc6d5d9; Luna first
message accidentallyquoted earlierstandaloneCUDAreceipt, rootusesactualmanifest.
Build1.494s/cacherepeatno-op, noPalace/depsrebuild. CPU/CUDA10/10realcomplex
casesPASS, includingzero,sourceoverwrite,complex31-i vswrong31+i detector.
Maxreldot CPU1.09e-13/CUDA2.17e-14, axpy0 vslegacy. MGSGram max2.724e-9,
orth max6.309e-11, normalizedvectorΔCPU<=2.475e-16/CUDA<=9.015e-17. AllgatesPASS.
CPU .191s/RSS308809728B;CUDA .595s/RSS511172608B/pool256MiB. One-rankwell-
conditionedMGSonly, no near-dependent/distributed claim. Rootanalysis stored
artifacts/m3-stored-api-root-analysis-20261019.json. W.1currenttargetscopePASS.

### EXP82 — prerejestracja: coax-medium native coarse + direct FP32, full sweep

NextW.2samefrozenmediummesh/Order/physics, 3.3/3.55/3.8GHz bothports, RIGHTpc,
tol1e-6/restart240. Newexplicit --coax-sweep preservesexistingfixturefrequencies
while enablingTEMq4/q6/probes instead of silentlysingle3.55GHz. DefaultoldCLI
unchanged. Nativecomplexcoarse uses sameFP64factor/operator forbothvariants;
newcombinednativecoarse+FP32allowed ONLYexplicitdirectflag (oldunpackstillguarded),
pendingthisqualification. No factorprecisionchange/shiftedmatrix; modelunchanged.
FP64reference vsFP32direct: samecurrentnative, fullfields/S/raw/TEM withfrozenK.
180s each, localRAM/VRAMonly/no paidcompute/appsclose, caches/fallbackpreserved.
No nativeCPU/Qpoolcombination; nsys remainsFP64only. No promotion onexecution.
111systemtests95PASS16SKIP. Exactargvs sequential nextafterterminalPASS:
`python3 tools/dev.py run coax-medium artifacts/m3-coax-medium-native-fp64-20261019 --basis fp64 --native-complex-coarse --pc-side right --coax-l2 --coax-sweep --save-fields --memory-marks --phase-trace --seconds 180`.
`python3 tools/dev.py run coax-medium artifacts/m3-coax-medium-native-fp32-direct-20261019 --basis fp32 --direct-basis --native-complex-coarse --pc-side right --coax-l2 --coax-sweep --save-fields --field-reference artifacts/m3-coax-medium-native-fp64-20261019 --memory-marks --phase-trace --seconds 180`.

EXP82 referenceTIMEOUT authoritative terminalRunningFalse/ExitCode-1/noOOM,
runnerexit255/181.026s;4/6solves, no candidate. Nativecoarse WASapplied (four
dimension155934/nnz2466144 complexFP64markers); resultboolFalse meansnotall6
requiredmarkers, not ignoredflag. Incompletepostprocessing/memorymarks expected,
no promotion. TEMq4~13.7s +q6~23.2s PERsolve: sixchecks alone~222s>180limit,
so unchangedretry cannotfinish. Fourrawchecks<1e-6 not fullqualification.

### EXP83 — prerejestracja: bounded frequency shards, same full W.2 quality

Keep180s/run; split existing3.3/3.55/3.8GHz into onefrequency/twoportjobs.
New --coax-frequency selects ONLYexistingfrozenfixturepoint, preservesmesh/
boundaries/ports/physics/tol/restart and allTEMq4/q6/wholefields/Schecks. Mutually
exclusivewith --coax-sweep; no weakerquadrature or omittedport. Same nativeFP64
coarse forFP64ref andexplicitFP32direct. Reference/candidate grouped perfrequency,
allthreepairsmustPASS before W.2 fullsweepqualification. No Palacerebuild.
Rootfirstreviews3.3pair beforequeueingremaining. 112systemtests96PASS16SKIP.
For each pair F in [3.3,3.55,3.8], tag in [330,355,380], exactcommands:
`python3 tools/dev.py run coax-medium artifacts/m3-coax-medium-native-fp64-F-20261019 --basis fp64 --native-complex-coarse --pc-side right --coax-l2 --coax-frequency F --save-fields --memory-marks --phase-trace --seconds 180`.
`python3 tools/dev.py run coax-medium artifacts/m3-coax-medium-native-direct-F-20261019 --basis fp32 --direct-basis --native-complex-coarse --pc-side right --coax-l2 --coax-frequency F --save-fields --field-reference artifacts/m3-coax-medium-native-fp64-F-20261019 --memory-marks --phase-trace --seconds 180`.
Paths replace F by tag (argvfrequency numericF). No autosourcechanges/retries;
nextonlyafterprior authoritative terminalexecutionPASS, root ownsanalysis.

EXP83 firstpair3.3GHzterminalPASS, samecurrentnative/coaxmesh/config,45/47iter
each, reference114.311s/candidate115.312s. Candidate maxraw8.335e-7, E/BΔ
7.554e-7/8.503e-9, TEMq4/6~.4937%E/.4558%B PASS. Nativecoarsemarkers2each,
candidateDIRECTtrue. RootverifiedS/native/state andmemoryphase intervals;
rootanalysis artifacts/m3-coax-medium-330-root-analysis-20261019.json.
Allocationmetricmanagedpeak4.7996→4.2176GB(~12.1%lower); GMRESphase4.429/3.297s
vs4.390/3.316s. This is NOTphysicalRAM/VRAM reduction: cgroup2.758→2.924GB,
GPUprocess4.660→4.689GB. No speedupclaim, other2frequenciesstillpending.
Next exactremainingEXP83pairs355/380, sameflags/caps/gates; rootreviewedfirstpair.

EXP83 all6shards terminalPASS, full W.2 threefreq/bothports/raw/TEMq4q6/fields/S
covered. All45/47iter; candidateEΔ<=7.554e-7/B<=8.503e-9, raw<=8.335e-7.
Rootanalysis artifacts/m3-coax-medium-sweep-root-analysis-20261019.json includes
allstates/fields/complexS/VSWR/portpower andallocationmetrics. Allocationpeak
same12.126%lower allfreq; physicalcgroup/GPUpeaksNOTimproved. Runs114.3sFP64,
115.3/116.4/115.3sFP32direct: no speedup. Geometry/Order/restart240 preserved;
full3freqsinglejobEXP82 remainsTIMEOUT, not rewritten asPASS.

### EXP84 — prerejestracja W.3: fresh samebuild FP64 reference, one medium antenna

W.1actualAPI/MGS andW.2fullsweep PASS justify bounded W.3. Same frozen3.50GHz/P2,
Order2/PA, mesh/ec56c9a7..., nativecomplexFP64coarse, RIGHTpc, explicitK64 to
match qualifiedM1profile, tol1e-6, hyprepool256MiB, releasebasis/finalsolver.
Both futurevariants must use SAME savedinitialapproximation fromcompleted
m1-antenna-resident-fp64-20261018 (startingguess only, not accuracyreference).
FreshFP64 checked against independentlytighter nativecoarse r2raw7.28e-10;
root preflight verifiedinput/reference/source/geometry hashes beforelaunch.
Candidate later referencesfreshFP64 plusfrozenK. No profilers/phase-trace,
no input/mesh/highquality changes. Existingfullrun1800s/60GiB/noswap/hostguard6GiB,
no paidcompute/appsclose, source/build/inputcache retained. Not a coldstart
benchmark; samewarmguess asM1profile, disclosure retained in commandmanifest.
Currentnative unchanged fromEXP78; no rebuild needed. Firstreference only:
`python3 tools/dev.py run tshaped-medium artifacts/m3-antenna-native-fp64-20261019 --basis fp64 --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --save-fields --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m1-native-complex-coarse-antenna-tight-r2-20261018 --seconds 1800`.
Rootreviewterminalquality before preparingcandidateexactargv; no auto retry.

EXP84 terminalPASS/rootverifiedstate/currentnative/freshfieldreferencebytes.
35iter, rawRHS8.35543e-7, E/Bvsindependenttight6.9955e-8/9.8852e-8, sevenentries.
Elapsed414.164s; cgroup58889510912B, managedpeak55147611962B, cuDSS25008217684B.
GPUprocesscounter2147483648B (doesnotmeasureallUVMresidency); minhostavailable
17846087680B>6GiBguard. Initialguess/nativecoarse/release/memoryflags confirmed.
No claim speedupfrom414vsolder447; background/cache/time differ. Freshreference
nowqualified forsamebuildcandidatecomparison, notcoldstartbenchmark.

### EXP85 — prerejestracja: FP32direct W.3 matched fresh reference

Onlybasisrepresentation/operations change vsEXP84: FP32DIRECT, allFP64operator/
factor/reduction/residual, samefrozenmesh/port/freq/order/warmguess/K64/tol1e-6/
pool256MiB/releaseflags. ReferencefreshEXP84 plusitsindependenttightcontrol.
Compare actualraw,wholefields,S/Z/VSWR,energy/portpower,allocation/cgroup/time;
no newtrace/profiler, no deadline/capchange, no environment/app intervention.
Rawguard1e-6 and frozenK fields1%/ΔS1e-3/VSWR.01/power1e-3; fallbackretained.
Rootverifiedfreshreferenceinput beforelaunch; sameoneGPU/local/no paidcompute.
Exactargv:
`python3 tools/dev.py run tshaped-medium artifacts/m3-antenna-native-direct-20261019 --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --save-fields --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m3-antenna-native-fp64-20261019 --seconds 1800`.

EXP85 terminalPASS, rootverifiedsamecurrentnative/state/raw/wholefields/S/energy.
35iter/no restart, rawRHS8.35625e-7, maxΔE/B1.1323e-8/1.5949e-9. ΔS3.447e-10,
ΔVSWRP2 6.777e-10,Δportpower5.123e-11,Δenergy1.388e-9 allfrozenKPASS.
Cgroup58889510912→56018751488B (−2870759424B/~4.87%); managed55147611962→
52276667194B (−2870944768B/~5.21%). cuDSSsame25008217684B. GPUprocesscounter
2147483648→2176843776B excludesfullUVMresidency, not VRAMreductionproof.
Time414.164→409.715s onlyonepair, no statisticallyestablishedspeedup.
Allocationowner model:36materializedFP64vectors vs36packed+2FP64workvectors+
1MiBpartials predicts EXACTmanagedpeakdelta;45logicalVcapacity includesuntouched
device allocations, don't calllogicalbytesphysical. Rootanalysis complete in
artifacts/m3-antenna-root-analysis-20261019.json. Goalusefulmemorygain observed
but NOTcomplete: M3policy test, M4/M5/M6/M7/finalqualification stillrequired.
Docs mixed-basis-validation, PLAN/M3/INDEX/ARCH/testing updated; M3ACTIVE.

Finalvalidation EXP80–85:112unitPASS pinned; system96PASS/16SKIP. SameLuna
read-only docs-gardenPASS, source/metric/scope reviewed incl actualprobe receipt,
EXP82FAIL retained, W2shards andsamebuildwarmW3, no falseVRAM/speed/defaultclaim.
Checker/diffcheckPASS; rootanalysis matches currentnative andterminalstates.
M3ACTIVE/policyexperiment next; M4–M7pending. Localcommit only/no push.

## EXP86 — opt-in managed basis prefetch (preregistered, 2026-10-19)
M3 active. Hypothesis: prefetch only FP32direct Dot sources before MFEM
stream0 kernels may reduce demand faults; may also evict PC pages and lose.
No CPU preferred/readmostly advice, no extra sync, no physics/restart change.
Strict managed-pointer/concurrentManagedAccess checks; CUDA errors fail.
Log request counts/bytes, never call them measured transfers/residency.
Primary source CUDA12.9 Runtime API memory cudaMemPrefetchAsync, accessed
2026-10-19: https://docs.nvidia.com/cuda/archive/12.9.0/cuda-runtime-api/group__CUDART__MEMORY.html
Installed MFEM forall.hpp:598 default kernel stream, cuda.hpp:28 stream0 sync.
Current qualified native+manifest preserved build/m3-basis/pre-prefetch-native.
Incremental build only; no dependency rebuild. First filter samebuild coax-tiny
FP32direct RIGHT,3.55GHz/bothports/TEM/fields,60s. Compare raw<=1e-6, fields1%,
S1e-3/VSWR.01/power1e-3 and positive prefetch markers per solve.
If pass, matched W.3 no-prefetch/prefetch warmstart K64/nativecoarse/pool256,
1800s/60GiB/no swap/hostguard6GiB; root analyzes total time/memory/quality.
Do not promote speedup from requested bytes or a single small run.

EXP86 tiny terminalPASS/rootverified: samebuild/config,62/64iter,raw<=9.045e-7.
MaxΔS9.132e-10/ΔVSWR9.707e-10; fields within1%; exact rootmetrics in
artifacts/m3-prefetch-tiny-root-analysis-20261019.json. Prefetch requests
3906+4160 (1.392+1.482GB requested, not migrated). 19.661/18.699s onepair
smallcase not speedup evidence. Build13.846s/5steps only Palace, cache counts
cumulative; dependencies untouched. Proceed matched W.3 per preregistration.
Exact tiny argv: common `python3 tools/dev.py run coax-tiny <output> --basis fp32 --direct-basis --pc-side right --coax-l2 --save-fields --field-reference <ref> --memory-marks --phase-trace --seconds 60`; control output=m3-prefetch-tiny-control-20261019/reference=m3-coax-tiny-fp64-20261019; candidate output=m3-prefetch-tiny-on-20261019/reference=control plus --basis-prefetch (all artifacts/).

EXP86 W.3 control terminalPASS/rootverified:408.622s/35iter/raw8.35621e-7,
all7fieldregionsPASS vs qualified FP32direct, E7.238e-9/B5.086e-10. Cgroup
56025440256B. No prefetch marker. Samebuild candidate now uses this reference.
Control exactargv: `python3 tools/dev.py run tshaped-medium artifacts/m3-prefetch-antenna-control-20261019 --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --save-fields --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m3-antenna-native-direct-20261019 --seconds 1800`.
Candidate changes output=m3-prefetch-antenna-on-20261019/reference=control
and adds --basis-prefetch; all other args identical.

EXP86 W3 candidate terminalPASS/rootverified, samebuild/config,35iter,
raw8.35655e-7, maxfieldE7.489e-9/B4.233e-10. Native coarse/prefetch applied.
Cgroup56025440256→56021962752B (effectivelysame), managedsame52276667194B,
cuDSSsame25008217684B. Marker1260requests/56542368960requestedB consistent
with35*36complexpartreads*11218724*4; NOT measured migrations. Whole run
408.622→396.526s (~3% onepair), NOT statistically established speedup.
Full frozenKmetrics: artifacts/m3-prefetch-antenna-root-analysis-20261019.json.

## EXP87 — measured late GMRES UVM movement (preregistered, 2026-10-19)
Extend existing diagnostic-only Nsight runner to explicit FP32direct (including
prefetch); no RF qualification in partial profile. No C++/native change.
Samebuild W3/control+prefetch, window30:2 (latebasis), samewarmstart/K64/
nativecomplexcoarse/pool256. Count actual Nsight copy enums/bytes periteration,
phase times inclusive, no sum of overlappingcopy/kernel times. Capture excludes
RF fields and stopscleanly afterwindow; timeout1800/60GiB/no swap/guard6GiB.
Temporary profiler output RAM /dev/shm; saved bounded report is diagnostic output,
not solver disk scratch. Retain profilerwarnings/clockcoverage failure as failure.
Exact commonargv: `python3 tools/dev.py run tshaped-medium <output> --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --nsys-window 30:2 --seconds 1800`. Outputs artifacts/m3-prefetch-profile-{control,on}-20261019; on adds --basis-prefetch.

EXP87 FAIL: full-process late-window collector exceeded60GiB cgroup, exit137/
OOMKilled true,456.588s, peak64424509440B. Profilecompletefalse/clockfalse/
CUDAeventlosswarning; no transfer or phase metrics accepted. No retry/capraise.
NormalEXP86 W3 passed; this failure is diagnostic collector memory pressure.

## EXP88 — bounded selected-window collection (preregistered, 2026-10-19)
Fix diagnostic collection instead of raising memory limit: cudaProfilerStart/
Stop around existing selectediterations, nsys --capture-range=cudaProfilerApi
--capture-range-end=stop; process still exits via clean diagnostic exception.
Start after draining earlier kernels, then retain all3clock syncanchors for2iter.
CUDA profiler API only in adapter/weak hook, opt-in PALACE_PROFILE_CAPTURE_RANGE.
No ordinary run math/precision/allocationpolicy change; fallback native+manifest
build/m3-basis/pre-selective-profile-native. CUDA12.9 profiler and Nsight
2026.5.1 pinned primary guidance, accessed2026-10-19:
https://docs.nvidia.com/nsight-systems/UserGuide/index.html
First smoke coax-tiny window0:2 <=60s, both diagnostic control andprefetch if
needed. Require cleanstop/clock/coverage/no collectorwarnings, not RFpass.
Then rerun late30:2 W3 diagnostic pair at same1800s/60GiB/no swap cap (new
artifacts m3-selective-profile-{control,on}-20261019, exactEXP87argv).
Add captureflag onlyprofiling runner/unsetforordinary, counters marker begin/end.

EXP88 firsttiny FAIL as completeprofile:10.422s/exit0/1.832GBcgroup, all
clock/window/cleanstop/coveragePASS but DIAGNOSTIC_EVENT severity2 'Not all
CUDA events might have been collected.' No totals accepted. Primary NVIDIA
engineer explains same2026.5.1 forcedflush-warning case (not proof forours):
https://forums.developer.nvidia.com/t/nsight-systems-2026-5-1-produced-112-collected-100-warning-despite-complete-coverage-of-32-kernels/384749
Nexttiny diagnostic changes only --capture-range-end=none: capture starts at
selectedwindow but collection ends at natural cleanprocess exit, so capture
includes boundedcleanup; window remains offlinefiltered. Keep warninggate
unchanged, no largecase untilwarningfree. No native rebuild for CLI-onlychange.

EXP88 tinyv2 PASS/rootverified: profilecomplete true, capture/window/clock/
coverage/cleanstop true, zero collectorwarnings. Naturalexitaftercapture-start
fixeswarningwithoutgateweakening. 8.423s/1.397GBcgroup. Partial diagnostic
resultcompletefalse deliberate, not RFpass. Proceedlate W3 pair withsame
newnative andsameparams asEXP87, only boundedcapture policy changed.

EXP88 latecontrol terminalPASS/profileonly rootverified:383.343s/57.623GB
cgroup, profilecomplete true/zerowarnings/allclockcoveragePASS. Twoiter late
window15.192s,PC13.567s inclusive/coarse4.869s included,orthog.706s.
Measured UVM HtoD10.900GBfault+126.512GBspeculative/DToH137.320GBeviction;
actualenum mapping retainedinreport, not requestedbytes. Candidate sameargv
except artifacts/m3-selective-profile-on-20261019 and --basis-prefetch.

EXP88 latecandidate terminalPASS/profileonly rootverified:381.014s/57.571GB
cgroup, samebuild/config, profilecomplete/clockcoverage/cleanstopPASS,
zerowarnings. Selected2iter14.761s vs15.192; orthog.330 vs.706s,PC13.505
vs13.567s (coarse4.879 vs4.869included). ActualUVM total272.984 vs274.732GB,
−0.6363%, periter136.492 vs137.366GB; no claimalltransfersareblocking.
Explicit HtoDprefetch5.654GB, fault9.982GB/speculative121.123GB/DToHeviction
136.224GB; numericenumlabels retained in artifacts/m3-prefetch-profile-root-analysis-20261019.json.
Decision: useful localorthogimprovement, not cure forPC residency; prefetch
remainsopt-in, no whole-solve speeduppromotion fromonepair. FP32directmemory
gainEXP85 remains primaryqualifiedbenefit. Restart120vs240 notrun:35iter<K64,
so neither reduces materializedbasis; below35 changes convergence/cost for
limitedsaving; no evidence tospendrun onthat now. M3.2 policy assessmentdone.

## EXP89 — final M3 W.2 prefetch quality regression (preregistered, 2026-10-19)
Newnative EXP88 no ordinaryphysicschange. Threeexistingmediumcoaxfrequency
shards3.3/3.55/3.8GHz,bothports,180s each, nativecomplexcoarseFP64/RIGHT;
FP32direct+prefetch vs independentqualifiedEXP83 FP64 fields (samefrozenmesh).
No new speedclaim fromdifferentbuildreference. Need raw<=1e-6/wholefields1%,
ΔS1e-3/VSWR.01/power1e-3, allTEMq4/q6,positiveprefetch/native markers.
Exact commonargv: `python3 tools/dev.py run coax-medium <output> --basis fp32 --direct-basis --basis-prefetch --native-complex-coarse --pc-side right --coax-l2 --coax-frequency <f> --save-fields --field-reference <ref> --memory-marks --phase-trace --seconds 180`.
Outputs artifacts/m3-prefetch-medium-{330,355,380}-20261019; references
artifacts/m3-coax-medium-native-fp64-{330,355,380}-20261019. Standardnoswap
60GiB/6GiBhostguard, no dependencybuild/paidcompute. StoponfirstFAIL.

EXP89 terminalPASS all3shards/bothports/45,47iter/raw<=8.334e-7,wholefields
E<=7.555e-7/B<=9.423e-9. Allq4/q6TEM records E<.495%/B<.457%. Native
andprefetchmarkersapplied; rootRFdeltas qualification pending analysisreceipt.
115unitPASS pinned/system99PASS16SKIP.

## EXP90 — integrated W.3 quality after diagnostic hook change (preregistered)
EXP86 W3 used immediateprecedingnative; EXP88 onlyadds inactive diagnostic
hook toordinarypath. Still rerun fullW3 oncurrentnative toprove integrated
quality; no needrepeatbuild. Samephysics/warmstart/K64/pool256/nativecoarse.
Exactargv: `python3 tools/dev.py run tshaped-medium artifacts/m3-prefetch-antenna-final-20261019 --basis fp32 --direct-basis --basis-prefetch --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --memory-marks --release-gmres-basis --release-final-solver --save-fields --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --field-reference artifacts/m3-prefetch-antenna-control-20261019 --seconds 1800`.
Same60GiB/noswap/6GiBhostguard; field/raw/S/VSWR/power frozenK, memory
expected same compressedbasis; speed statisticalqualification deferredtoM7.

EXP90 terminalPASS/rootverifiedcurrentnative:35iter/399.446s/raw8.35668e-7,
wholeE/B6.684e-9/4.860e-10,ΔS2.946e-10/ΔVSWR2.865e-10/power3.076e-11.
Currentnative matches allEXP89shards andEXP90, no activeprofileflags inW3.
EXP89 RFmaxΔS5.666e-9/ΔVSWR4.794e-9/totalportpower1.077e-8, allTEMPASS.
Rootreceipt artifacts/m3-prefetch-final-root-analysis-20261019.json. NoW4/W5
claim. Nextrelink existingactualAPIprobe againstcurrentnative CPU/CUDA,
6GiB/4CPU/noswap/RAMtmpfs512MiBeach/60s perrun, using existingtool.

EXP90 actualAPI relink currentnative CPU/CUDA PASS/all10rows+realcomplexMGS,
ownership/conjugationdetectorsPASS, FP64accum/quantization gates unchanged.
No managedprefetch flag inAPIprobe; actualprefetch qualifies viaEXP86/89/90.
M3.1–M3.3 assessment complete: usefulmemorygain, policybytes measured;
optionalprefetchkept/no globaldefaults/speedpromotion; restartconditionalnotrun
justified. W4/W5 and allM4–M7 remain. ActiveM4 sourceaudit setupreuse next.
New report docs/basis-prefetch.md and M4 checkpoint; finaldocsreview pending.

FinalEXP86–90 validation:115pinnedPASS/system99PASS16SKIP;8shellPASS,
docschecker/diffcheckPASS. SameLuna read-onlydocs-garden foundstaleM3ACTIVE
line in mixed-basis-validation; rootcorrected. Rootreviewedcode+currentnative
receipts andstrict profile enumtotals; no gateweakening, no SSDoffload/default
change. M3completeassessment/M4ACTIVE. Next sourceaudit existingdrivenloop/
SetOperator/factorizationcounts before writingcache. GlobalgoalNOTcomplete:
M4–M7/W4/W5/finalreproduciblequalification remain. Localcommitonly/no push.

## EXP91 — one-frequency port setup reuse (preregistered, 2026-10-19)
M4 sourceaudit: drivensolver.cpp SweepUniform outerexcitation/innerfrequency
reassembles A2/A/P and calls kspSetOperators perRHS. Nativecomplexcoarse
SetOperator clearsanalysis/factors everycall. EXP89 2nativecoarsemarkers per
singlefrequency confirms2factorizations. LumpedPort AddDamping loopsallactive
ports irrespectiveexcitation; AddExcitation filtersidx onlyRHS. A2/A/P depend
onfrequency/materials/mesh/boundaries, notexcitationidx. Restrictprototype to
singlefrequency/fixedmesh/oneMPIrank/multipleLPexcitations/noWave/Floquet.
Keep same A2/A/P ownership throughlastsolve; no multfreqfactorcache/reordering.
Runtime --port-setup-reuse opt-in, --setup-audit for control/candidate.
Audit records driverbuild/reuse, native CSRfnv1a64 structure/values fingerprints
(notcryptographicproof) and synchronizedanalysis/factor times. Noextra
workingcopy/cache ofmatrices, no SSD/swap, preserveglobaldefault. Native+manifest
fallback build/m4-reuse/pre-m4-native. Buildcached onlychangedPalaceTUs.
First samebuild tinycoax3.55GHz/bothports/fields/TEM/right FP32direct/nativecoarse
matchedcontrol/reuse,60s. Require raw1e-6,wholefields1%/S1e-3/VSWR.01/power1e-3,
onebuild+onereuse marker and1nativefactor vs2control, samebaselineCSRhashes.
Ifpass W2 threefrequencyshards180s each and justifiedbothportsantennaW3
withunchangedmesh/terminations, notdeclareantennaspeed fromcoaxonly.
Symbolicreuse decisionseparate fromnumericreuse basedmeasuredanalysiscost.

EXP91 buildPASS15.611s/5steps, no dependencyrebuild. FournewunitguardsPASS
(37devtests total); typo ininitialunithelpername corrected beforebuild.
Tinycommon exactargv: `python3 tools/dev.py run coax-tiny <output> --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --setup-audit --coax-l2 --save-fields --memory-marks --release-gmres-basis --release-final-solver --field-reference <ref> --seconds 60`.
Control artifacts/m4-reuse-tiny-control-20261019/ref artifacts/m3-coax-tiny-fp64-20261019;
candidate artifacts/m4-reuse-tiny-on-20261019/ref control, adds --port-setup-reuse.

EXP91 terminalPASS/rootfrozenKPASS, samebuild/config39/42iter, raw<=9.601e-7.
2build/2nativefactors control vs1build/1reuse/1nativefactor candidate. Control's
twoCSRstructure+valuefingerprints identical. Cross-process candidatevaluehash
differs; do NOT claimbitwise CSRreproducibility acrossprocesses. Fingerprints
are diagnostic identity ofbaselineportsetups, notqualitynorm. Frozenquality
usesactualraw/S/VSWR/power/wholefields; receipt m4-reuse-tiny-root-analysis.
18.623→17.755s onepair tiny, noantenna/statisticalspeedclaim. Peak629→593MB.
Proceed W2: currentnative/bothports3pointshards withsameparams; first355control
then355reuse and330/380reuse vsqualifiedFP64refs. No otheralgorithmchange.
Exactcommonargv: `python3 tools/dev.py run coax-medium <output> --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --setup-audit --coax-l2 --coax-frequency <f> --save-fields --memory-marks --release-gmres-basis --release-final-solver --field-reference <ref> --seconds 180`.
Control355 output artifacts/m4-reuse-medium-control-355-20261019/ref artifacts/m3-coax-medium-native-fp64-355-20261019; reuse output artifacts/m4-reuse-medium-on-{355,330,380}-20261019 adds --port-setup-reuse,355ref currentcontrol/others respectiveEXP83FP64.

EXP91 W2 all4runs terminalPASS, rootreceiptpending:45/47iter/raw<8.34e-7,
fields/TEM/auditPASS. 355control115.196s vsreuse110.150s,2→1factor. Independent
330/380refsPASS. BaselinecontrolportCSRfingerprintsidentical; not crossprocess
bitwise claim. Analysis1.1–1.3s/factorhot1.14s inW2, initialJITfactor8.4s.

## EXP92 — bounded both-port antenna study with explicit partial seed
Historicalcold M1 oneport151iter/1090–1384s; two coldports likelyexceed1800s.
Use the SAME existingP2 approximate field seed (m1resident) incontrol/candidate;
P1 remains explicitzero. Thisis initialguessonly, notaccuracyreference. Preserve
strictfullsnapshotvalidation; new --partial-initial-fields explicitly allows
verifiedsourceexcitation subsettarget, requiringidenticalotherphysics/mesh/
dependencies, originalsourceinventory/complete/hash. No fabricatedmergedresults.
Runner passesverifiedexcitationmask; driver zeros unseededRHS withdistinctmarker,
neverreusesprecedingportfield accidentally. Missingseedfiles stillfailbeforelaunch.
No change to strictaccuracyreferencepath. No warmstartspeedclaim/comparison;
setupreuse controlledbyidenticalstarts. Unitguards thenexistingtinyfilter and
W3bothportscontrol/reuse,1800s/60GiB/no swap/6GiBguard. K64/pool256/RIGHT,
FP32direct/nativecoarse, no prefetch. IfcoldP1doesnotfit stopatcap andrecordFAIL,
notraisebudget/altermesh/tolerance. Both-ports flagchangesonlyRHSrequests,
preservesallphysicalportimpedances. W4/W5 remainfinalM7.

EXP92 partialseedunitguardsPASS (39devtests). --excitation selectsoneexisting
physicalLPforseed/shards, neverchanges R/geometry. Beforeheavycase actualtiny
filter: sourceoneP2 (`--excitation 2 --coax-fields --save-fields`), thenbothports
control/reuse withverifiedpartialP2seed andtightertol1e-8 soP2 still exercises
PC. SameK64/nativecoarse/pool256/right, no prefetch;60s each. Rootargv below
are sentexactly tosameLuna. Newbuildonlydrivensolver weakseedbranch, depscached.
Tiny source artifacts/m4-partial-seed-tiny-source-20261019; bothcontrols
artifacts/m4-partial-seed-tiny-{control,on}-20261019, refsqualifiedEXP91tiny
controlthenfreshcontrol; no accuracyclaimedfromsourceexecutionalone.

EXP92 integratedtinybuild9.535s/sourceP2+bothcontrol/reuse PASS, partialmask
zerosP1/loadsP2provenactualmarkers. Tightfiltertol1e-8 requiresreliablerestart
onP1:58/17iters bothvariants, finalchecks<=9.20e-9; failedintermediate
recurrencecheckretained/corrected. Fields+setupauditsPASS. FulltargetP2seed
M1residentpasses strictpartialverify againstcurrenttarget+native (rootchecked).

EXP92 W3 commonexactargv: `python3 tools/dev.py run tshaped-medium <output> --basis fp32 --direct-basis --native-complex-coarse --pc-side right --krylov-size 64 --hypre-pool-mib 256 --setup-audit --both-ports --save-fields --memory-marks --release-gmres-basis --release-final-solver --initial-fields artifacts/m1-antenna-resident-fp64-20261018 --partial-initial-fields --seconds 1800`.
Controloutput artifacts/m4-reuse-antenna-control-20261019. No completebothport
fieldrefexistsyet; controlraw/S/energy/E+Bsaved, P2crosscheckagainstqualified
M3fullfield afterwards, P1qualityscopeexplicitno independenttightfullrefyet.
Candidateoutput artifacts/m4-reuse-antenna-on-20261019, adds --port-setup-reuse
and --field-reference artifacts/m4-reuse-antenna-control-20261019. Guard60GiB/
noswap/host6GiB, stopat1800s. No alteredmesh/physics/tolerance.

EXP92 W3 control FAIL/OOM exit137/550.848s, cgroup64378429440B, hostguard
notcrossed. P1completed44iter/raw7.490e-7 andsavedfields; P2started butnot
complete. DoNOTuseincompletewholejobasaccuracyref ordeclare2RHSqualified.
Peakcauseevidence: managedlive48.686GB afterP1solve→65.177GB duringpostproc;
remainslive, nextPCend64.929GB (peak66.264), thenOOM. No capraise/retryunchanged.

## EXP93 — release domain-energy workspace between solves (preregistered)
Hypothesis: persistent DomainPostOperator mass/energyworkspace causes betweenRHS
pressure. Add explicit opt-in release afterallmeasurements/fielddiagnostics/
AddEstimate, rebuildsameoperators onlyafter nextGMRES. Preservemeasurementcache,
primaryE/B, CSV/fields andphysicaldefinitions; no visualization writes/AMR for
thispilot. Neverholdtwoenergyoperators while rebuilding. Same releasepolicy
inreusecontrol/candidate isolates setupreuse; measuremarker livebytesdrop.
MinimalPostOperator resetAPI; no newdeps/diskcache/floatingtypechange.
Tinycontrol+policy pairedagainstlastqualifiedEXP92 samephysicalfields then
mediumsinglefrequency/bothports,180s; onlythenbothportantenna control+reuse
at1800s/60GiB/noswap/guard6GiB andsameverifiedpartialseed. Ifmemorydropnot
observed orqualityfail, keepFAIL andinvestigate, notrelaxgates.

EXP93 initialvalidation40devtestsPASS. Tiny commonexactargv: `python3 tools/dev.py run coax-tiny <output> --basis fp32 --direct-basis --native-complex-coarse --port-setup-reuse --setup-audit --pc-side right --krylov-size 64 --hypre-pool-mib 256 --coax-l2 --save-fields --memory-marks --release-gmres-basis --release-final-solver --field-reference <ref> --seconds 60`.
Control artifacts/m4-energy-tiny-control-20261019/ref artifacts/m4-reuse-tiny-on-20261019.
Candidate artifacts/m4-energy-tiny-on-20261019/ref currentcontrol adds
--release-postprocess-energy. CheckenergyCSVaswellasraw/S/wholefields/TEM;
markers releaseP1 andrebuiltP2 eachonce, measuredlivebytesdrop. No dualoperator
copies (resetemptyfirst, replacementconstructedonlybeforelaterpostproc).

EXP93 tinyterminalPASS/rootverifiedsamebuild/config39/42iter/raw<9.601e-7,
fields/audit/release+rebuildPASS; maxrelativeCSVenergy3.483e-9. Managedlive
127.942→91.082MB atrelease thenrebuild127.942MB. Actualdrop36.860MB, not
assumed16GBfullmodel. Build40.273s/12Palacesteps/noexternaldepsrebuild.
Medium355 nowcontrolreleaseonly vsreuse+release, samephysics/K64/pool256.
Common exactargv: `python3 tools/dev.py run coax-medium <output> --basis fp32 --direct-basis --native-complex-coarse --setup-audit --release-postprocess-energy --pc-side right --krylov-size 64 --hypre-pool-mib 256 --coax-l2 --coax-frequency 3.55 --save-fields --memory-marks --release-gmres-basis --release-final-solver --field-reference <ref> --seconds 180`.
Outputs artifacts/m4-energy-medium-{control,on}-20261019; controlref artifacts/m4-reuse-medium-control-355-20261019, onref currentcontrol/add --port-setup-reuse.

### Historyczny research integracji, 2026-10-19 — poza aktywnym zakresem
Poniższe propozycje Rust/SolidCraft/FieldCraft zostały wycofane przez użytkownika;
nie stanowią zadań ani warunków ukończenia aktualnego goal.
Useraskswholegoalstatus, accuracyvspeed, Rust/SolidCraft andalternativeengines.
LateststateEXP93 tinyPASS, mediumpairpreparedNOTLAUNCHED; no palace-run
containers live whenchecked. M4stillACTIVE/WIP; M5–M7 notcomplete.
Primaryresearch: SolidCraftROADMAP Scope(ownerdecision2026-10-07) defers
Simulation; separate tangency-labs/fieldcraft ispureRustCAE forstructures/heat/
LBM, notfoundRFMaxwellbackend. FieldCraft docs/adr/0001-libraries.md requires
permissive/cleanroomdependencies, itsownsolveralgebra; crates/lbm-gpu implements
wgpu/WGSLFP32flow checkedagainstCPU, notantennaEM/cuDSS. Noauthorendorsement
ofPalacefound. Proposedfuturecontribution: Rustanalysis/export/resultadapter
withPalaceasanexternalworker, notimmediatefullrewrite; confirmmaintainerfit.
URLs: https://github.com/tangency-labs/solidcraft/blob/main/ROADMAP.md
https://github.com/tangency-labs/fieldcraft/blob/main/README.md
https://github.com/tangency-labs/fieldcraft/blob/main/docs/adr/0001-libraries.md
https://github.com/tangency-labs/fieldcraft/blob/main/crates/lbm-gpu/src/lib.rs
Alternativeresearch: gprMaxdocumentedCUDAFDTD+ports/S/gain; fdtdzCUDAphotonic
lowlevel, ngsolve.gpu supportsCUDAngscuda (officialcurrentdemoPoisson, notproof
ourRFpipeline). No sameantenna benchmarkagainstPalaceperformed. Consider
boundedreferenceantennaFDTDpilotbeforeanyreplacementclaim; finefeed/slots/CFL
needcostestimate. Sources https://docs.gprmax.com/en/latest/inc_README.html
https://github.com/spinsphotonics/fdtdz
https://docu.ngsolve.org/latest/i-tutorials/unit-5.5-cuda/poisson_cuda.html
RustCUDApossiblevia cudarc(https://github.com/chelsea0x3b/cudarc); language
rewritealone doesnotchangeworking-set/iterations/kernelmath. Goalunchanged;
nextauthorizedrun remainsEXP93mediumfilterthenboundedfullantennapair.

### Aktualizacja planu na prośbę użytkownika, 2026-10-19
Dodano M4.4 lifecycle energii; M5.5 koszt/working-set PC, M5.6 ograniczone
porównanie FDTD/CUDA (zysk jednego szerokopasmowego przebiegu jako hipoteza),
oraz M6.5 fuzja/batching bez wymuszania TC.
Numeracja M0–M7 i ActiveM4 zachowane. Nowe kryteria nie są zaliczone przez
wcześniejsze runy. Rust/FieldCraft/GUI/CAD są poza zakresem obecnego goal.
Zmiany tylko MD; żadne nowe symulacje/buildy nie zostały uruchomione.

Korekta zakresu od użytkownika w tym samym turnie: bez researchu/implementacji
Rust ani FieldCraft. Usunięto proponowane M5.7 przed zatwierdzeniem planu.
M5.5/M5.6/M6.5 służą wyłącznie maksymalnemu przyspieszeniu wiarygodnych
symulacji na aktualnej5070Ti/96GBRAM. IntegracjeCAD/GUI nie są zadaniem.

### Doprecyzowanie polityki SSD przez użytkownika, 2026-10-19
Cache, zwykłe pliki i sporadyczny odczyt SSD dozwolone; niewielkie zapisy
oceniać po pomiarze bajtów/częstotliwości i czasu. Gorące dane solvera RAM/VRAM.
Bez swapowania zadania i intensywnego przepisywania workspace na dysk.
Nie przywrócono disk basis ani nie zmieniono runtime/limitów kontenera.
Historyczne zakwalifikowanie wyników bez zmian. Aktualizacja wyłącznie MD.

### EXP93 wznowienie, 2026-10-20
Poprzedni turn: progress (polityka SSD zapisana w repo). M4 pozostaje aktywny.
Docker był nieaktywny; uruchomiono lokalny daemon, bez przebudowy. RAM available
około77GiB, GPU wolne13,26GiB; aplikacji użytkownika nie zamykano.
Następny test: wcześniej zarejestrowana para coax-medium3,55GHz/bothports,
release-only vsrelease+reuse, identyczny build i polityka pamięci. Limit180s.
Nowe ścieżki artifacts/m4-energy-medium-{control,on}-20261020.

EXP93 medium3,55GHz rootverifiedPASS: samebuild/config/mesh,45/47iterboth,
control109,269s vsreuse102,770s (jedna para, nie statystyczna promocja).
Cgrouppeak3253268480→2665140224B (−588128256B), GPU-processcounterbez
zmiany; nie jest to pomiar całej rezydencji UVM. MaxΔS5,1434e−9,
ΔVSWR5,09994e−9, energyrelative5,8431e−9; wholeE9,4406e−7/B1,1535e−8.
Energyrelease manageddrop355899672B; control2setups, reuse1setup.
Receipt artifacts/m4-energy-medium-root-analysis-20261020.json.

Następny filtr EXP93 fullantenna3,50GHz/bothports: sameFP32direct/nativecoarse,
RIGHT/K64/pool256, releaseenergyinboth/controlvsreuse, rawtolunchanged,
partialinitial source artifacts/m1-antenna-resident-fp64-20261018(P2);
P1explicit zero. Newoutputs artifacts/m4-energy-antenna-{control,on}-20261020.
Limit1800s/60GiB/noswap/hostguard6GiB, no raising cap. Controlmaynotbe
fullindependentaccuracyreference: compareP2toqualifiedreference separately;
candidatefieldreference fullcontrol onlyafterwholejobcomplete. Stoponfailure.

EXP93 fullcontrol PASS execution684,805s,44/35iter/raw7,494e−7/8,357e−7,
peakcgroup60525092864B. Release managed65177433822→49902109334B,
actualdrop15275324488B (agent incorrectly copied medium355899672B; rootcorrected).
ReusecandidateFAIL/OOM137 entering P1 field diagnostics; cgroup64104218624B,
managedlive65177433822B, no P2/wholefieldqualification. Not retried unchanged.
Both share identical solver/postprocess managed phases until comparison begins;
reference field diagnostics add scratch on top of retained25,008GBcuDSS and
15,275GBenergy operators. Wholejobqualitycandidate remainsFAIL.

## EXP94 — defer two-port measurements until solver destruction (2026-10-20)
Hypothesis: avoid overlap of25GBfactors+energy/fielddiagnostics by solving both
RHS before measuring. Cache only first true-DOF complex E in RAM/VRAM
(16*Nbytes; antenna179499584B), compute B later with unchanged Curl/omega.
No solver data on disk, no physics/tolerance/mesh changes; finalsolverdestroyed
before any measurements, original excitation order/energy/fields preserved.
Opt-in --defer-postprocessing; exactlytwoLP/onefreq/fixedmesh/restart1/rank1,
no visualization/wave/Floquet; requires --release-final-solver. No newdefault.
First tiny/reference EXP93tiny, then medium355/reference EXP93mediumcontrol,
then samefullcontrol at1800s/60GiB/noswap/guard6GiB. SavefirstEonly once;
log/audit exact storeP1→solverrelease→measureP1→measureP2. Raw/S/VSWR/energy/
wholefields gates unchanged. New code needs cached build and regression suite.

Runtime faktycznie używa Podman, nie Docker. Przywrócono niepotrzebnie
uruchomiony Docker do uprzedniego stanu inactive; dalsze runy przez Podman.
EXP94 regresje124PASS; fallback build/m4-reuse/pre-exp94-native zachowany.

EXP94 cachedbuild9,215s/no deps; tiny39/42iter18,726s, medium45/47iter103,033s
PASS raw/TEM/wholefields/deferredaudit. Root checked S+energy <1e−5 vs existing
references, actual errors logged in next receipts. Next full matchedsamebuild
control defer/no-reuse vsdefer/reuse, ref EXP93fullcontrol for first, thenfresh
control forsecond. Both retainreleaseenergy andsamepartialseed/K64/pool256.
Artifacts/m4-deferred-antenna-{control,on}-20261020,1800s/60GiB/noswap.
This isolates reuse undercommondeferredpolicy andcheckswholequality vsEXP93.

EXP94 pełna matched para rootverifiedPASS: control681,698s vsreuse602,944s,
44/35iterboth; sameconfig/buildmanifest/fixture, dwa setupy vsjeden. Rawrelative
candidate7,492212451061e−7/8,356430312650e−7. MaxΔcomplexS2,366618e−8,
ΔVSWR5,138175e−8, Δsumymocy7,077207e−9, Δenergyrelative1,815256e−8,
wholeE/B2,141e−7/1,782e−8;14regionentries. Deferredcontrol vsEXP93 E/B
2,108e−7/1,500e−8. Rootreceipt artifacts/m4-deferred-antenna-root-analysis-20261020.json.
Managedpeak65353018230→53084415322B; deferredcontrolcgroup60525092864→56829792256B,
reuse56832888832B. Actualfullenergyreleasedrop15275324488B; firstEcache179499584B.
No memorycapraise, no diskworkspace; nativecoarseFP64 unchanged.

Final currentbuild filters: defaultposttiny17,712s/39,42iterPASS; deferredmedium
3,30GHz102,608s/45,47 and3,80GHz102,785s/45,47 bothPASS/TEM/wholefields.
MaxE1,034e−6/B1,142e−8 on3,30GHz, no phasefit. Mid355103,033s PASS earlier.
M4.3 symbolicmultifrequency NOT RUN (one-f shard; single analysis17,35s max2,88%
currentfulltime). Same verifiedpartialseed both runs, no warmstartspeedclaim.
M4 complete assessment, M5 active withindexedcheckpoint; M7 wholeband/statistics
remainNOTRUN. No globaldefaultpromotion. Docs-garden beforecommit required.

EXP94 finalvalidation:124 pinnedregressionsPASS/8shellPASS/docscheckerPASS.
SameLuna read-onlydocs-garden foundno materialdiscrepancies. Rootreviewed
source lifecycle/ownership/guards, samebuildreceipts andactualraw/S/power/fields.
Currentnative verified; no livePalacecontainers. Localcommit only (sole remote
is publicupstream), no push. M5 begins source/APIresearch next; goalactive.

## EXP95 — pinned cuDSS hybrid memory API filter (2026-10-21)
Previousgoalturn: progress, M4 actualfullpair+commit. M5 active. Readruntime
cuDSS0.7.1.4/CUDA12.9.1 andactualcudss.h0.7.1. Current nativecomplexguard
explicitly forbids hybrid. Existingadapter already configuresHYBRID_MODE and
DEVICE_MEMORY_LIMIT and uses realcudaMalloc forcuDSS workspaceinhybridmode;
other FEM arrays remainUVM. Hybridexecute isdifferent andincompatible in0.7.
Officialarchiveddocs: https://docs.nvidia.com/cuda/archive/12.9.1/cudss/advanced_features.html
Sourceschecked2026-10-21; defaultreordering/factorizationonly, no MGMN.

Hypothesis/preregistration: actualsamecomplexknown-solutionAPIprobe inUVM and
hybrid256/512MiB, nativeCUDA_C_64F/GENERAL and equivalentreal2N/SYMMETRIC,
2RHS/2valueupdates, errorsindependentlyhostFP64≤1e−10, allocatorlive0afterdestroy.
Beforefactor query actualCUDSS_DATA_HYBRID_DEVICE_MEMORY_MIN andMEMORY_ESTIMATES;
failifminimum>budget, no silentfallback. Hybridfactorworkspace devicecudaMalloc,
notmanaged; matrices/RHS managed. Outputexplicitbudget/queryvalues, parserstrict.
Tiny512DOFmayfitbothbudgets, soPASS provesAPI/accuracy only, notrealoffloadspeed
orfullantennaresources. No nativePalacerebuild/integrationuntilfilterPASS.
Samecachedprobecompiler,2GiB/noswap/2CPU/60scontainer/75swatchdog; eachterminal.
NextifPASS: nativecoarseminimumquery andboundedactualproblem, notextrapolation.
Artifacts planned m5-hybrid-api-{uvm,256,512}-20261021.

EXP95 initialprobecompileFAIL: pinnedcudssConfigSet takes void* ratherthan
constvoid*; pass mutable int64budget (sameexistingadapterpattern). NoAPIruns
launched.126PythonregressionsPASS do notsubstituteCUDAcompile. Fixedtype only;
nextbuildsamecachedrecipe, no limit/dependencychanges.

EXP95 v2 cachedprobecompile1,732s; UVM/256/512 allAPIquality/cleanupPASS.
Native min2517636B/hostestimate853424B; realblock min4749108B/host1025792B.
Allcases2RHS/2updates, error≤1,251e−13. Root independentlyread result.json;
smallfactorsfitbothbudgets, no proof ofoffloadspeed. Library0.7.1supports actual
complexGENERAL hybrid; APIfilter justifies nextintegration, notFP32/TC claims.

## EXP96 — native coarse hybrid memory prototype (2026-10-21)
Root allows explicit --cudss-hybrid-mib for nativecomplex FP64 factors only,
noCPU/hybridexecute/profiler. Existingadapterconfigurespolicy and usesactual
cudaMallocforcuDSSworkspace, FEMstillUVM. NativequeriesactualHYBRID_MODE,
DEVICE_MEMORY_LIMIT andafteranalysis MIN/MEMORY_ESTIMATES; logsactualbytes,
rejects minimum>budget beforefactor, no automaticbudgetraise/fallback.
Runner audits configmarker countperbuild +managed0FP64 andzeroallocatorafterdestroy.
Preserved build/m5-hybrid/pre-hybrid-native. CachedbuildoneTU, defaultunchanged.
First currentnative tinydefaultcontrol referenceM4, thenhybrid256tiny; onlyafter
PASS medium355 hybrid256referenceM4medium.60s/180s,60GiB/noswap/guard6GiB.
No fullantenna beforeAPI+tiny+medium gate. If actualminimum blocks a budget,
reportinfeasible, notRFfailproof. Nativehostestimate isestimate, notmeasuredRAM.
Next actualantenna minimum guard withsmallbudget under180s only afterfilters,
thenrootchooses feasiblebudgets fromactualminimum/currentfreeGPU. No assumption
16GBdevicebudget isusable onbusy desktop; no appsclosing/capraise.

EXP96 firstnativebuild11,270s, tinycontrol16,641s/hybrid25616,663s bothPASS,
39/42iter, raw<9,601e−7, wholeE<9,874e−7/B1,296e−8/TEMPASS.
Medium256FAIL15,501s/cuDSSerror3 beforeanyminmarker, noRFdata. No antenna run.
Rootverifiedstderr; genericCheck lacks operationlabel, so exact failingcall
wasnotproven. Newrevision labelsanalysis/factor/queries. ArchivedAPI permits
budget afteranalysis: nativeadapter nowdefersexplicitlimit, queriesMIN/estimate
beforefactor thenrejects infeasiblebudget orsets/verifiesactualconfiglimit.
No automaticbudgetraise oralgorithmchanges. This isnewhypothesis/APIordering,
notrepeatunchangedfailure; samecaseswithv2outputnames, limitsunchanged.

EXP96v2 build11,493s/tinyPASS39,42iter, actualhybridconfigPASS. Medium256
naturalfeasibilityFAIL beforefactor15,704s: MIN716326660B (~683,14MiB),
hostestimate3499154496B. Neworderingrevealsminimuminsteadgenericanalysiserror;
notRFqualitymeasurement. Nexttwoexplicitfeasiblebudgets768/1024MiB selected
byroot, notsilentautoretry. Medium355/2ports/deferredpolicy/fields vsM4samephysics,
thenfreshsamebuildUVMcontrol forcostcomparison. No fullmodeluntildataPASS.

EXP96 medium355768/1024MiB andsamebuildUVMcontrol all45/47iter/raw/fields/TEMPASS.
Time108,160/108,881 vs101,893s, cgroup4,223/4,240 vs2,598GB. Hybriddevicepeak
805306356/1073741812B (768MiB/1GiB−12B), UVMmanagedpeak1917315108B. No netRAM
saving orspeedup inthisfitsVRAMfixture. RootCSVchecksPASS; receipt
artifacts/m5-hybrid-medium-root-analysis-20261021.json. Hostestimate3499154496B
notobservedRAM. Next fullantenna minimum-only feasibilityguard:256MiB isknown
small; defaultanalysis thenqueryrejectbeforefactor ifminimumexceedsbudget.
Newoutput artifacts/m5-hybrid-antenna-minimum-20261021,180s/60GiB/no swap,
no retry/budgetraise. Expectedinfeasibility result isnotRFqualification.

EXP96 actualfullanalysis95,310s beforefactor: MIN3901173764B (~3,633GiB),
maxhostestimate32714788656B (~30,468GiB); 256MiBguard correctlyrejected.
NoRFsolveinthatdiagnostic. cgrouppeak10712457216B, no capraise.
Next efficient W.3P2only matchedsamebuildpair (35iterhistorically): UVMcontrol
vs4096MiBhybrid, sameverifiedseed/RIGHT/K64/Tol1e−6 andallphysicalfields.
No otherport/defer/cacheeffect; fieldreferenceM3direct forcontrol thenfreshcontrol.
Output artifacts/m5-hybrid-antenna-p2-{uvm,4096}-20261021. Limit900s each,
60GiB/noswap/guard6GiB; stopfailure. Halfworkbeforepossiblebothportpromotion.
4096MiBchosenexplicitlyaboveactualminimum; no autoVRAMincrease. Actualhost
working set mustbe observed, notassertedfromestimate. No performanceclaim from
minimumquery; ifslow/OOM retainnegativeevidence andFP64UVMfallback.

EXP96 W3P2 matchedsamebuildcontrol/hybrid4096 bothPASS/35iter/raw8,357e−7/
weightedE<7,81e−9/B5,59e−10. UVM350,371s vs4096 363,872s (~3,85%slower),
cgroup56023375872→55449051136B (−574324736B). DevicecuDSSactualmanaged0
4294967284B, allocatorlive0; UVMmanaged25008217684B. NotlargeRAMspeedwin.
Next onefinalbudget6144MiB (morefactorcachevsFEMUVMroom tradeoff), samebuild,
sameseed/W3P2/caps900s/60GiB, referencefreshUVM. No furtherbudgetswithoutnew
hypothesis. FulltwoportpromotionNOTRUN; ifnobenefit keepUVMfallback andmove
M5researchtoactualAMS/iterativecoarse, notunboundedbudgettuning.

EXP96 terminal6144MiB W3P2 PASS/35iter/raw8,35659e−7/7weightedregions,
time511,069s,cgroup55434739712B/devicecuDSS6442450932B/live0. Root samebuild/
configidentityverified threepolicies; maxΔS4,7764e−10/energyrelative9,2655e−10.
Receipt artifacts/m5-hybrid-antenna-root-analysis-20261021.json. Thisisoneport/
onepoint, notfullband/bothportsqualification orstatisticalspeedpromotion.
Exclusivecurrenttimers: UVMcoarse63,413s→hybrid31,44s, remainingPC97,153→
139,71/248,49s. SumexclusiveagreesTotalwithin0,1s. Hostestimate32,715GB not
actualpeak; cgroup55,4vs56,0GB isonlymodestnetRAMchange. Largerfixeddevice
workspace maystarveFEMUVM; no newmeasuredmigrationtracehere, keepashypothesis.
Close hybridbudgetbranch REJECTfornow, keepoptinresearch/fallback, M5 ACTIVE.
127regressionspreviouslyPASS; actualfull/min/error+quality evidencepreserved.

User scope2026-10-21: optimizehardware5070Ti16GB/96GBRAM, notonePCBhardcode;
PCB withreflectors/directors/parabola/otherantenna shapes within solverphysics,
no blanketperformanceguarantee forlargeelectricalstructures. AddedM6.6 assessment
frequency sweep3,3–3,9GHz/2ports: actualPROM audit, continuation/recycling,
symbolicreuse, independentoriginalresidual/heldoutpoints/cost+RAM+offlinework.
AddedM7.5 materiallychangedantennageometry/newmeshref, checkcache/seedinvalidation;
physicalgeometrydelta distinctfromnumericalerror. M0–M7order/ActiveM5 unchanged.
Newtasks plannedNOTRUN, notretroactivelypassedbycoax/oldantenna. References
updated inPLAN/MILESTONES/index/newdocs/milestones/sweeps.md.

EXP96 checkpointfinal:127pinnedtestsPASS/8shelltestsPASS, docschecker/diffcheck
PASS, sameLuna read-onlydocs-garden no discrepancies. Rootreviewed config/query
order, nativebudgetguard, mandatoryapplied/cleanupmarkers andoriginalequation
field/S/energy receipts. Currentnativeverified sourcehash
f156542d507a69bf07ddc3b742b0d52f852ab745b2ffff22103fc17ed2498298.
No livePalaceruncontainers. Localcommit/no push(publicupstreamonly). Goal/M5active.

## EXP97 — shifted real auxiliary AMS on GPU (2026-10-21)
Previousgoalturn: progress (hybrid actualW3+assessment andcommit1f8b629). M5 active.
Sourceaudit ksp.cpp chooses HypreAmsSolver oncoarsep1, geometricMG onfinep2.
spaceoperator.cpp realPC path uses K+omega*sigma+abs(omega²)*abs(eps) plus
positiveport/absorbingboundary terms; physicalcomplexA=K+iomegaC−omega²M
unchanged. ExplicitPCMatReal/PCMatShifted true/ComplexCoarseSolvefalse,
AMSSingularfalse,2fixedAMScycles,MGCycleIts1. NotCG onindefinitefullA.
Fixed HYPRE_AMSSetTol0 under opt-inPALACE_AMS_FIXED_GPU keepsstationarycycles
forGMRES. Verify publicHYPRE_GetMemoryLocation/GetExecutionPolicy frompinned
3.1.0header/CUDA_MASK; logconfiguration andactualoperator dimension. Configuration
isnotactualkernelproof; laterboundedNsightwindowmustshowHYPRE CUDAkernels.
Upstreamdocs checked2026-10-21 https://hypre.readthedocs.io/en/latest/solvers-ams.html
and https://github.com/hypre-space/hypre/wiki/GPUs ;latestdocs3.2notclaimpinned3.1
featureswithoutsource/APIcheck. GPUoptions existingams.cpp coarsen8/relax1.

Hypothesis: remove25GBexactLU byusingcheapshiftedauxiliaryPC; extraouteriterations
maynegatethesaving. SmallcoaxanalyticTEM/fields first, thenmedium355 andW3P2
onlyifvalidandplausiblecost. Samegeometry/Tol1e−6/RIGHT/K64/directFP32basis,
FP64physicaloperators/residual. No nativecoarse/hybrid/CPU/Qpool/reuseauditflags
withAMS; formernativefallback build/m5-ams/pre-ams-native preserved. Newflag
--ams-cycles1..4 optin/runtime, no defaultschange/dependencyrebuild. CachedAMS TU.
Preregister tiny2cycles60s/twoparts/referenceM5tinycontrol, raw/S/VSWR/energy/
wholefields/TEM frozenK. Stopfailure, no higheriterationtol ormeshrelaxation.
No paidcompute/appsclosing/SSDworkspace/swap; cap60GiB/guard6GiB unchanged.

EXP97 cachedbuild7,2s/no deps. TinyC2 numericalPASS23,8155s/244,239iterations,
raw≤9,412e−7, wholeE3,15945e−5/B4,39199e−7, Sdelta1,8215e−8/energy9,871e−8,
TEM<0,496%E/0,456%B. Configdevice/executionmarker andAMSdimension17146/cycle14
present; noCUDSSalloc. RootCSVchecks independentlyPASS. Moreiterations than
native39/42, tinytime~43%slower; no promotion. Managedpeak196373968B, cgroup786MB
notcomparabletomultiGBantenna. NextpartialNsight0:2 validatesactualAMSGPUkernels
(nonRFprofile,180slimit), thenmedium355bothports180s/previousqualifiedreference.
Stoponfailure; iftimeoutretainincompleteplusiterationrate, notraiseTol/cap.

EXP97 actualtinyNsight0:2 strictPASS/zerowarnings/clock+coverage+cleanstop;
CoarseSolve6978CUDAkernels/14,894ms, HYPREspgemm/IVAXPY andcuSPARSESpMV kernels
inmeasuredcoarsephase. Sourceactualcoarse=HypreAms; this isobservedCUDAwork,
not100%GPUtime guarantee (CPUsetup/controlremains). profile deliberatelypartial,
complete=false; noRFqualification fromtrace. Artifactm5-ams-tiny-profile-c2-20261021.
Medium355twoportC2 PASS146,825s/433,397iter/raw≤9,992e−7/wholeE9,032e−6/
B6,288e−7/TEM<0,494/0,457%; cgroup1822355456B/managed1841160104B.
Fewerworkingbytes butslowerthanUVM101,893s; rootS/energychecksPASS.

Next W3P2C2 fullfilter only: remove25GBLU andreducecomplexPC torealshifted
mayavoidVRAMthrashing despite~9×iterationsoncoax. This is hypothesis, not
predictedwin. Samephysicalmedium/RIGHT/K64/Tol/verifiedseed andW3P2reference.
Artifactm5-ams-antenna-p2-c2-20261021,900s/60GiB/noswap/guard6GiB, stopfailure,
no freshcontrolcostunlesscandidateactuallyfinishes. Morememory-efficientPareto
result maymatterevenifnotspeedwin; a timeoutisnotqualifiedmemorysaving.

EXP97 W3terminal901,727s/exit255/deadline900s/completefalse. Lastvisible264
(restart4) KSPrecurrencenorm1,501266e−3, notverifiedfinalraw. No fieldcomparison,
final/basisrelease; peakcgroup29319639040B observedonlyinpartialrun. Managed
16110654486B islastmarkthroughsetup, notfinalpeak. Cudsslive0/nodevicefactors,
AMSdimension2196005cycle14. Rootreceipt artifacts/m5-ams-root-analysis-20261021.json.
REJECTexistingC2 forW3; tiny/medium remainnumericPASS, notwithdrawn. No further
fullAMSC2runwithoutnewhypothesis. GPUkernelproof fromboundedtinycoarsephase,
not100%GPUsetupclaim. FP64nativefallback intact.

M5.3 nextplannedresearch basedonactualoldshim: oldFP32adapter convertsrealR64
only; nativecomplexC64 notsupported. Newprototype mustbecomplexC32GENERAL,
DAD/Db equilibration andoriginalFP64CSRresidual correction, strict dtype/control/
stagnation/fallback. CoarseFP32alone isn'tclaimedstable; adaptivecorrection/PC
requiresstationarityorFGMRES+Zbudgetassessment. docs/milestones/mixed-coarse-plan.md
holds pre-integrationgate; NO FP32nativeprototype run yet. CurrentUVMfulltimer
Amdahl:63,413/348,416=18,2%coarse→max~1,22×ifcoarsefree, notwholePCspeedup.
AMS/hybrid assessmentcheckboxes updated only, M5stillACTIVE; FDTD/mixedprototype/
M6sweeps/M7generalization+qualification remainpending. No goalcompletion.

EXP97 finalvalidation129pinnedPASS/8shellPASS/currentnativeverified sourcehash
db205b5d63d0746cba3c791af11e89bc87754e168bd0ae5ce6112943b6886c90.
Root S/VSWR/power/energy andprofile/terminalscopechecksPASS forcompletedfilters.
Read-onlyLuna docs-garden/diffcheck/checkerPASS,nodiscrepancies. No livePalace
containers, fallbackunchanged, localcommitonly/no publicupstreampush. M5active.

## EXP98 — manufactured scaled complex FP32 + external FP64 correction (2026-10-21)
Previousgoalturnprogress: EXP97actualGPU/mediumPASS/fullFAIL documented+commit2971f3c.
M5.3 begins cheapAPIprobe, no nativePalaceintegration/default changes. Reuse
complex_coarse.py build/run harness via --variant mixed, separatebinary/cache,
recipehash primary+includedreferenceCPP+script/arch/images. Oldmain guarded so
matrix/Allocation/Buffer shared, no dependencyrebuild. FP32factor C_32F GENERAL,
originalA remainsFP64host for independent residual/correction, libraryIRexplicit0.
TwoRHS/twovalueupdates atfixedpattern; normalindefinitecomplex stencil and
illscaled A=Gamma*A0*Gamma with gamma1e−3..1e3. B=DAD, g=Db, x=Dy with
D=1/sqrt(abs(diagA)), explicitzero/nonfiniteguard. BaselineF64/rawF32/refinedscaledF32.
ExactlytwoFP64originalCSRresidualcorrections; norequestadaptiveinnerpolicy.

Preregistersixcasecoverage: FP64/refined eachsolution,originalRHSresidual and
componentwisebackwarderror≤1e−10. RawFP32 ≤1e−2 sanitycontrol (notqualifiedhigh
accuracy). Perturbedx[0]mustbe rejectedby solution+rowwisebackward metric, to
catcherrorshiddenbyillscaledglobalRHSnorm. AllfactorINFO/finitevalues/cleanup0,
dtype/count/scale/manifest verified. ExpectedillscaleDmax/Dmin≥1e5. NOTfull
antennaquality orspeedproof; host-managedreading/correctioncostcounted explicitly.
First cachedmixedbuild+oneboundedAPIrun,60s/2GiB/no swap/2CPU/75swatchdog.
Rootselectsnextactiononlyafteractualdata. No paidcompute/appsclosing/SSDworkspace.
Planned artifacts/m5-mixed-coarse-api-20261021. Legacyreferenceprobe rebuilt/smoke
alsoaftermixedPASS toprotectvariantcompatibility; no fullFEMjobbeforeAPIPASS.

EXP98 initialbuild1,646s, APIrun2,232s incomplete afterillscaledrawF32fail:
solution0,20214/backward0,42083 thoughglobalRHSrelative1,085e−7. Fourpreviousrows
passed, includingregularscaled/refined4,36e−16 andillscaledFP646,47e−12.
RefinedillscaledNOTRUN becauseharnessstoppedonnegativecontrol. Newv2 preserves
rawpassed=false asdiagnostic (notcandidate), continues toREQUIREDrefinedcase.
F64/refined1e−10 gatesUNCHANGED; rawfinite/dtype/cleanup/faultcoverage stillrequired.
Thisisreclassificationofknownnegativecontrol, notqualificationofraw20%error.
Newtest ensurefalsepassedcan'tbehiddenandbadrefinedstillFAIL. Explicitnonfinite
checks beforemax avoidNaNhiding. Artifactv1retained; v2newoutputname.

EXP98v2 API completed2.219s: scaled/refined regular solution4.41e-16,
ill-scaled4.56e-12; original FP64 componentwise backward6.75e-16.
Raw ill-scaled remains failed (~0.202 solution/~0.420 backward) diagnostic.
Reference compatibility run2.178s PASS. These corrections ran on HOST; no native
antenna integration or runtime/memory win claimed. Artifacts m5-mixed-coarse-api-v2-
20261021 and m5-mixed-reference-regression-20261021 retained separately from v1.

EXP98 GPU-v3 preregistration: move packing, DAD, original FP64 CSR residual,
FP64 accumulation to shared CUDA helpers in palace/linalg/mixedcoarse.hpp.
Same six cases, 2 RHS/2 updates/exactly2 corrections and frozen1e-10 gates.
Independent CPU checks final solution/RHS residual/componentwise backward error;
host does not calculate correction RHS in FP32 cases. Additional helper tests
n=0,1,509,1009, two RHS, invalid dimensions, assign/add, non-Hermitian CSR and
canaries; parser requires exact success marker and actual correction backend.
New artifact m5-mixed-coarse-api-gpu-20261021; bounded2GiB/no swap/2CPU/60s,
75s watchdog, cached standalone compile. Stop on failure before native integration.

GPU-v3 complete/exit0 in2.241s, compile1.580s. All four boundary/canary cases
and six cuDSS cases covered; refined ill-scaled solution5.78e-12, backward6.16e-16.
FP64cuDSSpeak2,637,284B vsFP32 2,441,380B: not a half-total-memory result.
API GPU correction PASS; no antenna speed/accuracy claim. Add explicit conversion
overflow flag and diagonal-zero/rowmax/invalid scaling controls before integration.

EXP99 preregistration: opt-in --native-coarse-fp32 requires native complex coarse,
rejects realshim/hybrid/CPU/AMS/profile combinations. DAD complexFP32 GENERAL LU,
exactly2 CUDA original-FP64 corrections and FP64 accumulation, unchanged outer
FP64 operator/Tol/K and direct FP32 basis. Every PC apply must satisfy finite
original coarse ||b-Ax||/||b||<=1e-3 (separate PC safety, not outerqualitygate),
no silent fallback/adaptive count. Empty/nonfinite rows, matrix/RHS overflow or
factorINFO fail closed. Whole-field/raw/S/TEM gates remain frozen.
Fallback snapshot build/m5-mixed/pre-mixed-native +pre-mixed-manifest.json.
First cached2job build, rerun strengthened mixed API (new-v4 artifact), then
samebuild tiny FP64control and mixedcandidate at3.55GHz/bothports,60s each.
Both use portsetupreuse/deferredpostprocess, fieldcomparison to existing qualified
tiny FP64control, analyticTEM/L2, RAM/VRAM-only/no swap/hostguard. Stop firstFAIL;
medium/full only after root confirms tiny data. No source/dependency cache deletion.

EXP99 native build18.615s, API GPU-v4 compile1.531s/run2.256s PASS incloverflowflag
andscalecontrols. Tiny samebuild FP64control16.625s39/42iter vs mixed16.606s40/42.
Both complete/fieldgatePASS; mixed first recurrence stop failed true residual,
existing reliable restart recovered final8.496e-7/7.736e-7 (failure retained in log).
E/B candidate deltas<=1.060e-6/3.442e-8; nativeTEM<0.5%. Coarseapply85solves,
2corrections,maxoriginalcoarseresidual8.754e-5<1e-3 safetygate. cuDSSpeak
113,329,412→78,529,844B; cgroup575,119,360→579,624,960B (NOTmemorywin overall).
No tiny speed claim. Root reviewed actualresult/fields/CSRmarkers.
Next filter samebuild coax-medium3.55GHz/bothports,180s each, matchedflags and
fieldreference m4-deferred-medium-on-20261020; outputs m5-mixed-medium-{control,on}
-20261021. Frozenquality and limits unchanged; stop before full if any failure.

Medium completed101.531s45/47iter control vs97.503s47/49iter mixed (singlepair
-3.97%, notmedian). cuDSSpeak1,917,315,108→1,089,091,988B; cgroup2,614,333,440→
1,920,925,696B; managedphasepeak3,777,996,444→2,975,739,840B. Reliable true
residual restarts bothRHS retained (initial1.37e-5/1.23e-5), final9.830e-7/
8.949e-7; maxcoarse residual2.559e-4. Final qualityPASS, notfakeconvergence.
Root receipt m5-mixed-filters-root-analysis-20261021.json confirms matchedtiny/
medium deltaS<=5.05e-9, deltaVSWR<=1.01e-8, energy<=1.02e-8, fields/TEMPASS.

EXP100 preregistration W3: samebuild T-Shaped medium3.50GHz/P2, identical original
mesh/config/Tol/K64/initialfields and fieldreference m3-antenna-native-direct-
20261019; initial m1-antenna-resident-fp64-20261018 is ONLY startingapproximation.
ControlnativeFP64 and mixedcandidate, both directFP32basis/rightPC/releaseGMRES/
finalsolver/audit/pool256MiB. 900s each,60GiB/no swap/hostguard6GiB unchanged;
stop first failedexecution/field gate. No changing mesh/Tol, no partial claimed
memorywin. Compare complete walltime/iterations/exclusivephases/memory and K4
S/VSWR/power/energy/fields. Outputs m5-mixed-antenna-p2-{control,on}-20261021.
No bothport/sweep/globalpromotion from this onepoint; W4/W5/M7 remain required.

EXP100 pair COMPLETE/PASS. FP64 339.362s vs mixed273.843s (-19.31%),35/35iter;
cgroup56,026,882,048→45,375,688,704B (-19.01%); managedpeak52,276,667,194→
40,962,568,438B. cuDSS25,008,217,684→13,348,006,188B; factors40.528→4.823s,
exclusivecoarse61.613→32.038s, setup83.600→48.390s, otherPC96.235→95.123s.
Originalouterresidual8.35661e-7/8.35698e-7; mixed36calls/maxcoarseresidual2.32445e-5.
Root m5-mixed-antenna-root-analysis-20261021.json: deltaS6.70e-10,deltaVSWR5.92e-10,
power4.96e-11, relativeenergy1.85e-9; allsevenfieldregionsPASS E<=1.469e-8/B<=1.558e-9.
Measured GPUprocess bytes are NOT physicalUVMVRAM residency. One pair, no median.
Candidate promising opt-in, notglobalpromotion or wholebandqualification.

EXP101 preregistration: finish W2 coax-medium at3.3 and3.8GHz/bothports, same
FP64control/mixedcandidate pair perfrequency,180s each. Root prepared exact
artifacts/m5-mixed-w2-commands-20261021.sh; refs m4-reuse-medium-on-{330,380}-
20261019, identicalphysics/fields/TEM. Same flags/limits as3.55GHz. StopfirstFAIL,
no automaticretuning/retry. These separatefrequencyfilters do not prove sweepreuse.

EXP101 four jobs complete/PASS. Coax-medium3.3 control101.640s45/47iter vs
mixed96.486s48/50;3.8 control101.659s45/47 vs97.634s47/49. True restarts retained,
finalraw<=9.198e-7; maxcoarse safety5.068e-4, TEM E/B<0.5%, weightedfieldsPASS.
Root receipt updated: allthreefreq/bothports deltaS<=7.04e-9,deltaVSWR<=1.39e-8,
power<=1.38e-8,energy<=1.29e-8. Native source unchanged since qualified build.
No globaldefault/push; M5 staysACTIVE. Next: M5.5 actualmigration profile,
M5.6 FDTDcostassessment before M6. W4/W5/repeats/newgeometry remainNOTRUN.

EXP98–101 checkpoint validation: pinned134 unit tests PASS,8shell tests PASS,
docs index/stage check PASS, gitdiffcheck PASS. Same Luna read-only docs-garden
PASS; root reviewed diff/receipts and verified current native manifest sourceSHA
8692e80d926a58a74f38bff9c643b578810a94d35d4d534a2c027215fd11607f.
Hardened dtype/scaling/cleanup parser rechecked against allfive actual native
mixed artifacts PASS. Native default FP64 preserved; all jobs terminal/cleaned.

EXP102 preregistration M5.5: compare measured CUDA/UVM for the qualified EXP100
nativeFP64 vs mixedfixed2. Reuse existing pinned Nsight selectivecapture/affine
hostclock; no native/dependency rebuild. Runner now permits mixed partialprofile
and requires actual dtype +mixedsummary/cleanup for profile_complete; RF complete
remains false. Frozen strictclock/warning/iterationcoverage gates unchanged.
First coax-tiny mixed0:2,60s analytic profilefilter (no fieldqualification); only
after PASS matched W3P2 latewindow30:2,600s each, samephysics/K64/initialseed,
FP32directbasis. RAM-only profiler temp/SQLite, finalrep<=64MiB ordinary result,
60GiB/noswap/hostguard6GiB; no fullprocesscapture/paidcompute/appsclosing.
Compare selectedwindow bytes bydirection/migration cause and exclusivehostphase,
not summed overlappingkernel/copytimes; no extrapolation to fulljobtotal.

EXP102 firsttiny FAIL runnergate, preserved m5-mixed-profile-tiny-20261021:
Nsightstrictsummary PASS (clock/coverage/cleanstop/no warnings), CUDAactualmixed
markers/cleanup valid, but runner demanded6nativebuilds fromfullcoaxsweep after
intentionalstop inside firstsolve. New regression distinguishes partial1build vs
full6; no relaxation of strictprofile/RF gates. RFcomplete remainsfalse and full
expectedcounts unchanged. V2 separateartifact, same argv/limits, no nativebuild.

EXP102 tiny-v2 completefalse/profile_completetrue, actualdtype/mixedcleanup PASS,
clock/coverage/cleanstop/no warnings strictPASS; runtime8.453s. Root inspected
actualresult/summary. Full late30:2 matchedcommands prepared byroot in artifacts/
m5-mixed-profile-commands-20261021.sh; two bounded600s jobs, no fieldqualification.

EXP102 matched lateprofiles PASS: control329.345s/on263.181s includingprofile
setup/cleanup; notnewRFspeedclaim. Strictclock/coverage/cleanstop/no warnings,
actualdtype/cleanup PASS; RFcompletefalse. Root receipt m5-mixed-profile-root-
analysis-20261021.json decodes embeddedNsightenums: UVM251,124,858,880→
186,634,575,872B inselected2iterations (-25.68%); pagefault9.632→8.249GB,
speculativeprefetch115.596→85.280GB, eviction125.897→93.105GB. Window12.944→
10.530s, coarse4.450→2.279s, otherPC6.583→6.425s. GPUkernels5262→11420 due
correctionsteps; Hcurl~1.918→1.914s unchanged. Overlap/partiallimits documented.
M5.5 evaluated. FP64fallback/default and fullquality EXP100 unchanged.

EXP103 source research/resource screen, no FDTD solverrun. gprMax master pinned
d068a023265c1337982940efb41ef05a04f064a7 GPLv3; actualCUDA/HSG/portnormalization
read, sourceonlycache561KB+extra files, no installeddeps. Bounds ofactualfixture
299.943×299.953×300mm confirmedstream3.04s withmeshSHA. Read matching archived
geometryparams:0.2mmgap,0.035mmcopper,0.762mmsubstrate,0.14351mmpinradius,
coaxbodyz−40.303mm. ParameterSHA/source in m5-fdtd-budget-20261021.json.
New tested tools/fdtd_budget.py computes field/IDtypes, CFL, HSGFP64/padding/
parentalignment, optionalDFT cost and optimisticfields-onlystreaming at896GB/s.
Uniform0.2mm needs162.324GBdevicebase;0.5mm10.420GB butgap<onecell. HSG0.1mm
55cube20.622GB; thinslab55×55×2mm4.904GB yetdoesn'tresolveoutsidecoax;0.05mm
slab25.734GB. 100nsassumed/nonmeasureddecay; bothports, allfreqinoneportwindow,
20/100/200nssensitivity and Qdecayformula documented. No false runtime/accuracy
claim or blanketFDTDrejection. M5.6 OPEN: sourcecheck multiROI contact/nesting,
continuouscoaxgeometry/feasibleconvergence beforeactualsmallCUDA/TEMbenchmark.

EXP102–103 checkpoint:139pinnedtests/8shell/docscheck/gitdiffcheck PASS. SameLuna
read-only docs-garden PASS; root reviewed actualprofiles/enums/receipts and source
math, native verified unchanged sourceSHA8692e80d926a58a74f38bff9c643b578810a94d35d4d534a2c027215fd11607f.
No native/dependency rebuild needed, no paidcompute or runningjob. M5 ACTIVE,
M5.5 evaluated; M5.6 remains OPEN with explicit nextHSG feasibility action.

EXP104 source/API +actualgeometry assessment (no GPU/FDTD simulation). Archived
freecad_parts.json SHA matches samecase mesh-audit exportmanifest; source mesh
SHA rechecked identical to localfixture. Actual substrate bbox72×72×.762mm,
signal+PTFE selectedsubset union91.676×72×47.750mm, coaxportsx±45/z−46.803.
Old55mm parameter notwholephysicalboard; docs corrected, oldillustrativebudget
retained withscope. HSG1.1/.1mm parentaligned+paddedbase36,144,022,896B already
over16GiB withoutallreturn/director/PMLaux; .05mm235.753/265.216GB. Receipts
m5-fdtd-actual-feed-20261021.json and m5-fdtd-hsg-source-audit-20261021.json.
Pinned gprMax AST/source audit: SubGridHSG isModelUserObject, publicadd accepts
onlygeometry/grid/output, nestingrejected; sg.parent_grid=model.G andCUDAall
precursors/interfacesusemodel.G. No verifieddirectfinefineinterface; no claim
alloverlappingsiblingsinvalid. Thincoaxdetail belowmainstep cannotjustbeassumed
preserved. Directuniform/singleHSG workflow REJECT resource/API; benchmarkNOTRUN
afterfailedgate, customnewcoupling/subcell remainsunassessed. LimitedM5.6assessment
completed without changingK/physics or pretendingFDTDspeed/qualitywasmeasured.

Root completionaudit M5.1–M5.6: compatibility/API/budgets, AMS actualGPU+negative
W3, scaledfixed2coarse+FP64fallback, W2/W3/K/speed/memory, currentstrictUVMprofile,
andFDTDresource/APInegativeassessmentallhaveexplicitreceipts/limits. Assessment
M5COMPLETE, notgoal/globalpromotion. M6checkpoint created/INDEXlinked before
ActiveM6; noM7/W4/W5/medianclaim. No paidcompute/appsclosing/swap/depsrebuild.

M6 initialread-onlysourcework: copiedexistingMAGMAbackend fromstoppedbuilder,
notstarted/recompiled. libCEED basis source SHA0c41d35fde4470965b7b2beb6d1801aef526fea1c4c53e32f62bce7cdd1357ff
matches GitHub pin cbd49027b0ae891f0c8efd9d9cf05bc82385a388. Profilenamesandcode
showcustominterp/derivbranch P,Q<=40, notgenericGEMM; N=nelem*ncomp, curl/div
sharederivbranch, transpose/addmustpreserveaccumulation. Sourcecache+selection
receipt artifacts/m6-kernel-selection-20261021.json. ActualP/Q/N/qcompNOTYET
measured; M6.1 stillOPEN. Nextsmallopt-inaudit beforeTF32prototype, avoidglobal
operatorreplacementthatwouldcorruptindependentoriginalFP64residual.

EXP104/M5→M6 checkpoint:139pinnedtests/8shell/docschecker/gitdiffcheck PASS.
Root rechecked current W2/W3/profile/source receipts +unchangednative manifest.
SameLuna read-only criticaldocs-garden PASS includingconditionalM5.6benchmark
gate andlimitations. No runtime/performanceclaim fromsourceaudit. M6.1actual
dimensionaudit isnext; fullgoal/W4/W5/M7 remainOPEN.

EXP105 preregistration M6.1: opt-in --basis-audit via existing UVM/cuDSS adapter,
new host-only TU intercepts CeedBasisApply/ApplyAdd but always callsoriginal.
After successful call queryCPUmetadata(P/Q/elements/components/qcomp/space/topo,
eval/transpose/add/vectorlength), aggregate<=2048groups/counts. No field copies,
CUDA calls/sync, vector/workspace allocation or arithmetic replacement. Disabled
path only forwards; enabled counters areprocess-lifetimehostbookkeeping. Parser
requires exactsinglefooter/totalcalls/zeroqueryerrors/zerooverflow, FP64ABI,
validenums/bufferlengths. CountsAPIcalls, NOTGPUtime/uniqueallocations orPCrole.
Cachedbuildjobs2 shouldcompileonlyadapter(noPalace/depsTUs); snapshot
build/m6-basis-audit/pre-audit-native +manifest. Firstcoax-tiny3.55GHz/bothports
samebuild controlOFF vs auditON60s each, mixedcoarse/directbasis/reuse/deferred
sameflags andqualifiedfieldsref m5-mixed-tiny-on-20261021. Frozenqualityunchanged.
Root checksallactuals beforeW3partialaudit. No paidcompute/appsclosing/swap.

EXP105 root review: tiny bothports control/audit complete,40/42iterations each,
16.526/16.606s diagnosticpair. Independent CSV maxdeltaS3.340e-10,
VSWR6.483e-10,relativeenergy7.206e-10,portpower6.531e-10; wholefields PASS.
46groups/18882calls/zeroerrors/overflow; auditJSON24075B,47taglines9844B.
Cachedbuild8.455s recompiledmain.cpp+link plusadapter, no dependencies rebuilt;
expectedadapter-only statement above was prediction, notactual. No speedclaim.

EXP106 prereg: one full W3 tshaped-medium3.50GHz/P2 --basis-audit,900s hardlimit,
60GiB/no swap/hostguard, same native mixed/directFP32 K64/right/seed asEXP101.
Reference m5-mixed-antenna-p2-control-20261021 independentFP64coarse, frozenK.
Aim actual basis P/Q/N/qcomp/transpose/add dimensions across setup/solve/postproc;
no attribution ofAPIcounts toGPUtime orPC-onlyrole. Output m6-basis-audit-antenna-p2-20261021.
One run (expected~274s), not multiband/benchmarkmedian. No physicschange/paidcompute.

EXP106 completed272.718s/35iter,rawRHS8.357105e-7,wholefields7regionsPASS;
rootCSV deltaS7.029e-10/VSWR2.486e-9/energy3.548e-10/power3.113e-10.
Audit108groups/14627calls/errors0/overflow0,JSON55809B/taglines22789B.
Source a217334ae31f5df0a51953bc9e78bbc42cd4f3abab42121c95d0ecc59e4203ae.
Actual frequenttetHcurl20/14/qcomp3/N1601320; helpers/triangle/Q6 included.
Parser separateslengthvsrequiredbytes: workspace1.973GB notactioninput256.211MB.
Denseaction2.690GFLOP/logicalminimum794.255MB; simpleFP64→FP32→GEMM→FP64
idealtraffic1.589GB+397.127MBfloatworkspace, notphysicalmeasuredtraffic/runtime.
Rootreceipt artifacts/m6-basis-audit-antenna-root-analysis-20261021.json.
M6.1qualifiedcurrentfixture; M6.2next actualbasis/libraryprototype seconds-first,
conversion/transpose/add included, noTCclaim/globaloperatorprecisionchange.

EXP105–106 checkpoint:142pinnedtests/8shell/docschecker/diffcheck PASS.
SameLuna read-only docs-garden PASS; minor table/derivedreceipt wording clarified.
Root reviewed code/logs/CSVs/fieldhashes and honest auditlimits; no newnative
rebuild needed forPythonparser/docs. M6.1 PASScurrentfixture, M6.2 next;
M6/M7/sweeps/W4/W5/median/generalization remainOPEN. No paidcompute/swap/appsclosing.

EXP107 prereg M6.2: isolated cached two-TU probe, currentlibpalace MFEM
InitBasisFromRule +pinnedMAGMA original as GPUcontrol; independentlongdouble
CPUloop small257elements. FamiliesND2tet(P20),RT1tet(P15),H1P2tet(P10),
ND2triangle(P8); Q6/14, interp/curl/div/grad,transpose/ApplyAdd,odd257/131071
sizes, additional2components forNDtetQ14. 96actions; FP64librarycontrol,
FP32pedantic and requestedTF32 cuBLASGemmEx beforecustomTC/CUTLASS work.
Frozen action gates FP64 1e-11, FP32 2e-6, TF32 2e-3 relativeL2/scaledmax;
these arefiltergates, notrelaxedRFcriteria. Canary+faultdetector, conversionin/
out included inapply, staticbasispackcostseparate, FP64callerbuffersretained.
GPUresidentboundedbatches, noUVM/solver/TCinstructionclaim. FP64originalouter
operator/residual untouched. 120s build/run limits,6GiB/no swap, no paidcompute.
Native/dependencies untouched; build/m6-ceed-tensor cache/manifest.

EXP107 firstbuildFAIL: missing publicbackend header for
CeedBasisGetNumQuadratureComponents. No runtime performed. Root added
<ceed/backend.h> consistent withpinnedactualaudit TU; preservedbuild-v1log,
no dependency/nativechange. Retrynewrecipe onlyafterthissourcefix.

EXP107v2 addonbuildPASS4.326s, runFAIL1.016s noOOM/noactions: Q6 notfound
amongMFEMtetvolumerules. Preserved originalartifact unchanged. Source indicates
arbitraryfixedmappedface bases useInitCachedBasisFromRule; metadata alonecannot
identifyexacttracepoints. Correctedprototype Q6tet usesrepresentative mapped
triangle6pointz0trace; Q14 actualMFEMvolumerule. NotclaimingexportedactualW3
tracecoefficients. Retainmappedrules torespect MFEM pointerkeyedtabulationcache.
Retryv3newrecipe/newartifact only; no changes tophysicalsolver/fixture.

EXP107v3 PASS: addon4.108s/run13.466s/96actions/canaries/independentCPUcontrol.
AllactionfiltersPASS FP64maxrel2.37e-16,FP32~1.05e-7,TF32request~4.97e-4
(scaledmax~9.61e-4); noTCproof. Root comparedactualoriginal peraction:
large131071 FP32 faster39/48, medianratio.871; small257 slowerall48.
NDtet20/14 large6singlecomponentactions FP32~.55–.64oforiginal; TF32usually
slowerthanFP32 andmuchlessaccurate. No fullsolver/UVM claim. Originalfailed
runkept; screen sources+manifest savedbuild/m6-ceed-tensor/exp107-screen.

EXP108 prereg: extend identicalaction code --scale,42NDtetQ14actions incl
257/1023/4099/16383/65537/131071/actual1601320, interp/curl,forward/trans/Add.
SmallCPUcontrol retained, allsizecandidatevsexactoriginal; samefrozengates,
conversions/workspace/count/medianchecked.120s/6GiB/no swap,2GiBfreeGPUguard,
GPUresident boundedprobe only; no larger FEMrun. Resolve crossover/scaling
beforePCintegration/fusedkernel decision. No paidcompute/native/depsrebuild.

EXP108 root review PASS:42actions across7sizes, only6 atactualN1601320
(correctedagent shorthandthatall42wereactualN). Run18.556s/build4.224s,
noOOM; everyoriginalCPU/FP64layout/canary/filtergatePASS. Foractual6actions
FP32wall2.598–3.223ms vsoriginal3.473–3.744ms, medianratio.797, range.748–.863;
TF32requested3.325–3.631ms,ratio.958, largererror. ExtraallocatedFP32scratch
397130720B, notGPUresidency. Sizes<=4099: mixedslowerall6; no globalswitch.
Updated strictparser rechecks numericmetrics/frozenactiontol/flags/timingmedians,
notjustgreenbooleans. Rootverifiedoriginalscreen+scaleJSONcurrentchecker and
hash/cache; rootreceipt artifacts/m6-ceed-tensor-root-analysis-20261021.json.
ActualTCinstructionproofNOTRUN,noTCclaim,TF32backendnotpromoted. FP32fused
registerconversionnext boundedhypothesis beforePCscopeintegrationandfullK.

EXP107–108 checkpoint:146pinnedtests/8shell/docschecker/diffcheck PASS.
SameLuna read-onlydocs-garden PASS; corrected42total/6actualN count confirmed.
Root reviewed implementation/layout/math, actualcaseJSON independentCPU+GPU
controls/currentstrictvalidator andrecipehash; native/dependencies unchanged.
M6.2 firstlibraryfilterPASS; no solverpromotion/TCproof/UVMspeedup, no paidcompute.
NextfusedFP32workspace-free actionfilter, thenexplicitPCscope/K/W1→W3.
M6/M7/sweeps/generalization/W4/W5/median stillOPEN, goal remainsactive.

EXP109 prereg M6.5: isolated --fused fourthmethod in existingtwoTU actionprobe,
FP64caller arrays/FP32register FMAs, staticFP32basis only. Dimensiontemplates
P/Q/qcomp, forwardreusesconvertedx for3components; transpose sumsallcomponents,
AddkeepsoriginalFP64Y. No intermediaryvectors/packingkernel; noTCclaim. Explicit
badargument/unsupportedshape guard; CPU/FP64/canary/faultdetector retained,
fused actiongate2e-6 unchangedfromFP32; metadataworkspacebasisbytesonly.
First96actionsscreen120s/6GiB/noSwap, cachedaddoncompileonly120s. Candidate
negativeaccuracypreserved, notRFqualification. Benchmarkstillallocateslibrary
scratchforcomparators; do notclaimmeasuredprocesspeakreduction. Ifpromising,
second42size-ladder toactualN1601320; no fullFEM/defaultchange/paidcompute.

EXP109 screenPASS13.685s/build4.904s,96actions/fused maxrelative1.102e-7,
scaledmax5.003e-7. Root inspected individual NDtetQ14/N131071: fusedforward
.117–.119ms vsoriginal.298–.304ms (~.39ratio), transpose.297–.305ms vs
.320–.340ms (~.88–.96ratio), lessusefulthantheSGEMM+scratchtranspose.
Do notaverageawaydirectiondifferences. No native/operatorchange/RFclaim.
EXP110 prereg: samecode --scale --fused,42size-ladderactions/6actualN1601320,
120s/6GiB/noSwap. Keepforward/transpose/Add/permethodcosts separate before
integration. SourceunchangedafterEXP109; cachedprobe, nobuildrequired.

EXP110 rootreview strictvalidator/cache/CPU/GPU PASS. SixactualN rowstargeted:
forward1.334–1.342ms vs3.474–3.478ms; transpose3.549–3.562ms vs3.634–3.738ms.
Fusedmaxrelative1.148e-7/scaledmax5.003e-7; per-methodownbasis3360B vs
library397130720B, comparisonstillallocatesbothvectors, nopeakclaim.
Rootreceipt artifacts/m6-ceed-fused-root-analysis-20261021.json. Candidate
PCforwardonly; transposekeepFP64. ApplyB/B->Mult boundaryread initerative.cpp;
nextRAIIscopeaudit+content/lifetimecache/FP64outsidePC+cleanupbeforeKrun.
Root tighteneduntrustedkernelargumentp/q<=40/qcomp<=3 before64bitproducts
(nochangeforalltestedshapes), requirescachedrebuild+samecheapfilterbeforecommit.

EXP111 prereg regressiononly afterargumenthardening: cachedaddonrebuild,
96screen then42ladder samefrozenactiongates120s each. Newartifacts
m6-ceed-fused-guard-{screen,scale}-20261021 preserveEXP109/110 untouched.
Not aM7repeat/performancepromotion; verifycurrentcompiledrecipebeforecommit.

EXP111 guardedrecipePASS build1.811s/screen13.764s/scale19.295s,
96/42actions/noOOM; currentbinarya5900a00…c772aa04. Rootverified both strict
caseJSON+commandmanifest hash vsactualcachedbinary, allprecisionfiltersPASS;
fused errorsunchanged≤1.148e-7/5.003e-7. No native/dependencychange ornewRFclaim.

EXP109–111 checkpoint:147pinnedtests/8shell/docschecker/diffcheckPASS.
SameLuna read-onlydocs-garden PASS; root reviewed sharedcode/actions/error
bounds/currentrecipe hashes and direction/bytes distinction. Candidateonly
PCforward; integration/scope/cache/cleanup+fullK/netjob stillOPEN. No paidcompute,
no native/depsrebuild/swap/appsclosing. M6/M7/W4/W5/median/sweeps remainOPEN.

EXP112 prereg M6.4: opt-in --pc-basis-fp32-forward. Shared testedGPUkernel
moved totools/adapter/ceed_fused.cuh, probe hashes/sources includeit. RAII
ApplyB guard onlyaroundB->Mult; originalA/verifiedrawAx-b andtranspose remain
originalFP64. Adapter forwardonly/nonTensor/supportedP/Q/qcomp/N>=8192;
unsupported/small/nonfinitecoeff/alias/cachecapacity useoriginal path (counted),
API/CUDAerrors abort, no postfailurefallback. Staticcoeffcache keyedexact
finiteFP64content+dimensions, max256entries/<1MblogicalFP32basis, notCeedBasis
address; no intermediatevectors. Conservativepre/postdevice sync. Cache cleared
at finalsolverrelease beforefields; strictscope/cachecleanup gate + K separate.
Nativebuildjobs2/cache/no dependencyrebuild; fallbackactualnative+manifest saved
build/m6-pc-basis/pre-integration-native andpre-integration-manifest.json.
Firsttinybothports controlOFF/candidateON60s each,currentmixedcoarse/directK64/
right/reuse/deferred/releases andwholefieldsreference. 150pinnedtestsPASS.
No paidcompute/physicschange/defaultpromotion; do notstartmedium/W3untilrootreview.

EXP112 tinyPASS currentbuild13.698s; control16.512s40/42iter vsPCforward
16.617s45/45iter. IndependentrootCSV S/VSWR/energy/powerPASS, weightedfields
candidate<=7.372e-7/2.420e-7. Audit94enters=exits/active0/mixed4888/
outsideoriginal3714/transposeoriginal8460/cache3misses+4885hits/
allocated=freed8400B/live0/release1. OriginalA/rawchecksremainFP64. Extra
reliable-restartnorms2.736e-3/3.629e-4 thenfinal8.491e-7/7.504e-7; notsilently
acceptedrecurrence. FP32PC canbeinsufficientlylinear forclassicrightGMRES
reconstruction, coulderasekernelgain; noFEMspeedclaimfromtiny. Investigate
cheapmediumbeforefullW3; FGMRESextraZmemory isnotfree.
EXP113 prereg: mediumcoax3.55/bothports samebuildcontrol/candidate180s each,
sameK64/direct/mixedcoarse/reuse/defer/fields flags, rawcheck/frozenK. Onlyone
frequency first; ifmoreiterations/netloss do notautomaticallylaunchfullW3.

EXP113 rootCSV/strictauditPASS: mediumdeltaS1.027e-10/VSWR5.341e-11/
energy1.002e-10/power1.234e-10; fields≤9.361e-8/1.109e-7. Onepairtime
99.579642/99.592211s,48/49→55/57iterations. Scope116/116,8352mixed/
4258outside-original/10440transpose-original;4tables8784Ballocated=freed/live0.
No netgainclaimed,noW3 automaticrun. Rawgap.00922/.01011vscontrol1.52e-5/1.29e-5
beforeacceptedFP64rawrestarts. SourceclassicrightGMRES reconstructsB(sumyV),
FGMRESsumyZ; numericalnonlinearityhypothesisnotisolatedcausalproof. Existing
FGMRES rejectsFP32basis; illustrative fullK64V/Z capacity23.335GBvs5.834GB
packedV(+17.501GB), notmeasuredpeak/lazyallocation. NewnextstepcompensatedFP32
+homogeneity/superposition smallfilter, notnaivelytoggleFGMRESorlooserRFtol.

EXP112–113 checkpoint:150pinnedtests/8shell/docschecker/diffcheckPASS.
SameLuna read-onlydocs-garden PASS; root reviewed code/roleboundary/actualCSV/
rawchecks/fieldaudits/cachehash+cleanup andunchangedcurrentnativehash. Current
PCforwardintegrationNOTPROMOTED/HOLD, noW3costafterunpromisingmediumfilter.
Nextsmalllinearity/compensatedmixed arithmetic test. PriorqualifiedFP64basis
+M5mixedcoarse fallback/default retained. M6/M7/W4/W5/sweeps/median stillOPEN.

EXP114 prereg: addononly compensatedforward mixed dot, F32 hi+lo coefficient
splits andF32 TwoSum/FMAproductresidual, F64inputsplit/outputrecombine. No
native/adapter modification, no newintermediatevectors;2smallstaticbasisarrays.
InspiredbyOgita/Rump/Oishi AccurateSumDotProduct DOI10.1137/030601818,
notclaimingpaperproofapplies tothismixedvariant. FP32sumtransform explicitRN
intrinsics, nofastmath. Compareoriginal/CPU/FP64/F32pedantic/TF32/fused.
Forwardonlycandidategate1e-11 (not2e-6); preservedoriginalRFgates.
Small257columns addhomogeneityalpha1.23456789012345 andindependentv superposition
fororiginal/allmethods; baselineoriginal/FP64controlsrequired, candidatefailure
preserved. Basislinearity only, notwholePC/causalproof. Screen96actions32forward
candidate rows; ifpromising/qualitypassthenactualNladder.120s addonbuild/run,
6GiB/noSwap,allhotdataRAM/VRAM, no native/depsrebuild/paidcompute.151testsPASS.

EXP114 root strict96action validationPASS/build5.381s/run13.923s;32forward
candidate errors~7e-15 andhomogeneity/superposition~1e-14 (basis only).
All16largeN131071actions SLOWER1.332–4.053× originalFP64 CUDAinterval; no actualN/fullFEM
run/promote. Receipt artifacts/m6-compensated-root-analysis-20261021.json.
Goodaccuracyalone isnot hardwareoptimization; reject unchangedalgorithm.

EXP115 prereg: samecompensatedsum, separate bit-split inputvariantavoids
per-input FP64subtraction in common exponentrange[-74,100]. Out-of-range
terms explicitlyuseFP64fallback andsamehi/lo coefficientpair; no silentfloat
flush/overflow. F64outputrecombine remains. IndependentCPU/range11scales
1e-300..1e300 inclbinaryrangeedges andoriginal/FP64controls. Correct action
errorhelper tiny-reference floors beforestress; injected1e-300errorsmustfail.
RetainEXP114comparator/fused/librarymethods, action+linearitygate1e-11.
Addononly cachedbuild120s then96screen120s/6GiB/noSwap;152pinnedtestsPASS.
OnlyifqualityPASSandkeyND20Q14forwardN131071 fasterthanoriginalconsider42ladder.
No native/PC/defaultchange orfullFEM/paidcompute; allhotdataRAM/VRAM.
EXP115 invocation correction: cachedaddonbuild6.035sPASS; delegated argv had
--seconds120 (invalidCLI), exited2 beforeGPUrun/noartifact. Rootcorrectedto
--seconds 120; sameexperiment/source, no candidatefailure or simulationrerun.
EXP115 rootstrict96actionsPASS,32newforward/16small11scaleCPUrangetests,
maxrangeL2~9.16e-15. ND20/Q14/N131071 CUDAinterval.299–.305→.256–.258ms;
components2 .585–.592→.509–.510ms. ScalarQC1/traceoftenSLOWER, do notselect.
Thisisolates inputsplit substitutionwithincompensatedalgorithm, notwholePC
causality. Receipt artifacts/m6-compensated-bits-root-analysis-20261021.json.
EXP116 prereg: samecachedrecipe --scale --fused --compensated --seconds 120,
42actions/14newforward/actualN1601320, allsamegates. No nativebuildneeded.
OnlyND20/Q14largeforward candidate forfuturePCscope; transpose/defaultoriginal.
EXP116 rootstrict42actionsPASS/currentbinaryrecipe+commandmanifestverified;
14newforward qualityPASS,actualN1601320 interp3.481824→3.034816ms,
curl3.473312→3.048ms (CUDAinterval3samplesmedian). No TC/native/wholejob claim.
Scalar/tracevariants notselected. NextscopedPCND20/Q14 tiny/medium beforeW3;
FP64originaloutsidePC/rawresidual/default preserved. Newartifacts source+receipt
linked docs/ceed-tensor-probe.md, allhotdataRAM/VRAM. M6/M7/sweeps remainOPEN.
EXP114–116 checkpoint:152pinnedtests/8shell/docschecker/diffcheckPASS;
sameLuna read-onlydocs-gardenPASS; rootreviewed bitrange/formula/FMA sum,
strictnegative-result preservation, recipe/currentbinary and actualN timings.
Nativehash unchanged4e2fa56f…a4dc611; no solver/default change/promotion.
Next bounded scopedPC ND20/Q14 integration, control/quality/netcost first.
M6/M7/W4/W5/sweeps/medians/generalization remainOPEN; goalactive.

EXP117 prereg: shared testedcompensatedheader movedtoadapter (sameprobe+PC),
newopt-in --pc-basis-compensated-forward, exclusivewithpreviousFP32PCflag.
OnlynonTensorP20/Q14/QC3 forward withinexistingRAII B->Mult scope; allother
shapes/transpose/Add/outside originalFP64. CacheexactfiniteFP64coefficientcontent
+dimensions, same256entries, twohi/lotables6720B/shape, explicitcleanup.
Arithmeticname expectedbystrictaudit/runner, conflictingmodesfail/isolatedenv.
N>=8192 inheritedselection; tinyN13086 liesbetween4099/16383microcrossover,
so costmustbemeasured, notinferred. Do notlowernumericKtol. No extracandidate
largevectors orFGMRES switch. OriginalA/rawcheck remainFP64, default unchanged.
Fallbacksavedbuild/m6-pc-compensated/pre-compensated-{native,manifest.json}.
Cachednativebuildjobs2; thenaddonrebuild+96screen guardsharedrecipe.
Nexttinycontrol/candidate60s each bothports/frozenK64/right/directFP32storage/
M5mixedcoarse/reuse/deferred/fields; qualifycontrolvsM5tiny andcandidatevscontrol.
Onlyrootreview aftertinypermitsmedium/W3.153pinnedtestsPASS. No paidcompute,
no swap/appsclosing/depscleanup, allhotdataRAM/VRAM.
EXP117 cachednative9.152s/addon2.607s/sharedscreen14.115sPASS. Rootstrict
sharedheadercoverage+candidateCPU/range+currentbinary/recipePASS. Nativehash
6bec38a0…2ad0938 (adapterchanged, libpalacesameSHA7f1d1599…15e0fda8).
No solverqualificationyet; nextsamebuildtinycontrol/candidate aspreregistered.
EXP117 tinycontrolPASS16.532s40/42iter; candidateprocess0/fieldsPASSbutstrict
scopeauditFAIL: enters/mixed/release0, outsideoriginal18882. Thusno mixedPC
executionproof, NOT numericalqualification/performanceevidence. Rootfound
nativeApplyB/finalrelease envguards checkedoldflagonly. Fixedbothguards to
includecompensatedflag; regressionasserts bothnativepoints. Do notloosen audit.
EXP118 prereg: cachednativejobs2rebuild, freshsamebuildtinycontrol/candidate
exactEXP117flags/deadlines/newartifacts. PreservefailedEXP117candidateuntouched.
No needaddonrerun ifsharedkernelunchanged; onlynewnative2guardcode changed.
EXP118 actualtinyPCPASS: native8.582s/hash76f1edfc…d87c775d; control16.533s
40/42iter vs candidate16.629s40/42iter, no speedupclaim. Scope85/85/mixed3400/
outside3582/transpose7650/cache2entries13440Ballocated=freed/live0/release1.
Candidatecorrectedrawstop~8.46e-7/7.74e-7; initialraw~1.13e-6, no earlierFP32
~1e-3gap. Cannotattributecausalitysolelycompensation: shapeselectionalsonarrower.
RootindependentCSV S/VSWR/energy/powerandfieldcomparisonPASS; receipt
artifacts/m6-pc-compensated-tiny-root-analysis-20261021.json. No fullantennaclaim.
EXP119 prereg: samebuildmedium3.55/bothports control/candidate180s each, sameflags
andfrozenK; nativeunchanged/no rebuild, qualifycontrolvsM5medium andcandidatevs
samebuildcontrol. Largerbasis/costtest beforedecidingonW3; neverincreaseTol.
EXP119 rootindependentCSV/fields/raw/auditPASS: ΔS1.228e-10/VSWR1.484e-10/
energy1.308e-10/power1.243e-10. Both47/49iter/control98.577s/candidate98.546s,
no fulljobgainclaim. PCexclusive5.412→5.347s, coarse1.756→1.761s; ~70sL2
validationincludedidentically. Cgroup1.911→1.919GB notmemorysaving. Tables13440B
releasedcorrectly. Receipt artifacts/m6-pc-compensated-medium-root-analysis-20261021.json.
DecisionHOLD/no promotion/no automaticW3 for~12%microgain withoutnetjobbenefit.
NextM6.6 auditexistingUniform/Adaptive/PROM/reuse, localonly; M6/M7goalopen.
EXP117–119 checkpoint: finaladdonrecipe1.181s/sharedscreen14.184sPASS after
nativeguardfix. Rootverified strictactionCPU/linearity/range,currentbinary+
recipe andsamebuildidentityoftiny/mediumpairs.153pinnedtests/8shell/docschecker/
diffcheckPASS. SameLuna read-onlydocs-gardenPASS; rootreviewed exactBscope,
2nativeenvguards, modeexclusive/parser/cachebytes/cleanup andfailedcandidate
retained. Newnativehash76f1edfc…d87c775d7; originalbasisdefaultunchanged.
HOLD/nopromotion/W3NOTRUN; nextM6.6 audittocutwhole-sweepcost. M6/M7/W4/W5/
sweeps/medians/newgeometry stillOPEN, goalactive. No paidcompute/swap/appsclosed.

M6.6 audit@ef008b0: UniformalreadysharesK/C/M andInitialGuesstrue/E continuation;
excitation-majorlooprebuildsA/P/coarseanalysis+factor for eachport/f. Onefreq
M4reuse guarded; ComplexCuDSSSetOperatorclearsall. PROMexistingrealbasis
(2realvectors/complexsnapshot), HDMfielddiscrepancy training; online originalraw
residual/ourfielddiagnostichooksnotpresent, so notalreadyqualifiedROM. Source
receipt artifacts/m6-sweep-source-audit-20261021.json. W3onecomplexE179.5MB,
2per-porthistoryvectors359MBcapacity vs manyLUfactorsnotacceptable. PROM basis
at4samples/2ports up to16realvectors~1.436GB plusprojectors, notmeasuredpeak.
EXP120 prereg: generalizeexisting--port-setup-reuse tofrequency-majorbatch for
2lumpedports/fixedmesh/rank1, separateper-portpreviousE inRAM/VRAM; newnumeric
LU foreachf, sameLU onlybothRHSwithequalf. No multi-LUcache/precision/Tolchange.
Initialprototype no deferredpostprocessforNF>1 (explicitreject), noexternal
fieldseed/adaptive/wave/Floquet; measuredmemorybeforebigantenna. Minimizecode,
keepdefaultoldloop/onefreqreuse qualifiedpath. Strictauditexpects3builds/3reuse
andall6solves/fields for tiny3.30/3.55/3.80. Candidatevs samebuildcontrol,
60s each, coaxfields/probes+savefields butnoexpensiveanalyticalL2 doublequad.
Fallbackbuild/m6-sweep/pre-sweep-{native,manifest.json}. No paidcompute/swap/
appsclosing/cachecleanup. Fullsweep7pointsandantenna onlyaftercheapgate.
EXP120 implementation155pinnedtestsPASS; existingflag generalized, default
schedulepreserved. Nativehistoryguard/external/vizreject, extra2Ecapacity
onlywhenInitialGuessenabled; modeandfactoraudits requireexpectedorder/3builds/
6solves/historyrelease. No deferredmultiNF support claimed. Controlfirst,
rootreview thencandidate; no sharedTC/PCbasis changes. Cachedbuildjobs2.
EXP120 controlbuild8.727s/source31c23ac6…7a24cac; default6solvecomplete12.544s,
40/31/30/42/31/30iter. Root3CSVrows/allS-energy-probesfinite/12fieldfilesPASS,
actual6factorbuilds/6rawsuccesses. ExistingTEMhelperonefreqonly, nofalseclaim
sweepanalyticalgate; willaddperfreqCPUcheck aftercandidate. Candidate uses
samebuild3f2port andfieldreferenceexactcontrol,60sdeadline aspreregistered.
EXP120 rootPASS: tiny12.544→11.501s (~8.3%,singlepair),6→3actualfactorbuilds,
6completedrawsolves/12fields; per-portlogicalhistory2.851MB. IndependentCSV
ΔS4.345e-9/VSWR8.652e-9/energy1.118e-8/power8.346e-9. CPU TEMall3freq/bothports
RMS≤0.4497%,energy≤1.764e-5. Newhelperhandlesalignedmultirows; faulttests
missingfreq/mismatch/wrongBsign retained.155testsPASS. Receipt
artifacts/m6-sweep-tiny-root-analysis-20261021.json. Not antenna/globalpromotion.
EXP121 prereg: samebuildmedium3.30/3.55/3.80/bothports control/candidate180s each,
sameflags/no double-quadL2, savedwholefields/refcomparison+CPU TEM/RF/raw.
No native/depsrebuild. Separateper-porthistorylogicalcapacity26.526MB, notpeak.
Assessnettime/memory/all3CSRvalues before7point orW3. No paidcompute/swap.
EXP121 rootindependentall3freqPASS: medium53.570→45.344s (~15.4%,singlepair),
6→3factorbuilds, logicalhistory26.526MB, cgroup2.255→2.304GB (notmemorysaving).
ΔS3.198e-10/VSWR1.176e-10/energy1.933e-10/power2.989e-10,
fieldsE/B≤5.643e-8/9.511e-8, TEMsampleRMS≤0.4253%/energy≤1.506e-5.
CSRstructureidentical+3distinctvalueshashes butexactvaluefingerprintsnotidentical
acrosscontrol/candidate (alsotiny); no quantitativeCSRdiff/roundoff-onlyclaim.
Physicalconfig/buildidentity+sourceequal-frequencyreuse+frozenKpass retained.
Rootreceipt artifacts/m6-sweep-{tiny,medium}-root-analysis-20261021.json and
replayscript artifacts/m6-sweep-root-analysis.py. Outputsnapshotstiny22.56MB/
medium212.40MB perrun, ordinarysavedresultsnotworkinghistoryonSSD.
Full7freq/PROM/W3/newgeometry/mediansNOTRUN. Beforebigantenna: extendper-f
solverrelease/deferredmeasurement toavoidoldsolve+postprocesspeak, thenresourcegate.
EXP122 prereg regressiononly: oldonefreq tinyreuse+deferred flags/wholefields
vsM5tiny samegeometry/currentbuild60s; ensureflattenedschedule preservesoldpath.
No newnativebuild/precision/physicschange.
EXP122 oldonefreqreuse/deferredregressionPASS9.445s/40,42iter/1build+1reuse/
wholefields+memoryphases, finalraw8.48e-7/7.74e-7 afterretryinitial1.15e-6.
No newnativechanges afterqualifiedbuild31c23ac6…7a24cac; defaultfallthrough
preserved.155testsPASS includingaligned2freqanalyticphase/wrongBsign/missingrow,
modeguards/order/factors/seeds; no fullsweep7/antenna/defaultpromotion.
EXP120–122 checkpoint:155pinnedtests/8shell/docschecker/diffcheckPASS.
SameLuna read-onlydocs-gardenPASS; rootreviewed native(-w) lifetime/schedule/
per-porthistory, strictfactorcounts/modeguards/olddeferred path andTEMmultirows.
Currentnative31c23ac6…7a24cac bytesverified againstbothsamebuildpairs/rootKreceipts.
No globalpromotion/fullantenna/mediansclaim; prototypependingNF>1deferredpeakgate,
7points/PROM/heldout/generalization/W4/W5/finalpackage. GoalM6/M7remainOPEN.
No paidcompute/swap/appsclosed/depsrebuild; nativefallback/cachepreserved.

EXP123 prereg: extendexistingdefer tofrequency-majorreuseNF>1, withmandatory
energyrelease+finalsolverrelease/rank1/fixed2lumpedports/noexternal/viz/adaptive.
AfterP2eachf destroyksp/currentoperators/factors beforemeasuringP1/P2; keepK/C/M
untilfinalf. Recreatekspatnextf, addexplicitcumulative metadata counts so not
silentlyreportonlylast2solves. Originalprecision/Tol/fields/portphysicsunchanged.
Keep2historyE plusonetransientdeferredE (3vectorscapacity, independentofNF),
no many-LUcache/noSSDworkspace. W3capacity~538.5MBextraEvs359MBplainreuse,
measure netpeakbeforeclaimingsaving. No premature reuse ofdanglingoperators.
Strictfreqrelease/order+counteraudit andmemoryphasecounts per-f; finalrelease
oneexistingmarkerandPCcachecleanup onlyatend. Firsttiny3freqsamebuildplainreuse
control/candidate60seach, savedfields+TEM/K. Oldonefreqregressionretained.
Fallbackbuild/m6-sweep-deferred/pre-deferred-{native,manifest.json}. Cachedjobs2,
no paidcompute/swap/appsclosing/depscleanup.7points/mediumthenresourcegate.
EXP123 implementation156pinnedtestsPASS: optionalper-frequiredphasecounts,
strictstore→actualrelease→measure orderforeachf andcumulativecounts, missing/
wrongcounter/frequency/finalrelease negatives. Metadatahelper preservesexisting
SaveMetadata API andsumsreleasedsolvers. No tolerancechange. Ready cachedjobs2
build thenfreshsamebuildtinyplainreuse vsdeferredNF3, no doublequadL2.
EXP123 cachedbuild32.409s (driverheaderdependentTUs, no dependencyrebuild),
source037574a7…15bfc92c; tinycontrol11.508s/deferred11.538s, both40/40/31/31/30/30.
Actual3per-freleases/order+6cumulativesolves/202iterations metadataPASS,
wholefieldE/B≤1.562e-7/4.510e-8 andTEMallfreqPASS. Managedliveatpostprocessbegin
~241–259→97–113MB first2f; lifetimewindowonly, cgroup609.45→608.57MBnotnetclaim.
Histories+deferredbufferconstantNF. Rootinspectedphaseevents/counters/source,
originalrawchecksunchanged. No broadantenna/memorypromotion.
EXP124 prereg: medium3freq bothports samebuildplainreuse/deferred180s each,
referenceplaincontrolvsEXP121normalcontrol thennewcandidatevssamebuildcontrol.
No native/depsrebuild orfullantenna. Assessnetmemory/time/wholeK before7freq.
EXP124 mediumquality/metadata/lifetimePASS45.373→45.250s (singlenoisypair,
not timespeedup), both48/48/38/38/38/38iter. Cgroup2.307→2.264GB (~1.9%),
processGPU660.603→631.243MB notphysicalUVM. ΔS1.984e-10/VSWR8.156e-11/
energy1.393e-10/power2.509e-10, E/B≤3.996e-8/8.031e-8. Rootreplay receipts
artifacts/m6-sweep-deferred-{tiny,medium}-root-analysis-20261021.json.
EXP125 prereg: explicit --coax-sweep n78 selects[3.3..3.9 step0.1] runtimeonly,
no mesh/Tol/solverchange ornativebuild. Tiny7freq×2ports normalcontrol vs
frequencymajorreuse+deferred candidate60s each; baselinefullHDM14solves,
newcandidateall14originalraw/fields/TEM checked. Measurewholecost+metadata,
14→7factors/per-frelease, noPROM orsampling omission.156pinnedtestsPASS.
No expensive doublequadL2, paidcompute/swap/appsclosing. Medium7onlyafterrootgate.
EXP125 tiny7freq×2portsPASS18.675→15.598s (~16.5%,singlepair),14→7factorbuilds,
14completedrawsolves/28fieldfiles. AllfreqCPU TEM/K/wholefield+metadataPASS,
logicalhistory2.851MB/oneconstantdeferredE. Cgroup646.25→638.70MB notGPUphysical.
Root receipt artifacts/m6-sweep7-tiny-root-analysis-20261021.json. No antenna/
median/globalpromotion. FullHDMeverypoint, no approximatefrequencyinterpolation.
EXP126 prereg: samebuildmedium7freq×bothports normalfullcontrol vsreuse+deferred
candidate180seach; current--coax-sweep n78/runtimefreqoverride, frozenmesh/Tol.
Savefields/refcontrols plusCPU TEMall14, metadata14andper-frelease7/factors14→7.
No native/depsbuild/paidcompute/swap/appsclosing. Beforefullantennare-evaluate
memory/timegate vspriorverifiedM4deferredchunks, notunsafe80GBmonolithiccontrol.
EXP126 medium7freq×2portsPASS93.540→75.664s (~19.1%shorter,singlepair),14→7
factorbuilds,14fullHDMsolves/nointerpolation; candidateallraw/fields/metadata/
phase/order/historycleanupPASS. Cgroup2.515→2.535GB (+20.4MB), no netRAMsaving;
processGPU660.603→631.243MB notphysicalUVM. ΔS8.951e-9/VSWR8.180e-10/
energy1.373e-8/power1.043e-8, fieldsE/B≤5.945e-8/9.565e-8. CPU TEMall7freq/
bothports RMS≤0.4253%,energy≤1.506e-5. Root replay
artifacts/m6-sweep7-root-analysis.py +{tiny,medium}-root-analysis JSON; ordinary
snapshotoutputs49.74MBtiny/466.60MBmedium, no workinghistoryonSSD.
Deferredmedium3freq managedlivewindowfirst2f2.63–2.74→0.918–1.015GB, notprocess
peak/physicalresidency. Need antenna/UVM resourcegate; no M6/M7/globalpromotion.
Nextbaselineforlargecase mustalsofitmemory: allowfrequency-major(no setupreuse)
withsameper-fdeferredrelease forfaircontrol, then2fantenna/coldresourceestimate.
Avoidunsafe giantmonolithicnondeferredcontrol orsyntheticmergedreferences.
EXP127 prereg: oldonefreqtinyreuse/deferred regression currentbuild60s, fields
vsM5tiny+metadata2solves, then docs/rootreview/commit. No newnativebuild.

EXP127 wynik: singlefreq tiny reuse/deferred9,473s,40/42iter,2solves,
wholefields vsM5tiny +raw/setup/energyrelease/memorymarks/metadata PASS.
Artifact artifacts/m6-sweep-deferred-single-regression-20261021/result.json;
postpro/palace.json2solves/82iterations. Bez nowego nativebuilda.

EXP128 prereg: separate explicit --frequency-port-batch from optional equal-f
setupreuse; control and candidate share per-port history/per-fdeferred release,
only setupreuse differs. Existing reuse still implies batch forNF>1. Guard2ports/
rank1/fixed/uniform/restart1/noexternal-seed/viz; native adaptive guardadded.
Explicit --frequencies3.5 3.6 runtime Samples override leaves mesh/materials/Tol
unchanged; no fixturemutation. Firsttiny3freq two freshfactors vsreuse, saved
wholefields/TEM/raw/K,60seach. Then medium gate before W3. Fallback
build/m6-frequency-batch/pre-batch-{native,manifest.json}; jobs2cachedbuild,
no dependenciesrebuild/paidcompute/swap/appsclosing. Need nettime/memory before
antenna2f budget1800s and cgroup60GiB/available6GiB guard. No broadpromotion.

EXP128 wynik tiny3freq: fresh-factorfrequencymajor12,635→reuse11,574s,
6→3builds, identical40/40/31/31/30/30; allmetadata/release/history/raw/fieldsPASS.
RootCPU TEM/K PASS: ΔS1,654e-10/VSWR3,273e-10/energy3,583e-10/power3,297e-10,
E/B≤1,615e-7/4,576e-8. Cgroup612,819→608,367MB; singlepairnotpromotion.
Replay artifacts/m6-batch-root-analysis.py tiny, receiptm6-batch-tiny-root-analysis;
build8,640s currentnative.158testsPASS. No changedmesh/Tol/physics.
EXP129 prereg medium3freq samefrequencymajor/deferredhistory bothcontrols;
onlyreuseON vsOFF,180seach. Savefields/refEXP124plainreusecontrol thenfresh
samebuildcontrol; CPU TEMall6/raw/K +metadata/6→3factors, measuretime/cgroup.
Rootgatebefore2fantenna, no paidcompute/swap/appsclosing/newbuild.

EXP129 PASS medium3freq:53,464→45,324s (−15,22%,singlepair), identical48/48/38/
38/38/38,6→3builds. Cgroup2,293→2,226GB, notphysicalVRAM. RootCPU TEM/K/
fieldsPASS ΔS7,925e-11/VSWR8,743e-11/energy1,101e-10/power1,543e-10,
E/B≤3,878e-8/7,515e-8. Replay artifacts/m6-batch-root-analysis.py medium.
EXP130 prereg: actualW3T-Shaped medium fixedmesh, bothports3.5/3.6GHz, cold
firstf (no external seed), per-portwarmstartsecondf, FP32basis/FP64arith+
scaledFP32coarse/twoFP64corrections. Freshfactorfrequencymajorcontrol vsreuse,
sameper-fdeferredenergy/solverrelease. FourfullHDMsolves each, K64/Tol1e-6
unchanged,1800seach, cgroup60GiB/noswap/available6GiBguard. Runcontrolfirst;
onlyafterrootinspectionstartcandidate, notautomaticexpensivepair.
Prior W3mixed37371MBmanagedbeforefinalrelease,13348MBcuDSS; after9287MB,
postprocess25779MB. RetainingKCM estimates~14.7GB extraoverfinalpostprocessing,
plus3E538.5MB =>~41GBmanagedwindow, notpeakguarantee. Previouswholecgroup45.4GB,
currenthostavailable>79GiB; resources plausibleunder60GiBcap. IfFAILstopdiagnose,
no retryorappclosing. Save4E/Bnormaloutputs~1.68GB/run; referencefieldreadonce
atmeasurement, noworkspaceonSSD. Raw/frozenKfourrows and comparecandidate
wholefieldstonaturalcontrol; new3.6independentRFreference stillM7scope, notphysical
manufacturingvalidation. Controlold3.5P2CSVcrosscheckafterrun, nofake mergedref.

EXP130 freshfactorcontrolPASS996,519s/44,44,41,41iter; fourrawchecksfinalbelow
Tol1e-6 (two earliergapchecks exceedthreshold thenreliable restart; notaccepted
asfinal). Cgroup48,720GB;4factors/2per-frelease/metadata4/170iterationsPASS.
CPU CSV3.5bothports vsqualifiedM4: maxΔS1.859e-08/VSWR5.429e-08PASS,
notwholefield/new3.6independentreference. AllRFfields saved; controlwasnoseed.
Rootgate candidate sameconfig/currentnative, setupreuseonlydifference,
4fieldscompareenergy norm≤1%; S≤1e-3/VSWR≤.01/power-energy≤1e-3, originalraw.
Run1800s cap60GiB/noswap6GiBguard; noappsclosing/paidcompute/retry.

EXP130 candidatePASS915,924s vs996,519scontrol (−80,595s/−8,09%,onepair).
Both44/44/41/41iter;4→2factors (onlysame-freuse), analysis~17.0–17.2s/build,
factor2.69–4.77s. Savedanalysis+factor~39.6s; remainingdelta notassignedwithout
newprofile. Cgroup48,720→47,660GB (−2,18%onepair, notphysicalUVMresidency),
processGPU2,150GBboth notphysicalVRAMpeak. Actual3.5/3.6bothports finalraw
candidate[9.193e-7,6.735e-7,9.484e-7,8.389e-7],control≤9.600e-7PASS;
two intermediategapchecksrequired reliable restart, acceptedonlyafterfinalraw.
RootfrozenK ΔcomplexS1.698e-8/VSWR3.133e-8/relativeenergy4.775e-8/
portpower4.692e-9;28wholefieldcomparisons E/B≤4.146e-7/3.497e-8PASS.
Sameactualconfig/buildSHA3cd21b14…/medium/originalA/Tol verified, CPU CSV3.5
vspriorM4PASS; new3.6 lacksindependenttightreference/physicalvalidation. NoPROM/
interpolationandnoallbandclaim. Outputs2.017GB/run snapshots+results, notsolver
workspace; no swap/paidcompute/appclosing. Replay artifacts/m6-batch-antenna-
root-analysis.py andreceiptm6-batch-antenna-root-analysis-20261021.json.
CurrentcontrolnormalfreshfactorsbutalreadyM3/M5optimized, notupstreamFP64;
8.09%incremental gain mustnotbesummednaivelywithpriorpercentages.
Next cheaperalgorithmfilter: actualiterationsdominate916s, so symbolicanalysis
alone saves~17s peradditionalf atmostfor2freqcase (notwholePCspeedup).
AuditexistingPROM/rawfallback ormemoryboundedpredictor/recycling firstsmall;
extra per-port2-historypredictorwouldcost~359MBW3, measurebeforeimplementation.
No newlargerun untilcheapfilterwins. M6/M7/W4/W5/7freqantenna/median/newgeometry
stillOPEN; globaldefaultsunchanged, goalactive.

EXP130 closechunk:158Python/8shell/check.sh/diffcheckPASS; sameLuna read-only
docs-gardenPASS after rootnumericalreview. Native sourcehash/currentartifact
manifests match; no newnativebuildaftertests. Preserve source/config/fallback,
commitlocal only, no pushingupstream. CurrentM6goalactive; nextactioncheap
sweepalgorithmassessment, notanotherfullrunorclosure. No jobsleftscheduled.

EXP131 prereg: bounded per-port linear extrapolation of previous two E solutions:
x0=(1+r)E(f1)-rE(f0), r=(f2-f1)/(f1-f0). Onlyinitialguesschanges, originalFP64
A(f)rawresidualcomparestwo candidates; acceptifnewnorm<oldnorm, elsefallbackto
previousE. No interpolation/frequencyomission/Tolchange. Two Aapplies+norms each
portfromthirdf measuredinwholecost; mayloseevenwithfeweriterations.
Extraolderhistory2E~359MBW3plusone transientresidualE~179.5MBbeforeGMRES;
constantNF, noSSDworkspace. Explicit>=3f/batch2ports/InitialGuesstrue/fixed/
uniform/rank1/noexternalseed; exactolderlifetime/checkcounts/residualdecisionaudit.
Firsttiny7freqcontrolvsopt-in predictor60seach, savedfields+TEM/K/rawgate,
controlrefEXP125on; onlycheapPASS+netgainallowmedium180s, W3laterrootgate.
Fallbackbuild/m6-sweep-predictor/pre-predictor-{native,manifest.json}. Cachedjobs2,
no dependencyrebuild/paidcompute/swap/appsclosing. Defaultunchanged.
EXP131 implementation159PythonregressionsPASS: residualdecision/ratio/nonfinite/
missinghistory/invalidlifetime/malformedmarkers andphasecounts negativecontrols.
Nativepredictor hasoneephemeralresidual releasedbeforeGMRES, olderhistoriesfreed
atlastf. Strictaudit andoriginalfield/rawgatesrequiredforcompletion. Readybuild
thenexacttiny7pair; nochangesourcewhilerunning.

EXP131 tiny7freqPASS15,593→14,587s (−6,45%,onepair), sumiter412→266;
first4solves40/40/28/28unchanged, last10solves~27–28→13each.10predictoraccept/
0fallback, fullHDMall14/raw/fields/strictscopePASS. RootCPU TEM/Kpass:
ΔS2.286e-09/VSWR9.329e-10, olderhistory2,851MB;
cgroup640,315→665,866MB (+25.6MB, no netmemorysaving). Noantenna/generalpromotion.
EXP132 prereg: medium7freq samebuildcontrol vsonepredictorflag180seach,
referencequalifiedEXP126on thenfreshsamebuildcontrol. Exactall14fields/TEM/raw/K,
metadata/factor7/10checks/scope/constantmemory, rootgatebeforeanyfullantenna.
No native/depsbuild/paidcompute/swap/appsclosing/retry.

EXP132 medium7freq PASS75,139→67,970s (−9,54%onepair), sumiter510→406;
thirdf onward35/34→24each, all10checksaccept, originalinitialresidual~0.084–0.085×
previous-start. ExtraA/normchecks0,0962shostwindowtotal. RootTEM/K/fields/rawPASS
ΔS1,549e-8/VSWR2,987e-9/energy1,241e-8/power2,901e-8,E/B≤3,957e-8/1,317e-7.
Cgroup2,508→2,576GB (+68.1MB), olderhistory26.526MBlogical; notmemorysaving.
Native sourceSHA dc4ba1b2128b1b7959d17ba65e86fe106ad6827b1d1bc2ccc08a9dbd222ff69f.
EXP133 prereg rootgate actualW3 medium3.5/3.6/3.7GHzbothports, coldfirstf,
K64/Tol1e-6/right/directFP32basis/M5mixed/reuse/per-fdeferredrelease identical.
Onlypredictorflagchanged; controlnoexternalaccuracyref (new3.7), saveall6fields,
rootcrosscheckfirst2freqCSVvsEXP130 thencandidatewholefieldenergycomparison.
6fullHDMsolves/run,1800seach and60GiB/noswap/6GiBguard. Projectioncostestimate
prior2freq916s×1.5~1374s/run (notguarantee); memory48GBprior+~0.54GBpredictor
history/temporary, hostavailable~80GiB, noappclosing/paidcompute. Saveoutputs
~3GB/run ordinarysnapshots, no repeatedSSDworkspace. Controlfirst, rootgate
beforecandidate; no automaticexpensivepair/retry. Nativefallbackexecutionnotyet
observed(0of20checks); syntheticauditnegativesnotnativefallbackproof. No global
promotion/7freqantenna/median/newgeometry fromcheapfilters.

EXP133 controlPASS1312,606s/44,44,41,41,42,41iter,6rawfinal≤9,932e-7,
3builds+3reuse,6metadata/253iterations,12snapshotfiles. Cgroup48,876GB,
managedphasepeak43,166GB notphysicalVRAM; processcounter2,150GBnotresidency.
Rootfirst2freqCSVvsEXP130reuse ΔS1.933e-08/VSWR2.505e-08PASS;
new3.7independentwholefieldreferenceNOTRUN. Candidate rootgate1800s,
sameconfig/native/6fullHDM; onlypredictorflag+accuracyreferencechanges,
frozenK/power-energy/S/VSWR andall42regionfieldrowsrequired. No retry/appsclosing.

EXP133 predictorantenna assessmentREJECT/netgain:1312,606→1317,834s (+0,398%),
sumiter253→252; boththirdfchecksFALLBACK becauseinitialresidualP1 1,54363→2,14561,
P2 1,57244→2,11370. ActualnativefallbackthereforetestedandkeptpreviousE.
Predictorcheckwindow0,8559s; totaldelta5,228s notentirelyattributed. Cgroup
48,876→49,035GB (+159MB); managedphasepeak43,166→43,525GB; notphysicalUVM.
QualityPASS42regionrows E/B≤4,438e-7/1,327e-7, finalraw≤9,994e-7,
ΔS2,905e-8/VSWR5,006e-8/energy5,238e-8/power6,940e-9. Fullall6HDMsolve,
nofrequencyomission. Outputs2,858GB/run normaloutputs, nothotSSDworkspace.
Replay artifacts/m6-predictor-antenna-root-analysis.py, receipt...20261021.json.
No extrapolationpromotionfromcoax; defaultOFF, baselineM5/reusepreserved.
Followupnotnewlargerun: residual-minimizingcomplexprojectionofhistoricalfields
underCURRENT A(f), insteadoffixedfrequencyratio; originalRHS/stoppingtolerance
unchanged, recomputeimagesafterfchange. Needcheapindependentmathfilter+runtime
beforeW3. No promiseofiterationgainfromsmallinitialrawnorm. ExistingPROM source
andPETSc Fischerinitialguess reviewedasreference, no dependency/codeimport.
PostEXP133 guard-onlyfix includespredictorenv in nativeadaptive rejection even
withoutbatchenv; numericalpathunchanged. Newcachedbuild+tiny7regressionrequired;
fullW3dataremainexplicitlySHA dc4ba1b2..., no falselyrelabeledcurrentbinary.
EXP134 guard-only cachedbuild8.545s, source168bba06865626427102829030b38afc77fa3ee0700302c73b7ac06c59b7b651.
No numericalkernelchange; priorW3proofs remainoldSHA. Tiny7predictor regression
60s fields vsEXP131candidate, all14raw/K/10checks/metadata/history required.
159Python+8shell/check/diffPASS. SameLuna runthenread-onlydocs-gardenbeforecommit.

EXP134 tiny7guardregressionPASS14,591s/266iter,14raw/fields/TEM/checks/metadata
PASS;10accept0fallback. Rootactualbuildmanifestidentityverified, allfreqTEM
energy/RMSPASS, no fullW3relabeling. No livejobs.159Python/8shell/docscheck/diff
PASS; requiredsameLuna read-onlygardenbeforelocalcommit. Goal/M6active.

EXP131–134 read-onlysameLunagardenPASS, rootreview source/receipts/guards done;
no materialdiscrepancies.159Python+8shell/check/diffPASS, localcommitno upstream
push. Deferred/reuse baseline preserved; nextcheapmathematicalprojectionfilter,
notrepeatfailedlinearW3. GoalactiveM6, no live/scheduledGPUjobs.

EXP135 independentmathscreenPASS beforeintegration:96 nonsymmetriccomplex8×8
systems, scales1e-120/1/1e120, long-doubleoraclealphaerror≤7.448e-16,
stationarity≤4.959e-16.96wrongconjugation+96staleimagecontrolsdetected;
zero/nonfinite/overflow/|alpha|>1e6 guards, squarednormoverflowavoidedviaunitd.
Files palace/utils/sweepprojection.hpp +tools/experiments/sweep_projection_probe.cpp;
hostcompile+run0.36s, artifacts/m6-projection-math-20261021.json. ThisisnotGPU/
RF/warmstartspeedproof. No PETSc codeimport/dependency.
EXP136 prereg: --sweep-predictor projected opt-in, oldbareflag=>linear.
Compute r0=b-Aprev,d=A(prev-older) atCURRENTf, alpha=(unitd^H r0)/||d||,
finite/norm/capguard, fulloriginalAtrialresidual<baseline elsefallback.
3Aapplies/2temporaryE maxpercheck vs2/1linear; persistentolderhistorysame2E.
OriginalRHS/precision/Tol/fullsolveunchanged. Strictmode/alpha/conjugation-scalar/
operatorcount/actualdecisionaudit, cheap7freqtinycontrolvsprojected60seach,
thenmedium180s onlyrootPASS/netgain. No largeantennauntilqualifyleft2cheapgates.
Fallbackbuild/m6-projection/pre-projection-{native,manifest.json}. Cachedjobs2,
no paidcompute/swap/appsclosing/dependenciesrebuild. Need actualmeasurement,
smallrawstartnormaloneisnotguaranteediterationgain.

EXP136 tiny7freqPASS16.604→14.682s,
sumiter412→253,10projectedaccept/0fallback,
3actualAappliespercheck/strictalpha+history/raw/fields/TEMPASS. RootfrozenK
ΔS7.880e-10/VSWR4.009e-10, E/B≤1.663e-07/4.377e-07; projectioncheckwall0.0201s.
Onepairnotmedian/antenna; memorycounterwhole cgroup636.236→639.820MB.
EXP137 prereg medium7freqcontrol vsoneprojectedflag180seach, fieldsreference
priorEXP132control thenfreshsamebuildcontrol. All14originalraw/wholefields/TEM/K,
mode/alpha/3Achecks/lifetime/metadata, rootgatebeforeantenna. No newnativebuild/
paidcompute/swap/appsclosing/retry. Mathexperimentonlyprovescoefficientlogic,
notfield/iterationgain; need actualEMtest.

EXP137 medium7freqPASS75.124→66.858s,
sumiter509→386; rootparsedJSONcorrectssummary
arithmetic, not476/360.10projectedaccept/0fallback, originalraw/fields/TEMPASS.
ΔS9.520e-09/VSWR2.772e-09, E/B≤4.246e-08/1.251e-07; checkwall0.1479s.
Cgroup2,514→2,565GB; no netmemorysaving. OnepairnotM7median/antenna.
EXP138 prereg: actualW3same3.5/3.6/3.7GHzbothports, coldstart, K64/Tol1e-6/
M5mixed/reuse/deferred identical. ControlfullfieldsreferenceEXP133control,
thenrootgatecandidatecomplexprojectionvsfreshsamebuildcontrol; no changes
sourceafterbuildSHAe4b8abe0bc41372551079d149c4b2794183f11bb80168fcefb35bdf017146a1d.
6fullHDMsolve/run1800s,60GiBcap/noSwap/6GiBguard. Expectedpriorcontrol1313s,
no extrapolatedpromiseofgain. Priorpeak49GB+extra temporaryE~179.5MB belowcap,
currenthost~80GiBavailable. Saveordinaryoutputs~2.86GB/run, referenceI/Oonce
permeasurement, nothotdiskworkspace. No paidcompute/appsclosing/autoretry.
Originalraw/all42fieldrows/frozenK andcomplexalpha+rankcap+3Aauditrequired.

EXP138 controlPASS1574,144s/253iter (44/44/41/41/42/41), all42fields/raw/
metadata6/3factors/historyPASS; cgroup48,463GB. RootCSV3freqvsEXP133control
ΔS3.586e-08/VSWR5.508e-08PASS. Sameiterationsbutpriorcontrol1312,606s;
GMRESbegin intervals1085,682→1328,601s explain~243s of~262s delta, not
fieldreferenceI/O(mainfielddiagnostic15.6s). Causeunproven: do notattributeall
walltimedifferences toalgorithm, recordmedians/profilegateM7. CurrentGPUidle
counter2420MiB vs~1442MiBbefore; no appclosing, no physicalUVMresidencyclaim.
Candidate rootgate: samebuild/config/fielddiagnostics; onlyprojectedflag,
6fullHDM/originalraw/candidatealpha+finite/cap/3A/currentimageauditsrequired.
1800s cap60GiB/6GiBguard, no retry/paidcompute/appsclosing.

EXP138 candidateFAIL after1159,172s/5of6outer solves/211iterations;notaspeedup.
First4solves fields28rows, P13.7outerraw7,480e-7acceptedbutnotpostprocessed
(deferredwaitsP2). FirstP2coarseapplyat3.7 failed mixedcoarseFP64original
residual1,459992e-3 >1e-3. ThisisCOARSE-PCgate, notoriginalfullFEM1e-6rawgate.
OOMKilledfalse; cgroup49,082GBpartialpeaknotqualifiedmemorycomparison.
InitialprojectedrawactuallyimprovedP1 1,54363→0,56863 /P2 1,57244→0,55657
(ratios0,3684/0,3540). Complexalpha0,25970−0,61501i /0,28138−0,62833i;
strictmath/3Achecksvalid, butdoesnotqualifyfinishedRF/solverperformance.
P13.7only42→41iter; no evidenceenoughnetgain. Scalarprojectionitselfnotglobally
rejected, currentM5mixed2corrections+projectedantennaHOLD/FAIL/defaultOFF.
SourceMatrixCSRstructuresmatchbutvaluesfingerprintsacrossrunsdiffer; no
quantifiedCSRnorm/solecausattribution. NeedtargetedRHSreplaybeforeretry.
Rootstructuredfailureassessment artifacts/m6-projection-antenna-assessment.py
andJSON...20261021; preserve complete=false and fieldcomparisoncomplete=false.
No tolerancechange/noautoretry/no livejobs.
Nextresearchworkflowoptimizationbeforemorelargejobs: read-onlyfrequency-select
verifiedhistoryinput(singlecurrentf), preservephysicalmesh/material/port/deps
identityexceptexplicitSamplesselection, sourcefreqindexmap/provenance/bytes,
no fake completedresults oraccuracyreference. CanrecreateP2initialdirection
fromsaved3.5/3.6fieldsandactual3.7operator withoutre-solvingfirst4systems.
Referencefrequency-subsetverificationmustretainoriginalsourcecompletionand
fullinventory; subsetisview/provenance, notfabricatedsimulation. Dumpfailed
coarseRHS/CSRonlyifneededonceasdiagnosticresult, nohotdiskworkspace.
Thenconsiderfixed3IRvs2/FP64 atcheaprepro(originalgateunchanged); dynamic
innerstopping/fallbackwouldneedstationarity/FGMRESassessment, notsilentlyswitch
PCinsidecurrentGMRES. ExistingdefaultandqualifiedM5/reusecasespreserved.
M6/M7open, nexttargetedreplay+PROM/symbolicassessment, notanother45minpair.

EXP135–138 closechunk:160Python+8shell/check/diffPASS; root reviewed actual
coarsefailure site/containerOOMKilledfalse/currentmanifest/source. SameLuna
read-onlygarden foundonehistoricalnext-stepstale inM6checkpoint; rootcorrected
chronologytoEXP135–138 andrerandocscheck. Newheader+hostprobeincludedinlocal
commit, rawartifactsnotGit. No new paidcompute/swap/appsclosing/livejobs.
GoalactiveM6; failure/incomplete remainexplicit, qualifiedbaselinepreserved.

EXP139 prereg: explicit --initial-history completedSOURCE --history-frequencies
f0 f1 withonefuturetargetfrequency. Verifywholeoriginalsourcecompletion/config/
fullinventory+mesh/materials/physicalports/deps; onlyexplicitfrequencyand
excitationselectionallowed. Bytechecks/sourceindexmap/provenance saved,
read-onlymount; initialapproxnotaccuracyreference/nofakecompletedresults.
Native2sourceEreadsonceperport, sameFEspaceheader/GetTrueDofs, originalcurrentA
projection; releasesbothhistoryEafteroneouter solve; nohotdiskworkspace.
--frequencies nowsupportsonepoint; --frequency-port-batch stillrequires>=2.
162PythonregressionsPASS includingwrongphysics/headerbytes/unfinishedsource/
mode/pairs/map/lifetime/applies/ratio; no sourcefixturemutation.
Firstcachedbuildjobs2 then tiny3.8GHzbothports freshcontrolvsread-onlyhistory
3.6/3.7fromEXP136tiny7control,60seach andwholefields/TEM/raw(K)referencefresh.
Fullsourceverification~49.7MB, selectedhistoryE~5.7MB tiny; no statementofantenna
reproducibilityuntilactualrun. Later W3P2only3.7 source3.5/3.6,300s bound,
no repeatfirst4systems. FailedcoarseRHSnotcapturedpreviously; inputsource E and
CSRmaynotbitmatcholdrun, verifyquantities notclaimexactreproductionblindly.
Fallbackbuild/m6-history/pre-history-{native,manifest.json}; no dependency
rebuild/paidcompute/swap/appsclosing. Rootgateaftereachcase beforelarger.

EXP139 tiny singlef3.8history replayPASS: control9,457s/81iter, replay9,479s/
22iter; no netwholetimeclaim.2sourcef3.6/3.7 selectedindices3/4oforiginal7,
originalfullinventory/physics/provenancechecked. Raw/setup/defer/metadata/
historyrelease/predictorPASS; rootTEM/K E/B≤7,094e-7/4,300e-7,
ΔS1,714e-9/VSWR2,463e-9. Replayartifacts/m6-history-root-analysis.py tiny.
Nativebuild9,386s; rootmatchedbuild/controlconfig. Normalinputreadsnotworkspace.
Addedrunnerpreparation_seconds/end_to_end_seconds alongsideexistingelapsed;
sourcehash/inputverificationandcontainercreationoccurbeforeoldelapsedclock,
so reportseparatelyratherthanhidehistoryI/O. Olderresultsareunchangedandlack
thisextraend-to-endmeasurement; donotretroactivelyinferit. Pythononlynorebuild.
EXP140 prereg: medium3.8bothports freshcontrolvsverified3.6/3.7history from
EXP137control,180seach. Allfields/TEM/raw/K+bytephysics+modehistoryaudits,
end-to-end/preparation/nativeelapsed; rootgatebeforeonefreqW3P2repro300s.
No paidcompute/swap/appsclosing/autoexpensiveretry/newnativebuild.

EXP140 mediumsingle3.8bothports historyPASS:47/49→22/22iterations, native+cleanup
28,939→25,771s, preparation0,095→0,465s, end-to-end29,035→26,235s.
Onepairnotantenna/globalpromotion;4wholefieldE/B≤8,146e-8/1,280e-7,
ΔS1,533e-9/VSWR6,633e-10/TEM/rawPASS. Rootreplaym6-history-root-analysis.py.
EXP141 prereg diagnosticactualW3P2only3.7GHz, sourcecompletedEXP138control
f3.5/3.6 indices0/1, verifiedsourceinput2.521GB+selectedE358.999MBonce; source
bytes/physics/nativeFEspace matched, no artificialreference. OriginalTol1e-6,
currentA3.7/M5mixed2IR/K64/right/directstorage unchanged,300s bound60GiB/noSwap/
6GiBguard. No fieldreference(currentgoalreprofirstPC), savesnapshotsonlyif
successfulsolve. Coarse1e-3 gatekept, expectedfailureclassorcompletedsolve/
deadline recordedhonestly; sourcehistories/CSRmaydifferbitwisefromoldcandidate.
Do notclaimexactRHSreplayunlessproven. Nore-solvesfirst4systems, no auto retry/
paidcompute/appsclosing. Rootgatebeforefixed3IR/FP64assessment.

EXP141 diagnosticclassREPRODUCED in119,816s native/main+1,373sprep=121,189s
end-to-end, notcompletedRF. FirstcoarseP2at3.7failed1,474358e-3>1e-3,
outerGMRES0iterations/notconverged/completefalse; noOOM/hostdeadline.
Actualprojectedinitialraw0,5565711099vsold0,5565711229 (reldiff2.339e-08),
CSRstructuresmatch/valuesbitsdifferent; noclaimexactRHSorCSRidentity. Original
fullcandidatefailedafter1159s/first4solves; newdiagnosticavoidsre-solvingthem.
Assessment artifacts/m6-history-antenna-p2-20261021/diagnostic-assessment.json;
sourcebyte/provenance history-source.json, resultcompletefalsepreserved.
Nextfixed3IRassessmentscheduledonlyaftercommittingverifiedreproducer; no
adaptiveinnercountorlooseninggates. Userhardware/simulationgoalunchanged.
EXP142 prereg legacytiny7frequency-majorreuse/deferredbaseline regression60s
currentnative(nohistory/nopredictor), fields vsEXP136control.16sestimate,
all14raw/fields/TEM/setup/history/metadata, then docs/rootreview/localcommit.

EXP142 legacy7freq/2ports PASS exit0/completetrue,14raw≤9,920e-7,28fieldrows,
TEM/energy/setup/deferred/metadata/release PASS. Elapsed15,681s+prep0,103s=
end-to-end15,784s;412iter. Cgroup637468672B/GPUprocess631242752B, notphysicalUVM.
CurrentEXP139nativeSHA3ecd595dd0aa87454d29f3fec73e70371581ef9c1b2a17dcf5f0869d455fcb8e;
manifestfalse/globalqualificationunchanged. NewinputreplayisnotanRFreference.

EXP139–142 closechunk:162Python+8shell+docscheck/diffPASS; sameLuna read-only
docs-garden identifiedone stalefuture replaylineM6, rootfixedchronology.
Verifiedcurrentnative/legacyTEM/raw28fields; localcommit only, no paidcompute.
GoalactiveM6. Nextfixed3IRtiny/mediumgatebeforetargetedW3, originalfailpreserved.

EXP143 prereg fixedIRopt-in: --native-coarse-corrections integer2..4 with
--native-coarse-fp32 only, default2 unchanged. Native fixedcount perrun, no
adaptiveearlyexit/fallback; coarse1e-3/outer1e-6 unchanged. Both precision
markers and command/env count audited;163PythonPASS. Tiny3,8bothports verified
source3,6/3,7 control2IR vs3IR, then mediumsame afterrootgate, currentbuildboth.
Sameconfig/mesh/currentA, fields/TEM/K/raw;60stiny/180smedium, 60GiBnoSwap/6GiBguard.
UseEXP139/140controls asfieldreferences, not historyasreference. Fixed3maycost
more; no speedclaim from feweriterations or successclass alone. W3P2only3,7
historysourceEXP138 aftercoaxPASS,600s planned forsetup~120s plusfulliterations;
no repeatfirst4systems/no newfullsweepyet. Cachedbuildjobs2; fallback
build/m6-fixed-ir/pre-fixed-ir-{native,manifest.json}. No depsrebuild/cloud.

EXP143 tinyfixed2vs3PASS samecurrentbuild/config/historyf3,6/3,7→3,8bothports,
22/22outeriterations,24/24coarsesolves. Coarserelativemax8,23e-7→2,76e-7,
no loosenedgates. RootTEM/raw/K/fields/countauditPASS; onepairtime10,590→9,477s
end-to-end notstatisticalspeedproof. Cachednative12,05s,163PythonPASS.
EXP144 prereg samepairmedium180seach, fieldrefEXP140coldcontrol, rootgate
beforeW3P2/3,7 singlefrequencyhistory600s. No extra hypotheses/defaultchanges.

EXP144 mediumfixed2vs3PASS:44/44iterations,46coarsesolves, originalcoarse
relative9,32e-5→2,46e-5. Raw/wholefields/TEM/frozenK/count/auditsPASS.
End-to-end26,488→26,220s onepair/negligibledelta, notnetgainclaim.
EXP145 prereg W3P2only3,7GHz fixed3 withsameverifiedhistoryasEXP141,600s
limitsetup~120s+iterations, nofieldreference(no single-pointmatchingreferenceyet).
Ifcomplete comparetargetfrequencyfields tocompleteEXP138control viaexplicit
indexmap withinputphysics/hash checks; do notfakeconfigs/sourcecompletion.
Ifcoarsegatefails preserveFAIL; no automaticcount4/tolerancechange.

EXP145 executionPASS W3P2/3,7fixed3:40iter/raw7,959879e-7/coarse8,07e-4<1e-3.
Elapsed389,903s+prep2,498s=end-to-end392,401s; cgroup45,972GB (reportedGPU2GiB
notphysicalUVM). No fieldreference, so notyetwholefieldqualification orspeedup.
EXP146 prereg fullthreefrequencies3,5/3,6/3,7bothports projectedfixed3, original
EXP138controlcompleteasfieldreference, coldstart/noexternalhistory.1800s cap
predeclared: sixsolves, oldcontrol1574s, per-fdeferredrelease+reuse/K64/Tol1e-6.
Newfixed3mechanism already passedtiny/medium and failingP2diagnostic; thisis
notblindoldretry. Requireall6raw/42fields/RFenergy/counts/scopePASS; no partial
speedclaim or tolerancechange. ExistingEXP138partialFAIL retained. Compare
accuracytooldcontrol; crossbuildtime notisolatednewmechanisms, no netgainproof.
Afterassessment closeM6fixedIRchunk/docs, evaluatebudgetforfinalqualification.

EXP146 firstdispatch NOTRUN: runner rejected omitted --both-ports before
solver/outputallocation (fixturedefaultP2). Explicit --both-ports corrects
requestedtwo-excitation scope; no numericalretry or physics/tolerancechange.

EXP146 fullsweepFAILdeadline1800s/exit255/noOOM,5of6solves/209iterations
[44,43,41,40,41],5raw≤9,802155e-7,28fieldsatfirst2fonly.3,7P1completed,
P2stillrunningatdeadline, no coarsefailuremessage; finalcleanup/countaudits
falseexpected. Do notpromotefixed3/projectedantenna speedorfullquality.
EXP145singleP2executionPASS≠wholefieldqualification. Keepfixed2default/FP64
fallback; no blindcount4/deadlineextension. Rootassessment
artifacts/m6-fixed-ir-antenna-assessment-20261021.json.
EXP147 prereg currentnative legacytiny7freq2ports default2(noexplicitcount),
nohistory/predictor, fieldreferenceEXP136control;60s, allTEM/raw/28fields.
Then docs-garden/rootcommitfixedIRboundedassessment; M6/M7remainopen.

EXP147 legacydefault2currentnativePASS:14raw≤9,919892e-7/28fields/TEM/energy/
setup/deferred/count2/cleanupPASS, elapsed16,573/prep0,132/end-to-end16,704s.
Actualartifact artifacts/m6-fixed-ir-legacy-regression-20261021 (Lunafinal
linktypo namedoldhistorydirectory; rootverifiedactualnewartifactandmanifest).
CurrentnativeSHA4fc32f086badb3e4415f0944cc31d0deb99f0242999aed8992c48c18c5521ebc.
FixedIRassessment bounded/closedwithoutpromotion, default2andFP64fallbackkept.
M6.6symbolic/recycling/PROMremainingbeforeM7; no wholegoalcompletion.

EXP143–147 closechunk163Python+8shell+docscheck/diffPASS; sameLunaread-only
garden finallyconfirmedcorrectEXP147folder/artifact (initialfalsealarmread
oldEXP142folder, rootcrosscheckedbothsource/resultSHAs). No docsnumbercorrection
needed. Localcommit only/no push; no livejobs. Default2/FP64fallbackretained,
fixed3fullsweepFAIL andfieldlimitsstayvisible. GoalactiveM6.

EXP148 source/budget/prereg: symbolicreuse currentW3complete3fanalysis
17,136+17,331+17,273=51,740s of1574,144s. Ideal skip2lateranalyses saves
34,604s(~2,20%) upperboundbeforecachecost, notmeasuredspeedup. NVIDIAcuDSS
Tipsandtricks docs confirm analysisreuse/refactorization forunchangedpattern;
currentSetOperatorClear and per-f deferred release destroycontext. Retaining
LU throughpostprocess mayviolate existingpeakbenefit; no blindnumericfactorreuse.
Fullrecyclingrequires retaineddirectionsandcurrentAimages;4+4complexE adds
1,436GB (179499584B each), orthogonalization/update/Aactions extra. Existing
GMRES<64iter so restartdeflationbenefit not demonstrated; no blanketimpossibility.
Priorityremainingfilter existingPROMwithheldoutoriginalraw, notnewFEMengine.
New isolatedtools/experiments/prom_sweep.py copiesverifiedcompletedcoax7f
reference; onlyAdaptiveTol.01/AdaptiveMaxSamples2 changed. FourHDMsolves
(twoendpointsperport),14online originalfullA residuals,10heldout; no fallback
orloweredtol. NativeOriginalRelativeResidualbuildsfullA/b, rawgate1e-6;
separatefieldenergycomparisonsallsamples; failedqualitynotcomplete. Readonly
reference, measuredordinaryIO, nohotdiskworkspace;165PythonPASS. Native
flags defaultOFF, adaptive skipestimator respects existingexplicitenvoptin.
First tiny60s then medium180sonlyafterrootassessment; neitherantennaqualification
norautomaticpromotion. Cachejobs2/fallbackbuild/m6-prom/pre-prom-native.

EXP148 tinyPROM2endpointsperport: executionPASS4HDM/14online/10heldout/28fields
PASS, but originalrawFAIL max2,286513e-6>1e-6; also trainingmax1,052263e-6
vsHDMraw≤9,6714e-7. Completefalse kept. E/B≤3,8722e-7/9,8918e-7; TEMsamples
≤0,449754%. Elapsed12,609/end-to-end12,684s, noqualifiedspeedupfromfailedquality.
BuildfirstattemptcompileFAIL(noSpaceOperator.Initialize), rootremovedinvalid
call andrestrictedresidualhelperlumpedports; cachedcorrectbuild19,360s.
EXP149 prereg tinyPROM3samples/port withexplicitHDMTol1e-8 (tighter than
source1e-6, originalonlinegateunchanged1e-6),60s. Addressesbothinterpolation
spanandtrainingerrorfloor; no isolatedcauseattribution. Newoptionrejects
loosertolerance/NaN/types,165testsPASS. No rebuildneeded(Pythononly).
Mediumonlyafterquality/TEM/KrootPASS; no antenna run aftertinyFAIL.

EXP149 tinyPROM3/offlineTol1e-8PASS:6HDM/14online/10heldout, dimension12,
rawmax3,09e-8/offline≤9,14e-9. Wholefields28rows/TEM/frozenRFenergyrootPASS,
receipt/replayartifacts/m6-prom-root-analysis.py tiny.14,793elapsed/14,872
end-to-end,cgroup607113216B. Differentbuild/policyvsoldreference, noisolated
speedup/antenna/medianclaim.
EXP150 prereg samePROM3tightmedium7freq180s, sourceEXP137mediumuniformcontrol;
all14originalraw/28fields/TEM/RFenergy, no newnativebuild/noantennauntilgate.

EXP150 mediumPROM3tight executionPASS6HDM/14online/dim12, but rawFAIL
max2,2231e-6 despiteoffline≤7,2605e-9; fields28rowsPASS.74,683elapsed/75,112
end-to-end,cgroup3,158GB. Notantenna/globalquality orspeedpass.
EXP151 prereg lastboundedPROM4/offline1e-8 medium180s,8HDMvs14full; projection
span hypothesis notloosening. Estimatedcost~90–100s vsoldbest7f~75s, so even
qualityPASSwouldnotalonejustifyantenna/netpromotion. Freezealgorithm/sample
budget here; ifnofrozenquality+usefulnetcost stopcurrentPROMimplementation
assessment, noautomatic5/6samplesorantenna. Currentnativeunchanged.

EXP151 PROM4mediumPASS rawmax2,5762e-8/offline≤7,3037e-9,8HDM/dim16/14online.
Heldout10 (actualadditionalgreedysamplesareoffgrid); Lunareportcount8training/
6heldoutwasincorrect, rootverifiednativeflags/provenance and auditheld_out10. All28fieldrows/TEM/RFenergyPASS, rootreceipt
artifacts/m6-prom-medium-four-root-analysis-20261021.json. Elapsed90,480/
end-to-end90,729s/cgroup2,807GB; nofastclaim fromfewerfullsolves.
EXP152 prereg currentbuildbestuniformmedium7f(defaultmixed2IR/reuse/deferred),
180s, fieldreferenceEXP137control; sametargetphysics/raw/fields/TEM/RFenergy.
ThiscontrolswholechosenstrategyvsPROM4, notisolatedPROMorcoarseprecision.
OnlyonepairnotM7median; decidePROMpromotionassessmentscopebeforeantenna.

EXP152 currentbuildbestuniformPASS14raw/28fields/TEM/energy,509iter,
elapsed75,455/end-to-end75,752s/cgroup2,512GB. SamebuildPROM4 90,729s/
2,807GB means+19,77%time/+11,77%cgroup, onepairnotmedian/causeproof.
Wholechosenstrategy comparison: PROMFP64coarse+HDM1e-8 vsuniformmixed2IR/
reuse/deferred; do notattributealldeltatoPROMalone. REJECTpromotioncurrentPROM
for7f; no antennarun/new5samples. SourceSHAa6ec732f11cc7fe920365ba2aae354b68fe97e81f732d5afd4659ed5187c3338.
Rootreceiptartifacts/m6-prom-strategy-comparison-20261021.json; sourcecode
researchprobeandnegative/positiveaudits preserved. Full7factualantenna plus
W4/W5/medians/newgeometry/package remainnotdone; goalM6active.

EXP148–152 closechunk:165Python+8shell/check/diffPASS; sameLunaread-only
garden agrees source/actualofflinevsheldout/limits. Rootverifiedcurrentbuild
normalpathEXP152 too. No depsrebuild/cloud/swap/appsclosing. Localcommitonly,
M6active, no liveGPUjobs. Next actualsevenfreqantenna qualification with
explicitboundedchunksandaggregatecost; no fakeglobalpromotion fromcoax.

EXP153 prereg actualantenna7pointboundedqualificationstarts3,3GHzbothports.
Reference fullFP64basis/arithmetic/nativeFP64complexcoarse/cold/noportreuse,
RIGHT/K64/Tol1e-6/mediumOrder2/frozenmesh; defer+energy/finalrelease inboth
strategies.1800s/60GiBnoSwap/6GiBguard. Hostavailable78,62GiB/GPU1,775MiB
observedbefore dispatch, userappsuntouched. Root validatedsinglefrequency
bothport/deferredconfigbeforeGPU. No oldseed/PROM/predictor.
Aftercomplete2raw/fullfieldinventory, rootgate then samebuildcandidate
FP32directbasis/scaledFP32coarse/default2IR/equalfrequencysetupreuse against
thisFP64reference. IfreferenceFAIL preserveanddiagnose,noautomaticretry.
Sevenpoints3,3..3,9/0,1 toqualifybothports inindependentfrequencychunks; report
sumallsetup/IO/fulltimes, notmonolithic7f orcross-chunkwarmstartproof. Prior
2freqW3sharing/historyproofseparate. ThisqualificationdoesnotreplaceW4/W5/
medians/newgeometry/package. No paidcompute/swap/appsclosing/tolerancechange.

EXP153 referencePASS3,3GHzbothports coldFP64basis/coarse:43/44iterations,
2originalraw≤9,50e-7,4verifiedE/Bsnapshots,2freshsetups,nativeFP64/cleanup/
energydeferPASS/noOOM. Elapsed752,180/end-to-end752,534s, cgroup60,692GB
(notreportedprocessGPU2GiBphysicalresidency). Rootsource/config/bytes/native
precision/gates independentlychecked, root-reference-check.json saved.
EXP154 prereg samebuild/configphysics candidate3,3bothports directFP32basis/
scaledFP32coarse/default2IR/portsetupreuse,1800s. AgainstactualEXP153fullFP64
fieldreference, allraw/fields7regionsperport/RFenergyfrozenK. No externalseed/
predictor/PROM/tolerancechange. Rootgatebeforeanynextfrequency.

EXP154 candidatePASS3,3bothports:44/45iter/raw≤8,19e-7/coarse≤1,30e-4,
1build+1reuse,14wholefieldrowsPASS. Samebuild/config/mesh/source/fullinventory
verifiedroot, RFenergymaxΔS1,1852e-8/VSWR3,8873e-8/relativeenergy5,9247e-8/
power5,0239e-9, E/B≤1,2978e-7/1,1365e-7. End-to-end549,512s vsFP64ref
752,534s (−26,98%),cgroup46,357vs60,692GB (−23,62%). Combinedflags/cold
onepair notmedian ormonolithicsweep/physicalmeasurementproof. Raw/fields
provenancepreserved rootreceipt/replaym6-qualified-root-analysis.py330.
Qualificationmatrix docs/milestones/antenna-sweep-qualification.md,6points
NOTRUN; next3,4fullFP64reference thenrootgate/candidate. No newhypotheses.
GoalM6active, W4/W5/medians/newgeometry/package remainrequired.

EXP153–154 docs-onlyclosechunk: sameLunaread-onlygarden/check/diffPASS
againstactualnewqualificationartifacts. MatchedfullFP64referenceandcombined
candidateprovefirst3,3point only. Localcommit, no newnativebuild; cached
sourceSHAunchangeda6ec732f...187c3338. No GPUjobsleft; nextreference3,4
thenrootgate/candidate, no newresearchdetour. GoalM6active.

EXP155 prereg actualqualification3,4GHzbothports reference. Samecurrentnative
sourcea6ec732f...187c3338 checked/notrebuilt; noliveGPUjob. FullFP64basis/
arithmetic/nativecomplexFP64coarse,cold/noportreuse,RIGHT/K64/Tol1e-6,
mediumfrozenmesh,defer/energy/finalrelease unchanged.1800s/60GiBnoSwap/6GiBguard.
Rootgate2raw/inventory/source/config/setupbeforeEXP156candidate. Sameprotocol
asEXP153–154, no predictor/PROM/seed/cloud/appclosing/tolerancechange.
Onepoint7pointmatrix, totalsetup/IOcostcounted, M6active.

EXP1553,4referencePASS43/44iter/2raw≤9,43e-7/4verifiedsnapshots/nativeFP64/
2builds/cleanup, samebuildsource. End-to-end696,17s/cgroup60,687GB, notphysical
GPUresidency. Rootbyte/config/precision/raw/setupgatePASS savedreceipt.
EXP156 prereg exactsame3,4bothports combinedcandidate(default2IR/reuse/
FP32storage) vsverifiedEXP155fieldreference;1800s andsamefrozengates.
No newcode/build/seed/predictor/PROM/retry/tolerancerelaxation.

EXP1563,4candidatePASS44/45iter/2raw≤8,11e-7/coarse≤1,20e-4,1build+reuse,
14fieldsPASS. RootfrozenRFenergy source/config/inventory verificationPASS,
maxΔS8,135946e-9/VSWR2,808826e-8/relativeenergy8,010623e-8/power3,439677e-9.
Combinedchosenstrategy−27,0876%time/−23,6095%cgroup onepair (notmedian).
Addedversionedtools/qualify_antenna.py: read-onlysinglef/bothportsfullFP64
vscombinedprotocol, strictsource/native/config/inventory/raw/CSVunits/order/
fields/frozenK, explicitoutputreceipt; noexecution/promotion.168PythonPASS
includingNaN/missing/width/phasewrap/zeroenergy/nonpassiveVSWR/incomplete/config
negativecontrols. Recheckedboth3,3and3,4 usingversionedtool, sameproof/no new
nativebuild. LocalrootreceiptsretainwrittenartifactbytesandanalysisSHA.
EXP157 prereg3,5GHzbothports fullFP64reference sameasEXP155(1800s/60GiB
noSwap/6GiBguard/medium/K64/Tol1e-6/cold/deferenergyrelease). Thisnewcoldfull
FP64pairnotrelabelingoldseededW3. RootgatebeforeEXP158candidate. No detour.

EXP1573,5referencePASS44/44iter/2raw≤9,50e-7/4verifiedfields/nativeFP64/
2freshbuilds,rootconfig/source/inventory/rawchecksPASS. End-to-end736,49s/
cgroup60,703GB. EXP158 preregsame3,5bothports combinedcandidatevsactual
EXP157reference, default2IR/FP32direct/reuse same1800s guardsandfrozenK.
No seed/predictor/PROM/tolerancechange/build; rootgatebefore3,6.

EXP1583,5combinedcandidatePASS44/45iter/2raw≤9,47e-7/coarse≤1,06e-4/
14fields/setup1build+reuse. Rootversionedqualifier fullRFenergy/raw/source
checksPASS; coldpaircostandmemory receiptsaved, notoldseededW3comparison.
EXP159 prereg3,6GHzbothports fullFP64reference same frozenprotocol/1800s
60GiBnoSwap/6GiBguard, nativeunchanged,no paidcompute/appsclosing.
RootgatebeforeEXP160combinedcandidate. GoalM6active3of7pointsdone.

EXP1593,6FP64referencePASS44/45iter/raw≤8,553e-7/4verifiedsnapshots/
2freshbuilds/cleanup; source/config/inventoryrootPASS. End-to-end738,78s/
cgroup60,870GB. EXP160 preregsame3,6bothports combinedcandidatevsEXP159
fullFP64reference, default2IR/reuse/directFP32; same1800sguards/frozenK.
No newbuild/seed/predictor/PROM/physicschange; rootgatebefore3,7.

EXP1603,6combinedcandidatePASS45/46iter/raw≤7,358e-7/14fields/1build+reuse.
Reliablecheckrestarts recorded(notignored); strictfinalraw/frozenRFenergy/
fieldsvsFP64PASS inrootversionedreceipt. Smaller timebenefit thanprevious
points; do notpromiseconstant27%speedup. Allactualcosts retained.
EXP161 prereg3,7GHzbothports fullFP64reference same1800sprotocol, noseed/
predictor/PROM. Coldsinglepoint reference isdistinctfromoldpartialprojection
sweep; no replayofoldfailedmechanism. RootgatebeforeEXP162candidate.

EXP1613,7FP64referencePASS45/45iter/2raw≤9,883e-7/4verifiedsnapshots/
2freshbuilds, source/config/inventoryrootPASS. End-to-end739,63s/cgroup
60,865GB. EXP162 preregsame3,7bothports default2IR/FP32direct/reuse candidate
vsactualEXP161,1800s andfrozenK/guards. No predictor/PROM/seed/3IR; ifFAIL
preserveanddiagnose, notautomaticretry orrelabeloldprojectionresults.

EXP1623,7combinedcandidatePASS45/46iter/2raw≤8,961e-7/14fields/
1build+reuse. Reliablecheckrestart costpreserved; no oldprojectionmechanism.
Rootversionedqualifier fullRFenergy/config/source/inventoryPASS, receipt
saved. Fiveofsevenpointsqualified, singlepairsnotmedians/globalpromotion.
EXP163 prereg3,8GHzbothports fullFP64reference same1800s protocol, medium
K64/Tol1e-6/cold/deferredenergyrelease/60GiBnoSwap/6GiBguard. Rootgatebefore
EXP164combinedcandidate. No build/seed/PROM/predictor/newhypothesis.

EXP1633,8FP64referencePASS45/46iter/raw≤9,113e-7/4verifiedsnapshots/
2freshbuilds, source/config/inventoryrootPASS. End-to-end736,47s/cgroup
61,048GB (within60GiBcap), no userappsclosed. EXP164 preregsame3,8bothports
combinedcandidate/default2IR/reuse/directFP32 vsactualEXP163;1800sandfrozenK.
UseraskedTF/TCstatusduringrun; answerednoqualifiedTCgain, TF32requested
probe slowerthanFP32, currentwinsstorage/factor/reuse, goalnotreplaced.

EXP1643,8combinedcandidatePASS46/47iter/raw≤7,713e-7/14fields/setup1+reuse,
reliablechecks preserved. RootallfrozenRFenergy/raw/source/inventoryPASS;
sixofsevenpoints qualifiedsinglepairs, variationnotstatisticalpromotion.
EXP165 prereg3,9GHzbothportsfullFP64reference lastsevenpointchunk; same
1800s/60GiBnoSwap/6GiBguard/frozenmedium/K64/Tol1e-6/cold/defer.3,9outside
n78 butexplicitbenchpoint. RootgatebeforeEXP166combinedcandidate; no new
code/build/PROM/predictor/seed/retry. GoalstillM6untilfinalclosureaudit.

EXP1653,9FP64referencePASS46/47iter/raw≤7,941e-7/4verifiedsnapshots/
2freshbuilds/config/source/inventoryrootPASS. End-to-end723,95s/cgroup
61,224GB within60GiBcap. EXP166 prereglast3,9combinedcandidate default2IR/
reuse/FP32directvsactualEXP165, same1800s/frozenK. No autoretuning; after
rootPASS aggregateallsevenfullcost/quality thenauditM6closurebeforeM7.

EXP1663,9combinedcandidatePASS46/47iter/2raw≤9,499e-7/14fields/1build+reuse.
RootallfrozenRFenergy/bytes/source/configPASS. Sevenpointssummary rechecks
alloriginalpairs withversionedqualifier, commonbuild/mesh/configbeyondf,
98fieldrowsPASS. Sum5124,017→4043,095s/−21,095%, maxcgroup61,224→46,637GB/
−23,825%,625→635iter,14→7builds. Allperchunksetup/IO/cleanup included;
notmonolithic7fsweep ormedian. Ordinaryvalidationartifacts~16,48GBonce,
notdiskhotworkspace.170PythonPASS.
M6closureauditfoundexplicitremainingPLANcuBLASLtresearchandM6.3TCproof;
KEEPActiveM6, M6.6assessmentonlycomplete. SourceTF32requestedprobe uses
cublasGemmEx/FAST_TF32, no provenTCinstructions; ncu notinPATH; readonly
/proc/driver/nvidia/params RmProfilingAdminOnly=1. No permission/driverchange.
Nextlibraryresearch/counterorinstructionpathbeforeM7; do not inventTCwin
fromcombinedprecision/reuse. No newnativebuildneededforPythonqualifier.

EXP155–166 closechunk170Python+8shell/check/diffPASS; sameLuna read-only
docs-garden verifiedactualsevenpointsummary anduntrackedqualifier/tests, no
materialissues. Rootsource/allreceipts/config/mesh/native/RFenergy/98fields
independentchecksPASS. Localcommitonly/no push, no newnativebuild/cloud/
swap/appsclosing. No liveGPUjobsleft. M6.6 assessedcomplete, ActiveM6.3/
cuBLASLtresearch; nextchecklibraryprimarydocs/version/license andbounded
TCinstruction/counterpathwithoutglobaldriverpermissionchanges, thenM7.
Goalnotcomplete: W4/W5/threepairedmedians/newgeometry/package stillrequired.

## EXP167 prereg — cuBLASLt checked TF32 heuristic, isolated basis only

Previous goal turn was status-only/no progress; current work resumes the remaining
M6.3 requirement. Optional `--lt` in the cached two-TU probe, no native Palace
change/rebuild. ND2 P20/Q14, INTERP/CURL, forward/transpose/add, N257 and131071
first; if execution/independent CPU/layout/canary controls pass, identical seven-size
ladder through actualN1601320. Up to8 cuBLASLt heuristics, first checked algorithm
with tensor-op and TF32 input metadata, actual pointer alignments, shared64MiB
workspace ceiling; plan setup recorded separately, pack/GEMM/unpack included in
per-apply timing. Unsupported algorithms remain explicit negative results; no
TF32 precision promotion, full-antenna run or TC execution claim from metadata.
Bound120s/run,6GiB cgroup/no swap/local only. Root prepares; sameLuna babysits.
Primary source: CUDA12.9.1 cuBLAS docs (`cublasLtMatmulAlgoGetHeuristic`,
AlgoCheck, numerical implementation flags and alignment preferences),
https://docs.nvidia.com/cuda/archive/12.9.1/cublas/index.html . Existing runtime
library, no new dependency or CUTLASS; NVIDIA CUDA Toolkit proprietary license,
existing pinned12.9.1 image. Execution/instruction profiling remains separate.

EXP167 preflight NOT RUN: sameLuna exact screen command refused before
artifact creation due freeVRAM<2048MiB. Root read-only nvidia-smi observed
1120MiB free/98% GPU use, user strata process12330MiB; hostavailable8.7GiB,
swap0. No process killed, no retry/guard reduction. User explicitly will
signal when GPU freed. Cached probe build PASS9.656s after argument guard;
native solver/dependencies unchanged. Root source/metadata validator tests
cover incorrect algorithm flags/check/workspace/selection and unsupported
execution. Await GPU for numerical/runtime evidence; no TC/speedup claim.
Research and exact resumption commands: docs/cublaslt-assessment.md.

EXP167 checkpoint: final cached probe build4.606s/binarySHA
1ae0ebd71d1cb3eb4de600451adbb0924aa74d1df8f9d8a55ccb730d61f98398; check verifies recipe/native identity.
171Python tests/8shell/docschecker/diff PASS. SameLuna read-only docs-garden
PASS, root reviewed diff and first-success heuristic state guard. Local commit
contains experimental probe/research only; numerical execution/instruction
proof remain NOT RUN. Await explicit user signal before GPU test; no active
GPU simulation handle or paid resource. Goal remains M6, not complete.

EXP167 resumed after explicit user authorization to unload local strata.
Root used its authenticated /unload API (HTTP200/unloaded), retained serving
process/config; no forced kill. GPU13693MiB free/0%, host78GiB available/no swap.
SameLuna screen executed8.98s/exit0; root strict12-row validationPASS,
all original/FP64layout/independentCPU/canaries PASS. Lt supported12/12,
algorithm23/implflags262658, maxrelativeL2=3.3063933575848534e-4,
maxscaled=6.372e-4; allLt actionfilter2e-3PASS. Screen only, not RF/TC proof.
AtN131071 Lt0.190–0.224ms vsnative0.297–0.337ms; forward fused~0.118ms
still better, FP32pedantic generally better/equal toLt. SmallN Lt slower
thannative. Exact artifacts: artifacts/m6-lt-screen-20261021.

EXP168 prereg: identicalcachedprobe --lt --fused --scale,42actions/7sizes
throughactualN1601320; same120s/6GiB/no swap. No native rebuild/physics/default
change. Root will compare completeapply (inclconversions), errors/setup/workspace,
then separately assess instruction proof; no fullantenna based onmetadata alone.

EXP168 rootreview PASS42actions/allLt supported/CPU+FP64layout+canarycontrols,
20.21s. MaxLt relativeL2=3.3162791037778463e-4/scaled6.79161435784748e-4.
ActualN1601320: forward original3.478/3.484ms, FP32pedantic2.588/2.586,
fused1.337/1.337, Lt3.600/3.580ms. Transpose original3.637–3.884,
FP32pedantic2.914–3.513, Lt3.308–3.714ms; Lt slowerthanFP32all6actualactions.
Medianper-actionLt/native ratio0.9612, not wholejob speedup. Workspace actually
selected<=327360B acrossladder;64MiB is ceiling/allocation in isolatedprobe.
Lt metadata23/262658 consistent; first8heuristics notexhaustive tuning.
Negative performancefilter forPC integration, not universalTC rejection.
Artifacts artifacts/m6-lt-scale-20261021; no default/physics/native change.

EXP169 prereg: separate pinnedNsightSystems CUDAactivity trace of exactLt
scaleprobe,120s/6GiB/no swap. Add --profile-lt to same Pythonrunner only;
no C++/solver rebuild. Hot trace in/dev/shm, copy finalsqlite/nsys-rep only
if each<=64MiB, recordbytes/hash, remove privateRAMdirectory on terminal.
Traceincludesallprobe methods; profiledtimes notbenchmarks. Capture actually
launchedmangledsymbols, checkcollectorwarnings/schema/nonemptykernels before
staticcuobjdump onexactSM/function. No driverpermission change/counterclaim.

EXP169 root: process/42action controlsPASS, initialreceiptFAIL due parser
classifying enum tables and Info diagnostics as failures. Original receipts
retained. Reanalysis uses actual severity enum names, retainsallrows and
rejectsWarning/Error/unknown or lostdata evenatInfo. Addedregressiontest.
Offline root-reanalysis.json PASS/zeroissues/5052kernelcalls/29symbols,
SQLite2.42MB+nsys0.98MBordinaryfinalresults; hotRAMtracealreadyremoved.
No rerun needed. CUTLASSs1688 targetmangledsymbols actuallylaunched; SASS
stillrequired. Runtimeimage lacks cuobjdump; buildertool version invocation
failed container-initOOM at2GiB before toolstart, noGPUwork. No repeated
imageattempt: use hostcuobjdump13.4 for read-only audit of exactruntime12.9
library copiedonce to/dev/shm, sourceimage/library/toolSHA recorded.

EXP170 prereg: tools/experiments/ceed_lt_sass.py offline audit. Two actual
s1688 128x256NN/TN symbols fromEXP169, exactpinnedruntimeimage/library,
SM120-onlyfunctionSASS. Temporarylibrary inRAM/4GiBfreeguard; staticchild
8GiBaddressspace/50CPU-seconds/60wall/16MiBoutputlimit. Recordinstructions,
noGPUcalls/counters/permissions/globaltoolchainchange. Static evidence must
not be misreported as executedinstructioncounter or directLtcall attribution
(trace includes FAST_TF32 andLt methods). Root interprets branchlimitations.

EXP170 negative static lookup: runtimeLt749205904B/SHA96ddf489...fc541 matches
independent runtime hash. Both NN/TN exactsymbol absent in selectedSM120sections;
also checked runtimecublas, no match. Preserve outputs and FAIL/NOT PROVEN.
This does not prove noTCexecution: module/JIT identity unresolved; no counters.

EXP171 prereg: after libraryfilter, test missing fusedFP64input/output+TF32
function via native CUDA WMMA, isolated probe only. ActualbasisP20/Q14/QC3,
nogeometryconstant;64elements/4warps, paddedsharedtiles, no globalintermediate
floatvectors, only3360BstaticFP32basis and18432Bshared/block. Forwardonly;
transpose retains existing comparators. Allwarps execute same fixedMMAloops,
noearlyreturn. --wmma requires --lt --fused, defaultOFF; shape/pointerguards,
existingCPU/original/canary/error2e-3 controls. Screen thenladder onlyifcontrols
pass;120s/6GiB/no swap. Separate native SM120 kernel makes exact instruction
inspection possible without attributing opaque library/JIT instructions.
No solver/PCintegration until numerical and wholeapply costfilter passes.

EXP171 firstpreflight refused due strata autoreload; no artifacts/run. Root
respectfully followed user's no, then renewed explicit nowunload authorization.
Authenticated /unload HTTP200;14048MiBfree GPU. SameLuna screen9.23s/exit0,
12rows/4WMMAforward, allCPU/layout/canary/actioncontrolsPASS; WMMAmaxrelative
3.306e-4/scaled6.372e-4. AtN131071 WMMA~0.11ms vsfusedFP32~0.12ms;
not sufficient speedclaim, proceed to actualsize beforeintegration.
EXP172 prereg: identicalbinary --lt --fused --wmma --scale,120s/6GiB/no swap,
42rows/14forwardWMMA, actualN1601320; no native/physics/defaultchanges.

EXP172 root strict42row/allprecision/CPU/canaryPASS,14WMMAforward rows.
ActualN1601320 INTERP/CURL fullwall: original3.481956/3.475426ms,
fusedFP32=1.336048/1.337738, fusedWMMA=1.204328/1.197189.
WMMArelativeL2=2.2233351627431633e-4/3.303793142423953e-4.
~9.86%/10.51% forward improvement vsfusedFP32, one isolatedladder/3timings
peraction, no netFEMclaim. AdditionalglobalFP32basis3360B, shared18432B/block;
comparisonprocess stillallocatesalloldlibrarybuffers, notglobalpeakVRAMsaving.

EXP173 prereg: exactcurrentverifiedSM120binary staticSASS finds48unpredicated
HMMA.1684.F32.TF32 instructions in palace_probe_wmma_forward; noearlyEXIT
beforefirstHMMA, sourceloops have nofallback/earlyreturn andallwarps participate.
Retainbinary/toolSHA/argv/SASS in artifacts/m6-wmma-instructions-20261021.
Need dynamicmangledkernel trace tobindexecution explicitly: same --wmma
scaleprobe --profile-lt120s, noGPUcounters/permission changes. CorrectedInfo
severitygate, separateprofiletimesnotbenchmarks, RAMtrace/finalbytes limits.

EXP173 root dynamic+static instructionpath PASS, strictly scoped ownWMMA.
Profiler complete/exit0/23.41s/noissues, exact _Z25palace_probe_wmma_forwardPKfPKdPdi
70calls. Tracecommand binarySHA matches EXP172 and staticSASS receipt.
48staticunpredicatedHMMA.1684.F32.TF32 instructions; firstbeforeanyEXIT,
loaderbranches onlyloopback; source no earlyreturn/fallback in launchedkernel.
This is proof of executedTCinstructionpath, not countercount/utilization;
no hardwarecounters/adminchanges. Opaque cuBLAS/Lt exactkernel ownership/JIT
lookup remains unresolved and separate, not used as proof. TracefinalSQLite
~2.45MB/nsys~0.99MB; hotRAMremoved. No solver/PCnumericalpromotion.
EXP174–175 prereg: two more independently started samecached --wmma --lt
--fused --scale probes,120s/6GiB each, identicaloperator/actioncontrols.
Assess spread of per-action3timingmedians across3processes includingEXP172;
noFEM/medianwholejob claim. If preflight fails, stop/report, no usermodelkill.

EXP174–175 root strictactioncontrols/identicalmanifestPASS. Threeprocess
median-of-medians actualN: INTERP original3.474027/fusedFP32 1.336048/
WMMA1.204269ms (−9.863%vsfused); CURL3.475426/1.337738/1.201059ms
(−10.217%). WMMAprocessranges1.202709–1.204328/1.197189–1.205038ms.
NoRF/wholePC/UVM/peakclaim. Rootsummary artifacts/m6-wmma-root-analysis-20261021.json.
M6.3 instructionproof scopedPASS, M6 remainsactive for W.1/PC assessment.
Research/docs and exactlimits: docs/tf32-wmma.md. No active GPUjobs left.

EXP175 checkpoint:172Python tests/8shell/docschecker/diffPASS. SameLuna
read-only docs-gardenPASS; root reviewed currentdiff and numerical/instruction
receipts. Cached addon binary tested; native Palace/dependencies unchanged,
all new paths opt-in/defaultOFF. NoGPUjobs/containerslive. W.1 WMMA linearity/
range/fallback then justifiedPC assessment remain open; wholegoal/M7 notdone.
Usermodel unloaded viaAPI under renewed explicitauthorization; APIserver
retained (subsequent userrequest mayreload). No secrets recorded. Localcommit
only, no upstream push. Newhotworkspaces allRAM/VRAM, ordinarytrace/results
bytes recorded; no swap/diskbasis.

## EXP176 prereg — WMMA stationarity and dynamic range before PC

Previous goal turn made concrete progress EXP167–175/commitbd201d3. Current
GPU14177MiBfree/onlyTelegramcompute57MiB/host79GiBavailable/no swap.
Add optional --wmma-checks to existing cachedscreen, no native/deps change.
N257 forward INTERP/CURL independent homogeneity(alpha1.23456789012345)
and superposition; compareoriginal/FP64/FP32pedantic/TF32requested/fusedFP32/
Lt/WMMA. Reference linearity1e-11, mixedlinearity2e-6 (existingFP32action
filter, preregistered before results), not looseTF32action2e-3. Also11input
scales1e-300…1e300 using independentlongdoubleoracle; nonfinite outputs
explicitcounts/nullnorm, underflow finiteerrors retained. Original/FP64
range mustPASS1e-11. Mixednegative results mean completedassessment, not
numericalqualification. No fullFEM solelybecauseactiontime improved10%.
120s/6GiB/no swap; rootdesign/sameLunabaysitting. No driver/appchanges.

EXP176 root strict12row/newlinearity+rangecontrols PASS execution, negative
mixedresults preserved. Original/FP64linear~1.5–1.9e-16/range11of11PASS;
fusedFP32linear~7.9–8.7e-8PASS. WMMAhomogeneity2.3325e-4/3.5941e-4,
superposition2.3820e-4/3.5687e-4FAIL prereg2e-6. Midrange7of11actionPASS;
1e-300/1e-80 finitezeros/error1;1e80/1e300 10794nonfiniteoutputs each.
This is actiondefect/rangelimit, not measuredwholePC/RFfailure. Receipt
artifacts/m6-wmma-controls-20261021/root-analysis.json. RejectdirectWMMA
PCpromotion; no native/defaultchange. SourceFGMRES asserts !UseStoredBasis
(iterative.cpp), extraZ +fullFP64V representationcost described, notmeasured.
M6assessmentcomplete per negativefilter rule; originalscope/notolerancerelax.
M7active/fullW4W5/medians/geometry/package stillrequired. Detailedchecklist
and missingfrequencies docs/milestones/M7.md. No paidcompute.
EXP176 checkpoint172Python/8shell/docschecker/diffPASS. SameLuna docs-garden
foundstale current/open headings inM6; rootmarked oldcheckpointsections as
history and updatedcurrentTC/integration assessment, checker/diffPASS.
Native verifiedmanifest exactlyequalsEXP153–166, no rebuild required forM7.

EXP177 prereg M7/W.4: cold1.710GHz/physicalports1+2 fullFP64 reference,
identicalnative manifest toEXP153–166, same frozenmedium mesh/materials/feed,
RIGHT/K64/Tol1e-6, nativecomplexFP64coarse/freshsetup, deferredenergy+solver
release, snapshotsforE/B.1800s/60GiBcgroup/no swap/6GiBhostguard. GPUlocal;
noWMMA/PCbasisexperimentalflags, noseeds/predictor/PROM/profiler. Storeordinary
input/snapshotresults once and countbytes. Rootvalidatesraw/native/setup/
fields/inventory before EXP178 candidate. No new build/paidcompute.
EXP177 root referencePASS: endtoend686.203s/40+41iter/cgroup60146286592B.
Originalraw8.2004e-7/7.0181e-7, nativecomplexFP64/fresh2setups/strictoutput/
fieldinventory PASS; fourE/Bsnapshots. IndependentstoredS/energyfinitechecks,
source/nativeexactmatching; root-reference-check.json retained. Helpername
typo inrootanalysisfirstattempt raised beforewritingreceipt, corrected using
versionedrf_metrics; simulation unaffected/no rerun. Ordinaryartifactbytes
~1.18GB; exact inreceipt. No candidate outcome inferred.
EXP178 prereg: same1.710GHz/bothports/medium/config/native, combineddirect
FP32storage/scalednativeFP32LU+2fixedFP64IR/reuse, fieldreferenceEXP177.
Same1800s/60GiB/no swap/6GiBhostguard/frozenK; noTCexperimentalflags.
EXP178 rootconfirmedFAIL incomplete exit1/OOMfalse after399.041s,
firstport42iter/originalraw7.2463555e-7PASS; secondportfirstcoarseapply
failed originalFP64coarseresidual1.2963985270678087e-3>1e-3. No fullfields,
no valid candidate time/memorycomparison. Failure remains recorded. 2IR
cannotbeclaimedqualified acrossLTE; prior7n78points remain onlytheirscope.

EXP179 prereg: test one fixedadditional correction (3everycoarseapply) at
same1.710GHz/2ports/cold/fieldreferenceEXP177. This existingnativepath already
passedtiny/mediumW.2 inEXP143–144; previous3fdeadlineFAIL remains distinct
fromthissinglef bound. No newbuild/tolerancechange/adaptivePC/countpolicy.
Same1800s/60GiB/no swap/hostguard. PreserveEXP178failure separately; do not
claim rerunpolicycostfree or aggregate2IRand3IRasonefixedcandidate. Root
willqualifyexplicitcount3 ifcomplete, then choose broaderqualificationpolicy
basedonactualquality/cost. No failedrun speedupclaim.

EXP179 rootfixed3pairKPASS: reference686.203s/60146286592B →candidate
752.869s/45877805056B, time+9.715%/cgroup−23.723%. 42/43iter,
originalraw6.4386174e-7/6.5444737e-7/coarsemax8.063580729e-4,
14whole+regionalfieldrowsPASS, maxΔcomplexS5.1000644e-9,
ΔVSWR5.0958924e-9/power1.1911106e-9/relativeenergy9.4594957e-9.
Explicitfixed3receipt artifacts/m7-1710-fixed3-qualification-20261021.json.
Qualifier now accepts requested --corrections2/3/4, validates env/nativecounts,
summaryrejects mixedcounts; count4stillNOTRUN/notpromoted. Default2behavior
retained. Updatedtests mixedcohort/countguards, no globaltolerancechanges.
Older7fixed2pairs rechecked separately withcurrentversion; never combined
with1.71fixed3 asonefixedpolicy. FailedEXP178preserved; noautomaticrerunpolicy
claim/timegainfromincomplete. M7policyselectionstillopen; next2.69fixed3,
then3.30costvsfixed2beforebroaderW5. No GPUjobsactive.
EXP179 checkpoint173Python/8shell/docschecker/diffPASS; sameLuna readonly
docs-gardenPASS/rootreview. Actualguards rejectfixed3underdefault2policy and
rejectincompleteEXP178. Sevenlegacyfixed2pairs independentlyrecheckedPASS
withnewqualifier,21.095%time/23.825%cgroup unchanged; separatecohortreceipt
artifacts/m7-rechecked-seven-fixed2-summary-20261021.json. No nativebuild/
physics/defaultchange. M7active, globalpolicyselectionandremainingcoverage
stillopen. No paidresources/GPUjobsleft; all3runhandlesconfirmedterminal.

## EXP180 prereg — M7/W.4 2.690GHz reference

Previous goal turn progressed throughEXP176–179/commits070e2f2+0552afd,
qualifiedfixed3at1.71 and retained2IRfailure. Now cold2.690GHz/bothports
fullFP64reference, samemedium/config exceptf/native manifest verifiedunchanged.
RIGHT/K64/Tol1e-6, freshFP64coarse setupbothports, deferredenergy+solver
release/snapshots,1800s/60GiBcgroup/no swap/6GiBhostguard. GPU13205MiBfree,
host76GiBavailable. No TC/PCbasis experiments, seeds/PROM/profiler/cloud.
Rootchecksreference beforecandidatefixed3EXP181; qualitygates unchanged.
EXP180 rootreferencePASS: endtoend782.739s/46+47iter,
cgroup61227782144B. Actualoriginalraw<=8.868e-7, twofreshFP64coarsesetups,
fieldinventory/finiteS+energy/nativeidentityPASS/fourE+B snapshots. Stored
root-reference-check.json inclactualbytes. No candidate outcome inferred.
EXP181 prereg: same2.690GHz/bothports/medium/config/native, directFP32storage/
scalednativeFP32LU+3fixedFP64IR/reuse, fieldreferenceEXP180. Same1800s/
60GiB/no swap/6GiBhostguard/frozenK; noTCexperimentalflags, no globalpromotion.
EXP181 root fullpairfixed3 KPASS2.690GHz: ref782.739s/61227782144B,
candidate796.089s/46630957056B,47/48iter, originalraw<=9.458e-7,
coarsemax1.987243e-4,14fieldrowsPASS. Exact RF/energy/time/memorymetrics
in artifacts/m7-2690-fixed3-qualification-20261021.json. Time+1.706% and
cgroup−23.840% approximately; no speedupclaim. Actualbytes inreceipt.
EXP182 prereg: fixed3candidate3.300GHz/2ports/samemedium/native/cold,
existingfullFP64referenceEXP153revalidated native/mesh/inventory/raw before
reuse. Compareseparately withreference and existing2IRcandidateEXP154 for
fixedcorrectioncost; same1800s/60GiB/no swap/hostguard/frozenK. No seeds/PROM/
TC/profiler/globalpromotion. Reference is compatible; do not rerun it.
EXP182 rootfixed3KPASS3.300GHz: endtoend753.834s/cgroup46143578112B,
44/45iter, originalraw<=8.001e-7/coarsemax7.64124e-5,
14fieldrowsPASS. Ref752.534s/60692480000B, time+0.173%/cgroup−23.972%.
Relative2IRold549.512s is+37.18%, but not isolated causalcountcomparison:
telemetryinitialGPUusedold1613MiB vsnew2394MiB (~781MiBbackgrounddifference).
Timers: coarse101.439→295.050s, setup50.015→50.148, restPC249.128→256.165,
outerlinear62.259→63.428, IO19.625→19.511. Coarsephase explainsobservedtime
increase, but UVM/placement/bandwidth cause notproven withoutcontrolledprobe.
Threefixed3pairs1.71/2.69/3.3 requalifiedasonecountcohort, totals~3.66%slower,
maxcgroup−23.840%; artifacts/m7-three-fixed3-summary-20261021.json.

EXP183 prereg: repeatcoldfixed2at3.300GHz in currentdesktopGPUstate, same
flags/config/native/ref asold2IR andnew3IR exceptcount2. Existing2IRsamepoint
qualityPASS, no blanketretry of1.71failure. Need matchedconditions before
attributing37% tooneextraIR orchoosingglobalM7policy. 1800s/60GiB/no swap/
6GiBhostguard, no userappchanges. Recordtelemetryinitialbackground andphase
costs; ifconditionsdiffer,labelcomparisonconditional. No fullsweepuntilcost
reasoningupdated. This is diagnosticonepoint, notthreefullpairedmedians.

EXP183 rootqualificationKPASS fixed2/currentdesktop3.300GHz:680.730s,
cgroup46146531328B,44/45iter/raw<=8.266e-7/coarsemax1.303e-4.14fieldrowsPASS;
receipt artifacts/m7-330-fixed2-repeat-qualification-20261022.json. Compared
old2IR549.512s and current2IR680.730s (+23.88%), coarse101.439→221.662s;
other PC249.128→256.241s. Current3IR753.834s/current2IR680.730s (+10.74%),
coarse295.050/221.662s, restPC256.165/256.241s. InitialGPUbackground
1613(old2)/2392(current2)/2394(current3)MiB; desktopstateconfoundsoldvsnew.
No proofthatUVMcausedallregression, and neither historicalreference nor
currentcandidateisthreepairedmedians. Current2numericalqualityPASSdoesnot
repair1.71fixed2FAIL.

## EXP184 prereg — bounded coarse cost profiles, fixed2 vs fixed3

Rootsourceconfirmedexisting profiler0:2 cleanstop/2preconditionerapplies and
mixedcountsupported. Two sequential3.300GHz/P2-only directFP32storage native
scaledFP32LU runs with2vs3fixedIR, sameRIGHT/K64/Tol1e-6/hypre256MiB/release.
CaptureFIRST0 COUNT2,600s each/60GiB/no swap/hostguard; nofields/portreuse/
setupaudit/RFqualification. AlreadycachedNsight12.9-compatible tool/hottrace
in/dev/shm, finaldiagnosticfile<=64MiB. Keepnativehash/cacheunchanged.
Goal: attributeelapsedCUDAkernels/UVMcopy byhostphase, not pretendprofile
isunprofiledfullruntime. BackgroundGPUinitialsamplesretained.
Userunloadauthorized2026-10-22: API200 statusnotloaded, noforcedappkills.

EXP184 rootprofilesPASS: fixed2/3 sampled2coarsecalls7.277/9.450s,
restPCinclusive-minuscoarse7.338/7.308s, ortho0.0314/0.0314s. Coarselaunched
CUDAkernel9228/12300records,sum6.448/8.610s. ActualwindowUMcopyrecords
coherence10.630/12.333GB, speculativeprefetch125.101/148.357GB,
eviction139.351/163.395GB perNsightenum; overlappingcumulativerecordbytes,
notuniqueworkingset/SSDIO orallunprofiledPCIebandwidth. No causeattribution
ofallUMcopiestocoarsewithoutcopyphasemapping; samplecontainswholePC/A/ortho.
Two-windowcostsupportsadditionalcoarsework, not2IR/3IRstationarityproof or
RFqualification. Artifacts m7-coarse-cost-fixed{2,3}-profile-20261022.

## EXP185 prereg — M7/W.4 fixed3 at3.800GHz

Revalidatedexistingm6-qualified-380-reference-20261021 currentnative/mesh/
fieldsinventory/freshFP64setup2/originalrawPASS; referenceunchanged, reuse.
Candidate3IR/directFP32storage/FP64arithmetic/scaledFP32LU/reuse,
RIGHT/K64/Tol1e-6,bothports, samefrozenK. Snapshots/energy/defer/release,
1800s/60GiB/no swap/6GiBhostguard. NoTF/PCexperimentalflags/seeds/PROM/
profiler. Preregisterglobalfixed3asM7memoryfinalistpendingremainingW4/W5/
medians/geometry/package; keepfixed2historicalpointsscope,separatevariant.
No timespeedguarantee, noautomatic2to3fallback, no promotionyet.

EXP185 rootKPASS3.800GHzfixed3:754.772s/46325145600B vs
736.468s/61047599104B, +2.485%time/−24.116%cgroup.45/46iter,
raw<=9.569e-7,coarsemax3.753e-5,14fieldsPASS. Receipt
artifacts/m7-380-fixed3-qualification-20261022.json;4fixed3W4pairsrechecked
asonepolicy,56fieldrowsPASS,maxΔS3.430e-8/maxΔVSWR6.965e-8,
sum+3.368%time/maxcgroup−23.840%. No3medians/generalhardwaretimeclaim.

## EXP186 prereg — 2.900GHz antiresonance reference

Separateprotocol writtenbeforedata in docs/milestones/antiresonance-qualification.md.
Qualifieropt-inanti restrictedexact2.9/real50ohmports; keepscomplexS1e-3,
power1e-3,energy1e-3,E/B1%,originalraw1e-6/coarse1e-3/inventory/build.
Passivityportpower<=1.001 addedforanti; VSWRgateonlyomittedinthisseparate
antipoint, matcheddefaultunchanged/summariescannotmixanti. Zofmatchedother
portisdiagnosticwithCayleydeltaZbound/polehandling,noadhoctolerance.
175PythoncontrolsPASS includingpole,phase/energy/passivityFAIL,scopeguards,
summarymixguardandanalyticalbound. Nativeunchanged/no rebuildneeded.
Cold2.900/bothportsFP64reference first:RIGHT/K64/Tol1e-6/freshFP64coarse2,
defer/energy/release/snapshots,1800s/60GiB/no swap/hostguard. Rootaudits
referencebeforecandidate. No seeds/PROM/TC/profiler/globalpromotion.

EXP186 rootreferencePASS2.900GHz:869.128s,62654750720B,54/55iter,
originalraw<=8.703e-7/nativeFP64fresh2setup/inventory4snapshots/currentnative
identity/finiteS+energy+passivityPASS. root-reference-check.json includes
Zdiagnosticsandactualwrittenbytes; no candidatequalityclaimyet.
EXP187 prereg: same2.900GHzmedium/bothports/native/physics, directFP32
storage/scaledFP32LU+3fixedFP64IR/reuse/defer/energy/release/snapshots.
1800s/60GiB/no swap/hostguard, no seeds/PROM/TC/profiler. CompareEXP186
usingseparatepreregisteredantiS/Zprotocol; defaultmatchedKunchanged.

EXP187 rootantiKPASS:903.918s/47362490368B vs869.128s/62654750720B,
+4.003%time/−24.407%cgroup.55/56iter versus54/55; secondsolveoriginal
KSPcheck2.468e-6causedreliablecontinuation/restart, finalraw8.1771e-7/
9.6502e-7. Allcostincluded,norelaxation.115coarseapply/max1.08534e-4,
14fieldrowsmaxE4.4331e-7/B4.4879e-7. maxΔS7.7524e-8,Δpower8.4628e-8,
energy1.9953e-7,ΔZ3.00083e-6ohm; no poleatthisspecificf. Receipt
artifacts/m7-2900-fixed3-antiresonance-qualification-20261022.json.
Antiresultkeptoutofmatchedsummary; CLIguardsoriginalreceiptprotocolbefore
requalification,176Pythoncontrols. Fullfixed3W5still11pointsNOTRUN, M7active.
No nativebuild/defaultchange/paidsessions. Normalartifacts~1.177GB/job,
no diskhotworkspace. Nextaudit/docscommit, thenW5point1.785GHz.
EXP187 checkpoint:176Python/8shell/checker/diffPASS, sameLunareadonly
docs-gardenPASS/rootdiffreview. CLIantireceipt-to-matchedsummarynegative
controlPASS; fourfixed3pairsrecheckedwithfinalqualifierPASS. No native
rebuildorunrelatedappchanges. Allsimulations/profilehandlesterminal, M7active
with11W5points/3pairedmedians/newgeometry/packagepending.

## EXP188 prereg — M7/W.5 1.785GHz fullFP64 reference

PreviousgoalturnclassifiedPROGRESS: commite424d61, new2.69/3.3/3.8fixed3
W4evidence,2.9antiFP64/candidatepairKPASS,176Python/8shell/docsPASS.
Currentworktreeclean/nativeverifiedsamea6ec732f…187c3338; noactiveGPUjobs,
GPU2349MiBused/13551MiBfree,host82.23GBavailable,swap0. No compatible
1.785GHzreferencefound; do not substitute nearbyf.
Cold1.785GHz/bothportsfullFP64basis/coarse/fresh2setups,RIGHT/K64/Tol1e-6,
samemedium/mesh/materials/ports/defer/energy/release/snapshots,1800s/60GiB/
no swap/6GiBhostguard. No seeds/PROM/TF/profiler/PCexperimentalflags.
Rootverifiesreferencebefore3fixedIRcandidate. SameLunababysitsreadyargv.
EXP188rootreferencePASS1.785GHz:705.073s/60150403072B,40/41iter,
originalraw<=8.977e-7,2freshFP64setups/mesh+native/inventory4snapshots/
finiteSenergyPASS. root-reference-check.jsonactualbytesstored.
EXP189prereg: same1.785GHz/2ports/medium/currentnative, directFP32storage/
scaledcomplexFP32LU+3fixedFP64IR/reuse; identicalRIGHT/K64/Tol1e-6,
defer/energy/releases/snapshots,1800s/60GiB/no swap/hostguard. Fieldreference
EXP188, frozenmatchedK, noTF/seeds/PROM/profiler/defaultpromotion.
EXP189rootmatchedKPASS1.785GHz:ref705.073s/60150403072B,
fixed3candidate726.980s/46102175744B (+3.107%time/−23.355%cgroup).
40/41→42/43iter, originalrawfinal<=7.125e-7, maxcoarse7.60743e-4/
89applyfixed3. Bothsolvesrequiredreliablecontinuationafterinitialtrue
check>1e-6; noearlyacceptance/relaxation, costincluded.14fieldsPASS,
maxΔS4.3955e-9/ΔVSWR6.1738e-9/Δpower6.4858e-10/energy2.1006e-8.
Receipt artifacts/m7-1785-fixed3-qualification-20261022.json.

## EXP190–191 prereg — W.5 1.805 and1.880GHz references

Two sequentialcoldFP64referencejobs, notconcurrent, each1800s/60GiB/
no swap/6GiBhostguard. Sameverifiednative/medium/mesh/physics, bothports,
RIGHT/K64/Tol1e-6/nativeFP64coarse/fresh2setup/defer/energy/releases/
snapshots. No compatibleexistingexactreferencesfound; noapproximatefreq
substitution. Rootchecksbothexistingresultsbeforecorrespondingfixed3
candidates. No seeds/PROM/TF/profiler/PCexperiments/defaultchanges.
EXP190rootreferencePASS1.805GHz:709.171s/60149178368B,40/41iter,
originalraw<=9.181e-7,2freshFP64setups/native+mesh/inventory4snapshots/
finiteSenergyPASS. root-reference-check.jsonactualbytesstored.
EXP191INTERRUPTEDnotRFresult:1.880referenceexit130/SIGTERMat265.387s,
firstsolveiter19/recurrence2.289823e-2,nofinalraw/fields/containerstate.
Partialcgroup55850786816Bnotusablefullresult. Runnerexit130/interruptedtrue
andnoactivepodmancontainer/palaceprocessconfirmedroot; notobservationtimeout.
AgentreportedwronglythatEXP190notstarted; actualfilesprove190complete,
agentcorrected. EXP191handle45867terminalwrite_stdinreportedSIGTERM; agent
usedexactargv/noshelltimeout/nokill, sourceofsignalUNKNOWN/notlabelledOOM.
Preserveartifactandnewpathforretryafter190candidate.
EXP192prereg:1.805GHzfixed3candidate sameprotocol/frozenK/refEXP190,
1800s/60GiB/no swap/hostguard; no seeds/PROM/TF/profiler/defaultchange.
GPUbackgroundnow~3.0GB(vs~2.35GBprior); retaintelemetry, noforcedappchanges
orcausalspeedclaimfromunmatchedbackground.

EXP193prereg/usersteering: userexplicitlyrequestsretry afterEXP191SIGTERM.
Rootauthoritativestatebeforequeue: EXP1921.805candidateisLIVE, container
palace-run-1284a65e1f20, runnerPID1816174/Palace1816297, no terminalresult.
Do not restart192/duplicateGPUload. After192cleanterminal, retry1.880GHz
FP64reference atnewpathm7-qualified-1880-reference-r1-20261022 withsame
medium/config/native/RIGHT/K64/Tol1e-6/fresh2setup/bothports/snapshots/defer/
energy/releases/1800s/60GiB/no swap/hostguard. PreserveEXP191incomplete
artifact; unknownSIGTERMsource notnumericalFAIL/OOM/speedresult.
EXP192rootmatchedKPASS1.805GHz:744.025s/46215004160B vs709.171s/
60149178368B,42/43iter, originalraw<=7.514e-7/coarsemax7.37598e-4/
89applyfixed3. Bothsolvesreliablecontinuationincluded;14fieldsPASS,
receipt artifacts/m7-1805-fixed3-qualification-20261022.json.
EXP193rootreferencePASS1.880GHzretry:714.022s/60146532352B,41/41iter,
originalraw<=9.423e-7/FP64fresh2/native+mesh/inventory4snapshots/finiteRF
PASS. root-reference-check.json includesactualbytes. EXP191oldSIGTERM
incompletekeptunchanged; don'tmixitscost/partialmemoryintocompletedpair.
EXP194prereg:1.880GHzdirectFP32storage/scaledFP32LU+3fixedFP64IR/reuse,
fieldreferenceEXP193newr1path, samefullmedium/ports/RIGHT/K64/Tol1e-6/
defer/energy/releases/snapshots/1800s/60GiB/no swap/hostguard/frozenmatchedK.
No TF/seeds/PROM/profiler/defaultpromotion oruserappchanges.
EXP194rootmatchedKPASS1.880GHz:728.928s/46096318464B vs714.022s/
60146532352B,42/43vs41/41iter, finalraw8.91977e-7/7.76246e-7; initial
checks3.17e-6/5.65e-6triggeredreliablecontinuation, includedcost.
Fixed3maxcoarse6.36821e-4/89apply;14fieldsPASS, maxE4.5668e-8/
B4.0458e-8. ΔS7.4986e-9/ΔVSWR3.1271e-9/power1.0226e-9/energy8.7634e-9.
Receipt artifacts/m7-1880-fixed3-qualification-20261022.json.
All7fixed3matchedpairs requalified withversionscript: partialW5coverage
7/15,98fieldrowsPASS. Summary artifacts/m7-seven-fixed3-partial-W5-summary-
20261022.json:5086.211→5257.496s (+3.368%), maxcgroup61227782144→
46630957056B (−23.840%). Notpairedmedians/fullband/nohardwareclaim;
unknownSIGTERMresearchcost265.387s keptseparatefromcompletedpairtimes.
NextW5missing1.920/1.980/2.110/2.170/2.500/2.570/2.620/3.550GHz.
No native/code/default/cachechange, no paidcompute/hotSSDworkspace.
EXP194checkpoint: versionscriptrevalidatedall7fixed3pairsPASS; rootdocsdiff
review/checker/diffcheckPASS. Documentationonly sincecommite424d61; no
needfornativebuildorunitretests, previous176Python/8shellsourcevalidation
unchanged. AllEXP188–194jobhandlesterminal; noactivePalacecontainer/process
confirmedafter194. GoalM7active,next1.920GHzreference/candidateexactpair.

## EXP195 prereg — M7/W.5 1.920GHz FP64 reference

PreviousgoalturnPROGRESS: commit85ea4b3, new1.785/1.805/1.880GHzpairsKPASS
+preservedSIGTERM/authorizedretryevidence. Currentnativeverifiedunchanged,
worktreeclean,noactivePalacejobs. Missingexact1.920GHzcompatibleFP64ref.
Cold1.920GHz/bothports/fullFP64storage+coarse/fresh2setups, same medium/
mesh/materials/ports, RIGHT/K64/Tol1e-6/defer/energy/releases/snapshots.
1800s/60GiBcgroup/no swap/6GiBhostguard; no seeds/PROM/TF/profiler/PC
experiments/defaultpromotion. Rootchecksreferencebeforefixed3candidate.
EXP195rootreferencePASS1.920GHz:712.111s/60143570944B,41/41iter,
originalraw7.43405e-7/9.98203e-7, nativeFP64fresh2/mesh+native/inventory/
finiteSenergyPASS; root-reference-check.jsonactualbytesstored.
EXP196prereg:same1.920GHz/bothports/native/medium/RIGHT/K64/Tol1e-6,
directFP32storage/scaledFP32LU+3fixedFP64IR/reuse/defer/energy/releases/
snapshots/1800s/60GiB/no swap/hostguard,refEXP195,frozenmatchedK.
No seeds/PROM/TF/profiler/defaultchanges.
EXP196rootmatchedKPASS1.920GHz:727.344s/46104252416B versus712.111s/
60143570944B,42/43vs41/41iter, finaloriginalraw<=9.615e-7; twoinitial
checks>tolledtoreliablecontinuation, includedcost. Fixed3maxcoarse5.87405e-4/
89apply,14fieldsPASS. Receipt artifacts/m7-1920-fixed3-qualification-20261022.json.

## EXP197–198 prereg — W.5 1.980/2.110GHz references

Two sequentialcoldfullFP64jobs, sameverifiednative/medium/mesh/physics/
bothports/RIGHT/K64/Tol1e-6/fresh2setup/defer/energy/releases/snapshots.
Each1800s/60GiBcgroup/no swap/6GiBhostguard, no parallelGPUload. No exact
compatiblereferencefound; rootcheckscompletedrefsbeforespecificfixed3
candidates. NoTF/seeds/PROM/profiler/experimentalPC/defaultpromotion.
EXP197/198rootreferencesPASS:1.980GHz716.044s/60325879808B,41/42iter/
raw<=7.982e-7;2.110GHz715.774s/60327763968B,41/42iter/raw<=9.413e-7.
BothnativeFP64fresh2/currentnative+mesh/inventory4snapshots/finiteRFenergy
PASS; root-reference-check.jsonactualbytesstoredperrun.
EXP199–200prereg: exactsame1.980/2.110GHzconfigs/medium/bothports/native,
directFP32storage/scaledFP32LU+3fixedFP64IR/reuse/defer/energy/releases/
snapshots/RIGHT/K64/Tol1e-6/frozenmatchedK, exactrespectivefieldrefs.
Twoindependentsequentialjobsnotconcurrent;each1800s/60GiB/no swap/
hostguard, secondonlyafterfirstcomplete/fieldsflagPASS, rootfullRF
qualificationsafterboth. No seeds/PROM/TF/profiler/experimentalPC/defaults.
EXP199rootKPASS1.980GHz:733.449s/46179397632B vs716.044s/60325879808B,
42/44vs41/42iter, originalraw<=9.390e-7, coarsemax5.19265e-4/90apply.
ΔS4.4148e-9/ΔVSWR6.9985e-9/power7.8865e-10/energy2.3846e-8/14fieldsPASS.
EXP200rootKPASS2.110GHz:731.137s/45967593472B vs715.774s/60327763968B,
42/44vs41/42iter, originalraw<=9.595e-7, coarsemax3.92934e-4/90apply.
ΔS6.5527e-9/ΔVSWR1.6886e-8/power1.6446e-9/energy2.1225e-8/14fieldsPASS.
Bothfixed3/native/fields/reuseauditsPASS, reliablecontinuationsincludedin
cost. Receipts artifacts/m7-{1980,2110}-fixed3-qualification-20261022.json.

## EXP201 prereg — W.5 2.170GHz fullFP64 reference

Nativeunchanged, noactivePalacejobs, GPU2371MiBused/host85.14GBavailable,
swap0. Cold2.170GHz/bothports/fullFP64storage+coarse/fresh2setup, same
medium/mesh/physics/RIGHT/K64/Tol1e-6/defer/energy/releases/snapshots.
1800s/60GiBcgroup/no swap/hostguard, no seeds/PROM/TF/profiler/default
changes. No existingcompatibleexactreference; rootverifiesnewbeforecandidate.
EXP201rootreferencePASS2.170GHz:726.078s/60506451968B,42/43iter,
raw<=7.261e-7/nativeFP64fresh2/mesh+native/inventory4snapshots/finiteRF
PASS, root-reference-check.jsonstoredwithactualbytes.
EXP202prereg:2.170GHzfixed3candidate,bothports,sameconfig/native/medium/
RIGHT/K64/Tol1e-6, directFP32storage/scaledFP32LU/reuse/defer/energy/
releases/snapshots/1800s/60GiB/no swap/hostguard/frozenmatchedK. Exact
fieldrefEXP201,no seeds/PROM/TF/profiler/defaultchange.
EXP202rootmatchedKPASS2.170GHz:741.421s/46272794624B vs726.078s/
60506451968B,43/44vs42/43iter, raw8.0080e-7/9.7379e-7afterreliable
continuationbothRHS, costincluded. Fixed3maxcoarse3.38871e-4/91apply,
14fieldsPASS,maxE7.6749e-8/B3.7161e-8,ΔS7.5134e-9/ΔVSWR1.9294e-8/
power2.4793e-9/energy1.5047e-8. Receiptm7-2170-fixed3-qualification-20261022.json.
All11fixed3matchedpairsindependentlyrequalifiedwithversionscriptPASS:
154fieldrows, maxΔS3.430e-8/ΔVSWR6.965e-8/energy1.004e-7,
maxE5.929e-7/B1.308e-7. Summaryartifacts/m7-eleven-fixed3-partial-W5-
summary-20261022.json;7956.217→8190.846s (+2.949%),maxcgroup61.228→
46.631GB (−23.840%). Onepairperpoint/notmedians/fullband/newgeometry/
physicalVRAMclaim.26GBordinaryartifacts, noin-RAMsolverSSDworkspace.
W5now11/15,next2.500/2.570/2.620/3.550GHz. Native/cache/defaultsunchanged.
EXP202checkpoint:rootreviewedactual11pairreceiptfields/config/native/raw/
quality/costcoverage, currentdocsdiff/checker/diffcheckPASS. Documentation
onlysince85ea4b3,no nativebuild/unitretestneeded; previous176Python/8shell
sourcevalidationunchanged. AllEXP195–202handlesterminal/noactivePalace
container; no paidcompute/swap/appkills/native/defaultchange. M7ACTIVE,
notcomplete:fourW5points,3fullpairedmedians,newgeometry,package/auditpending.

## EXP203 prereg — M7/W.5 2.500GHz FP64 reference

PreviousgoalturnPROGRESS:commit8b474f6, fournew1.92/1.98/2.11/2.17pairs
KPASS/current11pointssummary, nativerebuildnotneeded. Currentworktreeclean/
noactivePalacejobs/GPU2372MiBused/host85.12GBavailable/swap0/nativeverified
unchangeda6ec732f…187c3338. No compatibleexact2.500GHzreferencefound.
Cold2.500GHz/bothports/fullFP64basis+coarse/fresh2setups, samemedium/mesh/
materials/ports/RIGHT/K64/Tol1e-6/defer/energy/releases/snapshots,1800s/
60GiBcgroup/no swap/6GiBhostguard. NoTF/seeds/PROM/profiler/experimentalPC/
defaultchanges. Rootchecksreferencebeforefixed3candidate.
EXP203rootreferencePASS2.500GHz:748.584s/60862611456B,44/45iter,
raw<=8.957e-7/nativeFP64fresh2/mesh+native/inventory4snapshots/finiteRF
PASS; root-reference-check.jsonactualbytesstored.
EXP204prereg:same2.500GHz/bothports/medium/native/config/RIGHT/K64/Tol1e-6,
directFP32storage/scaledFP32LU+3fixedFP64IR/reuse/defer/energy/releases/
snapshots,1800s/60GiB/no swap/hostguard/exactrefEXP203/frozenmatchedK.
No seeds/PROM/TF/profiler/experimentalPC/defaultchanges.
EXP204rootmatchedKPASS2.500GHz:768.071s/46457860096B vs748.584s/
60862611456B,45/46vs44/45iter, raw<=8.289e-7afterreliablecontinuationboth
RHS,costincluded.14fieldsPASS; receiptm7-2500-fixed3-qualification-20261022.json.

## EXP205–207 prereg — final three W.5 FP64 references

2.570/2.620/3.550GHz, three independentSEQUENTIALjobs, sameverifiednative/
medium/mesh/physics/bothports/RIGHT/K64/Tol1e-6/fullFP64basis+coarse/
fresh2setup/defer/energy/releases/snapshots. Each1800s/60GiBcgroup/no swap/
6GiBhostguard; stopqueueifonefails, no automaticretry. No compatibleexact
fulltwoportreferencesfound; rootauditscompletedresultsbeforecandidates.
No seeds/PROM/TF/profiler/experimentalPC/defaultchanges.
EXP205–207rootreferencesPASS:2.570GHz762.022s/61042880512B,45/46iter/
raw<=7.889e-7;2.620GHz761.448s/61046497280B,45/46iter/raw<=9.289e-7;
3.550GHz749.898s/60860223488B,44/45iter/raw<=7.834e-7. Allcurrentnative/
mesh/freshFP64two setups/inventory4snapshots/finiteRFenergyPASS. Perref
root-reference-check.jsonactualbytesstored. Workerclaimedtwo reliable
continuationsperreference,butrootlogsproveonly2totalKSPchecks(oneperRHS),
bothbelowthreshold,norestart1: do NOT propagateworkerclaim.

## EXP208–210 prereg — final three W.5 fixed3 candidates

2.570/2.620/3.550GHz, exactrespectiveverifiedreferences, sameconfigs/
native/medium/bothports/RIGHT/K64/Tol1e-6/directFP32storage/scaledFP32LU+
3fixedFP64IR/reuse/defer/energy/releases/snapshots. ThreeSEQUENTIALjobs,
1800s/60GiB/no swap/hostguardeach; stopifincomplete/fieldflagFAIL/noauto
retry. RootRFqualifiesallafterexecution. No seeds/PROM/TF/profiler/
experimentalPC/defaultchanges.
EXP208–210rootmatchedKPASS:2.570GHz781.432s/46550986752B versus
762.022s/61042880512B,46/47vs45/46iter/raw<=7.809e-7;2.620GHz781.405s/
46392844288Bvs761.448s/61046497280B,46/47vs45/46iter/raw<=8.759e-7;
3.550GHz739.425s/46279172096Bvs749.898s/60860223488B,44/45both/
raw<=8.875e-7. 2.57/2.62had2above-thresholdKSPchecksandcontinuation;
3.55hadnone; allcostincluded. 14fieldsperpointPASS, noloosening.
All15fixed3matchedpairsindependentlyrequalifiedwithversionscriptPASS:
210fieldrows,maxΔS3.430e-8/ΔVSWR6.965e-8/energy1.004e-7,maxE6.095e-7/
B1.308e-7. Summary artifacts/m7-full-W5-fixed3-summary-20261022.json.
10978.169→11261.178s (+2.578%), maxcgroup61227782144→46630957056B
(−23.840%),1289→1325iterations,35.305GBordinaryartifacts. No median/
continuousband/physicalVRAM/newgeometryclaim. W5samplingcomplete.

## EXP211 prereg — M7 integrated W.2 tiny reference

Auditfoundoldfixed3W2manifest4fc32f… !=currenta6ec732f… andhistory/PROM
policy,notcurrentcoldcombinedfinalist. NeedcurrenttinyTEML2thenmedium
3freq2ports beforeM7.1claim. W3willbecheckedincludingP2incontemporary
3.500GHzbothportpairedmedianruns, notsubstitutedby3.55nearbyf.
Tiny3.550GHz/bothports/coldprocessFP64basis+coarse/fresh2,RIGHT/K64/Tol1e-6/
defer/energy/releases/snapshots/coaxTEMprobes+volumeL2,60s/no swap/hostguard.
GatesinheritedM1: TEMsampleRMS<=1%,point<=2%,analyticenergy<=1e-3,
volumeE/B<=1%,q4/q6absolutechange<=5e-4; matchedRF/energy/fields/rawasK.
Thenrootrefauditbeforefixed3tinycandidate,followmedium3.3/3.55/3.8both
ports(noexpensivevolumeL2,probes+wholefields+S/TEM); donotrebuildnative.
EXP211rootreferencePASS:17.746s/574173184B,39/42iter/raw<=9.594e-7,
FP64fresh2/currentnative/inventory4snapshots/finiteRF/analyticTEMRMS+point+
energygatesPASS; volumeL2E/B~0.4953/0.4558%,q4→q6delta~2.2e-6<5e-4.
Storedtem-fields.jsonandroot-reference-check.jsoninclactualbytes.
EXP212prereg:exacttinyconfig/native/3.55/2ports,directFP32storage/scaled
FP32LU+3fixedFP64IR/reuse/defer/energy/releases/fields/TEML2,60s/no swap/
hostguard/sameref/frozenK. No seeds/PROM/TF/profiler/defaultchanges.
EXP212rootintegratedtinyW2PASS:versionedcold2portqualifierKPASSplus
analyticTEMsampleRMS/point/energy/L2q4+q6gatesPASS.39/42both, originalraw
<=9.702e-7, snapshotfields/RF/energy/nativefixed3PASSpreserved. Receipt
artifacts/m7-w2-tiny-fixed3-qualification-20261022.json, tem-fields.json.

## EXP213 prereg — integrated W.2 coax-medium FP64 3freq reference

Exactcurrentnative, mediumcoaxunchanged,3.3/3.55/3.8GHz/bothports,
FP64basis+coarse/fresh6setups,RIGHT/K64/Tol1e-6/TEMprobes/fields/defer/
energy/releases. Explicitfrequency-port-batchBOTHvariants forNF>1defer,
noexternalhistory/seeds/PROM/TF/profiler.180s/no swap/hostguard.
AnalyticTEMsampleRMS<=1%,point<=2%,energy<=1e-3; noexpensivemediumvolumeL2
(tinyL2passed). Rootreferencesixraw/inventory12snapshots/native6FP64/
TEMauditbeforefixed3candidate; noantennaqualificationinferredfromcoaxalone.
EXP213rootmedium3freqreferencePASS:62.980s/2967896064B,6solves/
raw<=8.657e-7/nativeFP64fresh6/f-majoraudit/currentnative+mesh/12snapshots/
finiteRF/TEM3freqallportsRMS+point+energygatesPASS. Rootreferencecheck+
tem-fields.jsonstored; nofullvolumeL2claimformedium.
EXP214prereg:same3freqcoaxmedium/f-major/config/currentnative,bothports/
directFP32storage/scaledFP32LU+3fixedFP64IR/reuse3setups/defer/energy/
releases/TEMprobes/fields,180s/no swap/hostguard,sameref/frozenK.
No externalhistory/seeds/PROM/TF/profiler/defaultchanges.
EXP214rootintegratedmediumW2PASS:6raw<=1e-6/currentnative+mesh/12snapshot
SHA/configidentity/nativeFP64fresh6vsfixed3LUbuild3/reuse3/f-major/no
externalhistory/allTEMsampleRMS+point+energygates/wholefields/RFenergyPASS.
Receipt artifacts/m7-w2-medium-fixed3-qualification-20261022.json.
W2tiny+mediumNOWcurrentbuild/currentfixed3qualified; old4fc…historytestsnot
usedasproofcurrentbuild. No mediumvolumeL2claim,tinyvolumeL2PASSseparate.
W3and3pairedmedians3.500GHzstillNOTRUNforfixed3; nextstepafterdoccheckpoint.
EXP214checkpointpreparation:W5all15/currentfixed3PASS,210fieldrows;
W2tiny+mediumcurrentbuildPASS.TinyKmaxΔS3.144e-10/ΔVSWR3.254e-10/
energy4.252e-9,analyticTEMvolumeL2<1%/qchange<5e-4. MediumKmaxΔS4.975e-9/
ΔVSWR9.539e-9/energy8.709e-9/12fieldrows/maxE5.870e-8/B2.404e-8,
62.980→47.667s onepair, notantenna speedup. No native/rebuild/defaultchanges.
Detailedpreregfor3new3.500GHzbothportfullpairsinM7.md BEFOREtimingdata;
firstpairwillverifyexactP2W3numericalcoverage, reporttwoportcosthonestly.
NextR1→C1→R2→C2→R3→C3eachownfieldref/fullK; retainunfavorable/failure
dataandbackground. Thennewgeometry/package/audit. GoalM7stillACTIVE.
EXP214checkpoint:currentW5all15KandW2tiny+mediumTEMqualified, sources/
config/native/currentartifactsrootverified. Rootdocsdiff/checker/diffPASS,
no code/nativechangesormandatoryunitretestsince8b474f6. AllEXP203–214
handlesterminal/noactivePalacecontainer. SameLunareusedonlyreadyargv
babysitting, rootdesigned/analyzed/recordsworkerreportcorrectionsfromactual
logs. No paidresources/swap/hotSSDworkspace/appkills/rebuild. GoalM7active,
nextthreecontemporary3.500GHzbothportR/CpairsperpreregM7.md, thenmeaningful
newgeometry, reproduciblepackageandfullcompletionaudit.

## EXP215 prereg — M7.2 pair1 3.500GHz FP64 reference

PreviousgoalturnPROGRESS:commitfa78284, W5all15fixed3KPASS+currentW2tiny/
mediumTEMrequalificationPASS. Worktreeclean/nativeverifiedunchanged.
FollowprewrittenM7.2preregM7.md:R1→C1→R2→C2→R3→C3, threefullnewpairs,
bothports/exact3.500GHz/medium/RIGHT/K64/Tol1e-6/60GiB/no swap/hostguard/
1800s/defer/energy/releases/snapshots, noprofiler/seeds/PROM/TF.
EXP215:R1fullFP64basis+coarse/fresh2setups, thenrootreferenceauditbeforeC1.
R/CcostincludesIOandfieldqualification; nodeps/nativebuild/cacheflush.
FirstpairalsoverifiesP2atW3exactf, don'tclaimtwoporttimeasP2-onlytime.
EXP215rootR1PASS3.500GHz:743.976s/60682346496B,44/44iter/raw<=9.497e-7,
currentnative/FP64fresh2/fieldsinventory/finiteRF/P2presentPASS. Ownreference
root-reference-check.jsonactualbytesstored.
EXP216preregC1:sameexactconfig/native/bothports/3.500GHz/medium,
directFP32storage/scaledFP32LU+3fixedFP64IR/reuse/defer/energy/releases/
snapshots/RIGHT/K64/Tol1e-6/1800s/60GiB/no swap/hostguard. OwnfieldrefR1,
no seeds/PROM/TF/profiler/cacheflush/defaultchanges. FullpairedKafterrun.
EXP216rootpairR1C1KPASS3.500GHz/2ports:743.976→747.515s,
60682346496→46364360704B,44/44→44/45iter, originalrawC<=8.694e-7;
oneRHS2above-thresholdchecktriggeredcontinuationincludedincost.
Receipt artifacts/m7-median-3500-pair-r1-qualification-20261022.json.
Keepallresults; no causal/medianclaimfromonepair.
EXP217preregR2:secondnewcoldfullFP64referenceat3.500GHz,bothports,same
config/currentnative/RIGHT/K64/Tol1e-6/defer/energy/releases/snapshots,
1800s/60GiB/no swap/hostguard. No profiler/seeds/PROM/TF/cacheflush/
defaultchange. FollowfixedR1C1R2C2R3C3orderandownreferenceperpair.
EXP217rootR2PASS3.500GHz:746.261s/60688879616B,44/44iter/raw<=9.497e-7,
identicalR1config/currentnative/FP64fresh2/inventory/finiteRFenergyPASS.
Rootreferencecheckstoredwithactualbytes; telemetry.jsonlretained.
EXP218preregC2:ownR2fieldref,sameexactconfig/native/bothports/3.500GHz/
medium/RIGHT/K64/Tol1e-6/directFP32storage/scaledFP32LU+3fixedFP64IR/
reuse/defer/energy/releases/snapshots/1800s/60GiB/no swap/hostguard.
No profiler/seeds/PROM/TF/cacheflush/defaultchange. Keepfixedrunorder.
EXP218rootR2C2KPASS3.500GHz/2ports:746.261→752.608s,
60688879616→46370021376B,44/44→44/45iter, finalCraw<=8.393e-7;
RHS2truecheck>tolthencontinuationincluded, maxcoarse9.49257e-5/92apply.
Receipt artifacts/m7-median-3500-pair-r2-qualification-20261022.json.
EXP219preregR3:thirdnewFP64reference,sameexact3.500GHz/2ports/config/
currentnative/medium/RIGHT/K64/Tol1e-6/fresh2/defer/energy/releases/fields,
1800s/60GiB/no swap/hostguard. No profiler/seeds/PROM/TF/cacheflush/
defaultchanges. Keepallrunresults; stillonepairremaining,nofinalmedianyet.
EXP219rootR3PASS3.500GHz:745.458s/60683603968B,44/44iter/raw<=9.497e-7,
identicalR1R2config/currentnative/FP64fresh2/inventory/finiteRFenergyPASS.
Rootreferencecheckstoredwithactualbytes.
EXP220preregC3:ownR3fieldreference,sameexact3.500GHz/bothports/config/
currentnative/medium/RIGHT/K64/Tol1e-6/directFP32storage/scaledFP32LU+
3fixedFP64IR/reuse/defer/energy/releases/snapshots/1800s/60GiB/no swap/
hostguard. No profiler/seeds/PROM/TF/cacheflush/defaultchanges. Third
paircannotreplacetheearlierunfavorablepairs, allthreeenterstatistics.
EXP220rootR3C3KPASS:745.458→747.733s,60683603968→46361014272B,
44/44→44/45iter, finalCraw<=8.221e-7, RHS2check>tolcontinuationincluded.
Maxcoarse6.17117e-5/92apply. All3newpairedreceiptssource/config/native
verifiedandP2exact3.500GHz/7regionsperpairseparatelychecked; W3numerical
coveragein2portjobs, notsingle-P2timingclaim.
Newversionscript--paired-mediansrequalifiesallinputs, requires3samef/config/
native/countpairsand6distinctpaths/containernames, separatespairedratios
fromratioofmedians; duplicates/mismatch/FAIL/NaN/antiprotocol/modesreject.
179PythoncontrolsPASS, actualCLIall3pairsPASS. No nativeSHA/defaultchanges.
Summaryartifacts/m7-median-3500-three-pairs-qualification-20261022.json:
medianR745.457956/C747.732711s (+0.305149%),pairedtimechangemedian
+0.475673%[0.305149,0.850440],RAMcgroupmedian−23.596560%.42fields/maxE
4.0888e-7/B8.7334e-8,ΔS2.3935e-8/ΔVSWR4.6196e-8/energy4.9630e-8.
NativeBlockTimerpausesparent(confirmedtimer.hpp):setupmedian166.680→50.159s,
coarse160.074→292.581s, PC256.687→253.330s, KSP79.247→62.916s,
IO19.219→19.160s. No summingindependentphasemedians/inclusiveranges.
InitialGPU2366–2373MiB/host84.08–84.86GB; globalNVMLpeak~15828–15845MiB
includesdesktop, no physicalVRAMreductionclaim. Managedalloc56.943→
41.950GB/cudssallocated25.008→13.348GBaredifferentlogicalmetrics.
No1.5xtimespeedup, RAMshort25%ambitionby1.4034pp. Usefulmemorygainwith
timecostexplicit. Writtenartifacts7.061GB/sixjobs, no diskhotworkspace.
Detailsdocs/milestones/paired-medians.md, phase/background/allocartifact
andP2proofJSON. NextM7.5meaningfulnewgeometry,thenpackage/audit;goalactive.
M7.2checkpoint: sameLuna docs-garden PASS/no material inconsistencies;
explicit compact Pareto table added with local rental0USD/energyunmeasured,
logical allocations versus physicalVRAM limits retained. Rootdiffreview,
docschecker anddiffcheck PASS. Prior179Python/8shell andactual3pairCLI
PASS; nativeA6/defaults unchanged. Next prepare M7.5newgeometry.

## EXP221–222 prereg — M7.5 geometry generalization
Previousgoalturn classifiedprogress: M7.2statistics/reportcommitteda42568f,
all3pairedKPASS/nativeunchanged/cleancheckpoint. NextM7.5preserved.
Newgeneric--fixture-dir verifies family/frozenmedium/archive/config/mesh,
keepsantennafeedregion3; no native/defaultchanges. ExperimentalNumPy
compactzdeformation, quadraticTet10detBernsteinpositiveboundauditsallcells,
notcorner-onlytest.184Python/8shellPASS. Originalsourceantenyreadonly.
TwoPREPONLYmeshesrad70/rad57alsomovedradome, retainednotGPUrun. Final
rad50/55,z2/11/14/30,shift2mm movesdirector+carrier/spacers/rods only;
radome/mainPCB/feed/reflector/absorber/ports unchanged.147607nodeschanged,
1601320curvedtetboundspositive/originalandnew; protected37996unchanged.
Finalfixtureartifacts/m7-director-gap-plus2-geometry-20261022,
SHA c66c6f55c8e28b3efe87bdc4eac373e65d69b71cb016454a2c92c7d4dbfaf8fb.
NativeverifiedA6unchanged. Actualoldreference+seed rejectednewmeshidentity;
stale-data-check.jsonstored, material/BC mismatch controlsPASS.
EXP221prereg: newcoldFP64reference,exact3.500GHz/2ports/medium/RIGHT/K64/
Tol1e-6/fresh2/defer/energy/releases/snapshots/1800s/60GiB/no swap/hostguard.
Outputartifacts/m7-director-gap-plus2-reference-20261022; EXP222candidate
onlyafterrootreferenceaudit. No seeds/PROM/TF/profiler/cloud/defaultchanges.
Candidatewillbesamefixed3policy/ownnewref;frozenKunchanged. Notantenna
retuningorphysicalvalidation;onepairnotmedian. Detailsgeometry-generalization.md.
EXP221rootreferencePASS:3.500GHz/2ports/newmeshSHA c66c6f55…,
764.0080178s/61139226624B,44/45iter/originalraw<=8.0418e-7.
Actualmesh/config/native/inventory/finiteRFenergy/fresh2setup audited.
CoarseCSR old5d0411e5/3139379a→new4afd6442/94fab340, bothnewRHSsame
newmatrix, no stalefactorreuse. root-reference-check.jsonstored.
EXP222prereg: ownnewreference, exactsameconfig/native/3.500GHz/bothports/
medium/RIGHT/K64/Tol1e-6/directFP32storage/scaledFP32LU+3fixedFP64IR/
reuse/defer/energy/releases/snapshots/1800s/60GiB/no swap/hostguard.
No seeds/PROM/TF/profiler/defaultchanges/cloud. FullfrozenKafterrun.

EXP222rootfullKPASS: exactnewmesh/currentA6/3.500GHz/2ports, maxΔS3.5071e-8/
ΔVSWR5.5569e-8/relativeenergy1.0187e-7/power6.6581e-9,14fieldrows/maxE
6.3829e-7/B5.2650e-8. C44/45iter/raw<=9.4438e-7,91coarseapply/count3/
maxcoarse6.8592e-5. Rfresh2setup/Cbuild1+reuse1 confirmed. Receipt
artifacts/m7-director-gap-plus2-fixed3-qualification-20261022.json.
ActualcostscopeJSON: managed57.398→42.172GB/cudssalloc25.284→13.481GB,
globalNVML15821/15819MiBincludesdesktop; no physicalVRAMreductionproof.
Onepairtime764.008→755.874s/RAM61.139→46.601GB; no median/globalclaim.
Threepreparations+twojobsordinaryartifacts3.789GB, no diskhotworkspace.
OriginalFP64vsnewFP64VSWR3.5GHz1.577/1.668→1.401/1.485isgeometricphysics,
notprecisionerror/newproductionbaseline. M7.5PASS;nextM7.3package/M7.4audit.
M7.5checkpoint: sameLuna docs-garden PASS/no edits/material inconsistencies;
rootreviewcode+docs/actualreceipts,184Python/8shell/docschecker/diffcheckPASS.
NativeverifiedA6/no dependencies/cacheflush/rebuild/defaultchange. M7.5
completewithinonechangedgeometryscope;M7.3packageandM7.4auditopen.
No simulationactive. Nextinspectpackage/reproduction/checkcleanupdeadline
without recompilingorlargeGPUjobs; goalactive.

## M7.3 package prereg — EXP223 onwards
Previousgoalturnprogress: M7.5newgeometryKPASS committed8312390.
NativeA6unchanged. Packagegap: oldthinimagewasstale/notcurrentM7; runner
alwayshostmountednative, so addactualimagepayloadverificationandno-overlay
execution. Newbundleincludescompilerinputhashsources/tools/frozenarchives/
smallcurrentFP64reference/explicitprofilesandboundedexample; pinnedimage
remainslocal, no3GBperrunupload. No dependency rebuild/cacheflush.
188PythonPASS includingmanifest/native/base-layer mismatch, checksum/paths/
missing/symlinkpayload, unsupportedprofile/overlay/walltimeguards.
Smallimage-native examplepreregistered; runmemory thenFP64, rootK/TEMaudit,
then1sdeadlineandcontrolledownprocessSIGTERM/cleanupcheck. Nofullantenna.
Bundle artifacts/m7-sm120-bundle-20261022/image localhost/palace:m7-sm120-20261022,
sourceFP64reference artifacts/m7-w2-tiny-reference-20261022.
Goal/M7active; M7.3notcompletedbybuildalone; next docs/runtime-package.md.
EXP223–224 initialbundle example memory/fullFP64 execution+analyticTEMPASS,
actualimage43ac46f6…/nohostnativeoverlaysconfirmed. MemoryfullKvsincluded
referencePASS (receipt m7-package-tiny-fixed3-qualification-20261022.json).
Rootalsoattemptedextra bitwise-equalityassertionforFP64replay; notidentical,
thoughraw/TEM/RFconsistent. BitwiseidentityisnotfrozenK; insteadimprove
referenceprofiletoexplicitnativeweightedfieldcomparisonagainstincludedref.
No accuracygateweakened; initialartifactsretained, no antenna timeclaim
from tiny/profileverificationoverhead. Newr1bundlecapturescurrenttoolswith
fieldrefbothprofilesandreadylifecyclecheck. EXP225memory/EXP226reference
willbothbevalidatedagain; EXP2271sdeadline+ownwrapperSIGTERMafterlive
coarsemarker. Newbundle artifacts/m7-sm120-bundle-r1-20261022, sameimage/
nativeA6, no rebuild/cacheflush.188PythonPASS; notcompleteyet.
Finalpre-runbundle r2 artifacts/m7-sm120-bundle-r2-20261022; r1PREPONLY
retained. Referenceprofile nowalsohasnativefield-referencequalitygate.
LifecycleunitcontrolsPASS inclSIGTERMwithoutpostexitinspectfile and
deadlinerejectOOM;190PythonPASS. EXP225/226r2memory/reference planned
exactwrappersfrom/tmp, thenrootauditbeforeEXP227lifecycle. NativeA6and
image43ac46f6… unchanged. No referencebitwisecriterion: weightednormgates.
EXP225/226 rootfullK/TEM/image-nativeauditPASS. R2memory18.344s/
582926336B/raw[9.7162623e-7,7.7029075e-7],coax4regionalrows,
maxE7.1847e-7/B1.2419e-8; reference18.410s/568180736B/raw[9.5930524e-7,
7.6820681e-7], maxE1.1968e-13/B3.2156e-13. Workerabbreviatedrawforboth
as~9.716e-7; rootreadcorrectdistinctvalues. TEMvolumeL2~.4953%/.4558%,
q4→6delta2.17445e-6, samples/points/energyfrozengatesPASSbothprofiles.
Actualargvimage-native/nohostnativeoverlaysconfirmed. Receiptm7-package-r2-
example-qualification-20261022.json andtiny-fixed3 receipt. Tinycostincludes
image/payloadchecks, no antennaspeedclaim. EXP227nextdeadline/SIGTERM.
M7.4auditnote: inspectqualifierbindingbetweenactualnativefield-reference
mountinventoryandprovidedR; previousrootpairsuseownRbutautomatedparser
shouldnotacceptanotherreferencewithcompatibleidentityalone.
EXP227firstdeadlinecheckFAILretained: appstopped~.855s/cleanupPASS/noOOM,
Podmanattach255/StateExitCode-1 didn'tmatchpreassumed137/143; SIGTERMnotrun.
IndependentCPUsleep30/timeout1onSAMEimage reproduces255/-1/1.95s; versions
Podman6.1.4/conmon2.2.1recorded, upstreamconmon.cmainkeeps exit_status=-1
in timeoutbranch. NoaccuracyKchanged. Lifecyclecheckeraccepts-1onlywith
separateCPUwitnessmatchingimage/version/timeout1/sleep30/noOOM/shorttime/
attach255 plusactualtarget1sconfig/shortduration/cleanup/incomplete.
OriginalFAILnotrewritten; nextnewlifecycle-r1. Source/control inartifact
m7-podman-timeout-control-20261022.json; no fixed-install-source claim.
Package r3 inventoryverified: comparedr2, onlylifecycleexperimentanditsunit
controls changed; allruntimesources/native/fixtures/reference/imageidentical.
191PythonPASS. Finalbundle artifacts/m7-sm120-bundle-r3-20261022.
EXP228memory/EXP229FP64repeat finalbundlefrom/tmp anyway, thenEXP230
lifecycle-r1 withseparateCPUcontrol witness; noaccuracygatechanges.

EXP228/229rootfullK/TEM/image-native/source/native/inventory/cleanupPASS;
rootreceipt artifacts/m7-package-r3-example-qualification-20261022.json,
fullcombinedtinyreceipt m7-package-r3-tiny-fixed3-qualification-20261022.json.
EXP230rootreadactualdeadline&SIGTERMreceiptsandcontainerabsencePASS;
przerwaniawciężniesąRFsuccess. EXP231legacyfullKand3hostnativeoverlays
PASS,16.861s/raw<=9.715e-7. R3payload745files206881879Bbeforecompanion
evidence. Fourstagingbundles+allsmallruns~0.904GBordinaryartifacts; no
nativebuild/cacheflush/hotSSDworkspace/cloud. Finaldoc/evidencecompanions
maychangeonlydocumentation/receipts, nevertestedruntime/native/inputbytes.
M7.3PASS, nextM7.4completeauditandreferencebinding.
FinalR3bundle docsupdatedaftertests (whitelistedMDonly), VALIDATION.md/json
companionsadded; manifestinventoryrefreshed andverified. Rootassertedall
testedruntime/source/native/fixture/referencebytesunchanged. SourceGitHEAD
isprovenanceonly, filehashesbindworkingtree. Buildglobalflagfalse/defaults
unchanged, M7.4pending. Evidence m7-package-final-doc-update-20261022.json.
M7.4additionalauditnote: inspectearlySIGTERMduringpodmancreate/command
metadatawrite beforemaincleanupscope; currentsuccessfullifecyclecovers
afterlivecoarsemarkerand1scontainerdeadline, notallpreparationphases.
M7.3finalcheckpoint: sameLuna docs-garden PASS/no edits/materialgaps;
reported75BpayloadcountdriftwaslastPLANMDcheckboxedit, notcode/inputchange.
Currentauthoritativeimmutablepayload 747files/206901199B; derived
pycache/unpackedmesh excluded (fixtureSHAstillchecksmesh). Pointerstored
build/sm120/runtime-bundle.json, finalaudittestpending explicit.
Rootdiffreview and191Python/8shell/docschecker/diffcheckPASS; nativeA6
verifiedunchanged. No simulationactive, builder/cachepreserved, no cloud.
NextM7.4referencebinding/earlypreparecleanup/fullrequirementaudit, then
recheck15W5+3medians+newgeometryonfinalqualifierwithoutnativeGPUrerun
unlesscodechangesneedone. Goalactive; no completionclaim.

## M7.4 audit start — EXP232 prereg
Previousgoalturnprogress: M7.3code/package/tests/liveexamplescommitted854c8a7.
AuditreadMILESTONES/currentcode; foundnativefieldcompareboundonlybyphysics,
notexactreferencebytes. Addcaptureoffieldreferenceidentity/inventoryatlaunch
andqualifierexactbindingtoactualreadonlymount. Legacyrequiresstillpresent
actualmountbytes; newrecordcanmoveoriginalonlyifprovidedRmatchesrecord.
Testsrejectdifferentbytes/samephysics, identity/mutable/missinglegacy/
duplicate/writablemounts; no Kthresholdchanges.193PythonPASS.
Secondgap: podmancreate/commandmetadatawriteoutsidemaincleanupscope.
Movemetadata+createunderfinally; preservedsuccesselapseddefinition, add
launch_phase; failureunitcoversbothmetadataandcreate/incompletereceipt/rm.
NativeA6unchanged. EXP232readytest tools/experiments/prepare_interrupt.py
withprivatePATHshim: realpodmancreatefirst, markerstatecreated/Pid0,
3sboundedreturn-delay, SIGTERMonlyownlivewrapperPID, no solverstart.
Outputartifacts/m7-early-create-interrupt-20261022. No systemPATHchange,
appsclose/cloud/rebuild/cacheflush/permissionschanges. Rootauditsreceipt.
Laterrequalifyall15W5+medians/newgeometryandupdatedbundlewithsmallcontrols.
Fullrequirementauditstillpending; goalactive.

## M7.4 explicit retry — EXP233–236
User requested restart. GPU check:2358MiB used/13542MiB free,3% utilization.
EXP232 pre-start SIGTERM receipt already PASS; no need rerun same evidence.
Updated Python runner/qualifier only; nativeA6 unchanged. Prepare bundle r4
using verified existing image43ac, no native/dependency build. Same Luna runs
tiny memory then FP64,60s limits, then1s deadline/own live SIGTERM controls.
Root checks exact reference binding, raw/K/TEM and cleanup. No full antenna,
cloud spend or app unload. Full M7.4 requirement audit still pending.

EXP233–236 zakończone: R4 memory17.317s / FP6418.377s end-to-end,
oba39/42iteracji, prawdziwe raw<=9.704e-7, K/TEM/volumeL2 PASS.
Root sprawdził dokładne bajty referencji, image-native i brak kontenerów.
Delta S9.819e-10 / VSWR1.936e-9 względem dołączonej referencji;
to nie pomiar przyspieszenia anteny. Deadline i SIGTERM podczas pracy PASS,
EXP232 przed startem także PASS. Artefakty opisane w docs/runtime-package.md.
NativeA6/cache bez zmian, bez kosztów cloud. Pełny audyt M7.4 nadal otwarty.

Retry checkpoint:193Python/8shell/docs checker/diffcheck PASS; ta sama
Luna wykonała docs-garden bez zmian, root przejrzał diff i dowody.
M7.4 pełny audyt pozostaje otwarty; brak aktywnych symulacji po tej próbie.

## M7.4 ROI/phase audit — EXP237 prereg
Previous goal turn made progress: commit4e86a57, R4 live examples and lifecycle
plus193Python/8shell passed. Full audit found K4 explicit slot-region/phase
assessment weaker than whole material-domain complex L2 evidence.
Add CPU saved-field replay linked to unchanged actual Palace mesh loader
(Load/nondimensionalize/Partition/RefineMesh); same ND2/RT1 and snapshot DOF
headers, no solve/native rebuild. First cached helper, then tiny mapping
control against native complex norm. Antenna ROIs fixed BEFORE inspection:
PTFE3, entire PCB2, four x/y-sign PCB sectors at radius>=6mm (includes slot
neighborhoods; not pointwise slot-tip convergence). Positive Duffy product
rules levels4/6; complex L2<=1%, reference-weighted local phase RMS<=asin(.01)
=0.572968deg; undefined phase reference-energy fraction<=1e-6. No phase fit.
Require exact same native/config/mesh/reference-byte binding, original K;
for tiny/global PCB/feed replay verify agreement with native norm, not just
DOF counts. CPU4threads/12GiB/no swap/180s each; read stored results once,
no hot SSD workspace. New helper/source/input/outputs hashed. If mapping
control fails, no antenna qualification or goal completion claim.

EXP237 mapping control PASS: positive q4/q6 complex L2 matches native region1
within3.582e-8 relative; exact same DOF/preprocessing, phase assessed without
fitting.43.529s CPU. Cached helper compilation initially lacked SLEPC enum
macro; added same default PALACE_WITH_SLEPC, native solver unchanged.
Next one 3.500GHz antenna replay,180s cap, no solve.

EXP238 offline antennaROI timeout180.8s/255/noOOM preserved; no fields,FAIL.
Optimized only evaluator coefficient/orientation extraction once per cell and
physical VShape once per point; actualnative unchanged. EXP239 tiny15.821s
vs43.529s, all8norm/phase metrics within1e-12 absolute; mapping controlPASS.
Next EXP240 antennaROI same180s cap.

EXP240 CPU timeout180.5s/noOOM afterE/P1/q4; preservedFAIL. Added fixed
referencebasis tables and physical ND/RT Piola mapping. EXP241tiny9.495s;
allnorm/phase metrics match originalMFEM evaluator within1e-12 absolute.
No native/operator/precision/gate changes; next EXP242 antenna same180scap.

EXP242 remainsFAIL180.299s/noOOM; completedE/P1q4+q6 andB/P1q4
beforedeadline. Three whole-replay limits motivate different scheduling:
checkpoint perquadrature and split by(port,field), same ROIs/q4/q6/norms.
No narrower quality region or relaxed threshold. Four bounded chunks required
for coverage; failed earlier runs never promoted. EXP243–246 readyafter
helper-only cachedbuild; no new FEMsolve or native change.

EXP243–246 four CPU chunks complete141.1/140.3/141.1/145.6s; root48rows
coverage/thresholds PASS, maxL2=4.0782561e-7, phaseRMS=1.0513844e-5deg,
undefinedphase0. PCB/feed norm vsnative agreeswithin9.954e-8 relative.
To coverremainingW5 without15mesh reloads, batch5 same-normalizedphysics
pairs inoneCPUprocess; mandatory q.summarize guards exact mesh/build/config
exceptfrequency. Sameperfreq/port/q/ROI gates, no reducedaccuracy/regions.
Three sequential CPUbatches cap900s each,12GiB/no swap/4CPU, no newFEMsolve.
EXP247–249 prereg coversall15f. Readonly stored fields, no hotdiskworkspace.

Pre-launch resourcecheck24CPU/76.114GB MemAvailable. EXP247–249 mayrun
3independentCPUbatches concurrently (each4CPU/12GiB/noswap/900s; total12
CPU/36GiB), sameLuna onlybabysitting, noGPUcompute. This changes scheduling
only and is not a timed solver benchmark. Helper/source frozen during jobs.

EXP247–249 all900s timeout/noOOM/FAIL retained. Checkpointselectionpolicy:
accept only independently complete48-row offlinefrequency records after exact
coverage/gates and nativePCB/feed check; originalRF solves MUSTbecomplete.
Never callfailedbatchPASS oracceptpartialfrequency; this avoids rerunning
completepostprocessing, not promotionofincompleteRF. Rootverified6complete
frequencycheckpoints;9remain. New completefrequency900s jobs, max3parallel;
EXP250–258 ready before execution. Full15freqqualification stillpending.

EXP250–259 dispatch10readycommands:9remainingW5singlef plusnewgeometry
localphase/ROI. Launcher3CPUjobsatmost,900s each, stopsnextwaveonFAIL;
SIGTERMhandleraddedtohelperCLI for cleanup.196PythonPASS. Sourcehelper
C++/native unchanged; ROOT still handles allnumericaldecisions.

W5localfields finalrootaudit PASS: all15frequency/2port/E+B/6ROI/q4+q6
720rows; fresh all15 originalRF requalification PASS. NativePCB/feed norm
agreement<1e-4 relative, thresholds unchanged, checkpoints parentFAILkept.
Artifacts m7-final-W5-local-fields-phase-20261022.json and
m7-final-W5-reference-binding-current-20261022.json. Changedgeometryoffline
lastjobpending; fullauditnotcloseduntilthatandfinalregressions/docsgarden.

EXP250–259 all10complete/noOOM; rootvalidated newgeometry48rowsPASS,
maxL2=6.382824e-7/phase1.642138e-5deg/nativeagreement1.134e-7relative.
Antiresonance currentRF recheckPASS; rigorous discrete phaseRMSupperbound
from complexL2 <=8.079e-5deg. AllW5/native/fields/phase nowcomplete.
Offline artifacts892727B; checkpointwriteupperbound5923264B excludingnormal
compiler cache; elapsed-processsum7924.609s(notwalltime). NoFEM/GPUsolve
inreplay.197PythonPASS. Futurehelper rejects knownbad5freqbatch/whole180s
antenna before work and avoidsduplicatequalifier scans. Next finalbundle
smallliveverification, docs-garden/rootreview/commit; nofullantennarerun.

EXP260–263 finalbundle actualimage native/nooverlay PASS; root K/TEM/volumeL2
/raw/referencebytes/cleanup checked. Memory18.498s/FP6418.408s aretinychecks,
notantenna performance claim.197PythonPASS inrepo AND separatebundle from/tmp;
8shell/docschecker/diffcheckPASS; no activecontainers. Finalauditmatrix in
docs/milestones/final-audit.md, scopequalificationledger staged inartifacts.
Remainingonlydocs-garden/rootdiffreview, closingstate+docpayload inventory
update(localdocs/evidenceonly), commit and goal completionaudit.

Docs-garden identified stale INDEX and implicitROIaggregation documentation.
RootfixedINDEX, added explicit assessCLI usingalready-testedassessfunction,
frequency-duplicateguard andCLIregression. ActualassessCLI720+48PASS.
Runtime/reproduce/native/input/referencebytesunchanged; finalbundleupdated
onlyMD andanalysis-onlyCLI/test; rerununitcoverage. Nativebuildnotneeded.

## M7.4 CLOSED — końcowy checkpoint2026-10-22
Poprzedni turngoal: postęp (4e86a57/R4); obecny audyt dołożył pełne720W5
ROI/phase i48changedgeometry, freshRF/native/referencebinding/W2medium
orazantiresonance PASS. NativeA6 i medium bez zmian.197→198Python PASS
wrepo i niezależnym finalbundle z/tmp;8shell/docschecker/diffcheck PASS.
Ta sama Luna wykonała2przeglądy docs-garden; realneuwagi INDEX i jawnego
assessCLI usunięte, finalreview PASS. Root potwierdził dowody i przejrzał diff.
Rekomendacja: explicit directFP32storage/FP64arith, scaledcomplexFP32LU+3IR,
reuse/defer. Mediana60.684→46.364GB cgroup (−23.5966%);745.458→747.733s
(+0.305%, brak speedupu). Physical peakVRAM/TCproduction nieudowodnione.
M2/FDTD/AMS/hybrid/WMMA/PROM negative assessments zachowane, niepromowane.
Raport: docs/milestones/final-audit.md; finalpakiet:
artifacts/m7-sm120-bundle-final-20261022. QUALIFICATION.json zakresowy;
globalny native numerically_validated=false bez zmiany. Bez cloud/swap/SSD
basis, zwykłeI/O zmierzone wraporcie. Nie ma activepomiarów/nextmilestone;
Active:none. Zakończenie celu po ostatnim sprawdzeniu inwentarza i commicie.
