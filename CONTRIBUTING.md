# Jak pomóc w tym projekcie

To jest most między Google NotebookLM a klientami MCP (Claude Code, Claude Desktop, Cursor, Cline, Continue). NotebookLM nie ma publicznego API — projekt stoi na odtworzonym protokole i na sesji z Twojej przeglądarki. Dlatego psuje się głównie od strony Google, nie od strony kodu.

Najcenniejsze zgłoszenie to takie, które mówi, co dokładnie przestało działać i na czym.

## Zanim zgłosisz błąd

1. Odśwież sesję: `uv run python scripts/import_chrome_cookies.py`, potem ponownie podłącz serwer w kliencie.
2. Sprawdź, czy `uv run notebooklm list` w ogóle wypisuje Twoje notatniki. Jeśli nie — to sprawa uwierzytelnienia, nie narzędzia.
3. Zaktualizuj pakiet pod spodem: `uv lock --upgrade-package notebooklm-py && uv sync`. Duża część usterek to zmiana API po stronie `notebooklm-py`.
4. Sprawdź, czy notatnik ma źródła. Pusty notatnik nic nie wygeneruje.

Jeśli po tych czterech krokach dalej nie działa — zgłaszaj.

## Co ma być w zgłoszeniu

- System operacyjny i sposób logowania: ciasteczka z Chrome czy `login_interactive.py`.
- Klient MCP i jego wersja.
- Wersja Pythona (`python --version`) oraz wersja `notebooklm-py` (`uv pip show notebooklm-py`).
- Nazwa narzędzia MCP, które zawiodło, i podane parametry.
- Pełny komunikat błędu z dziennika serwera.
- Czy konto NotebookLM jest bezpłatne czy Plus — limity się różnią.

**Nigdy nie wklejaj ciasteczek, zawartości `.env`, tokenów ani zrzutów ekranu z zalogowanym kontem.** Wartości wrażliwe zamień na `<usunieto>`.

## Co jest mile widziane

- Poprawki zgodności z nowym API `notebooklm-py`.
- Działające logowanie na Windowsie i Linuksie — tam jest najsłabiej przetestowane.
- Nowe narzędzia MCP odpowiadające funkcjom, które NotebookLM już ma.
- Poprawki w instrukcji instalacji, jeśli u Ciebie przebiegła inaczej niż opisana.

## Czego nie przyjmę

- Obchodzenia limitów Google, wielokrotnych kont, automatycznego zakładania kont.
- Zależności od płatnych usług zewnętrznych.
- Przepisania projektu na inny język albo inny szkielet.
- Zmian samego stylu kodu bez zmiany zachowania.
- Funkcji, których NotebookLM nie udostępnia — tu nic nie da się dopisać po stronie mostu.

## Zmiany w kodzie

1. Odgałęzienie i własna gałąź.
2. Jedna zmiana na jedno zgłoszenie scalenia. Duża przebudowa — najpierw zgłoszenie z opisem zamiaru.
3. Sprawdź na żywym koncie: `uv run notebooklm list` plus co najmniej jedno narzędzie, którego dotyczy zmiana.
4. W opisie napisz, na jakim systemie i na jakiej wersji `notebooklm-py` sprawdzałeś.
5. Nowe narzędzie MCP dopisz do tabeli w README i do CHANGELOG.md.

## Zasady rozmowy

Obowiązuje [Kodeks postępowania](CODE_OF_CONDUCT.md).

## Licencja

Wysyłając zmianę, zgadzasz się na udostępnienie jej na licencji [MIT](LICENSE).
