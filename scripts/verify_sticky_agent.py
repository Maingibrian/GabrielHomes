#!/usr/bin/env python3
"""Sticky agent card runtime verification on listing detail.

Asserts the card pins at top:~80px while the main column scrolls,
and captures mid-scroll evidence shots.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:3011/listing/3br-bungalow-in-nyali-77/"
OUT = Path("/home/z/my-project/scripts/shots/sticky-2026-10-12")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1200)

    card = page.locator(".agent-card-sticky")
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(400)

    probe = page.evaluate(
        """() => {
        const card = document.querySelector('.agent-card-sticky');
        const aside = document.querySelector('.detail-layout > aside');
        const cs = getComputedStyle(card);
        return {
            position: cs.position,
            top: cs.top,
            cardText: (card.querySelector('.agent-card-sticky__name')||{}).textContent || null,
            btns: card.querySelectorAll('.agent-card-sticky__btn').length,
            asideH: aside.offsetHeight,
            cardH: card.offsetHeight,
            viewportH: innerHeight,
        };
    }"""
    )
    print("STATE:", probe)

    # Scroll through the page; measure card viewport-top at each stop.
    samples = []
    for y in [600, 1400, 2200, 3000, 3800]:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(250)
        top = page.evaluate(
            "() => document.querySelector('.agent-card-sticky').getBoundingClientRect().top"
        )
        samples.append((y, round(top)))
    print("SCROLL->CARD_TOP:", samples)
    stuck = [t for _, t in samples if 60 <= t <= 100]
    print("STICKS:", "YES" if stuck else "NO", f"({len(stuck)} stops pinned ~80px)")

    # Evidence shot mid-page with the card pinned.
    page.evaluate("window.scrollTo(0, 1800)")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "sticky-mid-scroll-1440.png"))

    # Mobile: card must be static (in-flow) and the thumb bar present.
    page.set_viewport_size({"width": 390, "height": 844})
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    m = page.evaluate(
        """() => {
        const card = document.querySelector('.agent-card-sticky');
        const bar = document.querySelector('.mobile-contact-bar');
        return {pos: getComputedStyle(card).position,
                bar: bar ? getComputedStyle(bar).display : null};
    }"""
    )
    print("MOBILE:", m)
    print("CONSOLE:", errors[:3] or "none")
    browser.close()
