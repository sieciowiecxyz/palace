# M2 — globalne ND2 przed sprzężeniem z BEM

EXP33, 2026-10-19. **Małe odniesienie objętościowe PASS na poziomie3**.
M2/goal aktywne. Nie jest to rozwiązanie FEM–BEM ani kwalifikacja anteny.
Poprzednie [ND1 i parowania](maxwell-coupling.md) pozostają osobnymi dowodami.

## Implementacja i zakres

- `tools/experiments/mfem_global.cpp`: rzeczywisty serialMFEM4.9,
  ND_FECollection(2)/FiniteElementSpace, pełne sparseBilinearForms mass/curl,
  graniczneDOF, ProjectCoefficient i GetVectorValue/GetCurl.
- `maxwell_nd.py`: ctypes, walidacja topologii/Jacobianów, eksportCSR i
  fizycznej globalnej bazy. GetElementDofs daje znakiDOF; InvTransformPrimal
  obsługuje mieszanie faceDOFs. To nie rozszerzenie signedpermutationND1.
- `mfem_nd2.py`: transparent eps=mu1, k1, exp(−iωt), exactEx=exp(iz),
  exactHy=exp(iz). Ten sam wielościan z objętością4π/3, refinement20→160→1280tet,
  bez rzutowania wierzchołków na sferę. Referencja nie wymaga geometrii kuli:
  analityczna fala płaska jest poprawna wewnątrz dowolnej tej domeny.
- TangentialDirichlet: analyticE interpolowane przez MFEM na boundaryDOF,
  interior z (K−M)ii*u_i=−(K−M)ib*u_b. Nie stosujemy BEM/absorbera/exterior.
- CPU complex128 sparseLU w SciPy; nie CUDA/PA. Produkcyjne mediumOrder2/PA,
  solver Palace i jego referencja pozostają bez zmian.

MFEM raportuje `MFEM v4.9 (release)`, `GetGitStr()` pusty. Nie przypisujemy
mu SHA innego checkoutu. Binarka i oba źródła C++ przypięte wmanifestach.

## Niezależne kontrole

1. Fizyczne vshape/curlshape z MFEM zmapowane do globalnychDOF; osobna
   kwadraturaDuffy4 rekonstruuje mass/curl i porównuje z globalnymiBilinearForms.
   Gate relative1e−11; rzeczywiste błędy≤8,86e−16.
2. StałeE i linioweE=(z,x,y), curlE=(1,1,1), odtwarzane punktowo po
   ProjectCoefficient. Gate absolute1e−11; max≤3,56e−14 na wszystkich komórkach.
3. Eksportowana baza vs rzeczywisty GridFunction::GetVectorValue/GetCurl;
   max≤1,43e−14. Nie sprowadzamy ND2faceDOFs do samych znaków.
4. Licznik rzeczywistych zmian InvTransformPrimal(I) != I:
   **19/20,147/160,1167/1280** komórek. Sam IsIdentity() w MFEM opisuje klasę
   transformacji, a nie konfigurację orientacji konkretnej komórki.
5. Niezależna fizyczna całka całych E/H względem analitycznej fali, q6 vsq8.
   Gate różnicy norm1e−6; max6,94e−12. RawinteriorRHS gate1e−10.
   Pola normowane L2 przez sqrt(objętości), nie przez przybliżone pole.
6. Poziom1 sprawdza także niezmieniony legacyND1CAPI względem Whitney;
   maxmatrixerror6,03e−16. Nie jest to pełny ponowny sweep ND1/anteny.

## Wyniki

| Poziom / tet | ND2 / boundaryDOF | Dirichlet E / H L2 | Sama interpolacja E / H L2 | Runner / solve | RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 / 20 | 184 / 100 | 2,2046% / 3,3413% | 2,4518% / 5,3151% | 0,536s / 0,000327s | 281MB |
| 2 / 160 | 1228 / 400 | 0,5910% / 1,0541% | 0,7192% / 2,9080% | 1,051s / 0,005876s | 288MB |
| 3 / 1280 | 8936 / 1600 | **0,1505% / 0,3317%** | 0,1860% / 1,4681% | 5,514s / 0,5362s | 433MB |

