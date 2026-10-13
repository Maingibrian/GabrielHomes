"""Seed data for Gabriel Homes — locations, property types, amenities,
6 agencies, ~80 fictional listings with Pillow-generated covers.

Idempotent: re-running will not duplicate records. Identifiers are
matched on natural keys (slug / email / name) before creating.

Usage:
    python manage.py seed_demo               # full seed
    python manage.py seed_demo --no-images   # skip image generation (faster)
    python manage.py seed_demo --clear       # DELETE all seeded data first
"""
from __future__ import annotations

import hashlib
import io
import random
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageDraw

from apps.accounts.models import User
from apps.agents.models import AgencyProfile
from apps.listings.models import Amenity, Property, PropertyImage, PropertyType
from apps.locations.models import Location

random.seed(42)  # reproducible seed


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
PROPERTY_TYPES = [
    # (name, slug_plural, slug_single, is_residential, is_commercial, is_land, position)
    ("Flats & Apartments", "flats-apartments", "apartment", True, False, False, 1),
    ("Houses",              "houses",           "house",     True, False, False, 2),
    ("Townhouses",          "townhouses",       "townhouse", True, False, False, 3),
    ("Maisonettes",         "maisonettes",      "maisonette",True, False, False, 4),
    ("Bungalows",           "bungalows",        "bungalow",  True, False, False, 5),
    ("Villas",              "villas",           "villa",     True, False, False, 6),
    ("Land",                "land",             "land",      False, False, True,  7),
    ("Commercial Property", "commercial-property","commercial-property", False, True, False, 8),
    ("Offices",             "offices",          "office",    False, True, False, 9),
    ("Shops",               "shops",            "shop",      False, True, False, 10),
    ("Warehouses",          "warehouses",       "warehouse", False, True, False, 11),
]

AMENITIES = [
    # (name, icon, category)
    ("24/7 Security",        "ph-shield-check",      "security"),
    ("CCTV Surveillance",    "ph-video-camera",      "security"),
    ("Electric Fence",       "ph-fence",             "security"),
    ("Gated Community",      "ph-garage",            "security"),
    ("Guard Service",        "ph-person-simple",     "security"),
    ("Borehole Water",       "ph-drop",              "utilities"),
    ("Mains Electricity",    "ph-plug",              "utilities"),
    ("Solar Backup",         "ph-sun",               "utilities"),
    ("Fibre Internet",       "ph-wifi-high",         "utilities"),
    ("Backup Generator",     "ph-plugs",             "utilities"),
    ("Swimming Pool",        "ph-swimming-pool",     "lifestyle"),
    ("Gym",                  "ph-barbell",           "lifestyle"),
    ("Garden",               "ph-flower-lotus",      "lifestyle"),
    ("Balcony",              "ph-buildings",         "lifestyle"),
    ("Sea View",             "ph-wave",              "lifestyle"),
    ("Air Conditioning",     "ph-wind",              "lifestyle"),
    ("Ensuite Bedrooms",     "ph-bed",               "lifestyle"),
    ("Walk-in Closet",       "ph-t-shirt",           "lifestyle"),
    ("Modular Kitchen",      "ph-cooking-pot",       "lifestyle"),
    ("Family Room",          "ph-sofa",              "lifestyle"),
    ("Parking",              "ph-car",               "building"),
    ("Servant Quarter",      "ph-house-line",        "building"),
    ("Lift",                 "ph-elevator",          "building"),
    ("Perimeter Wall",       "ph-brick-wall",        "building"),
]


