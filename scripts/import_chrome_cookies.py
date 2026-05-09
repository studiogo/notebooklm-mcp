#!/usr/bin/env python3
"""Import Google session cookies from Chrome → ~/.notebooklm/storage_state.json

Skanuje wszystkie profile Chrome, znajduje ten z aktywną sesją NotebookLM,
eksportuje cookies w formacie Playwright storage_state.

Wsparcie OS:
- macOS: pełne (Keychain decrypt cookies automatycznie)
- Windows: częściowe (browser_cookie3 używa DPAPI — działa, ale czasem zawodzi)
- Linux: wymaga GNOME Keyring / KWallet (przez secretstorage)

Jeżeli skrypt nie zadziała na Twoim OS — użyj `login_interactive.py` (Playwright).
"""
import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

import browser_cookie3


def chrome_base_dir():
    """Cross-platform Chrome user data directory."""
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/Google/Chrome"
    elif sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA", str(home / "AppData/Local"))
        return Path(local_appdata) / "Google/Chrome/User Data"
    else:  # linux + other unix
        for candidate in ("google-chrome", "google-chrome-stable", "chromium"):
            p = home / ".config" / candidate
            if p.exists():
                return p
        return home / ".config/google-chrome"


CHROME_BASE = chrome_base_dir()
NEEDED_DOMAINS = {".google.com", "notebooklm.google.com", ".notebooklm.google.com"}
REQUIRED_COOKIE = "SID"
STORAGE_PATH = Path.home() / ".notebooklm" / "storage_state.json"


def list_profiles():
    if not CHROME_BASE.exists():
        print(f"❌ Chrome user data directory not found: {CHROME_BASE}", file=sys.stderr)
        print(f"   OS: {sys.platform}. Sprawdź czy Chrome jest zainstalowany w domyślnej lokalizacji.",
              file=sys.stderr)
        print(f"   Alternatywa: użyj `login_interactive.py` (Playwright login).", file=sys.stderr)
        sys.exit(1)
    return sorted([p.name for p in CHROME_BASE.iterdir()
                   if p.is_dir() and (p.name == "Default" or p.name.startswith("Profile"))])


def cookies_from_profile(profile: str):
    cookie_db = CHROME_BASE / profile / "Cookies"
    if not cookie_db.exists():
        return None
    try:
        cj = browser_cookie3.chrome(cookie_file=str(cookie_db), domain_name="google.com")
        return list(cj)
    except Exception as e:
        print(f"  [{profile}] error: {e}", file=sys.stderr)
        return None


def has_notebooklm_session(cookies):
    if not cookies:
        return False
    has_sid = any(c.name == REQUIRED_COOKIE and c.domain in NEEDED_DOMAINS for c in cookies)
    return has_sid


def cookie_to_playwright(c):
    same_site_map = {None: "None", "": "None", "no_restriction": "None",
                     "lax": "Lax", "strict": "Strict", "unspecified": "None"}
    return {
        "name": c.name,
        "value": c.value,
        "domain": c.domain,
        "path": c.path or "/",
        "expires": float(c.expires) if c.expires else -1,
        "httpOnly": bool(c._rest.get("HttpOnly", False)) if hasattr(c, "_rest") else False,
        "secure": bool(c.secure),
        "sameSite": "None",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="auto",
                    help="Chrome profile name (Default, 'Profile 1', auto). Default: auto")
    ap.add_argument("--out", default=str(STORAGE_PATH), help="Output path")
    args = ap.parse_args()

    profiles = list_profiles()
    print(f"Chrome profiles found: {profiles}")

    candidates = []
    if args.profile == "auto":
        for prof in profiles:
            cookies = cookies_from_profile(prof)
            if has_notebooklm_session(cookies):
                # zlicz "świeżość" — ile cookies dla google.com
                count = sum(1 for c in cookies if c.domain.endswith("google.com"))
                candidates.append((prof, cookies, count))
                print(f"  ✅ {prof}: SID present, {count} google.com cookies")
            else:
                print(f"  ⚪ {prof}: no SID")
        if not candidates:
            print("\n❌ Żaden profil nie ma sesji Google (SID cookie).", file=sys.stderr)
            print("Otwórz Chrome, zaloguj się do https://notebooklm.google.com/, spróbuj ponownie.",
                  file=sys.stderr)
            sys.exit(1)
        # Wybór: profil z największą liczbą cookies google.com (najbardziej aktywny)
        candidates.sort(key=lambda x: -x[2])
        chosen_profile, cookies, _ = candidates[0]
        print(f"\n→ Wybrany profil: {chosen_profile}")
    else:
        cookies = cookies_from_profile(args.profile)
        if not has_notebooklm_session(cookies):
            print(f"❌ Profil {args.profile} nie ma sesji Google.", file=sys.stderr)
            sys.exit(1)
        chosen_profile = args.profile

    # Filtruj — chcemy WSZYSTKIE cookies z domen google.com (auth + service tokens)
    filtered = [c for c in cookies if c.domain.endswith("google.com") or c.domain == "google.com"]
    print(f"Eksportuję {len(filtered)} cookies z domen *.google.com")

    storage = {
        "cookies": [cookie_to_playwright(c) for c in filtered],
        "origins": []
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    out.write_text(json.dumps(storage, indent=2))
    out.chmod(0o600)
    print(f"\n✅ Zapisane: {out}")
    print(f"   Cookies: {len(storage['cookies'])}")
    print(f"   Profil: {chosen_profile}")
    sids = [c["name"] for c in storage["cookies"] if c["name"] in ("SID", "HSID", "SSID", "APISID", "SAPISID", "__Secure-1PSID")]
    print(f"   Auth cookies obecne: {sorted(set(sids))}")


if __name__ == "__main__":
    main()
