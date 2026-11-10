# r13 — new homepage slogan ("Good homes, properly checked.").

from django.db import migrations, models

# Exact-match healing map (old default -> new default), same pattern as
# 0006: a row is updated ONLY while it still byte-matches the old default,
# so any copy the owner already edited in /manage/ survives untouched.
# Reverse is a no-op.
OLD_TO_NEW = {
    "hero_tag": (
        "Gabriel Homes · Homes for sale, rent and short stays",
        "Gabriel Homes · Mombasa, Kenya",
    ),
    "hero_heading_lead": (
        "Homes in Kenya,",
        "Good homes,",
    ),
    "hero_heading_accent": (
        "checked",
        "properly",
    ),
    "hero_heading_tail": (
        "before we show them.",
        "checked.",
    ),
    "hero_subtitle": (
        "We help people buy, rent and book short stays across Mombasa. Every "
        "listing we publish is checked by Gabriel and the team first.",
        "Buy, rent or book a short stay anywhere in Mombasa. Gabriel and "
        "the team check every listing before it goes live — and if we "
        "cannot check something, we tell you.",
    ),
}


def heal_old_slogan(apps, schema_editor):
    BrandSettings = apps.get_model("core", "BrandSettings")
    for row in BrandSettings.objects.all():
        changed = False
        for field, (old_value, new_value) in OLD_TO_NEW.items():
            if getattr(row, field) == old_value:
                setattr(row, field, new_value)
                changed = True
        if changed:
            row.save(update_fields=list(OLD_TO_NEW) + ["updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_alter_brandsettings_about_heading_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="brandsettings",
            name="hero_tag",
            field=models.CharField(
                default="Gabriel Homes · Mombasa, Kenya",
                help_text="Short label above the homepage headline.",
                max_length=120,
            ),
        ),
        migrations.AlterField(
            model_name="brandsettings",
            name="hero_heading_lead",
            field=models.CharField(default="Good homes,", max_length=120),
        ),
        migrations.AlterField(
            model_name="brandsettings",
            name="hero_heading_accent",
            field=models.CharField(default="properly", max_length=80),
        ),
        migrations.AlterField(
            model_name="brandsettings",
            name="hero_heading_tail",
            field=models.CharField(default="checked.", max_length=160),
        ),
        migrations.AlterField(
            model_name="brandsettings",
            name="hero_subtitle",
            field=models.TextField(
                default=(
                    "Buy, rent or book a short stay anywhere in Mombasa. Gabriel and "
                    "the team check every listing before it goes live — and if we "
                    "cannot check something, we tell you."
                ),
                max_length=500,
            ),
        ),
        # Heal singleton rows that still carry the old slogan (idempotent;
        # owner-edited values are never touched).
        migrations.RunPython(heal_old_slogan, migrations.RunPython.noop),
    ]
