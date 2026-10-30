# Bramki kampanii optymalizacji faz — 2026-10-29

Checkboxy są wyłącznie w PLAN.md. PASS oznacza wskazane dowody, nie sam build.
Przejście między etapami zatwierdza koordynator. Brak zysku jest poprawnym wynikiem badania.

## M0 - Zgodna referencja i krótka ścieżka testów

- M0.1: Powiązać Git SHA, diff źródeł, hash binarki/adaptera, obraz, zależności, flagi CUDA/precision/UVM i fixture. Audyt e288fe163 nie dowodzi zgodności z używaną binarką; uzgodnić manifest źródeł przed buildem. Nie nadpisywać frozen bundle.
- M0.2: Przypiąć mesh/config/geometry/material/output hashes, oba porty, liczbę rang/wątków i precyzje. Za referencję wydajności wziąć medium SMA-only 1,92 GHz, bez uznawania go za dobry projekt anteny. Dane i ścieżki w workflow.
- M0.3: Przygotować krótkie testy wybranych funkcji: preprocess na istniejącej siatce bez solve, konstrukcja/operator action bez GMRES, replay I/O na zachowanych danych. Wyników synthetic nie przedstawiać jako przyspieszenia całej anteny. Jeśli harness wymaga kodu, implementację najpierw sprawdzić na tiny.
- M0.4: Ustalić kontrolę wolnej pamięci, zakaz aktywnego LLM, cgroup/no-swap, cleanup, timeouty oraz bazowe testy poprawności. Nie zabijać usług bez aktualnego upoważnienia. Bez płatnego compute w tej kampanii bez nowego zlecenia.

## M1 - Profilowanie i wybór kandydatów

- M1.1: Jeden wspólny patch instrumentacji, zakresy bez podwójnego liczenia: load/transform/partition/refine, FE hierarchy/K/C/M/Curl/CEED, serializacja/transfer/write. Istniejący BlockTimer daje exclusive czasy; phase trace inclusive. Nie dodawać synchronizacji CUDA do standardowego timera.
- M1.2: CPU sampling i timery najpierw w krótkim harness, potem najwyżej jeden potrzebny profil medium. Narzut sprawdzić w sparowanym teście (cel ≤1%); profilowane wykonanie nie jest wynikiem benchmarku. Czasy reconcile do rodzica z wyjaśnioną różnicą, orientacyjnie ≤2%.
- M1.3: Każda ścieżka wskazuje najwyżej jeden pierwszy prototyp na podstawie czasu/bytes/alokacji, oczekiwany maksymalny zysk i test obalający hipotezę. Małe lub nieaktywne koszty oznaczyć DEFERRED. Znane 24,3 s JIT na CMP nie wyjaśnia 400 s budowy operatorów.

## M2 - Niezależne prototypy na trzech branchach

- M2.1: Preprocessing: PRE-02/PRE-03/PRE-04/PRE-05 tylko według profilu (PRE-03 wznowione po pomiarze 19,4 s także dla rank1); zachować topologię, atrybuty, orientację, BC, przypisanie portów i równoważność DOF po permutacji. Reordering on/off liczyć w E2E, nie tylko setup.
- M2.2: Operatory: usunąć potwierdzone powtórne przygotowanie/kopie lub serial bottleneck. Najpierw istniejące API; cache tylko z pełnym kluczem i testem invalidation. Zachować curl/div structure, coarse sparsity, constraints, operator action oraz aktualne precyzje. Nie wprowadzać TF32/nowego solvera w ramach tej kampanii.
- M2.3: I/O: po profilu priorytet IO-06 — binarny/native odczyt lub cache wejścia; udowodnić równoważność krzywizny order2, współrzędnych, topologii, orientacji, atrybutów/BC i portów. Cache invalidation po zmianie mesh, wersji/formatu, transformacji i konfiguracji; mierzyć osobno cold conversion + run oraz warm run. Rewrite CSV sprawdzony w M1 i odłożony jako koszt milisekundowy; jeśli kiedyś wróci, Append/buforowanie musi obsługiwać częściowe wiersze obu portów, restart/adaptive sweep, header, kolejność, precyzję i błąd zapisu. Samo wyłączenie pól/logów lub przeniesienie zapisu poza timer nie jest optymalizacją.
- M2.4: Osobne małe commity i build-dir na ścieżkę, wspólny bezpieczny compiler cache. Nie modyfikować współdzielonych dependency build trees ani zamrożonych artefaktów. Jedna przyczyna zmiany na eksperyment, bez równoczesnego tuningu anteny.

