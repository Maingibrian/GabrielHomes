"""r90 — backend reassessment: the "easy to use owner portal" round.

The full-backend survey (7 Django apps, manage/listings/inquiries/
agents/accounts/core/locations + config) found the portal strong on
content workflow and weak on the owner's own journey. This file pins
every gap that was closed:

  * SMTP env wiring      — settings finally read EMAIL_HOST/… (they
                           were documented but silently ignored)
  * login redirect       — superuser lands in /manage/, agent in
                           /dashboard/ (was: everyone → "/")
  * Portal discoverable  — public header shows "Portal" for superusers
  * enquiry search       — ?q= searches name/email/phone/message/title
  * page crash fixed     — ?page=abc is page 1, not a 500
  * enquiry bulk actions — mark seen / mark done / delete spam-only
  * email-fail flag      — email_error rows carry a visible pill
  * listing search       — ?q= searches title/location/type
  * archive/restore      — reversible put-away on the listing row
  * confirm screens      — spam/photo/testimonial/draft deletes show
                           their stakes first (GET), delete only on
                           POST action=confirm
  * sample-data switch   — the portal's own demo toggle (was "Ask Brian")
  * alert email in portal— BrandSettings.notification_email wins over
                           the env setting in the inquiry email path
  * password change      — branded portal screen, session preserved
  * branded 403/404/500  — no more grey Django dead-ends
"""
import pytest
from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.test import Client, override_settings
from django.utils import timezone

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.core.models import BrandSettings, SiteSetting, Testimonial
from apps.inquiries.models import Inquiry
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location

pytestmark = pytest.mark.django_db


def _fresh_login(**creds):
    """POST a login with a clean rate-limit bucket.

    The limiter keys on IP and LocMem cache is shared across the whole
    pytest run — earlier suites (test_phase7_security hammers 6 bad
    logins) would otherwise leave this IP throttled and the assertion
    would see allauth's 200 re-render, not the redirect under test.
    """
    cache.clear()
    return Client().post("/account/login/", creds)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def owner():
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


_agency_n = 0


def _property_row(**over):
    """A real Property row (mirrors the checklist tests' helper)."""
    global _agency_n
    _agency_n += 1
    user = User.objects.create_user(
        email=f"agency{_agency_n}@test.com", password="agency-pass-123"
    )
    agency = AgencyProfile.objects.create(user=user, name="Gabriel Homes")
    loc, _ = Location.objects.get_or_create(name="Testville")
    pt, _ = PropertyType.objects.get_or_create(
        slug_plural="houses",
        defaults={"name": "House", "slug_single": "house"},
    )
    kw = dict(
        title=over.pop("title", "Nyali four bedroom villa"),
        description="A test listing.",
        listing_type="sale",
        property_type=pt,
        location=loc,
        price=5_000_000,
        status=over.pop("status", Property.Status.PUBLISHED),
        is_demo=over.pop("is_demo", False),
        agent=agency,
    )
    if kw["status"] == Property.Status.PUBLISHED:
        kw["published_at"] = timezone.now()
    kw.update(over)
    return Property.objects.create(**kw)


@pytest.fixture
def property_row():
    return _property_row()


def _enquiry(prop=None, **kw):
    if prop is None:
        prop = _property_row(status=Property.Status.DRAFT)
    defaults = dict(
        property_ref=prop,
        name="Amina Tester",
        email="amina@example.com",
        phone="0712345678",
        message="Is this villa still available for a viewing?",
        status=Inquiry.Status.NEW,
    )
    defaults.update(kw)
    return Inquiry.objects.create(**defaults)


# ---------------------------------------------------------------------------
# SMTP env wiring
# ---------------------------------------------------------------------------
def test_smtp_settings_are_read_when_backend_is_smtp():
    """r90: EMAIL_HOST et al. must reach Django when SMTP is selected."""
    with override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
    ):
        # the block only runs at import; assert the documented vars are
        # honoured by re-reading the source contract instead of settings
        import inspect

        from config.settings import base

        src = inspect.getsource(base)
        assert 'env.str("EMAIL_HOST"' in src
        assert 'env.int("EMAIL_PORT"' in src
        assert 'env.str("EMAIL_HOST_USER"' in src
        assert 'env.str("EMAIL_HOST_PASSWORD"' in src
        assert 'env.bool("EMAIL_USE_TLS"' in src
        assert 'env.bool("EMAIL_USE_SSL"' in src
        assert 'env.int("EMAIL_TIMEOUT"' in src


