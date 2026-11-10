"""P2-2 — /manage/ home: counts + Setup Checklist.

Contract:
  * Numbers on the home screen come from the database — new enquiries
    (spam excluded), live listings (the public published() chokepoint),
    drafts.
  * Checklist items the site can verify are DERIVED (contact details,
    demo hiding, first real listing, enquiry email target) — the owner
    cannot tick them by hand and the checklist cannot lie.
  * Manual items (about story, founder name) are owner-ticked via POST;
    non-owners are blocked; derived keys refuse to toggle.
  * The FIRST open item in registry order is the exact next step.
"""
import pytest
from django.test import Client, override_settings
from django.utils import timezone

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.core.models import BrandSettings, SiteSetting
from apps.inquiries.models import Inquiry
from apps.listings.models import Property, PropertyType
from apps.locations.models import Location
from apps.manage import checklist
from apps.manage.models import ChecklistItemState

pytestmark = pytest.mark.django_db


def _owner():
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


def _agency():
    """Legacy storage requirement: Property.agent is NOT NULL (P1 kept the
    schema non-destructive; the agency concept is invisible on the public
    site). Tests must satisfy the column without reviving the concept."""
    user = User.objects.create_user(
        email=f"agency{_agency.n}@test.com", password="agency-pass-123"
    )
    _agency.n += 1
    return AgencyProfile.objects.create(user=user, name="Gabriel Homes")


_agency.n = 0


def _property(i=0, status="published", is_demo=False, **over):
    loc, _ = Location.objects.get_or_create(name="Testville")
    pt, _ = PropertyType.objects.get_or_create(
        slug_plural="houses",
        defaults={"name": "House", "slug_single": "house"},
    )
    kw = dict(
        title=f"Test home {i}",
        description="A test listing.",
        listing_type="sale",
        property_type=pt,
        location=loc,
        price=5_000_000,
        status=status,
        is_demo=is_demo,
        agent=_agency(),
    )
    if status == "published":
        kw["published_at"] = timezone.now()
    kw.update(over)
    return Property.objects.create(**kw)


def _inquiry(i=0, status="new", spam=False, prop=None):
    # default holding property is a DRAFT so enquiry helpers don't
    # silently add to the published-listings counts under test
    prop = prop or _property(i=i, status="draft")
    return Inquiry.objects.create(
        property_ref=prop,
        name=f"Enquirer {i}",
        email=f"enquirer{i}@example.com",
        message="Is this available?",
        status=status,
        honeypot="spam-bot" if spam else "",
    )


# ---------------------------------------------------------------------------
# Counts — database facts, spam never counted
# ---------------------------------------------------------------------------
def test_counts_are_database_facts():
    _property(1, status="published")
    _property(2, status="published", is_demo=True)  # demo: live only if switch off
    _property(3, status="draft")
    _inquiry(10)                                    # new
    _inquiry(11, status="replied")                  # not new
    _inquiry(12, spam=True)                         # spam: excluded from new
    c = _owner()
    r = c.get("/manage/")
    counts = r.context["counts"]
    assert counts["new_enquiries"] == 1
    assert counts["drafts"] == 4  # 1 explicit + 3 inquiry holding rows
    # live = public chokepoint: demo row visible while the switch is off
    assert counts["live_listings"] == 2


def test_live_listings_follows_demo_switch():
    _property(1, status="published")
    _property(2, status="published", is_demo=True)
    s = SiteSetting.load()  # mutate ONE instance, then save it
    s.hide_demo_data = True
    s.save()
    r = _owner().get("/manage/")
    assert r.context["counts"]["live_listings"] == 1


# ---------------------------------------------------------------------------
# Checklist — derived items computed, never tickable
# ---------------------------------------------------------------------------
def test_registry_order_is_pinned():
    """The next-step priority must not silently reorder."""
    assert checklist.REGISTRY_KEYS == (
        "contact", "hide_demo", "real_listings", "owner_email",
        "about_story", "founder_name",
    )


def test_fresh_site_state_and_next_step():
    """Empty site: only hide_demo is auto-done (nothing to hide)."""
    r = _owner().get("/manage/")
    cl = r.context["checklist"]
    assert cl["done_count"] == 1 and cl["total"] == 6
    assert cl["percent"] == 17
    assert cl["next"]["spec"].key == "contact"
    html = r.content.decode()
    assert "1 of 6 done" in html
    assert "Send Brian the phone" in html  # exact next step shown in banner


