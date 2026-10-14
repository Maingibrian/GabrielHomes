"""Tests for the closed public sign-up (agents + superusers only).

Product decision (2026-10-14): normal visitors do NOT get accounts.
The adapter returns is_open_for_signup=False, allauth renders the
signup_closed page, and the site exposes only a quiet "Agent sign in"
link (footer Company column + mobile menu) — the desktop header keeps
its clean contact block with no account buttons at all (Plan A).
"""
from django.test import Client

import pytest

pytestmark = pytest.mark.django_db


def test_signup_page_is_closed():
    """GET /account/signup/ renders the friendly closed page, no form."""
    r = Client().get("/account/signup/")
    assert r.status_code == 200
    assert "Registration is closed" in r.content.decode()
    # The actual signup form must NOT be rendered.
    assert 'name="password1"' not in r.content.decode()


def test_signup_post_creates_no_user():
    """POSTing valid signup data must not mint an account."""
    from apps.accounts.models import User

    before = User.objects.count()
    r = Client().post(
        "/account/signup/",
        {"email": "wannabe@example.com", "password1": "pw-123456789", "password2": "pw-123456789"},
    )
    assert r.status_code == 200
    assert User.objects.count() == before
    assert not User.objects.filter(email="wannabe@example.com").exists()


def test_login_page_is_agent_focused_and_has_no_signup_link():
    """The login page says 'Agent sign in' and never links to signup."""
    r = Client().get("/account/login/")
    html = r.content.decode()
    assert r.status_code == 200
    assert "Agent sign in" in html
    assert "/account/signup" not in html


def test_homepage_header_has_no_account_links_for_anonymous():
    """Plan A: clean header — no 'Sign in' button, no header agent link."""
    r = Client().get("/")
    html = r.content.decode()
    assert r.status_code == 200
    # Old public navbar link is gone entirely.
    assert ">Sign in</a>" not in html
    # The desktop contact block is back to exactly two links.
    contact = html.split('site-header__contact">')[1].split("</div>")[0]
    assert contact.count("<a ") == 2
    assert "Agent sign in" not in contact


def test_homepage_footer_and_mobile_offer_agent_sign_in():
    """Agents reach the login page via footer link + mobile menu."""
    r = Client().get("/")
    html = r.content.decode()
    assert html.count("Agent sign in") >= 2  # footer + mobile menu
    assert 'href="/account/login/"' in html
