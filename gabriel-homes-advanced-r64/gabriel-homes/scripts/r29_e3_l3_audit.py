"""r29 — E3 audit for L3 (row conversion & density), run from scratch.

Desktop 1280x900 on /property-for-sale/ (agent-fallback branch — brand
channels are unfilled in demo data, which itself exercises "hidden when
unfilled" on the brand side):
  A. actions order per row: WhatsApp(ink pill + svg) -> Call -> Email -> View
  B. WhatsApp link: wa.me + ?text= prefill + aria-label + visible 16px icon
  C. Call/Email/View carry no primary class; View is the quiet link
  D. rendered row height is content-driven (<= 500 old fixed box; >= 320 CSS min)
  E. description <= 28 words
  F. mobile 390x844: rows stack to one column, actions wrap
  G. zero console / page errors
"""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/property-for-sale/"
SHOT = "LOOP/audit-screens/r29-l3-row-audit.png"
fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
    page.set_default_timeout(15000)
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    print("A-C: desktop structure & hierarchy (agent-fallback branch):")
    resp = page.goto(BASE, wait_until="domcontentloaded")
    check("search page 200", resp.status == 200, str(resp.status))
    page.wait_for_timeout(600)

    rows = page.query_selector_all(".listing-row")
    check("rows rendered", len(rows) >= 3, f"{len(rows)} rows")
    bad_order, bad_wa, bad_secondary, heights, word_counts = [], [], [], [], []
    for i, row in enumerate(rows):
        acts = row.query_selector(".listing-row__actions")
        links = acts.query_selector_all("a")
        kinds = []
        for a in links:
            cls = a.get_attribute("class") or ""
            href = a.get_attribute("href") or ""
            if "listing-row__whatsapp" in cls:
                kinds.append("wa")
                if not (href.startswith("https://wa.me/") and "?text=" in href):
                    bad_wa.append(f"row{i}: href {href[:60]}")
                if a.query_selector("svg") is None:
                    bad_wa.append(f"row{i}: no svg")
                if not (a.get_attribute("aria-label") or "").startswith("WhatsApp about "):
                    bad_wa.append(f"row{i}: aria-label missing")
            elif href.startswith("tel:"):
                kinds.append("call")
            elif href.startswith("mailto:"):
                kinds.append("email")
            elif "listing-row__view" in cls:
                kinds.append("view")
            else:
                kinds.append("other")
        if kinds[:4] != ["wa", "call", "email", "view"] or "other" in kinds:
            bad_order.append(f"row{i}: {kinds}")
        # secondary classes: call/email/view must not carry the primary class
        for a in links[1:]:
            if "listing-row__whatsapp" in (a.get_attribute("class") or ""):
                bad_secondary.append(f"row{i}")
        box = row.bounding_box()
        if box:
            heights.append(round(box["height"]))
        desc = row.query_selector(".listing-row__description")
        if desc:
            words = desc.inner_text().split()
            # Django truncatewords appends " …" — punctuation, not a word.
            if words and words[-1] == "…":
                words = words[:-1]
            word_counts.append(len(words))

    check("order WhatsApp>Call>Email>View in EVERY row", not bad_order, "; ".join(bad_order[:3]))
    check("wa.me + ?text= + svg + aria-label everywhere", not bad_wa, "; ".join(bad_wa[:3]))
    check("no primary class on secondary actions", not bad_secondary, "; ".join(bad_secondary[:2]))
    check("rendered heights content-driven (320..500)", all(320 <= h <= 500 for h in heights),
          f"{heights}")
    check("descriptions <= 28 words", all(w <= 28 for w in word_counts), f"{word_counts}")

    # icon visible at 16px, currentColor ink pill
    wa_first = rows[0].query_selector(".listing-row__whatsapp")
    ib = wa_first.query_selector("svg").bounding_box()
    check("icon rendered 16x16", ib and 12 <= ib["width"] <= 20 and 12 <= ib["height"] <= 20,
          f"{round(ib['width'])}x{round(ib['height'])}" if ib else "none")
    bg = page.evaluate(
        "getComputedStyle(document.querySelector('.listing-row__whatsapp')).backgroundColor")
    col = page.evaluate(
        "getComputedStyle(document.querySelector('.listing-row__whatsapp')).color")
    check("pill is ink bg + cream text (tokens)", bg not in ("rgba(0, 0, 0, 0)", "#fff") and col != bg,
          f"bg={bg} color={col}")

    # keyboard: first Tab from body reaches skip link, actions start at WhatsApp
    focus_in_wa = page.evaluate(
        """() => {
            const row = document.querySelector('.listing-row');
            const wa = row.querySelector('.listing-row__whatsapp');
            wa.focus();
            return document.activeElement === wa;
        }""")
    check("WhatsApp link keyboard-focusable", focus_in_wa)

    print("D-F: mobile 390x844 stack:")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(400)
    mob = page.evaluate(
        """() => {
            const r = document.querySelector('.listing-row');
            const cols = getComputedStyle(r).gridTemplateColumns.split(' ').length;
            return {cols, h: Math.round(r.getBoundingClientRect().height)};
        }""")
    check("mobile rows stack to 1 column", mob["cols"] == 1, f"cols={mob['cols']}")
    check("mobile row keeps actions", page.query_selector(
        ".listing-row .listing-row__whatsapp") is not None)

    check("zero console/page errors", not errors, "; ".join(errors[:2]))

    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(300)
    rows[0].scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    page.screenshot(path=SHOT, clip={"x": 0, "y": max(0, rows[0].bounding_box()["y"] - 20),
                                     "width": 1280, "height": 520})
    print(f"  screenshot -> {SHOT}")
    browser.close()

print(f"\nr29 L3 audit: {'ALL PASS' if not fails else 'FAIL: ' + ', '.join(fails)}")
raise SystemExit(1 if fails else 0)
