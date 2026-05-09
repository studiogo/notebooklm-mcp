#!/usr/bin/env python3
"""Interactive login do NotebookLM przez Playwright — uniwersalny mac/Windows/Linux.

Otwiera okno Chromium, użytkownik loguje się ręcznie (login + hasło + 2FA),
skrypt eksportuje cookies do `~/.notebooklm/storage_state.json` w formacie Playwright.

Use case:
- Windows (gdzie `import_chrome_cookies.py` nie umie odszyfrować Chrome cookies)
- Linux (brak Keychain / Secret Service)
- macOS jako alternatywa, gdy nie chcesz dawać dostępu do Keychain

Wymaga:
    pip install playwright
    playwright install chromium

Usage:
    python3 scripts/login_interactive.py [--out PATH] [--timeout 300]
"""
import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_OUT = Path.home() / ".notebooklm" / "storage_state.json"
NOTEBOOKLM_URL = "https://notebooklm.google.com/"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(DEFAULT_OUT),
                    help=f"Output path for storage_state.json (default: {DEFAULT_OUT})")
    ap.add_argument("--timeout", type=int, default=300,
                    help="Sekundy na zalogowanie (default: 300 = 5 min)")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("BŁĄD: brak Playwright. Zainstaluj:", file=sys.stderr)
        print("    uv pip install playwright", file=sys.stderr)
        print("    uv run playwright install chromium", file=sys.stderr)
        return 1

    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    print("┌─ NotebookLM interactive login ────────────────────────")
    print("│ 1. Za chwilę otworzy się okno Chromium")
    print("│ 2. Zaloguj się na konto Google z dostępem do NotebookLM")
    print("│    (login + hasło + ewentualnie 2FA)")
    print("│ 3. Skrypt automatycznie wykryje gdy NotebookLM się załaduje")
    print(f"│ 4. Cookies zapisze do: {out}")
    print(f"│ Timeout: {args.timeout}s")
    print("└─────────────────────────────────────────────────────────")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=False)
        except Exception as e:
            print(f"BŁĄD uruchamiania Chromium: {e}", file=sys.stderr)
            print("Zainstaluj: `uv run playwright install chromium`", file=sys.stderr)
            return 1

        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(NOTEBOOKLM_URL, timeout=30000)
        except Exception as e:
            print(f"BŁĄD nawigacji: {e}", file=sys.stderr)
            browser.close()
            return 1

        print("\nCzekam aż się zalogujesz i NotebookLM się otworzy...")
        try:
            # Czekaj aż URL pokaże notebooklm po zalogowaniu (mogą być redirecty na accounts.google.com)
            page.wait_for_url("**notebooklm.google.com/**", timeout=args.timeout * 1000)
            # Daj czas na pełne załadowanie (cookies refresh, RPC handshake)
            page.wait_for_load_state("networkidle", timeout=30000)
        except PWTimeout:
            print(f"\nTimeout {args.timeout}s — nie zdążyłeś się zalogować.", file=sys.stderr)
            print("Uruchom skrypt ponownie z dłuższym --timeout albo dokończ login szybciej.",
                  file=sys.stderr)
            browser.close()
            return 1

        print("Wykryto zalogowaną sesję NotebookLM. Zapisuję cookies...")

        storage = context.storage_state()
        cookies_count = len(storage.get("cookies", []))
        google_cookies = [c for c in storage["cookies"] if "google.com" in c.get("domain", "")]

        out.write_text(json.dumps(storage, indent=2))
        out.chmod(0o600)

        # Sprawdź auth cookies
        auth_names = {"SID", "HSID", "SSID", "APISID", "SAPISID", "__Secure-1PSID"}
        present_auth = sorted({c["name"] for c in google_cookies if c["name"] in auth_names})

        print(f"\n✅ Zapisane: {out}")
        print(f"   Cookies total: {cookies_count}")
        print(f"   google.com cookies: {len(google_cookies)}")
        print(f"   Auth cookies: {present_auth}")

        if "SID" not in present_auth:
            print("\n⚠️  OSTRZEŻENIE: brak SID cookie. Sprawdź czy login przeszedł poprawnie.",
                  file=sys.stderr)
            browser.close()
            return 1

        browser.close()
        print("\nGotowe. Uruchom: `uv run notebooklm list` żeby przetestować.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
