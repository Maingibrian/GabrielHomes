#!/usr/bin/env python3
"""assign_demo_images.py — transform Gabriel Homes from placeholder art to
real photography.

1. Crop stock-photo watermark strips off the bottom of flagged images.
2. Build curated pools (house/apartment/shops/warehouse/office/land/interior).
3. Overwrite each PropertyImage file IN PLACE (filenames stay => DB intact):
   cover <- exterior pool by property type, 2nd image <- interior pool.
4. Set agency portraits (Django AgencyProfile.logo).
5. Replace static hero + add CTA bg + founder portrait.
6. Save the processed pools to media/demo-photos/ so future `seed_demo`
   runs can use real photos offline (fallback: old Pillow art).
"""
import os, sys, hashlib, shutil
from PIL import Image

PROJ = "/home/z/my-project/gabriel_homes"
LIB = "/home/z/my-project/scripts/design-audit/photo-library"
POOL_DIR = f"{PROJ}/media/demo-photos"

# --- curation -------------------------------------------------------------
# files with a watermark band at the bottom -> crop this % off the bottom
CROP_BOTTOM = {
    "beachhouse-03": 0.16, "apartment-01": 0.16, "apartment2-01": 0.16,
    "apartment2-02": 0.16, "apartment2-03": 0.18, "apartment2-04": 0.16,
    "apartment2-05": 0.16, "living-02": 0.14, "living-06": 0.14,
    "bedroom-02": 0.14, "bedroom-03": 0.16, "garden-02": 0.16,
    "garden-03": 0.14, "garden-04": 0.16, "men-02": 0.16, "men-04": 0.16,
    "men-05": 0.16, "women-01": 0.16, "women-02": 0.16, "women-03": 0.16,
    "women-05": 0.16, "coast-02": 0.14, "coast-04": 0.14,
    "warehouse-03": 0.16, "townhouse-02": 0.22, "coast-01": 0.18,
}
SKIP = {"shops-02", "shops-03", "shops-06", "city-02", "coast-01",
        "shops-05", "city-02"}  # off-topic / unusable content

POOLS = {
    "house":     ["villa-01", "villa-02", "villa-03", "villa-04", "villa-05",
                  "villa-06", "beachhouse-01", "beachhouse-02", "beachhouse-04",
                  "beachhouse-05", "townhouse-01", "townhouse-03", "townhouse-04"],
    "apartment": ["apartment-01", "apartment-02", "apartment-03", "apartment-04",
                  "apartment-05", "apartment2-01", "apartment2-03",
                  "apartment2-05", "apartment2-06"],
    "shops":     ["shops-01", "shops-04"],
    "warehouse": ["warehouse-01", "warehouse-02", "warehouse-03",
                  "warehouse-04", "warehouse-05"],
    "office":    ["officebld-01", "officebld-02", "officebld-03",
                  "officebld-05", "office-01", "office-02"],
    "land":      ["garden-01", "garden-02", "garden-04"],
    "interior":  ["living-01", "living-02", "living-03", "living-04",
                  "living-05", "kitchen-01", "kitchen-02",
                  "kitchen-03", "kitchen-04", "bedroom-01", "bedroom-03",
                  "bedroom-04", "office-01", "office-02"],
}
# 6 verified-clean portraits, order maps to agencies A..F.
# (men-01/women-02/women-03 rejected: tiled diagonal watermarks.)
PORTRAITS = ["men2-01", "men-03", "men-05", "men-06", "women-04", "women2-03"]
FOUNDER = "men-03"
HERO, CTA = "villa-01", "coast-05"

TYPE_POOL = {
    "flats-apartments": "apartment", "houses": "house", "townhouses": "house",
    "maisonettes": "house", "bungalows": "house", "villas": "house",
    "land": "land", "commercial-property": "office", "offices": "office",
    "shops": "shops", "warehouses": "warehouse",
}

def stable_pick(seed: str, pool: list, offset: int = 0):
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return pool[(h + offset) % len(pool)]

def load(name: str) -> Image.Image:
    im = Image.open(f"{LIB}/{name}.jpg")
    im = im.convert("RGB")
    crop = CROP_BOTTOM.get(name)
    if crop:
        w, h = im.size
        im = im.crop((0, 0, w, int(h * (1 - crop))))
    return im

def center_crop_ar(im: Image.Image, ar: float) -> Image.Image:
    w, h = im.size
    target = w / h
    if target > ar:                      # too wide -> trim sides
        nw = int(h * ar)
        x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:                                # too tall -> trim top/bottom
        nh = int(w / ar)
        y = (h - nh) // 2
        im = im.crop((0, y, w, y + nh))
    return im

