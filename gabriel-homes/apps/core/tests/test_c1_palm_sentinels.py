"""C1 — coast palm sentinels proving tests (r60, owner round ten).

Owner ask: "on the white sides next to each listings generate a
coconut tree... it will be stagnant parallax up to the start of the
footer."

Binary checks:
1. SPAN — the results region of the listings page is wrapped in
   .listings-band, and the band covers exactly the listings stretch:
   the search-map shell is BEFORE it, the results header / tools /
   results grid / related searches are INSIDE it, and only the fixed
   filter drawer comes after — so the sticky palms release precisely
   when the footer arrives.
2. VEHICLE — two palm sentinels (left/right gutters), aria-hidden and
   pointer-events-none, each carrying one coconut-palm SVG on a sticky
   .palm-sentinel__stick. The palms are coconut palms: the markup
   carries fronds, trunk, ring notches, nut cluster AND fallen nuts.
3. GATE — sentinels are display:none by default and only shown
   >= 1620px (where the white sides are real); the sticker is
   position: sticky with a top offset (the stagnant-parallax engine).
4. TOKENS — every .palm-* fill class used by the markup resolves to a
   rule in search.css, and search.css still carries ZERO hex colours
   (D-LOOP-38a). The r62 wind is STRICTLY gated to
   html[data-fx="rich"]: reduced motion (fx=none), Save-Data (lite)
   and scripts blocked (no attribute — fails closed) all see the same
   palms, standing still; the stagnant-parallax placement itself is
   pure CSS and holds with JS off.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
PALMS = (REPO / "templates" / "listings" / "_palms.html").read_text(
    encoding="utf-8")
SEARCH_HTML = (REPO / "templates" / "listings" / "search.html").read_text(
    encoding="utf-8")
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text(
    encoding="utf-8")
GENERATOR = (REPO / "scripts" / "r60_gen_palms.py").read_text(
    encoding="utf-8")

SEARCH_URL = "/property-for-sale/mombasa/"


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test (same isolation as L1)."""
    from django.core.cache import cache
    cache.clear()
    call_command("seed_demo", no_images=True, target=12, verbosity=0,
                 i_know_this_is_demo=True)
    yield


@pytest.fixture()
def page():
    resp = Client().get(SEARCH_URL)
    assert resp.status_code == 200
    return resp.content.decode("utf-8")


# ---------------------------------------------------------------- span
def test_band_spans_exactly_the_listings_stretch(page):
    """Map shell before the band; header, tools, grid and related
    inside it; only the fixed filter drawer after — the palms anchor
    to the listings stretch and nothing else."""
    map_shell = page.index('class="search-map-shell"')
    band = page.index('class="listings-band"')
    header = page.index('class="results-header"')
    tools = page.index('class="container listing-tools"')
    grid = page.index('id="results-grid"')
    related = page.index('class="related"')
    drawer = page.index('class="filter-drawer"')
    assert map_shell < band < header < tools < grid < related < drawer
    # and in the template the band closes after the related section,
    # before the fixed filter drawer (comments render away, so the
    # closing marker is checked against the source)
    t_related = SEARCH_HTML.index('class="related"')
    t_close = SEARCH_HTML.index("{# /listings-band #}")
    t_drawer = SEARCH_HTML.index('class="filter-drawer"')
    assert t_related < t_close < t_drawer


def test_band_present_on_all_listing_variants():
    """The type/location variants share search.html, so sentinels ride
    along everywhere listings are listed."""
    for url in ("/properties/", "/houses-for-sale/mombasa/",
                "/flats-apartments-for-rent/"):
        resp = Client().get(url)
        assert resp.status_code == 200, url
        assert 'class="listings-band"' in resp.content.decode("utf-8"), url


# ------------------------------------------------------------- vehicle
def test_two_sentinels_each_carry_one_sticky_palm(page):
    assert page.count('class="palm-sentinel palm-sentinel--left"') == 1
    assert page.count('class="palm-sentinel palm-sentinel--right"') == 1
    assert page.count('class="palm-sentinel__stick"') == 2
    assert page.count('<svg class="palm-tree"') == 2