# Location tree: county > [(area, [(neighbourhood, lat, lng), ...]), ...]
LOCATIONS = [
    ("Mombasa", (-1.2864, 36.8172), [
        ("Nyali",    [ ("Nyali Centre",   -1.2570, 36.8030),
                       ("Mkomani",        -1.2490, 36.7910),
                       ("Kongowea",       -1.2640, 36.8360) ]),
        ("Bamburi",  [ ("Bamburi Mwisho", -1.2190, 36.8550),
                       ("Shanzu",         -1.2070, 36.8660) ]),
        ("Mtwapa",   [ ("Mtwapa Town",    -1.1960, 36.8790) ]),
        ("Likoni",   [ ("Likoni Ferry",   -1.3260, 36.8360) ]),
        ("Town",     [ ("CBD",            -1.2830, 36.8210),
                       ("Tudor",          -1.2680, 36.8180) ]),
    ]),
    ("Nairobi", (-1.2864, 36.8172), [
        ("Westlands", [ ("Westlands",      -1.2630, 36.8040),
                        ("Parklands",      -1.2590, 36.8190) ]),
        ("Kilimani",  [ ("Kilimani",       -1.2900, 36.7860),
                        ("Lavington",      -1.2790, 36.7660),
                        ("Kileleshwa",     -1.2810, 36.7860) ]),
        ("Karen",     [ ("Karen",          -1.3190, 36.7080),
                        ("Langata",        -1.3650, 36.7450) ]),
        ("Runda",     [ ("Runda",          -1.2250, 36.8090),
                        ("Muthaiga",       -1.2410, 36.8510) ]),
    ]),
    ("Kilifi", (-3.6338, 39.8488), [
        ("Kilifi Town", [ ("Kilifi Town", -3.6338, 39.8488) ]),
        ("Watamu",      [ ("Watamu",      -3.3420, 40.0220) ]),
        ("Malindi",     [ ("Malindi",     -3.2180, 40.1170) ]),
    ]),
    ("Kwale", (-4.1735, 39.4505), [
        ("Diani",    [ ("Diani Beach",   -4.2720, 39.5840),
                       ("Galu",          -4.3010, 39.5840) ]),
        ("Ukunda",   [ ("Ukunda Town",   -4.2840, 39.5670) ]),
        ("Msambweni",[ ("Msambweni",     -4.4760, 39.4770) ]),
    ]),
    ("Kiambu", (-1.1714, 36.8356), [
        ("Kiambu Town", [ ("Kiambu Town", -1.1714, 36.8356) ]),
        ("Ruiru",       [ ("Ruiru",       -1.1460, 36.9600),
                          ("Juja",         -1.1020, 37.0090) ]),
        ("Limuru",      [ ("Limuru",      -1.1070, 36.6420),
                          ("Kikuyu",       -1.2520, 36.6730) ]),
    ]),
    ("Kajiado", (-1.8555, 36.7822), [
        ("Ngong",       [ ("Ngong",         -1.3520, 36.6600) ]),
        ("Kitengela",   [ ("Kitengela",     -1.4820, 36.8860),
                          ("Ongata Rongai", -1.3920, 36.7630) ]),
        ("Kiserian",    [ ("Kiserian",      -1.4130, 36.7100) ]),
    ]),
]


AGENCIES = [
    # (name, contact_email, phone, whatsapp, area_name) — area_name is matched to a Location
    ("Gabriel Homes",            "hello@gabrielhomes.co.ke",       "+254712345678", "+254712345678", "Nyali"),
    ("Coast Property Co.",       "info@coastproperty.co.ke",       "+254723456789", "+254723456789", "Bamburi"),
    ("Pwani Realty",             "team@pwanirealty.co.ke",         "+254734567890", "+254734567890", "Diani"),
    ("Highlands Estates",        "hello@highlandsestates.co.ke",   "+254745678901", "+254745678901", "Ruiru"),
    ("Ngong Ridge Properties",   "info@ngongridge.co.ke",          "+254756789012", "+254756789012", "Ngong"),
    ("Mombasa Bay Realty",       "hello@mombasabayrealty.co.ke",   "+254767890123", "+254767890123", "Mtwapa"),
]

# Real-sounding agency bios — shown on the About team cards and the agent
# profile page. Keyed by slug; unknown slugs fall back to a neutral line.
AGENCY_BIOS = {
    "gabriel-homes": (
        "Our flagship Nyali office — curated homes across Mombasa with "
        "verified details, honest photography, and support beyond the keys."
    ),
    "coast-property-co": (
        "Bamburi-based agency covering Mombasa's north coast — apartments, "
        "townhouses, and gated estates from Nyali to Shanzu."
    ),
    "pwani-realty": (
        "Diani team handling beachfront homes, cottages, and short-stay "
        "investments along Kwale's south coast."
    ),
    "highlands-estates": (
        "Ruiru specialists in Nairobi's metropolitan north — gated "
        "communities, townhouses, and family homes across Kiambu."
    ),
    "ngong-ridge-properties": (
        "Ngong Hills specialists — family homes, farms, and gated estates "
        "along Kajiado's rising ridge."
    ),
    "mombasa-bay-realty": (
        "Mtwapa agency covering the creek and north coast — sea-view "
        "apartments, villas, and holiday lets."
    ),
}


