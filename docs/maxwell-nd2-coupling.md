# M2 — rzeczywisty mortar ND2/BC-RBC i sparse Schur

EXP34, 2026-10-19. **Kontrole implementacji PASS, próg całych pól FAIL**.
M2/goal aktywne; brak promocji dla anteny. Odniesienie objętościowe:
[EXP33](maxwell-nd2.md), wybór dualnego parowania: [EXP32](maxwell-coupling.md).

## Model i równania

Transparentny wielościan eps=mu1/k1, exp(−iωt), exactEx=exp(iz),Hy=exp(iz).
Ten sam FEMND2/MFEM4.9, globalDOF/faceorientations i geometria jakEXP33.
Elektryczny trace t=E×n wRWG0, magnetyczny h=H×n wBC, testRBC=n×BC.
To przestrzenie wariantu `electric_dual` przypiętego Bempp, nie ND2trace.

Fizyczna kwadratura po barycentrictriangles daje sparseB=<vND2,BC> i
osobnoD=<RBC,vND2×n>. Sprawdzamy D=−Bᵀ, nie konstruujemyD jako−Bᵀ.
G=<RBC,RWG>, G*R=D. Nie odwracamy osobliwego Gprimal=<SNC,RWG>.

Układ, C=G/2+Kbem, A=Kcurl−k²M:

```text
A*u − ik*B*h = 0
C*G^−1*D*u + T*h = rhs_incident_RBC
Schur = T + ik*C*G^−1*D*A^−1*B
```

`bempp_nd2_coupling.py` zachowuje sparseFEM i sparseB/D. Jeden sparseLU(A),
jedno LU(G), RHSbloki16. Gęsty jest mały boundarySchur, nie globalnyFEM.
Tylko≤512FEMDOF dodatkowo rozwiązujemy pełny gęsty układ jako niezależną
kontrolę eliminacji. Residuum dotyczy obu pierwotnych równań, nie tylkoSchur.

## Brak w upstream i kontrolowane obejście

Pierwszy run `artifacts/m2-nd2-bc-coupling-level1-20261019`:
**FAIL15,625s/exit1/noOOM**, po `nd2_bc_mortar_validated`.
Pinned `core/dense_assembler.py:22` jawnie odrzuca
`requires_dof_transformation` dlaBC/RBC. Brak pól/Schur dla tej próby.

Izolowany `TransformedDense` nie zmienia/nie patchuje upstream ani nie
wyłącza checku. `make_localised_space` tworzy bazę beztransformacji.
Te same regular/singularMaxwellkernels Bempp liczą A_local, potem
Qtestᵀ*A_local*Qtrial, Q=map_to_localised_space*dof_transformation.

- Punktowe porównanie reprezentacji lokalnej/globalnej≤6,24e−16.
- Oba operatory T/K na RWG/SNC porównane ze standardowym publicznym
  assemblerem wlevel1: błędy1,22e−16/8,90e−17. Nie zastępuje to walidacji pól.
- BC/RBC są użyte z rzeczywistymi transforms, normalnymi i kwadraturą;
  nie utożsamiamy `local2global` z finalnymi globalDOF.
- Źródło API: przypięty Bempp-cl commit
  `a1eaaef9f96b9dd3d7c56b076740e06852a6e1c0`,
  `api/operators/boundary/maxwell.py`, `api/space/space.py`,
  `core/dense_assembler.py`, `core/numba_assemblers.py`.
  Farfield korzysta z natywnego assemblera potencjałów, który sam stosuje transforms.

## Wyniki

| Poziom | FEM / BEMDOF | Coupled E / H L2 | Dirichlet E / H L2 | Runner / Schur solve | RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 184 / 30 | **17,743% / 15,224% FAIL** | 2,205% / 3,341% | 35,789s / 0,00878s | 680MB |
| 2 | 1228 / 120 | **10,072% / 5,645% FAIL** | 0,591% / 1,054% | 43,671s / 0,03005s | 718MB |