def test_sentinels_are_pure_decoration(page):
    """aria-hidden on both gutters, never focusable — zero
    accessibility surface (owner round nine)."""
    assert page.count('class="palm-sentinel palm-sentinel--left"'
                      ' aria-hidden="true"') == 1
    assert page.count('class="palm-sentinel palm-sentinel--right"'
                      ' aria-hidden="true"') == 1
    assert 'focusable="false"' in PALMS
    assert PALMS.count('role="presentation"') == 2


def test_the_trees_are_coconut_palms():
    """Fronds in three depth layers, a ringed trunk, a hanging nut
    cluster, fallen nuts on the mound — the markup proves the brief
    ("a coconut tree") without needing eyes."""
    for cls in ("palm-frond--back", "palm-frond--mid", "palm-frond--front",
                "palm-trunk", "palm-trunk-ring", "palm-boot", "palm-nut",
                "palm-nut--lit", "palm-nut-shadow", "palm-mound",
                "palm-mound--shade", "palm-grass"):
        assert f'class="{cls}"' in PALMS, cls
    assert PALMS.count("<use ") == 18          # 9 fronds x two trees
    assert PALMS.count('class="palm-nut"') == 10   # cluster + fallen, both trees


def test_mounds_share_one_ground_plane():
    """Both stickers render at the same width, so the two sand mounds
    bottom-align only when the viewBox aspects match (the right tree
    is crown-padded by the generator to make them equal — VLM round-4
    finding). Within 1% keeps the palms planted on one baseline."""
    boxes = re.findall(r'viewBox="0 0 (\d+) (\d+)"', PALMS)
    assert len(boxes) == 2
    aspects = [int(h) / int(w) for (w, h) in boxes]
    assert abs(aspects[0] - aspects[1]) / aspects[0] < 0.01


# ---------------------------------------------------------------- gate
def test_sentinels_gated_to_real_white_sides():
    """display:none by default, block only >= 1620px — and the palms
    can never intercept a pointer."""
    base = re.search(r"\.palm-sentinel\s*\{[^}]*\}", SEARCH_CSS).group(0)
    assert "display: none" in base
    assert "pointer-events: none" in base
    assert "position: absolute" in base
    gate = re.search(r"@media \(min-width: 1620px\)\s*\{[^}]*\}", SEARCH_CSS)
    assert gate and ".palm-sentinel { display: block; }" in gate.group(0)
    stick = re.search(r"\.palm-sentinel__stick\s*\{[^}]*\}", SEARCH_CSS)
    assert stick and "position: sticky" in stick.group(0)
    assert "top:" in stick.group(0)


def test_sentinels_keep_clear_of_the_content_column():
    """Anchored 18px outside the 1280px container box on both sides —
    the palms frame the listings, never sit under the text."""
    for side in ("--left", "--right"):
        rule = re.search(rf"\.palm-sentinel{side}\s*\{{[^}}]*\}}",
                         SEARCH_CSS).group(0)
        assert "calc(50% + (var(--container-max) / 2) + 18px)" in rule, side


def test_sentinels_stand_on_the_viewport_floor():
    """r62 (owner: "they need to constantly be in the bottom... no
    white space under them"): the sticky top pins the box BOTTOM on
    the viewport bottom edge — top + height = 100vh exactly (the same
    min(64vh, 660px) pair in both arms: 36vh + 64vh on shorter
    screens, (100vh - 660px) + 660px on tall ones) — so the palm
    stands on the floor of the screen at every scroll depth, never
    suspended mid-page, and still departs when the footer pushes the
    band end up. The svg stands on that floor (align-items:
    flex-end) and is sized WIDTH-first (width 100%, height auto,
    capped by the box) so it can never letterbox a gap underneath."""
    stick = re.search(r"\.palm-sentinel__stick\s*\{[^}]*\}", SEARCH_CSS)
    assert stick, "stick rule missing"
    body = stick.group(0)
    assert "position: sticky" in body
    assert "top: calc(100vh - min(64vh, 660px))" in body
    assert "height: min(64vh, 660px)" in body
    # floor arithmetic must stay a matched pair: top + height == 100vh
    assert body.count("min(64vh, 660px)") == 2
    assert "align-items: flex-end" in body
    assert "justify-content: center" in body
    tree = re.search(r"\.palm-tree\s*\{[^}]*\}", SEARCH_CSS).group(0)
    assert "width: 100%" in tree          # width-first: fills the gutter
    assert "height: auto" in tree         # height follows the viewBox
    assert "max-height: 100%" in tree     # capped by the sticky box


