"""r84 — capture the CURRENT /services/ execution state for the upgrade pass.

Desktop 1280x800 viewport shots at the key scroll stations + a mobile pair.
All scrolls behavior:'instant' (r81 lesson).
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000"
OUT = Path("/home/z/my-project/download/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name, full=False):
    page.screenshot(path=str(OUT / name), full_page=full)
    print("saved", name)


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])

    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    page.goto(BASE + "/services/", wait_until="domcontentloaded")
    page.wait_for_timeout(1500)

    # stations: top (hero+toc), ledger, each chapter mid-pin, pledge
    page.evaluate("scrollTo(0, 0)"); page.wait_for_timeout(300)
    shot(page, "r84-cur-top.png")

    toc = page.locator(".svc-toc").first
    toc.scroll_into_view_if_needed(); page.wait_for_timeout(400)
    shot(page, "r84-cur-toc.png")

    ledger = page.locator(".svc-ledger").first
    ledger.scroll_into_view_if_needed(); page.wait_for_timeout(400)
    shot(page, "r84-cur-ledger.png")

    for cid in ["svc-buying", "svc-renting", "svc-listing", "svc-enquiries"]:
        el = page.locator(f"#{cid}").first
        el.scroll_into_view_if_needed(); page.wait_for_timeout(400)
        # nudge into the pin range (a bit past the chapter top)
        page.evaluate(f"scrollTo(0, document.getElementById('{cid}').offsetTop + 300)")
        page.wait_for_timeout(400)
        shot(page, f"r84-cur-{cid}.png")

    pledge = page.locator(".svc-pledge").first
    if pledge.count():
        pledge.scroll_into_view_if_needed(); page.wait_for_timeout(400)
        shot(page, "r84-cur-pledge.png")
    ctx.close()

    # mobile
    mctx = browser.new_context(viewport={"width": 390, "height": 844},
                               is_mobile=True, has_touch=True)
    mpage = mctx.new_page()
    mpage.goto(BASE + "/services/", wait_until="domcontentloaded")
    mpage.wait_for_timeout(1500)
    shot(mpage, "r84-cur-mobile-top.png")
    mpage.evaluate("scrollTo(0, document.getElementById('svc-renting').offsetTop - 60)")
    mpage.wait_for_timeout(400)
    shot(mpage, "r84-cur-mobile-chapter.png")
    mctx.close()
    browser.close()

print("done")
