"""Admin for the agents app."""
from django.contrib import admin  # noqa: F401 — decorators (admin.action/admin.display)
from apps.core.admin_site import gabriel_admin

from .models import AgencyProfile


@admin.register(AgencyProfile, site=gabriel_admin)
class AgencyProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_verified", "is_demo", "phone", "whatsapp", "office_location")
    list_filter = ("is_verified", "is_demo")
    list_select_related = ("user", "office_location")
    search_fields = ("name", "slug", "email", "phone", "user__email")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    actions = ["mark_demo", "mark_real"]

    @admin.action(description="Mark selected agencies as demo data")
    def mark_demo(self, request, queryset):
        updated = queryset.filter(is_demo=False).update(is_demo=True)
        self.message_user(
            request,
            f"Marked {updated} agency/agencies as demo (hideable via the demo switch).",
        )

    @admin.action(description="Mark selected agencies as real data")
    def mark_real(self, request, queryset):
        updated = queryset.filter(is_demo=True).update(is_demo=False)
        self.message_user(
            request,
            f"Marked {updated} agency/agencies as real (always listed).",
        )

    fieldsets = (
        (None, {"fields": ("user", "name", "slug", "is_verified")}),
        ("Contact", {"fields": ("phone", "whatsapp", "email", "website")}),
        ("Office", {"fields": ("office_location",)}),
        ("Branding", {"fields": ("logo", "bio")}),
        ("Timestamps", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )
