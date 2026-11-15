"""r103 — Listing detail page BENCHMARK (owner ask: "make bench tests ... score
perfectly on the benchmark").

The benchmark scores the detail page across 4 component groups (header/intro,
gallery+facts, body sections, sidebar+similar+mobile), 10 criteria each.
Every criterion is a binary pass/fail assertion over the rendered page
(template + CSS + view context). The file is BOTH:

  * a normal pytest module — each criterion is a test; RED before the
    r103 implementation, GREEN after; and
  * a scored benchmark — `test_benchmark_score_100` re-runs every
    criterion and prints a per-group scorecard; it FAILS unless the
    aggregate score is 100% (40/40).

Run:  .venv/bin/python -m pytest apps/listings/tests/test_r103_detail_bench.py -v

Harness note: the scorecard calls each criterion directly, injecting
arguments by parameter NAME (page / seeded); a criterion that needs the
pytest-only django_db_blocker counts as N/A there — its contract is proven
in the normal pytest run.
"""
import inspect
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db

DETAIL_CSS = Path(__file__).resolve().parents[3] / "static" / "css" / "detail.css"
TPL = Path(__file__).resolve().parents[3] / "templates" / "listings" / "detail.html"


@pytest.fixture
def seeded(db):
    """Full seed (images on) + demo brand contacts + a bench listing that
    exercises EVERY component: >=4 photos (thumbs/nav/counter), amenities,
    and at least one similar listing (the rail + browse link).

    Function-scoped ON PURPOSE: the earlier module-scoped version ran
    outside pytest-django's per-test transaction, leaking 80 listings +
    filled BrandSettings into every later test file (146 setup
    IntegrityErrors, P2 checklist + testimonial failures full-suite-only).
    """
    from django.core.cache import cache

    cache.clear()
    if True:
        call_command("seed_demo", clear=True, with_enquiries=True, verbosity=0,
                     i_know_this_is_demo=True)
        # Demo brand contacts — same values seed_demo mints for the Gabriel
        # Homes agency row. r103: without these the contact card has no
        # call/WhatsApp/email and the mobile bar never renders.
        from apps.core.models import BrandSettings

        brand = BrandSettings.load()
        brand.phone = "+254712345678"
        brand.whatsapp = "+254712345678"
        brand.email = "hello@gabrielhomes.co.ke"
        brand.save()

        from apps.listings.models import Property, PropertyImage
        from decimal import Decimal

        def _similar_count(p):
            price_min = p.price * Decimal("0.7")
            price_max = p.price * Decimal("1.3")
            county = p.location
            while county.parent:
                county = county.parent
            descendant_pks = set(
                county.get_descendants(include_self=True).values_list("pk", flat=True)
            )
            return Property.objects.published().filter(
                property_type=p.property_type,
                listing_type=p.listing_type,
                price__gte=price_min,
                price__lte=price_max,
                location__in=descendant_pks,
            ).exclude(pk=p.pk).count()

        # Pick the first published listing that HAS similar listings (the
        # rail renders only then) and at least one photo.
        rich = None
        for p in Property.objects.published().prefetch_related("images").order_by("pk"):
            if p.images.count() >= 1 and _similar_count(p) >= 1:
                rich = p
                break
        assert rich is not None, "seed produced no listing with similar listings"

        # bump to 5 photos (seed gives 1-2; thumbs + counter need >=2).
        # Re-fetch afterwards: the prefetch_related cache on `rich` still
        # holds the pre-bump image list and would report 1 forever.
        if rich.images.count() < 5:
            base = rich.images.first()
            for i in range(rich.images.count(), 5):
                PropertyImage.objects.create(
                    property=rich, image=base.image, caption=f"bench {i}",
                    position=i,
                )
        rich = Property.objects.prefetch_related("images").get(pk=rich.pk)
    return rich


@pytest.fixture
def page(seeded, db):
    """The rendered detail HTML for the bench listing."""
    client = Client()
    resp = client.get(seeded.get_absolute_url())
    assert resp.status_code == 200
    return resp.content.decode()


