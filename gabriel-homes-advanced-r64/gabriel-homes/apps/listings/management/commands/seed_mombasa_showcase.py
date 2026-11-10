"""Add the labelled Mombasa presentation set without deleting owner data."""
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta

from apps.agents.models import AgencyProfile
from apps.listings.models import Amenity, Property, PropertyImage, PropertyType
from apps.locations.models import Location


SHOWCASE = [
    ("4BR Tropical Villa near Nyali Beach", "villas", "Nyali Centre", "sale", 48_000_000, "total", False, 4, 5, 360, "Palm-lined family villa with a private garden, generous entertaining spaces and quick access to Nyali Beach.", "Near Nyali Beach, schools and supermarkets", "pool:house/house-02.jpg"),
    ("3BR Apartment near City Mall, Nyali", "flats-apartments", "Mkomani", "sale", 19_500_000, "total", False, 3, 3, 190, "Bright modern apartment with a balcony, lift and secure parking in one of Nyali's most convenient pockets.", "Minutes from City Mall and Nyali Centre", "pool:apartment/apartment-07.jpg"),
    ("3BR Sea-view Apartment in Mkomani", "flats-apartments", "Mkomani", "rent", 165_000, "monthly", False, 3, 3, 175, "A calm long-term home with an ocean-facing balcony, airy living room and reliable security.", "Near English Point Marina and the Nyali Bridge", "pool:interior/interior-04.jpg"),
    ("4BR Family Home in Nyali", "houses", "Nyali Centre", "rent", 250_000, "monthly", False, 4, 4, 290, "Spacious family house with a green compound, staff room and easy school-run connections.", "Close to schools, healthcare and Nyali Centre", "pool:house/house-10.jpg"),
    ("Pool Villa Short Stay in Shanzu", "villas", "Shanzu", "rent", 28_000, "nightly", True, 4, 4, 310, "Furnished coastal villa for short stays, with a private pool and relaxed indoor-outdoor living.", "Near Shanzu Beach and north-coast resorts", "pool:house/house-04.jpg"),
    ("Ocean-view BnB Apartment in Nyali", "flats-apartments", "Nyali Centre", "rent", 18_000, "nightly", True, 2, 2, 130, "Fully furnished short-stay apartment with a sea-view bedroom, fast Wi-Fi and a practical work area.", "Near Nyali Beach, cafés and entertainment", "pool:interior/interior-07.jpg"),
    ("2BR Apartment by Nyali Centre", "flats-apartments", "Nyali Centre", "rent", 95_000, "monthly", False, 2, 2, 125, "Contemporary apartment for convenient everyday living, with a balcony, parking and on-site security.", "Walkable to Nyali Centre and public transport", "pool:apartment/apartment-15.jpg"),
    ("3BR Home near Haller Park, Bamburi", "houses", "Bamburi Mwisho", "sale", 15_800_000, "total", False, 3, 3, 210, "Well-planned family home with a shaded garden and quick connections to Bamburi's shops and leisure facilities.", "Near Haller Park, City Mall and the beach road", "pool:house/house-09.jpg"),
]

# Owner-supplied example media for the lead Nyali showcase listing.
LEAD_GALLERY = [
    "real-01-kitchen-island.jpg",
    "real-02-living.jpg",
    "real-03-bedroom-garden.jpg",
    "real-04-bedroom-sea.jpg",
    "real-05-dining.jpg",
    "real-06-living-terrace.jpg",
    "real-07-balcony.jpg",
    "real-08-aerial.jpg",
]
LEAD_VIDEO = Path(settings.BASE_DIR) / "media" / "property-videos" / "real" / "nyali-real-tour.mp4"


