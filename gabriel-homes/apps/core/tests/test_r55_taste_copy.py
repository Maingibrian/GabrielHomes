"""r55 — taste-led language + card-wipe round (owner round six).

Three owner asks drive this revision:

1. "THE ABOUT PAGE STILL LOOKS BAD — USE VISION" — a fresh vision pass
   (scroll-through viewport captures, not full-page ghosts) found real
   defects: the story column dead zone, the quote band stretched with an
   orphaned eyebrow, ragged value-card baselines, a 170px founder caption
   breaking the 390px grid, a construction-site aerial in the proof
   triptych, and low-contrast footer/CTA microtext.
2. "WIPE THE CARDS OUT AND USE ONLINE STOCK IMAGES" — the demo-photo
   pools (media/demo-photos/*) were lost in a workspace recycle, so bulk
   listings had fallen back to Pillow gradient cards. scripts/
   install-stock-pools.py + scripts/r54_wipe_cards.py reinstall real
   photos in place (same filenames — URLs stable).
3. "THE LANGUAGE SHOULD BE ABOUT TASTE AND UNIQUE COASTAL HOMES — LESS
   ABOUT CHECKED AND VERIFIED LISTINGS" — /about/ now leads with taste
   and coastal living; the two test_h1_home_order pins (the philosophy
   line and the fee disclosure) survive as the only check-ledger lines.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """The home assertions below read conditional sections (market aside,
    bento CTA) — seed like test_h1_home_order so they render."""
    from django.core.cache import cache
    cache.clear()
    call_command("seed_demo", no_images=True, target=20, verbosity=0,
                 i_know_this_is_demo=True)
    yield
    cache.clear()

REPO = Path(__file__).resolve().parents[3]
PAGES_CSS = (REPO / "static" / "css" / "pages.css").read_text()
COMPONENTS_CSS = (REPO / "static" / "css" / "components.css").read_text()
HOME_CSS = (REPO / "static" / "css" / "home.css").read_text()
FOOTER = (REPO / "templates" / "includes" / "_footer.html").read_text()


def _page(path):
    return Client().get(path).content.decode()


# ---------------------------------------------------------------------------
# 1. About copy — taste leads, the check-ledger retreats to two pinned lines
# ---------------------------------------------------------------------------
def test_about_hero_and_story_lead_with_taste():
    body = _page("/about/")
    assert "Homes with taste, from the Kenyan coast." in body
    assert "care where they wake" in body  # subtitle wraps mid-phrase in HTML
    story = body.split("about-story__copy", 1)[1].split("</section>", 1)[0]
    assert "light at four in the afternoon" in story  # wraps across template lines
    assert "homes with character" in story
    # the check-ledger lines are gone from the story…
    assert "verifies every listing" not in body
    assert "one checked property at a time" not in body
    assert "If we could not check something" not in body
    # r56: the fee disclosure left the story for the footer FAQ (its
    # logistics, not a feeling) — the story column no longer carries it
    assert "Buyers pay Gabriel Homes a fee" not in story
    assert "Buyers pay Gabriel Homes a fee" in body  # footer FAQ keeps it
    assert "exact amount" in body and "before you commit" in body


def test_about_story_carries_the_taste_list_and_terrace_figure():
    body = _page("/about/")
    taste = body.split("about-story__taste", 1)[1].split("</ul>", 1)[0]
    assert "[ WHAT WE LOOK FOR ]" in taste
    assert "A street you would walk at dusk" in taste
    m = re.search(r'about-story__figure.*?real-(\d+)-', body, re.S)
    assert m and m.group(1) == "06", "the terrace room leads the story"


def test_quote_band_gains_the_taste_kicker():
    body = _page("/about/")
    band = body.split('class="section about-quote"', 1)[1].split("</section>", 1)[0]
    # r56: the band explains WHY the collection is small, in taste
    # terms — the checked-ledger quote lives on /checks/ only.
    assert "ten homes you'll love" in band
    assert "Every home here is one we would happily move into ourselves." in band
    assert 'class="about-quote__kicker"' in band
    assert "checked" not in band


def test_founder_rail_gains_the_coastal_focus_fact():
    body = _page("/about/")
    rail = body.split("about-founder__rail", 1)[1].split("</ul>", 1)[0]
    # r56: Territory replaces the walked-through standard — places,
    # not process (the checks live on /checks/).
    for fact in ("2026", "Mombasa · Kenya", "Nyali to Shanzu",
                 "Coastal homes &amp; stays"):
        assert fact in rail, f"the rail must state {fact!r}"
    assert "Every home walked through" not in rail


def test_about_cta_is_taste_led_with_the_garden_bedroom():
    body = _page("/about/")
    cta = body.split('class="section cta"', 1)[1].split("</section>", 1)[0]
    assert "Homes worth crossing town for." in cta
    assert "See the homes we have checked" not in cta
    # r56: the band is the sunlit collection, not the evidence exhibit
    assert "Sunlight, salt air, and rooms that breathe." in cta
    assert "honest photography" not in cta
    # r56 pass: each collection photo carries a sensory micro-caption
    caps = re.findall(r'<figcaption>([^<]+)</figcaption>', cta)
    assert caps == ["Golden hour", "Sea light", "Slow mornings"]


def test_about_meta_description_is_taste_led():
    body = _page("/about/")
    assert "chosen for character" in body
    assert "checked by hand" not in body


# ---------------------------------------------------------------------------
# 2. Brand rows — hero subtitle + footer lead (core.0013)
# ---------------------------------------------------------------------------
def test_brand_defaults_and_migration_adopt_taste_copy():
    from apps.core.models import BrandSettings

    brand = BrandSettings.load()
    # r56: the subtitle closes on the feeling ("weeks you wish would
    # never end"); the walked-through line lives on /checks/ + FAQ.
    assert "weeks you wish would never end" in brand.hero_subtitle
    assert "walked through ourselves" not in brand.hero_subtitle
    assert "chosen for character" in brand.footer_lead
    assert "checked" not in brand.footer_lead
    body = _page("/")
    assert brand.hero_subtitle in body
    assert brand.footer_lead in body


def test_home_market_aside_and_bento_cta_are_taste_led():
    body = _page("/")
    assert "picked for how they feel to live in" in body
    assert "Every home, chosen for character." in body
    assert "Every listing, checked first" not in body
    assert "walked through by the team before it appears here" not in body
    assert "Browse every home" in body


# ---------------------------------------------------------------------------
# 3. Vision-pass defect fixes (CSS pins)
# ---------------------------------------------------------------------------
def test_story_taste_list_and_quote_band_css_exist():
    assert ".about-story__taste {" in PAGES_CSS
    assert ".about-quote__kicker {" in PAGES_CSS
    # the band padding pulled in (was clamp(4.5rem, …, 7.5rem))
    band = re.search(r"\.about-quote \{[^}]*\}", PAGES_CSS).group(0)
    assert "clamp(3.6rem, 2.8rem + 3.2vw, 6rem)" in band


def test_value_card_titles_level_the_row():
    assert ".about-values .value-card__title { min-height: 2.5em; }" in PAGES_CSS


def test_founder_portrait_wears_the_warm_grade():
    rule = re.search(
        r"\.about-founder__portrait \.hv2-founder__photo \{[^}]*\}", PAGES_CSS)
    assert rule and "filter: saturate(0.86) sepia(0.17)" in rule.group(0)


def test_founder_caption_is_constrained_on_phones():
    # search inside the LAST ≤560px block (the r55 one) — the r52 block
    # above also matches a loose "@media ... caption" scan.
    block = PAGES_CSS.rsplit("@media (max-width: 560px)", 1)[1]
    m = re.search(r"\.about-founder__caption \{[^}]*\}", block)
    assert m, "the ≤560px founder caption rule must exist"
    assert "white-space: normal" in m.group(0)
    assert "width: 96px" in m.group(0)


def test_proof_strip_widened_and_note_brightened():
    strip = re.search(r"\.cta__proof-strip \{[^}]*\}", PAGES_CSS).group(0)
    assert "max-width: 680px" in strip
    note = re.search(r"\.cta__proof-note \{[^}]*\}", PAGES_CSS).group(0)
    assert "84%" in note


def test_cta_band_tag_contrast_bumped():
    rule = re.search(r"\.cta \.section-tag--light \{[^}]*\}", COMPONENTS_CSS)
    assert rule and "82%" in rule.group(0), "the band tag must read on the photo"


# ---------------------------------------------------------------------------
# 4. Footer — place line, newsletter microcopy, browse column, tap targets
# ---------------------------------------------------------------------------
def test_footer_tag_is_a_place_line_and_note_rewritten():
    body = _page("/")  # rendered: the template comment quotes the old label
    assert "[ MOMBASA · KENYA ]" in body
    assert "[ FOOTER ]" not in body
    assert "whenever ten new homes have gone up" in body
    assert "once ten new listings have been published" not in body


def test_footer_browse_column_widened_and_subheads_nowrap():
    m = re.search(
        r"@media \(min-width: 1200px\) \{[^}]*\.footer-cols \{[^}]*\}", COMPONENTS_CSS)
    assert m, "the ≥1200px footer-cols rule must exist"
    assert "repeat(4, 1fr) 1.35fr" in m.group(0), "wider browse track"
    sub = re.search(r"\.footer-cols__subhead \{[^}]*\}", COMPONENTS_CSS)
    assert sub and "white-space: nowrap" in sub.group(0)


def test_footer_links_get_phone_tap_targets():
    m = re.search(
        r"@media \(max-width: 560px\) \{[^@]*\.footer-cols__col a \{[^}]*\}",
        COMPONENTS_CSS)
    assert m and "0.55rem" in m.group(0)


# ---------------------------------------------------------------------------
# 5. Marquee — solid strip, text-only edge dissolve (the "white caps" fix)
# ---------------------------------------------------------------------------
def test_marquee_strip_is_solid_with_gradient_caps():
    strip = re.search(r"\.hv2-marquee \{[^}]*\}", HOME_CSS).group(0)
    assert "mask-image" not in strip, "the strip must not fade its own bg"
    assert "position: relative" in strip
    caps = re.findall(r"\.hv2-marquee::(?:before|after) \{[^}]*\}", HOME_CSS)
    burnt = [c for c in caps if "var(--burnt" in c]
    assert len(burnt) == 2, "two burnt gradient caps over the running text"
    assert any("linear-gradient(90deg" in c for c in burnt), "left cap"
    assert any("linear-gradient(270deg" in c for c in burnt), "right cap"


# ---------------------------------------------------------------------------
# 6. The card wipe — pools exist and the seeder maps to them
# ---------------------------------------------------------------------------
def test_demo_photo_pools_exist():
    """The pools the wipe depends on must ship (regenerated by
    scripts/install-stock-pools.py; bulk listings read them at seed time
    and scripts/r54_wipe_cards.py repairs a seeded DB in place)."""
    media = Path(__file__).resolve().parents[4] / "gabriel-homes" / "media"
    if not media.exists():  # fresh CI checkout: media is gitignored
        pytest.skip("media/ not present in this checkout")
    for pool, minimum in (("house", 10), ("apartment", 10), ("interior", 10),
                          ("land", 5), ("office", 5), ("shops", 5),
                          ("warehouse", 5)):
        files = list((media / "demo-photos" / pool).glob("*.jpg"))
        assert len(files) >= minimum, f"pool {pool} too thin: {len(files)}"
