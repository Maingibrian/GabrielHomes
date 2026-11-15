"""r44 — the bento card unpacks + brand wordmarks flank the bento.

Owner request (r44): "the card on expansion should open some items
within it … i would like some creativity" and "on the left to have
gabriel on the top (but with a stagnant parallax effect) … on the
right bottom the word homes".

These tests pin:
  1. every showcase property card carries the drawer (+ the "+"
     affordance and the listing-type flag), the CTA tile and the
     five-check fallback cards stay plain;
  2. the drawer only renders when there is something real inside
     (amenities / size / parking / furnishing) — never an empty box;
  3. the drawer opens on every expansion state: the live spotlight
     promotion, the resting spotlight on load, the CSS-only hover
     and keyboard fallbacks — and stays OFF under 1021px (the H3
     carousel keeps tap-through cards);
  4. "gabriel"/"homes" flank the bento as decorative, gated
     wordmarks and the parallax script fails closed.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = REPO / "static" / "css" / "home.css"
FLANK_JS = REPO / "static" / "js" / "bento-flank.js"
HOME_HTML = REPO / "templates" / "core" / "home.html"


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test — keeps tests isolated via transaction rollback."""
    from django.core.cache import cache
    cache.clear()  # the home showcase is cached for 5 minutes
    call_command("seed_demo", no_images=True, target=20, verbosity=0, i_know_this_is_demo=True)
    yield
    cache.clear()


def _home_body() -> str:
    from django.core.cache import cache
    cache.clear()
    return Client().get("/").content.decode()


def _card_slice(body: str, marker: str) -> str:
    """The bento card <a> that contains `marker` (title text).
    r49: the hero card legitimately repeats the spotlight listing's
    title above the bento, so scope the lookup to the grid — the
    first title match may now live in the hero, not the bento."""
    grid = body.split('class="bento-grid bento-grid--shift"', 1)[1]
    i = grid.index(marker)
    start = grid.rindex('<a class="bento-card', 0, i)
    end = grid.index("</a>", i)
    return grid[start:end]


def test_showcase_cards_carry_the_unpack_drawer():
    """Every showcase property card has the flag chip, the "+" affordance
    and the drawer with its real content (amenities → chips, specs, the
    checked-first chip and the view CTA that closes the drawer)."""
    from apps.listings.models import Property

    body = _home_body()
    for fragment in (
        'class="bento-card__drawer"',
        'class="bento-card__drawer-inner"',
        'class="bento-card__drawer-label"',
        "Inside this home",
        'class="bento-card__drawer-items"',
        'class="bento-card__more"',
        'class="bento-card__flag"',
        "View this home",
        "Seen in person",
    ):
        assert fragment in body, f"home page missing drawer fragment: {fragment!r}"

    # The chips are REAL data: a featured demo listing's amenity renders.
    demo = (Property.objects.filter(is_demo=True, is_featured=True,
                                    status="published").first())
    assert demo is not None, "seed produced no featured demo listings"
    assert demo.amenities.exists(), "seed gave the demo listing no amenities"
    assert demo.amenities.first().name in body

    # Card and affordance render in pairs (the CTA tile has neither).
    assert body.count('class="bento-card__drawer"') == body.count('class="bento-card__more"')
    assert body.count('class="bento-card__drawer"') >= 1


def test_drawer_renders_only_when_there_is_something_inside():
    """A listing with no amenities, no size, no parking and nothing
    furnished gets the flag (listing type always exists) but never an
    empty drawer or a lying "+" affordance. Real inventory wins the
    bento, so a stocked sibling proves the guard is per-listing."""
    from apps.agents.models import AgencyProfile
    from apps.listings.models import Amenity, Property, PropertyType
    from apps.accounts.models import User

    seeded = Property.objects.filter(is_demo=True).first()
    user = User.objects.create_user(email="bare-agent@test.com", password="bare-pass-123")
    agency = AgencyProfile.objects.create(
        name="Bare agency", slug="bare-agency", is_demo=True, user=user)

    # 1) a stocked real listing — drawer expected
    stocked = Property.objects.create(
        title="Real stocked home with amenities",
        description="Plenty to unpack.",
        listing_type="sale",
        property_type=PropertyType.objects.first(),
        location=seeded.location, price="3000000",
        status="published", agent=agency, is_featured=True,
        size_sqm=180, parking_spaces=2, furnishing="furnished",
    )
    stocked.amenities.set(Amenity.objects.all()[:3])

    # 2) the bare one — newer, so it takes the resting spotlight slot
    Property.objects.create(
        title="Real bare home for the drawer guard",
        description="Nothing extra to unpack.",
        listing_type="sale",
        property_type=PropertyType.objects.first(),
        location=seeded.location, price="2000000",
        status="published", agent=agency, is_featured=True,
        # no amenities, no size_sqm, no parking, unfurnished
    )

    body = _home_body()
    card = _card_slice(body, "Real bare home for the drawer guard")
    assert 'class="bento-card__flag"' in card, "the listing-type flag is unconditional"
    assert "bento-card__drawer" not in card, "empty drawer must not render"
    assert "bento-card__more" not in card, "the '+' affordance must not render"

    # the stocked sibling (a plain tile behind the bare spotlight) unpacks
    stocked_card = _card_slice(body, "Real stocked home with amenities")
    assert 'class="bento-card__drawer"' in stocked_card
    assert stocked.amenities.first().name in stocked_card
    assert "180 m" in stocked_card and "2 parking" in stocked_card
    assert "Furnished" in stocked_card

    # the bare listing is the resting spotlight (newest real featured)
    assert "bento-card--spotlight" in card


