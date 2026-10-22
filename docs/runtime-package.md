# Lokalny pakiet SM120 — M7.3

## Zakres

Pakiet ma działać z osobnego katalogu, bez pierwotnego repo/cache/builda.
Zawiera natywne binaria, źródła do kontroli hash, narzędzia stdlib, zamrożone
wejścia medium i małą aktualną referencję FP64. Zależności są przypięte przez
digest lokalnego obrazu Podman, CUDA12.9.1/cuDSS0.7.1.4/SM120.
Nie kompiluje przy odtwarzaniu i nie pobiera niczego z sieci.

Obraz pozostaje w lokalnym magazynie Podman. Przeniesienie na inny host wymaga
jednorazowego `podman save/load` obrazu i jego bazy; nie wysyłamy3GB z każdym
runem. `package` buduje tylko cienką warstwę binariów na już lokalnej bazie,
bez buildera/cacheflush/rekompilacji. Katalog pakietu ma nową ścieżkę i własne
wejścia; nie jest symlinkiem do repo.

## Tworzenie i użycie

```sh
python3 tools/dev.py package --tag localhost/palace:m7-sm120 --output NEW-BUNDLE --reference artifacts/m7-w2-tiny-reference-20261022
cd NEW-BUNDLE
python3 reproduce.py NEW-OUTPUT --profile memory --seconds 60
python3 reproduce.py NEW-FP64-OUTPUT --profile reference --seconds 60
python3 tools/qualify_antenna.py reference NEW-OUTPUT --corrections 3 --output NEW-QUALIFICATION.json
python3 tools/coax_fields.py NEW-OUTPUT
```

Manifest `bundle-manifest.json` przechowuje hash każdego pliku payload,
source/native/buildSHA, przypięty image/baseID, profile, pochodzenie i limity.
`reproduce.py` weryfikuje payload oraz obraz przed startem. Pliki wynikowe
i rozpakowane wejścia mogą powstać poza inwentarzem; nie zmieniać payload.
Hash nie jest podpisem ani sprzętowym attestation.

`--runtime-image IMAGE` w developerskim runnerze sprawdza rzeczywisty manifest
i sha256 wszystkich trzech binariów wewnątrz obrazu oraz prefix warstw bazy.
Uruchamia obraz po digest bez montowania natywnych plików z hosta. Zwykły run
bez tej flagi zachowuje developerskie montowania dla szybkich iteracji.
Profiler/Q-pool overlays są odrzucane w trybie obrazu.

## Precyzja i kontrola przykładu

- `memory`: operator i oryginalne residuumFP64, baza GMRESstorageFP32/FP64
  arithmetic, scaledcomplexFP32LU/3stałeFP64IR, reuse dwóch portów.
- `reference`: fullFP64basis/coarse, świeże2setup. Bez seedów/PROM/TF32.
- Oba: tinycoax3.55GHz/2porty, medium/RIGHT/K64/Tol1e-6, snapshots,
  analyticTEM/L2, defer/energy/releases, pool256, UVM RAM↔VRAM.
- Limit1..1800s, domyślnie60s;60GiB/no task swap i hostguard. Wejścia/pola/
  logi to zwykły I/O, nie gorący dyskowy workspace.
- Przykład ma być porównany z dołączoną referencją i analitycznym TEM.
  Sam exit0 nie potwierdza jakości. Ten mały run nie zastępuje antenowych
  W.2–W.5 ani audytu nowej geometrii; odpowiednie raporty są wdocs/milestones.

## Prereg wykonania

Po kontrolach jednostkowych: utworzyć pakiet, uruchomić mały profil memory
z niego na załadowanym przypiętym obrazie, sprawdzić prawdziwe K/TEM/native
bez mountów. Następnie profilem reference sprawdzić nową pełnąFP64 referencję.
Uruchomić1s deadline i kontrolowane SIGTERM tylko własnego procesu przykładu;
potwierdzić brak pozostawionego kontenera i brak uznania incomplete zaRF PASS.
Nie uruchamiać pełnej anteny ani nie przebudowywać natywnych zależności.

