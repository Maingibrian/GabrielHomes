"""r22 — E3 audit for G2 shared-element page transitions.

A: default load (this container grades lite per r17) — @view-transition rule
   parsed inside @supports, root name = root, a card img carries prop-<pk>.
B: reduced-motion emulation — gate sets fx=none: root name = none, card name
   = none (fail-closed override kills the inline name).
C: JS disabled — no data-fx attribute at all: root name = none, card name =
   none, content still visible (Q3/D-MOTION-SAFE).
Screenshots -> LOOP/audit-screens/r22-e3-g2-*.png
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
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

    # --- A: default (lite) -------------------------------------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(10000)
    print("A: default load (expects fx=lite in this container):")
    resp = page.goto(f"{BASE}/property-for-sale/mombasa/",
                     wait_until="domcontentloaded")
    check("search 200", resp.status == 200, str(resp.status))
    page.wait_for_selector(".listing-row img", timeout=8000)
    fx = page.evaluate("document.documentElement.dataset.fx")
    check("gate set data-fx", fx in ("rich", "lite"), f"data-fx={fx}")
    root_name = page.evaluate(
        "getComputedStyle(document.documentElement).viewTransitionName")
    check("root name active under gate", root_name == "root", f"got {root_name!r}")
    vt_rule = page.evaluate(
        "[...document.styleSheets].flatMap(s => { try { return [...s.cssRules] } "
        "catch (e) { return [] } }).filter(r => r.cssText && "
        "r.cssText.replace(/\\s+/g,' ').includes('@view-transition'))"
        ".map(r => r.cssText.replace(/\\s+/g,' '))")
    check("@view-transition parsed in CSSOM", len(vt_rule) >= 1,
          vt_rule[0][:80] if vt_rule else "none found")
    inside_supports = page.evaluate(
        "[...document.styleSheets].flatMap(s => { try { return [...s.cssRules] } "
        "catch (e) { return [] } }).some(r => r.constructor.name === "
        "'CSSSupportsRule' && [...r.cssRules].some(c => "
        "(c.cssText||'').includes('@view-transition')))")
    check("@view-transition nested inside @supports", inside_supports)
    card = page.evaluate(
        "(() => { const i = document.querySelector('.listing-row "
        "img[style*=\"view-transition-name\"]'); return i ? "
        "{name: getComputedStyle(i).viewTransitionName, w: i.width, "
        "h: i.height} : null })()")
    check("card img carries prop-<pk> name",
          bool(card) and str(card["name"]).startswith("prop-"),
          str(card))
    check("card img keeps width/height",
          bool(card) and card["w"] and card["h"], str(card))
    page.screenshot(path=str(SHOTS / "r22-e3-g2-lite.png"))
    ctx.close()

    # --- B: reduced-motion => fx=none --------------------------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(10000)
    print("B: reduced-motion (expects fx=none):")
    page.goto(f"{BASE}/property-for-sale/mombasa/", wait_until="domcontentloaded")
    page.wait_for_selector(".listing-row img", timeout=8000)
    fx = page.evaluate("document.documentElement.dataset.fx")
    check("gate set fx=none", fx == "none", f"data-fx={fx}")
    root_name = page.evaluate(
        "getComputedStyle(document.documentElement).viewTransitionName")
    check("root name none under fx=none", root_name == "none", f"got {root_name!r}")
    card_name = page.evaluate(
        "(() => { const i = document.querySelector('.listing-row "
        "img[style*=\"view-transition-name\"]'); return i ? "
        "getComputedStyle(i).viewTransitionName : 'NO-IMG' })()")
    check("inline card name neutralised", card_name == "none", f"got {card_name!r}")
    page.screenshot(path=str(SHOTS / "r22-e3-g2-none.png"))
    ctx.close()

    # --- C: JS blocked (fail-closed, D-MOTION-SAFE) -------------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              java_script_enabled=False)
    page = ctx.new_page()
    page.set_default_timeout(10000)
    print("C: JS blocked (no data-fx attr):")
    page.goto(f"{BASE}/property-for-sale/mombasa/", wait_until="domcontentloaded")
    page.wait_for_selector(".listing-row img", timeout=8000)
    fx = page.evaluate("document.documentElement.dataset.fx || null")
    root_name = page.evaluate(
        "getComputedStyle(document.documentElement).viewTransitionName")
    card_name = page.evaluate(
        "(() => { const i = document.querySelector('.listing-row "
        "img[style*=\"view-transition-name\"]'); return i ? "
        "getComputedStyle(i).viewTransitionName : 'NO-IMG' })()")
    rows_visible = page.evaluate(
        "[...document.querySelectorAll('.listing-row')].every("
        "r => getComputedStyle(r).display !== 'none' && "
        "getComputedStyle(r).visibility !== 'hidden')")
    check("no data-fx attr without JS", fx is None, f"data-fx={fx}")
    check("root name none without JS", root_name == "none", f"got {root_name!r}")
    check("card name none without JS", card_name == "none", f"got {card_name!r}")
    check("rows fully visible (Q3)", rows_visible)
    ctx.close()
    browser.close()

print(f"\n{'G2-E3-VERDICT: FAIL — ' + ', '.join(fails) if fails else 'G2-E3-VERDICT: PASS'}")
raise SystemExit(1 if fails else 0)
