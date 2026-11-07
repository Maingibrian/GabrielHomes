"""r24 — REPRO: mobile home at 390x844 (owner screenshot viewport).

Samples the same centre-column pixels as the owner's screenshot and
measures bounding boxes of hero/header/stats/search/marquee so we can
compare against upload/pasted_image_1793887384702.png.
"""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/"

with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=1,
        is_mobile=True,
        has_touch=True,
        user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                    "Mobile/15E148 Safari/604.1"),
    )
    page = ctx.new_page()
    page.set_default_timeout(15000)
    resp = page.goto(BASE, wait_until="domcontentloaded")
    print("status:", resp.status)
    page.wait_for_selector(".hero", timeout=10000)
    page.wait_for_timeout(2500)  # let entrance animations settle

    print("\n--- centre-column pixel samples (y, rgb) ---")
    samples = page.evaluate(
        """() => {
          const out = [];
          const el = document.elementFromPoint(195, 0); // doc under any overlay
          for (let y = 0; y < 844; y += 21) {
            const e = document.elementFromPoint(195, y);
            const cs = e ? getComputedStyle(e) : null;
            out.push({y, tag: e ? e.tagName + '.' + (e.className.baseVal !== undefined ? '' : String(e.className).slice(0, 30)) : 'none'});
          }
          return out;
        }""")
    for s in samples:
        print(f"y={s['y']:4d} top-element: {s['tag']}")

    print("\n--- bounding boxes ---")
    boxes = page.evaluate(
        """() => {
          const names = ['.site-header', '.hero', '.hero__bg', '.hero__stats',
                         '.hero__search', '.hv2-scroll', '.hv2-marquee',
                         '.hero__title', '.hero__tag', '.hero__subtitle'];
          const out = {};
          for (const n of names) {
            const e = document.querySelector(n);
            if (!e) { out[n] = null; continue; }
            const r = e.getBoundingClientRect();
            out[n] = {top: Math.round(r.top), bottom: Math.round(r.bottom),
                      left: Math.round(r.left), right: Math.round(r.right),
                      h: Math.round(r.height), w: Math.round(r.width)};
          }
          out._scrollY = window.scrollY;
          out._bodyH = document.body.scrollHeight;
          return out;
        }""")
    for k, v in boxes.items():
        print(f"{k:18s} {v}")

    print("\n--- style probes ---")
    probes = page.evaluate(
        """() => {
          const h = document.querySelector('.site-header');
          const hero = document.querySelector('.hero');
          const bodyCS = getComputedStyle(document.body);
          const html = document.documentElement;
          return {
            headerPosition: h ? getComputedStyle(h).position : null,
            heroMinHeight: hero ? getComputedStyle(hero).minHeight : null,
            bodyBg: bodyCS.backgroundColor,
            bodyMargin: bodyCS.marginTop,
            fx: html.dataset.fx || null,
            scrollY: window.scrollY,
          };
        }""")
    print(probes)

    page.screenshot(path="LOOP/audit-screens/r24-repro-mobile-full.png")
    print("\nscreenshot: LOOP/audit-screens/r24-repro-mobile-full.png")
    browser.close()
    print("R24-REPRO-DONE")
