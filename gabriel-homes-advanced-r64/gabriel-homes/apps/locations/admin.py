"""Admin for the locations app."""
from django.contrib import admin  # noqa: F401 — decorators (admin.action/admin.display)
from apps.core.admin_site import gabriel_admin

from .models import Location


@admin.register(Location, site=gabriel_admin)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "parent", "full_path_display", "lat", "lng")
    list_filter = ("level",)
    list_select_related = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("full_path_display",)

    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "level")}),
        ("Coordinates", {"fields": ("lat", "lng")}),
        ("Content", {"fields": ("description",)}),
        ("Read-only", {"classes": ("collapse",), "fields": ("full_path_display",)}),
    )

    @admin.display(description="Full path", ordering="parent")
    def full_path_display(self, obj: Location) -> str:
        return obj.full_path()
