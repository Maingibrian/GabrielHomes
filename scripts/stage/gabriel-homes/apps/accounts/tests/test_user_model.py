"""Tests for the accounts.User custom user model.

These run as part of Phase 0's quality gate. Phase 1 will add tests
for AgencyProfile, SavedProperty, etc.
"""
import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_create_user_normalises_email_and_hashes_password():
    user = User.objects.create_user(
        email="Test.User@Example.COM",
        password="pa55w0rd!",
        full_name="Test User",
    )
    assert user.email == "Test.User@example.com"  # normalised
    assert user.check_password("pa55w0rd!")
    assert user.password != "pa55w0rd!"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_agent is False


def test_create_user_requires_email():
    with pytest.raises(ValueError, match="email"):
        User.objects.create_user(email="", password="x")


def test_create_superuser_sets_staff_and_superuser():
    su = User.objects.create_superuser(
        email="admin@example.com", password="s3cr3t-pass", full_name="Admin",
    )
    assert su.is_staff is True
    assert su.is_superuser is True


def test_create_superuser_rejects_inconsistent_flags():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="bad@example.com", password="x", is_staff=False
        )
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="bad@example.com", password="x", is_superuser=False
        )


def test_get_full_name_falls_back_to_email():
    user = User.objects.create_user(email="nobody@example.com", password="x")
    assert user.get_full_name() == "nobody@example.com"
    user.full_name = "Gabriel Omullu"
    assert user.get_full_name() == "Gabriel Omullu"
    assert user.get_short_name() == "Gabriel"


def test_username_field_is_email():
    assert User.USERNAME_FIELD == "email"
    assert User.REQUIRED_FIELDS == []
