"""r65 E3 — palm-field parallax, live-browser proof (owner round 13).

Legs:
  RICH  desktop 1600x900, gate lands rich -> the ::before traveler's
        translateY drifts monotonically -140px -> +140px across the
        band's cover traversal, matching the expected linear position
  NONE  reduced-motion -> data-fx="none" -> no animation, stills
  NOJS  JS blocked -> no data-fx at all -> stills

Prints R65-E3-VERDICT: PASS only if every check holds.
Screenshots -> LOOP/audit-screens/r65-e3-palm-*.png (+ owner copies in
download/preview-screenshots/).
"""
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000/"
REPO = Path(__file__).resolve().parents[1]
SHOTS = REPO / "LOOP" / "audit-screens"
DL = Path("/home/z/my-project/download/preview-screenshots")

fails = []
checks = 0


def ok(cond, label, detail=""):
    global checks
    checks += 1
    print(f"[{'PASS' if cond else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(label)


def scroll_to(page, y):
    page.evaluate(
        """(y) => {
            if (window.__lenis && typeof window.__lenis.scrollTo === 'function') {
                window.__lenis.scrollTo(y, { immediate: true });
            } else {
                // base.css sets html{scroll-behavior:smooth} and fx=none
                // builds no Lenis, so a plain window.scrollTo(0, y) ANIMATES
                // — jump instantly or the shot fires mid-flight (found by
                // the r65 pixel check, check 3)
                window.scrollTo({ top: y, behavior: "instant" });
            }
        }""",
        y,
    )
    page.wait_for_timeout(300)  # let a scroll-driven frame tick land


def field_state(page):
    return page.evaluate(
        """() => {
            const cs = getComputedStyle(
                document.querySelector('.home-market'), '::before');
            return {transform: cs.transform, name: cs.animationName,
                    state: cs.animationPlayState};
        }"""
    )


def parse_ty(matrix):
    if not matrix or matrix == "none":
        return None
    return float(matrix.rsplit(",", 1)[1].strip().rstrip(")"))


def snap(page, stem):
    for d in (SHOTS, DL):
        d.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(d / f"{stem}.png"))
    print(f"      shot: {stem}.png")


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- Leg 1: RICH ----------
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(1400)  # entrance settles (r34 lesson)
    fx = page.get_attribute("html", "data-fx")
    ok(fx == "rich", "RICH: fx gate lands rich", f"data-fx={fx}")

    geo = page.evaluate(
        """() => {
            const el = document.querySelector('.home-market');
            const r = el.getBoundingClientRect();
            return {top: r.top + window.scrollY, height: r.height,
                    vh: window.innerHeight};
        }"""
    )
    subj_top = geo["top"] - 170          # ::before box: section +/- 170px
    subj_h = geo["height"] + 340
    ok(geo["height"] > geo["vh"],
       "RICH: the band is taller than the viewport",
       f"band {geo['height']:.0f}px vs vh {geo['vh']:.0f}px")

    # cover progress p for a scrollY: p = (vh - (subj_top - scrollY)) / (subj_h + vh)
    tys = []
    for i, frac in enumerate((0.15, 0.50, 0.76)):
        target = subj_top - geo["vh"] + frac * (subj_h + geo["vh"])
        scroll_to(page, target)
        st = field_state(page)
        ty = parse_ty(st["transform"])
        tys.append(ty)
        expected = -140 + 280 * frac
        ok(st["name"] == "palm-field-parallax",
           f"RICH probe {i+1}: animation attached", st["name"])
        ok(ty is not None and abs(ty - expected) <= 35,
           f"RICH probe {i+1}: translateY near the linear expectation",
           f"got {ty if ty is None else round(ty,1)}px, expected ~{expected:.0f}px")
        snap(page, f"r65-e3-palm-rich-{i+1}")
    ok(all(tys[i] is not None and tys[i+1] is not None and tys[i] < tys[i+1]
           for i in range(len(tys) - 1)),
       "RICH: the drift advances monotonically with scroll",
       f"translateY path: {[None if t is None else round(t,1) for t in tys]}")

    # ---------- Leg 2: NONE (reduced motion) ----------
    ctx2 = browser.new_context(viewport={"width": 1600, "height": 900},
                               reduced_motion="reduce")
    page2 = ctx2.new_page()
    page2.goto(BASE, wait_until="networkidle")
    page2.wait_for_timeout(800)
    fx2 = page2.get_attribute("html", "data-fx")
    ok(fx2 == "none", "NONE: reduced motion sets fx none", f"data-fx={fx2}")
    st2 = field_state(page2)
    ok(st2["name"] == "none" and st2["transform"] == "none",
       "NONE: no parallax animation, stills stand",
       f"name={st2['name']} transform={st2['transform']}")
    scroll_to(page2, subj_top - geo["vh"] + 0.76 * (subj_h + geo["vh"]))
    st2b = field_state(page2)
    ok(st2b["transform"] == "none",
       "NONE: mid-band the field never moves", f"transform={st2b['transform']}")
    snap(page2, "r65-e3-palm-none")

    # ---------- Leg 3: NOJS ----------
    ctx3 = browser.new_context(viewport={"width": 1600, "height": 900},
                               java_script_enabled=False)
    page3 = ctx3.new_page()
    page3.goto(BASE, wait_until="load")
    page3.wait_for_timeout(800)
    # page JS is disabled -> reach the band natively with the mouse wheel
    for _ in range(6):
        page3.mouse.wheel(0, 800)
        page3.wait_for_timeout(120)
    page3.wait_for_timeout(500)
    # no attribute at all -> CSS gate can never match (fails closed)
    has_fx = page3.evaluate(
        "() => document.documentElement.hasAttribute('data-fx')")
    ok(has_fx is False,
       "NOJS: the gate never ran (no data-fx attribute)", f"hasAttribute={has_fx}")
    snap(page3, "r65-e3-palm-nojs")

    browser.close()

print()
if fails:
    print(f"R65-E3-VERDICT: FAIL ({len(fails)} of {checks} checks failed)")
    raise SystemExit(1)
print(f"R65-E3-VERDICT: PASS ({checks} checks)")
