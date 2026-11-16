#!/usr/bin/env python3
"""r104 — capture the backend Edit-listing page (authenticated) at
1920/1440/413 for the whole-page review, then crops for VLM."""
import asyncio
import os

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:81"
LOGIN = "/account/login/"
EDIT = "/dashboard/listings/2/edit/"  # City Mall listing (pk 2 on fresh seed)
USER = "admin@gabrielhomes.co.ke"
PASS = "TempPass!r104"
OUT = "/home/z/my-project/download/screenshots/r104"
VIEWS = [
    ("desktop-1920", 1920, 1080),
    ("laptop-1440", 1440, 900),
    ("mobile-413", 413, 892),
]


async def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        for name, w, h in VIEWS:
            page = await browser.new_page(viewport={"width": w, "height": h})
            # login
            await page.goto(BASE + LOGIN, wait_until="networkidle")
            await page.fill('input[name="login"]', USER)
            await page.fill('input[name="password"]', PASS)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle")
            # edit page
            await page.goto(BASE + EDIT, wait_until="networkidle")
            await page.wait_for_timeout(900)
            await page.screenshot(path=f"{OUT}/edit-{name}-full.png", full_page=True)
            await page.screenshot(path=f"{OUT}/edit-{name}-fold.png")
            await page.close()
        await browser.close()
    print("saved:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    asyncio.run(main())
