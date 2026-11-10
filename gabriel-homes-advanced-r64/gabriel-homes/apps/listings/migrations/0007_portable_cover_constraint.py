"""Replace the conditional 'one cover per property' index with a portable one.

MySQL and MariaDB do not support unique indexes with a WHERE condition, so the
old partial constraint cannot be created there. The new cover_slot column is
1 for the cover and NULL otherwise; a plain unique constraint on
(property, cover_slot) gives the same guarantee on every database.
"""
from django.db import migrations, models


def _fill_cover_slot(apps, schema_editor):
    PropertyImage = apps.get_model("listings", "PropertyImage")
    PropertyImage.objects.filter(is_cover=True).update(cover_slot=1)


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0006_property_is_demo"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="propertyimage",
            name="one_cover_per_property",
        ),
        migrations.AddField(
            model_name="propertyimage",
            name="cover_slot",
            field=models.PositiveSmallIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(_fill_cover_slot, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="propertyimage",
            constraint=models.UniqueConstraint(
                fields=("property", "cover_slot"), name="one_cover_per_property"
            ),
        ),
    ]
