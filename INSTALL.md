# INSTALL — pełna instalacja per OS i klient MCP

## Wybór ścieżki auth — które rozwiązanie dla Ciebie?

| OS | Rekomendowana metoda | Alternatywa |
|---|---|---|
| **macOS** | `import_chrome_cookies.py` (Keychain — zero loginu) | `login_interactive.py` (Playwright) |
| **Windows** | `login_interactive.py` (Playwright — najpewniejsze) | `import_chrome_cookies.py` (DPAPI — czasem zawodzi) |
| **Linux** | `login_interactive.py` (Playwright) | `import_chrome_cookies.py` (wymaga GNOME Keyring/KWallet) |

---

## A) Pre-requirements wspólne

- **Chrome zalogowany w Google** + dostęp do https://notebooklm.google.com
- **Python ≥ 3.13** (zalecany przez `pyproject.toml`)
- **`uv`** — Python package manager:
  - macOS: `brew install uv` lub `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## B) Instalacja — kroki bazowe

### macOS

```bash
# 1. Sklonuj
git clone https://github.com/studiogo/notebooklm-mcp ~/Documents/Projekty/notebooklm-mcp
cd ~/Documents/Projekty/notebooklm-mcp

# 2. Zainstaluj zależności
uv sync

# 3. Pobierz cookies z Chrome (Keychain prompt → "Always Allow")
uv run python scripts/import_chrome_cookies.py

# 4. Test
uv run notebooklm list
```

### Windows (PowerShell)

```powershell
# 1. Sklonuj (lokalizacja przykładowa — możesz zmienić)
git clone https://github.com/studiogo/notebooklm-mcp $env:USERPROFILE\notebooklm-mcp
cd $env:USERPROFILE\notebooklm-mcp

# 2. Zainstaluj zależności + Playwright extra
uv sync --extra playwright

# 3. Zainstaluj browser dla Playwright (raz)
uv run playwright install chromium

# 4. Otwórz okno Chromium i zaloguj się ręcznie do NotebookLM
uv run python scripts/login_interactive.py

# 5. Test
uv run notebooklm list
```

### Linux

```bash
# 1. Sklonuj
git clone https://github.com/studiogo/notebooklm-mcp ~/notebooklm-mcp
cd ~/notebooklm-mcp

# 2. Zainstaluj zależności + Playwright extra
uv sync --extra playwright

# 3. Zainstaluj browser dla Playwright (raz)
uv run playwright install chromium

# 4. Otwórz okno Chromium i zaloguj się ręcznie
uv run python scripts/login_interactive.py

# 5. Test
uv run notebooklm list
```

**Dla zaawansowanych Linux** — jeśli masz GNOME Keyring/KWallet i Chrome login:
```bash
uv run python scripts/import_chrome_cookies.py
```
Nie wymaga Playwright, ale czasem rzuca `secretstorage` error — wtedy fallback to `login_interactive.py`.

---

## C) Podłączenie do klienta MCP

### macOS / Linux — Claude Code (CLI)

```bash
# macOS
claude mcp add notebooklm -- uv --directory ~/Documents/Projekty/notebooklm-mcp run python server.py

# Linux
claude mcp add notebooklm -- uv --directory ~/notebooklm-mcp run python server.py
```

W aktywnej sesji: `/mcp reconnect notebooklm`. Restart Claude Code nie jest potrzebny.

### Windows — Claude Code (CLI)

```powershell
claude mcp add notebooklm -- uv --directory $env:USERPROFILE\notebooklm-mcp run python server.py
```

### Claude Desktop

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "uv",
      "args": ["--directory", "/PEŁNA/ŚCIEŻKA/DO/notebooklm-mcp", "run", "python", "server.py"]
    }
  }
}
```

Zamień `/PEŁNA/ŚCIEŻKA/DO/notebooklm-mcp` na realną:
- macOS: `/Users/<USER>/Documents/Projekty/notebooklm-mcp`
- Windows: `C:\\Users\\<USER>\\notebooklm-mcp` (uwaga na podwójne backslashe w JSON)
- Linux: `/home/<USER>/notebooklm-mcp`

Restart Claude Desktop.

### Cursor

Cursor → Settings → Features → MCP → "Add Server":

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "uv",
      "args": ["--directory", "/PEŁNA/ŚCIEŻKA/DO/notebooklm-mcp", "run", "python", "server.py"]
    }
  }
}
```

### Cline (VSCode extension)

**macOS:** `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
**Windows:** `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
**Linux:** `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "uv",
      "args": ["--directory", "/PEŁNA/ŚCIEŻKA/DO/notebooklm-mcp", "run", "python", "server.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Restart VSCode.

### Continue (VSCode/JetBrains)

`~/.continue/config.json` (Linux/macOS) lub `%USERPROFILE%\.continue\config.json` (Windows) — sekcja `mcpServers`:

```json
{
  "mcpServers": [
    {
      "name": "notebooklm",
      "command": "uv",
      "args": ["--directory", "/PEŁNA/ŚCIEŻKA/DO/notebooklm-mcp", "run", "python", "server.py"]
    }
  ]
}
```

Restart Continue.

---

## D) Test — pierwsze wywołanie

W kliencie:

```
Wylistuj moje notebooki NotebookLM
```

Klient wywoła `mcp__notebooklm__list_notebooks` i zwróci tabelę. Jeśli widzisz swoje notebooki — działa.

---

## E) Refresh cookies (gdy klient zwraca błąd auth)

### macOS
```bash
cd ~/Documents/Projekty/notebooklm-mcp
uv run python scripts/import_chrome_cookies.py
```

### Windows (PowerShell)
```powershell
cd $env:USERPROFILE\notebooklm-mcp
uv run python scripts/login_interactive.py
```

### Linux
```bash
cd ~/notebooklm-mcp
uv run python scripts/login_interactive.py
```

Następnie:
- **Claude Code:** `/mcp reconnect notebooklm`
- **Inne klienty:** restart aplikacji

Cookies normalnie żyją tygodniami. Auto-refresh w server.py łapie większość przypadków sam.

---

## F) Wsparcie wielu profili Chrome (tylko `import_chrome_cookies.py`)

Skrypt automatycznie skanuje wszystkie profile (`Default`, `Profile 1`, `Profile 2`, ...) i wybiera ten z największą liczbą cookies `*.google.com`. Jeśli chcesz wymusić konkretny profil:

```bash
uv run python scripts/import_chrome_cookies.py --profile "Profile 3"
```

---

## G) Pliki referencyjne

| Plik | Opis |
|---|---|
| `~/.notebooklm/storage_state.json` | Sesja (auto-refreshable, **NIE commituj**) |
| `~/Library/Caches/claude-cli-nodejs/-Users-<USER>/mcp-logs-notebooklm/*.jsonl` | Logi MCP w Claude Code (macOS) |
| `%LOCALAPPDATA%\claude-cli-nodejs\...\mcp-logs-notebooklm\` | Logi MCP (Windows) |
| `server.py` | Definicje 27 narzędzi |
| `scripts/import_chrome_cookies.py` | macOS-first auth (Keychain bypass) |
| `scripts/login_interactive.py` | Cross-platform auth (Playwright headless login) |
