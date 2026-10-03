"""Standalone validation of the dashboard listing form fields."""
import os
import sys

sys.path.insert(0, "/home/z/my-project/gabriel_homes")
os.chdir("/home/z/my-project/gabriel_homes")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django

django.setup()

from django import forms

from apps.listings.models import Amenity, Property, PropertyType
from apps.locations.models import Location

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
    "furnishing": "unfurnished",
    "status": "published",
    "description": "A test listing created by the E2E functional test.",
    "amenities": am.pk,
}

FIELDS = [
    "title", "listing_type", "property_type", "location",
    "address_text", "lat", "lng",
    "price", "price_period", "price_negotiable",
    "bedrooms", "bathrooms", "size_sqm", "land_size_acres",
    "furnishing", "parking_spaces", "year_built", "service_charge",
    "amenities", "status", "is_featured", "description",
]


class F(forms.ModelForm):
    class Meta:
        model = Property
        fields = FIELDS


f = F(data=data)
print("is_valid:", f.is_valid())
print("errors:", dict(f.errors))

# Also try the exact live route with test client but inspect via view instance
from django.test import Client
from apps.accounts.models import User

u = User.objects.filter(is_agent=True).first()
c = Client()
c.force_login(u)
r = c.post("/dashboard/listings/new/", data)
print("view status:", r.status_code)
try:
    ctx = r.context
    if ctx:
        d = ctx[0] if isinstance(ctx, list) else ctx
        form = d.get("form")
        print("view form.errors:", dict(form.errors) if form else "no form in ctx")
        print("view is_create:", d.get("is_create"))
except Exception as e:
    print("ctx err:", e)