def test_mound_ink_sits_flush_on_the_floor():
    """The generator leaves NO bottom pad in the viewBox — the lowest
    ink (sand mound, fallen-nut contact shadows) lands exactly on the
    svg box floor, so no white strip can open under the tree on any
    screen width (the r61 bottom pad is what the owner saw as "white
    space under them")."""
    assert "h = max(ys) - min(ys) + pad + pad_top" in GENERATOR
    assert "h = max(ys) - min(ys) + 2 * pad" not in GENERATOR
    # and the shipped markup really carries the cropped boxes
    assert 'viewBox="0 0 317 597"' in PALMS
    assert 'viewBox="0 0 312 587"' in PALMS


def test_palms_hold_still_until_the_footer_covers_them():
    """r62 (VLM round: without this the trunk is "cut off at the
    footer's edge" — the palm visibly rides up the page). The sentinel
    columns extend one sticky-box height BELOW the band (under the
    footer's top edge), so the sticky release happens only once the
    footer has covered the trees outright: they never visibly move,
    the footer simply scrolls up over them, still."""
    base = re.search(r"\.palm-sentinel\s*\{[^}]*\}", SEARCH_CSS).group(0)
    assert "bottom: calc(-1 * min(64vh, 660px))" in base
    assert "bottom: 0" not in base


def test_grounding_shadow_is_token_only():
    """The grounded drop-shadow must come from the token palette,
    keeping search.css at zero hex."""
    tree = re.search(r"\.palm-tree\s*\{[^}]*\}", SEARCH_CSS).group(0)
    assert "drop-shadow" in tree
    assert "var(--taupe-35)" in tree


# --------------------------------------------------------------- tokens
def test_every_palm_class_is_styled_from_tokens():
    """Every .palm-* hook in the markup resolves to a rule in
    search.css — no path renders unstyled (black)."""
    used = set(re.findall(r'class="(palm-[a-z-]+)"', PALMS))
    used |= {"palm-tree"}
    assert used, "markup should carry palm classes"
    for cls in sorted(used):
        assert f".{cls}" in SEARCH_CSS, cls


def test_search_css_still_carries_zero_hex():
    """D-LOOP-38a: the palm colours are color-mix/var rules only."""
    assert not re.findall(r"#[0-9a-fA-F]{3,8}", SEARCH_CSS)


def test_wind_is_gated_to_rich():
    """r62 ("make them move in the wind"): the palm block carries a
    two-layer sway — but EVERY animation declaration sits inside a
    rule gated on html[data-fx="rich"] (D-FX-GATE contract). fx=none
    (reduced motion), lite (Save-Data) and scripts blocked (no
    attribute — fails closed) all get the same palms, standing still;
    the placement itself stays pure CSS."""
    block = SEARCH_CSS[SEARCH_CSS.index("r60 (owner round ten)"):]
    assert "@keyframes palm-sway" in block
    assert "@keyframes palm-flutter" in block
    for m in re.finditer(r"animation[a-z-]*\s*:", block):
        opener = block.rindex("{", 0, m.start())
        head = block[:opener]
        selector = head[max(head.rfind("}"), head.rfind(";")) + 1:]
        assert 'data-fx="rich"' in selector, (
            f"ungated animation in palm block: {selector.strip()!r}")


def test_wind_sways_around_the_base_out_of_lockstep():
    """The wind pivot is the base of the trunk (transform-origin at
    50% 100%), and the two trees run at different periods with
    negative delays — wind never moves two trees in lockstep."""
    tree = re.search(r"\.palm-tree\s*\{[^}]*\}", SEARCH_CSS).group(0)
    assert "transform-origin: 50% 100%" in tree
    block = SEARCH_CSS[SEARCH_CSS.index("r60 (owner round ten)"):]
    assert "animation: palm-sway 8.6s ease-in-out -2.4s infinite" in block
    assert "animation-duration: 10.2s" in block   # right tree: slower
    assert "animation-delay: -6.1s" in block       # and out of phase


def test_template_is_generator_owned():
    """_palms.html is machine-written (scripts/r60_gen_palms.py,
    seeds 60/61) — hand edits would be silently overwritten."""
    assert "Generated by scripts/r60_gen_palms.py" in PALMS
    assert "random.seed" not in PALMS          # no logic, pure markup
    for seed in ("seed=60", "seed=61"):
        assert seed in GENERATOR
