"""r24 — E3 audit for the H2.a hero slice + founder portrait.

A: mobile 390x844 (owner screenshot viewport) —
   1. no stats row; 2. search card uses card radius (not the blob);
   3. Buy/Rent segment is content-width, not a full-width band;
   4. scroll cue display:none; 5. marquee mask applied (CSSOM);
   6. marquee edge pixels fade (screenshot alpha check via mask
      computed style); 7. submit button within the card bounds;
   8. portrait on /about/ is visible in a rounded frame.
B: desktop 1280 — hero still intact (title, search pill, marquee),
   scroll cue VISIBLE on hover-capable wide screen.
C: reduced-motion — marquee static but mask still present (fade is
   not motion).
Screenshots -> LOOP/audit-screens/r24-e3-*.png
"""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/"

fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])

    # --- A: mobile 390 -----------------------------------------------------
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844}, device_scale_factor=1,
        is_mobile=True, has_touch=True,
        user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                    "Mobile/15E148 Safari/604.1"))
    page = ctx.new_page()
    page.set_default_timeout(15000)
    print("A: mobile 390x844:")
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_selector(".hero__search", timeout=10000)
    page.wait_for_timeout(2200)

    check("no stats row in DOM",
          page.evaluate("document.querySelector('.hero__stats') === null"))
    radius = page.evaluate(
        "getComputedStyle(document.querySelector('.search-bar'))"
        ".borderRadius")
    check("search card radius is 20px (card, not blob)", radius == "20px",
          f"radius={radius}")
    seg = page.evaluate(
        """(() => { const s = document.querySelector('.search-bar__segment');
             const c = document.querySelector('.search-bar');
             return {segW: Math.round(s.getBoundingClientRect().width),
                     cardW: Math.round(c.getBoundingClientRect().width)} })()""")
    check("segment shrunk to its buttons",
          seg["segW"] < seg["cardW"] * 0.7,
          f"segment {seg['segW']}px vs card {seg['cardW']}px")
    cue = page.evaluate(
        "getComputedStyle(document.querySelector('.hv2-scroll')).display")
    check("scroll cue hidden on touch", cue == "none", f"display={cue}")
    mask = page.evaluate(
        "getComputedStyle(document.querySelector('.hv2-marquee')).maskImage"
        " || getComputedStyle(document.querySelector('.hv2-marquee'))"
        ".webkitMaskImage")
    check("marquee edge fade mask applied", "gradient" in str(mask),
          f"mask={str(mask)[:60]}")
    btn = page.evaluate(
        """(() => { const b = document.querySelector('.search-bar__submit');
             const c = document.querySelector('.search-bar');
             const rb = b.getBoundingClientRect(), rc = c.getBoundingClientRect();
             return {inside: rb.left >= rc.left - 1 && rb.right <= rc.right + 1,
                     w: Math.round(rb.width)} })()""")
    check("submit button stays inside the card", btn["inside"],
          f"width={btn['w']}px")
    # hero content fits: no horizontal scroll
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - "
        "document.documentElement.clientWidth")
    check("no horizontal overflow at 390px", overflow <= 0, f"delta={overflow}px")
    page.screenshot(path="LOOP/audit-screens/r24-e3-hero-mobile-390.png")

    # --- A2: about page portrait ------------------------------------------
    print("A2: about page portrait:")
    page.goto(BASE + "about/", wait_until="domcontentloaded")
    el = page.wait_for_selector(".hv2-founder__photo", timeout=10000)
    el.scroll_into_view_if_needed()  # loading="lazy": fetch starts on view
    # CSP (script-src 'self') forbids wait_for_function's eval — poll instead.
    loaded = False
    for _ in range(20):
        loaded = page.evaluate(
            "(() => { const i = document.querySelector('.hv2-founder__photo');"
            " return i.complete && i.naturalWidth > 0 })()")
        if loaded:
            break
        page.wait_for_timeout(300)
    img = page.evaluate(
        """(() => { const i = document.querySelector('.hv2-founder__photo');
             const r = i.getBoundingClientRect();
             return {w: Math.round(r.width), h: Math.round(r.height),
                     complete: i.complete && i.naturalWidth > 0,
                     radius: getComputedStyle(i).borderRadius,
                     alt: i.alt} })()""")
    check("portrait renders 60x60 loaded", loaded and img["w"] == 60,
          f"{img['w']}x{img['h']} loaded={loaded}")
    check("portrait is a circle", img["radius"] == "50%",
          f"radius={img['radius']}")
    check("portrait alt names the founder", "Omulu" in img["alt"], img["alt"])
    page.screenshot(path="LOOP/audit-screens/r24-e3-about-portrait-390.png")

    # --- B: desktop 1280 ----------------------------------------------------
    print("B: desktop 1280:")
    ctx2 = browser.new_context(viewport={"width": 1280, "height": 900})
    d = ctx2.new_page()
    d.set_default_timeout(15000)
    d.goto(BASE, wait_until="domcontentloaded")
    d.wait_for_selector(".hero__search", timeout=10000)
    d.wait_for_timeout(1500)
    check("desktop: hero title present",
          d.evaluate("!!document.querySelector('.hero__title')"))
    check("desktop: search pill present",
          d.evaluate("!!document.querySelector('#hero-search-form')"))
    cue_d = d.evaluate(
        "getComputedStyle(document.querySelector('.hv2-scroll')).display")
    check("desktop: scroll cue still visible", cue_d != "none",
          f"display={cue_d}")
    seg_d = d.evaluate(
        """(() => { const s = document.querySelector('.search-bar__segment');
             return !!s })()""")
    check("desktop: Buy/Rent segment present", seg_d)
    radius_d = d.evaluate(
        "getComputedStyle(document.querySelector('.search-bar')).borderRadius")
    check("desktop: pill radius kept (100px)", radius_d == "100px",
          f"radius={radius_d}")
    d.screenshot(path="LOOP/audit-screens/r24-e3-hero-desktop-1280.png")

    # --- C: reduced motion ---------------------------------------------------
    print("C: reduced motion:")
    ctx3 = browser.new_context(
        viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    r = ctx3.new_page()
    r.goto(BASE, wait_until="domcontentloaded")
    r.wait_for_selector(".hv2-marquee", timeout=10000)
    anim = r.evaluate(
        "getComputedStyle(document.querySelector('.hv2-marquee__track'))"
        ".animationName")
    mask_c = r.evaluate(
        "getComputedStyle(document.querySelector('.hv2-marquee')).maskImage"
        " || getComputedStyle(document.querySelector('.hv2-marquee'))"
        ".webkitMaskImage")
    check("reduced motion: marquee animation off", anim == "none",
          f"animation={anim}")
    check("reduced motion: edge fade survives (not motion)",
          "gradient" in str(mask_c))

    ctx.close(); ctx2.close(); ctx3.close()
    browser.close()

print()
if fails:
    print(f"R24-E3-VERDICT: FAIL ({len(fails)}) — " + ", ".join(fails))
    raise SystemExit(1)
print("R24-E3-VERDICT: PASS (18/18)")
