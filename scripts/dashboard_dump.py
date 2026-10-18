#!/usr/bin/env python3
"""r12 diagnostic — dump what /dashboard/ actually serves for the owner."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    pg.goto(BASE + "/admin/login/", wait_until="load")
    pg.fill("#id_username", "admin@gabrielhomes.co.ke")
    pg.fill("#id_password", "gabriel2026")
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(1500)
    pg.goto(BASE + "/dashboard/", wait_until="load")
    print("url:", pg.url)
    print("title-ish:", pg.title()[:60])
    print("table-scroll divs:", pg.locator(".table-scroll").count())
    print("listing-tables:", pg.locator("table.listing-table").count())
    parent = pg.evaluate(
        "() => { const t = document.querySelector('table.listing-table');"
        " return t ? t.parentElement.className : 'no-table'; }")
    print("first table parent:", parent)
    sw = pg.evaluate("() => document.documentElement.scrollWidth")
    print("doc scrollWidth:", sw)
    b.close()