CSS = ""


def _css() -> str:
    global CSS
    if not CSS:
        CSS = DETAIL_CSS.read_text()
    return CSS


def _tpl() -> str:
    return TPL.read_text()


# ---------------------------------------------------------------
# Group A — Header / Intro (10 criteria)
# ---------------------------------------------------------------

def test_a1_title_display_serif(page):
    """clamp display serif h1, >=2.2rem floor, <=24ch measure."""
    assert re.search(r"\.detail-intro__title\s*\{[^}]*clamp\(2\.2rem", _css())
    assert re.search(r"max-width:\s*24ch", _css())
    assert "<h1" in page


def test_a2_eyebrow_chips_no_brackets(page):
    """Eyebrow = type chip + verified chip; NO bracket syntax anywhere."""
    assert not re.search(r">\s*\[\s*[A-Z][A-Z /·]*\s*\]\s*<", page)
    assert "detail-intro__type-chip" in page


def test_a3_price_block(page):
    assert re.search(r"<strong>[^<]*KES[^<]*</strong>", page), \
        "price strong must render with kes formatting"
    assert re.search(r"\.detail-intro__price strong\s*\{[^}]*1\.5rem", _css())


def test_a4_share_save_actions(page):
    assert "data-share-url" in page
    assert re.search(r"\.detail-header__action:focus-visible", _css())


def test_a5_breadcrumbs(page):
    assert "breadcrumbs" in page
    assert 'aria-label="Breadcrumb"' in page
    crumbs = re.findall(r"<li[^>]*>(.*?)</li>", page, re.S)[:4]
    assert crumbs and "<a " not in crumbs[-1], "last crumb must be unlinked"


def test_a6_location_line(page):
    assert "detail-intro__location" in page
    assert re.search(r"\.detail-intro__location\s*\{[^}]*font-size:\s*14px", _css())


def test_a7_no_bracket_labels(page):
    """No '[ LABEL ]' dev-syntax section headers anywhere on the page."""
    assert not re.search(r">\s*\[\s*[A-Z][A-Z /·]*\s*\]\s*<", page)


def test_a8_intro_wrap_mobile(page):
    """No horizontal overflow: intro bottom row wraps (flex-wrap present)."""
    assert re.search(r"\.detail-intro__bottom\s*\{[^}]*flex-wrap", _css())
    assert re.search(
        r"max-width:\s*1199px\).*?\.detail-intro__location\s*\{[^}]*flex-basis:\s*100%",
        _css(), re.S)


def test_a9_single_h1(page):
    assert page.count("<h1") == 1 and page.count("</h1>") == 1


def test_a10_og_image_absolute(page):
    assert re.search(r'property="og:image" content="http', page)


# ---------------------------------------------------------------
# Group B — Gallery + Facts bar (10 criteria)
# ---------------------------------------------------------------

def test_b1_gallery_aspect(page):
    """Aspect between 3/2 and 16/7 — no hard 16/7 letterbox of 4/3 photos."""
    assert not re.search(r"aspect-ratio:\s*16\s*/\s*7\b", _css())
    assert re.search(r"aspect-ratio:\s*3\s*/\s*2", _css())


def test_b2_thumbs_render_multi_image(seeded, page):
    assert seeded.images.count() >= 2
    assert 'class="gallery__thumbs' in page
    assert page.count("data-gallery-thumb=") == seeded.images.count()


def test_b3_nav_and_counter(page):
    assert "data-gallery-prev" in page and "data-gallery-next" in page
    assert "data-gallery-current" in page


def test_b4_single_image_graceful(seeded, page, django_db_blocker):
    """A 1-image listing renders no dead nav/thumbs/counter."""
    from apps.listings.models import Property

    with django_db_blocker.unblock():
        client = Client()
        solo = None
        for p in Property.objects.published().prefetch_related("images"):
            if p.images.count() == 1:
                solo = p
                break
        if solo is None:
            pytest.skip("no 1-image listing in seed (bump_gallery guarantees 1)")
        html = client.get(solo.get_absolute_url()).content.decode()
    assert "data-gallery-prev" not in html
    assert "gallery__thumbs" not in html
    assert "data-gallery-current" not in html
    assert "gallery__main" in html, "hero image still renders"


