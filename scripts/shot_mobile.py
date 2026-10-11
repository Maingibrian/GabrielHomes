"""Mobile hero close-ups."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = "/home/z/my-project/scripts/shots"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    page.goto(BASE + "/", wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{OUT}/home-390-fold.png")
    # check hero heights
    info = page.evaluate("""() => {
        const hero = document.querySelector('.hero');
        const bg = document.querySelector('.hero__bg');
        const title = document.querySelector('.hero__title');
        const search = document.querySelector('.hero__search');
        const header = document.querySelector('.site-header');
        const r = el => el ? {h: el.offsetHeight, w: el.offsetWidth, top: el.getBoundingClientRect().top + window.scrollY} : null;
        return {hero: r(hero), bg: r(bg), title: r(title), search: r(search), header: r(header),
                innerW: window.innerWidth, scrollW: document.documentElement.scrollWidth};
    }""")
    print("HOME 390:", info)

    page2 = ctx.new_page()
    page2.goto(BASE + "/listing/modern-beachfront-apartment-nyali-81/", wait_until="networkidle", timeout=45000)
    page2.wait_for_timeout(1500)
    page2.screenshot(path=f"{OUT}/detail-390-fold.png")
    wide = page2.evaluate("""() => {
        const out = [];
        const dw = document.documentElement.scrollWidth;
        document.querySelectorAll('*').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.right > 392 || r.left < -2) {
                out.push(el.tagName + '.' + String(el.className).slice(0,60) + ' right=' + Math.round(r.right) + ' left=' + Math.round(r.left) + ' w=' + Math.round(r.width));
            }
        });
        return {scrollW: dw, overflows: out.slice(0, 25)};
    }""")
    print("DETAIL 390 overflow:", wide)
    browser.close()