class Command(BaseCommand):
    help = "Add/update eight clearly labelled Mombasa demo listings (never deletes real data)."

    def add_arguments(self, parser):
        parser.add_argument("--no-images", action="store_true")
        parser.add_argument("--i-know-this-is-demo", action="store_true")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["i_know_this_is_demo"]:
            raise CommandError(
                "This creates fictional presentation listings. Re-run with "
                "--i-know-this-is-demo only when that is intentional."
            )
        agencies = list(AgencyProfile.objects.order_by("pk"))
        amenities = list(Amenity.objects.order_by("pk")[:4])
        if not agencies:
            raise CommandError("Run `python manage.py seed_demo --no-images` once to create reference data first.")
        created = 0
        for index, item in enumerate(SHOWCASE):
            (title, type_slug, location_name, kind, price, period, short_stay,
             beds, baths, size, description, address, filename) = item
            location = Location.objects.filter(name=location_name, level=Location.Level.NEIGHBOURHOOD).first()
            ptype = PropertyType.objects.filter(slug_plural=type_slug).first()
            if not location or not ptype:
                raise CommandError("Mombasa locations/property types are missing; run seed_demo first.")
            obj, was_created = Property.objects.update_or_create(
                slug=slugify(title),
                defaults={
                    "title": title, "description": description + " This is presentation data for the owner to replace after launch.",
                    "listing_type": kind, "property_type": ptype, "location": location,
                    "address_text": address, "lat": location.lat, "lng": location.lng,
                    "price": Decimal(price), "price_period": period, "is_short_stay": short_stay,
                    "bedrooms": beds, "bathrooms": baths, "size_sqm": size,
                    "furnishing": Property.Furnishing.FURNISHED if short_stay else Property.Furnishing.SEMI,
                    "parking_spaces": 2, "agent": agencies[index % len(agencies)],
                    "status": Property.Status.PUBLISHED,
                    # r18: all eight rows featured so each homepage market
                    # group (3 sale / 3 rent / 2 short stay) fills from this
                    # labelled presentation set.
                    "is_featured": True,
                    "is_verified": True, "is_demo": True,
                },
            )
            obj.amenities.set(amenities)
            # r59 (D-LOOP-59a): curated covers can ref the git-bundled
            # demo-photos pools via "pool:<pool>/<file>.jpg"; bare
            # filenames keep the legacy static/img/stock lookup.
            if filename.startswith("pool:"):
                source = (Path(settings.MEDIA_ROOT) / "demo-photos"
                          / filename.split(":", 1)[1])
            else:
                source = (Path(settings.BASE_DIR) / "static" / "img"
                          / "stock" / filename)
            if not options["no_images"] and source.exists() and not obj.images.exists():
                PropertyImage.objects.create(
                    property=obj, image=ContentFile(source.read_bytes(), name=filename),
                    caption=title, position=0, is_cover=True,
                )
            if index == 0 and not options["no_images"]:
                # Install the supplied photos as the lead listing's full gallery.
                if not obj.images.filter(caption__in=LEAD_GALLERY).exists():
                    lead_image = obj.images.order_by("position", "pk").first()
                    for photo_index, photo_name in enumerate(LEAD_GALLERY):
                        photo_source = Path(settings.BASE_DIR) / "static" / "img" / "real" / photo_name
                        if not photo_source.exists():
                            continue
                        if photo_index == 0 and lead_image:
                            lead_image.image.save(photo_name, ContentFile(photo_source.read_bytes()), save=False)
                            lead_image.caption = photo_name
                            lead_image.position = 0
                            lead_image.is_cover = True
                            lead_image.save()
                        else:
                            PropertyImage.objects.create(
                                property=obj,
                                image=ContentFile(photo_source.read_bytes(), name=photo_name),
                                caption=photo_name,
                                position=photo_index,
                                is_cover=(photo_index == 0 and lead_image is None),
                            )
                if LEAD_VIDEO.exists() and not obj.video:
                    obj.video.save(LEAD_VIDEO.name, ContentFile(LEAD_VIDEO.read_bytes()), save=True)
            created += int(was_created)
        # r18: keep this presentation set ahead of the bulk demo rows in the
        # homepage market ordering (-is_featured, -published_at), with a 1s
        # stagger that fixes each group's lead card.
        for offset, item in enumerate(reversed(SHOWCASE)):
            Property.objects.filter(slug=slugify(item[0])).update(
                published_at=timezone.now() - timedelta(seconds=offset)
            )
        self.stdout.write(self.style.SUCCESS(f"Mombasa showcase ready: {created} created, {8-created} updated."))
