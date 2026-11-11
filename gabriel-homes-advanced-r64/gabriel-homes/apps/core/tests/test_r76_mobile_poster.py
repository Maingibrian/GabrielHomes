"""r76 — the mobile poster hero + mobile compaction proving tests.

Owner ask (owner round fourteen, the mobile audit): "audit the mobile
view of the website — one should not scroll to view data on the page"
and "the mobile hero should be different only — make it look like a
poster by a graphics design person."

Binary checks:
1. GUARD — the page-level horizontal guard lives in base.css (promoted
   from search.css's page-local rule): html gets overflow-x clip with
   a hidden fallback. Armed row slides, market-veil pseudos and
   marquee tracks may over-report scrollWidth, but no engine may ever
   open a sideways scroll.
2. PLATE — home.html carries the poster plate line (Mombasa / Kenyan
   coast), aria-hidden (decorative — the facts live in the subtitle),
   hidden at desktop sizes and composed below the print at <=809px
   with flanking hairlines.
3. POSTER — home.css re-lays the hero below 810px: the page goes
   cream with espresso text (the poster caption), .hero__bg becomes
   the framed print (in-flow, edge margins, card radius, overflow
   hidden), the chip bar is dropped, and the desktop hero's
   espresso/cream pairing stays the DEFAULT above 810px.
4. HEADER — the melt-into-hero transparent header (components.css)
   is retired below 810px ON THE HOME PAGE ONLY (:has(.hero)); the
   solid in-flow espresso bar returns so cream nav text never sits on
   the cream poster ground. Content pages (:has(.page-hero)) keep the
   overlay.
5. PLATE-SEARCH — the hero search pill re-lays as the three-row
   control plate at <=809px: segment / location / type+submit grid
   areas, labels visually hidden (13px floor intact — clip-path, not
   font-size), the submit an inset burnt pill.
6. COMPACT — search.css compacts the results page above the fold at
   <=809px: the market cards become a three-up tile row (no more
   82vw carousel, no negative margins), the map sheds height, the
   corner arrows stop colliding with the two-line titles, and the
   results header tightens — the first listing card lands inside the
   first phone screen.
7. TOKENS — home.css and search.css still carry zero hard-coded hex
   outside tokens.css (covered globally by F1, re-asserted here for
   the two touched sheets) and no sub-13px font sizes were added.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE = (REPO / "static" / "css" / "base.css").read_text(encoding="utf-8")
HOME = (REPO / "static" / "css" / "home.css").read_text(encoding="utf-8")
SEARCH = (REPO / "static" / "css" / "search.css").read_text(encoding="utf-8")
COMPONENTS = (REPO / "static" / "css" / "components.css").read_text(
    encoding="utf-8")
HOME_HTML = (REPO / "templates" / "core" / "home.html").read_text(
    encoding="utf-8")


def _block(text, start, end=None):
    """Slice a media-query block (or to EOF) out of a stylesheet."""
    i = text.find(start)
    assert i >= 0, f"marker {start!r} not found"
    if end is None:
        return text[i:]
    j = text.find(end, i)
    assert j >= 0, f"end marker {end!r} not found after {start!r}"
    return text[i:j]


# ---------------------------------------------------------------------------
# 1. the global horizontal guard
# ---------------------------------------------------------------------------
def test_base_css_carries_the_global_overflow_guard():
    guard = re.search(r"html \{ overflow-x: hidden; overflow-x: clip; \}", BASE)
    assert guard, (
        "base.css must carry the page-level horizontal guard "
        "(overflow-x: clip with a hidden fallback) — promoted from "
        "search.css in r76 so no page can ever open a sideways scroll"
    )
    # and the search.css page-local guard stays (it was first)
    assert "overflow-x: clip" in SEARCH


# ---------------------------------------------------------------------------
# 2. the poster plate
# ---------------------------------------------------------------------------
def test_plate_markup_is_present_and_aria_hidden():
    assert 'class="hero__poster-plate" aria-hidden="true"' in HOME_HTML, (
        "the poster plate line must exist in home.html and stay "
        "aria-hidden (decorative: the facts repeat elsewhere)"
    )
    assert "<span>Mombasa</span>" in HOME_HTML
    assert "<span>Kenyan coast</span>" in HOME_HTML


def test_plate_is_hidden_at_desktop_and_composed_below_810():
    # base rule hides it; only the <=809px block shows it
    assert re.search(r"\.hero__poster-plate \{ display: none; \}", HOME), (
        "the plate must be display:none at desktop sizes"
    )
    mobile = _block(HOME, "@media (max-width: 809px) {\n  /* the page, not a dark overlay",
                    "\n\n@media (max-width: 359px)")
    assert ".hero__poster-plate {" in mobile
    assert "display: flex" in mobile
    # flanking hairlines: the gallery plate rule
    assert re.search(r"\.hero__poster-plate::before,\s*\n?\s*\.hero__poster-plate::after",
                     mobile), "the plate needs its flanking hairline rules"


# ---------------------------------------------------------------------------
# 3. the poster layering
# ---------------------------------------------------------------------------
def test_poster_relayer_rules_exist_at_809():
    mobile = _block(HOME, "@media (max-width: 809px) {\n  /* the page, not a dark overlay",
                    "\n\n@media (max-width: 359px)")
    checks = {
        # the page, not a dark overlay
        "hero cream": r"\.hero \{[^}]*background: var\(--cream\)",
        "hero espresso text": r"\.hero \{[^}]*color: var\(--ink\)",
        # the framed print
        "bg in-flow": r"\.hero__bg \{[^}]*position: relative",
        "bg margins": r"\.hero__bg \{[^}]*margin: 0 16px",
        "bg radius": r"\.hero__bg \{[^}]*border-radius: var\(--radius-card\)",
        "bg clips": r"\.hero__bg \{[^}]*overflow: hidden",
        # the caption
        "title espresso": r"\.hero__title \{[^}]*color: var\(--espresso\)",
        "accent burnt": r"\.hero__title \.hero__accent \{ color: var\(--burnt\); \}",
        # the chip bar is dropped on the poster
        "assurances hidden": r"\.hero__assurances \{ display: none; \}",
    }
    for name, rx in checks.items():
        assert re.search(rx, mobile), f"poster block missing: {name}"


def test_desktop_hero_rules_survive_above_810():
    """The desktop hero contract stays the default: dark espresso hero,
    cream text, absolute full-bleed .hero__bg (the r50/r51 pins). The
    poster's cream/espresso overrides must live INSIDE the 809px block
    (their offsets sit after the block marker, not before it)."""
    assert re.search(r"\.hero \{[^}]*background: var\(--espresso\)", HOME)
    assert re.search(r"\.hero__bg \{[^}]*position: absolute", HOME)
    block_start = HOME.find("@media (max-width: 809px) {\n  /* the page, not a dark overlay")
    assert block_start > 0, "the r76 poster block is missing"
    before = HOME[:block_start]
    # the poster's text override must not appear before its block
    # (cream BACKGROUNDS legitimately exist earlier — .philosophy etc.;
    #  the hero's cream ground is asserted scoped by the F1-style block
    #  slice above instead)
    assert "color: var(--espresso)" not in before, (
        "an espresso text override leaked outside the mobile block"
    )


# ---------------------------------------------------------------------------
# 4. the header exception
# ---------------------------------------------------------------------------
def test_header_overlay_retires_below_810_on_home_only():
    m = re.search(
        r"@media \(max-width: 809px\) \{\s*\n\s*html\.motion-ready:has\(\.hero\) "
        r"\.site-header \{[^}]*position: sticky",
        COMPONENTS)
    assert m, (
        "below 810px the home page header must return to the solid "
        "in-flow bar (cream text must never sit on the cream poster)"
    )
    # content pages keep the overlay at every width
    assert "html.motion-ready:has(.page-hero) .site-header {" in COMPONENTS


# ---------------------------------------------------------------------------
# 5. the control plate
# ---------------------------------------------------------------------------
def test_search_pill_relays_as_control_plate():
    mobile = _block(HOME, "@media (max-width: 809px) {\n  /* the page, not a dark overlay",
                    "\n\n@media (max-width: 359px)")
    for needle in (
        '"seg  seg"', '"loc  loc"', '"type go"',
        "grid-area: seg", "grid-area: loc", "grid-area: type", "grid-area: go",
    ):
        assert needle in mobile, f"control plate missing {needle}"
    # the submit is an inset pill, not a flush cell
    assert re.search(r"\.hero \.search-bar__submit \{[^}]*margin: 9px", mobile)
    # labels are visually hidden via clip-path, never shrunk below the
    # 13px floor
    assert "clip-path: inset(50%)" in mobile


# ---------------------------------------------------------------------------
# 6. the results-page compaction
# ---------------------------------------------------------------------------
def test_search_page_compaction_at_809():
    compact = _block(SEARCH, "/* r76 — the mobile compaction",
                     "\n\n/* ---------- Empty state")
    assert "repeat(3, minmax(0, 1fr))" in compact, (
        "market cards must become a three-up tile row at phone widths"
    )
    assert "grid-auto-flow: row" in compact
    assert "overflow-x: visible" in compact, (
        "the 82vw carousel negative-margin strip must be retired"
    )
    assert "height: 205px" in compact, "the map sheds height on phones"
    assert re.search(r"\.market-filter__arrow \{ display: none; \}", compact), (
        "the corner arrow must stop colliding with the two-line titles"
    )
    assert "-webkit-line-clamp: 2" in compact, (
        "tile titles clamp to two lines"
    )
    assert ".results-header { padding-block: .55rem 1.1rem; }" in compact


def test_market_carousel_still_exists_for_tablet_810_plus():
    """The 800px carousel block stays for the widths between the two
    designs' overlap — r76 only overrides it below 810px (later in the
    file, so the compact block wins where both apply)."""
    assert "grid-auto-columns:82vw" in SEARCH


# ---------------------------------------------------------------------------
# 7. tokens: zero hex in the touched sheets, no sub-13px additions
# ---------------------------------------------------------------------------
def test_touched_blocks_stay_tokenised():
    """The r76 blocks themselves add zero hard-coded hex — the wider
    sheets carry legacy inline fallbacks (the F1 ratchet baseline);
    only the NEW rules are held to the zero-hex bar here."""
    poster = _block(HOME, "r76 — THE MOBILE POSTER HERO",
                    "/* r51: the search pill leans in 2px")
    compact = _block(SEARCH, "/* r76 — the mobile compaction",
                     "\n\n/* ---------- Empty state")
    guard = _block(BASE, "r76 (owner round fourteen — the mobile audit)",
                   "/* F5 (D-LOOP-29a)")
    header = _block(COMPONENTS, "r76 (owner round fourteen — the mobile poster hero)",
                    "/* G1: floating pill nav")
    for name, text in (("home.css r76 block", poster),
                       ("search.css r76 block", compact),
                       ("base.css guard", guard),
                       ("components.css header block", header)):
        hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", text)
        assert not hexes, f"{name} grew hard-coded hex: {hexes}"


def test_no_sub_floor_font_sizes_added():
    """The r76 blocks use tokens/rem only — the F1 floor stays intact
    (the legacy maplibre attribution sizes elsewhere in search.css are
    allowlisted by F1 and out of scope here)."""
    blocks = (
        _block(HOME, "r76 — THE MOBILE POSTER HERO",
               "/* r51: the search pill leans in 2px"),
        _block(SEARCH, "/* r76 — the mobile compaction",
               "\n\n/* ---------- Empty state"),
    )
    for text in blocks:
        for rx in (r"font-size\s*:\s*(\d+(?:\.\d+)?)px",
                   r"font\s*:[^;{}]*?(\d+(?:\.\d+)?)px"):
            for m in re.finditer(rx, text):
                assert float(m.group(1)) >= 13, (
                    f"r76 block has a sub-13px px font size: {m.group(0)}"
                )
