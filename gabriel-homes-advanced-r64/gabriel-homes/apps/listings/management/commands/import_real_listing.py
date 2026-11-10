"""
import_real_listing — import the owner's REAL listing media as a featured
Property with a walkthrough video.

Source of truth:  MEDIA_ROOT/real-listing-src/
    real-01.jpg ... real-NN.jpg   (photos, order = gallery order)
    real-tour.mp4                 (optional walkthrough video)

Files are COPIED into media/property-images/real/ and media/property-videos/real/
(only when the destination file is missing), then registered on a single
featured Property identified by the fixed slug below. Re-running the command
refreshes captions/order and re-links files without duplicating rows.

Usage:
    python manage.py import_real_listing
    python manage.py import_real_listing --src /path/to/dir   # custom source
"""
import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.agents.models import AgencyProfile
from apps.listings.models import Amenity, Property, PropertyImage, PropertyType
from apps.locations.models import Location

REAL_SLUG = "modern-beachfront-apartment-nyali"

TITLE = "Modern Beachfront Apartment in Nyali"
DESCRIPTION = """\
A genuine, owner-listed apartment in Nyali finished to a high standard.
Floor-to-ceiling glass opens onto a wide private balcony with room for
lounge seating and outdoor dining, while the open-plan living area keeps
the kitchen, dining and lounge in one bright, social space. The bedrooms
are generous and light-filled, and the hallway is dressed with framed
coastal art for a warm, personal feel.

This is a REAL listing supplied directly by the owner — the photo gallery
and the video tour show the actual property, exactly as it is today.
Contact the listing agent to arrange an in-person viewing or a live
video walkthrough."""

WANTED_AMENITY_SLUGS = [
    "balcony", "swimming-pool", "borehole-water", "mains-electricity",
    "fibre-internet", "solar-backup", "backup-generator", "24-7-security",
    "cctv-surveillance", "gated-community", "electric-fence", "sea-view",
]


class Command(BaseCommand):
    help = "Import the owner's real listing photos + walkthrough video."

    def add_arguments(self, parser):
        parser.add_argument(
            "--src", default=None,
            help="Source dir (default: MEDIA_ROOT/real-listing-src).",
        )

    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        src = Path(options["src"] or (Path(settings.MEDIA_ROOT) / "real-listing-src"))
        photos = sorted(src.glob("real-*.jpg"))
        videos = sorted(src.glob("*.mp4")) + sorted(src.glob("*.webm"))

        existing = Property.objects.filter(slug=REAL_SLUG).first()

        if not photos and not videos:
            if existing:
                self.stdout.write(
                    "Source dir missing but real listing exists; leaving as-is."
                )
                return
            raise CommandError(
                f"No media found in {src}. Stage photos as real-NN.jpg first."
            )

        agency = (
            AgencyProfile.objects.filter(slug="gabriel-homes").first()
            or AgencyProfile.objects.first()
        )
        if agency is None:
            raise CommandError("No AgencyProfile exists — run seed_demo first.")

        location = (
            Location.objects.filter(slug="nyali").first()
            or Location.objects.filter(level=Location.Level.NEIGHBOURHOOD).first()
            or Location.objects.first()
        )
        ptype = (
            PropertyType.objects.filter(slug_plural="flats-apartments").first()
            or PropertyType.objects.first()
        )

        # -- copy media (idempotent) ------------------------------------
        img_dir = Path(settings.MEDIA_ROOT) / "property-images" / "real"
        img_dir.mkdir(parents=True, exist_ok=True)
        copied = 0
        image_names = []
        for i, p in enumerate(photos, 1):
            dest = img_dir / f"nyali-real-{i:02d}.jpg"
            if not dest.exists() or dest.stat().st_size != p.stat().st_size:
                shutil.copyfile(p, dest)
                copied += 1
            image_names.append(dest.name)

        video_field = ""
        if videos:
            vdir = Path(settings.MEDIA_ROOT) / "property-videos" / "real"
            vdir.mkdir(parents=True, exist_ok=True)
            vsrc = videos[0]
            vdest = vdir / "nyali-real-tour.mp4"
            if not vdest.exists() or vdest.stat().st_size != vsrc.stat().st_size:
                shutil.copyfile(vsrc, vdest)
                copied += 1
            video_field = "property-videos/real/nyali-real-tour.mp4"

        # -- upsert the Property ----------------------------------------
        prop, created = Property.objects.update_or_create(
            slug=REAL_SLUG,
            defaults=dict(
                title=TITLE,
                description=DESCRIPTION,
                listing_type=Property.ListingType.SALE,
                property_type=ptype,
                location=location,
                lat=location.lat,
                lng=location.lng,
                price=Decimal("12500000"),
                price_negotiable=True,
                bedrooms=2,
                bathrooms=2,
                size_sqm=120,
                furnishing=Property.Furnishing.SEMI,
                parking_spaces=1,
                agent=agency,
                status=Property.Status.PUBLISHED,
                is_featured=True,
                is_verified=True,
            ),
        )
        if not prop.published_at:
            from django.utils import timezone

            prop.published_at = timezone.now()
            prop.save(update_fields=["published_at"])

        if video_field:
            prop.video.name = video_field
            prop.save(update_fields=["video"])

        # -- images: rebuild gallery in staged order ---------------------
        prop.images.all().delete()
        for i, name in enumerate(image_names):
            PropertyImage.objects.create(
                property=prop,
                image=f"property-images/real/{name}",
                caption=f"{TITLE} — photo {i + 1} of {len(image_names)}",
                position=i,
                is_cover=(i == 0),
            )

        # -- amenities: best-match by slug -------------------------------
        wanted = list(
            Amenity.objects.filter(slug__in=WANTED_AMENITY_SLUGS)
        )
        if wanted:
            prop.amenities.set(wanted)

        self.stdout.write(
            self.style.SUCCESS(
                f"Real listing {'created' if created else 'updated'}: "
                f"{prop.title} | {len(image_names)} photos | "
                f"video={'yes' if video_field else 'no'} | files copied: {copied}"
            )
        )


