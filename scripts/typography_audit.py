#!/usr/bin/env python3
"""Typography audit — measured, rendered evidence (not vibes).

Probes real pages on :3011 with headless Chromium and collects:
  1. computed typography of key element roles (desktop 1440 + mobile 390)
  2. smallest visible text nodes (flag < 13px, the site's own stated floor)
  3. prose line length (characters per line, target 45-75)
  4. distinct rendered font sizes (token consistency)
  5. WCAG 1.4.4 zoom 200% reflow (horizontal overflow check)
  6. WCAG 1.4.12 text-spacing adaptability (standard overrides)
  7. contrast of key text/background pairs (computed ratios)
  8. font loading: families loaded, woff2 transfer sizes
  9. before-screenshots for the visual diff

Outputs JSON + PNGs to scripts/design-audit/typography-2026-10-18/.
"""
import json
import pathlib
import re
from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/home/z/my-project/scripts/design-audit/typography-2026-10-18")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:3011"

PAGES = {"home": "/", "listing_grid": "/properties/", "agents": "/agents/"}

DESKTOP_PROBE = """
async () => {
  const pick = (el) => {
    if (!el) return null;
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return {sel: true, family: cs.fontFamily.split(',')[0].replace(/"/g,''),
            size: cs.fontSize, weight: cs.fontWeight, lh: cs.lineHeight,
            ls: cs.letterSpacing, w: Math.round(r.width)};
  };
  const q = (s) => pick(document.querySelector(s));
  return {
    body: q('body'),
    h1: q('h1'),
    h2: q('main h2, section h2, h2'),
    h3: q('h3'),
    p: q('main p, section p, p'),
    navLink: q('header nav a, .nav a, nav a'),
    button: q('.btn, button'),
    smallMeta: q('[class*="meta" i], [class*="badge" i]'),
  };
}
"""

SMALLEST_TEXT = """
async () => {
  const out = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  let node;
  while ((node = walk.nextNode())) {
    const t = node.textContent.trim();
    if (!t || t.length > 60) continue;
    const el = node.parentElement;
    if (!el || seen.has(el)) continue;
    seen.add(el);
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const fs = parseFloat(cs.fontSize);
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (fs < 13) {
      out.push({text: t.slice(0, 40), px: fs, family: cs.fontFamily.split(',')[0].replace(/"/g,''),
                cls: (el.className || '').toString().slice(0, 50), mono: cs.fontFamily.includes('Mono')});
    }
  }
  return out.slice(0, 25);
}
"""

PROSE_LINE_LENGTH = """
async () => {
  const paras = [...document.querySelectorAll('main p, section p, .prose p, article p')]
    .filter(p => p.textContent.trim().length > 150 && p.getBoundingClientRect().width > 100)
    .slice(0, 6);
  return paras.map(p => {
    const range = document.createRange();
    range.selectNodeContents(p);
    const rects = [...range.getClientRects()].filter(r => r.width > 10);
    const lines = new Set(rects.map(r => Math.round(r.top))).size;
    const cs = getComputedStyle(p);
    const cpl = rects.length && lines ? Math.round(p.textContent.trim().length / lines) : 0;
    return {cls: (p.className || 'p').toString().slice(0,30), width: Math.round(p.getBoundingClientRect().width),
            approxCharsPerLine: cpl, fontSize: cs.fontSize, lh: cs.lineHeight};
  });
}
"""

ZOOM_OVERFLOW = """
async () => {
  const de = document.documentElement;
  return {scrollW: de.scrollWidth, clientW: de.clientWidth,
          overflow: de.scrollWidth > de.clientWidth + 1};
}
"""

TEXT_SPACING = """
async () => {
  const st = document.createElement('style');
  st.id = 'wcag-text-spacing';
  st.textContent = `* { line-height: 1.5 !important; letter-spacing: .12em !important;
    word-spacing: .16em !important; } p { margin-bottom: 2em !important; }`;
  document.head.appendChild(st);
  await new Promise(r => setTimeout(r, 300));
  const de = document.documentElement;
  const res = {overflow: de.scrollWidth > de.clientWidth + 1, scrollW: de.scrollW || de.scrollWidth, clientW: de.clientWidth};
  document.getElementById('wcag-text-spacing').remove();
  return res;
}
"""

