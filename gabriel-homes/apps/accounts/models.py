"""Accounts models — custom User (email-as-username) for Gabriel Homes.

WORK.md section 5 mandates a custom User model from day one, with email
as the username. AgencyProfile and SavedProperty are mentioned in
section 6; AgencyProfile lives in apps.agents (per WORK.md §5 layout),
while SavedProperty and SavedSearch belong here because they are
user-owned bookmarks rather than listing-owned data.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Email-based user. Used for both public users and agents.

    `is_agent` flags users who can publish listings through the dashboard
    (Phase 5). It is a plain boolean rather than a separate group so that
    a single user can flip from "saved a property" to "manages listings"
    without schema changes.
    """

    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(_("full name"), max_length=180, blank=True)
    phone = models.CharField(_("phone"), max_length=32, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_agent = models.BooleanField(
        default=False,
        help_text=_("Can publish and manage listings through the dashboard."),
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("-date_joined",)

    def __str__(self) -> str:
        return self.email or "(no email)"

    def get_full_name(self) -> str:
        return self.full_name or self.email

    def get_short_name(self) -> str:
        return self.full_name.split(" ")[0] if self.full_name else self.email


class SavedProperty(models.Model):
    """A user's bookmark on a Property."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_properties"
    )
    property = models.ForeignKey(
        "listings.Property",
        on_delete=models.CASCADE,
        related_name="saved_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "saved property"
        verbose_name_plural = "saved properties"
        unique_together = (("user", "property"),)
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user_id} saved {self.property_id}"


class SavedSearch(models.Model):
    """A user's saved search querystring (alerts are 'Later' per WORK.md §3).

    `querystring` is the raw URL query string (without the leading `?`)
    that the search view understands — e.g. `min_price=5000000&beds=3`.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_searches"
    )
    name = models.CharField(max_length=120)
    querystring = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "saved search"
        verbose_name_plural = "saved searches"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} ({self.user_id})"
