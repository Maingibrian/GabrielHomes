"""Vision-audit screenshots for Gabriel Homes (read-only, no code changes).

Captures the home page (desktop full/hero/bento/footer, mobile full/hero/bento/footer)
and the /properties/ listing page (desktop full) for a two-agent design critique.

Run with SYSTEM python3 (has Playwright): python3 scripts/audit_home_shots.py
"""
from pathlib import Path
import time

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = Path("/home/z/my-project/scripts/design-audit/home-2026-10-15")
OUT.mkdir(parents=True, exist_ok=True)

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


def scroll_through(page):
    """Trigger lazy-loaded media by walking to the bottom, then return to top."""
    page.evaluate(SCROLL_THROUGH)
    time.sleep(0.5)


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- Desktop 1440x900 ----------
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900}, device_scale_factor=1
    )
    page = ctx.new_page()
    page.goto(BASE + "/", wait_until="networkidle")
    scroll_through(page)

    page.screenshot(path=str(OUT / "home-desktop-full.png"), full_page=True)

    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.3)
    page.screenshot(path=str(OUT / "home-desktop-hero.png"))

    grid = page.locator(".bento-grid").first
    if grid.count() > 0:
        grid.scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -110)")
        time.sleep(0.3)
        page.screenshot(path=str(OUT / "home-desktop-bento.png"))

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(0.3)
    page.screenshot(path=str(OUT / "home-desktop-footer.png"))

    # /properties/ all-listings page (desktop)
    page.goto(BASE + "/properties/", wait_until="networkidle")
    scroll_through(page)
    page.screenshot(path=str(OUT / "properties-desktop-full.png"), full_page=True)
    ctx.close()

    # ---------- Mobile 390x844 @2x ----------
    mctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
    )
    mpage = mctx.new_page()
    mpage.goto(BASE + "/", wait_until="networkidle")
    scroll_through(mpage)

    mpage.screenshot(path=str(OUT / "home-mobile-full.png"), full_page=True)

    mpage.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.3)
    mpage.screenshot(path=str(OUT / "home-mobile-hero.png"))

    mgrid = mpage.locator(".bento-grid").first
    if mgrid.count() > 0:
        mgrid.scroll_into_view_if_needed()
        mpage.evaluate("window.scrollBy(0, -90)")
        time.sleep(0.3)
        mpage.screenshot(path=str(OUT / "home-mobile-bento.png"))

    mpage.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(0.3)
    mpage.screenshot(path=str(OUT / "home-mobile-footer.png"))
    mctx.close()

    browser.close()

print("done")
for f in sorted(OUT.glob("*.png")):
    print(f.name, f.stat().st_size)
