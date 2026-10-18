#!/usr/bin/env python3
"""Gabriel Homes — site-wide accessibility / contrast audit.

For every page (public + agent dashboard + owner dashboard + branded admin):
  - WCAG 2.1 contrast of EVERY visible text node (alpha-compositing aware,
    resolves color-mix/opacity, flags text-over-image for manual review)
  - unlabeled form controls, images without alt, text < 12px,
    links/buttons with no accessible name
  - mobile (390px): horizontal overflow
  - full-page screenshots (desktop 1440 + mobile 390) -> docs/a11y/
Output: docs/a11y/findings.json + docs/a11y/summary.txt
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = Path("/home/z/my-project/gabriel_homes/docs/a11y")
(OUT / "shots").mkdir(parents=True, exist_ok=True)

PUBLIC = [
    ("home", "/"),
    ("properties", "/properties/"),
    ("for-sale", "/property-for-sale/"),
    ("for-rent", "/property-for-rent/"),
    ("loc-page", "/property-for-sale/nyali/"),
    ("agents", "/agents/"),
    ("about", "/about/"),
    ("services", "/services/"),
    ("contact", "/contact/"),
    ("privacy", "/privacy/"),
    ("terms", "/terms/"),
    ("styleguide", "/styleguide/"),
    ("404", "/this-page-does-not-exist/"),
]
LISTINGS = ["/listing/acreage-parcel-in-watamu-80/", "/listing/3br-bungalow-in-nyali-77/"]
AGENT_PAGES = [("dashboard-agent", "/dashboard/"), ("inquiries-agent", "/dashboard/inquiries/")]
OWNER_PAGES = [
    ("dashboard-owner", "/dashboard/"),
    ("owner-all-listings", "/dashboard/all-listings/"),
    ("owner-agencies", "/dashboard/agencies/"),
    ("owner-import", "/dashboard/import/"),
]
ADMIN_PAGES = [("admin-dash", "/admin/"), ("admin-listings", "/admin/listings/property/")]

WALKER = r"""
() => {
  function parseColor(c) {
    if (!c || c === 'transparent') return [0,0,0,0];
    c = c.trim();
    let m = c.match(/^rgba?\(([^)]+)\)$/i);
    if (m) {
      const p = m[1].split(/\s*,\s*|\s+/).map(Number);
      if (p.length >= 3) return [p[0],p[1],p[2], p.length>3?p[3]:1].map((v,i)=> i<3 ? v/255 : v);
    }
    m = c.match(/^color\(\s*srgb\s+([^)]+)\)$/i);
    if (m) {
      const p = m[1].split(/\s+/).map(Number).filter(v=>!isNaN(v));
      if (p.length >= 3) return [p[0],p[1],p[2], p.length>3?p[3]:1];
    }
    m = c.match(/^#([0-9a-f]{3,8})$/i);
    if (m) {
      let h = m[1];
      if (h.length===3) h = h.split('').map(x=>x+x).join('');
      if (h.length===6) return [0,1,2,3,4,5].map(i=>parseInt(h.slice(i*2,i*2+2),16)/255).concat([1]).slice(0,4).map((v,i)=> i<3?v:v);
      if (h.length===8) return [0,1,2].map(i=>parseInt(h.slice(i*2,i*2+2),16)/255).concat([parseInt(h.slice(6,8),16)/255]);
    }
    return null;
  }
  function over(fg, bg) {
    const a = fg[3];
    return [fg[0]*a + bg[0]*(1-a), fg[1]*a + bg[1]*(1-a), fg[2]*a + bg[2]*(1-a), 1];
  }
  function lum([r,g,b]) {
    const f = v => v <= 0.04045 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
    return 0.2126*f(r) + 0.7152*f(g) + 0.0722*f(b);
  }
  function ratio(l1, l2) {
    const [a,b] = l1 > l2 ? [l1,l2] : [l2,l1];
    return (a+0.05)/(b+0.05);
  }
  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const node = walker.currentNode;
    const text = (node.textContent||'').replace(/\s+/g,' ').trim();
    if (!text) continue;
    const el = node.parentElement;
    if (!el || seen.has(el)) continue;
    seen.add(el);
    const cs = getComputedStyle(el);
    if (cs.display==='none'||cs.visibility==='hidden'||+cs.opacity===0) continue;
    if (el.offsetWidth===0 && el.offsetHeight===0 && cs.position!=='fixed') continue;
    // effective foreground
    let fg = parseColor(cs.color) || [0,0,0,1];
    let alpha = +cs.opacity;
    // walk ancestors: find solid bg, composite translucent layers
    let bg = null, bgParts = [], imageBg = false, p = el, hops = 0;
    while (p && hops < 20) {
      const pcs = getComputedStyle(p);
      if (pcs.backgroundImage && pcs.backgroundImage !== 'none') imageBg = true;
      const c = parseColor(pcs.backgroundColor);
      if (c && c[3] > 0) {
        bgParts.push(c);
        if (c[3] >= 0.999) break;
      }
      alpha *= +pcs.opacity || 1;
      p = p.parentElement; hops++;
    }
    if (fg[3] < 1 || alpha < 1) fg = [fg[0],fg[1],fg[2], fg[3]*alpha];
    if (!bgParts.length) bgParts.push([1,1,1,1]);
    bg = bgParts.reverse().reduce((acc,c)=> over(c, acc), [1,1,1,1]);
    const eff = over(fg, bg);
    const fs = parseFloat(cs.fontSize), fw = parseInt(cs.fontWeight)||400;
    const large = fs >= 24 || (fs >= 18.66 && fw >= 700);
    const need = large ? 3.0 : 4.5;
    const r = ratio(lum(eff), lum(bg));
    const rec = {
      t: text.slice(0,70), tag: el.tagName.toLowerCase(),
      cls: (el.className && typeof el.className==='string') ? el.className.slice(0,80) : '',
      fs: Math.round(fs*10)/10, fg: cs.color, bg: cs.backgroundColor,
      ratio: Math.round(r*100)/100, need, imageBg,
      tiny: fs < 12, imgPath: imageBg
    };
    if (r < need) out.push({kind:'contrast', ...rec});
    else if (fs < 12) out.push({kind:'tiny', ...rec});
  }
  // form controls without labels
  document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]), select, textarea').forEach(el => {
    if (!el.offsetParent && el.type !== 'hidden') return;
    const id = el.id, hasLabel = id && document.querySelector(`label[for="${id}"]`);
    const named = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || hasLabel;
    if (!named) out.push({kind:'unlabeled', t:(el.placeholder||el.name||el.type||''), tag:el.tagName.toLowerCase(),
      cls:(typeof el.className==='string'?el.className.slice(0,80):'')});
  });
  // images without alt
  document.querySelectorAll('img').forEach(img => {
    if (!img.offsetParent) return;
    if (!img.getAttribute('alt') && !img.getAttribute('aria-label') && !img.getAttribute('aria-hidden'))
      out.push({kind:'img-alt', t:(img.src||'').split('/').slice(-2).join('/').slice(0,70),
        cls:(typeof img.className==='string'?img.className.slice(0,60):'')});
  });
  // links/buttons with no accessible name
  document.querySelectorAll('a,button').forEach(el => {
    if (!el.offsetParent) return;
    const name = (el.getAttribute('aria-label')||el.textContent||'').trim();
    if (!name) out.push({kind:'no-name', tag:el.tagName.toLowerCase(),
      cls:(typeof el.className==='string'?el.className.slice(0,60):''),
      t:(el.getAttribute('href')||'').slice(0,50)});
  });
  return out;
}
"""

def dedup(rows):
    seen, outv = set(), []
    for r in rows:
        k = (r.get('kind'), r.get('t'), r.get('cls','')[:40], r.get('ratio'), r.get('tag'))
        if k in seen: continue
        seen.add(k); outv.append(r)
    return outv

def audit_page(page, name, url, findings):
    try:
        page.goto(url, wait_until="load", timeout=25000)
    except Exception as e:
        findings[name] = [{"kind": "nav-error", "t": str(e)[:120]}]
        return False
    page.wait_for_timeout(700)
    for w, tag in ((1440, "d"), (390, "m")):
        page.set_viewport_size({"width": w, "height": 900})
        page.wait_for_timeout(350)
        try:
            rows = page.evaluate(WALKER)
            rows = dedup(rows)
            if w == 390:
                ov = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                if ov > 2:
                    rows.append({"kind": "h-overflow", "t": f"{ov}px horizontal overflow", "tag": "html"})
            findings.setdefault(name, []).extend([{**r, "vp": tag} for r in rows])
        except Exception as e:
            findings.setdefault(name, []).append({"kind": "eval-error", "t": str(e)[:120]})
        try:
            page.screenshot(path=str(OUT / "shots" / f"{name}-{tag}.png"), full_page=(w==1440))
        except Exception:
            pass
    return True

def login(page, url, user, pw):
    page.goto(url, wait_until="load", timeout=25000)
    for sel_u, sel_p in (("#id_username", "#id_password"), ("[name=login]", "[name=password]"), ("[name=username]", "[name=password]")):
        if page.locator(sel_u).count():
            page.fill(sel_u, user); page.fill(sel_p, pw)
            page.keyboard.press("Enter"); page.wait_for_timeout(1200)
            return "login" not in page.url and "password" not in page.url
    return False

def main():
    findings = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width":1440,"height":900})
        page = ctx.new_page()
        errors = []
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text[:100]}") if m.type=="error" else None)

        for name, path in PUBLIC:
            audit_page(page, name, BASE + path, findings)
        for path in LISTINGS:
            audit_page(page, f"listing-{path.strip('/').split('-')[-1]}", BASE + path, findings)

        # delivery page on :3000 (the download-cards page)
        try:
            d = browser.new_context(viewport={"width":1440,"height":900}).new_page()
            audit_page(d, "delivery-3000", "http://127.0.0.1:3000/", findings)
        except Exception as e:
            findings["delivery-3000"] = [{"kind":"nav-error","t":str(e)[:120]}]

        # agent dashboard
        if login(page, BASE + "/accounts/login/?next=/dashboard/", "hello@gabrielhomes.co.ke", "gabriel2026"):
            for name, path in AGENT_PAGES:
                audit_page(page, name, BASE + path, findings)
        else:
            findings["dashboard-agent"] = [{"kind":"login-failed","t":"agent login failed"}]

        # owner dashboard + branded admin
        if login(page, BASE + "/admin/login/?next=/admin/", "admin@gabrielhomes.co.ke", "GH-7TPn-scN1-3tne-Hu2K"):
            page.goto(BASE + "/dashboard/", wait_until="load"); page.wait_for_timeout(600)
            for name, path in OWNER_PAGES:
                audit_page(page, name, BASE + path, findings)
            for name, path in ADMIN_PAGES:
                audit_page(page, name, BASE + path, findings)
        else:
            # try demo password as fallback
            if login(page, BASE + "/admin/login/?next=/admin/", "admin@gabrielhomes.co.ke", "gabriel2026"):
                for name, path in OWNER_PAGES + ADMIN_PAGES:
                    audit_page(page, name, BASE + path, findings)
            else:
                findings["dashboard-owner"] = [{"kind":"login-failed","t":"owner login failed"}]
        if errors:
            findings["_console"] = errors[:20]
        browser.close()

    (OUT / "findings.json").write_text(json.dumps(findings, indent=1))
    # summary
    lines, total = [], 0
    for name in sorted(findings):
        rows = findings[name]
        kinds = {}
        for r in rows:
            k = r["kind"] if isinstance(r, dict) else "console"
            kinds[k] = kinds.get(k, 0) + 1
        n = sum(v for k, v in kinds.items() if k != "tiny")
        total += n
        lines.append(f"{name:22s} " + "  ".join(f"{k}:{v}" for k, v in sorted(kinds.items())))
    (OUT / "summary.txt").write_text("\n".join(lines) + f"\n\nTOTAL significant findings: {total}")
    print("\n".join(lines))
    print(f"\nTOTAL significant findings: {total}")

if __name__ == "__main__":
    sys.exit(main())
