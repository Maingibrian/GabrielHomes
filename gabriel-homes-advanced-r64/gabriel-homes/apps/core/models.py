"""Core models — site-wide owner settings.

r11: the owner controls "placeholder data" visibility from the branded
dashboard (never the Django admin). SiteSetting is a single-row (pk=1)
table of those switches; it is created lazily so first boot needs no
extra setup step.

r73 (BACKEND-PLAN 1D/1E): BrandSettings also carries the owner's
brand ASSETS (logo, favicon, socials, address, hours — everything the
public chrome renders) and the SEO & tracking knobs (analytics ID,
Search Console token, default meta description). All blank by default:
empty field = hidden UI (honest blank), never an invented value.
"""
from __future__ import annotations

import os

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.utils import OperationalError, ProgrammingError

# Brand asset uploads (r73): small images only, web-safe formats.
MAX_BRAND_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_BRAND_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def validate_brand_image(image):
    """Brand logo/favicon uploads: type + size (BACKEND-PLAN 1D).

    Deliberately stricter than listing photos (2 MB, no SVG): these
    render on every page load and inside the <head>, so they must be
    tiny and raster. Plain-language errors — the owner sees them.
    """
    if image.size > MAX_BRAND_IMAGE_SIZE:
        raise ValidationError(
            f"That image is {image.size // (1024*1024)} MB — please keep it "
            f"under 2 MB (it shows on every page)."
        )
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in ALLOWED_BRAND_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"'{ext or 'no'}' files aren't supported — use a PNG, JPG or WebP image."
        )


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
    # r90 (backend reassessment): enquiry-alert destination, editable in
    # the portal's Site content screen. The inquiry email prefers this
    # DB value over settings.OWNER_EMAIL so the owner can change where
    # alerts go without a redeploy; empty falls back to the env setting
    # (see apps/inquiries/views._send_enquiry_email and the checklist's
    # owner_email item).
    notification_email = models.EmailField(
        blank=True,
        help_text=(
            "Where enquiry alert emails are sent. Empty = the server's "
            "OWNER_EMAIL setting is used."
        ),
    )
    hero_tag = models.CharField(
        max_length=120,
        # r13: owner asked for a better slogan — the tag now names the place,
        # the headline carries the promise (see hero_heading_* below).
        default="Gabriel Homes · Mombasa, Kenya",
        help_text="Short label above the homepage headline.",
    )
    hero_heading_lead = models.CharField(
        # r43 (owner request): "Good homes, properly checked." read as a
        # clinical framing — the headline now leads with the warm, home-like
        # promise; the checking story stays in hero_subtitle.
        max_length=120, default="A place to"
    )
    hero_heading_accent = models.CharField(
        max_length=80, default="come home"
    )
    hero_heading_tail = models.CharField(
        max_length=160, default="to."
    )
    hero_subtitle = models.TextField(
        max_length=500,
        # r56 (owner round seven): comfort-led rewrite — the subtitle sells
        # the feeling of waking up on the coast; the walked-through story
        # lives on /checks/ and in the footer FAQ, not in the hero.
        default=(
            "Sea-view apartments in Nyali, garden homes in Bamburi, quiet "
            "villas in Shanzu — homes for sale, for rent, and for the weeks "
            "you wish would never end."
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
        # r55: taste-led rewrite (owner request) — character and coast
        # lead; the checking story lives on /checks/.
        default=(
            "Homes for sale, rent and short stays across Mombasa — chosen "
            "for character, from Nyali sea views to Old Town courtyards."
        ),
    )

    # ------------------------------------------------------------------
    # Brand assets + contact places (r73, BACKEND-PLAN 1D)
    # ------------------------------------------------------------------
    logo = models.ImageField(
        upload_to="brand/",
        blank=True,
        validators=[validate_brand_image],
        help_text="Your logo, shown in the site header instead of the house mark. PNG with a transparent background works best. Leave empty to keep the house mark.",
    )
    favicon = models.ImageField(
        upload_to="brand/",
        blank=True,
        validators=[validate_brand_image],
        help_text="The little icon in the browser tab. A small square PNG (64×64 or 128×128). Leave empty to keep the current icon.",
    )
    address_line = models.CharField(
        max_length=200, blank=True,
        help_text="Shown on the Contact page when filled — e.g. 'Links Road, Nyali, Mombasa'.",
    )
    opening_hours = models.CharField(
        max_length=200, blank=True,
        help_text="One line, e.g. 'Mon–Sat 8am–6pm'. Shown under the address when filled.",
    )
    instagram_url = models.URLField(
        max_length=200, blank=True,
        help_text="Full link — shown in the footer when filled.",
    )
    facebook_url = models.URLField(
        max_length=200, blank=True,
        help_text="Full link — shown in the footer when filled.",
    )
    x_url = models.URLField(
        max_length=200, blank=True,
        verbose_name="X (Twitter) URL",
        help_text="Full link — shown in the footer when filled.",
    )
    tiktok_url = models.URLField(
        max_length=200, blank=True,
        help_text="Full link — shown in the footer when filled.",
    )

    # ------------------------------------------------------------------
    # SEO & tracking (r73, BACKEND-PLAN 1E)
    # ------------------------------------------------------------------
    analytics_id = models.CharField(
        max_length=40, blank=True,
        help_text="Google Analytics 4 ID (starts with G-). Leave empty to keep the site tracker-free.",
    )
    search_console_token = models.CharField(
        max_length=120, blank=True,
        help_text="The long code Google Search Console gives you to verify the site.",
    )
    meta_description = models.TextField(
        max_length=300, blank=True,
        help_text="One or two sentences describing the site for search results. Leave empty to keep the current wording.",
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


class Testimonial(models.Model):
    """A client's published words — entered by the owner, never scraped.

    r75 (BACKEND-PLAN 3C). Display contract: a testimonial appears on
    the public site only when ``shown`` AND ``consent_given`` are both
    True (and demo rows respect the demo switch, same as listings).
    No consent means no publication — the consent flag is the honest
    gate, not a decoration.
    """

    name = models.CharField(max_length=120, help_text="e.g. Amina K.")
    role = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional — e.g. 'Bought an apartment in Nyali'.",
    )
    quote = models.TextField(help_text="The client's words, exactly as agreed.")
    # 1-5 stars, optional: an unprompted thank-you text is enough.
    rating = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    shown = models.BooleanField(
        default=True, help_text="Hidden testimonials stay stored, just not shown.",
    )
    consent_given = models.BooleanField(
        default=False,
        help_text="Only testimonials with permission are ever published.",
    )
    is_demo = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "testimonial"
        verbose_name_plural = "testimonials"
        ordering = ("position", "-created_at")

    def __str__(self):
        return f"{self.name} — {self.quote[:40]}"

    @property
    def publishable(self) -> bool:
        """The single rule: shown + consent."""
        return self.shown and self.consent_given
