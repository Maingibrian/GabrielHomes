"""r21 — render smoke after the media diet + HYG-1 purge.

Home: hero slide 1 (WebP) loads, bento cards render.
Search: the three market-filter WebP images load (naturalWidth > 0).
Screenshots -> LOOP/audit-screens/r21-*.png.
"""
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
REPO = Path(__file__).resolve().parents[1]
SHOTS = REPO / "LOOP" / "audit-screens"
DL = Path("/home/z/my-project/download/preview-screenshots")

fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(10000)

    print("home @1280:")
    resp = page.goto(f"{BASE}/", wait_until="domcontentloaded")
    check("home 200", resp.status == 200, str(resp.status))
    page.wait_for_selector(".hero__slide", timeout=8000)
    page.wait_for_timeout(900)
    n = page.evaluate(
        "[...document.querySelectorAll('.hero__slide')].filter(s => {"
        "const u = s.style.getPropertyValue('--slide-img');"
        "return u.includes('hero-slide-1.webp');}).length")
    check("hero slide 1 ref is webp", n == 1, f"matches={n}")
    img1 = page.evaluate(
        "new Promise(res => { const i = new Image(); i.onload = () => "
        "res(i.naturalWidth); i.onerror = () => res(0); "
        "i.src = document.querySelector('.hero__slide').style.getPropertyValue("
        "'--slide-img').slice(5, -2); })")
    check("hero-slide-1.webp decodes", img1 > 0, f"naturalWidth={img1}")
    grid = page.locator(".bento-grid--shift")
    disp = grid.evaluate("el => getComputedStyle(el).display")
    check("bento grid renders (post-purge css)", disp == "grid", f"display={disp}")
    marq = page.locator(".hv2-marquee")
    check("live hv2-marquee still styled",
          marq.count() == 0 or marq.first.evaluate(
              "el => getComputedStyle(el).overflow") == "hidden")
    page.screenshot(path=str(SHOTS / "r21-home-after-diet.png"))
    shutil.copy(SHOTS / "r21-home-after-diet.png",
                DL / "r21-home-after-diet.jpg", )

    print("search @1280:")
    resp = page.goto(f"{BASE}/properties/", wait_until="domcontentloaded")
    check("search 200", resp.status == 200, str(resp.status))
    page.wait_for_selector(".market-filter img", timeout=8000)
    page.wait_for_timeout(900)
    loaded = page.evaluate(
        "[...document.querySelectorAll('.market-filter img')].map(i => "
        "[i.currentSrc.split('/').pop(), i.naturalWidth, "
        "getComputedStyle(i).width])")
    check("three market images", len(loaded) == 3, str(loaded))
    for src, nw, w in loaded:
        base = src.split("?")[0]
        check(f"{base} loads + renders", nw > 0 and w != "auto", f"nw={nw} css={w}")
        check(f"{base} is webp", base.endswith(".webp"))
    page.screenshot(path=str(SHOTS / "r21-search-after-diet.png"))
    ctx.close()
    browser.close()

print(f"\n{'SMOKE VERDICT: FAIL — ' + ', '.join(fails) if fails else 'SMOKE VERDICT: PASS'}")
raise SystemExit(1 if fails else 0)
