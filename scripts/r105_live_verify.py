#!/usr/bin/env python3
"""r105 — live verification of the agencies cleanup + pin picker + nav
cross-links, through the local chain first (public chain after)."""
import asyncio
import re

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:81"
LOGIN = "/account/login/"
USER = "admin@gabrielhomes.co.ke"
PASS = "TempPass!r104"
OUT = "/home/z/my-project/download/screenshots/r105"


async def main() -> None:
    import os
    os.makedirs(OUT, exist_ok=True)
    results = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(BASE + LOGIN, wait_until="networkidle")
        await page.fill('input[name="login"]', USER)
        await page.fill('input[name="password"]', PASS)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")

        # 1) owner dashboard: agencies UI gone, Studio link present
        await page.goto(BASE + "/dashboard/", wait_until="networkidle")
        html = await page.content()
        results["dashboard: no Agencies nav"] = "Agencies\n" not in html and ">Agencies<" not in html
        results["dashboard: no agency stat"] = 'dashboard-stat__label">Agencies' not in html
        results["dashboard: Studio link"] = "/manage/" in html
        results["dashboard: no bracket label"] = "[ EVERY AGENCY" not in html
        await page.screenshot(path=f"{OUT}/dashboard-1920.png")

        # 2) all-listings: agency filter/column gone, page 200
        await page.goto(BASE + "/dashboard/all-listings/", wait_until="networkidle")
        html = await page.content()
        results["all-listings: no agency filter"] = 'id="f-agency"' not in html
        results["all-listings: no agency col"] = "<th>Agency</th>" not in html
        results["all-listings: Studio link"] = "/manage/" in html

        # 3) agencies route still 200 (kept deliberately)
        resp = await page.goto(BASE + "/dashboard/agencies/", wait_until="networkidle")
        results["agencies route still 200"] = resp.status == 200

        # 4) edit page: pin map present and renders a real map canvas
        await page.goto(BASE + "/dashboard/listings/2/edit/", wait_until="networkidle")
        await page.wait_for_timeout(2500)  # maplibre import + tile fetch
        html = await page.content()
        results["edit: pin-map div"] = 'id="pin-map"' in html
        results["edit: pin script tag"] = "pin-picker.js" in html
        canvas = await page.query_selector("#pin-map canvas")
        results["edit: map canvas rendered"] = canvas is not None
        # lat/lng inputs still present and named right
        results["edit: lat input"] = 'id="id_lat"' in html
        results["edit: lng input"] = 'id="id_lng"' in html
        # click the map center -> coordinates should fill the inputs
        if canvas:
            box = await canvas.bounding_box()
            await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            await page.wait_for_timeout(600)
            lat_val = await page.input_value("#id_lat")
            lng_val = await page.input_value("#id_lng")
            try:
                ok = lat_val and lng_val and -4.6 < float(lat_val) < -3.2 and 39.0 < float(lng_val) < 40.5
            except ValueError:
                ok = False
            results["edit: click drops pin in Mombasa range"] = bool(ok)
        await page.screenshot(path=f"{OUT}/edit-pinmap-1920.png")

        # 5) Studio nav has the workspace cross-link
        await page.goto(BASE + "/manage/", wait_until="networkidle")
        html = await page.content()
        results["studio: workspace link"] = "Listings workspace" in html
        await page.screenshot(path=f"{OUT}/studio-nav-1920.png")

        # 6) mobile sanity of the edit page
        page2 = await browser.new_page(viewport={"width": 413, "height": 892})
        await page2.goto(BASE + LOGIN, wait_until="networkidle")
        await page2.fill('input[name="login"]', USER)
        await page2.fill('input[name="password"]', PASS)
        await page2.click('button[type="submit"]')
        await page2.wait_for_load_state("networkidle")
        await page2.goto(BASE + "/dashboard/listings/2/edit/", wait_until="networkidle")
        await page2.wait_for_timeout(2000)
        canvas2 = await page2.query_selector("#pin-map canvas")
        results["mobile: map canvas rendered"] = canvas2 is not None
        await page2.screenshot(path=f"{OUT}/edit-pinmap-413.png")

        await browser.close()

    ok = True
    for k, v in results.items():
        print(("PASS " if v else "FAIL ") + k)
        ok = ok and v
    print("ALL:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    asyncio.run(main())
