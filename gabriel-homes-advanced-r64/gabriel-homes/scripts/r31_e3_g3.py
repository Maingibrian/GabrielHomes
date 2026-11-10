"""r31 E3 — G3 scroll-linked reveals, live browser evidence.

Natural-scroll methodology: a real user's scroll is incremental, so every
sample advances the page in small steps with a rAF settle between them
(same-task reads of a scroll timeline are stale; r15 lesson in-script).

Proves, on Chromium (view() supported, fx=lite in headless):
  home   — nearby-card opacity: below-fold ~0, rises with entry, 1 inside;
  services — svc-row rise; media clip-path inset shrinks with entry;
  about  — story collage figure rise;
  reduced-motion (fx=none) — everything stays visible (kill rules);
  JS blocked — content fully visible (D-MOTION-SAFE);
  zero console/page errors.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
failures, errors = [], []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def scroll_to_bottom_offset(page, sel, index, bottom_offset, steps=24):
    """Naturally scroll until the element's bottom edge sits `bottom_offset`
    px from the viewport bottom (positive = below the fold)."""
    page.eval_on_selector_all(
        sel,
        """(els, a) => {
            window.__g3target = els[a.i];
            window.__g3goal = () => {
                const el = window.__g3target;
                const y = el.getBoundingClientRect().top + window.scrollY;
                return y + el.getBoundingClientRect().height - window.innerHeight - a.off;
            };
            window.__g3cur = window.scrollY;
        }""", {"i": index, "off": bottom_offset})
    page.evaluate("""async () => {
        const goal = window.__g3goal();
        const start = window.scrollY;
        const steps = 24;
        for (let s = 1; s <= steps; s++) {
            window.scrollTo({top: start + (goal - start) * s / steps, behavior: "instant"});
            await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
        }
    }""")
    page.wait_for_timeout(120)


def sample(page, sel, index=0):
    return page.eval_on_selector_all(
        sel,
        """(els, i) => {
            const el = els[i];
            const r = el.getBoundingClientRect();
            return {op: parseFloat(getComputedStyle(el).opacity),
                    clip: getComputedStyle(el).clipPath,
                    top: Math.round(r.top), h: Math.round(r.height)};
        }""", index)


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---- home: nearby-card rise under natural scrolling ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("console", lambda m: errors.append("home: " + m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append("home: " + str(e)))
    page.goto(BASE + "/", wait_until="networkidle")
    fx = page.eval_on_selector("html", "e => e.getAttribute('data-fx')")
    check("home fx gate ran", fx in ("lite", "rich"), f"fx={fx}")

    scroll_to_bottom_offset(page, ".nearby-card[data-reveal]", 0, 900)   # far below
    s0 = sample(page, ".nearby-card[data-reveal]")
    # entry % = 1 - off/h; put the card at ~30% entry for a true mid-state
    h = s0["h"] or 600
    scroll_to_bottom_offset(page, ".nearby-card[data-reveal]", 0, round(h * 0.7))
    s1 = sample(page, ".nearby-card[data-reveal]")
    scroll_to_bottom_offset(page, ".nearby-card[data-reveal]", 0, -400)  # well inside
    s2 = sample(page, ".nearby-card[data-reveal]")
    check("below the fold: hidden from-state", s0["op"] < 0.15, f"op={s0['op']}")
    check("mid-entry: part-way revealed", 0.15 < s1["op"] < 0.9, f"op={s1['op']}")
    check("inside viewport: fully revealed", s2["op"] > 0.95, f"op={s2['op']}")
    check("reveal is scroll-linked (rises)", s0["op"] < s1["op"] <= s2["op"],
          f"{s0['op']} -> {s1['op']} -> {s2['op']}")
    page.screenshot(path="/home/z/my-project/gabriel-homes/LOOP/audit-screens/r31-g3-nearby-mid.png")
    ctx.close()

    # ---- services: row rise + media clip ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("console", lambda m: errors.append("services: " + m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append("services: " + str(e)))
    page.goto(BASE + "/services/", wait_until="networkidle")
    scroll_to_bottom_offset(page, ".svc-row[data-reveal]", 1, 700)
    r0 = sample(page, ".svc-row[data-reveal]", 1)
    scroll_to_bottom_offset(page, ".svc-row[data-reveal]", 1, -350)
    r1 = sample(page, ".svc-row[data-reveal]", 1)
    check("svc-row rise is scroll-linked", r0["op"] < 0.2 and r1["op"] > 0.85,
          f"{r0['op']} -> {r1['op']}")
    scroll_to_bottom_offset(page, ".svc-row__media", 1, 700)
    c0 = sample(page, ".svc-row__media", 1)
    scroll_to_bottom_offset(page, ".svc-row__media", 1, -350)
    c1 = sample(page, ".svc-row__media", 1)
    check("svc media clip shrinks with entry",
          c0["clip"].startswith("inset") and c1["clip"].startswith("inset")
          and c0["clip"] != c1["clip"], f"{c0['clip'][:28]} -> {c1['clip'][:28]}")
    page.screenshot(path="/home/z/my-project/gabriel-homes/LOOP/audit-screens/r31-g3-services.png")
    ctx.close()

    # ---- about: story collage figure ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("console", lambda m: errors.append("about: " + m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append("about: " + str(e)))
    page.goto(BASE + "/about/", wait_until="networkidle")
    anim_kind = page.eval_on_selector(
        ".about-story__figure[data-reveal]",
        """e => {
            const a = e.getAnimations().find(x => (x.animationName || '').startsWith('g3-'));
            return a ? (a.timeline ? a.timeline.constructor.name : 'no-timeline') : 'no-anim';
        }""")
    scroll_to_bottom_offset(page, ".about-story__figure[data-reveal]", 0, 700)
    a0 = sample(page, ".about-story__figure[data-reveal]")
    scroll_to_bottom_offset(page, ".about-story__figure[data-reveal]", 0, -350)
    a1 = sample(page, ".about-story__figure[data-reveal]")
    check("about figure carries a ViewTimeline animation", anim_kind == "ViewTimeline",
          anim_kind)
    check("about figure reveal is scroll-linked (or in first viewport)",
          (a0["op"] < 0.2 and a1["op"] > 0.85) or (a0["op"] == 1 and a1["op"] == 1),
          f"{a0['op']} -> {a1['op']}")
    ctx.close()

    # ---- reduced motion => fx=none => kill rules => always visible ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    page = ctx.new_page()
    page.goto(BASE + "/", wait_until="networkidle")
    nfx = page.eval_on_selector("html", "e => e.getAttribute('data-fx')")
    scroll_to_bottom_offset(page, ".nearby-card[data-reveal]", 0, 900)
    n0 = sample(page, ".nearby-card[data-reveal]")
    scroll_to_bottom_offset(page, ".nearby-card[data-reveal]", 0, -400)
    n1 = sample(page, ".nearby-card[data-reveal]")
    check("fx=none under reduced motion", nfx == "none", f"data-fx={nfx}")
    check("fx=none: nearby-card always visible", n0["op"] == 1 and n1["op"] == 1,
          f"{n0['op']}, {n1['op']}")
    ctx.close()

    # ---- JS blocked: no motion-ready, nothing hidden ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, java_script_enabled=False)
    page = ctx.new_page()
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(400)
    j0 = page.eval_on_selector(".nearby-card", "e => getComputedStyle(e).opacity")
    check("JS blocked: nearby-card fully visible", float(j0) == 1, f"opacity={j0}")
    ctx.close()

    browser.close()

check("zero console/page errors", len(errors) == 0, "; ".join(errors[:3]) if errors else "clean")

print()
if failures:
    print(f"r31 G3 E3: {len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("r31 G3 E3: ALL PASS")