def test_cta_tile_and_check_cards_stay_plain():
    """The closing BROWSE ALL tile (and the five-check fallback cards)
    never grow a drawer — the unpacking belongs to property cards."""
    body = _home_body()
    cta = _card_slice(body, "Every home, chosen for character.")
    assert "bento-card--cta" in cta
    assert "bento-card__drawer" not in cta
    assert "bento-card__more" not in cta


def test_drawer_opens_on_every_expansion_state():
    """CSS pins: the drawer opens with the spotlight promotion, with the
    resting spotlight on load, and with the CSS-only hover/keyboard
    fallbacks for when the shift grid is not live; under 1021px it is
    display:none so the H3 carousel cards stay tap-through."""
    css = HOME_CSS.read_text(encoding="utf-8")

    # collapsed-by-default, animated via grid rows (no max-height hacks)
    assert "grid-template-rows: 0fr" in css
    assert "grid-template-rows: 1fr" in css

    # open state 1 — the live promotion
    assert ".bento-grid--shift .bento-card.is-spot .bento-card__drawer" in css
    # open state 2 — the resting spotlight arrives unpacked
    assert ":not(.has-spot) .bento-card--spotlight .bento-card__drawer" in css
    # open states 3+4 — CSS-only fallbacks (JS off / lite / fx=none)
    assert ":not(.is-live) .bento-card:hover .bento-card__drawer" in css
    assert ":not(.is-live) .bento-card:focus-visible .bento-card__drawer" in css

    # the "+" affordance spins open with the same states
    assert ".bento-grid--shift .bento-card.is-spot .bento-card__more" in css

    # the fallback opens on one-row tiles compactly — label + a single
    # fading chip row, no CTA — so it never climbs over the title
    # (full drawer only where there is room: .is-spot / resting spotlight)
    assert ":not(.bento-card--spotlight):hover .bento-card__drawer-items" in css
    assert "flex-wrap: nowrap" in css
    assert ".bento-card__drawer-cta" in css.split("compact shape", 1)[1].split("}", 1)[0]

    # the chips stagger in (creativity pin): per-chip index + open delay
    assert "li:nth-child(2) { --i: 1; }" in css
    assert "transition-delay: calc(80ms + var(--i, 0) * 55ms)" in css

    # bright chips (r43's "don't make things dull" direction)
    drawer_items = css.split(".bento-card--home .bento-card__drawer-items li {", 1)[1]
    drawer_items = drawer_items.split("}", 1)[0]
    assert "background: var(--cream)" in drawer_items
    assert "color: var(--espresso)" in drawer_items

    # under 1021px the drawer and the affordance are gone — H3 intact
    hide_blocks = [m.group(0) for m in
                   re.finditer(r"@media \(max-width: 1020px\) \{[^}]*\}", css, re.S)]
    drawer_hide = [b for b in hide_blocks if "bento-card__drawer" in b]
    assert drawer_hide and "display: none" in drawer_hide[0], (
        "the mobile carousel must hide the drawer"
    )


def test_brand_wordmarks_flank_the_bento():
    """"gabriel" rides the left gutter from the top, "homes" the right
    gutter to the bottom — inside the showcase section, decorative
    (aria-hidden), one on each side of the grid."""
    body = _home_body()
    for fragment in (
        'class="bento-flank bento-flank--gabriel" aria-hidden="true"',
        'class="bento-flank bento-flank--homes" aria-hidden="true"',
        ">gabriel</span>",
        ">homes</span>",
    ):
        assert fragment in body, f"missing flank fragment: {fragment!r}"

    # on either side: gabriel before the grid, homes after it
    left = body.index("bento-flank--gabriel")
    grid = body.index("bento-grid--shift")
    right = body.index("bento-flank--homes")
    assert left < grid < right

    css = HOME_CSS.read_text(encoding="utf-8")
    flank_block = css.split("3e. r44", 1)[1].split("HOME v2", 1)[0]
    # book-spine vertical, display serif, in the ≥1440px gutters only
    assert "writing-mode: vertical-rl" in flank_block
    assert "font-family: var(--font-display)" in flank_block
    assert "(min-width: 1440px)" in flank_block
    assert "pointer-events: none" in flank_block
    # token-only colour (the hex ratchet holds in this block too)
    assert "#" not in flank_block
    # r45: the words are scaled to the GUTTER (owner: "much bigger") —
    # 40vw − 30rem tracks the wrapper-edge-to-viewport budget
    # (50vw − 38.5rem) so the type fills ~80% of the gutter at every
    # width it is shown at (96px @1440 → 288px @1920, capped at 20rem)
    # and can never run off the viewport edge.
    assert "font-size: clamp(3.75rem, 40vw - 30rem, 20rem)" in flank_block


def test_flank_words_are_animated_in_place_r94():
    """r94 (owner round eleven): the words are "alive in motion... not
    moving up or down". The r44 vertical parallax script is RETIRED
    from the page (its file stays for history but never loads); the
    motion is now the fx-gated r94-flank-breathe CSS animation, which
    never translates the words. The reduce block keeps its
    belt-and-braces pin."""
    # the parallax script no longer loads on the home page (comments
    # may mention it; a <script> tag must not)
    html = HOME_HTML.read_text(encoding="utf-8")
    assert '<script src="{% staticv \'js/bento-flank.js\' %}"' not in html, (
        "r94: the vertical word parallax script must not load")
    # bento-shift.js (desktop shape-shift) is untouched
    assert "js/bento-shift.js" in html

    css = HOME_CSS.read_text(encoding="utf-8")
    assert "r94-flank-breathe" in css, "the in-place animation must exist"
    assert re.search(
        r'html\[data-fx="rich"\][^{]*\.bento-flank__word[^{]*\{[^}]*'
        r'r94-flank-breathe', css), "it must be gated on data-fx=rich"
    # reduced motion still pins the words in CSS
    assert ".bento-flank__word { transform: none !important; }" in css
