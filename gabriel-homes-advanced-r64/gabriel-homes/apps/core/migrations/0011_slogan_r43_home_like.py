"""r43 (owner request): retire the "Good homes, properly checked." slogan.

The owner found the framing clinical ("weird framing... it needs to be
something home like"). The headline now leads with the warm promise —
"A place to come home to." — while hero_subtitle keeps the checking /
trust story ("Gabriel and the team check every listing before it goes
live ...").

Mirrors core.0010: only rows still carrying the old slogan are swapped,
so deliberately-edited rows (manage portal) are left alone. Fresh rows
pick up the new defaults from models.py.
"""

from django.db import migrations


OLD_LEAD = "Good homes,"
OLD_ACCENT = "properly"
OLD_TAIL = "checked."

NEW_LEAD = "A place to"
NEW_ACCENT = "come home"
NEW_TAIL = "to."

FIELDS = [
    "hero_heading_lead", "hero_heading_accent", "hero_heading_tail",
]


def _swap(apps, schema_editor, from_values, to_values):
    BrandSettings = apps.get_model("core", "BrandSettings")
    for brand in BrandSettings.objects.all():
        changed = False
        for field, old, new in zip(FIELDS, from_values, to_values):
            if getattr(brand, field) == old:
                setattr(brand, field, new)
                changed = True
        if changed:
            brand.save(update_fields=FIELDS)


def adopt_home_like_slogan(apps, schema_editor):
    _swap(
        apps, schema_editor,
        [OLD_LEAD, OLD_ACCENT, OLD_TAIL],
        [NEW_LEAD, NEW_ACCENT, NEW_TAIL],
    )


def restore_previous_slogan(apps, schema_editor):
    _swap(
        apps, schema_editor,
        [NEW_LEAD, NEW_ACCENT, NEW_TAIL],
        [OLD_LEAD, OLD_ACCENT, OLD_TAIL],
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_adopt_canonical_r13_slogan"),
    ]

    operations = [
        migrations.RunPython(adopt_home_like_slogan, restore_previous_slogan),
    ]
