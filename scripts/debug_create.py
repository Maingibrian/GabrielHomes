"""Debug the dashboard listing-create rejection with exact form errors."""
import os, sys, django
sys.path.insert(0, "/home/z/my-project/gabriel_homes")
os.chdir("/home/z/my-project/gabriel_homes")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.test import Client
from apps.accounts.models import User

u = User.objects.filter(is_agent=True).first()
u.set_password("TestPass123!")
u.save()

c = Client()
assert c.login(email=u.email, password="TestPass123!"), "login failed"

from apps.locations.models import Location
from apps.listings.models import PropertyType, Amenity
loc = Location.objects.filter(level="neighbourhood").first()
pt = PropertyType.objects.filter(slug_plural="flats-apartments").first()
am = Amenity.objects.first()

data = {
    "title": "Agent Test Apartment Nyali",
    "listing_type": "sale",
    "property_type": pt.pk,
    "location": loc.pk,
    "price": "12500000",
    "price_period": "total",
    "bedrooms": "3",
    "bathrooms": "2",
    "parking_spaces": "0",
    "furnishing": "unfurnished",
    "status": "published",
    "description": "A test listing created by the E2E functional test.",
    "amenities": [am.pk],
}
r = c.post("/dashboard/listings/new/", data, follow=True)
print("status:", r.status_code)
from apps.listings.models import Property
p = Property.objects.filter(title="Agent Test Apartment Nyali").first()
print("created:", p.pk if p else False)
if p:
    print("public visible:", Property.objects.published().filter(pk=p.pk).exists())
    print("url:", p.get_absolute_url())
    # cleanup for repeat runs
    p.delete()
    print("cleaned up")
