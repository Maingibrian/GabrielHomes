"""r34 E3 — G4 pointer polish, live browser evidence.

Proves, on Chromium (headless defaults to fx=lite — the bubble must NOT be
built there; a spoofed-rich context exercises the full behaviour):
  fx=lite (natural headless) — no .cursor-view element exists (gate needs
             rich + fine pointer + hover);
  fx=rich (spoofed hardwareConcurrency/deviceMemory) — hovering a listing
             row shows the "View" bubble (body.cursor-view-on, opacity 1)
             and it follows the pointer (--cx/--cy update); leaving the row
             hides it; the hero search submit is magnetic (--mx/--my move,
             computed transform is non-identity; reset on leave);
  keyboard — Tab focus never shows the bubble (cursor-view-on never set);
  bento exclusion — bento cards carry no data-cursor-view (M4 owns them);
  JS blocked — no bubble element, content intact (D-MOTION-SAFE);
  zero console/page errors.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
SEARCH = BASE + "/property-for-sale/"
failures = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def watch(page):
    page.on("console", lambda m: failures.append(f"console.error: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: failures.append(f"pageerror: {e}"))


SPOOF = """
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
"""

with sync_playwright() as pw:
    browser = pw.chromium.launch()

    # ---- Context 0: JS blocked — nothing is built, content intact --------
    ctx_d = browser.new_context(viewport={"width": 1280, "height": 900},
                                java_script_enabled=False)
    page_d = ctx_d.new_page()
    watch(page_d)
    page_d.goto(SEARCH, wait_until="load")
    check("JS blocked: no .cursor-view element",
          page_d.locator(".cursor-view").count() == 0)
    check("JS blocked: listing rows intact",
          page_d.locator("article.listing-row").count() >= 3)
    ctx_d.close()

    # ---- Context 1: fx=lite natural headless — gate refuses --------------
    ctx_l = browser.new_context(viewport={"width": 1280, "height": 900})
    page_l = ctx_l.new_page()
    watch(page_l)
    page_l.goto(SEARCH, wait_until="load")
    fx = page_l.evaluate("document.documentElement.getAttribute('data-fx')")
    check(f"fx gate runs (lite in headless) — {fx}", fx == "lite")
    check("fx=lite: no .cursor-view element (rich-only gate)",
          page_l.locator(".cursor-view").count() == 0)
    ctx_l.close()

    # ---- Context 2: fx=rich spoofed — full behaviour ---------------------
    ctx_r = browser.new_context(viewport={"width": 1280, "height": 900})
    ctx_r.add_init_script(SPOOF)
    page_r = ctx_r.new_page()
    watch(page_r)
    page_r.goto(SEARCH, wait_until="load")
    fx = page_r.evaluate("document.documentElement.getAttribute('data-fx')")
    check("spoofed device reaches fx=rich", fx == "rich")
    check("rich: bubble element exists (JS-built)",
          page_r.locator(".cursor-view").count() == 1)
    check("rich: bubble is aria-hidden + 'View'",
          page_r.evaluate(
              "document.querySelector('.cursor-view').getAttribute('aria-hidden')")
          == "true"
          and page_r.inner_text(".cursor-view").strip().lower() == "view")  # uppercase transform

    # hover the first listing row: bubble appears and follows the pointer.
    # OPS: the map sits on top, so the first row starts BELOW the fold —
    # scroll it into the viewport first or the mouse cannot reach it.
    row = page_r.locator("article.listing-row").first
    row.scroll_into_view_if_needed()
    page_r.wait_for_timeout(400)
    box = row.bounding_box()
    cx, cy = box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.4
    page_r.mouse.move(cx - 60, cy - 40)
    page_r.mouse.move(cx, cy, steps=6)
    page_r.wait_for_timeout(250)
    check("rich: hovering a row shows the bubble (cursor-view-on)",
          page_r.evaluate("document.body.classList.contains('cursor-view-on')"))
    check("rich: bubble opacity 1",
          page_r.evaluate(
              "getComputedStyle(document.querySelector('.cursor-view')).opacity")
          == "1")
    cx2, cy2 = cx + 80, cy + 30
    page_r.mouse.move(cx2, cy2, steps=4)
    page_r.wait_for_timeout(120)
    moved = page_r.evaluate(
        "document.querySelector('.cursor-view').style.getPropertyValue('--cx')")
    check("rich: bubble follows the pointer (--cx updates)", "px" in moved)
    page_r.screenshot(path="LOOP/audit-screens/r34-g4-row-cursor.png")
    page_r.mouse.move(cx2, 60, steps=4)  # leave the rows (header area — no target)
    page_r.wait_for_timeout(250)
    check("rich: leaving the row hides the bubble",
          not page_r.evaluate("document.body.classList.contains('cursor-view-on')"))

    # bento exclusion is a home-page fact; assert the search page rows carry
    # the hook and (on home) bento cards do not
    n_hooked = page_r.evaluate(
        "document.querySelectorAll('[data-cursor-view]').length")
    check("rich: search rows carry data-cursor-view", n_hooked >= 3,
          f"{n_hooked} targets")
    page_r.goto(BASE + "/", wait_until="load")
    page_r.wait_for_timeout(1400)  # let the hero entrance settle before evidence
    bento_hooked = page_r.evaluate(
        "document.querySelectorAll('.bento-card[data-cursor-view]').length")
    nearby_hooked = page_r.evaluate(
        "document.querySelectorAll('.nearby-card[data-cursor-view]').length")
    check("bento cards carry NO data-cursor-view (M4 owns the pointer)",
          bento_hooked == 0)
    check("nearby cards carry data-cursor-view", nearby_hooked >= 2,
          f"{nearby_hooked} targets")

    # magnetic: hover the hero search submit
    sub = page_r.locator(".search-bar__submit")
    sbox = sub.bounding_box()
    sx, sy = sbox["x"] + sbox["width"] * 0.8, sbox["y"] + sbox["height"] * 0.75
    page_r.mouse.move(sx - 40, sy - 20)
    page_r.mouse.move(sx, sy, steps=5)
    page_r.wait_for_timeout(300)
    mx = page_r.evaluate(
        "document.querySelector('.search-bar__submit').style.getPropertyValue('--mx')")
    tr = page_r.evaluate(
        "getComputedStyle(document.querySelector('.search-bar__submit')).transform")
    check("rich: magnet leans toward the cursor (--mx set)", "px" in mx, mx)
    check("rich: magnet transform is non-identity", tr not in ("none", ""), tr)
    page_r.screenshot(path="LOOP/audit-screens/r34-g4-magnet.png")
    page_r.mouse.move(sx - 300, sy - 200, steps=4)
    page_r.wait_for_timeout(350)
    tr2 = page_r.evaluate(
        "getComputedStyle(document.querySelector('.search-bar__submit')).transform")
    check("rich: magnet resets on leave", tr2 in ("none", "matrix(1, 0, 0, 1, 0, 0)"),
          tr2)

    # keyboard: focus never shows the bubble
    page_r.keyboard.press("Tab")
    page_r.keyboard.press("Tab")
    page_r.keyboard.press("Tab")
    page_r.wait_for_timeout(150)
    check("keyboard focus never shows the bubble",
          not page_r.evaluate(
              "document.body.classList.contains('cursor-view-on')"))

    ctx_r.close()
    browser.close()

print()
if failures:
    print(f"r34 G4 E3: {len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("r34 G4 E3: ALL PASS")