Stan w chwili prereg: **NOT RUN**. Wyniki i konkretne ścieżki zostaną dopisane
po odtworzeniu. M7.3 oraz M7.4 pozostają otwarte, globalne defaulty bez zmian.

## EXP223–231 — wynik

**M7.3 PASS**, docelowy lokalny katalog:
`artifacts/m7-sm120-bundle-r3-20261022`. Runtime image
`43ac46f6430cf44d7a2da0a618a0f5c67c6965cca2fde510f2a96116333e6d76`.
Native sourceSHAa6ec732f… bez przebudowy, bazowy digest jak powyżej wmanifestach.
Pierwotny payload745plików/206881879B, dodatkowy `VALIDATION.json` zapisuje
dowody zakończonego przykładu; historyczny prereg jest zachowany w tej instrukcji, a aktualny wynik
opisuje także `VALIDATION.md`. Rewizja Git wmanifeście to
HEAD przy pakowaniu; faktyczne również niecommitowane narzędzia wiąże
inwentarz SHA wszystkich plików. Nie utożsamiać starego git_revision buildu
z brakiem późniejszych zmian Python/docs.

Końcowe EXP228/229 z `/tmp`, bez pierwotnego cwd/cache/buildsystemu:

|Profil|Cały przykład [s]|Peak cgroup [MB]|Iteracje P1/P2|max weightedΔE / ΔB|
|---|---:|---:|---:|---:|
|memory|17.412|578.273|39/42|7.027e-7 / 1.105e-8|
|reference|18.414|576.614|39/42|1.196e-13 / 3.222e-13|

To kontrola poprawności pakietu, nie pomiar oszczędności anteny/mediana.
W obu profilach originalraw<=1e-6, próbki TEM RMS<=1%, punkty<=2%,
energia<=1e-3; volumeL2 E/B~0.4953%/0.4558%, q4→q6delta~2.175e-6.
Memory pełneKvs dołączonaFP64 PASS: ΔS6.031e-10/ΔVSWR8.015e-10/
relativeenergy8.081e-9/power7.655e-10. Zwykły developer-run z trzema
hostnative mountami (EXP231) również pełne K PASS,16.861s.
Root sprawdził rzeczywiste argv, native/buildSHA, snapshoty, terminations,
raw, TEM i brak kontenerów; nie polegał na samym exit0 ani raporcie agenta.
Wyniki FP64 nie muszą być bitowo identyczne; boundpól nie został poluzowany.

### Deadline i sprzątanie

