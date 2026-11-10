"""Security regression tests: JSON-LD XSS via listing title (PLAN task S1, defect D-XSS).

A listing title containing `</script>` must not break out of the JSON-LD
<script type="application/ld+json"> block on the detail page.
"""
import json
import re

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils.text import slugify

pytestmark = pytest.mark.django_db

PAYLOAD = "</script><img src=x onerror=alert(1)>"


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test."""
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)
    yield


def _listing_with_title(title):
    from apps.listings.models import Property
    base = Property.objects.published().first()
    # Update a published row in place so the URL stays routable.
    Property.objects.filter(pk=base.pk).update(title=title)
    base.refresh_from_db()
    return base


def test_json_ld_title_cannot_break_out_of_script_tag():
    """The raw payload must never appear in the response body."""
    p = _listing_with_title(PAYLOAD)
    c = Client()
    r = c.get(p.get_absolute_url())
    body = r.content.decode()
    assert "</script><img" not in body
    assert 'onerror=alert(1)">' not in body
    # and the page still renders normally
    assert r.status_code == 200


def test_json_ld_block_still_parses_and_contains_title():
    """The JSON-LD block survives and round-trips the hostile title as JSON."""
    p = _listing_with_title(PAYLOAD)
    c = Client()
    r = c.get(p.get_absolute_url())
    body = r.content.decode()
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', body, re.DOTALL)
    assert match is not None
    data = json.loads(match.group(1).strip())
    assert data["@context"] == "https://schema.org"
    assert data["name"] == PAYLOAD


def test_json_ld_escapes_are_json_native():
    """Escaping must use JSON-native \\u003C sequences, not HTML entities
    (HTML entities inside a JSON-LD script would corrupt the data)."""
    p = _listing_with_title(PAYLOAD)
    c = Client()
    r = c.get(p.get_absolute_url())
    body = r.content.decode()
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', body, re.DOTALL)
    raw = match.group(1)
    assert "\\u003C" in raw  # < escaped as JSON-native sequence
    assert "&lt;" not in raw  # no HTML entity escaping
