"""r85 round 2 — which component of the palm field costs the frame?

A_rich was 58.9ms avg / 334 longtasks. C (field hidden) was 24.6ms.
Round 2 keeps the field visible but swaps one component at a time:

  H_rich_noMask   — field unmasked (hard cut, visually wrong, perf probe)
  I_rich_flatBg   — mask kept, tile swapped for a cheap CSS gradient
  J_rich_noMask_flatBg — neither (floor for "field present" cost)
  K_rich_stickyBox — ::before re-declared as viewport-sticky 100vh box,
                      mask kept (geometry probe: small box + mask)
"""
import json
import time

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000/properties/"
THROTTLE = 4
WHEEL_NOTCHES = 200
WHEEL_DELTA = 100
WHEEL_GAP_MS = 60

INIT = """
window.__frames = [];
window.__rec = false;
window.__scroll = [];
(function loop(now) {
  if (window.__rec) { window.__frames.push(now); window.__scroll.push(window.scrollY); }
  requestAnimationFrame(loop);
})();
window.__startRec = function () { window.__frames = []; window.__scroll = []; window.__rec = true; };
window.__stopRec = function () { window.__rec = false; };
window.__longtasks = [];
try {
  new PerformanceObserver(function (l) {
    for (const e of l.getEntries()) window.__longtasks.push([e.startTime, e.duration]);
  }).observe({ entryTypes: ["longtask"] });
} catch (err) {}
"""

REPORT = """
() => {
  const f = window.__frames, s = window.__scroll, n = f.length;
  const d = [];
  for (let i = 1; i < n; i++) d.push(f[i] - f[i - 1]);
  const sorted = [...d].sort((a,b)=>a-b);
  const q = (arr, p) => arr.length ? arr[Math.min(arr.length - 1, Math.floor(p * arr.length))] : 0;
  return {
    avgMs: d.length ? +(d.reduce((a,b)=>a+b,0) / d.length).toFixed(1) : 0,
    p95Ms: q(sorted, 0.95),
    over50: d.filter(x => x > 50).length,
    longtasks: window.__longtasks.length,
    longtaskMs: +window.__longtasks.reduce((a, b) => a + b[1], 0).toFixed(0),
    finalScrollY: Math.round(window.scrollY),
  };
}
"""

NO_MASK = (
    ".listings-band::before {"
    " -webkit-mask-image: none !important; mask-image: none !important; }"
)
FLAT_BG = (
    ".listings-band::before {"
    " background-image: linear-gradient(#cbb9a5, #b7a48e) !important; }"
)
STICKY_BOX = (
    ".listings-band::before {"
    " position: sticky !important;"
    " inset: 0 0 auto 0 !important;"
    " top: 0 !important;"
    " height: 100vh !important;"
    " margin-bottom: -100vh !important; }"
)


def run(playwright, name, css_overrides):
    browser = playwright.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    cdp = ctx.new_cdp_session(page)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": THROTTLE})
    page.add_init_script(INIT)
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    for css in css_overrides:
        page.add_style_tag(content=css)
    page.evaluate("window.__startRec()")
    for _ in range(WHEEL_NOTCHES):
        page.mouse.wheel(0, WHEEL_DELTA)
        page.wait_for_timeout(WHEEL_GAP_MS)
    page.wait_for_timeout(1200)
    page.evaluate("window.__stopRec()")
    rep = page.evaluate(REPORT)
    rep["config"] = name
    browser.close()
    return rep


def main():
    runs = [
        ("H_rich_noMask", [NO_MASK]),
        ("I_rich_flatBg", [FLAT_BG]),
        ("J_rich_noMask_flatBg", [NO_MASK, FLAT_BG]),
        ("K_rich_stickyBox", [STICKY_BOX]),
    ]
    results = []
    with sync_playwright() as p:
        for name, css in runs:
            t0 = time.time()
            rep = run(p, name, css)
            rep["wall_s"] = round(time.time() - t0, 1)
            results.append(rep)
            print(f"[{name}] avg={rep['avgMs']}ms p95={rep['p95Ms']} "
                  f">50ms={rep['over50']} lt={rep['longtasks']}/{rep['longtaskMs']}ms "
                  f"endY={rep['finalScrollY']}")
    with open("/home/z/my-project/scripts/r85_jank_results2.json", "w") as fh:
        json.dump(results, fh, indent=1)
    print("saved r85_jank_results2.json")


if __name__ == "__main__":
    main()
