"""L1 — map & list sync proving tests.

Binary checks (SCORECARD L1):
1. Owner layout kept: map shell on top, three market filter cards,
   alternating result rows (reverse class on even rows) — all frozen.
2. Two-way highlight: rows carry a stable identity (id + data-listing-pk),
   map data carries matching ids, and search-map.js wires
   row-hover → pin .is-hot and pin-activation → scroll to + .is-flashed row.
3. Keyboard operable: pins remain <button type="button"> with aria-labels
   (static), rows are links; the map region is focusable (tabindex="-1").
4. aria-live result count: #results-count is aria-live="polite" and the HTMX
   partial re-sends it out-of-band (hx-swap-oob) so filter changes announce.
5. Floating "Map" pill: [data-map-return] button in the template (hidden
   until JS proves the map left the viewport), styled in search.css.
6. Motion discipline: scroll behaviour reads html[data-fx] (D-LOOP-16a —
   fx-gate.js is the ONLY script allowed to mention prefers-reduced-motion);
   the flash animation is killed under reduced motion in CSS.
"""
import json
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
JS = (REPO / "static" / "js" / "search-map.js").read_text(encoding="utf-8")
# F5 (D-LOOP-29a): the fx-aware scroll helper that search-map.js routes through
INIT = (REPO / "static" / "js" / "smooth-scroll.js").read_text(encoding="utf-8")
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text(encoding="utf-8")

SEARCH_URL = "/property-for-sale/mombasa/"


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test (same isolation as test_detail)."""
    from django.core.cache import cache
    cache.clear()
    call_command("seed_demo", no_images=True, target=80, verbosity=0,
                 i_know_this_is_demo=True)
    yield


def _full_page() -> str:
    r = Client().get(SEARCH_URL)
    assert r.status_code == 200, f"{SEARCH_URL} -> {r.status_code}"
    return r.content.decode()


def _partial() -> str:
    r = Client().get(SEARCH_URL, HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    return r.content.decode()


# ---------------------------------------------------------------------------
# 1. the owner's layout is untouched
# ---------------------------------------------------------------------------
def test_owner_layout_untouched():
    html = _full_page()
    assert html.index('class="search-map-shell"') < html.index(
        'class="results-layout"'), "map must stay on top of the results"
    assert len(re.findall(r"market-filter__number", html)) == 3, (
        "exactly three market filter cards")
    assert "listing-row--reverse" in html, "alternating rows kept"


def test_rows_carry_identity():
    html = _full_page()
    rows = re.findall(
        r'<article class="listing-row[^"]*"\sid="listing-row-(\d+)"\s'
        r'data-listing-pk="\1"', html)
    assert len(rows) >= 2, (
        f"every listing row needs id=listing-row-<pk> + data-listing-pk "
        f"(found {len(rows)})")


# ---------------------------------------------------------------------------
# 2. the map data carries the same identities
# ---------------------------------------------------------------------------
def test_map_data_ids_unique_and_paired():
    html = _full_page()
    m = re.search(
        r'<script id="search-map-data" type="application/json">(.*?)</script>',
        html, re.S)
    assert m, "search-map-data json_script missing"
    data = json.loads(m.group(1))
    ids = [d.get("id") for d in data]
    assert data and all(isinstance(i, int) and i > 0 for i in ids), (
        f"every map listing needs a positive int id: {ids}")
    assert len(ids) == len(set(ids)), f"duplicate map ids: {ids}"
    row_pks = set(re.findall(r'data-listing-pk="(\d+)"', html))
    assert set(map(str, ids)) & row_pks, (
        "at least some map pins must pair with page-1 rows")


# ---------------------------------------------------------------------------
# 3. the JS wiring (static, per F2/F4 grep-test convention)
# ---------------------------------------------------------------------------
def test_pin_to_row_scroll_and_flash_wired():
    # F5 (D-LOOP-29a): programmatic scroll routes through the fx-aware
    # ghScrollTo helper (lenis under fx=rich, native otherwise) — the
    # behaviour contract (pin→row scroll + flash) is unchanged.
    for needle in ("dataset.listingPin", "listing-row-", "ghScrollTo",
                   "is-flashed", "'center'"):
        assert needle in JS, f"search-map.js missing pin→row wiring: {needle}"


def test_row_hover_highlights_pin():
    for needle in ("mouseover", "is-hot", "data-listing-pin",
                   "results-grid"):
        assert needle in JS, f"search-map.js missing row→pin wiring: {needle}"


def test_pins_stay_keyboard_buttons():
    assert "createElement('button')" in JS and "pin.type = 'button'" in JS, (
        "pins must remain real buttons (keyboard activable)")
    assert "aria-label" in JS, "pins must keep their aria-labels"


def test_scroll_respects_fx_gate():
    # F5 (D-LOOP-29a): fx awareness for programmatic scroll is centralised
    # in the ghScrollTo helper (static/js/smooth-scroll.js) — search-map.js
    # routes through it instead of reading html[data-fx] locally.
    assert "ghScrollTo" in JS, (
        "scroll behaviour must go through the fx-aware ghScrollTo helper")
    assert "data-fx" in INIT, (
        "the helper must read html[data-fx] (smooth only when the gate allows it)")
    assert "prefers-reduced-motion" not in JS and "prefers-reduced-motion" not in INIT, (
        "D-LOOP-16a: fx-gate.js is the only script allowed to mention "
        "prefers-reduced-motion")


# ---------------------------------------------------------------------------
# 4. aria-live result count (full page + HTMX oob)
# ---------------------------------------------------------------------------
def test_result_count_is_live_region():
    html = _full_page()
    assert re.search(
        r'<span class="results-header__count"\sid="results-count"\s'
        r'aria-live="polite"', html), (
        "the result count must be #results-count with aria-live=polite")


def test_htmx_partial_re_sends_count_oob():
    partial = _partial()
    assert 'hx-swap-oob="true"' in partial and 'id="results-count"' in partial, (
        "HTMX partial must re-send the count out-of-band so filter changes "
        "update the live region")


# ---------------------------------------------------------------------------
# 5. the floating Map pill
# ---------------------------------------------------------------------------
def test_map_return_pill_template_and_css():
    html = _full_page()
    assert re.search(
        r'<button[^>]*data-map-return[^>]*\bhidden\b', html), (
        "template must carry the hidden Map pill (JS reveals it)")
    assert ".map-return-pill" in SEARCH_CSS, (
        "search.css must style the Map pill")
    assert "IntersectionObserver" in JS and "data-map-return" in JS.replace(
        "'", '"') or "data-map-return" in JS, (
        "search-map.js must toggle the pill from map visibility")


# ---------------------------------------------------------------------------
# 6. motion discipline in CSS
# ---------------------------------------------------------------------------
def test_flash_animation_respects_reduced_motion():
    assert ".listing-row.is-flashed" in SEARCH_CSS, (
        "search.css must style the flashed row")
    rm = re.search(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{",
                   SEARCH_CSS)
    assert rm, "search.css needs a reduced-motion block for the flash"
    tail = SEARCH_CSS[rm.end():]
    assert "animation: none" in tail[:600], (
        "reduced-motion block must kill the flash animation")


def test_map_region_focusable():
    html = _full_page()
    assert re.search(r'<div id="search-map"[^>]*tabindex="-1"', html), (
        "the map container must be focusable so pin activation can move "
        "focus back to the map")
