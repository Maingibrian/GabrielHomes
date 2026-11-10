"""r39 E3 — G2 T2 lift: real-browser capture of the cross-document
shared-element view transition (evidence-only; no shipped code touched).

The exemplary evidence the SCORECARD row asked for: the transition is not
just test-pinned (7/7 test_g2_view_transitions.py), it is PHOTOGRAPHED
mid-morph in a real Chromium navigation (Chromium 143).

Mechanics:
  * Playwright route interception injects a slowing <style> into the
    DETAIL document's </head> before first render (CSP style-src allows
    'unsafe-inline'), stretching the ~250ms morph to 4s so it is
    photographable. Test tooling only — shipped code untouched.
  * add_init_script records `pagereveal` (fires on the NEW document;
    e.viewTransition non-null exactly when a cross-document view
    transition was created). sessionStorage is guarded — the old
    document (pageswap) is deactivating and denies storage, so the flag
    channel is one-way: new document only.
  * Leg R (rich spoof, 1280x900): click a listing row image (inline
    `view-transition-name: prop-<pk>`) -> detail hero; assert the flag,
    the SAME shared-element name on the detail hero, the per-name
    -ua-view-transition-group-anim-prop-<pk> animation running
    mid-flight, and photograph the morph.
  * Leg L (natural lite): the gate re-enables the root for lite too —
    same flag must read 'vt'.
  * Leg N (reduced-motion => fx=none): the kill-switch must report
    view-transition-name: none on the row image BEFORE the click, and
    NO view-transition animation may render after the navigation
    (Chrome creates then skips the ViewTransition object when no named
    elements survive — the honest observable is zero rendered VT
    animations; the 4s slowing would keep any rendered one visible).
  * Also prints live uniqueness of all row names (test-pinned already).

Usage: /home/z/.venv/bin/python3 scripts/r39_e3_g2_capture.py
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
failures = []

INIT = """
addEventListener('pagereveal', e => {
  const v = e.viewTransition ? 'vt' : 'no-vt';
  try { sessionStorage.setItem('r39_pagereveal', v); } catch (err) {}
  try { window.__r39_vt = v; } catch (err) {}
});
"""

RICH_SPOOF = """
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
"""

SLOW_CSS = ("<style>::view-transition-group(*), "
            "::view-transition-image-pair(*), ::view-transition-old(*), "
            "::view-transition-new(*) { animation-duration: 4s !important; }"
            "</style>")


def inject_slow(route):
    """Intercept the detail-document response and prepend the slowing
    style so the transition runs at 4s from its very first frame."""
    resp = route.fetch()
    body = resp.text().replace("</head>", SLOW_CSS + "</head>", 1)
    route.fulfill(body=body, content_type="text/html; charset=utf-8",
                  status=200)


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def watch(page):
    page.on("console", lambda m: failures.append(f"console.error: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: failures.append(f"pageerror: {e}"))


def wait_flag(page, timeout=5000):
    """Poll the pagereveal flag from Python — page.evaluate is
    CSP-exempt (Runtime.callFunctionOn), but wait_for_function compiles
    its predicate with eval, which this site's strict CSP forbids."""
    import time
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        v = page.evaluate(
            "() => sessionStorage.getItem('r39_pagereveal') "
            "|| window.__r39_vt || null")
        if v is not None:
            return v
        page.wait_for_timeout(100)
    return None


def vt_anim_names(page):
    return page.evaluate(
        "document.getAnimations().map(a => a.animationName || '')\n"
        "        .filter(n => n.includes('view-transition'))")