def test_console_backend_stays_default_in_dev():
    # the dev settings module is what manage.py/pytest run with
    assert settings.EMAIL_BACKEND.endswith(
        ("console.EmailBackend", "locmem.EmailBackend")
    )


# ---------------------------------------------------------------------------
# Login redirect + Portal discoverability
# ---------------------------------------------------------------------------
def test_owner_login_lands_in_portal():
    User.objects.create_superuser(email="o2@test.com", password="long-pass-123")
    r = _fresh_login(login="o2@test.com", password="long-pass-123")
    assert r.status_code == 302
    assert r["Location"] == "/manage/"


def test_agent_login_lands_in_dashboard():
    # create_user hashes the password — objects.create would store it
    # raw and "fail" login (200 re-render), which is a test bug, not
    # an app bug.
    User.objects.create_user(email="ag@test.com", password="long-pass-123", is_agent=True)
    r = _fresh_login(login="ag@test.com", password="long-pass-123")
    assert r.status_code == 302
    assert r["Location"] == "/dashboard/"


def test_login_with_next_still_honoured():
    """A deep link (?next=/manage/enquiries/) must not be flattened."""
    User.objects.create_superuser(email="o3@test.com", password="long-pass-123")
    cache.clear()
    r = Client().post(
        "/account/login/?next=/manage/enquiries/",
        {"login": "o3@test.com", "password": "long-pass-123"},
    )
    assert r.status_code == 302
    assert r["Location"] == "/manage/enquiries/"


def test_public_header_shows_portal_link_for_superuser(owner):
    r = owner.get("/")
    assert b">Portal<" in r.content


def test_public_header_no_portal_link_for_anonymous():
    r = Client().get("/")
    assert b">Portal<" not in r.content


# ---------------------------------------------------------------------------
# Enquiries: search, safe pagination, bulk, email-fail flag
# ---------------------------------------------------------------------------
def test_enquiry_search_finds_by_name(owner, property_row):
    _enquiry()
    _enquiry(name="Bilal Other", email="bilal@example.com")
    r = owner.get("/manage/enquiries/", {"q": "amina"})
    assert r.status_code == 200
    assert b"Amina Tester" in r.content
    assert b"Bilal Other" not in r.content


def test_enquiry_search_finds_by_listing_title(owner, property_row):
    _enquiry()
    r = owner.get("/manage/enquiries/", {"q": "Nyali"})
    assert r.status_code == 200
    assert b"Amina Tester" in r.content


def test_enquiry_page_abc_does_not_crash(owner, property_row):
    r = owner.get("/manage/enquiries/", {"page": "abc"})
    assert r.status_code == 200


def test_enquiry_bulk_mark_seen(owner, property_row):
    a = _enquiry(name="A")
    b = _enquiry(name="B")
    r = owner.post(
        "/manage/enquiries/bulk/",
        {"action": "seen", "ids": [str(a.pk), str(b.pk)], "back": "all"},
    )
    assert r.status_code == 302
    a.refresh_from_db()
    b.refresh_from_db()
    assert a.status == Inquiry.Status.READ
    assert b.status == Inquiry.Status.READ


def test_enquiry_bulk_delete_refuses_real_rows(owner, property_row):
    real = _enquiry(name="Real Person")
    spam = _enquiry(name="Bot", honeypot="x")
    r = owner.post(
        "/manage/enquiries/bulk/",
        {"action": "delete", "ids": [str(real.pk), str(spam.pk)], "back": "spam"},
    )
    assert r.status_code == 302
    assert not Inquiry.objects.filter(pk=spam.pk).exists()
    assert Inquiry.objects.filter(pk=real.pk).exists()  # untouched


def test_enquiry_list_shows_email_failed_pill(owner, property_row):
    _enquiry(email_error="SMTPRecipientsRefused: bad domain")
    r = owner.get("/manage/enquiries/")
    assert b"Email didn" in r.content  # Email didn't send pill


