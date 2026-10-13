"""probe_about_home.py — critical behavioral probes for about/home/detail.

Answers, with hard numbers:
  1. Do [data-reveal] sections reveal under NATURAL step scrolling?
  2. Are they visible with JS DISABLED (D-MOTION-SAFE claim)?
  3. What are the real heights of about hero / agent cards (design or bug)?
  4. Viewport screenshots at key scroll positions for vision inspection.
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = Path("/home/z/my-project/scripts/shots/audit-2026-10-13")
OUT.mkdir(parents=True, exist_ok=True)


def step_scroll(page, total: int, step: int = 400, pause: int = 120) -> None:
    y = 0
    while y < total:
        y = min(y + step, total)
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(pause)
    page.wait_for_timeout(400)


def probe(page, url: str, name: str, js: bool = True) -> dict:
    out: dict = {"url": url, "js": js}
    page.goto("about:blank")
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(800)

    stats = page.evaluate(
        """() => {
        const els = [...document.querySelectorAll('[data-reveal]')];
        const lit = els.filter(e => e.classList.contains('is-visible'));
        const cs = e => getComputedStyle(e).opacity;
        const hidden = els.filter(e => parseFloat(cs(e)) < 0.05).length;
        return {
          reveal_total: els.length,
          reveal_visible_class: lit.length,
          reveal_opacity_zero: hidden,
          motion_ready: document.documentElement.classList.contains('motion-ready'),
          doc_height: document.documentElement.scrollHeight,
        };
    }"""
    )
    out["initial"] = stats

    if js:
        # natural scroll to the bottom in small steps
        total = stats["doc_height"]
        step_scroll(page, total)
        out["after_scroll"] = page.evaluate(
            """() => {
            const els = [...document.querySelectorAll('[data-reveal]')];
            const cs = e => getComputedStyle(e).opacity;
            return {
              reveal_visible_class: els.filter(e => e.classList.contains('is-visible')).length,
              reveal_opacity_zero: els.filter(e => parseFloat(cs(e)) < 0.05).length,
            };
        }"""
        )
        # per-section geometry on about
        out["sections"] = page.evaluate(
            """() => {
            return [...document.querySelectorAll('section, .about-hero, .team, .agents-grid, .agent-card')].slice(0, 24).map(s => {
              const r = s.getBoundingClientRect();
              return {tag: s.tagName + '.' + (s.className || '').toString().split(' ')[0],
                      h: Math.round(r.height), top: Math.round(r.top + window.scrollY)};
            });
        }"""
        )

    # screenshots: top, middle (agent area on about), wherever matters
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / f"{name}-vp-top.png"))
    if js:
        step_scroll(page, out["initial"]["doc_height"])
        page.screenshot(path=str(OUT / f"{name}-vp-bottom.png"))
        page.evaluate("window.scrollTo(0, 0)")
    return out


def main() -> None:
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        report["about_js"] = probe(page, BASE + "/about/", "about")
        report["home_js"] = probe(page, BASE + "/", "home")

        # JS-disabled robustness (fresh context)
        ctx2 = browser.new_context(viewport={"width": 1440, "height": 900}, java_script_enabled=False)
        page2 = ctx2.new_page()
        page2.goto(BASE + "/about/", wait_until="networkidle")
        page2.wait_for_timeout(500)
        report["about_nojs"] = page2.evaluate(
            """() => {
            const els = [...document.querySelectorAll('[data-reveal]')];
            const cs = e => getComputedStyle(e).opacity;
            return {
              motion_ready: document.documentElement.classList.contains('motion-ready'),
              opacity_zero: els.filter(e => parseFloat(cs(e)) < 0.05).length,
              reveal_total: els.length,
            };
        }"""
        )
        page2.screenshot(path=str(OUT / "about-nojs.png"))
        browser.close()

    (OUT / "probe-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2)[:4000])


if __name__ == "__main__":
    main()