def cover_bytes(name: str, max_w=1200, q=80):
    im = load(name)
    im = center_crop_ar(im, 4 / 3)
    if im.size[0] > max_w:
        im = im.resize((max_w, int(im.size[1] * max_w / im.size[0])), Image.LANCZOS)
    return _jpeg(im, q)

def portrait_bytes(name: str, max_w=900, q=84):
    im = load(name)
    im = center_crop_ar(im, 4 / 5)
    if im.size[0] > max_w:
        im = im.resize((max_w, int(im.size[1] * max_w / im.size[0])), Image.LANCZOS)
    return _jpeg(im, q)

def wide_bytes(name: str, ar=16 / 9, max_w=1920, q=82):
    im = load(name)
    im = center_crop_ar(im, ar)
    if im.size[0] > max_w:
        im = im.resize((max_w, int(im.size[1] * max_w / im.size[0])), Image.LANCZOS)
    return _jpeg(im, q)

def _jpeg(im: Image.Image, q: int) -> bytes:
    import io
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=q, optimize=True)
    return buf.getvalue()

# ---------------------------------------------------------------------------
# 1+6. Process pools once, save to media/demo-photos/ for seed_demo reuse
# ---------------------------------------------------------------------------
os.makedirs(POOL_DIR, exist_ok=True)
pool_paths = {}   # pool -> [file paths]
for pool, names in POOLS.items():
    pool_paths[pool] = []
    pdir = f"{POOL_DIR}/{pool}"
    os.makedirs(pdir, exist_ok=True)
    for i, n in enumerate(names, 1):
        data = cover_bytes(n, max_w=1000, q=76)
        dest = f"{pdir}/{pool}-{i:02d}.jpg"
        open(dest, "wb").write(data)
        pool_paths[pool].append(dest)
        print(f"  pool {pool}-{i:02d}  <- {n}  ({len(data)//1024} KB)")

pdir = f"{POOL_DIR}/portraits"
os.makedirs(pdir, exist_ok=True)
portrait_files = []
for i, n in enumerate(PORTRAITS, 1):
    dest = f"{pdir}/portrait-{i:02d}.jpg"
    open(dest, "wb").write(portrait_bytes(n, max_w=800, q=80))
    portrait_files.append(dest)

# ---------------------------------------------------------------------------
# 2. Static hero / CTA / founder
# ---------------------------------------------------------------------------
open(f"{PROJ}/static/img/hero-bg.jpg", "wb").write(wide_bytes(HERO, ar=16/9, q=82))
open(f"{PROJ}/static/img/cta-bg.jpg", "wb").write(wide_bytes(CTA, ar=21/9, max_w=1920, q=80))
open(f"{PROJ}/static/img/founder.jpg", "wb").write(portrait_bytes(FOUNDER, max_w=960, q=85))
print("hero / cta / founder written")

# ---------------------------------------------------------------------------
# 3. Assign to Properties (Django) — overwrite image files in place
# ---------------------------------------------------------------------------
sys.path.insert(0, PROJ)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
django.setup()
from apps.listings.models import Property, PropertyImage
from apps.agents.models import AgencyProfile
from django.core.files.base import ContentFile

n_cov = n_int = 0
for p in Property.objects.select_related("property_type").prefetch_related("images").all():
    pool_key = TYPE_POOL.get(p.property_type.slug_plural, "house")
    images = list(p.images.all())
    for idx, img in enumerate(images):
        if idx == 0 or getattr(img, "is_cover", False):
            src = pool_paths[pool_key][
                int(hashlib.md5(p.slug.encode()).hexdigest(), 16) % len(pool_paths[pool_key])]
        else:
            src = pool_paths["interior"][
                (int(hashlib.md5(p.slug.encode()).hexdigest(), 16) + idx) % len(pool_paths["interior"])]
        path = img.image.path
        if os.path.exists(path):
            shutil.copyfile(src, path)
            if idx == 0 or getattr(img, "is_cover", False):
                n_cov += 1
            else:
                n_int += 1
print(f"covers overwritten: {n_cov}, interiors: {n_int}")

# ---------------------------------------------------------------------------
# 4. Agency portraits
# ---------------------------------------------------------------------------
for i, agency in enumerate(AgencyProfile.objects.all()):
    src = portrait_files[i % len(portrait_files)]
    name = f"{agency.slug or agency.name}-portrait.jpg"
    agency.logo.save(name, ContentFile(open(src, "rb").read()), save=True)
    print(f"  agency portrait: {agency.name} -> {agency.logo.name}")
print("agencies: DONE")
print("ALL IMAGES ASSIGNED")
