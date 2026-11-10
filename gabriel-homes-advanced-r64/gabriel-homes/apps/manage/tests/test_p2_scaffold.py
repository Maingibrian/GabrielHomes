"""P2-1 — /manage/ portal scaffold: owner-only gate + portal chrome.

The portal is the owner's private workspace:
  * anonymous visitors   -> redirected to login (with ?next= back)
  * authenticated non-owners (agents, plain users) -> 403, never a loop
  * the owner (superuser) -> a designed cream/espresso screen in the
    site's own design language, NOT the Django admin skin

Contract pinned here so every later portal module inherits the gate.
"""
import pytest
from django.test import Client

from apps.accounts.models import User

pytestmark = pytest.mark.django_db

LOGIN_URL = "/account/login/"


def _owner():
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


def _agent():
    User.objects.create(email="agent@test.com", full_name="A Agent", is_agent=True)
    c = Client()
    c.force_login(User.objects.get(email="agent@test.com"))
    return c


def _plain_user():
    User.objects.create(email="plain@test.com", full_name="P User")
    c = Client()
    c.force_login(User.objects.get(email="plain@test.com"))
    return c


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
def test_anonymous_redirected_to_login():
    r = Client().get("/manage/")
    assert r.status_code == 302
    assert r["Location"].startswith(LOGIN_URL)
    assert "next=/manage/" in r["Location"]


def test_agent_gets_403_not_redirect_loop():
    r = _agent().get("/manage/")
    assert r.status_code == 403


def test_plain_user_gets_403():
    r = _plain_user().get("/manage/")
    assert r.status_code == 403


def test_owner_gets_200():
    r = _owner().get("/manage/")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# The scaffold screen — portal chrome, not the admin skin
# ---------------------------------------------------------------------------
def test_owner_home_shows_portal_chrome():
    html = _owner().get("/manage/").content.decode()
    assert "Owner portal" in html
    assert "Gabriel Homes" in html
    assert "Sign out" in html  # POST form, matches allauth's own pattern
    assert "View your live site" in html  # the single primary action


def test_portal_does_not_use_admin_skin():
    html = _owner().get("/manage/").content.decode()
    # Django admin marks — must never appear in the portal
    assert "site_header" not in html
    assert "django-admin" not in html
    # Portal loads its own stylesheet, not the admin's
    assert "css/manage.css" in html
    assert "admin/css/base.css" not in html


def test_portal_pages_are_noindex():
    html = _owner().get("/manage/").content.decode()
    assert "noindex" in html


def test_logout_form_has_csrf_and_posts_to_allauth():
    html = _owner().get("/manage/").content.decode()
    assert 'action="/account/logout/"' in html
    assert "csrfmiddlewaretoken" in html
