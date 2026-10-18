#!/usr/bin/env python3
"""r12 probe — find the elements causing horizontal overflow on owner pages.

Logs in as the owner, loads each dashboard surface at 390px, and reports the
elements whose right edge (or scroll width) exceeds the viewport.
"""
import json
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
PAGES = ["owner-all-listings", "owner-agencies", "owner-import", "dashboard-owner"]
URLS = {
    "owner-all-listings": "/dashboard/listings/",
    "owner-agencies": "/dashboard/agencies/",
    "owner-import": "/dashboard/import/",
    "dashboard-owner": "/dashboard/",
}

JS = """
() => {
  const vw = document.documentElement.clientWidth;
  const bad = [];
  document.querySelectorAll('*').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1 || el.scrollWidth > el.clientWidth + 1) {
      // skip html/body and elements whose parents already overflow
      bad.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className && el.className.baseVal !== undefined
               ? el.className.baseVal : el.className || '').toString().slice(0, 60),
        right: Math.round(r.right),
        sw: el.scrollWidth, cw: el.clientWidth,
        w: Math.round(r.width),
      });
    }
  });
  return {vw, doc: document.documentElement.scrollWidth, bad: bad.slice(0, 14)};
}
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page()
    # owner login (Django admin login form: fill + Enter, like a11y_audit.py)
    pg.goto(BASE + "/admin/login/", wait_until="load")
    pg.fill("#id_username", "admin@gabrielhomes.co.ke")
    pg.fill("#id_password", "gabriel2026")
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(1500)
    out = {}
    for name in PAGES:
        pg.goto(BASE + URLS[name])
        pg.wait_for_load_state("networkidle")
        out[name] = pg.evaluate(JS)
    b.close()

print(json.dumps(out, indent=1))
