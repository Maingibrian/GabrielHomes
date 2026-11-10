"""r13 — new hero slogan.

The owner asked for a stronger homepage headline. Old:
    "Homes in Kenya, checked before we show them."
New:
    "We see every home before you do."

The subtitle is updated too: it used to repeat the "checked first" promise
the headline already makes, so it now says what the promise means in
practice.

The migration only touches rows still carrying the old defaults, so any
owner customisation made through /manage/site-content/ is preserved.
"""
from django.db import migrations

OLD_LEAD = "Homes in Kenya,"
OLD_ACCENT = "checked"
OLD_TAIL = "before we show them."
OLD_SUBTITLE = (
    "We help people buy, rent and book short stays across Mombasa. "
    "Every listing we publish is checked by Gabriel and the team first."
)

NEW_LEAD = "We see every home"
NEW_ACCENT = "before"
NEW_TAIL = "you do."
NEW_SUBTITLE = (
    "Buy, rent or book a short stay in Mombasa. We visit the homes, "
    "check the paperwork, and tell you what we honestly found."
)


def update_slogan(apps, schema_editor):
    BrandSettings = apps.get_model("core", "BrandSettings")
    for brand in BrandSettings.objects.all():
        changed = False
        if brand.hero_heading_lead == OLD_LEAD:
            brand.hero_heading_lead = NEW_LEAD
            changed = True
        if brand.hero_heading_accent == OLD_ACCENT:
            brand.hero_heading_accent = NEW_ACCENT
            changed = True
        if brand.hero_heading_tail == OLD_TAIL:
            brand.hero_heading_tail = NEW_TAIL
            changed = True
        if brand.hero_subtitle == OLD_SUBTITLE:
            brand.hero_subtitle = NEW_SUBTITLE
            changed = True
        if changed:
            brand.save(update_fields=[
                "hero_heading_lead", "hero_heading_accent",
                "hero_heading_tail", "hero_subtitle",
            ])


def restore_slogan(apps, schema_editor):
    BrandSettings = apps.get_model("core", "BrandSettings")
    for brand in BrandSettings.objects.all():
        changed = False
        if brand.hero_heading_lead == NEW_LEAD:
            brand.hero_heading_lead = OLD_LEAD
            changed = True
        if brand.hero_heading_accent == NEW_ACCENT:
            brand.hero_heading_accent = OLD_ACCENT
            changed = True
        if brand.hero_heading_tail == NEW_TAIL:
            brand.hero_heading_tail = OLD_TAIL
            changed = True
        if brand.hero_subtitle == NEW_SUBTITLE:
            brand.hero_subtitle = OLD_SUBTITLE
            changed = True
        if changed:
            brand.save(update_fields=[
                "hero_heading_lead", "hero_heading_accent",
                "hero_heading_tail", "hero_subtitle",
            ])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_alter_brandsettings_about_heading_and_more"),
    ]

    operations = [
        migrations.RunPython(update_slogan, restore_slogan),
    ]
