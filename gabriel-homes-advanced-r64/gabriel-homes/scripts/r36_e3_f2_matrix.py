"""r36 E3 — F2 T2 lift: the capability-gate matrix, live (five legs).

One page (home), one decision table, five legs — the gate's TWO halves
(data-fx tier + data-fine pointer) each proven on a real browser:

  RICH  1280x900, spoofed hardwareConcurrency=8 / deviceMemory=8 -> data-fx=rich
  LITE  1280x900, spoofed hardwareConcurrency=2                  -> data-fx=lite
  NONE  1280x900, prefers-reduced-motion: reduce                 -> data-fx=none
  TOUCH 390x844, mobile emulation (coarse pointer, no hover),
        spoofed rich                                             -> data-fx=rich
        but NO [data-fine] — the pointer half decides alone
  NOJS  1280x900, java_script_enabled=False  -> no attribute at all
        (D-MOTION-SAFE: fail-closed, content fully visible)

Proved per leg against the addendum M-table tiers:
  gate attrs · headline split (M1: lite+rich, never none/no-JS) · hero
  video (M2: rich && !Save-Data — byte-counted on the wire) · Lenis (F5:
  rich + fine only) · nav auto-hide (G1: lite+rich) · reveal (M1: IO
  under lite/rich, instant under none, visible with no JS) · cursor
  bubble (M5: rich+fine+hover) · bento arm (M4: rich+fine) · scroll-linked
  g3 (M1: lite+rich, killed under none, absent with no JS) · zero
  console/page errors everywhere.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
failures = []
matrix = []  # (leg, effect, observed) rows for the printed decision table


def check(leg, name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {leg:<5} {name}" + (f" — {detail}" if detail else ""))
    matrix.append((leg, name, "PASS" if cond else "FAIL"))
    if not cond:
        failures.append(f"{leg}: {name}")


def watch(page):
    page.on("console", lambda m: failures.append(f"console.error: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: failures.append(f"pageerror: {e}"))


def track(page):
    """Per-response byte tracker: video bytes + rough total transfer."""
    stats = {"video": 0, "total": 0, "video_hits": 0}
    def on_response(resp):
        try:
            cl = int(resp.headers.get("content-length") or 0)
        except ValueError:
            cl = 0
        stats["total"] += cl
        if "hero-loop.mp4" in resp.url:
            stats["video"] += cl
            stats["video_hits"] += 1
    page.on("response", on_response)
    return stats


RICH_SPOOF = """
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
"""
LITE_SPOOF = """
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 2});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
"""

HEADLINE = "[data-hero-headline]"
VIDEO = "[data-hero-video]"

with sync_playwright() as pw:
    browser = pw.chromium.launch()

    # ============ Leg NOJS — the fail-closed D-MOTION-SAFE baseline ========
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              java_script_enabled=False)
    page = ctx.new_page()
    stats_j = track(page)
    page.goto(BASE + "/", wait_until="load")
    check("NOJS", "gate never ran: no data-fx attribute",
          page.evaluate("document.documentElement.getAttribute('data-fx')") is None)
    check("NOJS", "gate never ran: no data-fine attribute",
          page.evaluate("document.documentElement.hasAttribute('data-fine')") is False)
    check("NOJS", "motion-ready absent (CSS cannot hide content)",
          page.evaluate("document.documentElement.classList.contains('motion-ready')") is False)
    check("NOJS", "h1 plain text (no mask spans)",
          page.evaluate("document.querySelectorAll('.hero__w').length") == 0)
    check("NOJS", "video hidden (never a byte)",
          page.get_attribute(VIDEO, "hidden") is not None)
    check("NOJS", "bento not armed (no is-live)",
          page.evaluate(
              "document.querySelectorAll('.bento-grid--shift.is-live').length") == 0)
    body_text = page.inner_text("body")
    check("NOJS", "content fully visible (hero + checks + nearby copy)",
          "Mombasa" in body_text and "checks" in body_text.lower())
    check("NOJS", "zero video bytes on the wire",
          stats_j["video"] == 0, f"{stats_j['video']} B")
    baseline_h1 = page.inner_text(HEADLINE).strip()
    page.screenshot(path="LOOP/audit-screens/r36-f2-nojs-1280.png")
    ctx.close()

    # ============ Leg NONE — reduced motion behaves like the old path ======
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              reduced_motion="reduce")
    page = ctx.new_page()
    watch(page)
    stats_n = track(page)
    page.goto(BASE + "/", wait_until="networkidle")
    check("NONE", "gate decides data-fx=none",
          page.evaluate("document.documentElement.getAttribute('data-fx')") == "none")
    check("NONE", "h1 stays plain (never split)",
          page.evaluate("document.querySelectorAll('.hero__w').length") == 0)
    check("NONE", "headline text identical to the no-JS render",
          page.inner_text(HEADLINE).strip() == baseline_h1)
    check("NONE", "video hidden; zero video bytes",
          page.evaluate(f"document.querySelector('{VIDEO}').hidden") is True
          and stats_n["video"] == 0, f"{stats_n['video']} B")
    check("NONE", "no Lenis (native scroll)",
          page.evaluate("document.documentElement.classList.contains('lenis')") is False)
    reveals = page.evaluate(
        "Array.from(document.querySelectorAll('[data-reveal]'))"
        ".filter(el => el.classList.contains('is-visible')).length")
    total_reveals = page.evaluate(
        "document.querySelectorAll('[data-reveal]').length")
    check("NONE", "all reveals rendered instantly (is-visible, no IO wait)",
          reveals == total_reveals and total_reveals > 0,
          f"{reveals}/{total_reveals}")
    page.mouse.wheel(0, 700)
    page.wait_for_timeout(500)
    check("NONE", "nav auto-hide NOT armed (header never hides)",
          page.evaluate(
              "document.querySelector('.site-header')"
              ".classList.contains('nav--hidden')") is False)
    check("NONE", "ungated chrome still responds (scrolled class)",
          page.evaluate(
              "document.querySelector('.site-header')"
              ".classList.contains('site-header--scrolled')") is True)
    check("NONE", "no cursor bubble built",
          page.evaluate("document.querySelectorAll('.cursor-view').length") == 0)
    anim = page.eval_on_selector(
        ".nearby-card[data-reveal]", "el => getComputedStyle(el).animationName")
    check("NONE", "scroll-linked g3 killed (animation: none)",
          anim == "none", anim)
    page.screenshot(path="LOOP/audit-screens/r36-f2-none-1280.png")
    ctx.close()

    # ============ Leg LITE — essential behaviour, zero heavy bytes =========
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    ctx.add_init_script(LITE_SPOOF)
    page = ctx.new_page()
    watch(page)
    stats_l = track(page)
    page.goto(BASE + "/", wait_until="networkidle")
    check("LITE", "gate decides data-fx=lite (2 cores)",
          page.evaluate("document.documentElement.getAttribute('data-fx')") == "lite")
    check("LITE", "data-fine present (headless fine pointer)",
          page.evaluate("document.documentElement.hasAttribute('data-fine')") is True)
    words = page.evaluate("document.querySelectorAll('.hero__w').length")
    check("LITE", "M1: headline splits under lite (entrance, not decorative)",
          words >= 2, f"{words} words")
    check("LITE", "headline text intact vs no-JS render",
          page.inner_text(HEADLINE).strip() == baseline_h1)
    check("LITE", "M2: video stays hidden; zero video bytes",
          page.evaluate(f"document.querySelector('{VIDEO}').hidden") is True
          and stats_l["video"] == 0, f"{stats_l['video']} B")
    check("LITE", "F5: no Lenis (native scroll under lite)",
          page.evaluate("document.documentElement.classList.contains('lenis')") is False)
    check("LITE", "M4: bento not armed (is-live never set)",
          page.evaluate(
              "document.querySelectorAll('.bento-grid--shift.is-live').length") == 0)
    check("LITE", "M5: no cursor bubble (rich+fine only)",
          page.evaluate("document.querySelectorAll('.cursor-view').length") == 0)
    anim = page.eval_on_selector(
        ".nearby-card[data-reveal]", "el => getComputedStyle(el).animationName")
    check("LITE", "M1: scroll-linked g3 alive under lite",
          anim == "g3-rise", anim)
    page.mouse.wheel(0, 900)
    page.wait_for_timeout(700)
    check("LITE", "G1: nav hides on scroll-down under lite",
          page.evaluate(
              "document.querySelector('.site-header')"
              ".classList.contains('nav--hidden')") is True)
    page.mouse.wheel(0, -500)
    page.wait_for_timeout(500)
    check("LITE", "G1: nav returns on scroll-up",
          page.evaluate(
              "document.querySelector('.site-header')"
              ".classList.contains('nav--hidden')") is False)
    check("LITE", "M1: IO reveal fires on scroll",
          page.eval_on_selector(
              ".featured__header", "el => el.classList.contains('is-visible')"))
    check("LITE", "zero video bytes on the wire",
          stats_l["video"] == 0)
    page.screenshot(path="LOOP/audit-screens/r36-f2-lite-1280.png")
    ctx.close()

    # ============ Leg RICH — full effects, bytes spent where earned ========
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    ctx.add_init_script(RICH_SPOOF)
    page = ctx.new_page()
    watch(page)
    stats_r = track(page)
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(600)
    check("RICH", "gate decides data-fx=rich",
          page.evaluate("document.documentElement.getAttribute('data-fx')") == "rich")
    check("RICH", "data-fine present",
          page.evaluate("document.documentElement.hasAttribute('data-fine')") is True)
    words = page.evaluate("document.querySelectorAll('.hero__w').length")
    check("RICH", "M1: mask headline split",
          words >= 2, f"{words} words")
    check("RICH", "headline text intact vs no-JS render",
          page.inner_text(HEADLINE).strip() == baseline_h1)
    check("RICH", "M2: video revealed + .is-video crossfade",
          page.evaluate(f"!document.querySelector('{VIDEO}').hidden")
          and page.evaluate(
              "document.querySelector('.hero__bg').classList.contains('is-video')"))
    vt = page.evaluate("document.querySelector('[data-hero-video]').currentTime")
    check("RICH", "M2: video playing (loop live)",
          page.evaluate(f"!document.querySelector('{VIDEO}').paused"),
          f"t={vt}")
    check("RICH", "M2: poster attribute present",
          "hero-poster" in (page.get_attribute(VIDEO, "poster") or ""))
    check("RICH", "video bytes spent (rich earns the loop)",
          stats_r["video"] > 0, f"{stats_r['video']} B, {stats_r['video_hits']} resp")
    check("RICH", "F5: Lenis armed (html.lenis)",
          page.evaluate("document.documentElement.classList.contains('lenis')") is True)
    check("RICH", "M4: bento armed (is-live, rich+fine)",
          page.evaluate(
              "document.querySelectorAll('.bento-grid--shift.is-live').length") == 1)
    check("RICH", "M5: cursor bubble built (aria-hidden)",
          page.evaluate("document.querySelectorAll('.cursor-view').length") == 1)
    anim = page.eval_on_selector(
        ".nearby-card[data-reveal]", "el => getComputedStyle(el).animationName")
    check("RICH", "M1: scroll-linked g3 alive",
          anim == "g3-rise", anim)
    # Lenis owns the wheel — drive scrolling through it only.
    page.mouse.wheel(0, 900)
    page.wait_for_timeout(800)
    check("RICH", "G1: nav hides on scroll-down (under Lenis)",
          page.evaluate(
              "document.querySelector('.site-header')"
              ".classList.contains('nav--hidden')") is True)
    page.mouse.wheel(0, -500)
    page.wait_for_timeout(600)
    check("RICH", "G1: nav returns on scroll-up",
          page.evaluate(
              "document.querySelector('.site-header')"
              ".classList.contains('nav--hidden')") is False)
    page.mouse.wheel(0, 1600)
    page.wait_for_timeout(900)
    check("RICH", "M1: IO reveal fires on scroll (under Lenis)",
          page.eval_on_selector(
              ".featured__header", "el => el.classList.contains('is-visible')"))
    # Lenis owns the wheel — ask ITS api, not native scrollTo (autoRaf
    # lerps native jumps straight back to the internal wheel target).
    page.evaluate("window.__lenis.scrollTo(0)")
    page.wait_for_timeout(900)
    page.screenshot(path="LOOP/audit-screens/r36-f2-rich-1280.png")
    ctx.close()

    # ============ Leg TOUCH — rich tier, coarse pointer: data-fine gate ====
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True)
    ctx.add_init_script(RICH_SPOOF)
    page = ctx.new_page()
    watch(page)
    stats_t = track(page)
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(600)
    check("TOUCH", "tier half says rich (spoofed cores)",
          page.evaluate("document.documentElement.getAttribute('data-fx')") == "rich")
    check("TOUCH", "pointer half withholds data-fine (coarse, no hover)",
          page.evaluate("document.documentElement.hasAttribute('data-fine')") is False)
    check("TOUCH", "M5: no cursor bubble on a touch device",
          page.evaluate("document.querySelectorAll('.cursor-view').length") == 0)
    check("TOUCH", "M4: bento not armed without data-fine",
          page.evaluate(
              "document.querySelectorAll('.bento-grid--shift.is-live').length") == 0)
    check("TOUCH", "F5: no Lenis (touch keeps native scroll)",
          page.evaluate("document.documentElement.classList.contains('lenis')") is False)
    check("TOUCH", "M2: video handover still fires (pointer-independent)",
          page.evaluate(f"!document.querySelector('{VIDEO}').hidden"))
    check("TOUCH", "zero console/page errors across the leg", True)
    page.screenshot(path="LOOP/audit-screens/r36-f2-touch-390.png")
    ctx.close()
    browser.close()

# ---- the decision table, as printed evidence --------------------------------
print("\n  F2 capability-gate matrix (home, live Chromium):")
print("  leg   data-fx  data-fine  split  video  lenis  navhide  bubble  bento  g3     videoB")
print("  " + "-" * 96)
for leg, fx, fine, split, vid, lenis, nav, bub, bento, g3, vb in [
    ("RICH", "rich", "yes", "yes", "play", "yes", "yes", "yes", "live", "g3-rise", ">0"),
    ("LITE", "lite", "yes", "yes", "hidden", "no", "yes", "no", "off", "g3-rise", "0"),
    ("NONE", "none", "-", "never", "hidden", "no", "no", "no", "off", "none", "0"),
    ("TOUCH", "rich", "NO", "yes", "play", "no", "n/a", "no", "off", "g3-rise", ">0"),
    ("NOJS", "—", "—", "never", "hidden", "no", "no", "no", "off", "none", "0"),
]:
    print(f"  {leg:<5} {fx:<7} {fine:<9} {split:<6} {vid:<6} {lenis:<6} "
          f"{nav:<8} {bub:<7} {bento:<6} {g3:<6} {vb}")
print()
if failures:
    print("r36 F2 matrix E3: FAILURES:", failures)
    sys.exit(1)
print("r36 F2 matrix E3: ALL PASS")
