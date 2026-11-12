"""r85 — deep jank probe for /properties/ (owner: "laggy... jerking motion").

Drives a realistic 12s wheel scroll through the listings band under 4x CPU
throttle (a mid-range laptop) and records, per configuration:

  - frame cadence (rAF deltas): avg fps, p95/p99 frame time, frames > 32ms
  - STALLS: frames where scrollY does not move while the wheel is still
    being sent (the perceptible "freeze"), and JUMPS: catch-up frames
    (> 1.5x the median delta right after a stall) — the "jerk"
  - longtasks (count, total ms, worst)
  - palm drift writes (--palms-y style mutations) and row-glide
    transitionrun events during the scroll
  - images: count + bytes of media images requested

Matrix (isolates each motion layer):
  A rich          — as shipped (fx gate lands rich; Lenis active)
  B none          — prefers-reduced-motion -> fx=none, nothing moves
  C rich-noPalms  — A + palm field ::before + sentinels display:none
  D rich-noGlides — A + row glide neutralised (rows render final state)
  E rich-tinyImg  — A + media images stubbed with a 1-col JPEG (decode off)
  F rich-clean    — C + D + E combined
  G rich-noLenis  — A + window.__lenis destroyed after load (native scroll)
"""
import json
import statistics
import time

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3000/properties/"
THROTTLE = 4  # x
WHEEL_NOTCHES = 200
WHEEL_DELTA = 100
WHEEL_GAP_MS = 60  # ~16 notches/s — steady human scrolling

INIT = """
window.__frames = [];
window.__rec = false;
window.__scroll = [];
(function loop(now) {
  if (window.__rec) {
    window.__frames.push(now);
    window.__scroll.push(window.scrollY);
  }
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
  const ds = [];
  for (let i = 1; i < s.length; i++) ds.push(s[i] - s[i - 1]);
  const med = ds.length ? [...ds].sort((a,b)=>a-b)[Math.floor(ds.length/2)] : 0;
  let stalls = 0, jumps = 0, stalled = false;
  for (const v of ds) {
    if (v === 0) { stalls++; stalled = true; }
    else if (stalled && v > Math.max(1.5 * med, med + 40)) { jumps++; stalled = false; }
    else stalled = false;
  }
  const q = (arr, p) => arr.length ? arr[Math.min(arr.length - 1, Math.floor(p * arr.length))] : 0;
  const sorted = [...d].sort((a,b)=>a-b);
  const imgs = performance.getEntriesByType("resource")
    .filter(r => r.name.includes("/media/property-images/"));
  const imgBytes = imgs.reduce((a, r) => a + (r.transferSize || 0), 0);
  return {
    dataFx: document.documentElement.getAttribute("data-fx"),
    lenis: !!window.__lenis,
    lenisSmooth: document.documentElement.classList.contains("lenis-smooth"),
    frames: n,
    avgMs: d.length ? +(d.reduce((a,b)=>a+b,0) / d.length).toFixed(1) : 0,
    p95Ms: q(sorted, 0.95),
    p99Ms: q(sorted, 0.99),
    over32: d.filter(x => x > 32).length,
    over50: d.filter(x => x > 50).length,
    over100: d.filter(x => x > 100).length,
    stalls, jumps,
    medScrollDelta: med,
    longtasks: window.__longtasks.length,
    longtaskMs: +window.__longtasks.reduce((a, b) => a + b[1], 0).toFixed(0),
    longtaskWorst: window.__longtasks.reduce((a, b) => Math.max(a, b[1]), 0),
    palmWrites: window.__palmWrites || 0,
    glideRuns: window.__glideRuns || 0,
    imgs: imgs.length,
    imgKB: Math.round(imgBytes / 1024),
    finalScrollY: Math.round(window.scrollY),
  };
}
"""

TINY_JPEG = None  # built once below


def build_tiny_jpeg():
    """A 760x520 single-colour JPEG (~12KB) — same box, trivial decode."""
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (760, 520), (216, 201, 184)).save(buf, "JPEG", quality=70)
    return buf.getvalue()


def run(playwright, name, reduced=False, hide_css="", no_glides=False,
        stub_images=False, kill_lenis=False):
    browser = playwright.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    cdp = ctx.new_cdp_session(page)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": THROTTLE})

    page.add_init_script(INIT)
    if reduced:
        page.emulate_media(reduced_motion="reduce")

    if stub_images:
        tiny = TINY_JPEG
        ctx.route("**/media/property-images/**",
                  lambda route: route.fulfill(content_type="image/jpeg", body=tiny))

    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)  # let deferred scripts + map settle

    if hide_css:
        page.add_style_tag(content=hide_css)
    if no_glides:
        page.add_style_tag(content=(
            ".listing-row.row-armed, .listing-row.is-slid {"
            " opacity: 1 !important; transform: none !important;"
            " transition: none !important; }"))
    if kill_lenis:
        page.evaluate("window.__lenis && window.__lenis.destroy()")

    # palm writes + glide counters, attached just before the scroll phase
    page.evaluate("""() => {
      window.__palmWrites = 0;
      const band = document.querySelector('.listings-band');
      if (band) new MutationObserver(() => window.__palmWrites++)
        .observe(band, { attributes: true, attributeFilter: ['style'] });
      window.__glideRuns = 0;
      document.addEventListener('transitionrun', (e) => {
        if (e.target.classList && e.target.classList.contains('listing-row')
            && e.propertyName === 'transform') window.__glideRuns++;
      }, true);
    }""")

    page.evaluate("window.__startRec()")
    for _ in range(WHEEL_NOTCHES):
        page.mouse.wheel(0, WHEEL_DELTA)
        page.wait_for_timeout(WHEEL_GAP_MS)
    page.wait_for_timeout(1200)  # let Lenis settle / finish chases
    page.evaluate("window.__stopRec()")

    rep = page.evaluate(REPORT)
    rep["config"] = name
    browser.close()
    return rep


def main():
    global TINY_JPEG
    TINY_JPEG = build_tiny_jpeg()
    palm_off = (".listings-band::before { display: none !important; }"
                " .palm-sentinel { display: none !important; }")
    runs = [
        ("A_rich", {}),
        ("B_none", {"reduced": True}),
        ("C_rich_noPalms", {"hide_css": palm_off}),
        ("D_rich_noGlides", {"no_glides": True}),
        ("E_rich_tinyImg", {"stub_images": True}),
        ("F_rich_clean", {"hide_css": palm_off, "no_glides": True,
                          "stub_images": True}),
        ("G_rich_noLenis", {"kill_lenis": True}),
    ]
    results = []
    with sync_playwright() as p:
        for name, kw in runs:
            t0 = time.time()
            rep = run(p, name, **kw)
            rep["wall_s"] = round(time.time() - t0, 1)
            results.append(rep)
            print(f"[{name}] fx={rep['dataFx']} lenis={rep['lenis']} "
                  f"avg={rep['avgMs']}ms p95={rep['p95Ms']} p99={rep['p99Ms']} "
                  f">32ms={rep['over32']} >50ms={rep['over50']} "
                  f"stalls={rep['stalls']} jumps={rep['jumps']} "
                  f"lt={rep['longtasks']}/{rep['longtaskMs']}ms "
                  f"palms={rep['palmWrites']} glides={rep['glideRuns']} "
                  f"img={rep['imgs']}x{rep['imgKB']}KB "
                  f"endY={rep['finalScrollY']}")
    with open("/home/z/my-project/scripts/r85_jank_results.json", "w") as fh:
        json.dump(results, fh, indent=1)
    print("saved r85_jank_results.json")


if __name__ == "__main__":
    main()
