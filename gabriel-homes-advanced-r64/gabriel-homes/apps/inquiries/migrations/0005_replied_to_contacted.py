"""Data migration r73: old "replied" enquiries become "contacted".

BACKEND-PLAN 1C — the status pipeline is new → seen → contacted →
viewing → done. The old "replied" value maps onto "contacted" (the
owner has already reached back). Idempotent and reversible: reverse
maps contacted back to replied (safe because "contacted" did not exist
before this migration, so every row it touches was "replied").
"""
from django.db import migrations


def replied_to_contacted(apps, schema_editor):
    Inquiry = apps.get_model("inquiries", "Inquiry")
    Inquiry.objects.filter(status="replied").update(status="contacted")


def contacted_to_replied(apps, schema_editor):
    Inquiry = apps.get_model("inquiries", "Inquiry")
    Inquiry.objects.filter(status="contacted").update(status="replied")


class Migration(migrations.Migration):
    dependencies = [
        ("inquiries", "0004_inquiry_is_demo_alter_inquiry_status_inquirynote"),
    ]

    operations = [
        migrations.RunPython(replied_to_contacted, contacted_to_replied),
    ]