# (title_template, type_slug_plural, beds, baths, size_sqm, land_acres,
#  furnishing, base_sale_price, base_rent_monthly)
# land_acres and rent may be None. title_template uses {beds} and {area}.
LISTING_TEMPLATES = [
    ("{beds}BR Apartment in {area}",            "flats-apartments", 1, 1,   85, None,                "semi",        9_500_000,   65_000),
    ("{beds}BR Apartment in {area}",            "flats-apartments", 2, 2,  130, None,                "semi",       14_500_000,   95_000),
    ("{beds}BR Apartment in {area}",            "flats-apartments", 3, 2,  175, None,                "furnished",  22_000_000,  145_000),
    ("{beds}BR Maisonette in {area}",           "maisonettes",      4, 4,  280, Decimal("0.08"),     "unfurnished",28_000_000,  220_000),
    ("{beds}BR Townhouse in {area}",            "townhouses",       4, 5,  320, Decimal("0.12"),     "semi",       38_000_000,  280_000),
    ("{beds}BR Bungalow in {area}",             "bungalows",        3, 3,  210, Decimal("0.10"),     "unfurnished",26_000_000,  180_000),
    ("{beds}BR Villa with Pool in {area}",      "villas",           5, 6,  410, Decimal("0.25"),     "furnished",  75_000_000,  450_000),
    ("{beds}BR Family House in {area}",         "houses",           3, 3,  180, Decimal("0.13"),     "unfurnished",19_500_000,  130_000),
    ("Prime Plot in {area}",                    "land",             0, 0, None, Decimal("0.50"),     "unfurnished", 6_500_000,    None),
    ("Acreage Parcel in {area}",                "land",             0, 0, None, Decimal("2.50"),     "unfurnished",18_000_000,    None),
    ("Commercial Premises in {area}",           "commercial-property",0,2,220, None,                "unfurnished",45_000_000,  320_000),
    ("Office Suite in {area}",                  "offices",          0, 2,  160, None,                "unfurnished",18_000_000,  145_000),
    ("Retail Shop in {area}",                   "shops",            0, 1,   80, None,                "unfurnished",12_000_000,   95_000),
    ("Warehouse in {area}",                     "warehouses",       0, 2,  500, Decimal("0.30"),     "unfurnished",55_000_000,  380_000),
]


DESCRIPTION_TEMPLATE = (
    "A {beds_word} {type_name} in {area}, {county}. {extra}. "
    "Built to a high standard with careful attention to detail, this "
    "property is positioned to suit owner-occupiers and investors alike. "
    "Verified details, full disclosures, and end-to-end support from the "
    "Gabriel Homes team are included as standard. Contact the listing "
    "agent to arrange a viewing."
)


# ---------------------------------------------------------------------------
# Pillow cover-image generator
# ---------------------------------------------------------------------------
PALETTE = [
    ((175, 71, 21), (255, 248, 244)),   # burnt -> cream
    ((42, 33, 28),  (216, 201, 184)),   # espresso -> sand
    ((90, 64, 50),  (250, 248, 244)),   # brown -> cream
    ((166, 106, 77),(255, 248, 244)),   # clay -> cream
    ((138, 125, 112),(250, 248, 244)),  # taupe -> cream
]


