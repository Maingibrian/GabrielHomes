"""Verify the Framer-reference bento reveal on the home showcase grid.

Captures:
  1. desktop rest state  (expect: desaturated photos, NO text)
  2. desktop hover state (expect: colored photo, scrim + text visible)
  3. mobile 390px        (expect: colored photos, text always visible)
Saves PNGs to scripts/design-audit/bento-reveal-2026-10-16/ and prints
computed-style probes so the check is forensic, not vibes.
Mirrors the proven audit_home_shots.py browser handling.
"""
import json
import pathlib
import time

from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/home/z/my-project/scripts/design-audit/bento-reveal-2026-10-16")
OUT.mkdir(parents=True, exist_ok=True)
HOME = "http://127.0.0.1:3011/"

SCROLL_THROUGH = """
async () => {
    const step = window.innerHeight;
    const h = document.body.scrollHeight;
    for (let y = 0; y <= h; y += step) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 120));
    }
    window.scrollTo(0, 0);
    await new Promise(r => setTimeout(r, 300));
}
"""

SCROLL_TO_GRID = """
() => {
    const g = document.querySelector('.showcase .bento-grid');
    if (!g) return null;
    const y = g.getBoundingClientRect().top + window.scrollY - 90;
    window.scrollTo(0, y);
    return Math.round(y);
}
"""


def probe(page):
    """Computed styles of the first non-CTA bento card's layers."""
    return page.evaluate(
        """() => {
        const card = document.querySelector('.showcase .bento-card:not(.bento-card--cta)');
        if (!card) return null;
        const grab = (sel, prop) => {
          const el = card.querySelector(sel);
          return el ? getComputedStyle(el)[prop] : null;
        };
        return {
          bgFilter: grab('.bento-card__bg', 'filter'),
          bodyOpacity: grab('.bento-card__body', 'opacity'),
          bodyTransform: grab('.bento-card__body', 'transform'),
          scrimOpacity: grab('.bento-card__scrim', 'opacity'),
        };
    }"""
    )


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--disable-dev-shm-usage", "--no-sandbox"])

    # --- desktop -------------------------------------------------------
    ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                              device_scale_factor=1)
    page = ctx.new_page()
    page.on("crash", lambda pg: print("!! PAGE CRASHED (desktop)"))
    page.goto(HOME, wait_until="networkidle")
    page.evaluate(SCROLL_THROUGH)
    time.sleep(0.5)

    page.evaluate(SCROLL_TO_GRID)
    time.sleep(0.9)

    rest = probe(page)
    page.screenshot(path=str(OUT / "desktop-rest.png"))

    card = page.locator(".showcase .bento-card:not(.bento-card--cta)").first
    card.hover()
    page.wait_for_timeout(700)  # let the 0.45s transitions finish
    hovered = probe(page)
    page.screenshot(path=str(OUT / "desktop-hover.png"))
    ctx.close()

    # --- mobile (touch: no hover) --------------------------------------
    mctx = browser.new_context(viewport={"width": 390, "height": 844},
                               device_scale_factor=2, is_mobile=True,
                               has_touch=True)
    mpage = mctx.new_page()
    mpage.on("crash", lambda pg: print("!! PAGE CRASHED (mobile)"))
    mpage.goto(HOME, wait_until="networkidle")
    mpage.evaluate(SCROLL_THROUGH)
    time.sleep(0.5)
    mpage.evaluate(SCROLL_TO_GRID)
    time.sleep(0.9)
    mobile = probe(mpage)
    mpage.screenshot(path=str(OUT / "mobile-rest.png"))
    mctx.close()
    browser.close()

print(json.dumps({
    "desktop_rest": rest,
    "desktop_hover": hovered,
    "mobile": mobile,
}, indent=2))
print(f"screenshots -> {OUT}")