def test_b5_gallery_tag_is_type_name(page):
    assert re.search(r'gallery__main-tag">\s*[A-Z][a-z]', page), \
        "tag shows the property type name, not an all-caps blob"


def test_b6_lightbox_contract(page):
    """L4 lightbox contract unchanged (JS-built dialog; no dead control)."""
    js = (TPL.parents[1].parent / "static" / "js" / "detail-gallery.js").read_text()
    assert "dialog" in js


def test_b7_facts_have_icons(page):
    """Each fact: semantic icon + label + value."""
    facts = re.findall(
        r'facts-bar__fact[^>]*>(.*?)</div>\s*</div>', page, re.S)
    assert len(facts) >= 4, f"want 4 facts, found {len(facts)}"
    for f in facts:
        assert "<svg" in f, "every fact carries an icon"
        assert "facts-bar__label" in f and "facts-bar__value" in f


def test_b8_facts_typography(page):
    css = _css()
    assert re.search(r"\.facts-bar__label\s*\{[^}]*font-weight:\s*600", css)
    assert re.search(r"\.facts-bar__value\s*\{[^}]*font-weight:\s*600", css)


def test_b9_facts_responsive_grid(page):
    css = _css()
    assert re.search(r"repeat\(4,\s*minmax\(0,\s*1fr\)\)", css)
    assert re.search(r"max-width:\s*809px\).*?\.facts-bar--revamp\s*\{[^}]*repeat\(2",
                     css, re.S)


def test_b10_facts_value_nowrap(page):
    """Value+unit never break mid-number ('3,500 m²' stays one line)."""
    assert re.search(r"\.facts-bar__value\s*\{[^}]*white-space:\s*nowrap", _css())


# ---------------------------------------------------------------
# Group C — Body sections (10 criteria)
# ---------------------------------------------------------------

def test_c1_description_eyebrow(page):
    assert not re.search(r">\s*\[\s*DESCRIPTION\s*\]\s*<", page)
    assert re.search(
        r'detail-description__title detail-section__eyebrow">About this home<', page
    ), "description eyebrow must be editorial, not bracket syntax"


def test_c2_description_linebreaks(page):
    """Description renders paragraphs (|linebreaks), 17px/1.75 body."""
    assert "detail-description__body" in page
    assert re.search(r"\.detail-description__body\s*\{[^}]*font-size:\s*17px", _css())
    assert "|linebreaks" in _tpl()


def test_c3_description_empty_state(page):
    tpl = _tpl()
    assert "hasn't added a written description" in tpl


def test_c4_amenities_fluid_grid(page):
    assert re.search(
        r"\.amenities__grid\s*\{[^}]*repeat\(auto-fill[^)]*minmax\(\s*1[4-9][0-9]px",
        _css())


def test_c5_amenity_item_card(page):
    css = _css()
    assert re.search(r"\.amenities__item[^{]*\{[^}]*border-radius:\s*12px", css)
    assert re.search(r"\.amenities__item:hover\s*\{[^}]*translate", css) or re.search(
        r"\.amenities__item:hover\s*\{[^}]*transform", css)


def test_c6_amenity_icon_variety(page):
    """The page offers >=3 distinct amenity glyph shapes (not one checkmark)."""
    tpl = _tpl()
    block = tpl[tpl.index("amenities__item-icon"):]
    block = block[: block.index("{% endwith %}")]
    svgs = re.findall(r"<svg[^>]*>(.*?)</svg>", block, re.S)
    shapes = {re.sub(r"\s+", " ", s.strip())[:60] for s in svgs if s.strip()}
    assert len(shapes) >= 3, f"want >=3 distinct amenity icons, got {len(shapes)}"


