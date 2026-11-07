"""r37 E3 — H2 T2 lift: the hero's five 3-dimensions proven live.

Evidence-only (no shipped code touched) — upgrades H2's T1 evidence to a
T2 claim on D1 (one-gesture + preload contract), D2 (crafted renders,
eyeballed screenshots), D4 (LCP bytes + first-view byte accounting on
the wire), D5 (keyboard path through the hero), D6 (mobile 390 legs).
The already-4 dimensions (D3 motion, D7 resilience, D8 tests) keep
their r33/r34 audit evidence; this pack adds what was missing.

Legs (home page, live Chromium):
  R   1280x900 rich spoof — video handover, mask headline, ONE gesture,
      LCP preload with fetchpriority=high;
  L   1280x900 natural lite — video hidden (0 B), slide-1 is the visual,
      LCP image bytes measured, full first-view byte accounting printed,
      real keyboard walk: skip link first, Buy/Rent segment flips on
      Enter, form action follows;
  M   390x844 mobile natural — hamburger, stacked pill, no horizontal
      overflow, split headline;
  MR  390x844 mobile rich spoof — video handover fires (the M2 gate is
      pointer-independent by contract);
  RM  1280x900 reduced-motion — h1 plain and visible, video never loads.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
failures = []


def check(leg, name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {leg:<3} {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        failures.append(f"{leg}: {name}")


def watch(page):
    page.on("console", lambda m: failures.append(f"console.error: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: failures.append(f"pageerror: {e}"))


def track(page):
    stats = {"video": 0, "lcp": 0, "css": 0, "js": 0, "font": 0,
             "img": 0, "other": 0, "lcp_seen": False}

    def on_response(resp):
        url = resp.url
        try:
            cl = int(resp.headers.get("content-length") or 0)
        except ValueError:
            cl = 0
        if "hero-loop.mp4" in url:
            stats["video"] += cl
        elif "hero-slide-1.webp" in url:
            stats["lcp"] += cl
            stats["lcp_seen"] = True
        elif url.split("?")[0].endswith(".css"):
            stats["css"] += cl
        elif url.split("?")[0].endswith(".js") or ".mjs" in url:
            stats["js"] += cl
        elif url.split("?")[0].endswith((".woff2", ".woff", ".ttf")):
            stats["font"] += cl
        elif url.split("?")[0].endswith((".webp", ".jpg", ".jpeg", ".png", ".svg", ".avif")):
            stats["img"] += cl
        else:
            stats["other"] += cl
    page.on("response", on_response)
    return stats


RICH_SPOOF = """
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
"""

HEADLINE = "[data-hero-headline]"

with sync_playwright() as pw:
    browser = pw.chromium.launch()

    # ---- Leg R: desktop rich — the full centrepiece -----------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    ctx.add_init_script(RICH_SPOOF)
    page = ctx.new_page()
    watch(page)
    stats_r = track(page)
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(700)
    check("R", "gate says rich",
          page.evaluate("document.documentElement.getAttribute('data-fx')") == "rich")
    check("R", "M2: video revealed, .is-video crossfade, playing",
          page.evaluate("!document.querySelector('[data-hero-video]').hidden")
          and page.evaluate(
              "document.querySelector('.hero__bg').classList.contains('is-video')")
          and page.evaluate("!document.querySelector('[data-hero-video]').paused"))
    check("R", "M2: poster present",
          "hero-poster" in (page.get_attribute("[data-hero-video]", "poster") or ""))
    words = page.evaluate("document.querySelectorAll('.hero__w-in').length")
    check("R", "M1: mask headline words staged", words >= 3, f"{words} words")
    submits = page.evaluate(
        "document.querySelectorAll('.hero button[type=submit]').length")
    other_anchors = page.evaluate(
        "document.querySelectorAll('.hero a:not(.hv2-scroll)').length")
    check("R", "D1: ONE gesture — a single submit CTA, no competing anchors",
          submits == 1 and other_anchors == 0,
          f"submits={submits}, other anchors={other_anchors}")
    check("R", "D1: stats row stays gone (no [data-count] in hero)",
          page.evaluate(
              "document.querySelectorAll('.hero [data-count]').length") == 0)
    pre = page.eval_on_selector(
        "head link[rel=preload][as=image]",
        "el => ({href: el.getAttribute('href'), fp: el.getAttribute('fetchpriority')})")
    check("R", "D1: LCP preloaded with fetchpriority=high",
          pre["href"].split("?")[0].endswith("hero-slide-1.webp")
          and pre["fp"] == "high",
          f"{pre['href']} fp={pre['fp']}")
    page.mouse.wheel(0, 400)
    page.wait_for_timeout(300)
    page.evaluate("window.__lenis.scrollTo(0)")
    page.wait_for_timeout(900)
    page.screenshot(path="LOOP/audit-screens/r37-h2-rich-1280.png")
    ctx.close()

    # ---- Leg L: desktop lite — budget, LCP, keyboard path -----------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    watch(page)
    stats_l = track(page)
    page.goto(BASE + "/", wait_until="networkidle")
    check("L", "natural headless stays lite (or richer is never forced)",
          page.evaluate("document.documentElement.getAttribute('data-fx')") in
          ("lite", "rich"))
    check("L", "M2: video hidden; zero video bytes",
          page.evaluate("document.querySelector('[data-hero-video]').hidden") is True
          and stats_l["video"] == 0, f"{stats_l['video']} B")
    slide_op = page.eval_on_selector(
        ".hero__slide", "el => getComputedStyle(el).opacity")
    check("L", "slide stack is the visual (slide-1 not faded out)",
          slide_op != "0", f"opacity={slide_op}")
    check("L", "LCP image actually fetched (preload honoured)",
          stats_l["lcp_seen"] and stats_l["lcp"] > 0, f"{stats_l['lcp']} B")
    total = (stats_l["css"] + stats_l["js"] + stats_l["font"] + stats_l["img"]
             + stats_l["video"] + stats_l["other"])
    print(f"      [L] first-view wire accounting (networkidle, no scroll):")
    print(f"          css {stats_l['css']} B · js {stats_l['js']} B · fonts "
          f"{stats_l['font']} B · images {stats_l['img']} B (LCP "
          f"{stats_l['lcp']} B) · video {stats_l['video']} B · other "
          f"{stats_l['other']} B · TOTAL {total} B")
    # Keyboard walk: skip link first, segment reachable, Enter flips it.
    page.keyboard.press("Tab")
    first = page.evaluate(
        "document.activeElement.className + '|' + document.activeElement.textContent.trim()")
    check("L", "D5: first focusable is the skip link",
          "skip" in first.lower(), first[:60])
    focused_seg = False
    for _ in range(14):
        page.keyboard.press("Tab")
        if page.evaluate(
                "!!document.activeElement.closest('[data-search-bar]')"
                " && document.activeElement.hasAttribute('data-segment')"):
            focused_seg = True
            break
    check("L", "D5: Buy/Rent segment reachable by keyboard",
          focused_seg)
    if page.evaluate(
            "document.activeElement.getAttribute('data-segment')") != "rent":
        page.keyboard.press("Tab")  # walk landed on Buy — one more to Rent
    check("L", "D5: Rent button is the focused segment",
          page.evaluate(
              "document.activeElement.getAttribute('data-segment')") == "rent")
    page.keyboard.press("Enter")
    page.wait_for_timeout(150)
    rent_active = page.eval_on_selector(
        "[data-segment='rent']", "el => el.classList.contains('is-active')")
    hidden_val = page.evaluate(
        "document.querySelector('#hero-search-form input[name=listing_type]').value")
    action = page.get_attribute("#hero-search-form", "action")
    check("L", "D5: Enter flips the segment + hidden input + action URL",
          rent_active and hidden_val == "rent"
          and action.endswith("-for-rent/"),
          f"rent_active={rent_active}, hidden={hidden_val}, action={action}")
    ctx.close()

    # ---- Leg M: mobile 390 natural — D6 craft ------------------------------
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True)
    page = ctx.new_page()
    watch(page)
    stats_m = track(page)
    page.goto(BASE + "/", wait_until="networkidle")
    check("M", "video hidden on mobile-lite (no bytes)",
          page.evaluate("document.querySelector('[data-hero-video]').hidden") is True
          and stats_m["video"] == 0)
    check("M", "hamburger menu present and visible",
          page.eval_on_selector(
              "[data-mobile-menu-open]",
              "el => el.getBoundingClientRect().width > 0"))
    check("M", "Buy/Rent segment survives the stack",
          page.eval_on_selector(
              "[data-search-bar] [data-segment='sale']",
              "el => el.getBoundingClientRect().width > 0"))
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - window.innerWidth")
    check("M", "D6: no horizontal overflow at 390px",
          overflow <= 1, f"{overflow}px overflow")
    check("M", "M1: headline splits on mobile too",
          page.evaluate("document.querySelectorAll('.hero__w').length") >= 2)
    page.wait_for_timeout(1200)  # let the hv2-rise entrance settle (r34 lesson)
    page.screenshot(path="LOOP/audit-screens/r37-h2-mobile-390.png")
    ctx.close()

    # ---- Leg MR: mobile 390 rich — the pointer-independent handover --------
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True)
    ctx.add_init_script(RICH_SPOOF)
    page = ctx.new_page()
    watch(page)
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(1300)
    check("MR", "tier stays rich on the phone (spoofed cores)",
          page.evaluate("document.documentElement.getAttribute('data-fx')") == "rich")
    check("MR", "M2: video handover fires on touch (pointer-independent)",
          page.evaluate("!document.querySelector('[data-hero-video]').hidden")
          and page.evaluate(
              "document.querySelector('.hero__bg').classList.contains('is-video')"))
    page.screenshot(path="LOOP/audit-screens/r37-h2-mobile-rich-390.png")
    ctx.close()

    # ---- Leg RM: reduced motion — parity -----------------------------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              reduced_motion="reduce")
    page = ctx.new_page()
    watch(page)
    stats_rm = track(page)
    page.goto(BASE + "/", wait_until="networkidle")
    check("RM", "fx=none: h1 plain and fully visible",
          page.evaluate("document.querySelectorAll('.hero__w').length") == 0
          and "properly" in page.inner_text(HEADLINE).lower())
    check("RM", "fx=none: video never a byte",
          page.evaluate("document.querySelector('[data-hero-video]').hidden") is True
          and stats_rm["video"] == 0)
    ctx.close()
    browser.close()

print()
if failures:
    print("r37 H2 T2 E3: FAILURES:", failures)
    sys.exit(1)
print("r37 H2 T2 E3: ALL PASS")
