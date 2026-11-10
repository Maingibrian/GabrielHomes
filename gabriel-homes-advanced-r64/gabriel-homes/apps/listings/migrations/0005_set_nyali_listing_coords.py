"""Give the flagship Nyali listing map coordinates.

The 'modern-beachfront-apartment-nyali' listing was created ad-hoc with real
media but without lat/lng, so its LOCATION map section never rendered
(the template guards on both fields). Nyali Beach, Mombasa approximates to
-4.0445, 39.6908 — good enough for the "approximate location" disclosure.

Only fills NULLs — never overwrites coordinates an owner has set.
"""

from django.db import migrations

NYALI_SLUG = "modern-beachfront-apartment-nyali"
NYALI_LAT = "-4.044500"
NYALI_LNG = "39.690800"


def set_coords(apps, schema_editor):
    Property = apps.get_model("listings", "Property")
    Property.objects.filter(
        slug=NYALI_SLUG, lat__isnull=True, lng__isnull=True
    ).update(lat=NYALI_LAT, lng=NYALI_LNG)


def unset_coords(apps, schema_editor):
    Property = apps.get_model("listings", "Property")
    Property.objects.filter(
        slug=NYALI_SLUG, lat=NYALI_LAT, lng=NYALI_LNG
    ).update(lat=None, lng=None)


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0004_property_video"),
    ]

    operations = [
        migrations.RunPython(set_coords, unset_coords),
    ]