def test_contact_item_flips_with_brand_settings():
    brand = BrandSettings.load()
    brand.phone = "+254 700 000 000"
    brand.save()
    r = _owner().get("/manage/")
    cl = r.context["checklist"]
    done_keys = {i["spec"].key for i in cl["items"] if i["done"]}
    assert "contact" in done_keys
    assert cl["next"]["spec"].key == "real_listings"


def test_hide_demo_follows_switch_and_zero_demo():
    # demo rows exist, switch off -> open
    _property(1, is_demo=True)
    cl = checklist.build_checklist()
    assert dict((i["spec"].key, i["done"]) for i in cl["items"])["hide_demo"] is False
    # switch on -> done
    s = SiteSetting.load()
    s.hide_demo_data = True
    s.save()
    assert checklist._hide_demo_done() is True
    # switch off again but no demo rows at all -> done (nothing to hide)
    s.hide_demo_data = False
    s.save()
    Property.objects.filter(is_demo=True).delete()
    assert checklist._hide_demo_done() is True


def test_real_listings_ignores_demo_rows():
    _property(1, status="published", is_demo=True)
    assert checklist._real_listings_done() is False  # demo doesn't count
    _property(2, status="published", is_demo=False)
    assert checklist._real_listings_done() is True
    # a draft real listing is not published yet
    _property(3, status="draft", is_demo=False)
    cl = checklist.build_checklist()
    assert dict((i["spec"].key, i["done"]) for i in cl["items"])["real_listings"] is True


@override_settings(OWNER_EMAIL="owner-inbox@example.com")
def test_owner_email_item_follows_setting():
    assert checklist._owner_email_done() is True


def test_owner_email_item_open_when_unset():
    assert checklist._owner_email_done() is False


# ---------------------------------------------------------------------------
# Manual items — owner ticks, others blocked, derived keys refuse
# ---------------------------------------------------------------------------
def test_manual_toggle_marks_done_then_reopens():
    c = _owner()
    url = "/manage/checklist/about_story/toggle/"
    r = c.post(url)
    assert r.status_code == 302 and r["Location"] == "/manage/"
    state = ChecklistItemState.objects.get(key="about_story")
    assert state.done is True and state.done_at is not None
    # home reflects it
    cl = c.get("/manage/").context["checklist"]
    item = next(i for i in cl["items"] if i["spec"].key == "about_story")
    assert item["done"] is True
    assert cl["done_count"] == 2  # fresh site's auto-done hide_demo + this one
    # reopen
    c.post(url)
    state.refresh_from_db()
    assert state.done is False and state.done_at is None


def test_toggle_shows_plain_language_message():
    c = _owner()
    r = c.post("/manage/checklist/about_story/toggle/", follow=True)
    html = r.content.decode()
    assert "Done: Read your About page" in html


def test_toggle_rejects_derived_and_unknown_keys():
    c = _owner()
    assert c.post("/manage/checklist/contact/toggle/").status_code == 404
    assert c.post("/manage/checklist/nonsense/toggle/").status_code == 404
    assert ChecklistItemState.objects.count() == 0


def test_toggle_blocked_for_anonymous_and_non_owners():
    # anonymous -> login redirect
    r = Client().post("/manage/checklist/about_story/toggle/")
    assert r.status_code == 302 and r["Location"].startswith("/account/login")
    # authenticated non-owner -> 403
    User.objects.create(email="agent@test.com", full_name="A Agent", is_agent=True)
    c = Client()
    c.force_login(User.objects.get(email="agent@test.com"))
    assert c.post("/manage/checklist/about_story/toggle/").status_code == 403
    # nothing was written
    assert ChecklistItemState.objects.count() == 0


# ---------------------------------------------------------------------------
# All done
# ---------------------------------------------------------------------------
def test_all_done_banner():
    brand = BrandSettings.load()
    brand.phone = "+254 700 000 000"
    brand.save()
    s = SiteSetting.load()
    s.hide_demo_data = True
    s.save()
    _property(1, status="published", is_demo=False)
    ChecklistItemState.objects.create(key="about_story", done=True,
                                      done_at=timezone.now())
    ChecklistItemState.objects.create(key="founder_name", done=True,
                                      done_at=timezone.now())
    with override_settings(OWNER_EMAIL="owner@example.com"):
        r = _owner().get("/manage/")
    cl = r.context["checklist"]
    assert cl["all_done"] is True and cl["percent"] == 100
    html = r.content.decode()
    assert "You're all set." in html
    assert 'aria-valuenow="100"' in html
