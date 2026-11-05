"""r24 — compare the owner's screenshot against the v6-slim baseline."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=1, is_mobile=True, has_touch=True,
        user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                    "Mobile/15E148 Safari/604.1"),
    )
    page = ctx.new_page()
    page.set_default_timeout(15000)
    resp = page.goto("http://127.0.0.1:8766/", wait_until="domcontentloaded")
    print("status:", resp.status)
    page.wait_for_timeout(2500)
    page.screenshot(path="/tmp/gh-baseline/baseline-mobile-390.png")

    boxes = page.evaluate(
        """() => {
          const out = {};
          for (const n of ['.site-header', '.hero', '.hero__search',
                           '.search-bar', '.hv2-marquee', '.hv2-scroll']) {
            const e = document.querySelector(n);
            out[n] = e ? Math.round(e.getBoundingClientRect().top) : null;
          }
          out.scrollY = window.scrollY;
          return out;
        }""")
    print(boxes)
    # what is the first element in the document, and what's above the header?
    probe = page.evaluate(
        """() => {
          const hdr = document.querySelector('.site-header');
          const r = hdr.getBoundingClientRect();
          // find all elements whose bottom is above the header top
          const above = [];
          for (const e of document.body.querySelectorAll('*')) {
            const b = e.getBoundingClientRect();
            if (b.height > 0 && b.bottom <= r.top + 1 && b.width > 50) {
              above.push({tag: e.tagName, cls: String(e.className).slice(0, 40),
                          h: Math.round(b.height), top: Math.round(b.top)});
            }
          }
          above.sort((a, b) => a.top - b.top);
          return above.slice(0, 8);
        }""")
    print("elements above header:", probe)
    browser.close()
    print("BASELINE-SHOT-DONE")
