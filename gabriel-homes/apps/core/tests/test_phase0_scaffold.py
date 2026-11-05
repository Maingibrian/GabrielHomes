"""Smoke tests for the Phase 0 scaffold.

These run as part of Phase 0's quality gate to prove the project
boots and the styled placeholder home renders.
"""
import pytest

pytestmark = pytest.mark.django_db


def test_home_page_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Gabriel Homes" in response.content
    # design-language markers from the placeholder hero (r13 slogan)
    assert b"properly" in response.content


def test_admin_login_page_loads(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200


def test_static_tokens_css_is_collected(client):
    """tokens.css must be findable by Django's staticfiles finder."""
    from django.contrib.staticfiles import finders
    path = finders.find("css/tokens.css")
    assert path is not None
    assert "tokens.css" in path
