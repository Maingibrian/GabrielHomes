"""P1-4 — enquiry routing in single-owner mode.

Public enquiries must reach THE OWNER, whoever owns the (legacy) listing
row:
  * ``settings.OWNER_EMAIL`` set  -> every notification goes there.
  * OWNER_EMAIL unset/blank (dev/demo) -> legacy fallback: the listing
    agent's own display email, so the flow still demonstrates end-to-end.
  * No recipient at all -> no email, no crash, tracking left untouched.

The owner dashboard inbox (/dashboard/inquiries/) already lists every
agency's enquiries for superusers — the data-level assertion lives here
too: an enquiry made on one agency's listing shows up for the owner with
the enquirer's details.
"""
import pytest
from django.core import mail
from django.core.management import call_command
from django.test import Client, override_settings

from apps.accounts.models import User
from apps.inquiries.models import Inquiry
from apps.listings.models import Property

pytestmark = pytest.mark.django_db

OWNER_INBOX = "owner-inbox@example.com"

SEED_KW = dict(no_images=True, target=12, verbosity=0, i_know_this_is_demo=True)


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", **SEED_KW)
    yield


def _first_listing() -> Property:
    return Property.objects.published().select_related("agent__user").first()


def _enquiry_url(p: Property) -> str:
    return f"/listing/{p.slug}-{p.pk}/enquire/"


VALID_DATA = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+254712345678",
    "message": "I am interested in viewing this property next week.",
    "website": "",  # honeypot — empty
}


def _post_enquiry(p: Property) -> None:
    assert Client().post(_enquiry_url(p), VALID_DATA).status_code == 200


def _owner_client():
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


# ---------------------------------------------------------------------------
# OWNER_EMAIL set — the owner gets everything
# ---------------------------------------------------------------------------
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    OWNER_EMAIL=OWNER_INBOX,
)
def test_owner_email_receives_every_enquiry():
    p = _first_listing()
    _post_enquiry(p)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [OWNER_INBOX]
    assert p.title in mail.outbox[0].subject
    inq = Inquiry.objects.latest("pk")
    assert inq.email_sent_at is not None
    assert inq.email_error == ""


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    OWNER_EMAIL=OWNER_INBOX,
)
def test_owner_routing_survives_agent_with_no_email():
    """The single-owner point: routing never depends on agency data."""
    p = _first_listing()
    agency = p.agent
    agency.email = ""
    agency.save(update_fields=["email"])
    agency.user.email = ""
    agency.user.save(update_fields=["email"])
    assert agency.display_email == ""

    _post_enquiry(p)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [OWNER_INBOX]
    assert Inquiry.objects.latest("pk").email_sent_at is not None


# ---------------------------------------------------------------------------
# OWNER_EMAIL unset/blank — dev/demo fallback to the listing agent
# ---------------------------------------------------------------------------
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_unset_owner_email_falls_back_to_agent():
    p = _first_listing()
    fallback = p.agent.display_email
    assert fallback  # seed gives every agency an address
    _post_enquiry(p)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [fallback]


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    OWNER_EMAIL="   ",  # whitespace-only counts as unset
)
def test_blank_owner_email_treated_as_unset():
    p = _first_listing()
    _post_enquiry(p)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [p.agent.display_email]


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_no_recipient_at_all_leaves_tracking_untouched():
    """OWNER_EMAIL unset AND the agency row has no address: no email, no
    crash, and the S9 tracking columns stay empty (nothing was attempted)."""
    p = _first_listing()
    agency = p.agent
    agency.email = ""
    agency.save(update_fields=["email"])
    agency.user.email = ""
    agency.user.save(update_fields=["email"])

    _post_enquiry(p)
    assert len(mail.outbox) == 0
    inq = Inquiry.objects.latest("pk")
    assert inq.email_sent_at is None
    assert inq.email_error == ""


# ---------------------------------------------------------------------------
# Owner inbox lists enquiries across agencies (data-level)
# ---------------------------------------------------------------------------
def test_owner_inbox_shows_enquiry_details_from_any_agency():
    p = _first_listing()
    _post_enquiry(p)

    c = _owner_client()
    r = c.get("/dashboard/inquiries/")
    assert r.status_code == 200
    html = r.content.decode()
    assert "Jane Doe" in html
    assert "jane@example.com" in html
    assert p.title in html
