"""Admin for the accounts app."""
from django.contrib import admin  # noqa: F401 — decorators (admin.action/admin.display)
from apps.core.admin_site import gabriel_admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import SavedProperty, SavedSearch, User


@admin.register(User, site=gabriel_admin)
class UserAdmin(DjangoUserAdmin):
    """Email-based user admin — adapted from Django's default UserAdmin."""

    ordering = ("-date_joined",)
    list_display = ("email", "full_name", "is_staff", "is_agent", "is_active", "date_joined")
    list_filter = ("is_staff", "is_agent", "is_active", "is_superuser")
    search_fields = ("email", "full_name", "phone")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("full_name", "phone")}),
        ("Permissions", {"fields": (
            "is_active", "is_staff", "is_agent", "is_superuser",
            "groups", "user_permissions",
        )}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2"),
        }),
    )

    readonly_fields = ("date_joined", "last_login")


@admin.register(SavedProperty, site=gabriel_admin)
class SavedPropertyAdmin(admin.ModelAdmin):
    list_display = ("user", "property", "created_at")
    list_filter = ("created_at",)
    list_select_related = ("user", "property")
    search_fields = ("user__email", "property__title")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)


@admin.register(SavedSearch, site=gabriel_admin)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    list_filter = ("created_at",)
    list_select_related = ("user",)
    search_fields = ("name", "querystring", "user__email")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