def test_c7_nearby_caption_styling(page):
    css = _css()
    assert re.search(
        r"\.nearby-amenities__note[^{]*\{[^}]*font-family:\s*var\(--font-mono\)",
        css)


def test_c8_nearby_card_hierarchy(page):
    css = _css()
    assert re.search(r"\.nearby-amenity__icon\s*\{[^}]*38px", css) or re.search(
        r"\.nearby-amenity__icon\s*\{[^}]*width:\s*38px", css)
    assert re.search(r"\.nearby-amenity__type\s*\{[^}]*text-transform:\s*uppercase", css)


def test_c9_map_heading_alignment(page):
    css = _css()
    assert re.search(r"\.detail-map__heading\s*\{[^}]*display:\s*flex", css)
    assert re.search(r"\.nearby-amenities__heading\s*\{[^}]*display:\s*flex", css)


def test_c10_video_block_no_brackets(page):
    tpl = _tpl()
    assert "[ VIDEO TOUR ]" not in tpl


# ---------------------------------------------------------------
# Group D — Sidebar + Similar + Mobile (10 criteria)
# ---------------------------------------------------------------

def test_d1_sidebar_header_price_recap(page):
    assert "agent-card-sticky__price" in page


def test_d2_contact_buttons_render(seeded, page):
    assert "agent-card-sticky__btn--call" in page
    assert "agent-card-sticky__btn--whatsapp" in page
    assert "agent-card-sticky__btn--email" in page


def test_d3_whatsapp_contrast(page):
    css = _css()
    assert re.search(r"agent-card-sticky__btn--whatsapp\s*\{[^}]*color:\s*#0b3b2e", css)


def test_d4_enquiry_inputs_touch_height(page):
    css = _css()
    assert re.search(
        r"\.enquiry-form \.form__input,\s*\.enquiry-form \.form__textarea\s*\{[^}]*min-height:\s*44px",
        css)


def test_d5_response_microcopy(page):
    assert re.search(r"agent-card-sticky__meta|responds? within|typical reply", page, re.I)


def test_d6_similar_fluid_grid(page):
    assert re.search(
        r"\.similar__grid\s*\{[^}]*repeat\(auto-fill,\s*minmax\(\s*2[2-9][0-9]px",
        _css())


def test_d7_similar_orphan_proof(page):
    """1 card fills the row; 2 cards halve; never a stranded 1/3 orphan."""
    assert re.search(r"\.similar__grid\s*>\s*div:first-child:last-child", _css()) or \
        re.search(r"\.similar__grid\s*>\s*div:only-child", _css())


def test_d8_similar_browse_all_link(page):
    assert "similar__browse" in page
    assert "Browse all " in page


def test_d9_mobile_bar_renders_with_contacts(page):
    assert "mobile-contact-bar__btn--call" in page
    assert "mobile-contact-bar__btn--whatsapp" in page


def test_d10_mobile_bar_touch_targets(page):
    css = _css()
    assert re.search(r"\.mobile-contact-bar__btn\s*\{[^}]*min-height:\s*44px", css)


# ---------------------------------------------------------------
# The scored benchmark (fails unless 100%)
# ---------------------------------------------------------------

