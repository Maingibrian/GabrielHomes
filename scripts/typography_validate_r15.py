#!/usr/bin/env python3
"""Post-fix validation for the r15 typography pass.

Verifies the CHANGED things only:
  V1. mono elements now compute POSITIVE tracking (0.02em) — probe the
      previously-negative selectors across pages
  V2. .story__body p measure <= 75 real chars (was 84-98)
  V3. .prose > * measure <= 75 real chars (was ~100)
  V4. zoom 200% (real viewport) + WCAG 1.4.12 text-spacing still pass
  V5. preload links present in served HTML
  V6. fonts still load; screenshots for the visual diff
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/home/z/my-project/scripts/design-audit/typography-2026-10-18")
BASE = "http://127.0.0.1:3011"

MONO_CHECK = """
async () => {
  const sels = ['.value-card__tag', '.principle-card__index', '.listing-card__facts',
                '.breadcrumbs', '.results-header__count', '.detail-header__verified',
                '.facts-bar__label', '.enquiry-form__title', '.prose__updated'];
  const out = [];
  for (const s of sels) {
    const el = document.querySelector(s);
    if (!el) continue;
    const cs = getComputedStyle(el);
    out.push({sel: s, ls: cs.letterSpacing, size: cs.fontSize,
              mono: cs.fontFamily.includes('Mono')});
  }
  return out;
}
"""

MEASURE = """
async (sel) => {
  const p = document.querySelector(sel);
  if (!p) return null;
  const range = document.createRange();
  range.selectNodeContents(p);
  const rects = [...range.getClientRects()].filter(r => r.width > 10);
  const lines = new Set(rects.map(r => Math.round(r.top))).size;
  const cs = getComputedStyle(p);
  return {width: Math.round(p.getBoundingClientRect().width),
          cpl: lines ? Math.round(p.textContent.trim().length / lines) : 0,
          lh: cs.lineHeight, size: cs.fontSize};
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    res = {"mono": {}, "measure": {}, "zoom": {}, "spacing": {}, "preload": None}

    for name, path in (("home", "/"), ("listing", "/properties/"),
                       ("agents", "/agents/"), ("about", "/about/")):
        page.goto(BASE + path, wait_until="networkidle")
        res["mono"][name] = page.evaluate(MONO_CHECK)

    page.goto(BASE + "/", wait_until="networkidle")
    res["measure"]["story"] = page.evaluate(MEASURE, ".story__body p")
    page.goto(BASE + "/about/", wait_until="networkidle")
    res["measure"]["prose"] = page.evaluate(MEASURE, ".prose > p")
    res["preload"] = page.evaluate(
        "() => [...document.querySelectorAll('link[rel=preload]')].map(l => l.href.split('/').pop())")
    page.screenshot(path=str(OUT / "after-about-desktop.png"))

    # zoom + text-spacing regression on home
    page.goto(BASE + "/", wait_until="networkidle")
    ctx2 = browser.new_context(viewport={"width": 720, "height": 450})
    pg2 = ctx2.new_page()
    pg2.goto(BASE + "/", wait_until="networkidle")
    pg2.wait_for_timeout(400)
    res["zoom"]["home720"] = pg2.evaluate(
        "() => ({overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1})")
    ctx2.close()
    res["spacing"]["home"] = page.evaluate("""
      async () => {
        const st = document.createElement('style');
        st.textContent = '* { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; }';
        document.head.appendChild(st);
        await new Promise(r => setTimeout(r, 250));
        const de = document.documentElement;
        const o = de.scrollWidth > de.clientWidth + 1;
        st.remove();
        return {overflow: o};
      }""")

    # fonts still load + after screenshots
    page.goto(BASE + "/", wait_until="networkidle")
    res["fonts"] = page.evaluate(
        "async () => { await document.fonts.ready; return {Geist: document.fonts.check('16px Geist'), Fraunces: document.fonts.check('16px Fraunces'), Mono: document.fonts.check('16px \"Geist Mono\"')}; }")
    page.screenshot(path=str(OUT / "after-home-desktop.png"))
    page.goto(BASE + "/agents/", wait_until="networkidle")
    page.screenshot(path=str(OUT / "after-agents-desktop.png"))
    mctx = browser.new_context(viewport={"width": 390, "height": 844})
    mp = mctx.new_page()
    mp.goto(BASE + "/", wait_until="networkidle")
    mp.screenshot(path=str(OUT / "after-home-mobile.png"))
    browser.close()

(OUT / "validation.json").write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=1))
