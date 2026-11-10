"""Inquiries models — Inquiry.

WORK.md §6 spec:
    Inquiry: property FK, name, email, phone, message, status
    (new | read | replied), created_at, user FK (nullable).
    Spam control: honeypot field + per-IP rate limit.

The honeypot field and per-IP rate limiting are wired up in Phase 4
when the enquiry form view is built; the model just holds the columns.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models


class Inquiry(models.Model):
    """An enquiry from a site visitor about a Property."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        READ = "read", "Read"
        REPLIED = "replied", "Replied"

    property_ref = models.ForeignKey(
        "listings.Property",
        on_delete=models.CASCADE,
        related_name="inquiries",
        verbose_name="property",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )

    name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    # S12 input limit: 5 000 chars ≈ 800 words — any real enquiry fits,
    # mail-bomb payloads don't. Enforced via the ModelForm automatically.
    message = models.TextField(max_length=5000)

    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.NEW, db_index=True
    )

    # Spam-control: honeypot value (any non-empty value flags the row as spam),
    # and the submitter's IP for per-IP rate limiting (Phase 4).
    honeypot = models.CharField(
        max_length=200, blank=True, default="",
        help_text="Honeypot: must stay empty. Any value flags the row as spam.",
    )
    submitter_ip = models.GenericIPAddressField(null=True, blank=True)

    # Delivery tracking for the agent notification email (S9). Both stay
    # null/blank when the agent has no email address on file.
    email_sent_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When the agent notification email was handed to the mail backend.",
    )
    email_error = models.CharField(
        max_length=300, blank=True, default="",
        help_text="Last notification-email failure, truncated to 300 chars. Empty = no failure.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "inquiry"
        verbose_name_plural = "inquiries"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["submitter_ip", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Inquiry from {self.name} on {self.property_ref_id}"

    @property
    def is_spam(self) -> bool:
        return bool(self.honeypot)
