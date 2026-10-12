#!/usr/bin/env python3
"""Runtime map verification: load flagship detail, count painted satellite tiles."""
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:3011/listing/3br-bungalow-in-nyali-77/"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="networkidle")
    page.locator("#detail-map").scroll_into_view_if_needed()
    page.wait_for_timeout(3500)

    state = page.evaluate(
        """() => {
        const el = document.getElementById('detail-map');
        const tiles = el.querySelectorAll('.leaflet-tile-loaded').length;
        const anyTile = el.querySelectorAll('.leaflet-tile').length;
        const srcs = [...el.querySelectorAll('.leaflet-tile-loaded')]
            .slice(0, 3).map(t => t.src.slice(8, 40));
        const marker = el.querySelectorAll('.leaflet-marker-icon').length;
        const layersCtrl = el.querySelectorAll('.leaflet-control-layers').length;
        const popup = el.querySelectorAll('.leaflet-popup').length;
        return {tiles, anyTile, srcs, marker, layersCtrl, popup,
                hasMap: !!el.classList.contains('leaflet-container')};
    }"""
    )
    print("MAP STATE:", state)
    # screenshot just the map block
    page.locator(".detail-map").screenshot(
        path="/home/z/my-project/scripts/shots/map-satellite-check.png"
    )
    print("CONSOLE ERRORS:", errors[:5] if errors else "none")
    browser.close()
