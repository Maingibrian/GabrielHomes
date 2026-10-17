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
