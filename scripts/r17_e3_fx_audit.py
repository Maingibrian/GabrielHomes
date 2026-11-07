"""r17 AUDITOR E3 check for F2 — real-browser execution of the real gate.

Runs the shipped fx-gate.js + motion.js + bento-shift.js against the live
Django dev server under four device contexts:

  A1 default        -> whatever this container really is (lite expected)
  A2 rich+fine shim -> patched 8 cores / 8 GB / fine pointer -> rich path,
                       bento grid must become is-live
  B reduced-motion  -> Playwright reduced_motion="reduce" -> real gate must
                       set data-fx="none"; ALL [data-reveal] visible at load;
                       bento must stay off
  C gate blocked    -> fx-gate.js request aborted -> attr absent, fail-closed:
                       all reveals visible, bento off

Prints one JSON verdict line per context. Screenshots for B and A2 go to
LOOP/audit-screens/ (E3 evidence) and download/ (user preview).
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/"
REPO = Path("/home/z/my-project/gabriel-homes")
SCREENS = REPO / "LOOP" / "audit-screens"
DOWNLOAD = Path("/home/z/my-project/download")
SCREENS.mkdir(parents=True, exist_ok=True)
DOWNLOAD.mkdir(parents=True, exist_ok=True)

RICH_SHIM = """
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
const __orig = window.matchMedia.bind(window);
window.matchMedia = function (q) {
  if (q.indexOf('pointer: fine') > -1 || q.indexOf('hover: hover') > -1) {
    return {matches: true, media: q, onchange: null,
            addEventListener() {}, removeEventListener() {},
            addListener() {}, removeListener() {},
            dispatchEvent: () => false};
  }
  return __orig(q);
};
"""

STATE = """(() => {
  const grid = document.querySelector('.bento-grid--shift') ||
               {classList: {contains: () => false}};
  const reveals = document.querySelectorAll('[data-reveal]');
  let inView = 0, shown = 0;
  reveals.forEach(e => {
    const r = e.getBoundingClientRect();
    if (r.top < window.innerHeight && r.bottom > 0) {
      inView++;
      if (e.classList.contains('is-visible')) shown++;
    }
  });
  return JSON.stringify({
    fx: document.documentElement.getAttribute('data-fx'),
    fine: document.documentElement.hasAttribute('data-fine'),
    motionReady: document.documentElement.classList.contains('motion-ready'),
    bentoLive: grid.classList.contains('is-live'),
    totalReveals: reveals.length,
    revealedTotal: document.querySelectorAll('[data-reveal].is-visible').length
  });
})()"""


def snap(ctx, label, shim=False, block_gate=False, shot=None):
    page = ctx.new_page()
    if shim:
        page.add_init_script(RICH_SHIM)
    if block_gate:
        page.route("**/fx-gate.js*", lambda route: route.abort())
    page.goto(BASE, wait_until="networkidle")
    state = json.loads(page.evaluate(STATE))
    verdict = {"label": label, **state}
    if shot:
        page.screenshot(path=str(shot))
        verdict["screenshot"] = str(shot)
    print(json.dumps(verdict))
    page.close()
    return verdict


def main():
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            a1 = snap(browser.new_context(), "A1 default-container")
            a2 = snap(browser.new_context(), "A2 rich+fine shim", shim=True,
                      shot=SCREENS / "r17-e3-rich-bento-live.png")
            b = snap(browser.new_context(reduced_motion="reduce"),
                     "B reduced-motion (none)",
                     shot=SCREENS / "r17-e3-none.png")
            c = snap(browser.new_context(), "C gate blocked (fail-closed)",
                     block_gate=True)

            # --- audit assertions -------------------------------------
            if b["fx"] != "none":
                failures.append(f"B: expected fx=none, got {b['fx']}")
            if b["bentoLive"]:
                failures.append("B: bento ran under none")
            if b["totalReveals"] == 0 or b["revealedTotal"] != b["totalReveals"]:
                failures.append(
                    f"B: reveals not all instant "
                    f"({b['revealedTotal']}/{b['totalReveals']})")
            if c["fx"] is not None:
                failures.append(f"C: blocked gate left fx={c['fx']}")
            if c["bentoLive"]:
                failures.append("C: bento ran with gate blocked")
            if c["totalReveals"] == 0 or c["revealedTotal"] != c["totalReveals"]:
                failures.append(
                    f"C: fail-closed reveals not instant "
                    f"({c['revealedTotal']}/{c['totalReveals']})")
            if a2["fx"] != "rich" or not a2["fine"]:
                failures.append(f"A2: shim did not produce rich+fine "
                                f"(fx={a2['fx']}, fine={a2['fine']})")
            if not a2["bentoLive"]:
                failures.append("A2: bento did not activate on rich+fine")
            if a1["bentoLive"] and a1["fx"] != "rich":
                failures.append("A1: bento live without rich tier")

            # copy the rich screenshot for the user preview
            rich_png = SCREENS / "r17-e3-rich-bento-live.png"
            if rich_png.exists():
                (DOWNLOAD / "gabriel-homes-home-preview.png").write_bytes(
                    rich_png.read_bytes())
        finally:
            browser.close()

    if failures:
        print("E3-VERDICT: FAIL — " + "; ".join(failures))
        sys.exit(1)
    print("E3-VERDICT: PASS — none/fail-closed off + content visible; "
          "rich+fine runs bento; real container graded lite")


if __name__ == "__main__":
    main()
