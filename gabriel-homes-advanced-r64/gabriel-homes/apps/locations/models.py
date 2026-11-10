"""Locations models — county / area / neighbourhood tree.

WORK.md §6 spec:
    Location: name, slug, parent (self FK, null), level (county | area |
    neighbourhood), lat, lng. Unique slug per parent. Methods
    get_descendants() and full_path().
"""
from __future__ import annotations

from django.db import models
from django.utils.text import slugify as django_slugify


class Location(models.Model):
    """Hierarchical location: county > area > neighbourhood.

    Levels are an enum-like `TextChoices` for clarity. `parent` is null
    only for counties. `lat` / `lng` are nullable because some leaf
    neighbourhoods won't have a pinned coordinate.

    The tree is shallow (3 levels max) so a recursive `get_descendants()`
    is acceptable for v1. If listings grow large enough to make this a
    bottleneck, switch to a materialised path or ltree on Postgres.
    """

    class Level(models.TextChoices):
        COUNTY = "county", "County"
        AREA = "area", "Area"
        NEIGHBOURHOOD = "neighbourhood", "Neighbourhood"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    level = models.CharField(max_length=16, choices=Level.choices)
    lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    # Friendly description used in SEO H1s ("Flats for sale in Mombasa")
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "location"
        verbose_name_plural = "locations"
        # Slug must be unique within its parent (counties have no parent).
        unique_together = (("parent", "slug"),)
        ordering = ("level", "name")
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["parent"]),
        ]

    def __str__(self) -> str:
        return self.full_path()

    # ------------------------------------------------------------------
    # Slug + tree helpers
    # ------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = django_slugify(self.name)
        # Derive level from parent if caller didn't set it.
        if not self.level:
            self.level = (
                Location.Level.AREA
                if self.parent and self.parent.level == Location.Level.COUNTY
                else Location.Level.NEIGHBOURHOOD
                if self.parent
                else Location.Level.COUNTY
            )
        super().save(*args, **kwargs)

    def get_descendants(self, include_self: bool = False) -> models.QuerySet["Location"]:
        """Return all descendants of this location.

        Walks the tree breadth-first. Three levels deep is the v1 max,
        so we cap at a depth of 3 to keep the query bounded.
        """
        pks: set[int] = set()
        if include_self:
            pks.add(self.pk)

        frontier = [self.pk]
        # 3 levels deep is the v1 contract; guard against runaway depth.
        for _ in range(3):
            if not frontier:
                break
            children = Location.objects.filter(parent__in=frontier).values_list("pk", flat=True)
            frontier = list(children)
            pks.update(frontier)

        return Location.objects.filter(pk__in=pks).order_by("level", "name")

    def get_ancestors(self, include_self: bool = False) -> list["Location"]:
        """Walk up the parent chain — useful for breadcrumbs."""
        chain: list[Location] = []
        node: Location | None = self if include_self else self.parent
        while node is not None:
            chain.append(node)
            node = node.parent
        chain.reverse()
        return chain

    def full_path(self) -> str:
        """Human-friendly 'Mombasa > Nyali > Nyali Centre' string."""
        names = [loc.name for loc in self.get_ancestors(include_self=True)]
        return " > ".join(names)

    @property
    def is_leaf(self) -> bool:
        return not self.children.exists()
