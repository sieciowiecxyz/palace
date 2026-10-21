# M7 — protokół antyrezonansu 2,900 GHz

Preregistered 2026-10-22, przed obliczeniem nowej pary. To kontrola błędu
solvera w trudnym punkcie, nie kwalifikacja dopasowania w użytkowym paśmie.
Medium, mesh, materiały, porty, K64/right/Tol1e-6 i native build bez zmian.
Oba porty: cold full FP64/fresh setup kontra direct FP32 storage, FP64
arithmetic, scaled complex FP32 LU, **trzy stałe korekcje FP64**, reuse setup.
Snapshots/energy/defer/release i limity jak w [M7](M7.md).

## Bramki ustalone przed wynikiem

- Identyczny config/build/mesh, poprawna inwentaryzacja pól i brak OOM.
- Oba oryginalne residua `||Ax-b||/||b|| <= 1e-6`; coarse <= 1e-3,
  bez zmiany countu wewnątrz GMRES lub automatycznego fallbacku.
- Max zespolone ΔS <= 1e-3, Δ sumy mocy portów <= 1e-3,
  względna Δ energii <= 1e-3, te same regionalne E/B <= 1%.
- Suma `|S1j|²+|S2j|² <= 1+1e-3` dla każdego pobudzenia w obu runach.
- **VSWR nie jest bramką tego protokołu.** Nie przenosić tego wyjątku do
  pasm użytkowych; zwykła kwalifikacja nadal wymaga ΔVSWR <= 0,01.
  Antyrezonans nie jest elementem zbiorczej tabeli matched-band W.5.

## Impedancja i uwarunkowanie

Dla każdego portu zapisać zespolone Γ=Sii oraz
`Zin=50(1+Γ)/(1-Γ)` [Ω], przy drugim porcie zakończonym 50 Ω.
To **impedancja wejściowa z obciążonym drugim portem**, nie element Zii
macierzy otwartoobwodowych parametrów Z.

Z dokładnej tożsamości:

`|Z(Γ+δ)-Z(Γ)| = 100|δ| / (|1-Γ-δ| |1-Γ|)`.

Przy `d=|1-Γ| > ε=1e-3` granica błędu wynikająca z bramki S to
`100ε/[d(d-ε)]` Ω. Zapisać d i tę granicę dla obu runów. Przy d<=ε nie
deklarować skończonej granicy; przy d<=1e-12 zapisać Zin=null (biegun).
Duża ΔZ w pobliżu bieguna nie zastępuje oceny zespolonego S/pól/raw.
Nie narzucać arbitralnej tolerancji absolutnego Zin po obejrzeniu wyniku.

## Odtworzenie oceny

```sh
python3 tools/qualify_antenna.py REFERENCE CANDIDATE --corrections 3 --protocol antiresonance --output NEW-2900-RECEIPT.json
```

Narzędzie dopuszcza ten protokół wyłącznie dla pojedynczego 2,900 GHz i
rzeczywistych rezystancyjnych portów 50 Ω. Summary matched-band odrzuca jego
receipt; domyślne bramki pasmowe i kwalifikacja wcześniejszych par bez zmian.

## Stan

EXP186–187: referencja i fixed3 kandydat **PASS**. Cały czas869.128→903.918s
(+4.00%), peakcgroup62.655→47.362GB (−24.41%). Oba porty,54/55→55/56iter;
po rzeczywistej kontroli residualu potrzebna kontynuacja/restart drugiego
solve kandydata jest wliczona w czas. Finalne oryginalne residua <=9.651e-7,
115coarseapply, maxcoarseresidual1.086e-4, bez zmiany tolerancji/countu.

14regionalnychwierszy pól PASS, maxE/B4.434e-7/4.488e-7. MaxΔS7.753e-8,
Δpower8.463e-8, relativeenergy1.996e-7, portpowerexcess0.
Zin reference P1=10.8193+j34.5424Ω, P2=7.53824+j7.90602Ω;
maxΔZ3.001e-6Ω. Ten konkretny punkt nie leży blisko bieguna Z
(d=1.430/1.722); nie stwierdzono dokładnego położenia antyrezonansu na
podstawie jednej częstotliwości.

Receipt: `artifacts/m7-2900-fixed3-antiresonance-qualification-20261022.json`.
Po dodaniu kontroli CLI176Python testsPASS. CLI odrzuca próbę ponownego
odczytu receipt anti jako matched-summary, zanim wykona rekwalifikację.
Nie łączyć tego wyniku ze zbiorczym czasem/VSWR W.5.
