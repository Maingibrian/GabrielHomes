"""r23 — E3 audit for L1 map & list sync.

A: default load — row identity, aria-live count, pill hidden, map canvas
   + button pins with data-listing-pin.
B: pin click → row scrolled into view + .is-flashed; row hover → pin .is-hot.
C: Map pill — hidden while map on screen, revealed after scrolling away,
   click returns to the top and hides it again.
D: JS blocked — pill never appears (no dead control), rows visible.
Screenshots -> LOOP/audit-screens/r23-e3-l1-*.png
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

    # --- A: default load ----------------------------------------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(12000)
    print("A: default load:")
    resp = page.goto(BASE, wait_until="domcontentloaded")
    check("search 200", resp.status == 200, str(resp.status))
    page.wait_for_selector("#results-grid .listing-row", timeout=10000)
    rows = page.evaluate(
        "[...document.querySelectorAll('#results-grid .listing-row')]"
        ".map(r => ({id: r.id, pk: r.dataset.listingPk}))"
        ".filter(r => r.id === 'listing-row-' + r.pk).length")
    total = page.evaluate(
        "document.querySelectorAll('#results-grid .listing-row').length")
    check("rows carry identity", rows == total and total >= 2,
          f"{rows}/{total}")
    live = page.evaluate(
        "(() => { const c = document.getElementById('results-count'); "
        "return c ? c.getAttribute('aria-live') : null })()")
    check("count is aria-live=polite", live == "polite", f"aria-live={live}")
    pill_hidden = page.evaluate(
        "document.querySelector('[data-map-return]').hidden")
    check("pill hidden while map on screen", pill_hidden is True,
          f"hidden={pill_hidden}")
    canvas = page.wait_for_selector(".maplibregl-canvas", timeout=15000)
    check("map canvas rendered", bool(canvas))
    pins = page.wait_for_selector("[data-listing-pin]", timeout=15000)
    n_pins = page.evaluate(
        "document.querySelectorAll('[data-listing-pin]').length")
    check("pins carry data-listing-pin", bool(pins) and n_pins > 0,
          f"{n_pins} pins")
    page.screenshot(path=str(SHOTS / "r23-e3-l1-map.png"))

    # --- B: two-way highlight ------------------------------------------------
    print("B: two-way highlight:")
    pin_id = page.evaluate(
        "document.querySelector('[data-listing-pin]').dataset.listingPin")
    page.evaluate(
        "document.querySelector('[data-listing-pin]').click()")
    page.wait_for_timeout(900)
    row_state = page.evaluate(
        "(() => { const r = document.getElementById('listing-row-' + " +
        pin_id + "); if (!r) return null; const b = r.getBoundingClientRect(); "
        "return {flashed: r.classList.contains('is-flashed'), "
        "top: b.top, vh: innerHeight, "
        "focused: document.activeElement && "
        "document.activeElement.closest('.listing-row') === r} })()")
    check("pin click scrolls row into view",
          bool(row_state) and -50 < row_state["top"] < row_state["vh"],
          str(row_state))
    check("row carries is-flashed",
          bool(row_state) and row_state["flashed"])
    popup_focus = page.evaluate(
        "(() => { const el = document.activeElement; return !!(el && "
        "(el.closest('.maplibregl-popup') || el.closest('#search-map'))) })()")
    check("popup/map owns focus after pin click (keyboard path)",
          bool(popup_focus))
    page.screenshot(path=str(SHOTS / "r23-e3-l1-flash.png"))
    # hover the flashed row -> its pin goes hot
    hot = page.evaluate(
        "(() => { const r = document.getElementById('listing-row-' + " +
        pin_id + "); "
        "r.dispatchEvent(new MouseEvent('mouseover', {bubbles: true})); "
        "const pin = document.querySelector('[data-listing-pin=\"' + " +
        pin_id + " + '\"]'); "
        "return pin && pin.classList.contains('is-hot') })()")
    check("row hover highlights pin (is-hot)", bool(hot))
    page.evaluate(
        "document.getElementById('results-grid')"
        ".dispatchEvent(new MouseEvent('mouseleave', {bubbles: true}))")
    hot_cleared = page.evaluate(
        "(() => { const pin = document.querySelector("
        "'[data-listing-pin=\"' + " + pin_id + " + '\"]'); "
        "return pin && !pin.classList.contains('is-hot') })()")
    check("mouseleave clears the highlight", bool(hot_cleared))

    # --- C: the Map pill ------------------------------------------------------
    print("C: Map pill:")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(700)
    shown = page.evaluate("document.querySelector('[data-map-return]').hidden")
    check("pill revealed after scrolling away", shown is False,
          f"hidden={shown}")
    page.click("[data-map-return]")
    # the map shell sits below the site header + breadcrumbs, so "returned"
    # means the map is back inside the viewport — not scrollY == 0.
    page.wait_for_function(
        "() => { const b = document.getElementById('search-map')"
        ".getBoundingClientRect(); return b.top > -80 && b.top < innerHeight * 0.4; }",
        timeout=4500)
    back = page.evaluate(
        "(() => ({y: window.scrollY, hidden: "
        "document.querySelector('[data-map-return]').hidden, "
        "mapTop: document.getElementById('search-map')"
        ".getBoundingClientRect().top}))()")
    check("pill click returns to the map", back["mapTop"] < 400, str(back))
    check("pill hides after returning", back["hidden"] is True)
    ctx.close()

    # --- D: JS blocked ---------------------------------------------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              java_script_enabled=False)
    page = ctx.new_page()
    page.set_default_timeout(12000)
    print("D: JS blocked:")
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_selector("#results-grid .listing-row", timeout=10000)
    page.mouse.wheel(0, 4000)
    page.wait_for_timeout(800)
    pill_state = page.get_attribute("[data-map-return]", "hidden")
    check("pill stays hidden without JS", pill_state is not None,
          f"hidden-attr={pill_state!r} (present = hidden)")
    n_rows = page.locator("#results-grid .listing-row").count()
    visible = all(
        page.locator("#results-grid .listing-row").nth(i).is_visible()
        for i in range(n_rows)) and n_rows > 0
    check("rows fully visible (Q3)", visible, f"{n_rows} rows")
    ctx.close()
    browser.close()

print(f"\n{'L1-E3-VERDICT: FAIL — ' + ', '.join(fails) if fails else 'L1-E3-VERDICT: PASS'}")
raise SystemExit(1 if fails else 0)
