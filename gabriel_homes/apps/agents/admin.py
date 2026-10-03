"""Admin for the agents app."""
from django.contrib import admin

from .models import AgencyProfile


@admin.register(AgencyProfile)
class AgencyProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_verified", "phone", "whatsapp", "office_location")
    list_filter = ("is_verified",)
    list_select_related = ("user", "office_location")
    search_fields = ("name", "slug", "email", "phone", "user__email")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("user", "name", "slug", "is_verified")}),
        ("Contact", {"fields": ("phone", "whatsapp", "email", "website")}),
        ("Office", {"fields": ("office_location",)}),
        ("Branding", {"fields": ("logo", "bio")}),
        ("Timestamps", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )
