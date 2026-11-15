#!/usr/bin/env python3
"""r103 — capture the listing detail page at 1920/1440/413 for the whole-page review.

Full-page screenshots + per-component element boxes (gallery, facts bar,
description, amenities, nearby, map, sidebar card, similar rail, mobile bar).
"""
import asyncio
import json
import os

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:81"
LISTING = "/listing/3br-apartment-near-city-mall-nyali-242/"
OUT = "/home/z/my-project/download/screenshots/r103"
VIEWS = [
    ("desktop-1920", 1920, 1080),
    ("laptop-1440", 1440, 900),
    ("mobile-413", 413, 892),
]

COMPONENTS = [
    ".detail-intro", ".gallery--revamp", ".facts-bar--revamp",
    ".detail-description", ".amenities", ".nearby-amenities",
    ".detail-map", ".agent-card-sticky", ".similar",
]


async def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    boxes = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        for name, w, h in VIEWS:
            page = await browser.new_page(viewport={"width": w, "height": h})
            await page.goto(BASE + LISTING, wait_until="networkidle")
            await page.wait_for_timeout(1200)
            await page.screenshot(path=f"{OUT}/detail-{name}-full.png", full_page=True)
            # element boxes for layout review
            vb = {}
            for sel in COMPONENTS:
                el = await page.query_selector(sel)
                if el:
                    bb = await el.bounding_box()
                    vb[sel] = {k: round(v, 1) for k, v in bb.items()} if bb else None
            boxes[name] = vb
            # viewport-height shot of the fold for each breakpoint
            await page.screenshot(path=f"{OUT}/detail-{name}-fold.png")
            await page.close()
        await browser.close()
    with open(f"{OUT}/element-boxes.json", "w") as fh:
        json.dump(boxes, fh, indent=2)
    print("saved:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    asyncio.run(main())