- Physicaladjoint/interiortangent/normal/coordinatechecks≤8,28e−16.
  Exactconstanttrace surfaceL2≤9,79e−16. Liniowy trace nadal34,055→16,634%:
  dokładna projekcja nie czyni RWG0 przestrzenią ND2.
- Rawblock3,37e−15/1,14e−14, tinyfull vsSchur1,93e−14,
  q6vs8delta≤8,06e−13. Wszystkie wykonane localrunyexit0/noOOM.
- Spuriousfarmax0,005935/0,002338<0,01, energyerror/π3,26e−7/7,20e−7<1e−3.
  **Residuum, farfield i energia PASS nie kwalifikują całych pól.**
- Coupled−DirichletE18,227→10,111%, H16,296→5,827%, normowane do exactincident.
  Nie jest to ścisłe oszacowanie całego błędu. Referencja ma exactDirichlet
  na tej samej domenie; nie jest większym FEM z absorberem.

Z dwóch poziomów obserwowane log2ratios≈0,817(E)/1,431(H), nie dowód rzędu
asymptotycznego. Różnica przy tym samym FEM wskazuje koszt błędu dołączonego
sprzężenia/przestrzeni brzegowych. Nie rozstrzyga jeszcze, czy dominuje trace
E, reprezentacja BC prądu H czy sam niedopasowany mortar.

## Koszt i decyzja

LocalBEM360²→1440² complex128: **2,074→33,178MB na jeden operator**.
Finaloperator/Schur14,4→230,4KB; localmatrix ma144×więcej danych niż wynik.
OperatorT/K są składane kolejno, więc nie sumujemy obu localpeaków jakoRSS.
M/KCSR0,149→1,128MB, B/DCSR0,067→0,377MB. RHSFEMbloki47,1→314,4KB.
Tylko wlevel1 tinyfullcoupled732736B, poza nim brakdenseglobalFEM.

Poziom2: do mortaru12,33s, T gotowy27,92s, C gotowy38,40s,
Schur38,43s, kontrolapól38,84s. Setup/JIT/operatorassembly dominują, nie sparseLU.
Timery obejmują JIT/runtime; nie ekstrapolować ich jako czystego kosztu quadrature.
Nie jest to porównanie przy równym błędzie ani zmierzone przyspieszenie anteny.

**Zachować witness implementacji, odrzucić promocję obecnego wariantu.**
Level3 tego samego sprzężenia NOT RUN: następna praca ma rozdzielić przestrzeń
powierzchniową od ustalonego, zakwalifikowanego FEM, zamiast zagęszczać obie naraz.
Potrzebne również assembly bezfull-localdense, stabilizacja, dielectricFEM,
porty/metale oraz reprezentatywny koszt anteny. M2 nie jest ukończony.

## Odtworzenie i dowody

```sh
python3 tools/experiments/bempp_oracle.py run artifacts/new-nd2-coupled-l1 --physics nd2-coupling --level 1 --seconds 180
python3 tools/experiments/bempp_oracle.py run artifacts/new-nd2-coupled-l2 --physics nd2-coupling --level 2 --seconds 180
```

Artefakty `artifacts/m2-nd2-bc-coupling-level{1,2}-local-20261019`.
Root sprawdził aktywne source/helper/C++/binarySHA, terminalstate i qualityFAIL
w `artifacts/m2-nd2-bc-coupling-root-analysis-20261019.json`.
71testsPASSwpinnedenv, systemowo63PASS/8SKIP(SciPy). Dwa nowe testy Schur
porównują niezależny pełny complexblock, trace, RHSchunking i brak mutacji T.
Case testuje prawdziwe MFEM/Bempp; unitmocks nie zastępują tych runów.

CPU6GiB/4CPU/tmpfs/noaddedSwap/networknone/rootRO/deadline180s.
Brak nowych buildów/paidcompute/GPUrunów; cachedMFEM/JIT zachowane.
Wszystkie macierze/workspace RAM, JSON/logi zwykłe wyniki.
