"""r44 E3 — bento unpack + flank wordmarks: reproducible browser proof.

Owner request r44: (1) the bento card "opens some items within it" on
expansion, (2) giant "gabriel"/"homes" wordmarks flank the bento with a
stagnant-parallax lag — WITHOUT altering the bento's size.

This script re-proves, in a real browser, what the r44 session verified:
  A. flanks: at 1600px both words are display:block, one per side of the
     grid, fully on-screen, with a positive gap to the grid; the grid box
     still equals the .container content box (flanks cannot push it);
  B. resting spotlight: the first card arrives unpacked — drawer rows
     resolve open (px), opacity 1, ≥3 cream chips visible;
  C. hover fallback (this headless context is fx=lite, no [data-fine],
     so the shift grid is NOT live): a hovered tile opens the COMPACT
     drawer — one chip row (nowrap), no CTA — and never the full one;
  D. stagnant parallax: scrolling 600px deeper into the section swings
     the word's translateY by ≥40px (0.14x lag, ±110px clamp);
  E. mobile 390px: drawer + "+" hidden, flanks hidden, grid is the H3
     flex rail.

Usage: /home/z/.venv/bin/python3 scripts/r44_e3_unpack_probe.py [--base http://127.0.0.1:3000]
Exit 1 on the first failing check group; prints a PASS line per group.
"""
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000"
if "--base" in sys.argv:
    BASE = sys.argv[sys.argv.index("--base") + 1]

failures = []


