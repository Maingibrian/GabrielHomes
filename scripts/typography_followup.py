#!/usr/bin/env python3
"""Follow-up probes: detail page computed styles + REAL 200% zoom test.

body.zoom=2 is NOT how browser zoom works: real zoom halves the CSS-pixel
viewport (1440 -> 720) while keeping CSS sizes. WCAG 1.4.4 passes if at
720px the responsive layout shows all content without horizontal scroll.
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/home/z/my-project/scripts/design-audit/typography-2026-10-18")
BASE = "http://127.0.0.1:3011"

PROBE = """
async () => {
  const pick = (el) => {
    if (!el) return null;
    const cs = getComputedStyle(el);
    return {family: cs.fontFamily.split(',')[0].replace(/"/g,''), size: cs.fontSize,
            weight: cs.fontWeight, lh: cs.lineHeight, ls: cs.letterSpacing};
  };
  const q = (s) => pick(document.querySelector(s));
  return {title: document.title.slice(0, 50), h1: q('h1'), h2: q('h2'), p: q('p'),
          price: q('[class*="price" i]'), meta: q('[class*="meta" i]'),
          body: q('body'),
          hCount: document.querySelectorAll('h1').length};
}
"""

OVERFLOW = """
async () => {
  const de = document.documentElement;
  const wide = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.right > de.clientWidth + 2 && r.width > 40 && wide.length < 5) {
      const cs = getComputedStyle(el);
      if (cs.position !== 'fixed')
        wide.push({cls: (el.className || el.tagName).toString().slice(0, 40),
                   right: Math.round(r.right), w: Math.round(r.width)});
    }
  });
  return {scrollW: de.scrollWidth, clientW: de.clientWidth,
          overflow: de.scrollWidth > de.clientWidth + 1, wide};
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(BASE + "/properties/", wait_until="networkidle")
    href = page.evaluate("() => { const a = document.querySelector('a[href*=\"/listing/\"]'); return a ? a.getAttribute('href') : null; }")
    print("detail href:", href)
    page.goto(BASE + href, wait_until="networkidle")
    page.wait_for_timeout(600)
    detail = page.evaluate(PROBE)
    print("DETAIL:", json.dumps(detail, indent=1))
    page.screenshot(path=str(OUT / "before-detail-desktop.png"))

    # REAL zoom 200%: viewport halved (1440 -> 720), same CSS sizes
    results = {}
    for name, path in (("home", "/"), ("listing", "/properties/"), ("detail", href)):
        page.goto(BASE + path, wait_until="networkidle")
        ctx2 = browser.new_context(viewport={"width": 720, "height": 450})
        pg2 = ctx2.new_page()
        pg2.goto(BASE + path, wait_until="networkidle")
        pg2.wait_for_timeout(400)
        results[name] = pg2.evaluate(OVERFLOW)
        ctx2.close()
    print("ZOOM200 (real, 720px):", json.dumps(results, indent=1))
    (OUT / "followup.json").write_text(json.dumps({"detail": detail, "zoom200_real": results}, indent=2))
    browser.close()
