"""H1 — home order & diet proving tests.

The home page carries exactly the owner's order (hero, bento, recommended,
nearby) and everything that used to be a home section lives on its
destination page or in the footer — moved, not deleted (runbook §6 H1):

  About        -> /about/      (philosophy + fee disclosure lines)
  Services     -> /services/   (buying / renting / enquiries / listing rows)
  Commitments  -> /checks/     ("What you can hold us to.")
  FAQ          -> footer       (site-wide, details/summary, no JS needed)
  Browse       -> footer       (curated hub links: service counties +
                                type hubs — query-free by design,
                                D-LOOP-18b)
  Newsletter   -> footer       (same form, action unchanged)
  CTA band     -> footer       (closing get-in-touch row)
  Talk-to-us   -> recommended section (channels strip, runbook §6 H1 spec)
                  + the footer "Talk to us" column (was already there)

The trust message ("five checks") may appear in at most 2 places on home.
"""
import re

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Same isolation as test_phase2_home: seed before each test so the
    conditional sections (recommended / nearby / footer browse) render."""
    from django.core.cache import cache
    cache.clear()
    call_command("seed_demo", no_images=True, target=20, verbosity=0,
                 i_know_this_is_demo=True)
    yield
    cache.clear()


def body_of(path: str) -> str:
    r = Client().get(path)
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    return r.content.decode()


def home() -> str:
    return body_of("/")


# ---------------------------------------------------------------------------
# 1. the owner's order
# ---------------------------------------------------------------------------
def test_home_section_id_order_exact():
    ids = re.findall(r'<section[^>]*\bid="([^"]+)"', home())
    assert ids == ["hero", "bento", "recommended", "nearby"], (
        f"home section order must be hero, bento, recommended, nearby — "
        f"got {ids}"
    )


def test_home_has_at_most_seven_top_level_sections():
    count = len(re.findall(r"<section\b", home()))
    assert count <= 7, f"home has {count} top-level sections (max 7)"


def test_trust_message_at_most_two_places_on_home():
    count = len(re.findall(r"five checks", home(), re.IGNORECASE))
    assert count <= 2, (
        f"the five-checks trust message appears {count} times on home "
        f"(max 2) — it lives on /checks/ now"
    )


# ---------------------------------------------------------------------------
# 2. moved content is at its destination — nothing silently deleted
# ---------------------------------------------------------------------------
def test_about_block_lives_on_about_page():
    body = body_of("/about/")
    # r56: the philosophy line is taste-led now (owner round seven);
    # the checked-ledger version lives on /checks/.
    assert "ten homes you'll love" in body, (
        "the home about philosophy line must live on /about/"
    )
    assert "exact amount before you commit" in body, (
        "the buyer-fee disclosure must live on /about/ (footer FAQ)"
    )


def test_services_block_lives_on_services_page():
    body = body_of("/services/")
    for marker in (
        "Find a home to buy",
        "Find a home to rent",
        "List a property with us",
        "Talk to a person",
    ):
        assert marker in body, f"services page missing moved block: {marker!r}"


def test_commitments_block_lives_on_checks_page():
    body = body_of("/checks/")
    assert "What you can hold us to" in body
    assert "No home goes live unchecked" in body
    assert "No invented track record" in body


def test_faq_lives_in_footer():
    body = home()
    assert "Things people ask us" in body
    assert "Who pays your fee?" in body
    assert "How do you choose which homes to list?" in body


def test_browse_links_live_in_footer():
    body = home()
    assert "By location" in body and "By property type" in body
    # at least one live county hub and one live type hub
    assert re.search(r'href="/property-for-sale/[a-z0-9-]+/"', body), (
        "footer must carry the live by-location browse links"
    )
    assert re.search(r'href="/[a-z0-9-]+-for-sale/"', body), (
        "footer must carry the live by-type browse links"
    )


def test_newsletter_lives_in_footer():
    body = home()
    assert 'action="/newsletter/subscribe/"' in body, (
        "the newsletter form must live in the footer now"
    )
    assert "New listings, by email" in body


def test_cta_lives_in_footer():
    body = home()
    assert 'id="footer-cta"' in body, (
        "the closing CTA must live in the footer now"
    )
    assert 'href="/contact/"' in body


def test_talk_to_us_channels_survive_on_home():
    """The old talk-to-us band moved into the recommended section strip +
    the footer column. Honest blank by design: with an empty brand row no
    channel UI renders at all (r12 rule); with channels set, wa.me / tel:
    / mailto: links appear — twice (strip + footer), never a dead band."""
    from apps.core.models import BrandSettings

    body = home()
    assert "[ TALK TO US ]" not in body, (
        "empty brand row must render no channel UI (honest blank)"
    )

    brand = BrandSettings.load()
    brand.whatsapp = "+254 712 000 111"
    brand.phone = "+254 700 000 222"
    brand.email = "hello@example.com"
    brand.save()
    body = home()
    assert "wa.me/" in body
    assert 'href="tel:' in body
    assert "mailto:" in body
    assert 'id="talk-to-us"' not in body, (
        "the standalone talk-to-us band must not remain a home section"
    )
