"""Test at the user's apparent viewport width (~849px) and nearby widths."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = "/home/z/my-project/scripts/shots"

with sync_playwright() as p:
    browser = p.chromium.launch()
    for w in (849, 900, 1024):
        ctx = browser.new_context(viewport={"width": w, "height": 700})
        page = ctx.new_page()
        page.goto(BASE + "/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1500)
        page.screenshot(path=f"{OUT}/home-{w}-fold.png")
        info = page.evaluate("""() => {
            const overlaps = [];
            const header = document.querySelector('.site-header');
            const title = document.querySelector('.hero__title');
            if (header && title) {
                const hr = header.getBoundingClientRect();
                const tr = title.getBoundingClientRect();
                overlaps.push('header-bottom=' + Math.round(hr.bottom) + ' title-top=' + Math.round(tr.top));
            }
            const hdr = document.querySelector('.site-header .container');
            if (hdr) {
                const kids = [...hdr.querySelectorAll('*')].filter(el => {
                    const r = el.getBoundingClientRect();
                    return r.width > 0 && (r.right > window.innerWidth - 4 || r.left < 4);
                });
                overlaps.push('header-overflow-els=' + kids.length);
            }
            return {scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth, info: overlaps};
        }""")
        print(w, info)
        page.close(); ctx.close()
    browser.close()