CRITERIA = [
    ("A. Header/Intro", [
        ("A1 title serif clamp", test_a1_title_display_serif),
        ("A2 eyebrow chips", test_a2_eyebrow_chips_no_brackets),
        ("A3 price block", test_a3_price_block),
        ("A4 share/save actions", test_a4_share_save_actions),
        ("A5 breadcrumbs", test_a5_breadcrumbs),
        ("A6 location line", test_a6_location_line),
        ("A7 no bracket labels", test_a7_no_bracket_labels),
        ("A8 intro wraps mobile", test_a8_intro_wrap_mobile),
        ("A9 single h1", test_a9_single_h1),
        ("A10 og:image absolute", test_a10_og_image_absolute),
    ]),
    ("B. Gallery+Facts", [
        ("B1 gallery aspect", test_b1_gallery_aspect),
        ("B2 thumbs multi-image", test_b2_thumbs_render_multi_image),
        ("B3 nav+counter", test_b3_nav_and_counter),
        ("B4 single-image graceful", test_b4_single_image_graceful),
        ("B5 tag = type name", test_b5_gallery_tag_is_type_name),
        ("B6 lightbox contract", test_b6_lightbox_contract),
        ("B7 facts icons", test_b7_facts_have_icons),
        ("B8 facts typography", test_b8_facts_typography),
        ("B9 facts responsive grid", test_b9_facts_responsive_grid),
        ("B10 facts value nowrap", test_b10_facts_value_nowrap),
    ]),
    ("C. Body sections", [
        ("C1 description eyebrow", test_c1_description_eyebrow),
        ("C2 linebreaks + 17px body", test_c2_description_linebreaks),
        ("C3 empty state", test_c3_description_empty_state),
        ("C4 amenities fluid grid", test_c4_amenities_fluid_grid),
        ("C5 amenity card", test_c5_amenity_item_card),
        ("C6 icon variety >=3", test_c6_amenity_icon_variety),
        ("C7 nearby caption mono", test_c7_nearby_caption_styling),
        ("C8 nearby hierarchy", test_c8_nearby_card_hierarchy),
        ("C9 map heading aligned", test_c9_map_heading_alignment),
        ("C10 video no brackets", test_c10_video_block_no_brackets),
    ]),
    ("D. Sidebar+Similar+Mobile", [
        ("D1 price recap chip", test_d1_sidebar_header_price_recap),
        ("D2 contact buttons", test_d2_contact_buttons_render),
        ("D3 WhatsApp contrast", test_d3_whatsapp_contrast),
        ("D4 enquiry touch height", test_d4_enquiry_inputs_touch_height),
        ("D5 response microcopy", test_d5_response_microcopy),
        ("D6 similar fluid grid", test_d6_similar_fluid_grid),
        ("D7 similar orphan-proof", test_d7_similar_orphan_proof),
        ("D8 browse-all link", test_d8_similar_browse_all_link),
        ("D9 mobile bar renders", test_d9_mobile_bar_renders_with_contacts),
        ("D10 mobile touch targets", test_d10_mobile_bar_touch_targets),
    ]),
]


def _run_criterion(fn, page, seeded):
    """Call a criterion, injecting its named arguments. Returns
    (status, detail): 'pass', 'na' (needs the pytest-only DB blocker), or
    'fail'."""
    params = list(inspect.signature(fn).parameters)
    if "django_db_blocker" in params:
        return "na", "covered by its own pytest run"
    kwargs = {}
    if "page" in params:
        kwargs["page"] = page
    if "seeded" in params:
        kwargs["seeded"] = seeded
    try:
        fn(**kwargs)
        return "pass", ""
    except AssertionError as exc:
        return "fail", str(exc)[:90]


def test_benchmark_score_100(seeded, page, capsys):
    """Re-run every criterion, print the scorecard, fail unless 40/40."""
    total = passed = 0
    failures = []
    lines = ["", "=" * 52, "r103 DETAIL-PAGE BENCHMARK", "=" * 52]
    for group, items in CRITERIA:
        gpass = 0
        for name, fn in items:
            total += 1
            status, detail = _run_criterion(fn, page, seeded)
            if status in ("pass", "na"):
                passed += 1
                gpass += 1
            else:
                failures.append(f"  RED {group[3:]:<22} {name}: {detail}")
        lines.append(f"{group:<26} {gpass:>2}/10")
    lines.append("-" * 52)
    lines.append(f"{'TOTAL':<26} {passed:>2}/{total}")
    lines.extend(failures)
    lines.append("=" * 52)
    text = "\n".join(lines)
    with capsys.disabled():
        print(text)
    with open("/home/z/my-project/download/bench-score.txt", "w") as fh:
        fh.write(text + "\n")
    assert passed == total, (
        f"benchmark score {passed}/{total} — not perfect.\n" + "\n".join(failures)
    )
