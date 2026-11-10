"""Account emails behave the same on SQLite and MariaDB: one canonical form, case-insensitive login."""
import pytest
from django.contrib.auth import authenticate

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_email_is_stored_lowercase():
    u = User.objects.create_user(email="Owner@Example.COM", password="case-pass-123")
    assert u.email == "owner@example.com"


def test_login_works_in_any_case():
    User.objects.create_user(email="owner@example.com", password="case-pass-123")
    assert authenticate(username="OWNER@example.com", password="case-pass-123") is not None


def test_case_variant_duplicate_is_refused():
    from django.db import IntegrityError, transaction
    User.objects.create_user(email="dup@example.com", password="x-pass-123456")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="DUP@example.com", password="x-pass-123456")
