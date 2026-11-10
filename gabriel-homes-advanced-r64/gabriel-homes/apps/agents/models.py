"""Agents models — AgencyProfile.

WORK.md §6 spec:
    AgencyProfile: user OneToOne, name, slug, logo, bio, phone, whatsapp,
    email, website, office_location FK, is_verified.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import SiteSetting
from apps.listings.models import validate_image_file


class AgencyProfileQuerySet(models.QuerySet):
    """Queryset for agencies with the r11 demo-visibility helper."""

    def public(self) -> "AgencyProfileQuerySet":
        """Agencies visible on the public site (demo-aware).

        Used by the public directory, agency profile pages and the about
        page. When the owner hides demo data, seeded placeholder agencies
        vanish from the directory and their profile pages 404.
        """
        qs = self
        if SiteSetting.demo_hidden():
            qs = qs.exclude(is_demo=True)
        return qs


class AgencyProfile(models.Model):
    """An agency (the listing owner) — one-to-one with a User.

    Phase 5 will gate the dashboard on `user.is_agent and
    hasattr(user, 'agency_profile')`.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agency_profile",
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    logo = models.ImageField(
        upload_to="agency-logos/", blank=True, validators=[validate_image_file]
    )
    bio = models.TextField(blank=True)

    phone = models.CharField(max_length=32, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    office_location = models.ForeignKey(
        "locations.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agencies_based_here",
    )

    is_verified = models.BooleanField(default=False)
    # r11: stamped True by seed_demo; hidden from the public site while
    # the owner's demo switch is on "hide demo data". Default False so
    # agencies added by hand (dashboard / admin / import) are real.
    is_demo = models.BooleanField(
        default=False,
        db_index=True,
        help_text=(
            "Seeded placeholder agency. Hidden from the public site while "
            "the owner's demo switch is off-position (hide demo data)."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "agency"
        verbose_name_plural = "agencies"
        ordering = ("name",)
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_verified"]),
        ]

    def __str__(self) -> str:
        return self.name

    objects = AgencyProfileQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 2
            # De-duplicate slug across agencies.
            qs = AgencyProfile.objects.filter(slug=slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.exists():
                slug = f"{base}-{i}"
                i += 1
                qs = AgencyProfile.objects.filter(slug=slug)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
            self.slug = slug
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Convenience contact helpers (used by listing detail in Phase 4)
    # ------------------------------------------------------------------
    @property
    def display_phone(self) -> str:
        """Return phone normalised to +254... if it looks local."""
        return self.phone or self.user.phone or ""

    @property
    def display_email(self) -> str:
        return self.email or self.user.email

    @property
    def display_whatsapp(self) -> str:
        """Return a wa.me-compatible digits-only string."""
        raw = self.whatsapp or self.phone or ""
        # Strip everything that isn't a digit
        return "".join(ch for ch in raw if ch.isdigit())
