"""Scroll-through screenshots at multiple widths to see true rendered state."""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = "/home/z/my-project/scripts/shots"

JOBS = [
    ("home",   "/",           [390, 1440]),
    ("services", "/agents/",  [390, 1440]),
    ("detail", "/listing/modern-beachfront-apartment-nyali-81/", [390, 1440]),
]

def scroll_through(page):
    """Scroll down in steps to trigger IntersectionObserver reveals, then back up."""
    height = page.evaluate("document.body.scrollHeight")
    y = 0
    while y < height:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(320)
        y += 600
        height = page.evaluate("document.body.scrollHeight")
    page.wait_for_timeout(600)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, path, widths in JOBS:
            for w in widths:
                h = 844 if w < 500 else 900
                ctx = browser.new_context(viewport={"width": w, "height": h})
                page = ctx.new_page()
                errors = []
                page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
                page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
                try:
                    resp = page.goto(BASE + path, wait_until="networkidle", timeout=45000)
                    page.wait_for_timeout(1200)
                    scroll_through(page)
                    tag = f"{name}-{w}"
                    page.screenshot(path=f"{OUT}/{tag}-full.png", full_page=True)
                    sw = page.evaluate("document.documentElement.scrollWidth")
                    hidden = page.evaluate(
                        "[...document.querySelectorAll('[data-reveal]:not(.is-visible)')].length"
                    )
                    print(f"[{tag}] {resp.status} scrollW={sw} unrevealed={hidden}")
                    for e in errors[:8]:
                        print("   ", e)
                except Exception as exc:
                    print(f"[{name}-{w}] FAILED: {exc}")
                page.close()
                ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
