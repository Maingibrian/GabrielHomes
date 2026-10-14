"""capture_auth_shots.py — read-only screenshots of the pages touched by the
agents-only-accounts change (login, signup-closed, home header).
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = Path("/home/z/my-project/scripts/shots/auth-review")
OUT.mkdir(parents=True, exist_ok=True)

SHOTS = [
    ("home-desktop", "/", 1440, 900, False),
    ("home-mobile", "/", 390, 844, False),
    ("login-desktop", "/account/login/", 1440, 900, False),
    ("login-mobile", "/account/login/", 390, 844, False),
    ("signup-closed", "/account/signup/", 1440, 900, False),
]

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for name, path, width, height, _full in SHOTS:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(BASE + path, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / f"{name}.png"), full_page=_full)
        print(f"  shot: {name}.png ({width}x{height})")
        page.close()
    browser.close()
print("CAPTURE OK ->", OUT)
