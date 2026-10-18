# Praca podczas długich sesji

## Wznowienie
Przeczytaj reguły główne i lokalne, INDEX, PLAN, cel i wyłączenia projektu, kryteria aktywnego etapu i checkpoint. Sprawdź Git status, diff oraz ostatnie commity. Porównaj dowody z aktualną rewizją: wynik PASS sprzed zmiany nie dowodzi poprawności nowego kodu. Przed zmianą kodu ustal odpowiednie testy bazowe; przy samych dokumentach wykonaj kontrolę dokumentacji, bez symulacji. Po kompakcji lub nowej sesji ponownie odczytaj stan z dysku. Nie zakładaj, że klient sam przeładował instrukcje.

## Wykonanie
Wybieraj małe, sprawdzalne fragmenty aktywnego milestone. Implementuj, testuj, przeglądaj i aktualizuj checkpoint oraz plan. Zapisuj stan po istotnym postępie lub nieudanym podejściu, przed ryzykownymi krokami i przekazaniem pracy. Nie czekaj na przepełnienie kontekstu. Zapisuj dokładne ścieżki i następne czynności, nie dzienniki rozumowania.

Wykonuj bezpieczne zadania w uzgodnionym zakresie bez potwierdzania każdego kroku. Jeżeli kolejne próby nie przynoszą nowych dowodów (orientacyjnie trzy), zmień podejście lub zapisz bloker. Nie omijaj zablokowanego etapu przez rozpoczęcie przyszłych funkcji. Zgłaszaj decyzje wymagające użytkownika.

## Zakończenie
Sprawdź każde ID kryterium na zintegrowanym kodzie. Uruchom regresje i rzeczywiste smoke/E2E; następnie jako agent główny zleć Lunie High wykonanie skilla `docs-garden`, sprawdź jej wynik i przejrzyj diff przed commitem. Raport subagenta nie zastępuje walidacji. Przy ryzykownej zmianie użyj niezależnego przeglądu lub wykonaj osobny przegląd samodzielnie. Nie osłabiaj testów i wymagań dla uzyskania PASS. Zamknij etap, zaktualizuj PROGRESS.md, następnie aktywuj kolejny etap w jednej spójnej zmianie.

Commituj i pushuj zweryfikowane fragmenty. Sprawdzaj prawdziwe wyniki Git i CI. Niedokończone zmiany zapisuj jawnie jako WIP wyłącznie na gałęzi roboczej; WIP nie zalicza kryteriów.

## Praca równoległa
Tylko koordynator edytuje PLAN, MILESTONES, INDEX i wspólne checkpointy. Wykonawcom przydzielaj cel, pliki lub worktree, zależności, kryteria i testy. Równoleglij niezależne zadania w aktywnym etapie, nie kroki zależne od siebie. Wspólne manifesty i lockfile przydziel jednej osobie. Zbierz wyniki wykonawców przed integracją, przetestuj całość ponownie i anuluj zbędne zadania. Domyślnie unikaj rekurencyjnego tworzenia subagentów i wspólnej edycji plików. Bez subagentów realizuj zadania kolejno.

Stosuj zasady ograniczania kontekstu z context.md. Same pliki nie uruchamiają automatycznie sesji, nie przyznają uprawnień ani nie zastępują systemu zatwierdzeń.

## Workflow badań wydajności

PLAN.md jest checklistą i wskazuje aktywny etap; MILESTONES.md definiuje bramki; PROGRESS.md jest aktywnym checkpointem oraz rejestrem eksperymentów. Aktualizuj istniejący checkpoint po istotnym wyniku zamiast tworzyć nowy plik dla każdej sesji. docs/speedup.md zachowuje uzasadnienie i źródła; bieżących checkboxów nie dubluj w nim. Na razie Mode: normal, Active: none; przygotowanie dokumentów nie uruchamia obliczeń.

Po rozpoczęciu pracy w goal ustaw Mode: goal i Active na pierwszy niezamknięty etap. Zachowaj krótkie dowody zamknięcia w docs/milestones/Mx.md; checkpoint aktywnego etapu utwórz i zaindeksuj przed jego aktywacją (wymagane przez kontrolę docs-garden). Bieżące wpisy EXP pozostają w PROGRESS, bez duplikowania checklist. Przed runem zapisz hipotezę, referencję, kryteria i limit. Research prowadź w kodzie i pierwotnych źródłach upstream: wersja/commit, URL, data, ograniczenia/licencja i konsekwencja dla projektu. Sprawdź istniejące API przed nową zależnością; brakującej funkcji nie zakładaj na podstawie samego README.

Agent główny przygotowuje case/build i dokładne argv. Do tej samej GPT-6 Luna high przekazuje uruchomienie, oczekiwanie, deadline, cleanup i listę artefaktów. Luna nie wybiera modelu fizycznego ani solvera. Czekaj na raport bez cyklicznego odpytywania; potem sam przeanalizuj wynik i zdecyduj o promocji. Research i edycje dokumentów nie wymagają uruchamiania symulacji.

Po każdej próbie uzupełnij wpis EXP w PROGRESS: także porażki i brak danych. Po przejściu wszystkich ID bramki odhacz etap w PLAN, zapisz dowody oraz najlepszy wariant i dopiero aktywuj kolejny etap. Zablokowany etap pozostaje otwarty. Nie zamykaj celu wyłącznie na podstawie zakończenia listy prób.
