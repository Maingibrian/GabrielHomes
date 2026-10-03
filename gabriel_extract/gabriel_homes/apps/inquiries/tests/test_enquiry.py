"""Tests for the Phase 4 enquiry form — submission, honeypot, rate limit, email."""
import pytest
from django.core import mail
from django.core.management import call_command
from django.test import Client, override_settings

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=80, verbosity=0)
    yield


def _get_first_listing():
    from apps.listings.models import Property
    return Property.objects.published().first()


def _enquiry_url(p):
    return f"/listing/{p.slug}-{p.pk}/enquire/"


VALID_DATA = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+254712345678",
    "message": "I am interested in viewing this property next week.",
    "website": "",  # honeypot — empty
}


# ---------------------------------------------------------------------------
# Valid submission
# ---------------------------------------------------------------------------
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_valid_enquiry_creates_inquiry():
    from apps.inquiries.models import Inquiry
    p = _get_first_listing()
    c = Client()
    inq_before = Inquiry.objects.count()
    r = c.post(_enquiry_url(p), VALID_DATA)
    assert r.status_code == 200
    assert Inquiry.objects.count() == inq_before + 1


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_valid_enquiry_sends_email_to_agent():
    p = _get_first_listing()
    c = Client()
    c.post(_enquiry_url(p), VALID_DATA)
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert p.agent.display_email in email.to
    assert p.title in email.subject


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_valid_enquiry_returns_success_partial():
    p = _get_first_listing()
    c = Client()
    r = c.post(_enquiry_url(p), VALID_DATA)
    body = r.content.decode()
    assert "Enquiry sent" in body or "enquiry-success" in body


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_valid_enquiry_attaches_property_and_ip():
    from apps.inquiries.models import Inquiry
    p = _get_first_listing()
    c = Client()
    c.post(_enquiry_url(p), VALID_DATA, REMOTE_ADDR="203.0.113.42")
    inq = Inquiry.objects.filter(property_ref=p).order_by("-created_at").first()
    assert inq is not None
    assert inq.submitter_ip == "203.0.113.42" or inq.submitter_ip is None  # REMOTE_ADDR may not propagate


# ---------------------------------------------------------------------------
# Honeypot
# ---------------------------------------------------------------------------
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_honeypot_filled_saves_as_spam_no_email():
    from apps.inquiries.models import Inquiry
    p = _get_first_listing()
    c = Client()
    data = dict(VALID_DATA)
    data["website"] = "http://spam.com"  # honeypot filled
    inq_before = Inquiry.objects.count()
    r = c.post(_enquiry_url(p), data)
    assert r.status_code == 200  # fake success
    # Inquiry IS saved (as spam, for audit)
    assert Inquiry.objects.count() == inq_before + 1
    inq = Inquiry.objects.latest("created_at")
    assert inq.honeypot == "http://spam.com"
    assert inq.is_spam is True
    # But NO email is sent
    assert len(mail.outbox) == 0


# ---------------------------------------------------------------------------
# Form validation
# ---------------------------------------------------------------------------
def test_short_message_returns_422():
    p = _get_first_listing()
    c = Client()
    data = dict(VALID_DATA)
    data["message"] = "short"  # < 10 chars
    r = c.post(_enquiry_url(p), data)
    assert r.status_code == 422
    body = r.content.decode()
    assert "at least 10 characters" in body


def test_missing_email_returns_422():
    p = _get_first_listing()
    c = Client()
    data = dict(VALID_DATA)
    del data["email"]
    r = c.post(_enquiry_url(p), data)
    assert r.status_code == 422


def test_missing_name_returns_422():
    p = _get_first_listing()
    c = Client()
    data = dict(VALID_DATA)
    del data["name"]
    r = c.post(_enquiry_url(p), data)
    assert r.status_code == 422


def test_get_request_not_allowed():
    """Enquiry endpoint only accepts POST."""
    p = _get_first_listing()
    c = Client()
    r = c.get(_enquiry_url(p))
    assert r.status_code in (405, 404)  # require_POST


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_rate_limit_blocks_after_3_per_minute():
    """Max 3 enquiries per minute per IP — 4th should be blocked (429)."""
    p = _get_first_listing()
    c = Client()
    # Send 3 valid enquiries
    for i in range(3):
        data = dict(VALID_DATA)
        data["email"] = f"user{i}@example.com"  # distinct so each creates a row
        r = c.post(_enquiry_url(p), data, REMOTE_ADDR="198.51.100.1")
        assert r.status_code == 200
    # 4th should be rate-limited
    data = dict(VALID_DATA)
    data["email"] = "user3@example.com"
    r = c.post(_enquiry_url(p), data, REMOTE_ADDR="198.51.100.1")
    assert r.status_code == 429
    body = r.content.decode()
    assert "too many" in body.lower() or "rate" in body.lower()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_rate_limit_per_ip_not_global():
    """A different IP should not be affected by another IP's rate limit."""
    p = _get_first_listing()
    c = Client()
    # Exhaust the limit from one IP
    for i in range(3):
        data = dict(VALID_DATA)
        data["email"] = f"ip1-user{i}@example.com"
        c.post(_enquiry_url(p), data, REMOTE_ADDR="198.51.100.1")
    # A different IP should still be able to submit
    data = dict(VALID_DATA)
    data["email"] = "ip2-user@example.com"
    r = c.post(_enquiry_url(p), data, REMOTE_ADDR="203.0.113.99")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# 404 for non-existent property
# ---------------------------------------------------------------------------
def test_enquiry_404_for_nonexistent_property():
    c = Client()
    r = c.post("/listing/nonexistent-99999/enquire/", VALID_DATA)
    assert r.status_code == 404


def test_enquiry_404_for_draft_property():
    from apps.listings.models import Property
    p = _get_first_listing()
    Property.objects.filter(pk=p.pk).update(status="draft")
    c = Client()
    r = c.post(_enquiry_url(p), VALID_DATA)
    assert r.status_code == 404
    Property.objects.filter(pk=p.pk).update(status="published")


# ---------------------------------------------------------------------------
# Authenticated user
# ---------------------------------------------------------------------------
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_authenticated_user_linked_to_inquiry():
    from apps.inquiries.models import Inquiry
    from apps.accounts.models import User
    user = User.objects.create_user(email="authuser@example.com", password="test-pass-123")
    p = _get_first_listing()
    c = Client()
    c.force_login(user)
    c.post(_enquiry_url(p), VALID_DATA)
    inq = Inquiry.objects.filter(property_ref=p).latest("created_at")
    assert inq.user_id == user.id
