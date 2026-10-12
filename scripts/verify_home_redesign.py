#!/usr/bin/env python3
"""Home redesign runtime verification (docs/HOME-REDESIGN.md cycles 1-4).

Checks:
  1. Hero slideshow: 4 slides, heroFade/heroDrift animations armed under
     html.motion-ready, slide 1 visible immediately.
  2. Story word-reveal: .word spans light up as the quote scrolls into view.
  3. Showcase bento: 6 listing cards + 1 CTA tile, reveal stagger, hover zoom.
  4. Console/page errors.
  5. Horizontal overflow hunt at 849 and 390.
  6. /agents/ regression: bento-grid still present with agent cards.
"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = "/home/z/my-project/scripts/shots"


def scroll_to(page, y):
    page.evaluate(f"window.scrollTo(0, {y})")
    page.wait_for_timeout(350)


def check_hero(page):
    res = page.evaluate(
        """() => {
        const html = document.documentElement;
        const slides = [...document.querySelectorAll('.hero__slide')];
        const anims = slides.map(s => {
            const cs = getComputedStyle(s);
            return {name: cs.animationName, dur: cs.animationDuration, delay: cs.animationDelay,
                    play: cs.animationPlayState, op: getComputedStyle(s).opacity};
        });
        return {
            motionReady: html.classList.contains('motion-ready'),
            n: slides.length,
            anims,
            bgCount: document.querySelectorAll('.hero__bg > *').length,
        };
    }"""
    )
    print("[hero]", json.dumps(res))
    return res


def check_word_reveal(page):
    quote = page.locator(".story__quote")
    quote.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    total = page.evaluate("document.querySelectorAll('.story__quote .word').length")
    lit0 = page.evaluate("document.querySelectorAll('.story__quote .word.is-lit').length")
    # scroll through the quote slowly (setupQuoteReveal lights on scroll progress)
    box = quote.bounding_box()
    vh = page.evaluate("window.innerHeight")
    for step in range(8):
        page.evaluate(
            f"window.scrollBy(0, {int((box['height'] + vh) / 10) if box else 120})"
        )
        page.wait_for_timeout(260)
    lit1 = page.evaluate("document.querySelectorAll('.story__quote .word.is-lit').length")
    print(f"[word-reveal] total={total} litAtEntry={lit0} litAfterScroll={lit1}")
    return total, lit0, lit1


def check_bento(page):
    res = page.evaluate(
        """() => {
        const cards = [...document.querySelectorAll('#showcase .bento-card')];
        const cta = document.querySelectorAll('#showcase .bento-card--cta').length;
        const withBg = cards.filter(c => {
            const bg = c.querySelector('.bento-card__bg');
            return bg && bg.style.backgroundImage && bg.style.backgroundImage.includes('url');
        }).length;
        const spotlight = document.querySelectorAll('#showcase .bento-card--spotlight').length;
        const gridCols = getComputedStyle(document.querySelector('#showcase .bento-grid')).gridTemplateColumns.split(' ').length;
        const revealPending = document.querySelectorAll('#showcase [data-reveal]:not(.is-visible)').length;
        return {cards: cards.length, cta, withBg, spotlight, gridCols, revealPending};
    }"""
    )
    print("[bento]", json.dumps(res))
    # hover zoom check on 2nd card
    card = page.locator("#showcase .bento-card").nth(1)
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(600)
    before = card.evaluate("(el) => getComputedStyle(el).transform")
    card.hover()
    page.wait_for_timeout(700)
    after = card.evaluate("(el) => getComputedStyle(el).transform")
    print(f"[bento-hover] before={before[:48]} after={after[:48]} changed={before != after}")
    return res


def hunt_overflow(page, width):
    sw = page.evaluate("document.documentElement.scrollWidth")
    if sw <= width:
        print(f"[overflow {width}] none (scrollW={sw})")
        return
    offenders = page.evaluate(
        """(vw) => {
        const out = [];
        document.querySelectorAll('body *').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.right > vw + 1 && r.width > 8) {
                const cs = getComputedStyle(el);
                if (cs.position === 'fixed' && parseFloat(cs.transform.replace(/[^\\d.-]/g, '')) < 0) return;
                out.push({sel: el.tagName + '.' + String(el.className).split(' ')[0],
                          right: Math.round(r.right), w: Math.round(r.width)});
            }
        });
        return out.slice(0, 12);
    }""",
        width,
    )
    print(f"[overflow {width}] scrollW={sw} offenders={json.dumps(offenders, indent=1)}")


def check_agents(page):
    page.goto(BASE + "/agents/", wait_until="networkidle", timeout=45000)
    res = page.evaluate(
        """() => ({
        grids: document.querySelectorAll('.bento-grid').length,
        agentCards: document.querySelectorAll('.agents-page .bento-card, main .bento-card').length,
        title: document.querySelector('h1') ? document.querySelector('h1').textContent.trim().slice(0, 40) : null,
    })"""
    )
    print("[agents]", json.dumps(res))
    page.screenshot(path=f"{OUT}/verify-agents-top.png")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        errors_all = []
        ctx = browser.new_context(viewport={"width": 1200, "height": 900})
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors_all.append(f"pageerror: {e}"))
        page.on(
            "console",
            lambda m: errors_all.append(f"console.{m.type}: {m.text}")
            if m.type == "error"
            else None,
        )
        page.goto(BASE + "/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1200)

        check_hero(page)
        check_bento(page)
        check_word_reveal(page)

        # section paddings snapshot for rhythm audit
        pads = page.evaluate(
            """() => {
            const secs = [...document.querySelectorAll('section.section')];
            return secs.map(s => ({id: s.id, h: Math.round(s.getBoundingClientRect().height)}));
        }"""
        )
        print("[section-heights]", json.dumps(pads))
        page.screenshot(path=f"{OUT}/verify-home-1200-full.png", full_page=True)

        hunt_overflow(page, 1200)
        ctx.close()

        for width, height in ((849, 900), (390, 844)):
            ctx = browser.new_context(viewport={"width": width, "height": height})
            pg = ctx.new_page()
            pg.goto(BASE + "/", wait_until="networkidle", timeout=45000)
            pg.wait_for_timeout(1000)
            hunt_overflow(pg, width)
            if width == 390:
                pg.screenshot(path=f"{OUT}/verify-home-390-full.png", full_page=True)
            else:
                pg.screenshot(path=f"{OUT}/verify-home-849-full.png", full_page=True)
            ctx.close()

        check_agents(browser.new_context(viewport={"width": 1200, "height": 900}).new_page()
                     ) if False else None
        ctx = browser.new_context(viewport={"width": 1200, "height": 900})
        check_agents(ctx.new_page())
        ctx.close()

        print("[errors]", errors_all[:10] if errors_all else "none")
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
