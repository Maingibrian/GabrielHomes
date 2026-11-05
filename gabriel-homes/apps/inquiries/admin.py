"""Admin for the inquiries app."""
from django.contrib import admin  # noqa: F401 — decorators (admin.action/admin.display)
from apps.core.admin_site import gabriel_admin

from .models import Inquiry


@admin.register(Inquiry, site=gabriel_admin)
class InquiryAdmin(admin.ModelAdmin):
    list_display = (
        "name", "email", "phone", "property_ref",
        "status", "is_spam_display", "created_at",
    )
    list_filter = ("status", "created_at")
    list_select_related = ("property_ref",)
    search_fields = ("name", "email", "phone", "message")
    readonly_fields = ("created_at", "updated_at", "honeypot", "submitter_ip", "is_spam_display")
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("property_ref", "user", "status")}),
        ("Sender", {"fields": ("name", "email", "phone", "message")}),
        ("Spam control", {
            "classes": ("collapse",),
            "fields": ("honeypot", "submitter_ip", "is_spam_display"),
        }),
        ("Timestamps", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    actions = ["mark_read", "mark_replied"]

    @admin.display(boolean=True, description="Spam?")
    def is_spam_display(self, obj: Inquiry) -> bool:
        return obj.is_spam

    @admin.action(description="Mark selected as read")
    def mark_read(self, request, queryset):
        updated = queryset.filter(status="new").update(status="read")
        self.message_user(request, f"Marked {updated} inquiry/inquiries as read.")

    @admin.action(description="Mark selected as replied")
    def mark_replied(self, request, queryset):
        updated = queryset.exclude(status="replied").update(status="replied")
        self.message_user(request, f"Marked {updated} inquiry/inquiries as replied.")
