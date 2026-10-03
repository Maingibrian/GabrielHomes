"""Tests for Phase 5 — save/unsave toggle + saved list page."""
import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=20, verbosity=0)
    yield


def _get_first_listing():
    from apps.listings.models import Property
    return Property.objects.published().first()


# ---------------------------------------------------------------------------
# Save/unsave toggle
# ---------------------------------------------------------------------------
def test_save_requires_login():
    c = Client()
    p = _get_first_listing()
    r = c.post(f"/account/save/{p.pk}/")
    assert r.status_code == 302  # redirect to login
    assert "/account/login" in r.url or "login" in r.url


def test_save_creates_savedproperty():
    from apps.accounts.models import User, SavedProperty
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    p = _get_first_listing()
    assert SavedProperty.objects.filter(user=user, property=p).count() == 0
    c.post(f"/account/save/{p.pk}/")
    assert SavedProperty.objects.filter(user=user, property=p).count() == 1


def test_unsave_removes_savedproperty():
    from apps.accounts.models import User, SavedProperty
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    p = _get_first_listing()
    # Save then unsave
    c.post(f"/account/save/{p.pk}/")
    c.post(f"/account/save/{p.pk}/")
    assert SavedProperty.objects.filter(user=user, property=p).count() == 0


def test_toggle_is_idempotent():
    """Saving twice doesn't create duplicates (unique_together)."""
    from apps.accounts.models import User, SavedProperty
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    p = _get_first_listing()
    c.post(f"/account/save/{p.pk}/")
    c.post(f"/account/save/{p.pk}/")  # toggle -> unsave
    c.post(f"/account/save/{p.pk}/")  # toggle -> save again
    assert SavedProperty.objects.filter(user=user, property=p).count() == 1


def test_htmx_save_returns_partial():
    """HTMX request returns the save button partial, not a redirect."""
    from apps.accounts.models import User
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    p = _get_first_listing()
    r = c.post(f"/account/save/{p.pk}/", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    body = r.content.decode()
    assert "save-btn" in body
    assert "is-saved" in body  # saved state reflected
    assert "hx-post" in body   # HTMX attrs present for next toggle


def test_htmx_unsave_returns_partial():
    from apps.accounts.models import User
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    p = _get_first_listing()
    c.post(f"/account/save/{p.pk}/")  # save first
    r = c.post(f"/account/save/{p.pk}/", HTTP_HX_REQUEST="true")  # unsave
    assert r.status_code == 200
    body = r.content.decode()
    assert "save-btn" in body
    assert "is-saved" not in body  # unsaved state reflected


def test_save_nonexistent_property_404():
    from apps.accounts.models import User
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    r = c.post("/account/save/99999/")
    assert r.status_code == 404


def test_save_draft_property_404():
    """Can only save published listings."""
    from apps.accounts.models import User
    from apps.listings.models import Property
    p = _get_first_listing()
    Property.objects.filter(pk=p.pk).update(status="draft")
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    r = c.post(f"/account/save/{p.pk}/")
    assert r.status_code == 404
    Property.objects.filter(pk=p.pk).update(status="published")


def test_save_get_not_allowed():
    from apps.accounts.models import User
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    p = _get_first_listing()
    r = c.get(f"/account/save/{p.pk}/")
    assert r.status_code in (405, 404)


# ---------------------------------------------------------------------------
# Saved list page
# ---------------------------------------------------------------------------
def test_saved_list_requires_login():
    c = Client()
    r = c.get("/account/saved/")
    assert r.status_code == 302
    assert "login" in r.url


def test_saved_list_empty():
    from apps.accounts.models import User
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    r = c.get("/account/saved/")
    assert r.status_code == 200
    assert "No saved properties" in r.content.decode()


def test_saved_list_shows_saved_properties():
    from apps.accounts.models import User, SavedProperty
    user = User.objects.create_user(email="saver@test.com", password="pass123!")
    c = Client()
    c.force_login(user)
    p = _get_first_listing()
    SavedProperty.objects.create(user=user, property=p)
    r = c.get("/account/saved/")
    assert r.status_code == 200
    body = r.content.decode()
    assert p.title in body
    assert "listing-card" in body


def test_saved_list_only_shows_own_saves():
    """User A's saves should not appear in User B's saved list."""
    from apps.accounts.models import User, SavedProperty
    user_a = User.objects.create_user(email="a@test.com", password="pass123!")
    user_b = User.objects.create_user(email="b@test.com", password="pass123!")
    p = _get_first_listing()
    SavedProperty.objects.create(user=user_a, property=p)
    c = Client()
    c.force_login(user_b)
    r = c.get("/account/saved/")
    body = r.content.decode()
    assert p.title not in body
    assert "No saved properties" in body