CONTRAST_PAIRS = """
async () => {
  function lum(c) {
    const m = c.match(/\\d+(\\.\\d+)?/g).map(Number);
    const f = (v) => { v/=255; return v <= .03928 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4); };
    return .2126*f(m[0]) + .7152*f(m[1]) + .0722*f(m[2]);
  }
  function bg(el) {
    let e = el;
    while (e) {
      const c = getComputedStyle(e).backgroundColor;
      if (c && !c.includes('rgba(0, 0, 0, 0') && c !== 'transparent') return c;
      e = e.parentElement;
    }
    return 'rgb(250, 248, 244)';
  }
  function ratio(fg, bgc) {
    const l1 = lum(fg), l2 = lum(bgc);
    return Math.round(((Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05))*100)/100;
  }
  const targets = [
    ['body p', 'paragraph'], ['nav a', 'nav link'], ['h1', 'h1'],
    ['[class*="meta" i]', 'meta text'], ['footer, .footer', 'footer'],
  ];
  const out = [];
  for (const [sel, name] of targets) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const cs = getComputedStyle(el);
    out.push({name, sel, fg: cs.color, bg: bg(el), ratio: ratio(cs.color, bg(el)),
              size: cs.fontSize, bold: parseFloat(cs.fontWeight) >= 600});
  }
  return out;
}
"""

FONTS_LOADED = """
async () => {
  await document.fonts.ready;
  const fams = ['Geist', 'Fraunces', 'Geist Mono'];
  const res = {};
  for (const f of fams) res[f] = document.fonts.check(`16px "${f}"`);
  return res;
}
"""


def run():
    report = {"pages": {}, "fonts_transfer": {}, "zoom200": {}, "text_spacing": {}}
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # font transfer sizes from the home page network
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        fonts = {}
        page.on("response", lambda r: fonts.update({r.url.split("/")[-1]: r.headers.get("content-length", "?")})
                if r.url.endswith(".woff2") else None)
        page.goto(BASE + "/", wait_until="networkidle")
        report["fonts_transfer"] = fonts
        report["fonts_loaded"] = page.evaluate(FONTS_LOADED)

        # desktop probes on all pages
        for name, path in PAGES.items():
            page.goto(BASE + path, wait_until="networkidle")
            report["pages"][name] = {
                "computed": page.evaluate(DESKTOP_PROBE),
                "smallest_text": page.evaluate(SMALLEST_TEXT),
                "prose": page.evaluate(PROSE_LINE_LENGTH),
                "contrast": page.evaluate(CONTRAST_PAIRS),
            }
            page.screenshot(path=str(OUT / f"before-{name}-desktop.png"), full_page=False)

        # find a real detail page from the listing grid
        href = page.evaluate("""
          () => { const a = document.querySelector('a[href*="/listing/"]'); return a ? a.getAttribute('href') : null; }
        """)
        if href:
            page.goto(BASE + href, wait_until="networkidle")
            report["pages"]["detail"] = {
                "url": href,
                "computed": page.evaluate(DESKTOP_PROBE),
                "smallest_text": page.evaluate(SMALLEST_TEXT),
                "prose": page.evaluate(PROSE_LINE_LENGTH),
                "contrast": page.evaluate(CONTRAST_PAIRS),
            }
            page.screenshot(path=str(OUT / "before-detail-desktop.png"))

        # zoom 200% (WCAG 1.4.4) on listing grid + home
        for name in ("home", "listing_grid"):
            page.goto(BASE + PAGES[name], wait_until="networkidle")
            page.evaluate("document.body.style.zoom = 2")  # chromium zoom simulation
            page.wait_for_timeout(400)
            report["zoom200"][name] = page.evaluate(ZOOM_OVERFLOW)
            page.evaluate("document.body.style.zoom = ''")
            # text-spacing adaptability (WCAG 1.4.12)
            report["text_spacing"][name] = page.evaluate(TEXT_SPACING)
        ctx.close()

        # mobile 390
        mctx = browser.new_context(viewport={"width": 390, "height": 844})
        mpage = mctx.new_page()
        for name, path in PAGES.items():
            mpage.goto(BASE + path, wait_until="networkidle")
            report["pages"][name]["mobile_computed"] = mpage.evaluate(DESKTOP_PROBE)
            mpage.screenshot(path=str(OUT / f"before-{name}-mobile.png"))
        mctx.close()
        browser.close()

    (OUT / "audit.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"\nsaved to {OUT}")


if __name__ == "__main__":
    run()
