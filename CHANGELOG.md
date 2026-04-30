# CHANGELOG

## v1.0.0 — 2026-04-30

Pierwszy release forka. Zmiany względem [alfredang/notebooklm-mcp](https://github.com/alfredang/notebooklm-mcp) (upstream).

### Nowe funkcjonalności

#### Cookies-from-Chrome bypass (eliminacja Playwright login)
- Skrypt `scripts/import_chrome_cookies.py` czyta cookies sesji Google z **lokalnego Chrome** (wszystkie profile: `Default`, `Profile 1-7`)
- Decryption AES-256-GCM przez macOS Keychain (entry `Chrome Safe Storage`)
- Automatyczny wybór profilu z największą liczbą cookies `*.google.com`
- Zapis w formacie Playwright `storage_state.json` zgodnym z `notebooklm-py`
- **Efekt:** zero ręcznego loginu, wykorzystanie istniejącej sesji w Twoim Chrome

#### Lazy MCP server + auto-refresh + per-call retry
- `lifespan` **nie crashuje** przy auth fail — klient budowany leniwie przy pierwszym wywołaniu narzędzia
- `get_client()` przy auth error wywołuje `import_chrome_cookies.py` i retry
- `call_with_retry()` opakowuje wszystkie tooly: błąd zawierający `auth/expired/401/403/redirect/signin/login` → drop client → refresh cookies → retry raz
- **Efekt:** serwer sam radzi sobie z rotacją cookies przez Google, bez restartu CC

#### 12 dodatkowych narzędzi MCP (vs 15 w upstream → 27 total)
**Źródła:**
- `add_source_file` — lokalny plik (PDF, DOCX, TXT, MD, RTF) z auto-detekcją MIME
- `add_source_drive` — Google Drive (Docs/Sheets/Slides/PDF) po `file_id`

**Pobieranie artefaktów (lokalnie, do dalszej obróbki):**
- `download_infographic` (PNG)
- `download_audio` (MP3 — Audio Overview / podcast)
- `download_video` (MP4 — Video Overview)
- `download_slide_deck` (PPTX)
- `download_mind_map` (JSON)
- `download_quiz`
- `download_flashcards`
- `download_report` (briefing)
- `download_data_table`

**Utility:**
- `wait_for_completion(task_id, timeout)` — blokuje do zakończenia generowania artefaktu (default 300s)

### Bug fixes

1. **`Notebook.source_count` → `sources_count`** — typo w upstream, pakiet `notebooklm-py>=0.3.x` ma `sources_count` (z "s")
2. **`AskResult.text/sources` → `answer/references`** — pakiet zwraca `dataclass(answer, conversation_id, turn_number, is_follow_up, references, raw_response)`
3. **`generate_infographic` brakujące wymagane parametry** — pakiet w sygnaturze ma `orientation` i `detail_level` jako Optional, ale Google odrzuca wywołanie bez nich. Dodane defaulty: `orientation="LANDSCAPE"`, `detail_level="STANDARD"`, `language="pl"`
4. **`generate_*` zwracało fałszywe "Task started" przy pustym `task_id`** — `generate_infographic` waliduje teraz, zwraca `{status: "failed", error: ...}`

### Zależności

- `notebooklm-py>=0.3.4` (było `>=0.3.1` — RPC IDs naprawione w 0.3.4)
- `browser-cookie3>=0.20.1` (nowe — do `scripts/import_chrome_cookies.py`)
- `fastmcp>=2.14.4` (bez zmian)

### Wymagania systemowe (dodane)

- **macOS** — `browser-cookie3` decrypt przez Keychain (Linux/Windows wymagałyby innej implementacji)
- **Chrome** zalogowany do Google z dostępem do NotebookLM
- **uv** (Python package manager)

### Co zostaje do zrobienia (v1.1+)

- Wsparcie Linux/Windows w `import_chrome_cookies.py` (na razie tylko macOS)
- Convenience tool `generate_and_download_audio` (jeden call: generate → wait → download → return path)
- Validation `task_id != ""` we wszystkich `generate_*` (obecnie tylko `generate_infographic`)
- `list_artifacts` i `delete_artifact` jako MCP tooly
