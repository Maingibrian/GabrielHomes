#!/usr/bin/env python3
"""Final full-page shots of the redesigned home at 390 / 849 / 1200."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011/"
OUT = Path("/home/z/my-project/scripts/shots/after-2026-10-12")
OUT.mkdir(parents=True, exist_ok=True)

WIDTHS = [(390, 844), (849, 1100), (1200, 900)]


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for w, h in WIDTHS:
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(BASE, wait_until="networkidle")
            page.wait_for_timeout(2500)  # let reveals/arm animations settle
            page.evaluate(
                """() => new Promise(res => {
                    let y = 0;
                    const step = () => {
                        y += 600; window.scrollTo(0, y);
                        if (y < document.body.scrollHeight) setTimeout(step, 120);
                        else { window.scrollTo(0, 0); setTimeout(res, 400); }
                    };
                    step();
                })"""
            )
            path = OUT / f"home-after-{w}.png"
            page.screenshot(path=str(path), full_page=True)
            sw = page.evaluate("document.documentElement.scrollWidth")
            print(f"{path.name}: scrollW={sw} (viewport {w}) {'OK' if sw == w else 'OVERFLOW!'}")
            page.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
