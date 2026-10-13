#!/usr/bin/env python3
"""Vision-verify the About page hero + agent cards after the redesign.

Captures:
  - about-hero.png   — top of the page (real-photo hero check)
  - about-agents.png — the #team section (agent card layout + contacts)
  - about-mobile.png — 390px viewport, team section
Also dumps every contact link href found in the team section.
"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:3011"
OUT = "/home/z/my-project/scripts/shots"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # ---------- desktop ----------
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto(f"{BASE}/about/", wait_until="networkidle")
        await page.evaluate("""async () => {
            // step-scroll to the bottom so data-reveal fires naturally
            const h = document.body.scrollHeight;
            for (let y = 0; y <= h; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
            window.scrollTo(0, 0);
        }""")
        await page.wait_for_timeout(700)

        await page.screenshot(path=f"{OUT}/about-hero.png")

        team = page.locator("#team")
        await team.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        await team.screenshot(path=f"{OUT}/about-agents.png")

        # contact links audit
        links = await page.eval_on_selector_all(
            "#team .agent-contact",
            "els => els.map(e => e.href)",
        )
        cards = await page.eval_on_selector_all(
            "#team .agent-card",
            "els => els.map(e => { const r = e.getBoundingClientRect(); return `${r.width}x${r.height}`; })",
        )
        grid_cols = await page.eval_on_selector(
            "#team .agents__grid", "el => getComputedStyle(el).gridTemplateColumns"
        )
        print("CONTACT LINKS:")
        for l in links:
            print("  ", l)
        print("CARD SIZES:", cards)
        print("GRID COLS:", grid_cols)

        # hero background actually resolves
        hero_bg = await page.evaluate(
            """() => { const s = getComputedStyle(document.querySelector('.page-hero'), '::before');
                       return s.backgroundImage.slice(0, 120); }"""
        )
        print("HERO BG:", hero_bg)

        # ---------- mobile ----------
        mob = await browser.new_page(viewport={"width": 390, "height": 844})
        await mob.goto(f"{BASE}/about/", wait_until="networkidle")
        await mob.evaluate("""async () => {
            const h = document.body.scrollHeight;
            for (let y = 0; y <= h; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 50)); }
        }""")
        await mob.wait_for_timeout(500)
        mt = mob.locator("#team")
        await mt.scroll_into_view_if_needed()
        await mob.wait_for_timeout(400)
        await mt.screenshot(path=f"{OUT}/about-mobile.png")

        overflow = await mob.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )
        print("MOBILE OVERFLOW PX:", overflow)

        await browser.close()


asyncio.run(main())
