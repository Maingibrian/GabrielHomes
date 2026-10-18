#!/usr/bin/env python3
"""r13 spot-check: shape-shift on /agents/ (shared .bento-grid) + JS errors."""
import json
import sys

from playwright.sync_api import sync_playwright

OUT = "/home/z/my-project/download"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    cdp = page.context.new_cdp_session(page)
    cdp.send("Emulation.setEmulatedMedia", {"features": [
        {"name": "hover", "value": "hover"},
        {"name": "pointer", "value": "fine"},
        {"name": "prefers-reduced-motion", "value": "no-preference"},
    ]})

    page.goto("http://127.0.0.1:3011/agents/", wait_until="networkidle")
    page.locator(".bento-grid").scroll_into_view_if_needed()
    page.wait_for_timeout(1500)

    info = page.evaluate("""() => {
        const g = document.querySelector('.bento-grid');
        const cards = g.querySelectorAll('.bento-card');
        const c = cards[1];
        const r = c.getBoundingClientRect();
        return {ready: document.documentElement.classList.contains('bento-live-ready'),
                n: cards.length,
                hx: r.x + r.width / 2, hy: r.y + r.height / 2,
                w0: c.offsetWidth};
    }""")
    page.mouse.move(info["hx"], info["hy"], steps=5)
    page.wait_for_timeout(800)
    grown = page.evaluate("""() => {
        const g = document.querySelector('.bento-grid');
        const c = g.querySelectorAll('.bento-card')[1];
        return {grown: c.classList.contains('is-grown'),
                w1: c.offsetWidth,
                grownCount: g.querySelectorAll('.is-grown').length};
    }""")
    print("agents page:", json.dumps({**info, **grown}))
    page.screenshot(path=f"{OUT}/r13-agents-grown.png")
    ok = (info["ready"] and grown["grown"]
          and grown["w1"] > info["w0"] * 1.6
          and grown["grownCount"] == 1 and not errors)
    print("JS errors:", errors)
    browser.close()
    sys.exit(0 if ok else 1)