Pierwszy EXP227 checker odrzucił255/StateExitCode−1 zamiast oczekiwanego
137/143; zachowany jako FAIL walidatora. Niezależny CPU `sleep30` na tym
samym obrazie i z `--timeout1` dał255/−1/1.95s, bezOOM. Na tym hoście
Podman6.1.4/conmon2.2.1; [kod Conmon](https://github.com/containers/conmon/blob/main/src/conmon.c)
w timeoutbranch pozostawia exit_status−1; [Podman --timeout](https://docs.podman.io/en/stable/markdown/podman-run.1.html)
określa przerwanie przez conmon. Nie potwierdzono identyczności źródeł
upstreammain z zainstalowanym commitem; niezależny lokalny control zapisany.

EXP230: checker dopuszcza−1 tylko z oddzielnym zgodnym control image/version/
sleep30/timeout1/attach255/noOOM/krótki czas oraz rzeczywistym krótkim
czasem targetu/incomplete/cleanup. Nie rozluźnia K ani nie uznaje timeoutu zaRF.
Deadline1s: targetrun2.313s, resultincomplete, attach255/State−1, kontener
usunięty. SIGTERM po żywym coarsemarkerze tylko własnego PID: exit130,
interrupted=true/SIGTERM,8.194s targetrun, kontener usunięty. Oba PASS.
Limity dotyczą uruchomienia kontenera; setup/weryfikacja obrazu/cleanup
dodają czas do pełnego wrappera.

Artefakty: `m7-package-r3-example-qualification-20261022.json`,
`m7-package-r3-tiny-fixed3-qualification-20261022.json`,
`m7-package-lifecycle-r1-20261022/qualification.json`,
`m7-podman-timeout-control-20261022.json`, `m7-package-legacy-qualification-20261022.json`
w `artifacts/`. Wcześniejsze bundle i przerwania zachowano; łącznie~0.904GB
zwykłych artefaktów etapu przed dodaniem końcowych receiptów; brak SSD hot
workspace, czyszczenia cache, kompilacji lub płatnego compute. Energia
niemierzona.191Python/8shell PASS; pełny audyt M7.4 wciąż otwarty.

## M7.4 — ponowienie EXP233–236

Aktualny pakiet po poprawkach runnera i kwalifikatora:
`artifacts/m7-sm120-bundle-r4-20261022`. Natywny solver i obraz pozostają
identyczne jak w M7.3; bez rekompilacji i pobierania zależności.

| Kontrola | Wynik |
| --- | --- |
| Tiny memory / oba porty | PASS, 17,317 s end-to-end |
| Tiny FP64 / oba porty | PASS, 18,377 s end-to-end |
| Analityczny TEM, volume L2 i oryginalne residuum | PASS dla obu profili |
| Limit 1 s / SIGTERM podczas obliczeń | PASS; incomplete, kontenery usunięte |
| SIGTERM przed startem solvera, EXP232 | PASS; kontener usunięty przez runner |

Nowy `command.json` zapisuje tożsamość i inwentarz plików referencji. Kwalifikator
wiąże je z rzeczywistym montowaniem tylko do odczytu i podaną referencją.
Dla starszych uruchomień wymaga nadal dostępnego oryginalnego montowania.
To kontrola pochodzenia danych, nie podpis ani sprzętowe poświadczenie.
Cleanup obejmuje także zapis metadanych i tworzenie kontenera; sukces ma
niezmienioną definicję czasu wykonania. Pole `launch_phase` rozróżnia fazy.

Root sprawdził obie próby niezależnie od raportu babysittingu: zgodność
przypiętego obrazu, brak montowań natywnych plików hosta, referencję bajtową,
residuum <=1e-6, zamrożone K i analityczny TEM. Memory względem dołączonej
referencji: max delta S = 9,819e-10, max delta VSWR = 1,936e-9.
To test odtwarzania małego modelu, bez wniosku o przyspieszeniu całej anteny.

Dowody: `artifacts/m7-package-r4-root-qualification-20261022.json`,
`artifacts/m7-package-r4-tiny-fixed3-qualification-20261022.json`,
`artifacts/m7-package-lifecycle-r4-20261022/qualification.json` i
`artifacts/m7-early-create-interrupt-20261022/qualification.json`.
Końcowy audyt wszystkich wymagań M7.4 pozostaje otwarty.


## Finalny pakiet — EXP260–263

Aktualny docelowy katalog to `artifacts/m7-sm120-bundle-final-20261022`.
Native/source/image pozostają identyczne z kwalifikacją M7, bez przebudowy.
Nowe rzeczywiste testy memory18,498s i reference18,408s przechodzą K/TEM/
volumeL2, dokładne wiązanie referencji i image-native bez host overlays;
deadline/SIGTERM oraz brak kontenerów PASS. Root potwierdził to w
`artifacts/m7-package-final-root-qualification-20261022.json`.
198testów Python przechodzi również z tego odrębnego pakietu przy cwd `/tmp`.
Końcowa decyzja i granice: [audyt M7.4](milestones/final-audit.md).
`QUALIFICATION.json` określa zakres po zakończeniu audytu; oryginalne
`build-manifest.json numerically_validated=false` pozostaje niezmienione.


Aktualny stan po przeglądzie: **M7.4 CLOSED**. Historyczne wpisy OPEN/NOT RUN
powyżej zachowują stan w chwili prereg, nie opisują obecnego finalnego pakietu.
