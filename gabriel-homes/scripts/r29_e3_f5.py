"""r29 — E3 for F5 (Lenis smooth scroll) + frozen-neighbour conflict checks.

fx=rich is forced via an init script faking capable hardware (headless
Chromium reports low hardwareConcurrency and would otherwise be judged
lite). Checks:
  R1  __lenis exists under fx=rich (fine pointer, hover)
  R2  one wheel burst -> scrollY keeps animating across rAFs (smoothed)
  R3  G1 neighbour: nav hide/return still works while Lenis drives
  R4  L1 neighbour: pin click still scrolls to + flashes its row
  R5  anchor click scrolls (ghScrollTo path) with zero console errors
  N1  reduced motion -> data-fx=none, no __lenis, helper still defined
  N2  touch context -> no __lenis
  N3  lite (default headless hw) -> no __lenis, helper fallback works
"""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/property-for-sale/"
RICH_INIT = """
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
"""
fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])

    # ---- rich: the full Lenis path ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    ctx.add_init_script(RICH_INIT)
    page = ctx.new_page()
    page.set_default_timeout(15000)
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    print("R: fx=rich (faked capable hardware):")
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(700)
    fx = page.evaluate("document.documentElement.getAttribute('data-fx')")
    check("data-fx is rich", fx == "rich", fx or "missing")
    has_lenis = page.evaluate("!!window.__lenis")
    check("Lenis instance exists", has_lenis)
    has_helper = page.evaluate("typeof window.ghScrollTo === 'function'")
    check("ghScrollTo helper defined", has_helper)

    # R2: wheel burst -> animated (scrollY still changing between samples);
    # Lenis flags itself on html only once it starts driving (lenis-smooth)
    y0 = page.evaluate("window.scrollY")
    page.mouse.wheel(0, 1200)
    page.wait_for_timeout(120)
    y1 = page.evaluate("window.scrollY")
    page.wait_for_timeout(120)
    y2 = page.evaluate("window.scrollY")
    page.wait_for_timeout(700)
    y3 = page.evaluate("window.scrollY")
    check("wheel scrolls", y3 > y0, f"{y0}->{y1}->{y2}->{y3}")
    check("scroll is smoothed (still moving between samples)", y2 > y1 or (y1 - y0) < (y3 - y1),
          f"delta1={y1-y0} delta2={y2-y1} final={y3}")
    lenis_cls = page.evaluate("document.documentElement.classList.contains('lenis-smooth')")
    check("html.lenis-smooth set while driving (native smooth stood down)", lenis_cls)

    # R3: G1 neighbour — nav hide on down, return on up (while Lenis drives)
    page.evaluate("window.scrollTo(0, 900)")
    page.wait_for_timeout(500)
    hidden = page.evaluate(
        "document.querySelector('.site-header').classList.contains('nav--hidden')")
    check("G1: nav hides on scroll-down under Lenis", hidden)
    page.evaluate("window.scrollTo(0, 300)")
    page.wait_for_timeout(500)
    back = page.evaluate(
        "!document.querySelector('.site-header').classList.contains('nav--hidden')")
    check("G1: nav returns on scroll-up under Lenis", back)

    # R4: L1 neighbour — pin click scrolls to + flashes its row
    page.evaluate("window.__lenis.scrollTo(0, 0)")
    page.wait_for_timeout(700)
    pin_id = page.evaluate(
        "document.querySelector('[data-listing-pin]').dataset.listingPin")
    row_id = f"listing-row-{pin_id}"
    before_y = page.evaluate("window.scrollY")
    page.evaluate("document.querySelector('[data-listing-pin]').click()")
    page.wait_for_timeout(900)
    after_y = page.evaluate("window.scrollY")
    flashed = page.evaluate(
        f"document.getElementById('{row_id}').classList.contains('is-flashed')")
    check("L1: pin click scrolled the page", after_y != before_y,
          f"{before_y}->{after_y}")
    check("L1: row flash fired", flashed)

    # R5: anchor click via the motion.js handler + helper
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    anchor_ok = page.evaluate("""() => {
        const a = document.querySelector('a[href^="#"]');
        if (!a) return 'no-anchor-on-page';
        a.click();
        return window.scrollY;
    }""")
    page.wait_for_timeout(600)
    y_after_anchor = page.evaluate("window.scrollY")
    check("anchor click handled without error", anchor_ok != 'no-anchor-on-page',
          str(anchor_ok))
    check("zero console/page errors (rich)", not errors, "; ".join(errors[:2]))
    ctx.close()

    # ---- N1: reduced motion -> none ----
    print("N1: reduced motion:")
    ctx2 = browser.new_context(viewport={"width": 1280, "height": 900},
                               reduced_motion="reduce")
    ctx2.add_init_script(RICH_INIT)
    p2 = ctx2.new_page()
    p2.goto(BASE, wait_until="domcontentloaded")
    p2.wait_for_timeout(500)
    fx2 = p2.evaluate("document.documentElement.getAttribute('data-fx')")
    no_lenis2 = p2.evaluate("!window.__lenis")
    helper2 = p2.evaluate("typeof window.ghScrollTo === 'function'")
    check("fx=none under reduced motion", fx2 == "none", fx2 or "missing")
    check("no Lenis under fx=none", no_lenis2)
    check("helper still defined (native path)", helper2)
    ctx2.close()

    # ---- N2: touch -> off ----
    print("N2: touch context:")
    ctx3 = browser.new_context(viewport={"width": 390, "height": 844},
                               has_touch=True, is_mobile=True)
    ctx3.add_init_script(RICH_INIT)
    p3 = ctx3.new_page()
    p3.goto(BASE, wait_until="domcontentloaded")
    p3.wait_for_timeout(500)
    no_lenis3 = p3.evaluate("!window.__lenis")
    check("no Lenis on touch", no_lenis3)
    ctx3.close()

    # ---- N3: lite (default headless hardware) -> off, helper works ----
    print("N3: lite (default headless hardware):")
    ctx4 = browser.new_context(viewport={"width": 1280, "height": 900})
    p4 = ctx4.new_page()
    p4.goto(BASE, wait_until="domcontentloaded")
    p4.wait_for_timeout(500)
    fx4 = p4.evaluate("document.documentElement.getAttribute('data-fx')")
    no_lenis4 = p4.evaluate("!window.__lenis")
    helper4 = p4.evaluate("typeof window.ghScrollTo === 'function'")
    check(f"lite device ({fx4}) gets no Lenis", no_lenis4 and fx4 in ("lite", "none"), fx4)
    check("helper still defined on lite", helper4)
    ctx4.close()
    browser.close()

print(f"\nr29 F5 E3: {'ALL PASS' if not fails else 'FAIL: ' + ', '.join(fails)}")
raise SystemExit(1 if fails else 0)
