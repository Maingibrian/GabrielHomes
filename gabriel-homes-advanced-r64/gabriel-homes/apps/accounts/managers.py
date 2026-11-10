"""Custom managers for the accounts.User model.

Implements email-as-username: there is no `username` field on the User
model, so we need `UserManager` and a `BaseUserManager` that work in
terms of `email` instead of `username`.
"""
from __future__ import annotations

from django.contrib.auth.base_user import BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager for the custom User model — uses `email` as the identifier."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        # Store the address in one canonical form. MariaDB compares strings
        # case-insensitively and SQLite does not; lower-casing here keeps the
        # two databases behaving the same.
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        # Login matches the email regardless of case, on every database.
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class AgencyProfileManager(models.Manager):
    """Convenience manager for agency lookups — populated in Phase 1."""
