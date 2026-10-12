#!/usr/bin/env python3
"""Per-section viewport shots at 1200 to inspect the middle of the page."""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011/"
OUT = Path("/home/z/my-project/scripts/shots/after-2026-10-12")
OUT.mkdir(parents=True, exist_ok=True)
SECTIONS = ["showcase", "story", "numbers", "philosophy", "browse", "cta"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(1500)
    for sid in SECTIONS:
        el = page.locator(f"#{sid}")
        el.scroll_into_view_if_needed()
        page.wait_for_timeout(900)  # allow reveal transition to finish
        path = OUT / f"section-{sid}.png"
        page.screenshot(path=str(path))
        # opacity probe of first few children
        ops = page.evaluate(
            """(sid) => {
                const el = document.getElementById(sid);
                return [...el.querySelectorAll('h2,h3,p,a,li')].slice(0, 8)
                    .map(e => ({tag: e.tagName, cls: e.className.slice(0,30),
                                op: getComputedStyle(e).opacity}));
            }""",
            sid,
        )
        hidden = [o for o in ops if float(o["op"]) < 0.05]
        print(f"{sid}: {len(ops)} probes, hidden={len(hidden)}")
        if hidden:
            print("   ", hidden[:3])
    browser.close()
print("done ->", OUT)
