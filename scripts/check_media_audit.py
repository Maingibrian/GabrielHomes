"""Read-only audit check: do seeded listings actually have images? (audit-19)"""
import os
import sys

import django

sys.path.insert(0, "/home/z/my-project/gabriel_homes")

for mod in ("config.settings.dev", "config.settings.base", "config.settings"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", mod)
    try:
        django.setup()
        break
    except Exception:
        os.environ.pop("DJANGO_SETTINGS_MODULE", None)

from django.conf import settings  # noqa: E402
from apps.listings.models import Property, PropertyImage  # noqa: E402

total = Property.objects.count()
img_rows = PropertyImage.objects.count()
with_img = Property.objects.filter(images__isnull=False).distinct().count()
print(f"properties={total} propertyimage_rows={img_rows} properties_with_images={with_img}")
print("MEDIA_ROOT:", settings.MEDIA_ROOT)

for pi in PropertyImage.objects.select_related("property")[:3]:
    ok = pi.image.storage.exists(pi.image.name)
    print("sample row:", pi.image.name, "file_exists=", ok)

media_root = settings.MEDIA_ROOT
n_files = 0
for _root, _dirs, files in os.walk(str(media_root)):
    n_files += len(files)
print("files under MEDIA_ROOT:", n_files)
