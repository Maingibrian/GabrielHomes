"""r20 AUDITOR — H3 E3 real-browser audit (mobile bento carousel).

Four Playwright contexts against the live dev server:
  A. mobile 390x844 default      -> rail computed styles, snap, scrollable,
                                    bento-shift NOT live, keyboard walk
  B. mobile 390x844 reduced      -> grow animation stopped (animation-name none)
  C. mobile 390x844 JS blocked   -> rail still flex + scrollable (D-MOTION-SAFE)
  D. desktop 1280x900 rich+fine  -> is-live set, grid NOT a rail (desktop
                                    shape-shift untouched by the mobile block)

Prints H3-E3-VERDICT: PASS only if every assertion holds.
Screenshots -> LOOP/audit-screens/r20-e3-h3-*.png (+ owner copy in download/).
"""
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/"
REPO = Path(__file__).resolve().parents[1]
SHOTS = REPO / "LOOP" / "audit-screens"
DL = Path("/home/z/my-project/download/preview-screenshots")
SHOTS.mkdir(parents=True, exist_ok=True)
DL.mkdir(parents=True, exist_ok=True)

fails = []
checks = 0


def check(name, cond, detail=""):
    global checks
    checks += 1
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


RICH_SHIM = """
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
"""

with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])

    # ---------- A. mobile default ----------
    print("A. mobile 390x844 — default capabilities")
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    page.set_default_timeout(8000)
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_selector(".bento-grid--shift", timeout=8000)
    page.wait_for_timeout(700)
    grid = page.locator(".bento-grid--shift")
    check("shift grid present", grid.count() == 1)
    disp = grid.evaluate("el => getComputedStyle(el).display")
    ovx = grid.evaluate("el => getComputedStyle(el).overflowX")
    snap = grid.evaluate("el => getComputedStyle(el).scrollSnapType")
    pad = grid.evaluate("el => getComputedStyle(el).scrollPaddingInline")
    check("display: flex rail", disp == "flex", f"display={disp}")
    check("overflow-x auto", ovx == "auto", f"overflowX={ovx}")
    check("scroll-snap-type x mandatory", "mandatory" in snap, f"snapType={snap}")
    check("scroll-padding-inline set", pad not in ("", "0px", "normal"), f"pad={pad}")
    card = grid.locator(".bento-card").first
    align = card.evaluate("el => getComputedStyle(el).scrollSnapAlign")
    check("first card snap-align center", align == "center", f"align={align}")
    # card 2 is a regular card (82%); card 1 is the spotlight (88%)
    basis_reg = grid.locator(".bento-card").nth(1).evaluate(
        "el => getComputedStyle(el).flexBasis")
    basis_spot = card.evaluate("el => getComputedStyle(el).flexBasis")
    check("regular card flex-basis 82%", basis_reg == "82%", f"basis={basis_reg}")
    check("spotlight card flex-basis 88%", basis_spot == "88%",
          f"basis={basis_spot}")
    n_cards = grid.locator(".bento-card").count()
    check("rail has cards", n_cards >= 3, f"cards={n_cards}")
    sw, cw = grid.evaluate("el => [el.scrollWidth, el.clientWidth]")
    check("rail horizontally scrollable", sw > cw, f"scrollWidth={sw} clientWidth={cw}")
    live = grid.evaluate("el => el.classList.contains('is-live')")
    check("bento-shift NOT live on mobile", not live, "is-live must not exist <1021px")
    grow = card.evaluate("el => getComputedStyle(el).animationName")
    print(f"  (info) default animationName on cards: {grow!r}")

    # keyboard walk: Tab from the top, record rail scrollLeft per focused card
    page.evaluate("document.body.focus()")
    page.keyboard.press("Tab")
    focused, sls = [], []
    for _ in range(24):
        tag, cls = page.evaluate(
            "[document.activeElement.tagName,"
            " document.activeElement.className]")
        if "bento-card" in (cls or ""):
            sl = grid.evaluate("el => el.scrollLeft")
            focused.append(cls.split()[1] if len(cls.split()) > 1 else cls)
            sls.append(sl)
        if len(focused) >= n_cards:
            break
        page.keyboard.press("Tab")
    check("keyboard reaches cards", len(focused) >= 3, f"focused={len(focused)}")
    check("keyboard walk scrolls the rail", max(sls, default=0) > 100,
          f"scrollLeft walk 0->{max(sls, default=0)}")
    page.screenshot(path=str(SHOTS / "r20-e3-h3-mobile-rail.png"))
    shutil.copy(SHOTS / "r20-e3-h3-mobile-rail.png",
                DL / "r20-mobile-bento-audit.jpg")
    ctx.close()

    # ---------- B. mobile reduced motion ----------
    print("B. mobile 390x844 — prefers-reduced-motion: reduce")
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(8000)
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_selector(".bento-grid--shift", timeout=8000)
    page.wait_for_timeout(700)
    grid = page.locator(".bento-grid--shift")
    card = grid.locator(".bento-card").first
    anim = card.evaluate("el => getComputedStyle(el).animationName")
    check("grow animation stopped under reduce", anim == "none", f"animation={anim!r}")
    trans = card.evaluate("el => getComputedStyle(el).transitionDuration")
    check("card transitions zeroed", all(float(t.split("s")[0]) == 0
          for t in trans.split(", ")), f"transitionDuration={trans}")
    page.screenshot(path=str(SHOTS / "r20-e3-h3-mobile-reduced.png"))
    ctx.close()

    # ---------- C. mobile JS blocked ----------
    print("C. mobile 390x844 — all JS aborted (D-MOTION-SAFE)")
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    page.set_default_timeout(8000)
    page.route("**/*.js*", lambda route: route.abort())
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_selector(".bento-grid--shift", timeout=8000)
    page.wait_for_timeout(700)
    grid = page.locator(".bento-grid--shift")
    disp = grid.evaluate("el => getComputedStyle(el).display")
    sw, cw = grid.evaluate("el => [el.scrollWidth, el.clientWidth]")
    vis = grid.evaluate("el => { const r = el.getBoundingClientRect();"
                        " return r.width > 0 && r.height > 0; }")
    opac = grid.locator(".bento-card").first.evaluate(
        "el => getComputedStyle(el).opacity")
    check("rail still flex with JS blocked", disp == "flex", f"display={disp}")
    check("rail still scrollable with JS blocked", sw > cw,
          f"scrollWidth={sw} clientWidth={cw}")
    check("rail visible with JS blocked", vis and float(opac) == 1,
          f"visible={vis} opacity={opac}")
    ctx.close()

    # ---------- D. desktop rich + fine pointer ----------
    print("D. desktop 1280x900 — rich + fine shim (desktop must be untouched)")
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(8000)
    page.add_init_script(RICH_SHIM)
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_selector(".bento-grid--shift", timeout=8000)
    page.wait_for_timeout(700)
    page.wait_for_timeout(900)
    grid = page.locator(".bento-grid--shift")
    fx = page.evaluate("document.documentElement.getAttribute('data-fx')")
    disp = grid.evaluate("el => getComputedStyle(el).display")
    live = grid.evaluate("el => el.classList.contains('is-live')")
    check("gate grades rich with shim", fx == "rich", f"data-fx={fx!r}")
    check("desktop shape-shift live", live, "is-live must exist on desktop")
    check("desktop grid is NOT a flex rail", disp == "grid", f"display={disp}")
    page.screenshot(path=str(SHOTS / "r20-e3-h3-desktop-untouched.png"))
    ctx.close()

    browser.close()

print(f"\n{checks - len(fails)}/{checks} checks passed")
if fails:
    print("FAILED: " + ", ".join(fails))
    print("H3-E3-VERDICT: FAIL")
    raise SystemExit(1)
print("H3-E3-VERDICT: PASS")
