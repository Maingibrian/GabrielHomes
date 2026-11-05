"""r27 — E3 smoke for G1: the floating pill nav hides and returns.

Rich fx: scroll down past 160px -> header gains nav--hidden; scroll up ->
class removed; focus into the header returns it. fx=none: the class never
appears. JS blocked: header stays visible (D-MOTION-SAFE, class is
JS-only).
"""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/about/"
fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def hidden_class(page):
    return page.evaluate(
        "document.querySelector('.site-header').classList.contains('nav--hidden')")


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
    page.set_default_timeout(15000)

    print("A: fx=rich (default desktop) — hide on down, return on up:")
    resp = page.goto(BASE, wait_until="domcontentloaded")
    check("about 200", resp.status == 200, str(resp.status))
    fx = page.evaluate("document.documentElement.getAttribute('data-fx')")
    check("gate active (lite or rich)", fx in ("lite", "rich"), fx or "missing")
    check("header visible at top", not hidden_class(page))
    page.evaluate("window.scrollTo(0, 800)")
    page.wait_for_timeout(400)
    check("hidden after scroll-down", hidden_class(page))
    page.evaluate("window.scrollTo(0, 400)")
    page.wait_for_timeout(400)
    check("returned after scroll-up", not hidden_class(page))
    page.evaluate("window.scrollTo(0, 1200)")
    page.wait_for_timeout(400)
    check("hidden again deep-down", hidden_class(page))
    page.evaluate("document.querySelector('.site-header__brand').focus()")
    page.wait_for_timeout(200)
    check("focus into header returns it", not hidden_class(page))

    print("B: fx=none — never hides:")
    page.emulate_media(reduced_motion="reduce")
    page.goto(BASE, wait_until="domcontentloaded")
    fx = page.evaluate("document.documentElement.getAttribute('data-fx')")
    check("gate reports none", fx == "none", fx or "missing")
    page.evaluate("window.scrollTo(0, 800)")
    page.wait_for_timeout(400)
    check("header never hides under none", not hidden_class(page))
    page.emulate_media(reduced_motion="no-preference")

    print("C: JS blocked — header stays visible (D-MOTION-SAFE):")
    ctx2 = browser.new_context(viewport={"width": 1280, "height": 900}, java_script_enabled=False)
    page2 = ctx2.new_page()
    page2.goto(BASE, wait_until="domcontentloaded")
    check("header rendered without JS",
          page2.locator(".site-header").is_visible())

    browser.close()

print("R27-E3-G1-VERDICT:", "PASS" if not fails else f"FAIL {fails}")
