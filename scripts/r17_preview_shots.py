"""r17 preview screenshots — fresh renders of the live Django site.

Captures home (full page), properties browse+map, and the first listing
detail into download/preview-screenshots/r17-*.jpg, then verifies each file
is a real render (non-blank pixel ratio via PIL).
"""
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image
import io

OUT = Path("/home/z/my-project/download/preview-screenshots")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8000"

SHOTS = []


def shoot(page, url, name, full=True):
    page.goto(url, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(800)
    # walk the page so IntersectionObserver reveals fire like a real scroll
    page.evaluate(
        """async () => {
          const step = window.innerHeight * 0.7;
          for (let y = 0; y <= document.body.scrollHeight; y += step) {
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 160));
          }
          window.scrollTo(0, 0);
          await new Promise(r => setTimeout(r, 400));
        }""")
    page.wait_for_timeout(600)
    path = OUT / name
    page.screenshot(path=str(path), full_page=full, type="jpeg", quality=70)
    SHOTS.append((name, path))


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        shoot(page, f"{BASE}/", "r17-home-desktop.jpg")
        shoot(page, f"{BASE}/properties/", "r17-properties-map.jpg")
        # first listing detail link on the browse page
        href = page.evaluate(
            "(() => { const a = document.querySelector("
            "  'a[href^=\"/properties/\"]:not([href=\"/properties/\"])');"
            "  return a ? a.getAttribute('href') : null; })()")
        if href:
            shoot(page, f"{BASE}{href}", "r17-listing-detail.jpg")
        # mobile home for the responsive story
        mob = browser.new_context(viewport={"width": 390, "height": 844},
                                  is_mobile=True, has_touch=True)
        mpage = mob.new_page()
        shoot(mpage, f"{BASE}/", "r17-home-mobile.jpg")
        browser.close()

    print(f"{'file':36} {'size':>8}  non-white")
    for name, path in SHOTS:
        img = Image.open(path).convert("L")
        small = img.resize((160, max(1, int(160 * img.height / img.width))))
        px = list(small.getdata())
        nonwhite = sum(1 for v in px if v < 245) / len(px)
        ok = "OK" if nonwhite > 0.15 else "SUSPICIOUS-BLANK"
        print(f"{name:36} {path.stat().st_size//1024:>6}KB  "
              f"{nonwhite:6.1%}  {ok}")


if __name__ == "__main__":
    main()
