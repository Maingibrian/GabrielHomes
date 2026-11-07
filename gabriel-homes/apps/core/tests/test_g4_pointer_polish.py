"""G4 — pointer polish proving tests (r34).

Binary checks (SCORECARD G4): cursor "View" bubble on listing rows/cards
plus magnetic primary CTAs; fx=rich AND fine pointer AND hover only; hidden
for keyboard users; carries no information that exists only on hover.

Design notes pinned here:
  - the bubble element is JS-BUILT (no dead element without JS — D-MOTION-SAFE);
  - the bento cards are deliberately NOT bubble targets: M4 bento-shift
    already owns the pointer on that element (no stacking on one element);
  - "View" duplicates an existing link affordance (rows/cards are links) —
    the bubble is aria-hidden decoration, the information path is the link;
  - magnetic is transform-only, clamped, and never fires from keyboard
    focus (pointermove does not fire on focus).
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
MOTION_JS = REPO / "static" / "js" / "motion.js"
COMPONENTS_CSS = REPO / "static" / "css" / "components.css"
HOME_HTML = REPO / "templates" / "core" / "home.html"
HEADER_HTML = REPO / "templates" / "includes" / "_header.html"
DETAIL_HTML = REPO / "templates" / "listings" / "detail.html"
RESULTS_HTML = REPO / "templates" / "listings" / "_results_grid.html"
ADDENDUM = REPO / "docs" / "DESIGN-ADDENDUM.md"


def _js():
    return MOTION_JS.read_text(encoding="utf-8")


def _css():
    return COMPONENTS_CSS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. The gate: fx=rich AND fine pointer AND hover only
# ---------------------------------------------------------------------------
def test_pointer_polish_gate_rich_fine_hover():
    js = _js()
    assert "setupPointerPolish" in js, "motion.js must define setupPointerPolish"
    fn = js[js.index("function setupPointerPolish"):js.index("function init")]
    assert 'getAttribute("data-fx") !== "rich"' in fn or \
        'getAttribute("data-fx") === "rich"' in fn, \
        "the bubble and magnets must be fx=rich only"
    assert '(pointer: fine)' in fn, "fine pointer required"
    assert '(hover: hover)' in fn, "hover-capable device required"
    assert "matchMedia" in fn
    # wired into init()
    init = js[js.index("function init"):]
    assert "setupPointerPolish()" in init, "setupPointerPolish must be called from init()"


# ---------------------------------------------------------------------------
# 2. The bubble is JS-built, aria-hidden, pointer-transparent, "View"
# ---------------------------------------------------------------------------
def test_cursor_bubble_is_js_built_and_inert():
    js = _js()
    css = _css()
    fn = js[js.index("function setupPointerPolish"):]
    assert 'createElement("div")' in fn, "bubble must be JS-built (no dead element)"
    assert 'cursor-view' in fn and 'aria-hidden' in fn
    assert '"View"' in fn or "'View'" in fn, "bubble text must be View"
    assert 'textContent' in fn, "View must be set via textContent (no innerHTML)"
    # CSS: fixed, pointer-events none, transform-positioned (no layout shift)
    m = re.search(r"\.cursor-view\s*\{([^}]*)\}", css)
    assert m, ".cursor-view CSS block missing"
    block = m.group(1)
    assert re.search(r"position:\s*fixed", block)
    assert re.search(r"pointer-events:\s*none", block)
    assert re.search(r"transform:\s*translate\(", block), \
        "the bubble must be positioned via transform, not top/left"
    assert "cursor-view-on" in css, "a visibility class must toggle the bubble"


# ---------------------------------------------------------------------------
# 3. Targets: listing rows + nearby cards carry the hook; bento does not
# ---------------------------------------------------------------------------
def test_cursor_bubble_targets_rows_and_cards_not_bento():
    results = RESULTS_HTML.read_text(encoding="utf-8")
    home = HOME_HTML.read_text(encoding="utf-8")
    row = re.search(r'<article class="listing-row[^"]*"[^>]*>', results)
    assert row, "listing row article missing"
    assert "data-cursor-view" in row.group(0), "listing rows must carry data-cursor-view"
    card = re.search(r'<a class="nearby-card"[^>]*>', home)
    assert card, "nearby card anchor missing"
    assert "data-cursor-view" in card.group(0), "nearby cards must carry data-cursor-view"
    # deliberate exclusion: bento cards keep M4 bento-shift as the sole owner
    bento = re.search(r'class="bento-card bento-card--home[^"]*"', home)
    assert bento, "bento card missing"
    bento_tag = re.search(r"<a class=\"bento-card bento-card--home[^>]*>", home)
    if bento_tag:
        assert "data-cursor-view" not in bento_tag.group(0), \
            "bento cards must NOT carry the bubble (M4 bento-shift owns the pointer there)"


# ---------------------------------------------------------------------------
# 4. Magnetic primary CTAs: attribute present, transform-only, clamped
# ---------------------------------------------------------------------------
def test_magnetic_primary_ctas_transform_only():
    home = HOME_HTML.read_text(encoding="utf-8")
    header = HEADER_HTML.read_text(encoding="utf-8")
    detail = DETAIL_HTML.read_text(encoding="utf-8")
    submit = re.search(r'<button class="search-bar__submit"[^>]*>', home)
    assert submit and "data-magnetic" in submit.group(0), \
        "hero search submit must be magnetic"
    cta = re.search(r'<a class="btn btn--primary btn--sm site-header__cta"[^>]*>', header)
    assert cta and "data-magnetic" in cta.group(0), "the Enquire CTA must be magnetic"
    wa = re.search(r'<a class="agent-card-sticky__btn agent-card-sticky__btn--whatsapp"[^>]*>', detail)
    assert wa and "data-magnetic" in wa.group(0), \
        "the detail-page WhatsApp primary must be magnetic"
    js = _js()
    fn = js[js.index("function setupPointerPolish"):]
    assert "setProperty" in fn and "--mx" in fn and "--my" in fn, \
        "magnetic offset must flow through custom properties"
    assert "Math.max(" in fn and "Math.min(" in fn, \
        "the magnetic pull must be clamped (Math.max/Math.min)"
    assert "getBoundingClientRect" in fn
    # CSS: transform-only movement on the magnets, scoped under motion-ready
    css = _css()
    m = re.search(r"html\.motion-ready \[data-magnetic\]\s*\{([^}]*)\}", css)
    assert m, "magnetic CSS must be scoped under html.motion-ready (D-MOTION-SAFE)"
    block = m.group(1)
    assert re.search(r"transform:\s*translate\(var\(--mx", block)
    tr = re.search(r"transition:\s*([^;]+);", block)
    assert tr and "transform" in tr.group(1), "only transform may transition"


# ---------------------------------------------------------------------------
# 5. Keyboard hidden + no hover-only information
# ---------------------------------------------------------------------------
def test_no_hover_only_information_and_keyboard_hidden():
    results = RESULTS_HTML.read_text(encoding="utf-8")
    # the information path is the link itself: rows keep their title link
    assert re.search(r'<h2><a href="\{\{ property\.get_absolute_url \}\}">', results) or \
        re.search(r"<h2><a href=", results), "row title must stay a link"
    js = _js()
    fn = js[js.index("function setupPointerPolish"):js.index("function init")]
    # nothing fires on focus: only pointer events drive the bubble/magnets
    for event in fn.split("addEventListener")[1:]:
        head = event[:40]
        assert "focus" not in head, "G4 must not hook focus events (keyboard users)"
    assert "pointerenter" in fn and "pointerleave" in fn
    # the bubble is aria-hidden: assistive tech never sees decoration
    assert 'setAttribute("aria-hidden", "true")' in fn


# ---------------------------------------------------------------------------
# 6. Token hygiene in the new CSS block
# ---------------------------------------------------------------------------
def test_pointer_polish_css_uses_tokens_no_hex():
    css = _css()
    start = css.index("G4 pointer polish")
    block = css[start:css.index("=== 8.", start)] if "=== 8." in css[start:] else css[start:start + 2200]
    hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", block)
    assert not hexes, f"no raw hex in the G4 block: {hexes}"
    assert "var(--ink)" in block and "var(--paper)" in block, "bubble colours must be tokens"


# ---------------------------------------------------------------------------
# 7. Addendum mapping: M5 gains cursor-view, M6 gains magnetic (cap stays 6)
# ---------------------------------------------------------------------------
def test_addendum_maps_cursor_view_and_magnetic():
    text = ADDENDUM.read_text(encoding="utf-8")
    rows = re.findall(r"^\| M\d+\b", text, re.M)
    assert len(rows) <= 6, "the vocabulary cap must stay at 6 — no new rows"
    m5 = [r for r in text.splitlines() if r.startswith("| M5")][0]
    m6 = [r for r in text.splitlines() if r.startswith("| M6")][0]
    assert "data-cursor-view" in m5, "M5 confirm must document the cursor-view bubble"
    assert "data-magnetic" in m6, "M6 invite must document the magnetic CTAs"
    assert "bento" in (m5 + m6).lower(), "the bento exclusion must be documented"
