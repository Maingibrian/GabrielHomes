#!/usr/bin/env python3
"""r13 verification: bento shape-shift (Framer Spotlight Bento Grid replica).

Forces the same media features a real desktop reports (hover:hover,
pointer:fine), then proves the full interaction chain:
  1. html.bento-live-ready gets armed by the script
  2. hovering a 1x1 tile adds .is-grown -> grid-column: span 2 (width doubles)
  3. siblings re-pack (dense flow) while the FLIP animation runs
  4. un-hover restores the original geometry
  5. spotlight card never grows; hovering the spotlight is a no-op
Uses RAW mouse moves (bypasses Playwright's stability retries, which a
deliberately moving FLIP target always fails).
Saves before/mid/settled screenshots to download/.
"""
import json
import sys

from playwright.sync_api import sync_playwright

HOME = "http://127.0.0.1:3011/"
OUT = "/home/z/my-project/download"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    cdp = page.context.new_cdp_session(page)
    cdp.send("Emulation.setEmulatedMedia", {"features": [
        {"name": "hover", "value": "hover"},
        {"name": "pointer", "value": "fine"},
        {"name": "prefers-reduced-motion", "value": "no-preference"},
    ]})
    page.goto(HOME, wait_until="networkidle")

    probe = page.evaluate("""() => ({
        ready: document.documentElement.classList.contains('bento-live-ready'),
        cards: document.querySelectorAll('.bento-grid .bento-card').length,
    })""")
    print("armed:", json.dumps(probe))

    grid = page.locator(".bento-grid")
    grid.scroll_into_view_if_needed()
    page.wait_for_timeout(1600)  # reveal animations settle

    def geom(i):
        return page.evaluate(
            """(i) => { const c = document.querySelectorAll('.bento-grid .bento-card')[i];
                const r = c.getBoundingClientRect();
                return {w: c.offsetWidth, h: c.offsetHeight,
                        x: c.offsetLeft, y: c.offsetTop, vx: Math.round(r.x),
                        grown: c.classList.contains('is-grown')}; }""", i)

    before = [geom(1), geom(2), geom(3)]
    page.screenshot(path=f"{OUT}/r13-bento-before.png")

    # Raw mouse move to the center of card 1 (first small tile).
    page.evaluate("""() => {
        const c = document.querySelectorAll('.bento-grid .bento-card')[1];
        const r = c.getBoundingClientRect();
        window.__hx = r.x + r.width / 2; window.__hy = r.y + r.height / 2;
    }""")
    hx = page.evaluate("window.__hx")
    hy = page.evaluate("window.__hy")
    page.mouse.move(hx, hy, steps=6)
    page.wait_for_timeout(130)  # mid-flight
    mid = page.evaluate("""() => {
        const c = document.querySelectorAll('.bento-grid .bento-card')[1];
        return getComputedStyle(c).transform; }""")
    page.screenshot(path=f"{OUT}/r13-bento-midflight.png")
    page.wait_for_timeout(800)  # spring + settle pass done

    after = [geom(1), geom(2), geom(3)]
    print("before:", json.dumps(before))
    print("mid-flight transform:", (mid or "")[:64])
    print("after :", json.dumps(after))
    page.screenshot(path=f"{OUT}/r13-bento-grown.png")

    checks = {
        "armed": probe["ready"],
        "grown_class": after[0]["grown"],
        "width_doubled": after[0]["w"] > before[0]["w"] * 1.6,
        "neighbor_moved": (after[1]["x"] != before[1]["x"]) or
                          (after[1]["y"] != before[1]["y"]),
        "flip_ran": mid not in ("none", "", None),
        "spotlight_never_grown": page.evaluate(
            """() => !document.querySelector('.bento-card--spotlight')
                      .classList.contains('is-grown')"""),
        "settled_no_oscillation": page.evaluate(
            """() => { const g = document.querySelector('.bento-grid');
                 return g.classList.contains('bento-live') &&
                        g.querySelectorAll('.bento-card.is-grown').length === 1; }"""),
    }

    # Hover the spotlight card: must NOT grow (it is already 3x2).
    page.evaluate("""() => {
        const c = document.querySelector('.bento-card--spotlight');
        const r = c.getBoundingClientRect();
        window.__sx = r.x + r.width / 2; window.__sy = r.y + r.height / 2;
    }""")
    sx = page.evaluate("window.__sx")
    sy = page.evaluate("window.__sy")
    page.mouse.move(sx, sy, steps=4)
    page.wait_for_timeout(600)
    checks["spotlight_hover_noop"] = page.evaluate(
        """() => !document.querySelector('.bento-card--spotlight')
                  .classList.contains('is-grown')""")

    # Leave the grid entirely -> mosaic relaxes back to rest.
    page.mouse.move(20, 40, steps=4)
    page.wait_for_timeout(800)
    restored = geom(1)
    print("restored:", json.dumps(restored))
    checks["restored_after_unhover"] = (
        restored["w"] == before[0]["w"] and restored["x"] == before[0]["x"])
    page.screenshot(path=f"{OUT}/r13-bento-rest.png")

    print("CHECKS:", json.dumps(checks, indent=1))
    ok = all(checks.values())
    browser.close()
    sys.exit(0 if ok else 1)
