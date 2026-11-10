"""Reconcile the two parallel r13 slogan lineages.

Two r13 migrations both rewrote the hero slogan:
  - core.0007_slogan_good_homes_properly_checked -> "Good homes, properly
    checked."  (the slogan the live site actually shows; models.py and the
    phase-2 test treat it as canonical)
  - core.0007_hero_slogan_r13 + core.0008 defaults -> "We see every home
    before you do."  (a parallel attempt; its data migration still hijacks
    freshly-created rows that carry the original defaults)

This migration leaves deliberately-edited rows alone and only converts rows
still carrying the abandoned attempt back to the canonical slogan, so a
fresh install matches what the live site shows.
"""

from django.db import migrations


NEW_LEAD = "Good homes,"
NEW_ACCENT = "properly"
NEW_TAIL = "checked."
NEW_SUBTITLE = (
    "Buy, rent or book a short stay anywhere in Mombasa. Gabriel and "
    "the team check every listing before it goes live — and if we "
    "cannot check something, we tell you."
)

OLD_LEAD = "We see every home"
OLD_ACCENT = "before"
OLD_TAIL = "you do."
OLD_SUBTITLE = (
    "Buy, rent or book a short stay in Mombasa. We visit the homes, "
    "check the paperwork, and tell you what we honestly found."
)

FIELDS = [
    "hero_heading_lead", "hero_heading_accent",
    "hero_heading_tail", "hero_subtitle",
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


def adopt_canonical_slogan(apps, schema_editor):
    _swap(
        apps, schema_editor,
        [OLD_LEAD, OLD_ACCENT, OLD_TAIL, OLD_SUBTITLE],
        [NEW_LEAD, NEW_ACCENT, NEW_TAIL, NEW_SUBTITLE],
    )


def restore_abandoned_slogan(apps, schema_editor):
    _swap(
        apps, schema_editor,
        [NEW_LEAD, NEW_ACCENT, NEW_TAIL, NEW_SUBTITLE],
        [OLD_LEAD, OLD_ACCENT, OLD_TAIL, OLD_SUBTITLE],
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_merge_20261103_1542"),
    ]

    operations = [
        migrations.RunPython(adopt_canonical_slogan, restore_abandoned_slogan),
    ]
