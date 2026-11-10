"""Open the user's browser once the local site is actually reachable.

Used by the one-click launchers (START-GABRIEL-HOMES.bat/.command/.sh).

Why this exists (v2 bug fix):
    The v1 launchers opened the browser BEFORE `manage.py runserver` had
    bound its port, so users saw the browser open straight into
    "This site can't be reached" (or, on some systems, nothing at all).
    This helper flips the order: it POLLS the site until it answers,
    and only then opens the default browser. If no browser can be
    opened it says so loudly and prints the URL to open by hand.

Usage (run with the project's venv python, backgrounded by the launcher):
    python scripts/open_browser_when_ready.py <port> [path]

Environment:
    GABRIEL_NO_BROWSER=1   exit immediately without opening anything
                           (used by headless/test runs)

Output is deliberately plain ASCII so it renders on every Windows
console codepage (cp850/cp1252/...).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

POLL_INTERVAL = 0.5
TIMEOUT_SECONDS = 45.0


def _is_wsl() -> bool:
    try:
        with open("/proc/version", "r", encoding="utf-8", errors="ignore") as fh:
            return "microsoft" in fh.read().lower()
    except OSError:
        return False


def _try_open(url: str) -> bool:
    """Try every sensible way of opening the URL. Returns True on success."""
    # 1. The stdlib way — honours $BROWSER and the OS default-browser
    #    association. On Windows this uses os.startfile internally.
    try:
        if webbrowser.open(url, new=2, autoraise=True):
            return True
    except Exception:
        pass

    # 2. Explicit platform fallbacks.
    candidates: list[list[str]] = []
    if sys.platform.startswith("win"):
        candidates.append(["cmd", "/c", "start", "", url])
    elif sys.platform == "darwin":
        candidates.append(["open", url])
    else:
        if _is_wsl():
            # WSL: open the browser on the Windows side.
            candidates.append(["wslview", url])
            candidates.append(["cmd.exe", "/c", "start", "", url])
            candidates.append(["explorer.exe", url])
        candidates.append(["xdg-open", url])

    for cmd in candidates:
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                check=False,
            )
            if proc.returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            continue
    return False


def main() -> int:
    if os.environ.get("GABRIEL_NO_BROWSER") == "1":
        return 0

    args = sys.argv[1:]
    if len(args) < 1:
        print("[gabriel] open_browser_when_ready: missing port argument")
        return 0

    port = args[0].strip()
    path = args[1].strip() if len(args) > 1 else "/"
    url = f"http://127.0.0.1:{port}{path}"

    deadline = time.monotonic() + TIMEOUT_SECONDS
    up = False
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if getattr(resp, "status", 200) < 500:
                    up = True
                    break
        except urllib.error.HTTPError:
            # A 4xx/5xx still proves the server is listening; the
            # homepage is expected to be 200, so treat this as up.
            up = True
            break
        except Exception:
            time.sleep(POLL_INTERVAL)

    if not up:
        print("")
        print("==============================================================")
        print("  [gabriel] The site did not respond within "
              f"{int(TIMEOUT_SECONDS)} seconds.")
        print("  [gabriel] It may still be starting - check the console,")
        print("  [gabriel] then open this address in your browser:")
        print(f"  [gabriel]     {url}")
        print("==============================================================")
        return 0

    if _try_open(url):
        print(f"[gabriel] Browser opened: {url}")
    else:
        print("")
        print("==============================================================")
        print("  [gabriel] COULD NOT OPEN A BROWSER AUTOMATICALLY.")
        print("  [gabriel] The site IS running - please open this address")
        print("  [gabriel] in your browser manually:")
        print(f"  [gabriel]     {url}")
        print("==============================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
