"""r82 — visual check of /services/ with the real-listing photos."""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000"
OUT = Path("/home/z/my-project/download/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(20000)

    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    resp = page.goto(BASE + "/services/", wait_until="domcontentloaded")
    print("status:", resp.status)

    # let entrance reveals settle; force-lazy images near viewport
    page.wait_for_timeout(1800)

    probe = page.evaluate(
        """() => {
          const rows = [...document.querySelectorAll('.svc-row')].map(r => {
            const m = r.querySelector('.svc-row__media');
            const url = m ? m.style.backgroundImage : '';
            const rect = m ? m.getBoundingClientRect() : null;
            return { url: url.slice(5, -2), w: rect ? Math.round(rect.width) : 0,
                     h: rect ? Math.round(rect.height) : 0 };
          });
          const credit = document.querySelector('.svc-photo-credit');
          const cr = credit ? credit.getBoundingClientRect() : null;
          const link = credit ? credit.querySelector('a') : null;
          const img = new Image();
          // verify each background URL actually decodes (natural size > 0)
          return new Promise(resolve => {
            const checks = rows.map(r => new Promise(res => {
              const im = new Image();
              im.onload = () => res({ ...r, loaded: true, nw: im.naturalWidth, nh: im.naturalHeight });
              im.onerror = () => res({ ...r, loaded: false, nw: 0, nh: 0 });
              im.src = r.url;
            }));
            Promise.all(checks).then(rs => resolve({
              rows: rs,
              credit: credit ? {
                text: credit.textContent.trim().slice(0, 90),
                top: Math.round(cr.top), left: Math.round(cr.left),
                linkHref: link ? link.getAttribute('href') : null,
                linkStatus: link ? link.textContent.trim() : null,
              } : null,
            }));
          });
        }""")

    print("rows:")
    for r in probe["rows"]:
        print(f"  {r['url']}  panel={r['w']}x{r['h']}  "
              f"loaded={r['loaded']} natural={r['nw']}x{r['nh']}")
    print("credit:", probe["credit"])

    page.screenshot(path=str(OUT / "svc-r82-real-listing.png"), full_page=False)
    page.evaluate(
        "document.querySelectorAll('[data-reveal]').forEach(e => e.classList.add('is-visible'));")
    page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / "svc-r82-real-listing-full.png"), full_page=True)

    # the credit link should lead to a live listing page
    if probe["credit"]:
        r2 = page.goto(BASE + probe["credit"]["linkHref"], wait_until="domcontentloaded")
        print("credit link target:", probe["credit"]["linkHref"], "=>", r2.status)

    # quick site smoke through the bridge
    for path in ["/", "/properties/", "/property-for-sale/", "/contact/"]:
        code = page.evaluate(
            "u => fetch(u, {method:'HEAD'}).then(r => r.status)", path)
        print(f"HEAD {path} => {code}")

    print("console errors:", errors[:5] if errors else "none")
    ctx.close()
    browser.close()
print("done")
