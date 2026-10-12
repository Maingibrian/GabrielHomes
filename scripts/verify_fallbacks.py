#!/usr/bin/env python3
"""Verify bento bg hover zoom, reduced-motion fallback, and no-JS visibility."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"

with sync_playwright() as p:
    browser = p.chromium.launch()

    # 1. bg hover zoom
    ctx = browser.new_context(viewport={"width": 1200, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    card = pg.locator("#showcase .bento-card").nth(1)
    card.scroll_into_view_if_needed()
    pg.wait_for_timeout(700)
    bg = card.locator(".bento-card__bg")
    before = bg.evaluate("(el) => getComputedStyle(el).transform + ' | ' + getComputedStyle(el).filter")
    card.hover()
    pg.wait_for_timeout(800)
    after = bg.evaluate("(el) => getComputedStyle(el).transform + ' | ' + getComputedStyle(el).filter")
    print("[bg-hover]")
    print("  before:", before)
    print("  after :", after)
    ctx.close()

    # 2. reduced motion: no animation on slides, slide 1 static visible
    ctx = browser.new_context(
        viewport={"width": 1200, "height": 900}, reduced_motion="reduce"
    )
    pg = ctx.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    res = pg.evaluate(
        """() => [...document.querySelectorAll('.hero__slide')].map(s => {
            const cs = getComputedStyle(s);
            return {name: cs.animationName, op: cs.opacity};
        })"""
    )
    print("[reduced-motion]", res)
    ctx.close()

    # 3. no-JS: content visible, slide 1 shown, quote fully lit
    ctx = browser.new_context(viewport={"width": 1200, "height": 900}, java_script_enabled=False)
    pg = ctx.new_page()
    pg.goto(BASE + "/", wait_until="load")
    pg.wait_for_timeout(1500)
    res = pg.evaluate(
        """() => {
        const slide1 = getComputedStyle(document.querySelector('.hero__slide')).opacity;
        const quote = document.querySelector('.story__quote');
        const qOp = quote ? getComputedStyle(quote).opacity : 'missing';
        const words = document.querySelectorAll('.story__quote .word').length;
        const statement = document.querySelector('.story__statement');
        const sOp = statement ? getComputedStyle(statement).opacity : 'missing';
        const bento = document.querySelectorAll('#showcase .bento-card').length;
        return {slide1, quoteOpacity: qOp, wordSpans: words, statementOpacity: sOp, bentoCards: bento};
    }"""
    )
    print("[no-js]", res)
    pg.screenshot(path="/home/z/my-project/scripts/shots/verify-home-nojs-top.png")
    ctx.close()

    browser.close()
