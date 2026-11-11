"""r75 (BACKEND-PLAN 3C) — testimonials: screen + public band.

Pinned here: the owner gate, the consent gate (no permission, no
publication — the public band only ever shows shown+consent rows), the
demo switch respected on the public band, hide/show, edit, delete, and
"hidden when none" (the band's whole section vanishes).
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.core.models import SiteSetting, Testimonial

pytestmark = pytest.mark.django_db

LOGIN_URL = "/account/login/"
URL = "/manage/site-content/testimonials/"


@pytest.fixture(autouse=True)
def base(db):
    User = get_user_model()
    User.objects.create(email="agency-user@test.com", full_name="Test Agency", is_agent=True)


@pytest.fixture
def owner():
    User = get_user_model()
    User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
    c = Client()
    c.force_login(User.objects.get(email="owner@test.com"))
    return c


@pytest.fixture
def agent():
    User = get_user_model()
    c = Client()
    c.force_login(User.objects.get(email="agency-user@test.com"))
    return c


def _add(owner, **overrides):
    payload = {
        "name": "Amina K.", "role": "Bought an apartment in Nyali",
        "quote": "Gabriel found us the flat we had given up on.",
        "rating": "5", "consent_given": "on",
    }
    payload.update(overrides)
    return owner.post(URL, payload)


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
def test_anon_is_sent_to_login():
    r = Client().get(URL)
    assert r.status_code == 302
    assert LOGIN_URL in r["Location"]


def test_agent_gets_403(agent):
    assert agent.get(URL).status_code == 403


# ---------------------------------------------------------------------------
# Add — the consent gate
# ---------------------------------------------------------------------------
def test_add_with_consent_publishes_on_home(owner, client):
    r = _add(owner)
    assert r.status_code == 302
    home = client.get("/")
    assert b"quote-card" in home.content
    assert b"Amina K." in home.content
    assert b"Gabriel found us the flat" in home.content


def test_add_without_consent_stays_off_the_home_page(owner, client):
    r = _add(owner, consent_given="")
    assert r.status_code == 302
    assert Testimonial.objects.filter(name="Amina K.").exists()
    home = client.get("/")
    assert b"quote-card" not in home.content
    assert b"Amina K." not in home.content
    # The screen says so, honestly.
    screen = owner.get(URL)
    assert b"Waiting for permission" in screen.content


def test_home_band_hidden_when_no_testimonials(client):
    home = client.get("/")
    assert b"quote-card" not in home.content
    assert b"What clients say" not in home.content


# ---------------------------------------------------------------------------
# The public display contract
# ---------------------------------------------------------------------------
def test_hide_takes_it_off_the_home_page(owner, client):
    _add(owner)
    row = Testimonial.objects.get(name="Amina K.")
    r = owner.post(f"{URL}{row.pk}/action/", {"action": "toggle"})
    assert r.status_code == 302
    assert b"Amina K." not in client.get("/").content
    # The words stay saved.
    assert Testimonial.objects.filter(pk=row.pk).exists()


def test_demo_testimonials_respect_the_demo_switch(owner, client):
    Testimonial.objects.create(
        name="Sample Person", quote="Sample words.", consent_given=True, shown=True, is_demo=True,
    )
    assert b"Sample Person" in client.get("/").content
    switch, _created = SiteSetting.objects.get_or_create(pk=1)
    switch.hide_demo_data = True
    switch.save()
    assert b"Sample Person" not in client.get("/").content


def test_rating_renders_as_stars(owner, client):
    _add(owner, rating="4")
    home = client.get("/")
    assert b"aria-label=\"Rated 4 out of 5\"" in home.content


def test_rating_out_of_range_is_refused(owner):
    r = _add(owner, rating="9")
    assert r.status_code == 302  # honest error, back to the form
    assert not Testimonial.objects.filter(name="Amina K.").exists()


# ---------------------------------------------------------------------------
# Edit + delete
# ---------------------------------------------------------------------------
def test_edit_updates_the_words(owner, client):
    _add(owner)
    row = Testimonial.objects.get(name="Amina K.")
    r = owner.post(f"{URL}{row.pk}/action/", {
        "action": "edit", "name": "Amina K.", "role": "Bought in Bamburi",
        "quote": "Updated words.", "rating": "5", "consent_given": "on",
    })
    assert r.status_code == 302
    row.refresh_from_db()
    assert row.quote == "Updated words."
    assert b"Updated words." in client.get("/").content


def test_delete_removes_the_row(owner, client):
    _add(owner)
    row = Testimonial.objects.get(name="Amina K.")
    r = owner.post(f"{URL}{row.pk}/action/", {"action": "delete"})
    assert r.status_code == 302
    assert not Testimonial.objects.exists()
    assert b"quote-card" not in client.get("/").content


def test_unknown_action_404s(owner):
    _add(owner)
    row = Testimonial.objects.get(name="Amina K.")
    assert owner.post(f"{URL}{row.pk}/action/", {"action": "nonsense"}).status_code == 404
