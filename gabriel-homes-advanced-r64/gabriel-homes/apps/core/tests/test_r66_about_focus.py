"""r66 — owner round: the About focus pass.

Three owner asks drive this round:

1. "Remove the carousel — Homes worth crossing town for — it doesn't
   look good, the background and images are shaded."  →  the closing
   band's shaded photo strip (and every about-tile rule) left the page;
   the band keeps the tag, the taste-led headline and the Explore
   button. (Removal pins also live in the updated r53/r55/r63/r64
   files; this file pins the new whole.)

2. "The cards above should get better styling... cards stacked in
   columns that you hover and they expand and reveal more info."
   →  the 001/002/003 principles are now tall white panels in an
   accordion row: fine pointers collapse them to numeral strips and
   bloom the hovered/focused card open, detail (title + body) fading
   in behind the panel. Phones, touch, no-JS and print render every
   card fully open — the reveal is a nicety, never a gate.

3. "Remove the palm tree background in the about us page... maybe some
   waves patterns."  →  .about-values::before now tiles wave-field.svg
   (scripts/r66_wave_field.py — nine sine rows, the palm's clay pair),
   same z-index -1 / pointer-events none / bottom-fade contract.

This file pins all three so a future refactor cannot silently drop
them.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=80, verbosity=0,
                 i_know_this_is_demo=True)
    yield


REPO = Path(__file__).resolve().parents[3]
PAGES_CSS = (REPO / "static" / "css" / "pages.css").read_text()
ABOUT = (REPO / "templates" / "core" / "about.html").read_text()
WAVE_SVG = (REPO / "static" / "img" / "wave-field.svg").read_text()


def _page(path):
    return Client().get(path).content.decode()


# ---------------------------------------------------------------------------
# 1. The accordion — markup
# ---------------------------------------------------------------------------
def test_every_principle_card_is_focusable_and_carries_its_detail():
    body = _page("/about/")
    values = body.split('class="section about-values"', 1)[1].split("</section>", 1)[0]
    assert values.count('class="value-card" data-reveal tabindex="0"') == 3, (
        "three cards, each tabindex=0 — :focus-within gives keyboard users "
        "the same reveal hover buys"
    )
    assert values.count('class="value-card__detail"') == 3, (
        "title + body ride inside the detail block (the reveal target)"
    )
    # the detail wraps title AND body, in order, three times
    details = re.findall(
        r'<div class="value-card__detail">\s*<h3 class="value-card__title">.*?'
        r'</h3>\s*<p class="value-card__body">', values, re.S)
    assert len(details) == 3


def test_collapsed_panels_carry_their_spine():
    """r66 pass-2 (VLM): the first pass's collapsed strips read as
    "loading content" — every card now carries an aria-hidden vertical
    spine (its title, mono caps) that makes the collapse a deliberate
    book-spine pose and crossfades out when the detail blooms in."""
    body = _page("/about/")
    values = body.split('class="section about-values"', 1)[1].split("</section>", 1)[0]
    spines = re.findall(
        r'<span class="value-card__spine" aria-hidden="true">([^<]+)</span>', values)
    assert spines == ["People first, property second.",
                      "Homes with soul.",
                      "Support beyond the keys."], (
        "each spine carries its card's title, in order"
    )
    # the spine lives ONLY inside the accordion gate — hidden everywhere
    # else (phones/touch/print keep it out of the flow)
    base = re.search(r"\.about-values \.value-card__spine \{ display: none; \}",
                     PAGES_CSS)
    assert base, "a base display:none keeps the spine out of the fallback"
    gate = _gate_block()
    spine = re.search(r"\.about-values \.value-card__spine \{[^}]*\}", gate)
    assert spine and "writing-mode: vertical-rl" in spine.group(0), (
        "the spine reads as a vertical book-spine label"
    )
    gone = re.search(
        r"\.value-card:focus-within \.value-card__spine \{[^}]*\}", gate)
    assert gone and "opacity: 0" in gone.group(0), (
        "the spine crossfades out as the panel blooms open"
    )


def test_principle_copy_survives_the_restyle():
    body = _page("/about/")
    values = body.split('class="section about-values"', 1)[1].split("</section>", 1)[0]
    for num, tag, title in (
            ("001", "[ People ]", "People first, property second."),
            ("002", "[ Character ]", "Homes with soul."),
            ("003", "[ Support ]", "Support beyond the keys.")):
        assert num in values and tag in values and title in values, (
            f"{tag} card keeps its numeral, bracket tag and title"
        )
    assert "the school run, the sea breeze" in values
    assert "doesn't join the" in values
    assert "local trades only" in values


# ---------------------------------------------------------------------------
# 2. The accordion — CSS behaviour
# ---------------------------------------------------------------------------
def _gate_block():
    m = re.search(
        r"@media \(hover: hover\) and \(pointer: fine\) and \(min-width: 811px\) \{.*?\n\}",
        PAGES_CSS, re.S)
    assert m, "the accordion gate block must exist"
    return m.group(0)


def test_accordion_collapses_and_blooms_on_hover_and_focus():
    gate = _gate_block()
    # the row becomes a flex of tall panels
    assert ".about-values .story__values" in gate
    assert "display: flex" in gate
    assert "min-height: 29rem" in gate, "tall panels — the accordion look"
    # the hovered/focused card grows, the siblings shrink
    grow = re.search(
        r"\.about-values \.story__values \.value-card:hover,\s*"
        r"\.about-values \.story__values \.value-card:focus-within \{[^}]*\}",
        gate)
    assert grow and "flex-grow: 4.2" in grow.group(0), (
        ":hover AND :focus-within bloom the panel (keyboard parity)"
    )
    # the growth animates on flex-grow specifically
    card = re.search(
        r"\.about-values \.story__values \.value-card \{[^}]*\}", gate)
    assert card and "flex-grow 0.55s" in card.group(0), (
        "the expansion is a flex-grow transition, not a jump"
    )


def test_accordion_detail_reveals_after_the_panel_leads():
    gate = _gate_block()
    detail = re.search(r"\.about-values \.value-card__detail \{[^}]*\}", gate)
    assert detail, "the detail rule ships inside the gate"
    css = detail.group(0)
    assert "opacity: 0" in css and "translateY(10px)" in css, (
        "collapsed panels hide the detail (never display:none — the copy "
        "stays in the a11y tree)"
    )
    assert "width: 26rem" in css, "fixed width — no mid-expand text reflow"
    assert "margin-top: auto" in css, "the text rides the panel floor"
    reveal = re.search(
        r"\.value-card:focus-within \.value-card__detail \{[^}]*\}", gate)
    assert reveal and "opacity: 1" in reveal.group(0)
    assert "transition-delay: 0.16s" in reveal.group(0), (
        "the panel leads, the text follows"
    )


def test_accordion_is_gated_to_fine_pointers_only():
    """Phones, touch tablets and print must render every card fully open —
    the base grid (outside the gate) carries all the copy at full size."""
    gate = _gate_block()
    assert "(hover: hover) and (pointer: fine)" in gate, (
        "the collapse/expand lives behind the hover-capability gate"
    )
    assert "(min-width: 811px)" in gate
    # the base (gate-free) card rule keeps the panels readable everywhere
    base = re.search(r"\.about-values \.value-card \{[^}]*\}", PAGES_CSS)
    assert base and "display" not in base.group(0), (
        "the base card never hides anything — opacity/flex tricks live in "
        "the gate only"
    )
    # and no opacity:0 outside the gate
    outside = PAGES_CSS.replace(gate, "")
    assert ".about-values .value-card__detail { margin-top: 0.2rem; }" in outside


def test_accordion_respects_reduced_motion():
    """State changes stay (collapsed/expanded), motion does not."""
    block = re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{[^@]*?"
        r"\.about-values \.value-card \{ transition: none; \}[^@]*?"
        r"\.about-values \.value-card__detail \{ transition: none; \}",
        PAGES_CSS)
    assert block, "the reduced-motion block kills both transitions"


def test_reveal_stagger_never_delays_the_hover_expand():
    """The stagger delays grew to five values so the reveal rise keeps its
    trail while flex-grow/border/shadow react instantly to hover."""
    for n, ms in ((2, "110ms"), (3, "220ms")):
        rule = re.search(
            rf"html\.motion-ready:not\(\[data-fx=\"none\"\]\) "
            rf"\.story__values \.value-card:nth-child\({n}\) "
            rf"\{{ transition-delay: {ms}, {ms}, 0s, 0s, 0s; \}}", PAGES_CSS)
        assert rule, f"card {n} stagger must lead with the reveal pair only"


# ---------------------------------------------------------------------------
# 3. The wave field
# ---------------------------------------------------------------------------
def test_wave_tile_exists_and_matches_the_generator_contract():
    assert '<g id="wave-field"' in WAVE_SVG
    # the palm's clay pair — the sea texture stays in the brand family
    assert "#e7d9cd" in WAVE_SVG and "#dcc6b8" in WAVE_SVG
    # nine rows x two tones = eighteen stroke paths
    assert WAVE_SVG.count("<path ") == 18
    assert 'viewBox="0 0 1000 700"' in WAVE_SVG


def test_wave_field_is_decorative_only():
    rule = re.search(r"\.about-values::before \{[^}]*\}", PAGES_CSS)
    css = rule.group(0)
    assert "z-index: -1" in css, "paints under every in-flow block"
    assert "pointer-events: none" in css, "never steals a click"
    m = re.search(r"mask-image:\s*linear-gradient\([^)]*\)", css)
    assert m and "78%" in m.group(0) and "transparent 100%" in m.group(0), (
        "dissolves before the founder band, like the r65 field before it"
    )


def test_palm_left_the_about_values_band_only():
    """The palm stays exactly where it was pinned (home market, listings
    band) — only the about values band traded it for waves."""
    about_values = re.search(
        r"\.about-values \{[^}]*\}\s*\.about-values::before \{[^}]*\}", PAGES_CSS)
    assert "palm-field" not in about_values.group(0)
    # home + listings keep the palm (r46/r65 contracts, untouched)
    home_css = (REPO / "static" / "css" / "home.css").read_text()
    assert 'url("../img/palm-field.svg")' in home_css


# ---------------------------------------------------------------------------
# 4. The closing band after the carousel removal
# ---------------------------------------------------------------------------
def test_closing_band_is_the_quiet_cta():
    body = _page("/about/")
    cta = body.split('class="section cta"', 1)[1].split("</section>", 1)[0]
    assert "[ THE COLLECTION ]" in cta
    assert "Homes worth crossing town for." in cta
    assert 'href="/properties/"' in cta, "the Explore button survives"
    # one quiet close: nothing after the button except the container end
    assert "cta__proof" not in cta and "about-tile" not in cta
    assert cta.count("<img") == 0, "no shaded photos remain in the band"


def test_no_shaded_photo_assets_load_on_the_page():
    """The three strip photos are gone from the about page entirely —
    lazy or not, they are not referenced."""
    body = _page("/about/")
    for gone in ("real-09-golden-hour", "real-10-sea-light", "real-11-slow-mornings"):
        assert gone not in body, f"{gone} left with the carousel"
