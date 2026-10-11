"""Listings models — PropertyType, Amenity, Property, PropertyImage.

WORK.md §6 spec. The custom `PropertyQuerySet.published()` manager is
the single chokepoint that keeps draft / archived listings off the
public site (every public view MUST use `.published()`).
"""
from __future__ import annotations

import os
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils.text import slugify
from django.utils.timezone import now


# ---------------------------------------------------------------------------
# Upload validators
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}


def validate_image_file(image):
    """Validate uploaded image: type + size.

    Per WORK.md §11 Phase 7: upload validation (type and size).
    """
    if image.size > MAX_UPLOAD_SIZE:
        raise ValidationError(
            f"Image too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)} MB. "
            f"This file is {image.size // (1024*1024)} MB."
        )
    # Check extension
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}."
        )
    # Check content type if available
    if hasattr(image, "content_type") and image.content_type:
        if image.content_type not in ALLOWED_IMAGE_MIMES:
            raise ValidationError(
                f"Unsupported content type '{image.content_type}'. Allowed: {', '.join(sorted(ALLOWED_IMAGE_MIMES))}."
            )


def property_image_upload_path(instance, filename: str) -> str:
    """Upload path for property images: property-images/<year>/<month>/<filename>."""
    from django.utils.timezone import now as tz_now
    ym = tz_now().strftime("%Y/%m")
    return f"property-images/{ym}/{filename}"


# ---------------------------------------------------------------------------
# PropertyType
# ---------------------------------------------------------------------------
class PropertyType(models.Model):
    """A type of property — also used in SEO-friendly URLs.

    `slug_plural` is used in listing-browse URLs (e.g. /flats-apartments-for-sale/),
    `slug_single` is used in titles ("Apartment for sale in Mombasa").
    """

    name = models.CharField(max_length=80, unique=True)
    slug_plural = models.SlugField(max_length=80, unique=True)
    slug_single = models.SlugField(max_length=80, unique=True)
    is_residential = models.BooleanField(default=True)
    is_commercial = models.BooleanField(default=False)
    is_land = models.BooleanField(default=False)

    # Display ordering for the home page's "Browse by type" block.
    position = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "property type"
        verbose_name_plural = "property types"
        ordering = ("position", "name")
        indexes = [models.Index(fields=["slug_plural"])]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Amenity
# ---------------------------------------------------------------------------
class Amenity(models.Model):
    """A feature a property can have (pool, gym, borehole, etc.).

    `icon` is a string key (e.g. 'ph-swimming-pool') that the template
    layer will map to an inline Phosphor SVG in Phase 2.
    """

    class Category(models.TextChoices):
        SECURITY = "security", "Security"
        UTILITIES = "utilities", "Utilities"
        LIFESTYLE = "lifestyle", "Lifestyle"
        BUILDING = "building", "Building"

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    icon = models.CharField(
        max_length=60,
        blank=True,
        help_text="Phosphor icon key, e.g. 'ph-swimming-pool'.",
    )
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.LIFESTYLE)

    class Meta:
        verbose_name = "amenity"
        verbose_name_plural = "amenities"
        ordering = ("category", "name")
        indexes = [models.Index(fields=["category"])]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Property + custom QuerySet
# ---------------------------------------------------------------------------
class PropertyQuerySet(models.QuerySet):
    """Only `published` listings are shown on the public site."""

    def published(self) -> "PropertyQuerySet":
        return self.filter(
            status=Property.Status.PUBLISHED,
            published_at__isnull=False,
            published_at__lte=now(),
        )

    def for_sale(self) -> "PropertyQuerySet":
        return self.filter(listing_type=Property.ListingType.SALE)

    def for_rent(self) -> "PropertyQuerySet":
        return self.filter(listing_type=Property.ListingType.RENT)

    def featured(self) -> "PropertyQuerySet":
        return self.filter(is_featured=True)


