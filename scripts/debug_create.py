"""Debug the dashboard listing-create POST with the exact functional-test data."""
import os
import sys

sys.path.insert(0, "/home/z/my-project/gabriel_homes")
os.chdir("/home/z/my-project/gabriel_homes")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django

django.setup()

from django.test import Client

from apps.accounts.models import User
from apps.listings.models import Amenity, Property, PropertyType
from apps.locations.models import Location

u = User.objects.filter(is_agent=True).first()
c = Client()
c.force_login(u)

loc = Location.objects.filter(level="neighbourhood").first()
pt = PropertyType.objects.filter(slug_plural="flats-apartments").first()
am = Amenity.objects.first()
print(f"agent={u.email} loc={loc and loc.pk} pt={pt and pt.pk} am={am and am.pk}")

data = {
    "title": "Agent Test Apartment Nyali",
    "listing_type": "sale",
    "property_type": pt.pk,
    "location": loc.pk,
    "price": "12500000",
    "price_period": "total",
    "bedrooms": "3",
    "bathrooms": "2",
    "furnishing": "unfurnished",
    "status": "published",
    "description": "A test listing created by the E2E functional test.",
    "amenities": am.pk,
}
r = c.post("/dashboard/listings/new/", data)
print("status:", r.status_code)
print("template:", getattr(r, "template_name", None))
if hasattr(r, "context") and r.context:
    try:
        print("context keys:", list(r.context[0].keys()) if isinstance(r.context, list) else list(r.context.keys()))
    except Exception as e:
        print("context inspect failed:", e)
    form = (r.context[0] if isinstance(r.context, list) else r.context).get("form")
    if form is not None:
        print("form.errors:", dict(form.errors))
from django.contrib.messages import get_messages
w = get_messages(c)
print("messages:", [m.message for m in w])
exists = Property.objects.filter(title="Agent Test Apartment Nyali").exists()
print("created:", exists)