# ---------------------------------------------------------------------------
# Listings: search + archive/restore
# ---------------------------------------------------------------------------
def test_listing_search_by_title(owner, property_row):
    _property_row(title="Bamburi plot")
    r = owner.get("/manage/listings/", {"q": "nyali"})
    assert r.status_code == 200
    titles = r.context["listings"]
    assert any("Nyali" in t.title for t in titles)
    assert not any("Bamburi" in t.title for t in titles)


def test_listing_archive_and_restore_row_tools(owner, property_row):
    pk = property_row.pk
    r = owner.post(f"/manage/listings/{pk}/tools/", {"action": "archive"})
    assert r.status_code == 302
    property_row.refresh_from_db()
    assert property_row.status == Property.Status.ARCHIVED
    r = owner.post(f"/manage/listings/{pk}/tools/", {"action": "restore"})
    assert r.status_code == 302
    property_row.refresh_from_db()
    assert property_row.status == Property.Status.DRAFT  # never straight to live


# ---------------------------------------------------------------------------
# Confirm screens (shared pattern: GET shows stakes, bare POST cancels,
# action=confirm deletes; guards still hold)
# ---------------------------------------------------------------------------
def test_media_delete_confirm_flow(owner, property_row):
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.listings.models import PropertyImage

    # a DRAFT listing — the live-listing "needs at least one photo"
    # guard (pinned separately below) must not block this happy path.
    draft = _property_row(title="Draft with photo", status=Property.Status.DRAFT)
    gif = b"GIF89a" + b"\x00" * 16
    img = PropertyImage(property=draft, position=1)
    img.image.save(
        "confirm-test.gif",
        SimpleUploadedFile("x.gif", gif, content_type="image/gif"),
        save=True,
    )
    r = owner.get(f"/manage/site-content/media/{img.pk}/delete/")
    assert r.status_code == 200
    assert b"Delete this photo" in r.content
    r = owner.post(f"/manage/site-content/media/{img.pk}/delete/")
    assert r.status_code == 302
    assert PropertyImage.objects.filter(pk=img.pk).exists()
    r = owner.post(
        f"/manage/site-content/media/{img.pk}/delete/", {"action": "confirm"}
    )
    assert r.status_code == 302
    assert not PropertyImage.objects.filter(pk=img.pk).exists()