def _cover_image(caption: str, w: int = 1280, h: int = 800) -> ContentFile:
    """Return a ContentFile holding a JPEG cover image with `caption` overlaid."""
    from PIL import ImageFont

    bg, fg = random.choice(PALETTE)
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Subtle diagonal gradient by overlaying translucent stripes.
    for i in range(0, h, 4):
        shade = int(255 * (i / h) * 0.08)
        draw.rectangle([(0, i), (w, i + 4)], fill=(
            max(0, bg[0] - shade),
            max(0, bg[1] - shade),
            max(0, bg[2] - shade),
        ))

    # Try to load a real font; fall back to the default if not available.
    font = None
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        try:
            font = ImageFont.truetype(path, 48)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Centre the caption text in two lines.
    lines = [caption[:50], caption[50:100]] if len(caption) > 50 else [caption]
    y = h // 2 - (len(lines) * 30)
    for line in lines:
        if not line:
            continue
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = len(line) * 28
        draw.text(((w - tw) // 2, y), line, fill=fg, font=font)
        y += 64

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return ContentFile(buf.getvalue(), name=f"{slugify(caption)[:60] or 'cover'}.jpg")


# ---------------------------------------------------------------------------
# Real-photo pool (bundled under MEDIA_ROOT/demo-photos/<pool>/) — generated
# by scripts/assign_demo_images.py. When present, seeded listings use real
# photography instead of the Pillow placeholder art.
# ---------------------------------------------------------------------------
DEMO_TYPE_POOL = {
    "flats-apartments": "apartment", "houses": "house", "townhouses": "house",
    "maisonettes": "house", "bungalows": "house", "villas": "house",
    "land": "land", "commercial-property": "office", "offices": "office",
    "shops": "shops", "warehouses": "warehouse",
}


def _demo_photo(caption: str, pool: str) -> ContentFile | None:
    """Return a ContentFile with a real demo photo, or None if the bundled
    demo-photos pool is not shipped (then callers fall back to Pillow art)."""
    base = Path(settings.MEDIA_ROOT) / "demo-photos" / pool
    files = sorted(base.glob("*.jpg")) if base.is_dir() else []
    if not files:
        return None
    digest = int(hashlib.md5(caption.encode("utf-8")).hexdigest(), 16)
    src = files[digest % len(files)]
    name = f"{slugify(caption)[:60] or 'photo'}.jpg"
    return ContentFile(src.read_bytes(), name=name)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seed Gabriel Homes with locations, types, amenities, agencies, ~80 listings."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--no-images", action="store_true",
                            help="Skip Pillow cover-image generation (faster).")
        parser.add_argument("--clear", action="store_true",
                            help="Delete all seeded data first (DESTRUCTIVE).")
        parser.add_argument("--target", type=int, default=80,
                            help="Target number of listings to seed (default 80).")
        parser.add_argument(
            "--i-know-this-is-demo",
            action="store_true",
            help="Explicit override required when DEBUG=False (C2: "
                 "production must never be seeded with fictional data).",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        # C2 — production starts empty. Fictional listings on a live site
        # would be a launch-killer; refuse unless explicitly overridden.
        if not settings.DEBUG and not opts["i_know_this_is_demo"]:
            raise SystemExit(
                "seed_demo: refusing to run — DEBUG is False. This command "
                "fills the site with FICTIONAL listings. Production starts "
                "empty; enter listings via the agent dashboard or admin. "
                "If you really mean it, pass --i-know-this-is-demo."
            )

        do_clear = opts["clear"]
        no_images = opts["no_images"]
        target = opts["target"]

        if do_clear:
            self._clear_all()
            self.stdout.write(self.style.WARNING("Cleared all seeded data."))

        loc_count = self._seed_locations()
        type_count = self._seed_property_types()
        amenity_count = self._seed_amenities()
        agency_count = self._seed_agencies()
        listing_count = self._seed_listings(target=target, with_images=not no_images)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone.\n"
            f"  Locations:      {loc_count}\n"
            f"  Property types: {type_count}\n"
            f"  Amenities:      {amenity_count}\n"
            f"  Agencies:       {agency_count}\n"
            f"  Listings:       {listing_count}\n"
            f"  Images:         {'skipped' if no_images else 'generated'}"
        ))

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------
    def _clear_all(self) -> None:
        PropertyImage.objects.all().delete()
        Property.objects.all().delete()
        Amenity.objects.all().delete()
        PropertyType.objects.all().delete()
        AgencyProfile.objects.all().delete()
        # Delete agency users too — they were created by this command.
        User.objects.filter(is_agent=True).delete()
        Location.objects.all().delete()

    # ------------------------------------------------------------------
    # Locations
    # ------------------------------------------------------------------
    def _seed_locations(self) -> int:
        created = 0
        for county_name, (lat, lng), areas in LOCATIONS:
            county, _ = Location.objects.get_or_create(
                parent=None,
                slug=slugify(county_name),
                defaults={
                    "name": county_name,
                    "level": Location.Level.COUNTY,
                    "lat": lat,
                    "lng": lng,
                },
            )
            for area_name, neighbourhoods in areas:
                area, _ = Location.objects.get_or_create(
                    parent=county,
                    slug=slugify(area_name),
                    defaults={"name": area_name, "level": Location.Level.AREA},
                )
                for n_name, n_lat, n_lng in neighbourhoods:
                    _, created_n = Location.objects.get_or_create(
                        parent=area,
                        slug=slugify(n_name),
                        defaults={
                            "name": n_name,
                            "level": Location.Level.NEIGHBOURHOOD,
                            "lat": n_lat,
                            "lng": n_lng,
                        },
                    )
                    if created_n:
                        created += 1
            created += 1 if county.pk else 0
        return Location.objects.count()

    # ------------------------------------------------------------------
    # Property types
    # ------------------------------------------------------------------
    def _seed_property_types(self) -> int:
        for name, plural, single, res, com, land, pos in PROPERTY_TYPES:
            PropertyType.objects.update_or_create(
                slug_plural=plural,
                defaults={
                    "name": name,
                    "slug_single": single,
                    "is_residential": res,
                    "is_commercial": com,
                    "is_land": land,
                    "position": pos,
                },
            )
        return PropertyType.objects.count()

    # ------------------------------------------------------------------
    # Amenities
    # ------------------------------------------------------------------
    def _seed_amenities(self) -> int:
        for name, icon, category in AMENITIES:
            Amenity.objects.update_or_create(
                slug=slugify(name),
                defaults={"name": name, "icon": icon, "category": category},
            )
        return Amenity.objects.count()

    # ------------------------------------------------------------------
    # Agencies (each gets a User + AgencyProfile)
    # ------------------------------------------------------------------
    def _seed_agencies(self) -> int:
        for name, email, phone, whatsapp, area_name in AGENCIES:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "phone": phone,
                    "is_agent": True,
                    "is_staff": True,
                },
            )
            if created:
                # Seeded agents get an UNUSABLE password so that
                # scripts/setup_accounts.py performs the one-and-only initial
                # password set (S4: seed never mints working credentials).
                user.set_unusable_password()
                user.save(update_fields=["password"])
            # Office location = the area itself, not a neighbourhood.
            office = Location.objects.filter(
                name__iexact=area_name, level=Location.Level.AREA
            ).first() or Location.objects.filter(
                name__iexact=area_name
            ).first()
            AgencyProfile.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    "user": user,
                    "name": name,
                    "phone": phone,
                    "whatsapp": whatsapp,
                    "email": email,
                    "website": f"https://{slugify(name).replace('-', '')}.co.ke",
                    "office_location": office,
                    "is_verified": True,
                    "bio": AGENCY_BIOS.get(
                        slugify(name),
                        f"{name} — a Gabriel Homes partner agency.",
                    ),
                },
            )
        return AgencyProfile.objects.count()

    # ------------------------------------------------------------------
    # Listings
    # ------------------------------------------------------------------
    def _seed_listings(self, target: int, with_images: bool) -> int:
        # Skip if listings already exist — idempotency.
        if Property.objects.exists():
            self.stdout.write("Listings already seeded; skipping generation.")
            return Property.objects.count()

        neighbourhoods = list(Location.objects.filter(level=Location.Level.NEIGHBOURHOOD))
        agencies = list(AgencyProfile.objects.all())
        amenities = list(Amenity.objects.all())
        if not (neighbourhoods and agencies and amenities):
            raise RuntimeError("Cannot seed listings — missing prerequisites.")

        type_map = {pt.slug_plural: pt for pt in PropertyType.objects.all()}

        made = 0
        attempts = 0
        # Cap attempts to avoid an infinite loop if target is set absurdly high.
        max_attempts = target * 5
        while made < target and attempts < max_attempts:
            attempts += 1
            template = random.choice(LISTING_TEMPLATES)
            (title_tmpl, type_slug, beds, baths, size_sqm,
             land_acres, furnishing, base_sale, base_rent) = template

            ptype = type_map.get(type_slug)
            if ptype is None:
                continue

            loc = random.choice(neighbourhoods)
            area_name = loc.parent.name if loc.parent else loc.name
            county_name = loc.get_ancestors()[0].name if loc.parent else loc.name

            # 60% sale, 40% rent
            is_sale = random.random() < 0.6
            listing_type = Property.ListingType.SALE if is_sale else Property.ListingType.RENT
            price_period = (Property.PricePeriod.TOTAL if is_sale
                            else Property.PricePeriod.MONTHLY)
            base = base_sale if is_sale else (base_rent or 0)
            if not base:
                # Template has no rent price — skip rent for this template.
                if not is_sale:
                    continue
            # Apply ±15% noise to the price.
            price = Decimal(base) * Decimal(str(random.uniform(0.85, 1.15))).quantize(Decimal("0.01"))
            # Round to a sensible step.
            step = 50_000 if price >= 5_000_000 else 5_000
            price = (price // step) * step

            title = title_tmpl.format(beds=beds or "", area=area_name)
            # Ensure uniqueness by suffixing a counter on collisions.
            base_slug = slugify(title)
            slug = base_slug
            i = made + 1
            while Property.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 5
            title = f"{title} #{made + 1:03d}"

            beds_word = "no-bedroom" if beds == 0 else f"{beds}-bedroom"
            extra_choices = [
                "Steps from the main road",
                "Quiet residential street",
                "Sea breeze in the afternoons",
                "Close to schools and shops",
                "Easy access to public transport",
                "Tucked away from the noise",
            ]
            description = DESCRIPTION_TEMPLATE.format(
                beds_word=beds_word,
                type_name=ptype.name.lower(),
                area=area_name,
                county=county_name,
                extra=random.choice(extra_choices),
            )

            property_obj = Property.objects.create(
                title=title,
                slug=slug,
                description=description,
                listing_type=listing_type,
                property_type=ptype,
                location=loc,
                lat=loc.lat,
                lng=loc.lng,
                price=price,
                price_period=price_period,
                price_negotiable=random.random() < 0.3,
                bedrooms=beds,
                bathrooms=baths,
                size_sqm=size_sqm,
                land_size_acres=land_acres,
                furnishing=furnishing,
                parking_spaces=random.randint(0, 3) if not ptype.is_land else 0,
                year_built=random.choice([None, None, 2015, 2018, 2020, 2022, 2024]),
                service_charge=Decimal("15000") if not is_sale and random.random() < 0.5 else None,
                # Round-robin assignment: every agency gets its own
                # DISJOINT set of listings (no agent doubles up on another
                # agent's listing), and the spread stays even as `made`
                # grows.
                agent=agencies[made % len(agencies)],
                status=Property.Status.PUBLISHED,
                is_featured=random.random() < 0.15,
                is_verified=random.random() < 0.6,
            )

            # Attach 2-4 random amenities.
            picked = random.sample(amenities, k=random.randint(2, 4))
            property_obj.amenities.set(picked)

            # Cover image (real demo photo when bundled, else Pillow art)
            if with_images:
                pool = DEMO_TYPE_POOL.get(ptype.slug_plural, "house")
                cover = _demo_photo(title, pool) or _cover_image(title)
                PropertyImage.objects.create(
                    property=property_obj,
                    image=cover,
                    caption=title,
                    position=0,
                    is_cover=True,
                )
                # Optionally add a second non-cover image
                if random.random() < 0.4:
                    extra_img = (_demo_photo(f"{title} — interior", "interior")
                                 or _cover_image(f"{title} — interior"))
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=extra_img,
                        caption=f"{title} — interior",
                        position=1,
                        is_cover=False,
                    )

            made += 1

        return Property.objects.count()