`analytic_target_passed=true` dopiero dla **rozwiązania Dirichlet poziomu3**.
Sama interpolacja/projekcja E na ND2 ma nadal H>1% — to inny wektor,
nie rozwiązanie równania wewnętrznego. Nie mylić kolumn ani nie kwalifikować
projekcji tylko na podstawie residuum/znanej dokładności FESpace.

Rawinterior:6,83e−16/1,73e−15/4,09e−15. Łączne M/K CSR148552/1128424/8793480B.
Nie alokowano denseglobalFEM; RSS zawiera runtime/importy/obie kopie CSR,
rekonstrukcję kontrolną i sparseLU. Brak porównania pamięci/czasu anteny.

Artefakty `artifacts/m2-global-nd2-level{1,2,3}-q6-20261019`.
Root sprawdził case/fem/nd/C++/binary/referenceSHA i terminalstate w
`artifacts/m2-global-nd2-root-analysis-20261019.json`. Wszystkie q6runy
exit0/noOOM/executionPASS. Poziomy1/2 mają analyticfieldFAIL zachowane.

## Odtworzenie, cache i pierwszy FAIL

```sh
python3 tools/experiments/mfem_bridge.py build
python3 tools/experiments/bempp_oracle.py check
python3 tools/experiments/bempp_oracle.py run artifacts/new-nd2-l1 --physics nd2 --level 1 --seconds 120
python3 tools/experiments/bempp_oracle.py run artifacts/new-nd2-l2 --physics nd2 --level 2 --seconds 120
python3 tools/experiments/bempp_oracle.py run artifacts/new-nd2-l3 --physics nd2 --level 3 --seconds 120
```

Bridge to2TUs/ccache+linkSO w istniejącym builderze /opt/view. Pierwszy
build3,361s, korekta licznika3,310s; zależności i Palace nie były przebudowywane.
Recepta sprawdza osobne SHA legacy/globalCpp, builder/runtime i flags.
Mały buildlog zachowuje również fallback SIGTERM→SIGKILL przy zatrzymaniu
kontenera sleep; nie oznacza to błędu kompilacji, SO i exitbuild zweryfikowane.

Pierwszy level1 w `artifacts/m2-global-nd2-level1-20261019` pozostaje **FAIL**:
containerexit0, brakOOM, lecz q4vs6delta3,192e−6>1e−6. Poprawiono wyłącznie
diagnostyczne całkowanie błędu na q6 z kontroląq8. Nie zmieniono siatki,
ND2, operatora, progu1% ani progu zgodności kwadratur1e−6. Dawna różnicaq4vs6
nadal raportowana także w nowych case.json. To nie speedup ani promocja FAIL.

Wszystkie tablice robocze RAM, CPU6GiB/4CPU/memory-swap=memory, tmpfs/rootRO,
networknone, deadline120s. Cachebuild/JIT i końcowe JSON/logi są osobną funkcją.
Brak paidcompute/wyłączania aplikacji użytkownika/GPUrunów.

## Następne prace

1. Rzeczywisty BC/RBC mortar: sparse B=∫v_FEM·BC i niezależnie
   D=<RBC,v_FEM×n>; gate D=−Bᵀ. Wyznaczać R przez GdualR=D,
   nie odwracać Gprimal ani nie traktować niedopasowanych przestrzeni jako exacttrace.
2. Odtworzyć constanttrace; zmierzyć błąd liniowego/płaskiego trace i wpływ
   zbieżności samej powierzchni przy ustalonym FEMND2. Małe Gramrank/condition
   z EXP32 nie dowodzą stabilności dla portów/siatek graded.
3. SparseFEM + mały dokładny Schur; kontrola względem pełnego coupled dense
   tylko na najniższym poziomie. Potem coupledE/H≤1%, farfield/energia,
   dielectricFEMtransmission/stabilizacja/scalableBEMassembly i kosztanteny.
4. Nie zamykać M2 ani przechodzić do M3 na podstawie tej referencji.
