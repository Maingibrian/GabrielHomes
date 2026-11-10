"""r66 + r67 — owner rounds: the About focus pass, twice over.

r66 shipped three owner asks:

1. "Remove the carousel — Homes worth crossing town for — it doesn't
   look good, the background and images are shaded."  →  the closing
   band's shaded photo strip (and every about-tile rule) left the page;
   the band keeps the tag, the taste-led headline and the Explore
   button.

2. "The cards above should get better styling... cards stacked in
   columns that you hover and they expand and reveal more info."
   →  the 001/002/003 principles became stacked columns that bloom
   open on hover/focus.

3. "Remove the palm tree background in the about us page... maybe some
   waves patterns."  →  .about-values::before tiles wave-field.svg
   (scripts/r66_wave_field.py — nine sine rows, the palm's clay pair),
   same z-index -1 / pointer-events none / bottom-fade contract.

r67 (owner round): "looks bad." The E3 pass read the r66 white boxes
as floating on a void with "no real-estate warmth", and the collapsed
accordion strips hid the photography the site sells with. The columns
are now PHOTO EXPANDERS: tall coast photographs (object-fit cover, NO
shading filter — the carousel complaint was the scrim crushing the
pictures; only the copy zone carries a gradient) with numeral + tag +
title + body on a bottom-anchored panel. Fine pointers collapse the
row and bloom the hovered/focused card open; every other context
renders the same cards fully open — the reveal is a nicety, never a
gate.

This file pins the current contract (r64 precedent: obsolete pins are
rewritten to pin the NEW whole) so a future refactor cannot silently
drop any of it.
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
# 1. The photo expander — markup
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


def test_every_card_is_a_tall_photo_with_honest_alt_text():
    """r67: the icon medallions left with the white panels — every card
    is now a coast photograph. The photos are CONTENT (real alt text,
    intrinsic width/height), not decoration; the scrim that keeps the
    copy readable is the aria-hidden span, never a filter on the img."""
    body = _page("/about/")
    values = body.split('class="section about-values"', 1)[1].split("</section>", 1)[0]
    cards = re.findall(r'<article class="value-card".*?</article>', values, re.S)
    assert len(cards) == 3
    for card in cards:
        assert 'class="value-card__photo"' in card, "the photo backs the panel"
        assert re.search(r'alt="[A-Z][^"]*"', card), "honest alt text, capitalised"
        assert 'loading="lazy"' in card and 'width="' in card and 'height="' in card, (
            "lazy load + intrinsic size — no layout shift"
        )
        assert 'class="value-card__scrim" aria-hidden="true"' in card, (
            "the readability gradient is decorative and unlabeled"
        )
    # the trio (pass-4, E3 contact-sheet verdicts): slow mornings
    # (the life first) / golden hour (the dusk street — the one frame
    # that feels like the coast, A-tier) / sea light through the open
    # doors (life after the keys, A-tier)
    for photo in ("real-11-slow-mornings", "real-09-golden-hour",
                  "real-10-sea-light"):
        assert photo in values, f"{photo} backs its principle"


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
# 2. The photo expander — CSS behaviour
# ---------------------------------------------------------------------------
def _gate_block():
    m = re.search(
        r"@media \(hover: hover\) and \(pointer: fine\) and \(min-width: 811px\) \{.*?\n\}",
        PAGES_CSS, re.S)
    assert m, "the expander gate block must exist"
    return m.group(0)


def test_expander_blooms_on_hover_and_focus():
    gate = _gate_block()
    # the row becomes a flex of tall photo panels
    assert ".about-values .story__values" in gate
    assert "display: flex" in gate
    assert "min-height: 32rem" in gate, "tall columns — the expander look"
    # the hovered/focused card grows, the siblings shrink
    grow = re.search(
        r"\.about-values \.story__values \.value-card:hover,\s*"
        r"\.about-values \.story__values \.value-card:focus-within \{[^}]*\}",
        gate)
    assert grow and "flex-grow: 2.8" in grow.group(0), (
        ":hover AND :focus-within bloom the panel (keyboard parity)"
    )
    # the growth animates on flex-grow specifically
    card = re.search(
        r"\.about-values \.story__values \.value-card \{[^}]*\}", gate)
    assert card and "flex-grow 0.55s" in card.group(0), (
        "the expansion is a flex-grow transition, not a jump"
    )


def test_expander_detail_reveals_after_the_panel_leads():
    gate = _gate_block()
    detail = re.search(r"\.about-values \.value-card__detail \{[^}]*\}", gate)
    assert detail, "the detail rule ships inside the gate"
    css = detail.group(0)
    assert "opacity: 0" in css and "translateY(10px)" in css, (
        "collapsed panels hide the detail (never display:none — the copy "
        "stays in the a11y tree)"
    )
    assert "width: 24rem" in css, "fixed width — no mid-expand text reflow"
    reveal = re.search(
        r"\.value-card:focus-within \.value-card__detail \{[^}]*\}", gate)
    assert reveal and "opacity: 1" in reveal.group(0)
    assert "transition-delay: 0.16s" in reveal.group(0), (
        "the panel leads, the text follows"
    )


def test_expander_is_gated_to_fine_pointers_only():
    """Phones, touch tablets and print must render every card fully open —
    the base grid (outside the gate) carries all the copy at full size."""
    gate = _gate_block()
    assert "(hover: hover) and (pointer: fine)" in gate, (
        "the collapse/expand lives behind the hover-capability gate"
    )
    assert "(min-width: 811px)" in gate
    # the detail hides NOWHERE outside the gate — every non-gate context
    # shows title + body in full. The allowed stragglers are the base
    # alignment rule (bottom-anchored flex, min-height — a leveller, not
    # a hider) and the reduced-motion kill (transition: none).
    outside = PAGES_CSS.replace(gate, "")
    stragglers = re.findall(r"\.about-values \.value-card__detail \{[^}]*\}",
                            outside)
    for rule in stragglers:
        assert "opacity" not in rule and "display: none" not in rule, (
            f"outside the gate a detail rule must never hide copy: {rule}"
        )
    assert any("min-height: 11rem" in rule for rule in stragglers), (
        "the baseline leveller ships outside the gate (all contexts align)"
    )
    assert any("transition: none" in rule for rule in stragglers), (
        "the reduced-motion kill still ships"
    )
    # and the base card rule never hides anything (display:flex is the
    # panel's bottom-anchor layout, not a hider — the ban is on
    # display:none / opacity:0 style gating)
    base = re.search(r"\.about-values \.value-card \{[^}]*\}", outside)
    assert base, "the base card rule ships outside the gate"
    assert "display: none" not in base.group(0) and "opacity" not in base.group(0), (
        "the base card never hides anything — opacity/flex tricks live in "
        "the gate only"
    )


def test_expander_respects_reduced_motion():
    """State changes stay (collapsed/expanded), motion does not."""
    block = re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{[^@]*?"
        r"\.about-values \.value-card \{ transition: none; \}[^@]*?"
        r"\.about-values \.value-card__detail \{ transition: none; \}",
        PAGES_CSS)
    assert block, "the reduced-motion block kills both transitions"


def test_reveal_stagger_never_delays_the_hover_expand():
    """The stagger delays lead with the reveal pair only so the rise
    keeps its trail while flex-grow/border/shadow react instantly to
    hover (a delayed expand would read as lag)."""
    for n, ms in ((2, "110ms"), (3, "220ms")):
        rule = re.search(
            rf"html\.motion-ready:not\(\[data-fx=\"none\"\]\) "
            rf"\.story__values \.value-card:nth-child\({n}\) "
            rf"\{{ transition-delay: {ms}, {ms}, 0s, 0s, 0s; \}}", PAGES_CSS)
        assert rule, f"card {n} stagger must lead with the reveal pair only"


def test_photos_are_unshaded_and_only_the_copy_zone_carries_a_scrim():
    """The owner's carousel complaint was the scrim crushing the images.
    The value photos carry NO filter; readability comes from a bottom
    espresso gradient that owns the copy zone (the lower ~60% of the
    card) and dissolves in the top fifth — the picture breathes."""
    photo = re.search(r"\.about-values \.value-card__photo \{[^}]*\}", PAGES_CSS)
    assert photo, "the photo rule ships"
    assert "filter" not in photo.group(0), "no shading filter on the photos"
    assert "object-fit: cover" in photo.group(0)
    scrim = re.search(r"\.about-values \.value-card__scrim \{[^}]*\}", PAGES_CSS)
    css = scrim.group(0)
    assert "linear-gradient(to top" in css, "the gradient lifts toward the sky"
    assert css.count("var(--espresso)") == 4, "token-only scrims (no new palette)"
    assert "92%" in css and "transparent 93%" in css, (
        "solid under the copy, gone by the top fifteenth — the photo breathes"
    )
    assert "62%" in css, "the mid-zone stays espresso-rich where the numerals sit"
    assert "pointer-events: none" in css, "the scrim never steals a click"


def test_panel_copy_is_cream_on_the_photo():
    """The shared components.css value-card text is the ink-on-white
    set; the photo context overrides it — ember numeral, cream tag,
    white Fraunces title, base-size cream body (the E3 pass called the
    old sm grey 'cramped and marginal')."""
    num = re.search(r"\.about-values \.value-card__num \{[^}]*\}", PAGES_CSS)
    assert "var(--ember)" in num.group(0), "ember reads warm on espresso"
    tag = re.search(r"\.about-values \.value-card__tag \{[^}]*\}", PAGES_CSS)
    assert "var(--cream)" in tag.group(0)
    title = re.search(r"\.about-values \.value-card__title \{[^}]*\}", PAGES_CSS)
    assert "var(--white)" in title.group(0)
    assert "var(--font-display)" in title.group(0), "Fraunces, not UI sans"
    body_rule = re.search(r"\.about-values \.value-card__body \{[^}]*\}",
                          PAGES_CSS)
    assert "var(--cream)" in body_rule.group(0)
    assert "var(--text-base)" in body_rule.group(0), "base size, not sm"


def test_base_cards_are_tall_photo_panels_everywhere():
    """The base (gate-free) card is already the expander at rest — tall,
    espresso-framed (the photo's bed while it loads), with the shared
    components.css card frame (2.25rem inset + hover lift) killed."""
    base = re.search(r"\.about-values \.value-card \{[^}]*\}", PAGES_CSS)
    css = base.group(0)
    assert "min-height: 30rem" in css, "tall columns at rest"
    assert "overflow: hidden" in css, "the photo clips to the squircle"
    assert "padding: 0" in css, "the panel owns the inset, not the card"
    assert "transform: none" in css, "no hover bounce on a photo column"
    assert "background: var(--espresso)" in css
    mobile = re.search(
        r"@media \(max-width: 810px\) \{[^@]*?\.about-values \.story__values "
        r"\{ grid-template-columns: 1fr; \}[^@]*?\.about-values \.value-card "
        r"\{ min-height: 26rem; \}", PAGES_CSS)
    assert mobile, "phones stack the columns one-per-row, still tall"


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


def test_the_carousel_stays_gone_while_the_values_photos_load():
    """r66 evicted the shaded strip (and its photos) from the page; r67
    brought real-09/real-11 back as UNSHADED value-card photos — a
    different job with a different treatment. The pin keeps its teeth:
    the carousel MARKUP must stay gone, and the quiet close stays
    photo-free."""
    body = _page("/about/")
    assert "about-tile" not in body and "cta__proof" not in body, (
        "the carousel markup never returns"
    )
    values = body.split('class="section about-values"', 1)[1].split("</section>", 1)[0]
    assert values.count('class="value-card__photo"') == 3, (
        "the three value photos load as card backgrounds"
    )