def check(group, ok, detail):
    print(("PASS  " if ok else "FAIL  ") + group + (" — " + detail if detail else ""))
    if not ok:
        failures.append(group)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_context(viewport={"width": 1600, "height": 1000}).new_page()
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(1500)

    # ---- A. flanks ---------------------------------------------------
    a = page.evaluate(
        """() => {
          const grid = document.querySelector('.bento-grid--shift').getBoundingClientRect();
          const contEl = document.querySelector('.showcase .container');
          const csC = getComputedStyle(contEl);
          const cont = contEl.getBoundingClientRect();
          const contContent = {left: cont.left + parseFloat(csC.paddingLeft),
                               right: cont.right - parseFloat(csC.paddingRight)};
          const g = document.querySelector('.bento-flank--gabriel .bento-flank__word');
          const h = document.querySelector('.bento-flank--homes .bento-flank__word');
          const gr = g.getBoundingClientRect(), hr = h.getBoundingClientRect();
          return {
            gabrielBlock: getComputedStyle(g.parentElement).display,
            gabrielLeft: Math.round(gr.left), gabrielRight: Math.round(gr.right),
            homesLeft: Math.round(hr.left), homesRight: Math.round(hr.right),
            gridLeft: Math.round(grid.left), gridRight: Math.round(grid.right),
            gridW: Math.round(grid.width),
            contLeft: Math.round(contContent.left), contRight: Math.round(contContent.right),
          };
        }""")
    check("A1 gabriel in the LEFT gutter",
          a["gabrielBlock"] == "block" and a["gabrielLeft"] >= 0
          and a["gabrielRight"] <= a["gridLeft"],
          f"gabriel [{a['gabrielLeft']},{a['gabrielRight']}] vs grid@{a['gridLeft']}")
    check("A2 homes in the RIGHT gutter",
          a["homesLeft"] >= a["gridRight"] and a["homesRight"] <= 1600,
          f"homes [{a['homesLeft']},{a['homesRight']}] vs grid@{a['gridRight']}")
    check("A3 bento size untouched (grid == container content box)",
          abs(a["gridLeft"] - a["contLeft"]) <= 1 and abs(a["gridRight"] - a["contRight"]) <= 1,
          f"grid {a['gridLeft']}..{a['gridRight']} == container content {a['contLeft']}..{a['contRight']}")

    # ---- B. resting spotlight unpacks on load ------------------------
    b = page.evaluate(
        """() => {
          const card = document.querySelector('.bento-card--spotlight');
          const d = card.querySelector('.bento-card__drawer');
          const cs = getComputedStyle(d);
          const lis = card.querySelectorAll('.bento-card__drawer-items li');
          const chip = lis[0] ? getComputedStyle(lis[0]) : null;
          return {rows: cs.gridTemplateRows, opacity: cs.opacity,
                  chips: lis.length, chipBg: chip && chip.backgroundColor};
        }""")
    rows_px = float(b["rows"].replace("px", "")) if b["rows"].endswith("px") else 0
    check("B resting spotlight drawer open with cream chips",
          rows_px > 40 and float(b["opacity"]) > 0.9 and b["chips"] >= 3
          and b["chipBg"] == "rgb(250, 248, 244)",
          f"rows={b['rows']} opacity={b['opacity']} chips={b['chips']}")

    # ---- C. hover fallback = compact drawer on a tile -----------------
    page.evaluate(
        """() => { const s = document.getElementById('bento');
             (window.__lenis ? window.__lenis.scrollTo(s.offsetTop + 320, {duration: 0})
                             : window.scrollTo(0, s.offsetTop + 320)); }""")
    page.wait_for_timeout(900)
    xy = page.evaluate(
        """() => { const c = document.querySelectorAll(
                 '.bento-grid--shift .bento-card:not(.bento-card--spotlight)')[0];
             const r = c.getBoundingClientRect();
             return {x: r.x + r.width / 2, y: r.y + r.height / 2}; }""")
    page.mouse.move(xy["x"], xy["y"])
    page.wait_for_timeout(1300)
    c = page.evaluate(
        """() => {
          const cards = document.querySelectorAll('.bento-grid--shift .bento-card');
          for (const card of cards) {
            if (!card.matches(':hover')) continue;
            const d = card.querySelector('.bento-card__drawer');
            const items = card.querySelector('.bento-card__drawer-items');
            const cta = card.querySelector('.bento-card__drawer-cta');
            const cr = card.getBoundingClientRect();
            const ir = items.getBoundingClientRect();
            return {rows: getComputedStyle(d).gridTemplateRows,
                    wrap: getComputedStyle(items).flexWrap,
                    cta: getComputedStyle(cta).display,
                    rowH: Math.round(ir.height),
                    inside: ir.bottom <= cr.bottom + 0.5};
          }
          return null;
        }""")
    c_rows = float(c["rows"].replace("px", "")) if c and c["rows"].endswith("px") else -1
    check("C hovered tile opens the COMPACT drawer (one row, no CTA, inside card)",
          c is not None and c_rows > 30 and c["wrap"] == "nowrap"
          and c["cta"] == "none" and 24 < c["rowH"] < 48 and c["inside"],
          f"rows={c and c['rows']} wrap={c and c['wrap']} rowH={c and c['rowH']}")

    # ---- D. stagnant parallax lag -------------------------------------
    t1 = page.evaluate(
        """() => document.querySelector('.bento-flank--gabriel .bento-flank__word')
                   .style.transform || 'none'""")
    page.evaluate(
        """() => { const s = document.getElementById('bento');
             (window.__lenis ? window.__lenis.scrollTo(s.offsetTop + 920, {duration: 0})
                             : window.scrollTo(0, s.offsetTop + 920)); }""")
    page.wait_for_timeout(1700)
    t2 = page.evaluate(
        """() => document.querySelector('.bento-flank--gabriel .bento-flank__word')
                   .style.transform || 'none'""")

    def ty(t):
        try:
            return float(t.split("translate3d(0px,")[1].split("px")[0])
        except (IndexError, ValueError):
            return None

    y1, y2 = ty(t1), ty(t2)
    check("D parallax: the word lags the scroll (transform swings ≥40px)",
          y1 is not None and y2 is not None and abs(y2 - y1) >= 40,
          f"{t1} -> {t2}")

    # ---- E. mobile rail stays H3 --------------------------------------
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(900)
    e = page.evaluate(
        """() => ({
          drawer: getComputedStyle(document.querySelector('.bento-card--home .bento-card__drawer')).display,
          more: getComputedStyle(document.querySelector('.bento-card--home .bento-card__more')).display,
          flank: getComputedStyle(document.querySelector('.bento-flank')).display,
          rail: getComputedStyle(document.querySelector('.bento-grid--shift')).display,
        })""")
    check("E mobile 390px: drawer/more/flank hidden, H3 rail intact",
          e["drawer"] == "none" and e["more"] == "none"
          and e["flank"] == "none" and e["rail"] == "flex",
          f"{e}")

    browser.close()

print()
if failures:
    print(f"r44 E3: {len(failures)} FAILURES: {failures}")
    sys.exit(1)
print("r44 E3: ALL PASS (A flanks · B resting unpack · C compact hover · D parallax lag · E mobile rail)")
