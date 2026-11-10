"""r33 E3 — H2.b hero motion slice, live browser evidence.

Proves, on Chromium (headless defaults to fx=lite — the video must stay
hidden there; a spoofed-rich context exercises the video hand-over):
  fx=lite (natural headless) — headline word-splits into .hero__w masks
             with staggered --d, h1's own hv2-rise handed over, text and
             em accent intact, mask animation live on the words, video
             stays hidden (lite never gets the 1.5MB loop);
  fx=rich (spoofed hardwareConcurrency/deviceMemory) — video becomes
             visible, .hero__bg.is-video set, slides hidden, poster
             attribute present, video.play() accepted;
  fx=none (reduced motion) — h1 stays PLAIN (no split at all —
             D-MOTION-SAFE), video never loads;
  JS blocked — h1 plain text only, no video activation;
  zero console/page errors.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
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

    # ---- Context 0: JS blocked — the plain-text baseline ------------------
    ctx_d = browser.new_context(viewport={"width": 1280, "height": 900},
                                java_script_enabled=False)
    page_d = ctx_d.new_page()
    page_d.goto(BASE + "/", wait_until="load")
    ctx_d_text = page_d.inner_text("[data-hero-headline]").strip()
    check("JS blocked: h1 is plain text (no spans)",
          page_d.evaluate("document.querySelectorAll('.hero__w').length") == 0)
    check("JS blocked: video hidden",
          page_d.get_attribute("[data-hero-video]", "hidden") is not None)
    ctx_d.close()

    # ---- Context A: natural headless (fx=lite) ----------------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    watch(page)
    page.goto(BASE + "/", wait_until="networkidle")
    check("fx gate runs (lite in headless)",
          page.evaluate("document.documentElement.getAttribute('data-fx')") in
          ("lite", "rich"), page.evaluate(
              "document.documentElement.getAttribute('data-fx')"))
    words = page.evaluate("document.querySelectorAll('.hero__w').length")
    check("headline word-splits into masks", words >= 2, f"{words} words")
    check("stagger indices increment (--d)",
          page.evaluate(
              "document.querySelector('.hero__w-in').style.getPropertyValue('--d')") == "0"
          and page.evaluate(
              "document.querySelectorAll('.hero__w-in')[1].style.getPropertyValue('--d')") == "1")
    check("h1's own hv2-rise handed over",
          page.evaluate("document.querySelector('[data-hero-headline]').classList.contains('hv2-rise')") is False)
    check("accent em survives the split",
          page.evaluate("document.querySelector('[data-hero-headline] em .hero__w-in') !== null"))
    plain = ctx_d_text
    check("headline text intact (matches the JS-blocked render)",
          page.inner_text("[data-hero-headline]").strip() == plain,
          page.inner_text("[data-hero-headline]")[:60])
    anim = page.evaluate(
        "getComputedStyle(document.querySelector('.hero__w-in')).animationName")
    check("mask animation live on the words", anim == "hero-mask-rise", anim)
    check("fx=lite: video stays hidden (never loads)",
          page.evaluate("document.querySelector('[data-hero-video]').hidden") is True
          and page.evaluate("document.querySelectorAll('.hero__bg.is-video').length") == 0)
    ctx.close()

    # ---- Context B: spoofed rich — the video hand-over --------------------
    ctx_b = browser.new_context(viewport={"width": 1280, "height": 900})
    ctx_b.add_init_script(SPOOF)
    page_b = ctx_b.new_page()
    watch(page_b)
    page_b.goto(BASE + "/", wait_until="networkidle")
    page_b.wait_for_timeout(400)
    check("spoofed device reaches fx=rich",
          page_b.evaluate("document.documentElement.getAttribute('data-fx')") == "rich")
    check("rich: video revealed + .is-video flip",
          page_b.evaluate("document.querySelector('[data-hero-video]').hidden") is False
          and page_b.evaluate("document.querySelector('.hero__bg').classList.contains('is-video')"))
    check("rich: slides yield to the loop",
          page_b.evaluate(
              "getComputedStyle(document.querySelector('.hero__slide')).opacity") == "0")
    vt = page_b.evaluate("document.querySelector('[data-hero-video]').currentTime")
    check("rich: video is playing",
          page_b.evaluate("!document.querySelector('[data-hero-video]').paused"),
          f"t={vt}")
    check("poster attribute present",
          "hero-poster" in page_b.get_attribute("[data-hero-video]", "poster"))
    page_b.wait_for_timeout(700)  # crossfade settles
    page_b.screenshot(path="LOOP/audit-screens/r33-h2b-hero-rich-1280.png")
    ctx_b.close()

    # ---- Context C: reduced motion (fx=none) — plain h1, no video ---------
    ctx_c = browser.new_context(viewport={"width": 1280, "height": 900},
                                reduced_motion="reduce")
    page_c = ctx_c.new_page()
    watch(page_c)
    page_c.goto(BASE + "/", wait_until="networkidle")
    check("fx=none: h1 stays plain (never split)",
          page_c.evaluate("document.querySelectorAll('.hero__w').length") == 0)
    check("fx=none: headline text fully visible",
          page_c.inner_text("[data-hero-headline]").strip() == ctx_d_text,
          page_c.inner_text("[data-hero-headline]")[:60])
    check("fx=none: video never activates",
          page_c.evaluate("document.querySelector('[data-hero-video]').hidden") is True)
    ctx_c.close()
    browser.close()

print()
if failures:
    print("r33 H2.b E3: FAILURES:", failures)
    sys.exit(1)
print("r33 H2.b E3: ALL PASS")
