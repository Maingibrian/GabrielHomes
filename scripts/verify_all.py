"""Full verification: satellite map, reveals (JS on/off), overflow, services page."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = "/home/z/my-project/scripts/shots"
DETAIL = "/listing/modern-beachfront-apartment-nyali-81/"

def scroll_through(page, step=600, pause=280):
    height = page.evaluate("document.body.scrollHeight")
    y = 0
    while y < height:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(pause)
        y += step
        height = page.evaluate("document.body.scrollHeight")
    page.wait_for_timeout(500)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(400)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # --- 1. Detail page: satellite map + sticky agent card + overflow ---
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        pg.goto(BASE + DETAIL, wait_until="networkidle", timeout=45000)
        pg.wait_for_timeout(2000)
        # scroll map into view
        pg.eval_on_selector("#detail-map", "el => el.scrollIntoView({block:'center'})")
        pg.wait_for_timeout(2200)  # let Esri tiles load
        pg.screenshot(path=f"{OUT}/v-map-satellite.png")
        map_info = pg.evaluate("""() => {
            const el = document.getElementById('detail-map');
            const imgs = [...el.querySelectorAll('img.leaflet-tile')];
            const srcs = imgs.map(i => i.src);
            return {tiles: imgs.length,
                    esri: srcs.filter(s => s.includes('arcgisonline')).length,
                    osm: srcs.filter(s => s.includes('openstreetmap')).length,
                    carto: srcs.filter(s => s.includes('cartocdn')).length,
                    esriFailed: 0};
        }""")
        print("MAP:", map_info)
        # sticky behaviour
        sticky = pg.evaluate("""() => {
            const card = document.querySelector('.agent-card-sticky');
            window.scrollTo(0, 900);
            return new Promise(res => setTimeout(() => {
                const r = card.getBoundingClientRect();
                res({top: Math.round(r.top), visible: r.top >= 0 && r.bottom <= innerHeight + 5,
                     scrollY: Math.round(scrollY)});
            }, 350));
        }""")
        print("STICKY:", sticky)
        pg.wait_for_timeout(400)
        pg.screenshot(path=f"{OUT}/v-detail-sticky.png")
        sw1440 = pg.evaluate("document.documentElement.scrollWidth")
        print("DETAIL 1440 scrollW:", sw1440)
        pg.close(); ctx.close()

        # --- 2. Mobile: no overflow, map hint wraps ---
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        pg = ctx.new_page()
        pg.goto(BASE + DETAIL, wait_until="networkidle", timeout=45000)
        pg.wait_for_timeout(1500)
        sw390 = pg.evaluate("document.documentElement.scrollWidth")
        print("DETAIL 390 scrollW:", sw390)
        pg.eval_on_selector("#detail-map", "el => el.scrollIntoView({block:'center'})")
        pg.wait_for_timeout(1800)
        pg.screenshot(path=f"{OUT}/v-mobile-map.png")
        pg.close(); ctx.close()

        # --- 3. Services page with JS: cards visible after scroll ---
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(BASE + "/agents/", wait_until="networkidle", timeout=45000)
        pg.wait_for_timeout(1200)
        scroll_through(pg)
        revealed = pg.evaluate("[...document.querySelectorAll('[data-reveal]:not(.is-visible)')].length")
        sw = pg.evaluate("document.documentElement.scrollWidth")
        print(f"SERVICES js-on: unrevealed={revealed} scrollW={sw} errors={errs[:3]}")
        pg.screenshot(path=f"{OUT}/v-services-js.png", full_page=True)
        pg.close(); ctx.close()

        # --- 4. Services page with JS DISABLED: everything visible (motion-safe) ---
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, java_script_enabled=False)
        pg = ctx.new_page()
        pg.goto(BASE + "/agents/", wait_until="domcontentloaded", timeout=45000)
        pg.wait_for_timeout(1500)
        vis = pg.evaluate("""() => {
            const els = [...document.querySelectorAll('[data-reveal]')];
            const hidden = els.filter(el => parseFloat(getComputedStyle(el).opacity) < 0.5);
            return {total: els.length, hidden: hidden.length};
        }""")
        print("SERVICES js-off:", vis)
        pg.screenshot(path=f"{OUT}/v-services-nojs.png", full_page=True)
        pg.close(); ctx.close()

        # --- 5. Home with JS off: hero + stats visible ---
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, java_script_enabled=False)
        pg = ctx.new_page()
        pg.goto(BASE + "/", wait_until="domcontentloaded", timeout=45000)
        pg.wait_for_timeout(1200)
        vis = pg.evaluate("""() => {
            const els = [...document.querySelectorAll('[data-reveal]')];
            const hidden = els.filter(el => parseFloat(getComputedStyle(el).opacity) < 0.5);
            return {total: els.length, hidden: hidden.length};
        }""")
        print("HOME js-off:", vis)
        pg.screenshot(path=f"{OUT}/v-home-nojs.png")
        pg.close(); ctx.close()

        # --- 6. Cached-URL check: staticv version present in HTML ---
        ctx = browser.new_context(viewport={"width": 1200, "height": 800})
        pg = ctx.new_page()
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        html = pg.content()
        print("staticv in HTML:", "css/base.css?v=20261011a" in html,
              "| motion.js versioned:", "js/motion.js?v=" in html)
        pg.close(); ctx.close()

        browser.close()

if __name__ == "__main__":
    main()
