"""r84 — capture the UPGRADED /services/ execution + hover choreography proof.

Desktop stations + a hover probe on TOC row 2 (thumbnail swap + name slide)
+ mobile pair. All scrolls behavior:'instant'.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000"
OUT = Path("/home/z/my-project/download/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name):
    page.screenshot(path=str(OUT / name))
    print("saved", name)


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])

    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    page.goto(BASE + "/services/", wait_until="domcontentloaded")
    page.wait_for_timeout(1500)

    page.evaluate("scrollTo(0, 0)"); page.wait_for_timeout(300)
    shot(page, "r84-new-top.png")

    page.locator(".svc-toc").first.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    shot(page, "r84-new-toc.png")

    # hover probe: second row — thumbnail swaps in, name slides
    row = page.locator(".svc-toc__row").nth(1)
    row.hover()
    page.wait_for_timeout(450)
    shot(page, "r84-new-toc-hover.png")
    state = page.evaluate("""() => {
      const row = document.querySelectorAll('.svc-toc__row')[1];
      const thumb = row.querySelector('.svc-toc__thumb');
      const num = row.querySelector('.svc-toc__num');
      const name = row.querySelector('.svc-toc__name');
      const meta = row.querySelector('.svc-toc__meta');
      const ts = getComputedStyle(thumb), ns = getComputedStyle(num),
            ms = getComputedStyle(name), es = getComputedStyle(meta);
      return {thumbOpacity: ts.opacity, thumbTransform: ts.transform,
              numOpacity: ns.opacity, nameColor: ms.color,
              nameTransform: ms.transform, metaColor: es.color,
              thumbW: thumb.getBoundingClientRect().width};
    }""")
    print("hover state:", state)
    page.mouse.move(640, 5); page.wait_for_timeout(300)

    page.locator(".svc-ledger").first.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    shot(page, "r84-new-ledger.png")

    page.evaluate("scrollTo(0, document.getElementById('svc-buying').offsetTop + 420)")
    page.wait_for_timeout(400)
    shot(page, "r84-new-svc-buying.png")

    page.evaluate("scrollTo(0, document.getElementById('svc-renting').offsetTop + 300)")
    page.wait_for_timeout(400)
    shot(page, "r84-new-svc-renting.png")

    pledge = page.locator(".svc-pledge").first
    pledge.scroll_into_view_if_needed(); page.wait_for_timeout(400)
    shot(page, "r84-new-pledge.png")
    ctx.close()

    mctx = browser.new_context(viewport={"width": 390, "height": 844},
                               is_mobile=True, has_touch=True)
    mpage = mctx.new_page()
    mpage.goto(BASE + "/services/", wait_until="domcontentloaded")
    mpage.wait_for_timeout(1500)
    shot(mpage, "r84-new-mobile-top.png")
    mpage.evaluate("scrollTo(0, document.getElementById('svc-buying').offsetTop - 40)")
    mpage.wait_for_timeout(400)
    shot(mpage, "r84-new-mobile-chapter.png")
    ovw = mpage.evaluate(
        "() => document.documentElement.scrollWidth - window.innerWidth")
    print("mobile overflow:", ovw)
    mctx.close()
    browser.close()

print("done")
