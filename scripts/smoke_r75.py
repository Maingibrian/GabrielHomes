"""Quick live smoke of the r75 Phase 3 screens (scratch script)."""
import os
import sys

sys.path.insert(0, "/home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django

django.setup()

from django.test import Client
from apps.accounts.models import User

User.objects.filter(email="owner@test.com").delete()
owner = User.objects.create_superuser(email="owner@test.com", password="owner-pass-123")
c = Client()
c.force_login(owner)

for url in [
    "/manage/site-content/categories/",
    "/manage/site-content/media/",
    "/manage/site-content/media/?filter=covers",
    "/manage/site-content/media/?q=villa",
    "/manage/site-content/testimonials/",
    "/manage/site-content/newsletter/",
    "/",
]:
    r = c.get(url)
    print(f"{r.status_code}  {url}")

# POST smoke: add a testimonial with consent, check home shows the band
r = c.post("/manage/site-content/testimonials/", {
    "name": "Amina K.", "role": "Bought an apartment in Nyali",
    "quote": "Gabriel found us the sea-view flat we'd given up on.",
    "rating": "5", "consent_given": "on",
})
print("add testimonial ->", r.status_code)
r = c.get("/")
print("home with quote band:", b"quote-card" in r.content and b"Amina K." in r.content)

# preview the newsletter
from apps.listings.models import Property
pks = list(Property.objects.published().order_by("-published_at").values_list("pk", flat=True)[:3])
r = c.post("/manage/site-content/newsletter/", {"action": "preview", "listings": [str(p) for p in pks]})
print("newsletter preview ->", r.status_code, "preview box" if b"manage-preview__box" in r.content else "NO PREVIEW")