## M3 - Kwalifikacja oddzielnych patchy

- M3.1: Tanie testy strukturalne/readback/operator action PASS; błędy i próby przerwane zapisane. Dla równoważnego FP64 operator action cel relL2 ≤1e-10 na stałym zestawie wektorów, zero/near-zero oceniane również absolutnie. Uzasadnić próg przed testem, nie po niepowodzeniu.
- M3.2: Jeśli mikrotest daje korzyść, A/B na nieprofilowanym medium i identycznych wyjściach; minimum 3 sparowane wykonania tylko dla finalistów. Zbalansowana kolejność AB/BA, takie same warunki cache i brak konkurencyjnego obciążenia. Raport mediany i rozrzutu, nie najlepszej próbki.
- M3.3: Każdy port: raw residual ≤1e-6, max |Δcomplex S| ≤1e-5, |ΔVSWR| ≤0,001, istniejący bilans mocy i FF/flux ≤2%. Kontrolować pola/phase w tej samej bazie/fizycznych punktach (relL2 cel ≤1e-5); dla samego I/O wymagać zgodnego numerycznego readback. Używać również ostrzejszych obowiązujących testów referencji; ich wersję przypiąć w M0.
- M3.4: Mierzyć peak cgroup RAM, VRAM i UVM osobno, zwykłe I/O bytes, czas całkowity i faz. Brak OOM/swap i istotnej regresji w solve. Orientacyjnie ≥5% fazy i ponad rozrzut to kandydat; zysk wyłącznie syntetyczny nie upoważnia do promocji E2E. Koszt wzrostu pamięci >2% wymaga jawnej decyzji, nie automatycznej promocji.

## M4 - Kontrolowana integracja

- M4.1: Po M3 branch opt/stages-integration-20261029 z tej samej uzgodnionej bazy. Koordynator przegląda i cherry-pickuje wyłącznie zakwalifikowane commity, po jednym z regresją. REJECTED/DEFERRED pozostają w ledgerze, kod nie trafia do rekomendowanego buildu.
- M4.2: Rozstrzygnąć nakładanie mesh parser/preprocessing i HostRead/operator-memory z I/O. Sprawdzić combined vs base i vs najlepszy pojedynczy patch; sumowanie oddzielnych oszczędności nie dowodzi ich addytywności.

## M5 - Reprezentatywna walidacja

- M5.1: Zintegrowany build na 5070 Ti: ten sam medium 1,92 GHz oba porty, 3 pary A/B; poprawność M3 i zysk E2E ponad zmienność. Wynik bez speedupu opisać uczciwie, ewentualne korzyści I/O/pamięci nazwać osobno.
- M5.2: Krótki sweep 1,71 / 2,69 / 3,80 GHz oba porty i jedna druga geometria ze zmienionym reflektorem/directorem z własną referencją. To test generalizacji i invalidation, nie nowe strojenie anteny. Sprawdzić zapis/reload, restart i cache miss po zmianie materiału, mesh, BC, order/backend.
- M5.3: CPU/MPI small regressions według zmienionego kodu. Wyniki A100/CMP/multi-GPU pozostają NOT RUN bez rzeczywistej kwalifikacji; lokalne przyspieszenie nie dowodzi zysku na słabszym CPU Vast. Nie kupować GPU do domknięcia tabelki.

## M6 - Zamknięcie i rekomendacja

- M6.1: Ledger każdej hipotezy ma wynik, artefakty i powód ewentualnego ponowienia. Brak nierozstrzygniętego IN_PROGRESS. Podsumowanie czasy/pamięć/accuracy per patch i combined, w tym negatywne wyniki.
- M6.2: Reprodukowane komendy, manifest rekomendowanego buildu, rollback do frozen bundle, zakres kwalifikacji i NOT RUN. Docs-garden, root review, lokalny commit; bez push/PR. Cel zamykany dopiero po rzeczywistym audycie bramek, nie z powodu końca czasu.
