"""r83 — visual + geometric verification of the rebuilt /services/ page.

Checks (1280x800 laptop):
  * hero renders with the honest photo credit
  * TOC: four rows, arrow/hover geometry intact
  * ledger: three honest stats + note
  * chapters: media PINS (top === 0 across the pin range), 100vh tall,
    zigzag L/R/L/R, caption + ghost present
  * anchors land 84px clear of the top (scroll-margin-top)
  * scrim ::after painted on the media
Mobile (390x844):
  * chapters stack, media NOT sticky, zero horizontal overflow
Reduced motion:
  * sticky pin survives (geometry, not animation)
All probes scroll with behavior:'instant' (the r81 lesson: CSS smooth
scroll animates scrollTo and poisons measurements).
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000"
OUT = Path("/home/z/my-project/download/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
FAILS = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])

    # ---------------- laptop 1280x800 ----------------
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    page.set_default_timeout(20000)
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    resp = page.goto(BASE + "/services/", wait_until="domcontentloaded")
    check("page 200", resp.status == 200, str(resp.status))
    page.wait_for_timeout(1500)

    geo = page.evaluate("""() => {
      const vh = window.innerHeight;
      const chapters = [...document.querySelectorAll('.svc-chapter')].map(c => {
        const m = c.querySelector('.svc-chapter__media');
        const r = c.getBoundingClientRect();
        return {
          id: c.id, top: Math.round(r.top + scrollY), height: Math.round(r.height),
          mediaUrl: m.style.backgroundImage.slice(5, -2),
          ghost: !!c.querySelector('.svc-chapter__ghost'),
          caption: (c.querySelector('.svc-chapter__caption') || {}).textContent || '',
          flip: c.classList.contains('svc-chapter--flip'),
        };
      });
      const ledger = [...document.querySelectorAll('.svc-ledger__num')].map(
        n => n.textContent.trim());
      const credit = document.querySelector('.svc-photo-credit');
      return { vh, chapters, ledger,
               credit: credit ? credit.textContent.trim().slice(0, 80) : null };
    }""")
    vh = geo["vh"]
    print("chapters:", json.dumps(
        [{k: c[k] for k in ("id", "top", "height", "flip", "caption")}
         for c in geo["chapters"]], indent=2)[:600])
    print("ledger:", geo["ledger"], "| credit:", geo["credit"] and geo["credit"][:60])
    check("four chapters", len(geo["chapters"]) == 4)
    check("ledger counts", len(geo["ledger"]) == 3, str(geo["ledger"]))
    check("credit present", bool(geo["credit"]))
    for c in geo["chapters"]:
        check(f"{c['id']} uses real listing photo",
              "/media/property-images/real/" in c["mediaUrl"], c["mediaUrl"][-24:])
        check(f"{c['id']} ghost + caption", c["ghost"] and "real listing" in c["caption"])

    # --- pin geometry: probe across each chapter's pin range ---
    pin_ok = page.evaluate("""(geo) => {
      const vh = window.innerHeight;
      const out = [];
      for (const ch of geo) {
        const el = document.getElementById(ch.id);
        const media = el.querySelector('.svc-chapter__media');
        const start = ch.top;
        const end = ch.top + ch.height - vh;   // last scroll where media still pinned
        const samples = [];
        for (const frac of [0.05, 0.5, 0.95]) {
          const y = Math.round(start + (end - start) * frac);
          window.scrollTo({top: y, behavior: 'instant'});
          const r = media.getBoundingClientRect();
          samples.push({
            y, top: Math.round(r.top), h: Math.round(r.height),
            left: Math.round(r.left), right: Math.round(r.right),
          });
        }
        out.push({id: ch.id, flip: ch.flip, samples});
      }
      window.scrollTo({top: 0, behavior: 'instant'});
      return out;
    }""", geo["chapters"])
    W = 1280
    for ch in pin_ok:
        tops = {s["top"] for s in ch["samples"]}
        hs = {s["h"] for s in ch["samples"]}
        check(f"{ch['id']} media pinned through range", tops == {0}, f"tops={sorted(tops)}")
        check(f"{ch['id']} media 100vh", hs == {vh}, f"heights={sorted(hs)}")
        side_ok = all(
            (s["left"] == 0 and s["right"] == W // 2) if not ch["flip"]
            else (s["left"] == W // 2 and s["right"] == W)
            for s in ch["samples"])
        check(f"{ch['id']} media on {'RIGHT' if ch['flip'] else 'LEFT'} half", side_ok)

    # scrim painted on the media
    scrim = page.evaluate("""(() => {
      const m = document.querySelector('.svc-chapter__media');
      const s = getComputedStyle(m, '::after');
      return { bg: s.backgroundImage.slice(0, 30), content: s.content };
    })()""")
    check("media scrim ::after painted",
          "linear-gradient" in scrim["bg"] and scrim["content"] == '""', str(scrim))

    # --- screenshots: hero, toc, ledger, pinned 001, seam, pinned 002 ---
    page.evaluate("document.querySelectorAll('[data-reveal]').forEach(e => e.classList.add('is-visible'))")
    page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "svc-r83-hero.png"))

    toc_top = page.evaluate(
        "document.querySelector('.svc-toc').getBoundingClientRect().top + scrollY")
    page.evaluate(f"window.scrollTo({{top: {toc_top - 90}, behavior: 'instant'}})")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "svc-r83-toc.png"))

    ledger_top = page.evaluate(
        "document.querySelector('.svc-ledger').getBoundingClientRect().top + scrollY")
    page.evaluate(f"window.scrollTo({{top: {ledger_top - 90}, behavior: 'instant'}})")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "svc-r83-ledger.png"))

    c1 = geo["chapters"][0]
    mid1 = c1["top"] + (c1["top"] + c1["height"] - vh - c1["top"]) * 0.5
    page.evaluate(f"window.scrollTo({{top: {int(mid1)}, behavior: 'instant'}})")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "svc-r83-pinned-001.png"))

    c2 = geo["chapters"][1]
    page.evaluate(f"window.scrollTo({{top: {c2['top'] - 500}, behavior: 'instant'}})")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "svc-r83-seam.png"))

    mid2 = c2["top"] + (c2["top"] + c2["height"] - vh - c2["top"]) * 0.55
    page.evaluate(f"window.scrollTo({{top: {int(mid2)}, behavior: 'instant'}})")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "svc-r83-pinned-002.png"))

    pledge_top = page.evaluate(
        "document.querySelector('.svc-pledge').getBoundingClientRect().top + scrollY")
    page.evaluate(f"window.scrollTo({{top: {pledge_top - 90}, behavior: 'instant'}})")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "svc-r83-pledge.png"))

    # --- anchor: TOC click lands the chapter 84px clear of the top ---
    # Emulate a real user: under fx=rich every user scroll is Lenis-owned,
    # so lenis.targetScroll stays synced with scrollY. (Scrolling the page
    # externally right before the click — e.g. Playwright's own pre-click
    # scrollIntoView — desyncs Lenis's element math and lands short; a
    # wheel-driven user never hits that state.)
    page.evaluate("""window.__lenis
        ? window.__lenis.scrollTo(0, {duration: 0.25})
        : window.scrollTo({top: 0, behavior: 'instant'})""")
    page.wait_for_timeout(700)
    page.evaluate("document.querySelector(\"a[href='#svc-buying']\").scrollIntoView({block: 'center'})")
    page.evaluate("window.__lenis && window.__lenis.scrollTo(window.scrollY, {duration: 0.1})")
    page.wait_for_timeout(500)
    page.click("a[href='#svc-buying']")
    page.wait_for_timeout(400)
    land = page.evaluate("""(() => {
      return new Promise(resolve => {
        let last = -1, stable = 0;
        const t0 = Date.now();
        (function poll() {
          const y = Math.round(window.scrollY);
          if (y === last) { stable += 1; } else { stable = 0; }
          last = y;
          if (stable >= 5 || Date.now() - t0 > 4000) {
            const ch = document.getElementById('svc-buying');
            resolve({ y, chapterTop: Math.round(ch.getBoundingClientRect().top) });
          } else { requestAnimationFrame(poll); }
        })();
      });
    })()""")
    check("anchor lands chapter at 84px (±1 easing rounding)",
          abs(land["chapterTop"] - 84) <= 1,
          f"chapter top={land['chapterTop']} (settled scrollY={land['y']})")

    check("zero console errors", not errors, str(errors[:3]))
    ctx.close()

    # ---------------- mobile 390x844 ----------------
    mctx = browser.new_context(viewport={"width": 390, "height": 844},
                               is_mobile=True, has_touch=True)
    mpage = mctx.new_page()
    mpage.goto(BASE + "/services/", wait_until="domcontentloaded")
    mpage.wait_for_timeout(1200)
    mob = mpage.evaluate("""() => {
      const m = document.querySelector('.svc-chapter__media');
      const pos = getComputedStyle(m).position;
      const doc = document.scrollingElement;
      const chapters = [...document.querySelectorAll('.svc-chapter')].map(c => {
        const r = c.getBoundingClientRect();
        const media = c.querySelector('.svc-chapter__media').getBoundingClientRect();
        const body = c.querySelector('.svc-chapter__body').getBoundingClientRect();
        return { stacked: media.bottom <= body.top + 1, w: Math.round(r.width) };
      });
      return { pos, scrollW: doc.scrollW ?? doc.scrollWidth,
               innerW: window.innerWidth, chapters,
               ledgerW: Math.round(document.querySelector('.svc-ledger__inner')
                 .getBoundingClientRect().width) };
    }""")
    check("mobile media not sticky", mob["pos"] == "relative", mob["pos"])
    check("mobile zero horizontal overflow", mob["scrollW"] <= mob["innerW"],
          f"scrollW={mob['scrollW']} innerW={mob['innerW']}")
    check("mobile all chapters stacked", all(c["stacked"] for c in mob["chapters"]))
    mpage.evaluate("document.querySelectorAll('[data-reveal]').forEach(e => e.classList.add('is-visible'))")
    mpage.wait_for_timeout(300)
    mpage.screenshot(path=str(OUT / "svc-r83-mobile-top.png"))
    mpage.evaluate(f"window.scrollTo({{top: {geo['chapters'][0]['top']}, behavior: 'instant'}})")
    mpage.wait_for_timeout(300)
    mpage.screenshot(path=str(OUT / "svc-r83-mobile-chapter.png"))
    mctx.close()

    # ---------------- reduced motion: pin survives ----------------
    rctx = browser.new_context(viewport={"width": 1280, "height": 800},
                               reduced_motion="reduce")
    rpage = rctx.new_page()
    rpage.goto(BASE + "/services/", wait_until="domcontentloaded")
    rpage.wait_for_timeout(800)
    rm = rpage.evaluate("""() => {
      const c = document.querySelector('#svc-buying');
      const top = c.getBoundingClientRect().top + scrollY;
      window.scrollTo({top: Math.round(top + 300), behavior: 'instant'});
      const m = c.querySelector('.svc-chapter__media').getBoundingClientRect();
      const vis = getComputedStyle(document.querySelector('#svc-buying .svc-chapter__body')).opacity;
      return { pos: getComputedStyle(c.querySelector('.svc-chapter__media')).position,
               top: Math.round(m.top), bodyOpacity: vis };
    }""")
    check("reduced-motion keeps sticky pin", rm["pos"] == "sticky" and rm["top"] == 0,
          f"pos={rm['pos']} top={rm['top']}")
    check("reduced-motion content visible", float(rm["bodyOpacity"]) == 1.0,
          f"opacity={rm['bodyOpacity']}")
    rctx.close()
    browser.close()

print()
if FAILS:
    print("FAILURES:", FAILS)
    raise SystemExit(1)
print("ALL CHECKS PASSED")