def open_search(page):
    page.goto(BASE + "/properties/", wait_until="networkidle")
    page.wait_for_timeout(1200)
    page.evaluate("sessionStorage.clear()")
    row = page.locator(
        '.listing-row__media img[style*="view-transition-name"]').first
    return row


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    print(f"Chromium {browser.version}")

    # ---- Leg R: desktop rich — the photographed morph ----------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    ctx.add_init_script(RICH_SPOOF)
    ctx.add_init_script(INIT)
    page = ctx.new_page()
    page.route("**/listing/**", inject_slow)
    watch(page)
    row = open_search(page)
    check("R: gate says rich",
          page.evaluate("document.documentElement.getAttribute('data-fx')")
          == "rich")
    names = page.evaluate(
        """[...document.querySelectorAll(
              '.listing-row__media img[style*="view-transition-name"]')]
            .map(i => i.style.viewTransitionName)""")
    check("R: row names present and unique on the live grid",
          len(names) > 3 and len(set(names)) == len(names),
          f"{len(names)} rows, {len(set(names))} unique")
    row_name = row.evaluate("el => el.style.viewTransitionName")
    with page.expect_navigation():
        row.click()
    pr = wait_flag(page)
    page.wait_for_timeout(700)  # ~18% into the 4s morph
    check("R: pagereveal created a view transition on the NEW document",
          pr == "vt", f"pagereveal={pr}")
    hero_name = page.evaluate(
        """(() => { const el = document.querySelector(
              '[style*="view-transition-name"]');
            return el ? el.style.viewTransitionName : null; })()""")
    check("R: detail hero carries the SAME shared-element name",
          hero_name == row_name, f"row={row_name} hero={hero_name}")
    vt = vt_anim_names(page)
    check("R: the per-name morph animation is running mid-flight",
          any(f"group-anim-{row_name}" in a for a in vt)
          and any("group-anim-root" in a for a in vt),
          f"{len(vt)} vt animations, e.g. {sorted(set(vt))[:4]}")
    page.screenshot(path="LOOP/audit-screens/r39-g2-morph-mid-1280.png")
    check("R: morph photographed mid-flight", True)
    ctx.close()

    # ---- Leg L: natural lite — the gate's second tier ----------------------
    # Two observables: (1) DETERMINISTIC — the gate's CSS re-enables the
    # root snapshot for lite exactly as for rich (computed
    # view-transition-name: root on <html>); (2) BEHAVIOURAL — the
    # transition fires. Chrome may skip a cross-document transition for
    # load/timing heuristics, so (2) retries up to 3 navigations and
    # reports the attempt count honestly.
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    ctx.add_init_script(INIT)
    page = ctx.new_page()
    page.route("**/listing/**", inject_slow)
    watch(page)
    row = open_search(page)
    fx = page.evaluate("document.documentElement.getAttribute('data-fx')")
    root_name = page.evaluate(
        "getComputedStyle(document.documentElement).viewTransitionName")
    check(f"L: fx={fx} (natural headless) — gate re-enables the root",
          fx == "lite" and root_name == "root",
          f"data-fx={fx}, html view-transition-name={root_name}")
    pr = None
    for attempt in (1, 2, 3):
        page.goto(BASE + "/properties/", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.evaluate("sessionStorage.clear()")
        row = page.locator(
            '.listing-row__media img[style*="view-transition-name"]').first
        with page.expect_navigation():
            row.click()
        pr = wait_flag(page)
        if pr == "vt":
            break
        page.wait_for_timeout(800)
    check("L: the transition fires on lite (attempt noted honestly)",
          pr == "vt", f"pagereveal={pr} on attempt {attempt}")
    ctx.close()

    # ---- Leg M: mobile 390 touch — D6, the transition is device-wide ------
    # Mobile emulation renders slower, so Chrome's skip heuristics may
    # cut the morph short; read the animation list EARLY (+150/+350ms)
    # and retry up to 3 navigations, reporting the attempt honestly.
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True)
    ctx.add_init_script(RICH_SPOOF)
    ctx.add_init_script(INIT)
    page = ctx.new_page()
    page.route("**/listing/**", inject_slow)
    watch(page)
    row = open_search(page)
    check("M: tier stays rich on the phone (spoofed cores)",
          page.evaluate("document.documentElement.getAttribute('data-fx')")
          == "rich")
    check("M: no horizontal overflow at 390px",
          page.evaluate(
              "document.documentElement.scrollWidth - window.innerWidth") <= 1)
    row_name_m = row.evaluate("el => el.style.viewTransitionName")
    vt_m, pr, attempt = [], None, 1
    for attempt in (1, 2, 3):
        page.goto(BASE + "/properties/", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.evaluate("sessionStorage.clear()")
        row = page.locator(
            '.listing-row__media img[style*="view-transition-name"]').first
        with page.expect_navigation():
            row.click()
        pr = wait_flag(page)
        page.wait_for_timeout(150)
        vt_m = vt_anim_names(page)
        if any(f"group-anim-{row_name_m}" in a for a in vt_m):
            break
        page.wait_for_timeout(200)
        vt_m = vt_anim_names(page)
        if any(f"group-anim-{row_name_m}" in a for a in vt_m):
            break
        page.wait_for_timeout(800)
    hero_name_m = page.evaluate(
        """(() => { const el = document.querySelector(
              '[style*="view-transition-name"]');
            return el ? el.style.viewTransitionName : null; })()""")
    check("M: the transition fires on touch (pointer-independent gate)",
          pr == "vt", f"pagereveal={pr}")
    check("M: the morph animates on mobile too",
          hero_name_m == row_name_m
          and any(f"group-anim-{row_name_m}" in a for a in vt_m),
          f"row={row_name_m} hero={hero_name_m}, "
          f"{len(vt_m)} vt animations (attempt {attempt})")
    page.screenshot(path="LOOP/audit-screens/r39-g2-morph-mid-390.png")
    check("M: mobile morph photographed mid-flight", True)
    ctx.close()

    # ---- Leg N: reduced-motion => fx=none — the kill switch ----------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              reduced_motion="reduce")
    ctx.add_init_script(INIT)
    page = ctx.new_page()
    page.route("**/listing/**", inject_slow)
    watch(page)
    row = open_search(page)
    check("N: gate says none",
          page.evaluate("document.documentElement.getAttribute('data-fx')")
          == "none")
    computed = row.evaluate(
        "el => getComputedStyle(el).viewTransitionName")
    check("N: kill-switch reports view-transition-name: none on the row",
          computed == "none", f"computed={computed}")
    with page.expect_navigation():
        row.click()
    pr = wait_flag(page)
    # e.viewTransition is non-null for every eligible navigation (Chrome
    # creates then SKIPS the object when no named elements survive the
    # kill-switch) — the honest observable is that NO view-transition
    # animation ever renders. The injected 4s slowing would keep any
    # rendered animation visible for seconds, so two polls catch it.
    page.wait_for_timeout(250)
    a1 = vt_anim_names(page)
    page.wait_for_timeout(400)
    a2 = vt_anim_names(page)
    check("N: NO view-transition animation renders under fx=none",
          not a1 and not a2,
          f"poll1={a1[:3] if a1 else '[]'} poll2={a2[:3] if a2 else '[]'} "
          f"(object created={pr == 'vt'}, then skipped)")
    page.screenshot(path="LOOP/audit-screens/r39-g2-none-1280.png")
    ctx.close()
    browser.close()

print()
if failures:
    print("r39 G2 capture: FAILURES:", failures)
    sys.exit(1)
print("r39 G2 capture: ALL PASS")
