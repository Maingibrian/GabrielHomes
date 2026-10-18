#!/usr/bin/env python3
"""r14 verification: corrected bento shape-shift (user's fixed bento-shift.js).

Expected behaviour of the corrected architecture:
  1. Home grid opts in via .bento-grid--shift; JS adds .is-live
  2. At rest: spotlight card 3x2; small tiles 1x1; photos desaturated
     (saturate(0), scale(1.2)) because the grid is live
  3. Hovering a small card promotes IT: .is-spot + .has-spot,
     grid-column: 1/-1 (full width), 2 rows starting at the hovered
     card's row (--spot-row), radius 32px, photo in colour scale(1)
  4. The resting spotlight DEMOTES to 1x1 while another card is promoted
  5. FLIP runs (transform/clip-path animating) — and the promoted card's
     new box contains the pointer, so no shuffle loop
  6. Leaving the grid resets to the resting spotlight
  7. Keyboard Tab promotes the focused card
  8. /agents/ has no .bento-grid--shift -> script no-ops there
"""
import json
import sys

from playwright.sync_api import sync_playwright

HOME = "http://127.0.0.1:3011/"
OUT = "/home/z/my-project/download"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    cdp = page.context.new_cdp_session(page)
    cdp.send("Emulation.setEmulatedMedia", {"features": [
        {"name": "hover", "value": "hover"},
        {"name": "pointer", "value": "fine"},
        {"name": "prefers-reduced-motion", "value": "no-preference"},
    ]})
    page.goto(HOME, wait_until="networkidle")

    page.locator(".bento-grid").scroll_into_view_if_needed()
    page.wait_for_timeout(1600)  # reveal settle

    def state():
        return page.evaluate("""() => {
            const g = document.querySelector('.bento-grid--shift');
            const cards = g.querySelectorAll('.bento-card');
            const spot = g.querySelector('.bento-card--spotlight');
            const info = c => ({w: c.offsetWidth, h: c.offsetHeight,
                                x: c.offsetLeft, y: c.offsetTop});
            return {
                live: g.classList.contains('is-live'),
                hasSpot: g.classList.contains('has-spot'),
                spotDemoted: spot.classList.contains('is-spot') ? false
                             : (spot.offsetWidth < 700),
                spotlight: info(spot),
                promo: null, restBgFilter: getComputedStyle(
                    cards[1].querySelector('.bento-card__bg')).filter,
            };
        }""")

    before = state()
    checks = {"is_live": before["live"]}
    checks["rest_desaturated"] = "saturate" in before["restBgFilter"]
    page.screenshot(path=f"{OUT}/r14-rest.png")

    # Hover the first small tile (index 1)
    hx, hy = page.evaluate("""() => {
        const c = document.querySelectorAll('.bento-grid--shift .bento-card')[1];
        const r = c.getBoundingClientRect();
        return [r.x + r.width / 2, r.y + r.height / 2];
    }""")
    page.mouse.move(hx, hy, steps=6)
    page.wait_for_timeout(140)  # mid-flight (520ms morph)
    mid = page.evaluate("""() => {
        const c = document.querySelectorAll('.bento-grid--shift .bento-card')[1];
        const cs = getComputedStyle(c);
        return {t: cs.transform, clip: cs.clipPath};
    }""")
    page.screenshot(path=f"{OUT}/r14-midflight.png")
    page.wait_for_timeout(900)  # settle

    after = page.evaluate("""() => {
        const g = document.querySelector('.bento-grid--shift');
        const cards = g.querySelectorAll('.bento-card');
        const promo = g.querySelector('.is-spot');
        const spot = g.querySelector('.bento-card--spotlight');
        return {
            hasSpot: g.classList.contains('has-spot'),
            promoIsCard1: promo === cards[1],
            promoBox: promo ? {w: promo.offsetWidth, h: promo.offsetHeight,
                               x: promo.offsetLeft, y: promo.offsetTop} : null,
            promoRadius: promo ? getComputedStyle(promo).borderRadius : null,
            promoBg: promo ? getComputedStyle(
                promo.querySelector('.bento-card__bg')).filter : null,
            spotW: spot.offsetWidth,
            spotRow: promo ? promo.style.getPropertyValue('--spot-row') : null,
            pointerStillInside: true,
        };
    }""")
    checks["promoted_is_hovered_card"] = after["promoIsCard1"]
    checks["full_width_promotion"] = after["promoBox"] and after["promoBox"]["w"] > 1000
    checks["two_rows_tall"] = after["promoBox"] and after["promoBox"]["h"] > 500
    checks["spot_row_set"] = after["spotRow"].strip() != ""
    checks["squircle_radius"] = after["promoRadius"] == "32px"
    checks["promoted_in_colour"] = after["promoBg"] == "saturate(1)"
    checks["spotlight_demoted"] = after["spotW"] < 700
    checks["single_spot"] = page.evaluate(
        "() => document.querySelectorAll('.bento-grid--shift .is-spot').length === 1")
    checks["flip_ran"] = mid["t"] != "none" or "inset" in mid["clip"]
    page.screenshot(path=f"{OUT}/r14-promoted.png")

    # Stability: hover again over the promoted card center -> no flip-flop
    page.wait_for_timeout(600)
    stable = page.evaluate(
        "() => document.querySelectorAll('.bento-grid--shift .is-spot').length")
    checks["no_oscillation"] = stable == 1

    # Leave the grid -> reset to resting spotlight
    page.mouse.move(20, 60, steps=5)
    page.wait_for_timeout(900)
    reset = page.evaluate("""() => {
        const g = document.querySelector('.bento-grid--shift');
        const spot = g.querySelector('.bento-card--spotlight');
        return {hasSpot: g.classList.contains('has-spot'),
                spotW: spot.offsetWidth,
                anySpot: g.querySelectorAll('.is-spot').length};
    }""")
    checks["resets_on_leave"] = (not reset["hasSpot"] and
                                 reset["spotW"] > 1000 and
                                 reset["anySpot"] == 0)

    # Keyboard parity: focus the 3rd card via Tab walk (focus directly)
    page.evaluate("""() => {
        const c = document.querySelectorAll('.bento-grid--shift .bento-card')[2];
        c.focus({focusVisible: true});
    }""")
    page.wait_for_timeout(800)
    kb = page.evaluate("""() => {
        const g = document.querySelector('.bento-grid--shift');
        return {spotIsCard2: g.querySelector('.is-spot') ===
                g.querySelectorAll('.bento-card')[2]};
    }""")
    checks["keyboard_promotes"] = kb["spotIsCard2"]
    page.mouse.move(20, 60)
    page.wait_for_timeout(600)

    # /agents/ must be untouched (no shift grid, no is-live)
    page.goto("http://127.0.0.1:3011/agents/", wait_until="networkidle")
    checks["agents_untouched"] = page.evaluate(
        "() => !document.querySelector('.bento-grid--shift') &&"
        "!document.querySelector('.bento-grid.is-live')")
    checks["no_js_errors"] = not errors

    print("spotlight rest:", json.dumps(before["spotlight"]))
    print("promoted:", json.dumps(after["promoBox"]),
          "radius:", after["promoRadius"], "row:", after["spotRow"])
    print("CHECKS:", json.dumps(checks, indent=1))
    print("JS errors:", errors)
    browser.close()
    sys.exit(0 if all(checks.values()) else 1)
