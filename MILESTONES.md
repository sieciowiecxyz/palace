# Bramki przygotowania lokalnego PR-a

Postęp wyłącznie w [PLAN](PLAN.md). Etapy kolejno; pierwszy PR jest pilotażem.
Bez publikacji na GitHubie. Poniższe kryteria są do wykonania, nie potwierdzają gotowości zmian.

## M0 - Aktualny upstream

- M0.1: pobrano upstream; zapisano domyślną gałąź i SHA, bez resetowania forka badawczego.
- M0.2: sprawdzono, czy kandydat nadal jest potrzebny i nie powiela istniejącej zmiany/PR-a.

## M1 - Jeden niezależny patch

- M1.1: lokalny branch z ustalonego upstream; jedna przyczyna, mały diff i zwykłe mechanizmy Palace, bez zależności od lokalnego adaptera i narzędzi benchmarkowych.
- M1.2: krótki przypadek odtwarza problem; zachowano licencje, styl i dotychczasowe zachowanie poza deklarowaną zmianą.

## M2 - Dowody poprawności i korzyści

- M2.1: adekwatne testy upstream i regresja problemu przechodzą; zakres CPU/CUDA/MPI jawny, niewykonane testy oznaczone NOT RUN.
- M2.2: upstream kontra upstream + ten patch, te same wejścia, ustawienia i warunki. Zapisane polecenia, wyniki oraz ograniczenia; czas i pamięć mierzone oddzielnie. Dawne −23,6% RAM całego profilu nie jest wynikiem tego PR-a.
- M2.3: build przyrostowy z cache; krótki smoke przed droższym pomiarem. Brak zmiany fizyki/medium, progów dokładności i domyślnych precyzji dla uzyskania zysku.

## M3 - Zgodność z praktykami maintainerów

- M3.1: przeczytano aktualne CONTRIBUTING, dokumentację developer/testów i kilka podobnych review; zapisano konkretne źródła oraz wymagania.
- M3.2: lokalny opis po angielsku: problem, rozwiązanie, zakres, testy, wyniki i ograniczenia. Tematy wymagające konsultacji zapisane do decyzji użytkownika; żadnych wysłanych wiadomości.

## M4 - Pakiet do ręcznej publikacji

- M4.1: wskazano branch, bazowe SHA, commity, diff/stat, polecenia testów i plik z opisem PR-a; lokalny przegląd i dokumentacja zakończone.
- M4.2: instrukcja zawiera sprawdzenie zmian, dodanie własnego forka jako origin, push tylko wybranego brancha i utworzenie PR-a do ustalonej gałęzi upstream. Polecenia publikujące pozostają niewykonane.

## Historia

Zakończone badania optymalizacji mają osobne [kryteria](docs/milestones/optimization-contract.md) i [audyt](docs/milestones/final-audit.md). Historyczne M0–M7 nie oznaczają zaliczenia powyższych etapów.
