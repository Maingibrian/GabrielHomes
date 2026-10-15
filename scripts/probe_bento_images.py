"""Probe: do bento card background images actually render in a real browser?"""
import time

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = "/home/z/my-project/scripts/design-audit/home-2026-10-15"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    console_msgs = []
    page.on(
        "console",
        lambda m: console_msgs.append(f"[{m.type}] {m.text[:160]}"),
    )
    failed = []
    page.on(
        "requestfailed",
        lambda r: failed.append(f"{r.url[:110]} :: {r.failure}"),
    )

    page.goto(BASE + "/", wait_until="networkidle")
    grid = page.locator(".bento-grid").first
    grid.scroll_into_view_if_needed()
    page.wait_for_timeout(2500)  # generous time for bg decode + reveal

    info = page.evaluate(
        """() => {
            const cards = [...document.querySelectorAll('.bento-card__bg')];
            return cards.map((el, i) => {
                const cs = getComputedStyle(el);
                return {
                    i,
                    styleAttr: (el.getAttribute('style') || '').slice(0, 90),
                    computedBG: cs.backgroundImage.slice(0, 90),
                    zIndex: cs.zIndex,
                    visibleW: el.offsetWidth,
                };
            });
        }"""
    )
    for row in info:
        print(row)

    # fetch each bg URL from inside the page (with cookies/origin)
    statuses = page.evaluate(
        """async () => {
            const urls = [...document.querySelectorAll('.bento-card__bg')]
                .map(el => (el.getAttribute('style') || '').match(/url\\('([^']+)'/)?.[1])
                .filter(Boolean);
            const out = [];
            for (const u of urls) {
                try { const r = await fetch(u); out.push(`${u} -> ${r.status}`); }
                catch (e) { out.push(`${u} -> ERR ${e}`); }
            }
            return out;
        }"""
    )
    for s in statuses:
        print(s)

    page.screenshot(path=f"{OUT}/bento-probe-2p5s.png")

    print("--- failed requests:", len(failed))
    for f in failed[:8]:
        print("   ", f)
    csp = [m for m in console_msgs if "Content Security" in m or "CSP" in m.upper()]
    print("--- console msgs:", len(console_msgs), "| CSP-related:", len(csp))
    for m in (csp or console_msgs)[:8]:
        print("   ", m)
    browser.close()