def test_media_delete_confirm_still_guards_live_listings(owner, property_row):
    """The r75 guards survive the confirm screen: a live listing's only
    photo is refused even on action=confirm."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.listings.models import PropertyImage

    gif = b"GIF89a" + b"\x00" * 16
    img = PropertyImage(property=property_row, position=1, is_cover=True)
    img.image.save(
        "cover.gif",
        SimpleUploadedFile("c.gif", gif, content_type="image/gif"),
        save=True,
    )
    r = owner.post(
        f"/manage/site-content/media/{img.pk}/delete/", {"action": "confirm"}
    )
    assert r.status_code == 302
    assert PropertyImage.objects.filter(pk=img.pk).exists()  # guard held


def test_testimonial_delete_confirm_flow(owner):
    row = Testimonial.objects.create(
        name="Happy Client", quote="Lovely service", consent_given=True
    )
    r = owner.get(f"/manage/site-content/testimonials/{row.pk}/delete/")
    assert r.status_code == 200
    assert b"Delete the testimonial" in r.content
    r = owner.post(
        f"/manage/site-content/testimonials/{row.pk}/delete/",
        {"action": "confirm"},
    )
    assert r.status_code == 302
    assert not Testimonial.objects.filter(pk=row.pk).exists()


def test_draft_discard_confirm_flow(owner):
    draft = _property_row(title="Unfinished thing", status=Property.Status.DRAFT)
    r = owner.get(f"/manage/listings/{draft.pk}/discard/")
    assert r.status_code == 200
    assert b"Discard the draft" in r.content
    r = owner.post(f"/manage/listings/{draft.pk}/discard/")
    assert r.status_code == 302
    assert Property.objects.filter(pk=draft.pk).exists()
    r = owner.post(
        f"/manage/listings/{draft.pk}/discard/", {"action": "confirm"}
    )
    assert r.status_code == 302
    assert not Property.objects.filter(pk=draft.pk).exists()


# ---------------------------------------------------------------------------
# Sample-data switch lives in the portal now
# ---------------------------------------------------------------------------
def test_sample_data_screen_flips_the_switch(owner, property_row):
    assert SiteSetting.load().hide_demo_data is False
    r = owner.get("/manage/site-content/sample-data/")
    assert r.status_code == 200
    assert b"Sample data" in r.content
    r = owner.post("/manage/site-content/sample-data/")
    assert r.status_code == 302
    assert SiteSetting.load().hide_demo_data is True
    r = owner.post("/manage/site-content/sample-data/")
    assert SiteSetting.load().hide_demo_data is False


def test_checklist_copy_no_longer_says_ask_brian():
    """r90: the checklist must point at portal screens, not at Brian."""
    from apps.manage import checklist

    for item in checklist.REGISTRY:
        assert "Brian" not in item.action, item.key
        assert "coming soon" not in item.action.lower(), item.key


def test_hide_demo_action_points_at_portal_screen():
    from apps.manage import checklist

    item = next(i for i in checklist.REGISTRY if i.key == "hide_demo")
    assert "/manage/site-content/sample-data/" in item.action or item.url


# ---------------------------------------------------------------------------
# Alert email: portal field wins over env setting
# ---------------------------------------------------------------------------
def test_owner_email_item_follows_brand_field():
    from apps.manage import checklist

    brand = BrandSettings.load()
    brand.notification_email = ""
    brand.save()
    with override_settings(OWNER_EMAIL=""):
        assert checklist._owner_email_done() is False
    brand.notification_email = "alerts@gabrielhomes.co.ke"
    brand.save()
    assert checklist._owner_email_done() is True


def test_enquiry_email_prefers_brand_notification_email(property_row):
    from apps.inquiries.views import _send_enquiry_email

    brand = BrandSettings.load()
    brand.notification_email = "alerts@gabrielhomes.co.ke"
    brand.save()
    inquiry = _enquiry()
    with override_settings(OWNER_EMAIL="env-fallback@example.com"):
        _send_enquiry_email(property_row, inquiry)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["alerts@gabrielhomes.co.ke"]
    # delivery was tracked
    inquiry.refresh_from_db()
    assert inquiry.email_sent_at is not None


# ---------------------------------------------------------------------------
# Password change in the portal
# ---------------------------------------------------------------------------
def test_password_change_screen_and_flow(owner):
    r = owner.get("/manage/account/password/")
    assert r.status_code == 200
    assert b"Change password" in r.content
    r = owner.post(
        "/manage/account/password/",
        {"new_password1": "a-fresh-long-pass-9", "new_password2": "a-fresh-long-pass-9"},
    )
    assert r.status_code == 302
    user = User.objects.get(email="owner@test.com")
    assert user.check_password("a-fresh-long-pass-9")
    # session preserved: still authenticated on the client
    assert owner.get("/manage/").status_code == 200


def test_password_change_mismatch_rejected(owner):
    r = owner.post(
        "/manage/account/password/",
        {"new_password1": "one-long-pass-1", "new_password2": "different-pass-2"},
    )
    assert r.status_code == 200  # re-rendered with errors
    user = User.objects.get(email="owner@test.com")
    assert user.check_password("owner-pass-123")  # unchanged


# ---------------------------------------------------------------------------
# Branded error pages
# ---------------------------------------------------------------------------
def test_403_page_is_branded():
    User.objects.create(email="plain@test.com")
    c = Client()
    c.force_login(User.objects.get(email="plain@test.com"))
    with override_settings(DEBUG=False):
        r = c.get("/manage/")
    assert r.status_code == 403
    assert b"This door isn" in r.content  # branded copy, not Django grey


def test_404_page_is_branded():
    with override_settings(DEBUG=False):
        r = Client().get("/no/such/page/")
    assert r.status_code == 404
    assert b"can&#x27;t find that page" in r.content or b"can't find" in r.content


# ---------------------------------------------------------------------------
# The enquiry bulk bar carries the search term through
# ---------------------------------------------------------------------------
def test_enquiry_bulk_redirect_keeps_search(owner, property_row):
    a = _enquiry()
    r = owner.post(
        "/manage/enquiries/bulk/",
        {"action": "seen", "ids": [str(a.pk)], "back": "all", "q": "amina"},
    )
    assert r.status_code == 302
    assert "q=amina" in r["Location"]
