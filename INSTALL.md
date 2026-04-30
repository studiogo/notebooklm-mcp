# INSTALL — pełna instalacja per klient MCP

## Pre-requirements

- macOS (na razie tylko)
- Chrome z zalogowaną sesją Google + dostęp do https://notebooklm.google.com
- `uv` — `brew install uv` lub `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Kroki bazowe (raz, niezależne od klienta)

```bash
# 1. Sklonuj
git clone https://github.com/studiogo/notebooklm-mcp ~/Documents/Projekty/notebooklm-mcp
cd ~/Documents/Projekty/notebooklm-mcp

# 2. Zainstaluj zależności
uv sync

# 3. Pobierz cookies z Chrome (Keychain prompt → "Always Allow")
uv run python scripts/import_chrome_cookies.py
```

**Sprawdź:** `uv run notebooklm list` powinno zwrócić Twoje notebooki.

---

## Podłączenie do klienta

### A) Claude Code (CLI)

```bash
claude mcp add notebooklm -- uv --directory ~/Documents/Projekty/notebooklm-mcp run python server.py
```

W aktywnej sesji: `/mcp reconnect notebooklm`. Restart Claude Code nie jest potrzebny.

**Alternatywa (ręczna edycja `~/.claude.json`):**
```json
{
  "mcpServers": {
    "notebooklm": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/Users/<USER>/Documents/Projekty/notebooklm-mcp", "run", "python", "server.py"]
    }
  }
}
```

### B) Claude Desktop

Plik: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "uv",
      "args": ["--directory", "/Users/<USER>/Documents/Projekty/notebooklm-mcp", "run", "python", "server.py"]
    }
  }
}
```

Restart Claude Desktop.

### C) Cursor

Cursor → Settings → Features → MCP → "Add Server":

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "uv",
      "args": ["--directory", "/Users/<USER>/Documents/Projekty/notebooklm-mcp", "run", "python", "server.py"]
    }
  }
}
```

### D) Cline (VSCode extension)

Plik: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "uv",
      "args": ["--directory", "/Users/<USER>/Documents/Projekty/notebooklm-mcp", "run", "python", "server.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Restart VSCode.

### E) Continue (VSCode/JetBrains extension)

Plik: `~/.continue/config.json` — sekcja `mcpServers`:

```json
{
  "mcpServers": [
    {
      "name": "notebooklm",
      "command": "uv",
      "args": ["--directory", "/Users/<USER>/Documents/Projekty/notebooklm-mcp", "run", "python", "server.py"]
    }
  ]
}
```

Restart Continue.

---

## Test — pierwsze wywołanie

W kliencie:

```
Wylistuj moje notebooki NotebookLM
```

Klient wywoła `mcp__notebooklm__list_notebooks` i zwróci tabelę. Jeśli widzisz swoje notebooki — działa.

---

## Refresh cookies

Gdy klient zwraca błąd auth (rotacja Google):

```bash
cd ~/Documents/Projekty/notebooklm-mcp
uv run python scripts/import_chrome_cookies.py
```

Następnie:
- **Claude Code:** `/mcp reconnect notebooklm`
- **Inne klienty:** restart aplikacji

Cookies normalnie żyją tygodniami. Auto-refresh w server.py łapie większość przypadków sam.

---

## Wsparcie wielu profili Chrome

Skrypt automatycznie skanuje wszystkie profile (`Default`, `Profile 1`, `Profile 2`, ...) i wybiera ten z największą liczbą cookies `*.google.com`. Jeśli chcesz wymusić konkretny profil:

```bash
uv run python scripts/import_chrome_cookies.py --profile "Profile 3"
```

---

## Pliki referencyjne

- `~/.notebooklm/storage_state.json` — sesja (auto-refreshable, NIE commituj)
- `~/Library/Caches/claude-cli-nodejs/-Users-<USER>/mcp-logs-notebooklm/*.jsonl` — logi MCP w Claude Code
- `server.py` — definicje 27 narzędzi
- `scripts/import_chrome_cookies.py` — bypass Playwright
