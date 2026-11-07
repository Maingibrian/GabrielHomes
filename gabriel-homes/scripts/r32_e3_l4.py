"""r32 E3 — L4 detail gallery lightbox, live browser evidence.

Proves, on Chromium (fx=lite in headless — Lenis not initialised, the
window.__lenis guards must hold):
  detail page  — JS-injected "Enlarge photo" control exists; no .lightbox
                 in the DOM before first open (JS-built, lazy);
  open         — role=dialog + aria-modal, focus lands on the close
                 button, html.lb-open scroll lock set;
  focus trap   — Tab cycles INSIDE the dialog (never escapes);
  keyboard     — ArrowRight advances image + counter (gallery stays in
                 sync via show()); Escape closes and restores focus to
                 the opener;
  backdrop     — clicking the backdrop (the .lightbox element itself)
                 closes; clicking a nav button does NOT;
  swipe        — the original touch swipe still advances the gallery;
  fx=none      — viewer still opens and functions, transition none;
  JS blocked   — no expand control, no lightbox, gallery fully visible
                 (D-MOTION-SAFE);
  zero console/page errors.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
DETAIL = BASE + "/listing/3br-apartment-in-nyali-19/"   # 2 images: swipe + arrows meaningful
SINGLE = BASE + "/listing/3br-home-near-haller-park-bamburi-88/"  # 1 image: fallback path
failures = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def console_watch(page):
    page.on("console", lambda m: failures.append(f"console.{m.type}: {m.text}")
            if m.type in ("error",) else None)
    page.on("pageerror", lambda e: failures.append(f"pageerror: {e}"))


with sync_playwright() as pw:
    browser = pw.chromium.launch()

    # ---- Context A: default (fx=lite in headless) ------------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    console_watch(page)
    page.goto(DETAIL, wait_until="networkidle")

    expand = page.query_selector('button[aria-label="Enlarge photo"]')
    check("expand control is JS-injected", expand is not None)
    check("no lightbox DOM before first open (lazy build)",
          page.query_selector(".lightbox") is None)
    if not expand:
        print("r32 L4 E3: FAILURES:", failures)
        sys.exit(1)

    check("gallery main carries the G2 shared-element name",
          "view-transition-name: prop-" in
          page.get_attribute("[data-gallery-main]", "style"))

    expand.click()
    page.wait_for_selector(".lightbox.is-open", timeout=3000)
    check("lightbox opens with role=dialog + aria-modal",
          page.get_attribute(".lightbox", "role") == "dialog" and
          page.get_attribute(".lightbox", "aria-modal") == "true")
    check("focus lands inside the dialog (close button)",
          page.evaluate("document.activeElement.classList.contains('lightbox__close')"))
    check("scroll lock set (html.lb-open)",
          page.evaluate("document.documentElement.classList.contains('lb-open')"))

    # Focus trap: walk Tab several times, focus must stay inside .lightbox.
    trapped = True
    for _ in range(6):
        page.keyboard.press("Tab")
        if not page.evaluate("document.querySelector('.lightbox').contains(document.activeElement)"):
            trapped = False
            break
    check("focus trap: Tab never leaves the dialog", trapped)
    page.keyboard.press("Shift+Tab")
    check("Shift+Tab also stays inside",
          page.evaluate("document.querySelector('.lightbox').contains(document.activeElement)"))

    first_bg = page.evaluate("document.querySelector('.lightbox__main').style.backgroundImage")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(60)
    second_bg = page.evaluate("document.querySelector('.lightbox__main').style.backgroundImage")
    counter = page.inner_text("[data-lb-current]")
    check("ArrowRight advances the viewer image", first_bg != second_bg, counter)
    check("viewer counter updated", counter.strip() == "2", counter)
    page.wait_for_timeout(600)  # the gallery crossfade settles at ~480ms
    gallery_bg = page.evaluate("document.querySelector('[data-gallery-main]').style.backgroundImage")
    check("gallery main stays in sync with the viewer", gallery_bg == second_bg)

    page.keyboard.press("Escape")
    page.wait_for_timeout(60)
    check("Escape closes the viewer",
          page.evaluate("!document.querySelector('.lightbox').classList.contains('is-open')"))
    check("scroll lock released",
          page.evaluate("!document.documentElement.classList.contains('lb-open')"))
    check("focus restored to the opener",
          page.evaluate("document.activeElement.getAttribute('aria-label') === 'Enlarge photo'"))

    # Backdrop click closes; nav button click does not.
    expand.click()
    page.wait_for_selector(".lightbox.is-open", timeout=3000)
    page.mouse.click(12, 12)  # the .lightbox padding area = backdrop
    page.wait_for_timeout(60)
    check("backdrop click closes the viewer",
          page.evaluate("!document.querySelector('.lightbox').classList.contains('is-open')"))
    expand.click()
    page.wait_for_selector(".lightbox.is-open", timeout=3000)
    page.click(".lightbox__nav--next")
    page.wait_for_timeout(60)
    check("nav button click does NOT close the viewer",
          page.evaluate("document.querySelector('.lightbox').classList.contains('is-open')"))

    # Screenshot of the open viewer (desktop). Settle first: the focus
    # changes above smooth-scroll the page (html scroll-behavior:smooth),
    # and a mid-scroll capture offsets the fixed layer in the compositor.
    page.wait_for_timeout(700)
    page.screenshot(path="LOOP/audit-screens/r32-l4-lightbox-1280.png")
    page.keyboard.press("Escape")
    page.wait_for_timeout(60)

    # Original touch swipe still works on the gallery main.
    before = page.inner_text("[data-gallery-current]")
    page.evaluate("""() => {
        const main = document.querySelector('[data-gallery-main]');
        const r = main.getBoundingClientRect();
        const y = r.top + r.height / 2;
        const mk = (x) => new Touch({identifier: 1, target: main,
                                     clientX: x, clientY: y});
        main.dispatchEvent(new TouchEvent('touchstart',
            {touches: [mk(r.left + 300)], bubbles: true}));
        main.dispatchEvent(new TouchEvent('touchend',
            {changedTouches: [mk(r.left + 200)], bubbles: true}));
    }""")
    page.wait_for_timeout(60)
    after = page.inner_text("[data-gallery-current]")
    check("original touch swipe still advances the gallery", before != after,
          f"{before} -> {after}")
    ctx.close()

    # ---- Context B: reduced motion (fx=none) — viewer still functions ----
    ctx_b = browser.new_context(viewport={"width": 1280, "height": 900},
                                reduced_motion="reduce")
    page_b = ctx_b.new_page()
    console_watch(page_b)
    page_b.goto(DETAIL, wait_until="networkidle")
    page_b.click('button[aria-label="Enlarge photo"]')
    page_b.wait_for_selector(".lightbox.is-open", timeout=3000)
    check("fx=none: viewer still opens and functions",
          page_b.evaluate(
              "getComputedStyle(document.querySelector('.lightbox')).visibility === 'visible'"))
    dur = page_b.evaluate(
        "getComputedStyle(document.querySelector('.lightbox')).transitionDuration")
    check("fx=none: fade is instant (transition none)", "0s" in dur, dur)
    page_b.keyboard.press("Escape")
    ctx_b.close()

    # ---- Context C: JS blocked — no dead control, content visible --------
    ctx_c = browser.new_context(viewport={"width": 1280, "height": 900},
                                java_script_enabled=False)
    page_c = ctx_c.new_page()
    page_c.goto(DETAIL, wait_until="load")
    check("JS blocked: no expand control",
          page_c.query_selector('button[aria-label="Enlarge photo"]') is None)
    check("JS blocked: no lightbox markup",
          page_c.query_selector(".lightbox") is None)
    check("JS blocked: gallery main still shows the photo",
          "background-image" in
          (page_c.get_attribute("[data-gallery-main]", "style") or ""))
    ctx_c.close()

    # ---- Context D: single-image listing — the fallback path --------------
    ctx_d = browser.new_context(viewport={"width": 1280, "height": 900})
    page_d = ctx_d.new_page()
    console_watch(page_d)
    page_d.goto(SINGLE, wait_until="networkidle")
    check("single-image listing: no thumbs, viewer still ships via fallback",
          page_d.query_selector("[data-gallery-thumb]") is None and
          page_d.query_selector('button[aria-label="Enlarge photo"]') is not None)
    page_d.click('button[aria-label="Enlarge photo"]')
    page_d.wait_for_selector(".lightbox.is-open", timeout=3000)
    check("single-image listing: viewer opens, counter reads 1 / 1",
          page_d.inner_text("[data-lb-current]").strip() == "1")
    page_d.screenshot(path="LOOP/audit-screens/r32-l4-lightbox-single-1280.png")
    ctx_d.close()
    browser.close()

print()
if failures:
    print("r32 L4 E3: FAILURES:", failures)
    sys.exit(1)
print("r32 L4 E3: ALL PASS")
