"""Seed the BrandSettings singleton row (idempotent).

The brand contact row is read on every public request via the
``brand_contact`` context processor. Creating it here (instead of lazily
on first GET) keeps requests read-only and the query count flat: one
SELECT per request in steady state. Idempotent — get_or_create on pk=1,
safe to run against any database state, destroys nothing.
"""
from django.db import migrations


def seed_brand_row(apps, schema_editor):
    brand = apps.get_model("core", "BrandSettings")
    brand.objects.get_or_create(pk=1)


def unseed_brand_row(apps, schema_editor):
    # Reverse is a no-op: never delete data (protocol §4).
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_brandsettings"),
    ]

    operations = [
        migrations.RunPython(seed_brand_row, unseed_brand_row),
    ]
