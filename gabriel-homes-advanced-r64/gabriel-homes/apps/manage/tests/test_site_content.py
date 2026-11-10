"""Owner-only site-content editor and public rendering contract."""

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.core.models import BrandSettings

pytestmark = pytest.mark.django_db


def _owner_client():
    owner = User.objects.create_superuser(
        email="content-owner@test.com", password="owner-pass-123"
    )
    client = Client()
    client.force_login(owner)
    return client


def _valid_payload(**overrides):
    brand = BrandSettings.load()
    payload = {
        name: getattr(brand, name)
        for name in (
            "phone", "whatsapp", "email", "hero_tag", "hero_heading_lead",
            "hero_heading_accent", "hero_heading_tail", "hero_subtitle",
            "about_heading", "about_intro", "services_heading",
            "services_intro", "cta_heading", "cta_intro", "footer_lead",
        )
    }
    payload.update(overrides)
    return payload


def test_site_content_requires_owner():
    assert Client().get("/manage/site-content/").status_code == 302

    user = User.objects.create_user(email="visitor@test.com", password="pass-123")
    client = Client()
    client.force_login(user)
    assert client.get("/manage/site-content/").status_code == 403


def test_owner_can_open_editor():
    response = _owner_client().get("/manage/site-content/")
    assert response.status_code == 200
    assert "Edit the public website" in response.content.decode()
    assert 'name="hero_subtitle"' in response.content.decode()
    assert 'name="phone"' in response.content.decode()


def test_saved_content_appears_on_public_homepage():
    response = _owner_client().post(
        "/manage/site-content/",
        _valid_payload(
            phone="+254 700 111 222",
            hero_heading_lead="Find your next home,",
            hero_heading_accent="confidently",
            hero_heading_tail="with Gabriel Homes.",
            footer_lead="Thoughtful homes across Kenya.",
        ),
        follow=True,
    )
    assert response.status_code == 200
    assert "Site content saved" in response.content.decode()

    home = Client().get("/").content.decode()
    assert "Find your next home," in home
    assert ">confidently</em>" in home
    assert "with Gabriel Homes." in home
    assert "Thoughtful homes across Kenya." in home
    assert BrandSettings.load().phone == "+254 700 111 222"


def test_owner_content_is_escaped_on_public_homepage():
    # r50: hero_tag no longer renders on the home page (the hero eyebrow
    # is gone), so the escape tripwire rides hero_heading_lead — a
    # BrandSettings field the home h1 still renders live.
    _owner_client().post(
        "/manage/site-content/",
        _valid_payload(hero_heading_lead='<img src=x onerror="alert(1)">'),
    )
    home = Client().get("/").content.decode()
    assert '<img src=x onerror="alert(1)">' not in home
    assert "&lt;img" in home


def test_invalid_content_is_not_saved():
    response = _owner_client().post(
        "/manage/site-content/",
        _valid_payload(hero_heading_accent="x" * 81),
    )
    assert response.status_code == 200
    assert "Ensure this value has at most 80 characters" in response.content.decode()
    # r43: slogan defaults swapped (core.0011) — invalid POST must leave
    # the current accent, "come home", untouched.
    assert BrandSettings.load().hero_heading_accent == "come home"
