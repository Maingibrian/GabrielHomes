"""P0-1 — the public site must not claim "Verified".

The old Framer badge said "Verified"; the loop protocol forbids unprovable
"verified" badges. The badge is now "Checked", rendered only when the owner
flag (stored non-destructively in the existing is_verified column) is set,
and all public copy uses checked language.

Note: the CSS class hooks (`listing-card__verified`, `detail-intro__checked`)
keep their names — they are invisible to users and renaming them would churn
the design files; the visible text is the claim, and that is what we sweep.

P0-2 (run 3) closed the last gap: /agents/ and /agents/<slug>/ no longer
say "Verified" — the hero, count heading, card labels, profile eyebrow and
the Python-built meta descriptions are all honest, and migration 0005
self-heals the seeded bio that 0003 shipped with "verified details".

P1-1 (run 5) went further: /agents/ and /agents/<slug>/ are now PERMANENT
redirects to /about/ (single-owner mode), so the agent-page-specific tests
below became redirect assertions. The directory/profile templates remain
in-repo, unrouted (see apps/agents/urls.py).
"""
import re

import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db


def _strip_class_attrs(html: str) -> str:
    """Remove class="..." attributes so internal CSS hooks don't trip the
    visible-wording assertions."""
    return re.sub(r'class="[^"]*"', "", html)


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test (fresh demo data, no images — fast)."""
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)
    yield


def _first_published():
    from apps.listings.models import Property

    return Property.objects.published().order_by("pk").first()


def _set_flag(instance, value):
    from apps.listings.models import Property

    Property.objects.filter(pk=instance.pk).update(is_verified=value)
    instance.refresh_from_db()


# ---------------------------------------------------------------------------
# Listing card badge (search results)
# ---------------------------------------------------------------------------
def test_card_badge_shown_when_flagged(client):
    from apps.listings.models import Property

    # Flag every published listing so page 1 (newest-first sort) is covered.
    Property.objects.update(is_verified=True)

    html = client.get("/properties/").content.decode()
    assert 'class="listing-card__verified"' in html
    assert "Checked" in html
    assert "Verified" not in html


def test_card_badge_hidden_when_unflagged(client):
    from apps.listings.models import Property

    Property.objects.update(is_verified=False)
    html = client.get("/properties/").content.decode()
    assert 'class="listing-card__verified"' not in html
    assert "Verified" not in html


# ---------------------------------------------------------------------------
# Detail page badge + agency card
# ---------------------------------------------------------------------------
def test_detail_badge_follows_flag(client):
    from apps.listings.models import Property

    p = _first_published()
    url = p.get_absolute_url()

    Property.objects.update(is_verified=False)
    _set_flag(p, True)
    html = client.get(url).content.decode()
    assert 'class="detail-intro__checked"' in html
    assert "Checked" in html

    _set_flag(p, False)
    html = client.get(url).content.decode()
    assert 'class="detail-intro__checked"' not in html


def test_detail_agent_card_has_no_verified_claim(client):
    """The sticky contact card must not claim "Verified agency" (P1-2 will
    replace the whole agency card with the brand contact card)."""
    url = _first_published().get_absolute_url()
    html = _strip_class_attrs(client.get(url).content.decode())
    assert "Verified agency" not in html
    assert "verified" not in html.lower()


# ---------------------------------------------------------------------------
# Public copy sweep — no "verified" anywhere in the page chrome or seed copy
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "url",
    ["/", "/about/", "/checks/", "/services/", "/terms/", "/privacy/", "/contact/", "/agents/"],
)
def test_public_pages_free_of_verified_wording(client, url):
    html = _strip_class_attrs(client.get(url).content.decode())
    assert "verified" not in html.lower(), f"'verified' found on {url}"


def test_detail_free_of_verified_wording(client):
    """Fresh seed copy says "Checks completed before publication..." — the
    detail page must contain no visible "verified" at all (chrome, badge,
    JSON-LD, seed description)."""
    url = _first_published().get_absolute_url()
    html = _strip_class_attrs(client.get(url).content.decode())
    assert "verified" not in html.lower()


def test_seed_description_template_is_honest():
    """The seed's own description template must not carry the old claim."""
    from apps.listings.management.commands.seed_demo import DESCRIPTION_TEMPLATE

    assert "verified" not in DESCRIPTION_TEMPLATE.lower()
    # P1-3: single-owner phrasing — enquirers contact Gabriel Homes directly.
    assert "listing agent" not in DESCRIPTION_TEMPLATE.lower()
    assert "Contact Gabriel Homes directly" in DESCRIPTION_TEMPLATE


# ---------------------------------------------------------------------------
# P0-2 — agent directory + agency profile pages
# ---------------------------------------------------------------------------
def _first_agency():
    from apps.agents.models import AgencyProfile

    return AgencyProfile.objects.public().order_by("pk").first()


def test_directory_count_heading_is_honest(client):
    """P1-1: the directory itself is gone — old URLs must 301 to /about/
    (the honest "N agencies on Gabriel Homes." heading lives in the retired
    template only)."""
    r = client.get("/agents/")
    assert r.status_code == 301
    assert r["Location"] == "/about/"


def test_agency_profile_free_of_verified_wording(client):
    """P1-1: profile URLs redirect permanently — nothing agency-branded
    renders at the old address."""
    agency = _first_agency()
    r = client.get(f"/agents/{agency.slug}/")
    assert r.status_code == 301
    assert r["Location"] == "/about/"


def test_public_pages_ignore_agency_is_verified_flag(client):
    """Even with is_verified set, no public page may show "Verified agency"
    — and since P1-1 the agent URLs redirect regardless of the flag (it is
    storage for the owner dashboard toggle only)."""
    from apps.agents.models import AgencyProfile

    AgencyProfile.objects.update(is_verified=True)
    r = client.get("/agents/")
    assert r.status_code == 301
    agency = _first_agency()
    r = client.get(f"/agents/{agency.slug}/")
    assert r.status_code == 301
    # And the redirect target stays honest.
    html = _strip_class_attrs(client.get("/about/").content.decode())
    assert "Verified agency" not in html
    assert "verified" not in html.lower()


# ---------------------------------------------------------------------------
# P0-2 — seed-bio migrations must not reintroduce "verified" on any install
# ---------------------------------------------------------------------------
def test_seed_bio_migration_swap_covers_0003():
    """0003 shipped with "verified details" in one bio; 0005 must swap it
    everywhere 0003 can write it, and stay idempotent."""
    import importlib

    m3 = importlib.import_module(
        "apps.agents.migrations.0003_fix_seed_agency_bios"
    )
    m5 = importlib.import_module(
        "apps.agents.migrations.0005_fix_seed_bio_checked_wording"
    )

    for slug, bio in m3.REAL_BIOS.items():
        fixed = m5.swap_verified_bio(bio)
        assert "verified" not in fixed.lower(), f"bio for {slug} still claims verified"
    # Idempotent: swapping an already-swapped bio changes nothing.
    assert m5.swap_verified_bio(m5.NEW_PHRASE) == m5.NEW_PHRASE
    # Owner-customised bios without the phrase pass through untouched.
    assert m5.swap_verified_bio("A family agency in Kilifi.") == "A family agency in Kilifi."


def test_seeded_agency_bios_clean():
    from apps.agents.models import AgencyProfile

    for agency in AgencyProfile.objects.all():
        assert "verified" not in (agency.bio or "").lower(), agency.slug
