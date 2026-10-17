"""Admin for the listings app."""
from django.contrib import admin  # noqa: F401 — decorators (admin.action/admin.display)
from apps.core.admin_site import gabriel_admin

from .models import Amenity, Property, PropertyImage, PropertyType


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ("image", "caption", "position", "is_cover")
    readonly_fields = ()
    ordering = ("position",)


@admin.register(PropertyType, site=gabriel_admin)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug_plural", "slug_single", "is_residential", "is_commercial", "is_land", "position")
    list_filter = ("is_residential", "is_commercial", "is_land")
    search_fields = ("name", "slug_plural", "slug_single")
    ordering = ("position", "name")


@admin.register(Amenity, site=gabriel_admin)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "icon", "slug")
    list_filter = ("category",)
    search_fields = ("name", "icon")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("category", "name")


@admin.register(Property, site=gabriel_admin)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "title", "listing_type", "property_type", "location",
        "price", "status", "is_featured", "is_verified", "is_demo",
        "agent", "published_at",
    )
    list_filter = (
        "listing_type", "status", "is_featured", "is_verified", "is_demo",
        "property_type", "furnishing",
    )
    list_select_related = ("property_type", "location", "agent", "agent__user")
    search_fields = ("title", "slug", "description", "address_text")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views_count", "created_at", "updated_at", "published_at")
    inlines = [PropertyImageInline]
    filter_horizontal = ("amenities",)

    fieldsets = (
        (None, {"fields": ("title", "slug", "listing_type", "status", "property_type")}),
        ("Location", {"fields": ("location", "address_text", "lat", "lng")}),
        ("Pricing", {"fields": ("price", "price_period", "price_negotiable", "service_charge")}),
        ("Specs", {"fields": (
            "bedrooms", "bathrooms", "size_sqm", "land_size_acres",
            "furnishing", "parking_spaces", "year_built",
        )}),
        ("Amenities", {"fields": ("amenities",)}),
        ("Ownership & flags", {"fields": ("agent", "is_featured", "is_verified")}),
        ("Description", {"fields": ("description",)}),
        ("Read-only", {
            "classes": ("collapse",),
            "fields": ("views_count", "created_at", "updated_at", "published_at"),
        }),
    )

    actions = ["mark_published", "mark_archived", "mark_demo", "mark_real"]

    @admin.action(description="Publish selected listings")
    def mark_published(self, request, queryset):
        from django.utils.timezone import now
        updated = queryset.filter(status="draft").update(
            status="published", published_at=now()
        )
        self.message_user(request, f"Published {updated} listing(s).")

    @admin.action(description="Archive selected listings")
    def mark_archived(self, request, queryset):
        updated = queryset.update(status="archived")
        self.message_user(request, f"Archived {updated} listing(s).")

    @admin.action(description="Mark selected listings as demo data")
    def mark_demo(self, request, queryset):
        updated = queryset.filter(is_demo=False).update(is_demo=True)
        self.message_user(
            request,
            f"Marked {updated} listing(s) as demo (hideable via the demo switch).",
        )

    @admin.action(description="Mark selected listings as real data")
    def mark_real(self, request, queryset):
        updated = queryset.filter(is_demo=True).update(is_demo=False)
        self.message_user(
            request,
            f"Marked {updated} listing(s) as real (always visible when published).",
        )


@admin.register(PropertyImage, site=gabriel_admin)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "property", "position", "is_cover", "caption")
    list_filter = ("is_cover",)
    list_select_related = ("property",)
    search_fields = ("caption", "property__title")
    readonly_fields = ("created_at",)
