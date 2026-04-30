# NotebookLM MCP — Claude Code, Claude Desktop, Cursor, Cline, Continue

> Sterowanie Google NotebookLM z dowolnego klienta MCP. **Zero ręcznego loginu** — wykorzystuje sesję Twojego Chrome'a.
>
> Fork [alfredang/notebooklm-mcp](https://github.com/alfredang/notebooklm-mcp) z 12 dodatkowymi narzędziami, auto-refresh cookies i naprawami zgodności z `notebooklm-py>=0.3.4`.

## Co potrafi

**27 narzędzi MCP:**

| Kategoria | Narzędzia |
|---|---|
| 📓 Notebooki | `list_notebooks` · `create_notebook` · `get_notebook_summary` |
| 📥 Źródła | `add_source_url` · `add_source_file` (PDF/DOCX/MD/TXT) · `add_source_text` · `add_source_drive` |
| 💬 Q&A | `ask_notebook` (z citations ze źródeł) |
| 🎙️ Generowanie | `generate_audio_overview` (podcast) · `generate_video_overview` · `generate_slide_deck` · `generate_mind_map` · `generate_infographic` · `generate_quiz` · `generate_flashcards` · `generate_summary_report` · `generate_data_table` |
| 💾 Pobieranie | `download_audio/video/slide_deck/mind_map/infographic/quiz/flashcards/report/data_table` |
| ⏳ Utility | `wait_for_completion` |

## Co odróżnia od upstream

- **Cookies-from-Chrome bypass** — pobiera sesję Google z Twojego Chrome'a (skrypt `scripts/import_chrome_cookies.py`). Zero Playwright login, zero osobnego profilu.
- **Lazy server + auto-refresh + per-call retry** — gdy Google zrotuje cookies, MCP sam pobiera świeże i ponawia. Bez restartu Claude Code.
- **+12 narzędzi** vs 15 w upstream (źródła plików/Drive, 9× download, wait utility).
- **3 bug fixy** zgodności z aktualnym `notebooklm-py>=0.3.4` (`sources_count`, `AskResult.answer/references`, wymagane params w `generate_infographic`).

Pełna lista zmian: [CHANGELOG.md](CHANGELOG.md).

---

## Wymagania

| Wymóg | Komentarz |
|---|---|
| **macOS** | Skrypt cookies używa Keychain do decrypt Chrome cookies (Linux/Windows na razie nie) |
| **Chrome zalogowany w Google** | + dostęp do https://notebooklm.google.com (free lub Plus) |
| **uv** | Python package manager — `brew install uv` lub `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Klient MCP** | Claude Code / Claude Desktop / Cursor / Cline / Continue |

---

## Instalacja — 4 komendy

```bash
# 1. Sklonuj
git clone https://github.com/studiogo/notebooklm-mcp ~/Documents/Projekty/notebooklm-mcp
cd ~/Documents/Projekty/notebooklm-mcp

# 2. Zainstaluj zależności
uv sync

# 3. Pobierz cookies sesji z Twojego Chrome (raz, akceptuj Keychain prompt)
uv run python scripts/import_chrome_cookies.py

# 4. Test (lista Twoich notebooków)
uv run notebooklm list
```

Jeśli `notebooklm list` wylistuje Twoje notebooki — auth działa. Pora podpiąć MCP do klienta.

## Podłączenie do klienta MCP

Pełne instrukcje per klient: [INSTALL.md](INSTALL.md).

**Claude Code (skrót):**
```bash
claude mcp add notebooklm -- uv --directory ~/Documents/Projekty/notebooklm-mcp run python server.py
```

**Claude Desktop:** edycja `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "uv",
      "args": ["--directory", "/Users/TWOJ_USER/Documents/Projekty/notebooklm-mcp", "run", "python", "server.py"]
    }
  }
}
```

Po restarcie klienta — narzędzia `mcp__notebooklm__*` są dostępne.

---

## Use case — Audio Overview po polsku

```
Ty: zrób mi notebook "Trendy AI 2026", znajdź 8 źródeł i wrzuć je tam,
    potem zrób z tego podcast po polsku 12-15 min.

Claude:
  1. WebSearch → 15 wyników
  2. filtruje top 8
  3. mcp__notebooklm__create_notebook("Trendy AI 2026")
  4. pętla mcp__notebooklm__add_source_url × 8
  5. mcp__notebooklm__generate_audio_overview(language="pl", instructions="...")
  6. mcp__notebooklm__wait_for_completion (~3 min)
  7. mcp__notebooklm__download_audio("~/Desktop/podcast.mp3")
  → masz gotowy 13-min podcast 2-osobowy AI w pliku MP3
```

Inne praktyczne flow:
- **SmartLetter podcast** — 5 newsów dnia → notebook → Audio Overview → automatyczny podcast bez nagrywania
- **Lekcja kursu** — skrypt + materiały → mind_map + quiz + flashcards → eksport
- **Brand Brain** — komplet researchu marki → ask z citations + briefing
- **Research konkurencji** — 10 stron + 5 YT + 3 PDF → cytowane odpowiedzi z całości

---

## Refresh cookies (gdy MCP zwraca auth error)

Auto-refresh w server.py łapie większość przypadków. Gdy nie pomaga (np. Google wymaga 2FA re-auth):

```bash
cd ~/Documents/Projekty/notebooklm-mcp
uv run python scripts/import_chrome_cookies.py
# w kliencie MCP: /mcp reconnect notebooklm   (Claude Code)
# albo restart klienta (inne)
```

Cookies normalnie żyją tygodniami.

---

## Troubleshooting

**`Authentication expired or invalid`** — odpal `import_chrome_cookies.py`. Jeśli nie pomaga, sprawdź czy Chrome ma aktywną sesję NotebookLM (otwórz https://notebooklm.google.com w przeglądarce).

**`No SID cookie found`** — żaden z profili Chrome nie ma zalogowanej sesji Google. Zaloguj się w Chrome do konta z dostępem do NotebookLM, odpal skrypt ponownie.

**`Generation failed - no artifact_id returned`** — typowo brak wymaganych parametrów (zwłaszcza w `generate_infographic`: `orientation` + `detail_level`). Sprawdź też czy Twój notebook ma źródła (puste notebooki nic nie wygenerują).

**MCP server nie startuje** — `uv sync` w katalogu repo. Sprawdź `python --version` (wymagane >=3.13). Sprawdź `which uv`.

**Wywala `'Notebook' object has no attribute 'X'`** — pakiet `notebooklm-py` zmienił API. Update: `uv lock --upgrade-package notebooklm-py && uv sync`. Jeśli problem zostaje, otwórz issue.

---

## Atrybucja

- **Upstream:** [alfredang/notebooklm-mcp](https://github.com/alfredang/notebooklm-mcp) — bazowa struktura MCP wrappera
- **Pakiet pod spodem:** [teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py) — reverse-engineered klient NotebookLM RPC
- **Cookies bypass:** [borisbabic/browser_cookie3](https://github.com/borisbabic/browser_cookie3)

## Licencja

[MIT](LICENSE) — bezpłatne komercyjne i prywatne użytkowanie.

---

**Autor forka:** [Łukasz Hodorowicz](https://lukaszhodorowicz.pl) — [Ogarniam AI](https://ogarniamai.pl)
