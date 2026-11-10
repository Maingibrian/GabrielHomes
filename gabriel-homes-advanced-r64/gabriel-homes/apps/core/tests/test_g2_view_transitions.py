"""G2 — shared-element page transitions proving tests.

Binary checks (SCORECARD G2):
1. `@view-transition { navigation: auto }` lives inside `@supports` in base.css.
2. Unique per-listing view-transition-name on the listing card/row image AND
   the detail hero (renders list + detail; names present and unique).
3. Off under fx=none AND with JS blocked (fail-closed, D-LOOP-16b): base.css
   must opt the root OUT by default and only back in under data-fx=rich|lite,
   plus an override that kills the inline per-listing names when the gate is
   absent or none.
4. HTMX pagination/partials unaffected: the grid partial carries the same
   unique names (existing pagination tests stay green — they run in the same
   suite).

Design (D-LOOP-22b): names are inline styles (`view-transition-name:
prop-<pk>`) — CSP style-src 'unsafe-inline' already permits them. The root
opt-out uses `html { view-transition-name: none }` (kills the default root
snapshot) re-enabled only for html[data-fx=rich|lite]; the inline names are
neutralised via an attribute-substring override under the same conditions.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
BASE_CSS = (REPO / "static" / "css" / "base.css").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test (same isolation as test_detail), then attach a
    small generated image to every published property: seed_demo runs with
    no_images=True (suite convention), but the names ride on the card/row
    <img> elements, which only render when a property has an image."""
    from django.core.cache import cache
    cache.clear()
    call_command("seed_demo", no_images=True, target=80, verbosity=0,
                 i_know_this_is_demo=True)
    _attach_tiny_images()
    yield


def _attach_tiny_images():
    """Generate a 760x520 JPEG in-memory per published property (PIL, local,
    no network — mirrors what seed_demo does when images are enabled)."""
    import io

    from django.core.files.base import File
    from PIL import Image as PILImage

    from apps.listings.models import Property, PropertyImage
    for p in Property.objects.published():
        buf = io.BytesIO()
        PILImage.new("RGB", (760, 520), (196, 178, 158)).save(buf, "JPEG")
        buf.seek(0)
        PropertyImage.objects.create(
            property=p, image=File(buf, name=f"g2-fix-{p.pk}.jpg"))


def _names_in(html: str):
    """All per-listing view-transition names found in a rendered page."""
    return re.findall(r"view-transition-name:\s*(prop-\d+)", html)


# ---------------------------------------------------------------------------
# 1. the opt-in rule is feature-guarded
# ---------------------------------------------------------------------------
def _supports_blocks(css: str):
    """Return the contents of every top-level @supports block (brace-matched)."""
    blocks = []
    for m in re.finditer(r"@supports[^{]*\{", css):
        i = m.end()
        depth = 1
        while i < len(css) and depth:
            if css[i] == "{":
                depth += 1
            elif css[i] == "}":
                depth -= 1
            i += 1
        blocks.append(css[m.end():i - 1])
    return blocks


def test_view_transition_optin_inside_supports():
    hit = [b for b in _supports_blocks(BASE_CSS)
           if "@view-transition" in b and "navigation" in b and "auto" in b]
    assert hit, (
        "base.css must carry @view-transition { navigation: auto } inside an "
        "@supports block (progressive enhancement, binary check 1)")


def test_transitions_fail_closed_without_gate():
    """JS blocked (no data-fx) or data-fx=none ⇒ no transition at all."""
    hit = [b for b in _supports_blocks(BASE_CSS)
           if "@view-transition" in b]
    assert hit, "@view-transition opt-in block missing"
    block = hit[0]
    # root opt-out: default none, re-enabled only under rich/lite
    assert re.search(r"html\s*\{[^}]*view-transition-name:\s*none", block), (
        "base.css must set html { view-transition-name: none } by default "
        "(fail-closed with JS blocked, D-LOOP-16b)")
    assert re.search(
        r'html\[data-fx="(?:rich|lite)"\][^{]*\{[^}]*view-transition-name:\s*root',
        block), ("base.css must re-enable the root transition only under "
                 "data-fx=rich or lite")
    # the inline per-listing names must be neutralised when the gate is off
    assert 'html:not([data-fx]) [style*="view-transition-name"]' in block and \
        'html[data-fx="none"] [style*="view-transition-name"]' in block, (
        "base.css must kill inline per-listing names under no-gate and fx=none")


# ---------------------------------------------------------------------------
# 2. names on the list/card surfaces — present and unique
# ---------------------------------------------------------------------------
def test_search_rows_carry_unique_names():
    r = Client().get("/property-for-sale/mombasa/")
    assert r.status_code == 200
    names = _names_in(r.content.decode())
    assert len(names) >= 2, (
        f"search rows must carry per-listing view-transition names "
        f"(found {len(names)})")
    assert len(names) == len(set(names)), f"duplicate names on search: {names}"


def test_home_recommended_cards_carry_unique_names():
    r = Client().get("/")
    assert r.status_code == 200
    names = _names_in(r.content.decode())
    assert len(names) >= 1, "home recommended cards must carry names"
    assert len(names) == len(set(names)), f"duplicate names on home: {names}"


# ---------------------------------------------------------------------------
# 3. the detail hero pairs with its listing
# ---------------------------------------------------------------------------
def test_detail_hero_name_matches_pk():
    from apps.listings.models import Property
    p = Property.objects.published().first()
    r = Client().get(p.get_absolute_url())
    assert r.status_code == 200
    html = r.content.decode()
    assert f"view-transition-name: prop-{p.pk}" in html, (
        f"detail hero must carry view-transition-name prop-{p.pk} so the "
        "list card image pairs with it")


def test_no_duplicate_names_on_detail():
    """Hero + any similar-listing cards must never share a name in one
    document (view-transition-name must be unique per page)."""
    from apps.listings.models import Property
    p = Property.objects.published().first()
    html = Client().get(p.get_absolute_url()).content.decode()
    names = _names_in(html)
    assert len(names) == len(set(names)), (
        f"duplicate view-transition names on detail: "
        f"{[n for n in names if names.count(n) > 1]}")


# ---------------------------------------------------------------------------
# 4. HTMX partials unaffected — same names, still unique
# ---------------------------------------------------------------------------
def test_htmx_grid_partial_carries_names():
    r = Client().get("/property-for-sale/mombasa/", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    names = _names_in(r.content.decode())
    assert len(names) >= 2, "HTMX grid partial must carry the names"
    assert len(names) == len(set(names)), "duplicate names in the HTMX partial"
