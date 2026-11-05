"""Newsletter: opt-in, double confirmation, unsubscribe, ten-listing trigger.
Plus the checks page and the removed styleguide."""
import re

import pytest
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.core.models import NewsletterIssue, NewsletterSubscriber
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db


@pytest.fixture
def base_objects(db):
    user = User.objects.create_user(email="nl-agent@test.com", password="nl-pass-123")
    agency = AgencyProfile.objects.create(name="NL agency", slug="nl-agency", user=user)
    loc = Location.objects.create(name="NL place", slug="nl-place", level=Location.Level.COUNTY)
    ptype = PropertyType.objects.create(name="NL type", slug_plural="nl-types")
    return agency, loc, ptype


def _listing(base, i, demo=False):
    agency, loc, ptype = base
    return Property.objects.create(
        title=f"Listing {i}", description="d", listing_type="sale", property_type=ptype,
        location=loc, price="1000000", status="published", agent=agency,
        is_demo=demo, published_at=timezone.now(),
    )


def _confirm_link(body):
    return re.search(r"/newsletter/confirm/([0-9a-f]+)/", body).group(1)


def test_subscribe_creates_pending_opt_in_and_sends_confirmation(client):
    r = client.post("/newsletter/subscribe/", {"email": "Buyer@Example.com", "consent": "yes"})
    assert r.status_code == 200
    sub = NewsletterSubscriber.objects.get(email="buyer@example.com")
    assert sub.confirmed_at is None
    assert not sub.is_active
    assert len(mail.outbox) == 1
    assert "/newsletter/confirm/" in mail.outbox[0].body


def test_subscribe_without_consent_is_refused(client):
    r = client.post("/newsletter/subscribe/", {"email": "x@example.com"})
    assert r.status_code == 302
    assert not NewsletterSubscriber.objects.exists()
    assert len(mail.outbox) == 0


def test_confirm_activates_and_unsubscribe_stops_mail(client):
    client.post("/newsletter/subscribe/", {"email": "a@example.com", "consent": "yes"})
    token = _confirm_link(mail.outbox[0].body)
    assert client.get(f"/newsletter/confirm/{token}/").status_code == 200
    sub = NewsletterSubscriber.objects.get(email="a@example.com")
    assert sub.is_active
    assert client.get(f"/newsletter/unsubscribe/{token}/").status_code == 200
    sub.refresh_from_db()
    assert sub.unsubscribed_at is not None and not sub.is_active


def test_bad_tokens_return_404(client):
    assert client.get("/newsletter/confirm/nope/").status_code == 404
    assert client.get("/newsletter/unsubscribe/nope/").status_code == 404


def test_no_send_below_ten_new_listings(base_objects):
    for i in range(9):
        _listing(base_objects, i)
    NewsletterSubscriber.objects.create(email="c@example.com", consent_at=timezone.now(),
                                        confirmed_at=timezone.now(), token="t1")
    call_command("send_newsletter", verbosity=0)
    assert len(mail.outbox) == 0
    assert NewsletterIssue.objects.count() == 0


def test_sends_at_ten_only_to_confirmed_and_not_unsubscribed(base_objects):
    for i in range(10):
        _listing(base_objects, i)
    now = timezone.now()
    NewsletterSubscriber.objects.create(email="ok@example.com", consent_at=now, confirmed_at=now, token="ok1")
    NewsletterSubscriber.objects.create(email="pending@example.com", consent_at=now, token="p1")
    NewsletterSubscriber.objects.create(email="gone@example.com", consent_at=now, confirmed_at=now,
                                        unsubscribed_at=now, token="g1")
    call_command("send_newsletter", verbosity=0)
    recipients = sorted(m.to[0] for m in mail.outbox)
    assert recipients == ["ok@example.com"]
    issue = NewsletterIssue.objects.get()
    assert issue.listing_count == 10 and issue.recipient_count == 1
    body = mail.outbox[0].body
    assert "Unsubscribe:" in body and "/newsletter/unsubscribe/ok1/" in body
    assert mail.outbox[0].extra_headers.get("List-Unsubscribe")


def test_demo_listings_never_count_toward_the_trigger(base_objects):
    for i in range(10):
        _listing(base_objects, i, demo=True)
    now = timezone.now()
    NewsletterSubscriber.objects.create(email="d@example.com", consent_at=now, confirmed_at=now, token="d1")
    call_command("send_newsletter", verbosity=0)
    assert len(mail.outbox) == 0


def test_second_issue_waits_for_ten_more(base_objects):
    for i in range(10):
        _listing(base_objects, i)
    now = timezone.now()
    NewsletterSubscriber.objects.create(email="e@example.com", consent_at=now, confirmed_at=now, token="e1")
    call_command("send_newsletter", verbosity=0)
    assert len(mail.outbox) == 1
    call_command("send_newsletter", verbosity=0)
    assert len(mail.outbox) == 1          # nothing new since the last issue
    for i in range(10, 19):
        _listing(base_objects, i)
    call_command("send_newsletter", verbosity=0)
    assert len(mail.outbox) == 1          # nine new: still below threshold
    _listing(base_objects, 19)
    call_command("send_newsletter", verbosity=0)
    assert len(mail.outbox) == 2


def test_index_has_optin_form(client):
    cache.clear()
    body = client.get("/").content.decode()
    assert 'action="/newsletter/subscribe/"' in body
    assert 'name="consent" value="yes" required' in body


def test_checks_page_lists_the_five_checks(client):
    body = client.get("/checks/").content.decode()
    assert client.get("/checks/").status_code == 200
    for label in ["Ownership", "Written mandate", "Site visit", "Price and details in writing", "Encumbrances"]:
        assert label in body
    assert "/checks/" in client.get("/sitemap.xml").content.decode()


def test_styleguide_is_removed(client):
    assert client.get("/styleguide/").status_code == 404
    assert "styleguide" not in client.get("/robots.txt").content.decode()


@pytest.mark.parametrize("nxt,expected", [
    ("https://evil.example.com/", "/#newsletter"),
    ("//evil.example.com/", "/#newsletter"),
    ("/\\\\evil.example.com", "/#newsletter"),
])
def test_bad_redirect_target_is_refused(client, nxt, expected):
    r = client.post("/newsletter/subscribe/", {"email": "bad", "next": nxt})
    assert r.status_code == 302
    assert r["Location"] == expected
