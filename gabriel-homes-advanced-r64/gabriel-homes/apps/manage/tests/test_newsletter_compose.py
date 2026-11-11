"""r75 (BACKEND-PLAN 3D) — newsletter compose: /manage/site-content/newsletter/.

Pinned here: the owner gate, the subscriber numbers, the pick-list +
preview + send flow, the recipients rule (confirmed, not unsubscribed,
only — the pending and the gone never receive), the recording of every
sent issue, and the 10-listing cap.
"""
import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client

from apps.agents.models import AgencyProfile
from apps.core.models import NewsletterIssue, NewsletterSubscriber
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location

pytestmark = [pytest.mark.django_db, pytest.mark.override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)]

LOGIN_URL = "/account/login/"
URL = "/manage/site-content/newsletter/"


@pytest.fixture(autouse=True)
def base(db):
    User = get_user_model()
    county = Location.objects.create(name="Mombasa", slug="mombasa", level="county")
    hood = Location.objects.create(name="Nyali", slug="nyali", level="neighbourhood", parent=county)
    ptype = PropertyType.objects.create(name="Apartment", slug_plural="flats-apartments", slug_single="apartment")
    agent_user = User.objects.create(email="agency-user@test.com", full_name="Test Agency", is_agent=True)
    agency = AgencyProfile.objects.create(user=agent_user, name="Test Agency", slug="test-agency")
    for i in range(3):
        Property.objects.create(
            title=f"Listing number {i}", slug=f"listing-{i}", listing_type="sale",
            property_type=ptype, location=hood, price=10_000_000 + i, agent=agency,
            status=Property.Status.PUBLISHED, published_at=f"2026-01-0{i + 1}T10:00:00Z",
        )


def _sub(email, confirmed=True, unsubscribed=False):
    from django.utils import timezone

    row = NewsletterSubscriber.objects.create(
        email=email, consent_at=timezone.now(), token=f"tok-{email}",
    )
    if confirmed and not unsubscribed:
        row.confirmed_at = timezone.now()
    if unsubscribed:
        row.unsubscribed_at = timezone.now()
    row.save()
    return row


@pytest.fixture
def owner():
    User = get_user_model()
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


def _pks(n=2):
    return [str(pk) for pk in Property.objects.published().order_by("pk").values_list("pk", flat=True)[:n]]


# ---------------------------------------------------------------------------
# The gate + the screen
# ---------------------------------------------------------------------------
def test_anon_is_sent_to_login():
    r = Client().get(URL)
    assert r.status_code == 302
    assert LOGIN_URL in r["Location"]


def test_screen_shows_subscriber_numbers_and_past_issues(owner):
    _sub("happy@example.com")
    _sub("waiting@example.com", confirmed=False)
    _sub("gone@example.com", unsubscribed=True)
    r = owner.get(URL)
    assert r.status_code == 200
    assert b"Confirmed (get the newsletter)" in r.content
    assert b"Nothing sent yet" in r.content


# ---------------------------------------------------------------------------
# Preview — see exactly what goes out
# ---------------------------------------------------------------------------
def test_preview_renders_the_picked_listings(owner):
    _sub("happy@example.com")
    r = owner.post(URL, {"action": "preview", "listings": _pks(2)})
    assert r.status_code == 200
    assert b"manage-preview__box" in r.content
    assert b"Listing number 0" in r.content
    assert b"Listing number 2" not in r.content
    assert b"Send to 1" in r.content


def test_preview_with_nothing_picked_is_refused(owner):
    r = owner.post(URL, {"action": "preview", "listings": []})
    assert r.status_code == 302
    assert not r["Location"].startswith("http")  # back to the same screen


def test_eleven_valid_picks_is_refused(owner):
    # Grow to 11 live listings, then try to pick all of them.
    base_type = PropertyType.objects.first()
    base_loc = Location.objects.first()
    base_agency = AgencyProfile.objects.first()
    for i in range(3, 11):
        Property.objects.create(
            title=f"Listing number {i}", slug=f"listing-{i}", listing_type="sale",
            property_type=base_type, location=base_loc, price=10_000_000 + i,
            agent=base_agency, status=Property.Status.PUBLISHED,
            published_at=f"2026-01-10T10:00:0{i}Z",
        )
    all_pks = [str(pk) for pk in Property.objects.published().values_list("pk", flat=True)[:11]]
    assert len(all_pks) == 11
    r = owner.post(URL, {"action": "preview", "listings": all_pks})
    # Refused — back to the form, no preview rendered.
    assert r.status_code == 302


# ---------------------------------------------------------------------------
# Send — confirmed subscribers only, every send recorded
# ---------------------------------------------------------------------------
def test_send_reaches_confirmed_subscribers_only(owner):
    _sub("happy@example.com")
    _sub("waiting@example.com", confirmed=False)
    _sub("gone@example.com", unsubscribed=True)
    r = owner.post(URL, {"action": "send", "listings": _pks(2)})
    assert r.status_code == 302

    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == ["happy@example.com"]
    assert "2 new listings" in msg.subject
    assert "Listing number 0" in msg.body
    assert "List-Unsubscribe" in msg.extra_headers
    assert "tok-happy@example.com" in msg.body

    issue = NewsletterIssue.objects.get()
    assert issue.listing_count == 2
    assert issue.recipient_count == 1


def test_send_with_no_subscribers_is_an_honest_refusal(owner):
    r = owner.post(URL, {"action": "send", "listings": _pks(1)})
    assert r.status_code == 302
    assert len(mail.outbox) == 0
    assert NewsletterIssue.objects.count() == 0


def test_picked_ids_that_are_not_live_are_dropped(owner):
    _sub("happy@example.com")
    draft = Property.objects.create(
        title="A draft", slug="a-draft", listing_type="sale",
        property_type=PropertyType.objects.first(), location=Location.objects.first(),
        price=1, agent=AgencyProfile.objects.first(), status=Property.Status.DRAFT,
    )
    r = owner.post(URL, {"action": "send", "listings": [str(draft.pk)]})
    assert r.status_code == 302
    assert len(mail.outbox) == 0  # nothing live was picked -> honest refusal
    assert NewsletterIssue.objects.count() == 0


def test_past_issues_list_after_sending(owner):
    _sub("happy@example.com")
    owner.post(URL, {"action": "send", "listings": _pks(1)})
    r = owner.get(URL)
    assert b"Nothing sent yet" not in r.content
    assert b"sent to 1" in r.content
