---
name: docs-garden
description: Przegląd zgodności dokumentacji z kodem i porządkowanie docs po zmianach, przed commitem.
---

# Docs garden

1. Sprawdź diff, ARCHITECTURE.md, INDEX i dokumenty związane ze zmienionym kodem. Przy pełnym przeglądzie sprawdź całe docs/.
2. Potwierdź fakty w kodzie, konfiguracji i testach. Napraw nieaktualne opisy i linki; usuń duplikaty i zbędne notatki.
3. Nie zmieniaj wymagań, by ukryć błędy kodu. Nie usuwaj nierozwiązanych ograniczeń i blokerów. Nie zmieniaj kodu produktu.
4. Zaktualizuj INDEX i checkpoint, jeśli trzeba. Uruchom `sh .agents/skills/docs-garden/scripts/check.sh`.
5. Zgłoś poprawione pliki, usunięcia, niezweryfikowane fakty i wynik kontroli.
