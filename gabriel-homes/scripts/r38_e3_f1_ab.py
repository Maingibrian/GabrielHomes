"""r38 E3 — F1 tokenisation pass: computed-style A/B proof.

The F1 T2 lift rewrites search.css hex literals to token var() references
(8x #fff -> var(--white), 2x #e7e4df -> var(--map-stage), a new token).
A var() swap of identical values must be render-invisible. This script
PROVES it: run with `before` (old css on disk), make the edit, run with
`after` — the two computed-style snapshots must be exactly equal.

Probed surfaces (every declaration the edit touches):
  stage/map backgrounds, map reset button (base + focus outline),
  map price pin (base + focus), market-filter text color,
  market-filter.is-active::after badge (forced), listing-row background.

Usage: /home/z/.venv/bin/python3 scripts/r38_e3_f1_ab.py before|after
Exit 1 on any missing probe surface.
"""
import json
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
PHASE = sys.argv[1] if len(sys.argv) > 1 else "before"
OUT = f"/tmp/r38_f1_{PHASE}.json"

# (key, selector, mode, property)  mode: "" base | "focus" | "after-badge"
PROBES = [
    ("stage_bg", ".search-map-stage", "", "backgroundColor"),
    ("map_bg", ".search-map", "", "backgroundColor"),
    ("reset_bg", ".search-map__reset", "", "backgroundColor"),
    ("reset_color", ".search-map__reset", "", "color"),
    ("pin_bg", ".map-price-pin", "", "backgroundColor"),
    ("pin_color", ".map-price-pin", "", "color"),
    ("filter_color", ".market-filter", "", "color"),
    ("row_bg", ".listing-row", "", "backgroundColor"),
    ("reset_focus_outline", ".search-map__reset", "focus", "outlineColor"),
    ("pin_focus_bg", ".map-price-pin", "focus", "backgroundColor"),
    ("pin_focus_outline", ".map-price-pin", "focus", "outlineColor"),
    ("badge_bg", ".market-filter", "after-badge", "backgroundColor"),
    ("badge_color", ".market-filter", "after-badge", "color"),
]

JS_BASE = """
sel => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const cs = getComputedStyle(el);
  return {bg: cs.backgroundColor, color: cs.color, outline: cs.outlineColor};
}
"""

JS_FOCUS = """
sel => {
  const el = document.querySelector(sel);
  if (!el) return null;
  el.focus();
  const cs = getComputedStyle(el);
  return {bg: cs.backgroundColor, color: cs.color, outline: cs.outlineColor};
}
"""

results, missing = {}, []
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
    page.goto(BASE + "/properties/", wait_until="networkidle")
    page.wait_for_timeout(1200)
    for key, sel, mode, prop in PROBES:
        if mode == "focus":
            r = page.evaluate(JS_FOCUS, sel)
        elif mode == "after-badge":
            r = page.evaluate(
                """sel => {
                  const el = document.querySelector(sel);
                  if (!el) return null;
                  el.classList.add('is-active');
                  const cs = getComputedStyle(el, '::after');
                  return {bg: cs.backgroundColor, color: cs.color};
                }""", sel)
        else:
            r = page.evaluate(JS_BASE, sel)
        if r is None:
            missing.append(f"{key} ({sel})")
        else:
            results[key] = r.get(
                {"backgroundColor": "bg", "color": "color",
                 "outlineColor": "outline"}[prop])
    page.screenshot(path=f"LOOP/audit-screens/r38-f1-search-{PHASE}.png")
    browser.close()

if missing:
    print("MISSING PROBES:", missing)
    sys.exit(1)

with open(OUT, "w") as fh:
    json.dump(results, fh, indent=1, sort_keys=True)
for k in sorted(results):
    print(f"  {k:22s} {results[k]}")
print(f"r38 F1 A/B snapshot '{PHASE}' -> {OUT} ({len(results)} probes)")
