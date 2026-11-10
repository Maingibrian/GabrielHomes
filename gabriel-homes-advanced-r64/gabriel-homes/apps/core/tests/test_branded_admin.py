"""r11 — branded admin ("Studio"): the owner never sees the Django skin.

The admin runs on its own AdminSite mounted at /admin/ with Gabriel
Homes branding (templates/admin/base_site.html + admin-studio.css), and
carries the demo/real bulk actions.
"""
import pytest
from django.core.management import call_command
from django.test import Client

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.listings.models import Property

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=20, verbosity=0, i_know_this_is_demo=True)
    yield


def _owner_client():
    user = User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(user)
    return user, c


# ---------------------------------------------------------------------------
# Skin
# ---------------------------------------------------------------------------
def test_admin_login_page_is_branded():
    c = Client()
    r = c.get("/admin/login/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "Gabriel Homes" in body
    assert "Django administration" not in body


def test_admin_index_is_branded_for_owner():
    _, c = _owner_client()
    r = c.get("/admin/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "Gabriel Homes" in body
    assert "Django administration" not in body


def test_admin_login_page_still_loads_regression():
    """Phase-0 pin: /admin/login/ must return 200 (now via the branded site)."""
    c = Client()
    assert c.get("/admin/login/").status_code == 200


def test_non_staff_redirected_from_admin_index():
    user = User.objects.create_user(email="civilian@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    r = c.get("/admin/")
    assert r.status_code == 302


# ---------------------------------------------------------------------------
# Demo / real bulk actions
# ---------------------------------------------------------------------------
def _changelist_action(client, model_admin_path, action, pks):
    from django.contrib.admin.sites import site as _  # noqa: F401 (docs only)
    data = {
        "action": action,
        "_selected_action": [str(pk) for pk in pks],
    }
    return client.post(model_admin_path, data, follow=True)


def test_property_bulk_actions_mark_demo_and_real():
    _, c = _owner_client()
    real_pks = list(Property.objects.filter(is_demo=False).values_list("pk", flat=True))
    # Start from a known-real listing: make one via ORM.
    p = Property.objects.first()
    Property.objects.filter(pk=p.pk).update(is_demo=False)
    p.refresh_from_db()
    assert p.is_demo is False

    r = _changelist_action(c, "/admin/listings/property/", "mark_demo", [p.pk])
    assert r.status_code == 200
    p.refresh_from_db()
    assert p.is_demo is True

    r = _changelist_action(c, "/admin/listings/property/", "mark_real", [p.pk])
    p.refresh_from_db()
    assert p.is_demo is False


def test_agency_bulk_actions_mark_demo_and_real():
    _, c = _owner_client()
    a = AgencyProfile.objects.first()
    AgencyProfile.objects.filter(pk=a.pk).update(is_demo=False)
    a.refresh_from_db()

    r = _changelist_action(c, "/admin/agents/agencyprofile/", "mark_demo", [a.pk])
    assert r.status_code == 200
    a.refresh_from_db()
    assert a.is_demo is True

    r = _changelist_action(c, "/admin/agents/agencyprofile/", "mark_real", [a.pk])
    a.refresh_from_db()
    assert a.is_demo is False


# ---------------------------------------------------------------------------
# bootstrap_owner command
# ---------------------------------------------------------------------------
def test_bootstrap_owner_creates_superuser():
    from django.core.management import call_command
    from io import StringIO
    out = StringIO()
    call_command("bootstrap_owner", password="temp-pass-99", stdout=out)
    user = User.objects.get(email="admin@gabrielhomes.co.ke")
    assert user.is_superuser and user.is_staff
    assert user.check_password("temp-pass-99")
    assert "TEMP PASSWORD" in out.getvalue()


def test_bootstrap_owner_never_resets_existing():
    from django.core.management import call_command
    User.objects.create_superuser(
        email="admin@gabrielhomes.co.ke", password="original-pass-1"
    )
    out = __import__("io").StringIO()
    call_command("bootstrap_owner", password="attacker-pass-9", stdout=out)
    user = User.objects.get(email="admin@gabrielhomes.co.ke")
    assert user.check_password("original-pass-1")
    assert not user.check_password("attacker-pass-9")
    assert "already exists" in out.getvalue()