class Property(models.Model):
    """A property listing."""

    class ListingType(models.TextChoices):
        SALE = "sale", "For Sale"
        RENT = "rent", "To Let"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        UNDER_OFFER = "under_offer", "Under Offer"
        SOLD_LET = "sold_let", "Sold / Let"
        ARCHIVED = "archived", "Archived"

    class Furnishing(models.TextChoices):
        UNFURNISHED = "unfurnished", "Unfurnished"
        SEMI = "semi", "Semi-furnished"
        FURNISHED = "furnished", "Furnished"

    class PricePeriod(models.TextChoices):
        TOTAL = "total", "Total"
        MONTHLY = "monthly", "Per month"

    # Identity
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    # S12 input limit: 20 000 chars ≈ 3 000 words — far above any real listing
    # copy, but stops multi-megabyte junk from admins or API misuse.
    description = models.TextField(max_length=20000)

    listing_type = models.CharField(max_length=8, choices=ListingType.choices, db_index=True)
    property_type = models.ForeignKey(
        PropertyType, on_delete=models.PROTECT, related_name="properties"
    )
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.PROTECT,
        related_name="properties",
        limit_choices_to={"level": "neighbourhood"},
        help_text="Pick the most specific (neighbourhood-level) location.",
    )
    address_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Public-safe street description. Never include house numbers if the owner wants privacy.",
    )
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Pricing
    # S12 input limit: min 0 rejects negative prices; the max_digits=14 DB
    # cap already bounds the upper end (KSh 9 999 999 999 999.99).
    price = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    price_period = models.CharField(
        max_length=8, choices=PricePeriod.choices, default=PricePeriod.TOTAL
    )
    price_negotiable = models.BooleanField(default=False)

    # Specs
    # S12 input limits: Positive* fields reject negatives at DB and validation
    # level; the Max validators reject absurd values (no 500-bedroom flat).
    bedrooms = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(20)]
    )
    bathrooms = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(20)]
    )
    size_sqm = models.PositiveIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(100000)]
    )
    land_size_acres = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    furnishing = models.CharField(
        max_length=16, choices=Furnishing.choices, default=Furnishing.UNFURNISHED
    )
    parking_spaces = models.PositiveSmallIntegerField(default=0)
    year_built = models.PositiveSmallIntegerField(null=True, blank=True)
    service_charge = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Monthly service charge in KES (rentals).",
    )

    amenities = models.ManyToManyField(Amenity, blank=True, related_name="properties")

    # Optional walkthrough video (mp4/webm) rendered on the detail page
    # beneath the photo gallery. Blank for image-only listings.
    video = models.FileField(
        upload_to="property-videos/%Y/%m/",
        blank=True,
        verbose_name="Walkthrough video",
        help_text="Optional listing walkthrough video (mp4 or webm).",
    )

    # Ownership & state
    agent = models.ForeignKey(
        "agents.AgencyProfile",
        on_delete=models.PROTECT,
        related_name="properties",
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True
    )

    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = PropertyQuerySet.as_manager()

    class Meta:
        verbose_name = "property"
        verbose_name_plural = "properties"
        ordering = ("-published_at", "-created_at")
        indexes = [
            models.Index(fields=["status", "listing_type", "property_type", "location"]),
            models.Index(fields=["price"]),
            models.Index(fields=["published_at"]),
            models.Index(fields=["is_featured"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_listing_type_display()})"

    # ------------------------------------------------------------------
    # Validation + slug
    # ------------------------------------------------------------------
    def clean(self):
        super().clean()
        # Sale listings use total pricing; rent uses monthly.
        if self.listing_type == Property.ListingType.SALE and self.price_period != Property.PricePeriod.TOTAL:
            raise ValidationError({"price_period": "Sale listings must use 'total' pricing."})
        if self.listing_type == Property.ListingType.RENT and self.price_period != Property.PricePeriod.MONTHLY:
            raise ValidationError({"price_period": "Rent listings must use 'monthly' pricing."})
        if self.price is not None and Decimal(self.price) < 0:
            # Decimal() coercion: price is a str when the instance was not
            # built through a ModelForm (e.g. constructed in tests/shells).
            raise ValidationError({"price": "Price cannot be negative."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._make_unique_slug()
        # Stamp published_at the first time we flip into 'published'.
        if self.status == Property.Status.PUBLISHED and not self.published_at:
            self.published_at = now()
        # If the listing is taken off the public site, leave published_at intact
        # (we use status, not published_at, to decide visibility).
        super().save(*args, **kwargs)

    def _make_unique_slug(self) -> str:
        base = slugify(self.title) or "listing"
        slug = base
        i = 2
        qs = Property.objects.filter(slug=slug)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        while qs.exists():
            slug = f"{base}-{i}"
            i += 1
            qs = Property.objects.filter(slug=slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
        return slug

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @property
    def is_published(self) -> bool:
        return (
            self.status == Property.Status.PUBLISHED
            and self.published_at is not None
            and self.published_at <= now()
        )

    def increment_views(self) -> None:
        """Bump the views counter without triggering updated_at."""
        Property.objects.filter(pk=self.pk).update(views_count=models.F("views_count") + 1)

    def get_absolute_url(self) -> str:
        """Public detail-page URL.

        Phase 3 builds the actual search/browse URLs; the listing detail
        URL pattern (`/listing/<slug>-<id>/`) is wired in Phase 4. For now
        this returns the future-shape URL so cards can link to it.
        """
        return f"/listing/{self.slug}-{self.pk}/"


# ---------------------------------------------------------------------------
# PropertyImage — one cover per property enforced via partial unique index
# ---------------------------------------------------------------------------
class PropertyImage(models.Model):
    """An image attached to a Property. Exactly one must be the cover."""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(
        upload_to=property_image_upload_path,
        validators=[validate_image_file],
    )
    caption = models.CharField(max_length=200, blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    is_cover = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "property image"
        verbose_name_plural = "property images"
        ordering = ("position", "pk")
        constraints = [
            # At most one cover per property.
            UniqueConstraint(
                fields=["property"],
                condition=Q(is_cover=True),
                name="one_cover_per_property",
            ),
        ]

    def __str__(self) -> str:
        return f"Image #{self.pk} for {self.property.title}"

    def clean(self):
        super().clean()
        if self.is_cover:
            # Disallow setting a second cover via .save(); the partial unique
            # constraint is the real guard at the DB layer.
            existing = PropertyImage.objects.filter(
                property=self.property, is_cover=True
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    {"is_cover": "This property already has a cover image."}
                )
