"""r24 — E3 visual audit: owner mobile defects fixed + founder portrait.

A: home at 390x844 (the owner's exact viewport) — header at top, no
   stats row in the DOM, scroll cue hidden, marquee masked at the edges,
   search card radius = card radius, segment shrunk, submit stretched.
B: /about/ — the founder card shows the portrait (decoded, 60px circle).
Screenshots -> LOOP/audit-screens/r24-e3-*.png (+ owner copies in
download/preview-screenshots/).
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
REPO = Path(__file__).resolve().parents[1]
SHOTS = REPO / "LOOP" / "audit-screens"

fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=1, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.set_default_timeout(15000)

    # --- A: mobile home -----------------------------------------------------
    print("A: mobile home 390x844:")
    resp = page.goto(BASE + "/", wait_until="domcontentloaded")
    check("home 200", resp.status == 200, str(resp.status))
    page.wait_for_selector(".hero", timeout=10000)
    page.wait_for_timeout(2200)  # entrance animations settle

    probe = page.evaluate(
        """() => {
          const gs = (sel, prop) => {
            const e = document.querySelector(sel);
            return e ? getComputedStyle(e)[prop] : null;
          };
          const rect = sel => {
            const e = document.querySelector(sel);
            if (!e) return null;
            const r = e.getBoundingClientRect();
            return {t: Math.round(r.top), b: Math.round(r.bottom),
                    l: Math.round(r.left), r: Math.round(r.right)};
          };
          return {
            statsInDom: !!document.querySelector('.hero__stats'),
            scrollCueDisplay: gs('.hv2-scroll', 'display'),
            marqueeMask: gs('.hv2-marquee', 'maskImage') ||
                         gs('.hv2-marquee', 'webkitMaskImage'),
            cardRadius: gs('.search-bar', 'borderRadius'),
            segJustify: gs('.search-bar__segment', 'justifySelf'),
            submitJustify: gs('.search-bar__submit', 'justifySelf'),
            header: rect('.site-header'),
            hero: rect('.hero'),
            search: rect('.hero__search'),
            marquee: rect('.hv2-marquee'),
            docW: document.documentElement.scrollWidth,
            vw: innerWidth,
          };
        }""")
    check("stats row gone from DOM", probe["statsInDom"] is False)
    check("scroll cue hidden on mobile", probe["scrollCueDisplay"] == "none",
          probe["scrollCueDisplay"])
    check("marquee has edge mask", bool(probe["marqueeMask"]) and
          "linear-gradient" in probe["marqueeMask"])
    check("search card uses card radius",
          probe["cardRadius"] not in (None, "100px") and
          "px" in str(probe["cardRadius"]), probe["cardRadius"])
    check("segment shrunk to buttons", probe["segJustify"] == "start",
          probe["segJustify"])
    check("submit stretched", probe["submitJustify"] == "stretch",
          probe["submitJustify"])
    check("header at top of page", probe["header"] and probe["header"]["t"] == 0,
          str(probe["header"]))
    check("no horizontal overflow", probe["docW"] <= probe["vw"],
          f"{probe['docW']} vs {probe['vw']}")
    if probe["marquee"] and probe["search"]:
        gap = probe["marquee"]["t"] - probe["search"]["b"]
        check("search card inside hero, above marquee", 0 <= gap < 220,
              f"gap {gap}px")
    page.screenshot(path=str(SHOTS / "r24-e3-mobile-hero.png"))

    # --- B: founder portrait on /about/ -------------------------------------
    print("B: founder portrait on /about/:")
    resp = page.goto(BASE + "/about/", wait_until="domcontentloaded")
    check("about 200", resp.status == 200, str(resp.status))
    img = page.wait_for_selector("img.hv2-founder__photo", timeout=10000)
    # lazy image below the fold: scroll it into view and wait for decode
    img.scroll_into_view_if_needed()
    page.wait_for_function(
        """() => {
          const im = document.querySelector('img.hv2-founder__photo');
          return im && im.complete && im.naturalWidth > 0;
        }""", timeout=10000)
    info = page.evaluate(
        """() => {
          const im = document.querySelector('img.hv2-founder__photo');
          if (!im) return null;
          const r = im.getBoundingClientRect();
          return {w: Math.round(r.width), h: Math.round(r.height),
                  natural: im.naturalWidth, complete: im.complete,
                  alt: im.alt, radius: getComputedStyle(im).borderRadius};
        }""")
    check("portrait rendered", bool(info) and info["natural"] > 0,
          str(info))
    check("portrait is a 60px circle", info and info["w"] == 60 and
          info["h"] == 60 and info["radius"] == "50%", str(info))
    check("alt text present", info and "Gabriel Omulu" in info["alt"])
    check("monogram gone", page.evaluate(
        "!document.querySelector('.hv2-founder__mark')"))
    page.screenshot(path=str(SHOTS / "r24-e3-about-founder.png"))

    browser.close()

print()
if fails:
    print(f"R24-E3-VERDICT: FAIL — {len(fails)}: " + ", ".join(fails))
    raise SystemExit(1)
print("R24-E3-VERDICT: PASS")
