"""r85 — precise drift-rate check: read palmsVar and the live expected
target at the same instant, at a series of settled positions."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000/properties/"

READ = """() => {
  const band = document.querySelector('.listings-band');
  const cs = getComputedStyle(band, '::before');
  const y = window.scrollY;
  const rect = band.getBoundingClientRect();
  const vh = window.innerHeight;
  const DRIFT = 0.5;
  const top = rect.top + y;
  const bottom = top + rect.height;
  const pinEnd = Math.max(top, bottom - vh);
  let expected;
  if (rect.top >= vh) expected = 0;
  else if (rect.bottom <= 0) expected = null;
  else if (y <= top) expected = Math.max(0, (1 - DRIFT) * (y - (top - vh)));
  else if (y >= pinEnd) {
    const join = vh * (1 - DRIFT) - DRIFT * (pinEnd - top);
    expected = join + (1 - DRIFT) * (Math.min(y, bottom) - pinEnd);
  } else expected = vh * (1 - DRIFT) - DRIFT * (y - top);
  return {
    y: Math.round(y),
    bandTop: Math.round(top),
    bandBottom: Math.round(bottom),
    phase: rect.top >= vh ? 'entry0' : rect.bottom <= 0 ? 'gone' :
           y <= top ? 'entry' : y >= pinEnd ? 'release' : 'pinned',
    palms: parseFloat(band.style.getPropertyValue('--palms-y')) || 0,
    expected: expected === null ? null : +expected.toFixed(1),
    bgpos: cs.backgroundPositionY,
    pseudoH: cs.height,
  };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    top = page.evaluate(
        "document.querySelector('.listings-band').getBoundingClientRect().top"
        " + scrollY")
    print(f"band doc-top: {top:.0f}")
    # instant scrolls, settle 600ms each
    for probe in [top - 700, top, top + 400, top + 2000, top + 6000,
                  top + 11000, top + 11549]:
        page.evaluate(f"scrollTo({{top: {probe}, behavior: 'instant'}})")
        page.wait_for_timeout(700)
        r = page.evaluate(READ)
        ok = (r["expected"] is None or
              abs(r["palms"] - r["expected"]) < 1.5)
        print(f"y={r['y']:>6} {r['phase']:<8} palms={r['palms']:>8.2f} "
              f"expected={str(r['expected']):>8} bgpos={r['bgpos']:<12} "
              f"pseudoH={r['pseudoH']} {'OK' if ok else '** MISMATCH **'}")
    browser.close()
