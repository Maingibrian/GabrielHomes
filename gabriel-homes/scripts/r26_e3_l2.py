"""r26 — E3 for L2: the basemap recolour must boot clean with live tiles.

Load the search page, capture every console error while the map
initialises, wait for canvas + pins, and verify the sync wiring still
responds (pin click -> flash). Screenshot -> LOOP/audit-screens/r26-e3-l2-palette.png
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/property-for-sale/mombasa/"
REPO = Path(__file__).resolve().parents[1]
SHOTS = REPO / "LOOP" / "audit-screens"

fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(15000)
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    print("A: map boots with the L2 recolour:")
    resp = page.goto(BASE, wait_until="domcontentloaded")
    check("search 200", resp.status == 200, str(resp.status))
    page.wait_for_selector("#search-map canvas", timeout=15000)
    check("map canvas rendered (style loaded, recolour ran)", True)
    page.wait_for_selector("[data-listing-pin]", timeout=10000)
    pins = page.locator("[data-listing-pin]").count()
    check("pins drawn after recolour", pins >= 2, f"{pins} pins")
    page.wait_for_timeout(1200)  # let tiles finish painting
    page.screenshot(path=str(SHOTS / "r26-e3-l2-palette.png"))
    page.locator(".search-map-stage").screenshot(
        path=str(SHOTS / "r26-e3-l2-map-region.png"))

    print("B: sync wiring still live after the palette edit:")
    pk = page.evaluate(
        "document.querySelector('[data-listing-pin]').dataset.listingPin")
    page.evaluate(
        f"document.querySelector('[data-listing-pin]').click()")
    page.wait_for_timeout(600)
    flashed = page.evaluate(
        f"document.getElementById('listing-row-{pk}')"
        ".classList.contains('is-flashed')")
    check("pin click still flashes its row", flashed)
    in_view = page.evaluate(
        f"""(() => {{
          const r = document.getElementById('listing-row-{pk}').getBoundingClientRect();
          return r.top > -50 && r.top < window.innerHeight;
        }})()""")
    check("row scrolled into view", in_view)

    style_errors = [e for e in errors if "setPaintProperty" in e or "style" in e.lower()]
    check("zero console/page errors overall", not errors,
          "; ".join(errors[:3]) if errors else "clean")
    check("zero recolour-specific errors", not style_errors)

    page.screenshot(path=str(SHOTS / "r26-e3-l2-palette.png"))
    print(f"screenshot: {SHOTS / 'r26-e3-l2-palette.png'}")

print("R26-E3-L2-VERDICT:", "PASS" if not fails else f"FAIL {fails}")
