#!/usr/bin/env python3
"""Hover screenshots of the spotlight bento grid (home page).

Run with the SYSTEM python3 (it has Playwright; the project .venv does not).
Produces before/after-hover shots so the cursor-tracked glow is visible.
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/home/z/my-project/scripts/shots/bento-spotlight")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:3011"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE + "/", wait_until="networkidle")

        grid = page.locator(".bento-grid").first
        grid.scroll_into_view_if_needed()
        page.wait_for_timeout(900)  # let reveal animations settle

        cards = page.locator(".bento-grid .bento-card")
        first = cards.nth(0)
        box = first.bounding_box()

        # Before hover — baseline
        page.screenshot(path=str(OUT / "bento-before-hover.png"))

        # Hover the big spotlight card, off-centre so the glow placement
        # is obvious in the capture.
        first.hover(position={"x": int(box["width"] * 0.72),
                              "y": int(box["height"] * 0.30)})
        page.wait_for_timeout(700)  # 0.4s fade + settle
        # Programmatic proof: both spotlight layers must be active now.
        proof = page.evaluate(
            """() => {
              const c = document.querySelector('.bento-grid .bento-card');
              const gs = (sel) => getComputedStyle(c, sel).opacity;
              return { before: gs('::before'), after: gs('::after'),
                       mx: c.style.getPropertyValue('--mx'),
                       my: c.style.getPropertyValue('--my') };
            }"""
        )
        print("spotlight proof:", proof)
        page.screenshot(path=str(OUT / "bento-hover-card1.png"))

        # Move to the next card — the glow must FOLLOW the cursor.
        second = cards.nth(1)
        box2 = second.bounding_box()
        second.hover(position={"x": int(box2["width"] * 0.35),
                               "y": int(box2["height"] * 0.65)})
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / "bento-hover-card2.png"))

        browser.close()
    for f in sorted(OUT.glob("*.png")):
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
