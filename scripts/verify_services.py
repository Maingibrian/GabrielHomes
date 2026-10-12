#!/usr/bin/env python3
"""Services page visual verification: full-page 1200 + 390, nav check."""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = Path("/home/z/my-project/scripts/shots/services-2026-10-12")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    for w, h in [(1200, 900), (390, 844)]:
        page = browser.new_page(viewport={"width": w, "height": h})
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(f"{BASE}/services/", wait_until="networkidle")
        page.wait_for_timeout(1200)
        # scroll through to trigger reveals, back to top
        page.evaluate(
            """() => new Promise(res => {
                let y = 0;
                const step = () => {
                    y += 500; window.scrollTo(0, y);
                    if (y < document.body.scrollHeight) setTimeout(step, 100);
                    else { window.scrollTo(0, 0); setTimeout(res, 350); }
                };
                step();
            })"""
        )
        path = OUT / f"services-{w}.png"
        page.screenshot(path=str(path), full_page=True)
        sw = page.evaluate("document.documentElement.scrollWidth")
        print(f"{w}: scrollW={sw} {'OK' if sw == w else 'OVERFLOW'} | errors={errors[:2] or 'none'}")
        page.close()
    browser.close()
print("shots ->", OUT)
