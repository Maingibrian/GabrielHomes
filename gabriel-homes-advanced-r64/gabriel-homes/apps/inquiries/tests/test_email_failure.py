"""S9 — Enquiry email failures must be visible, never silent.

Spec (docs/PLAN.md S9):
  * send_mail runs with fail_silently=False inside a try.
  * On success  -> inquiry.email_sent_at is set.
  * On failure  -> inquiry.email_error is set (<=300 chars), logged via
    logger.exception, and the visitor STILL gets the success partial
    (the enquiry itself succeeded; only the notification failed).
  * The agent dashboard shows an "Email not delivered" badge on rows
    where email_error is set.
"""
from unittest import mock

import pytest
from django.core.management import call_command
from django.test import Client, override_settings

from apps.inquiries.models import Inquiry

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)
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
# Success path records email_sent_at
# ---------------------------------------------------------------------------
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_successful_email_sets_email_sent_at():
    p = _get_first_listing()
    c = Client()
    r = c.post(_enquiry_url(p), VALID_DATA)
    assert r.status_code == 200
    inq = Inquiry.objects.latest("pk")
    assert inq.email_sent_at is not None
    assert inq.email_error == ""


# ---------------------------------------------------------------------------
# Failure path: error recorded, visitor still sees success
# ---------------------------------------------------------------------------
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_failed_email_sets_email_error_and_returns_success_partial():
    p = _get_first_listing()
    c = Client()
    with mock.patch("apps.inquiries.views.send_mail",
                    side_effect=RuntimeError("SMTP connection refused")):
        with mock.patch("apps.inquiries.views.logger.exception") as log_exc:
            r = c.post(_enquiry_url(p), VALID_DATA)
    # The visitor must NOT see an error — the enquiry itself was saved.
    assert r.status_code == 200
    assert b"enquiry-success" in r.content or r.context_data is not None
    # Failure is recorded on the inquiry row.
    inq = Inquiry.objects.latest("pk")
    assert inq.email_sent_at is None
    assert "SMTP connection refused" in inq.email_error
    # And it is logged, not swallowed silently.
    log_exc.assert_called_once()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_email_error_field_is_capped_at_300_chars():
    p = _get_first_listing()
    c = Client()
    long_error = "E" * 5000
    with mock.patch("apps.inquiries.views.send_mail",
                    side_effect=RuntimeError(long_error)):
        c.post(_enquiry_url(p), VALID_DATA)
    inq = Inquiry.objects.latest("pk")
    assert len(inq.email_error) <= 300


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_dashboard_shows_email_not_delivered_badge():
    agent_user = _get_first_listing().agent.user
    p = _get_first_listing()
    c = Client()
    with mock.patch("apps.inquiries.views.send_mail",
                    side_effect=RuntimeError("SMTP down")):
        c.post(_enquiry_url(p), VALID_DATA)
    c.force_login(agent_user)
    r = c.get("/dashboard/inquiries/")
    assert r.status_code == 200
    html = r.content.decode()
    assert "Email not delivered" in html


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_dashboard_hides_badge_when_email_sent():
    agent_user = _get_first_listing().agent.user
    p = _get_first_listing()
    c = Client()
    c.post(_enquiry_url(p), VALID_DATA)
    c.force_login(agent_user)
    r = c.get("/dashboard/inquiries/")
    assert r.status_code == 200
    assert "Email not delivered" not in r.content.decode()
