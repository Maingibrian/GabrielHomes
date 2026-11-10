"""Pytest fixtures for Gabriel Homes."""
import pytest
from django.conf import settings


@pytest.fixture
def user_factory(db):
    """Lazy factory for creating test users."""
    from apps.accounts.models import User

    def _create(email="user@example.com", password="pa55w0rd!", **extra):
        return User.objects.create_user(email=email, password=password, **extra)

    return _create


@pytest.fixture
def settings_dev(monkeypatch):
    """Pin dev settings for tests that depend on DEBUG-only behaviour."""
    monkeypatch.setattr(settings, "DEBUG", True)
