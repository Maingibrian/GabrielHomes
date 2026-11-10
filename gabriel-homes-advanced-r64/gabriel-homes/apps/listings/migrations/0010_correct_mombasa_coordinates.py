from django.db import migrations


COORDINATES = {
    "Nyali Centre": (-4.0430, 39.7060),
    "Mkomani": (-4.0290, 39.6970),
    "Kongowea": (-4.0200, 39.7000),
    "Bamburi Mwisho": (-3.9970, 39.7080),
    "Shanzu": (-3.9790, 39.7390),
    "Mtwapa Town": (-3.9390, 39.7440),
    "Likoni Ferry": (-4.0860, 39.6610),
    "CBD": (-4.0540, 39.6670),
    "Tudor": (-4.0400, 39.6500),
}


def correct_coordinates(apps, schema_editor):
    Location = apps.get_model("locations", "Location")
    Property = apps.get_model("listings", "Property")
    Location.objects.filter(name="Mombasa", level="county").update(lat=-4.0435, lng=39.6682)
    for name, (lat, lng) in COORDINATES.items():
        locations = Location.objects.filter(
            name=name,
            parent__parent__name="Mombasa",
        )
        location_ids = list(locations.values_list("pk", flat=True))
        locations.update(lat=lat, lng=lng)
        Property.objects.filter(location_id__in=location_ids).update(lat=lat, lng=lng)


class Migration(migrations.Migration):
    dependencies = [
        ("listings", "0009_property_short_stay"),
        ("locations", "0001_initial"),
    ]

    operations = [migrations.RunPython(correct_coordinates, migrations.RunPython.noop)]
