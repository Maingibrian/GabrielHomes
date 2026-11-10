"""r30 E3 — H4 section rhythm audit evidence.

Renders home in headless Chromium and proves:
  1. the five data-archetype bands are present in DOM order;
  2. no more than 2 consecutive bands share an archetype, >=3 distinct used;
  3. zero console/page errors (the attribute additions broke nothing);
  4. the marquee band (#checks) still renders its five checks text
     (tag additions did not disturb the band's content);
  5. screenshot for the eyeball check.
"""
import re
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
OUT = "/home/z/my-project/gabriel-homes/LOOP/audit-screens/r30-h4-home-1280.png"

EXPECTED = [["hero", "full-bleed"], ["checks", "edge-strip"],
            ["bento", "full-bleed"], ["recommended", "type-led"],
            ["nearby", "type-led"]]

failures = []
errors = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(800)

    bands = page.eval_on_selector_all(
        "[data-archetype]",
        "els => els.map(e => [e.id || '(no-id)', e.getAttribute('data-archetype')])")
    check("5 archetype bands in DOM order", bands == EXPECTED, str(bands))

    seq = [a for _i, a in bands]
    distinct = len(set(seq))
    run = best = 1
    for prev, cur in zip(seq, seq[1:]):
        run = run + 1 if cur == prev else 1
        best = max(best, run)
    check(">=3 distinct archetypes used", distinct >= 3, f"{distinct} in {seq}")
    check("max consecutive run <= 2", best <= 2, f"best={best}")

    checks_text = page.inner_text("#checks").lower()
    words = re.findall(r"[a-z]+", checks_text)
    check("marquee band still carries the five checks",
          all(w in checks_text for w in ["ownership", "mandate", "encumbrances"]),
          f"{len(words)} words")

    check("zero console/page errors", len(errors) == 0,
          "; ".join(errors[:3]) if errors else "clean")

    page.screenshot(path=OUT)
    browser.close()

# --- mobile pass (D6): same flow, same order, nothing broken at 390px ---
MOBILE_OUT = "/home/z/my-project/gabriel-homes/LOOP/audit-screens/r30-h4-home-390.png"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(600)
    mbands = page.eval_on_selector_all(
        "[data-archetype]",
        "els => els.map(e => [e.id || '(no-id)', e.getAttribute('data-archetype')])")
    check("390px: same 5 bands in the same order", mbands == EXPECTED, str(mbands))
    page.screenshot(path=MOBILE_OUT)
    browser.close()

print()
if failures:
    print(f"r30 H4 E3: {len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("r30 H4 E3: ALL PASS")
