"""Core models — site-wide owner settings.

r11: the owner controls "placeholder data" visibility from the branded
dashboard (never the Django admin). SiteSetting is a single-row (pk=1)
table of those switches; it is created lazily so first boot needs no
extra setup step.
"""
from __future__ import annotations

from django.db import models
from django.db.utils import OperationalError, ProgrammingError


class SiteSetting(models.Model):
    """Singleton row (pk=1) of owner-controlled site-wide switches."""

    hide_demo_data = models.BooleanField(
        default=False,
        help_text=(
            "Public site: hide all content stamped as demo (seeded agencies "
            "and listings). Dashboards and admin still see everything."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "site setting"
        verbose_name_plural = "site settings"

    def __str__(self) -> str:
        return "Site settings"

    def save(self, *args, **kwargs):
        # Singleton: every save writes the same row.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSetting":
        """Return the singleton row, creating it on first access."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def demo_hidden(cls) -> bool:
        """Cheap read used by public querysets.

        Defensive against the one weird window where a queryset is built
        before migrations have created this table (e.g. during a fresh
        `migrate` run) — treat as "not hidden" there.
        """
        try:
            return bool(
                cls.objects.filter(pk=1)
                .values_list("hide_demo_data", flat=True)
                .first()
            )
        except (OperationalError, ProgrammingError):
            return False


class BrandSettings(models.Model):
    """Singleton row (pk=1) of the Gabriel Homes brand contact details.

    Single-owner mode: the listing-detail contact card and mobile bar read
    from here, not from the (retired) agency concept. Code defaults are
    empty — a button that needs a value (Call / WhatsApp / Email) renders
    only when the owner has filled the field in, so the site never shows
    an invented phone number (OWNER_NEEDS A3: honest blank by design).

    P3-8 (Brand & contact editor) will make this row owner-editable in
    the /manage/ portal; the public templates keep reading the same row.
    """

    phone = models.CharField(
        max_length=32, blank=True, help_text="Shown on Call buttons. Empty = button hidden."
    )
    whatsapp = models.CharField(
        max_length=32, blank=True,
        help_text="WhatsApp number for click-to-chat. Empty = button hidden.",
    )
    email = models.EmailField(
        blank=True, help_text="Shown on the Email button. Empty = button hidden."
    )
    hero_tag = models.CharField(
        max_length=120,
        # r13: owner asked for a better slogan — the tag now names the place,
        # the headline carries the promise (see hero_heading_* below).
        default="Gabriel Homes · Mombasa, Kenya",
        help_text="Short label above the homepage headline.",
    )
    hero_heading_lead = models.CharField(
        max_length=120, default="Good homes,"
    )
    hero_heading_accent = models.CharField(
        max_length=80, default="properly"
    )
    hero_heading_tail = models.CharField(
        max_length=160, default="checked."
    )
    hero_subtitle = models.TextField(
        max_length=500,
        default=(
            "Buy, rent or book a short stay anywhere in Mombasa. Gabriel and "
            "the team check every listing before it goes live — and if we "
            "cannot check something, we tell you."
        ),
    )
    about_heading = models.CharField(
        # r12: was "We are new. So we show our working." — keeps the
        # show-your-working sentiment without the new-company framing.
        max_length=180, default="We would rather show our working."
    )
    about_intro = models.TextField(
        max_length=800,
        default=(
            "Gabriel Homes was founded in 2026 and is centred in Kenya. We are "
            "building our listings one checked property at a time."
        ),
    )
    services_heading = models.CharField(
        max_length=180, default="What we do for buyers and renters."
    )
    services_intro = models.TextField(
        max_length=600,
        default=(
            "Two things, done carefully: finding the right home, and making "
            "sure the listing is accurate before you spend time on it."
        ),
    )
    cta_heading = models.CharField(
        max_length=180, default="Tell us what you are looking for."
    )
    cta_intro = models.TextField(
        max_length=500,
        default=(
            "Enquire on a listing, or contact us about a property you want to "
            "list. A person will reply."
        ),
    )
    footer_lead = models.CharField(
        max_length=220,
        # r12: listings-first lead line instead of the founding-date line.
        default=(
            "Homes for sale, rent and short stays across Mombasa, checked "
            "before they are published."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "brand settings"
        verbose_name_plural = "brand settings"

    def __str__(self) -> str:
        return "Brand settings"

    def save(self, *args, **kwargs):
        # Singleton: every save writes the same row.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "BrandSettings":
        """Return the singleton row, creating it on first access.

        Read-first: the context processor calls this on every public
        request, so the steady state is one SELECT — a GET must not write.
        Migration 0004 seeds the row, so the INSERT path is a fallback for
        pre-migration databases only. Defensive against the pre-migration
        window (same rationale as SiteSetting.demo_hidden).
        """
        try:
            try:
                return cls.objects.get(pk=1)
            except cls.DoesNotExist:
                obj, _ = cls.objects.get_or_create(pk=1)
                return obj
        except (OperationalError, ProgrammingError):
            return cls(pk=1)  # transient empty-row stand-in; nothing saved

    @property
    def whatsapp_digits(self) -> str:
        """wa.me-compatible digits-only form of the WhatsApp number."""
        return "".join(ch for ch in self.whatsapp if ch.isdigit())


class NewsletterSubscriber(models.Model):
    """Someone who asked for the Gabriel Homes newsletter.

    Opt-in is double: the person ticks a consent box, then confirms by
    email. Only confirmed, non-unsubscribed people ever receive an issue.
    """

    email = models.EmailField(unique=True)
    consent_at = models.DateTimeField(help_text="When the person ticked the consent box.")
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    @property
    def is_active(self) -> bool:
        return self.confirmed_at is not None and self.unsubscribed_at is None


class NewsletterIssue(models.Model):
    """One newsletter that was sent, and the listings it covered."""

    sent_at = models.DateTimeField(auto_now_add=True)
    listing_count = models.PositiveIntegerField()
    recipient_count = models.PositiveIntegerField()

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Issue {self.pk} · {self.listing_count} listings · {self.sent_at:%Y-%m-%d}"
