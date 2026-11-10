"""Setup Checklist service (P2-2) — the owner's to-do list, kept honest.

Every item is either:

* **derived** — the site verifies it itself from the database/settings
  each time the home screen renders. The owner can never tick these by
  hand, so the checklist cannot drift from reality.
* **manual** — only the owner can decide it (e.g. "the About page tells
  my story right"). State lives in ChecklistItemState rows.

The FIRST open item in registry order is "the exact next step" shown in
the home banner (protocol §5 module 1). Registry order = blocking-first:
contact details and demo-data honesty gate the launch, listings feed it,
email delivery and page reviews follow.

Plain-language copy only; no invented facts — an item that needs a
portal screen that does not exist yet says so instead of pretending.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from apps.core.models import BrandSettings, SiteSetting
from apps.inquiries.models import Inquiry
from apps.listings.models import Property

from .models import ChecklistItemState


@dataclass(frozen=True)
class ChecklistItem:
    """One checklist entry: copy + how its done-state is decided."""

    key: str
    label: str          # short plain-language title
    help: str           # inline help text (protocol §5: inline help)
    action: str         # the exact next step, shown in the banner
    url: str = ""       # optional public page the step opens
    derived: bool = False

    def is_done(self, states: dict[str, ChecklistItemState]) -> bool:
        if self.derived:
            return DERIVED_PREDICATES[self.key]()
        state = states.get(self.key)
        return bool(state and state.done)


# ---------- derived predicates (all DB/settings facts, nothing invented) ----------

def _contact_done() -> bool:
    """At least one public contact channel exists (BrandSettings, P1-2)."""
    brand = BrandSettings.load()
    return any((brand.phone, brand.whatsapp, brand.email))


def _hide_demo_done() -> bool:
    """Demo rows hidden site-wide, or none left to hide."""
    if SiteSetting.demo_hidden():
        return True
    return not Property.objects.filter(is_demo=True).exists()


def _real_listings_done() -> bool:
    """At least one published listing that is NOT seeded demo data."""
    return Property.objects.filter(
        status=Property.Status.PUBLISHED, is_demo=False
    ).exists()


def _owner_email_done() -> bool:
    """Enquiry notification emails have a destination (P1-4 OWNER_EMAIL)."""
    return bool((getattr(settings, "OWNER_EMAIL", "") or "").strip())


DERIVED_PREDICATES = {
    "contact": _contact_done,
    "hide_demo": _hide_demo_done,
    "real_listings": _real_listings_done,
    "owner_email": _owner_email_done,
}

MANUAL_KEYS = frozenset({"about_story", "founder_name"})

REGISTRY: tuple[ChecklistItem, ...] = (
    ChecklistItem(
        key="contact",
        derived=True,
        label="Add your contact details",
        help=(
            "Buyers and renters reach you by phone, WhatsApp or email. "
            "Add at least one so no enquiry goes cold."
        ),
        action=(
            "Send Brian the phone / WhatsApp / email you want published — "
            "the Brand editor inside this portal is coming soon."
        ),
    ),
    ChecklistItem(
        key="hide_demo",
        derived=True,
        label="Hide the sample listings",
        help=(
            "The site currently shows sample homes so it doesn't look empty. "
            "Before you go live they must be hidden from visitors."
        ),
        action=(
            "Ask Brian to switch on \u201chide demo data\u201d — a one-tap switch "
            "for it is coming to this portal."
        ),
    ),
    ChecklistItem(
        key="real_listings",
        derived=True,
        label="Publish your first real listing",
        help=(
            "A listing is live when it has photos, a price and a location, "
            "and its status is Published. Sample homes don't count."
        ),
        action=(
            "Send Brian your first real property (photos, price, location) — "
            "the step-by-step listing wizard is coming soon."
        ),
    ),
    ChecklistItem(
        key="owner_email",
        derived=True,
        label="Make sure enquiries reach your inbox",
        help=(
            "Every enquiry is saved in this portal and also emailed to you. "
            "Choose the address those emails should go to."
        ),
        action=(
            "Tell Brian which email address should receive enquiry alerts "
            "(he sets it once in the site settings)."
        ),
    ),
    ChecklistItem(
        key="about_story",
        label="Read your About page",
        help=(
            "Read it once and check the story, services and wording feel "
            "right to you. Tick this when it does."
        ),
        action="Open the About page, read it, then tick this item done.",
        url="/about/",
    ),
    ChecklistItem(
        key="founder_name",
        label="Check your name is spelled right",
        help=(
            "The site shows the founder name from the original brief. "
            "Confirm the spelling is yours before launch."
        ),
        action="Open the About page, check the spelling, then tick this done.",
        url="/about/",
    ),
)

# Registry order is the "next step" priority. Asserted in tests so a
# future edit can't silently reorder the owner's priorities.
REGISTRY_KEYS = tuple(item.key for item in REGISTRY)


def build_checklist() -> dict:
    """Render-shape snapshot: items, completion % and the exact next step."""
    states = {s.key: s for s in ChecklistItemState.objects.all()}
    items = []
    for spec in REGISTRY:
        items.append(
            {
                "spec": spec,
                "done": spec.is_done(states),
                "manual": not spec.derived,
            }
        )
    done_count = sum(1 for i in items if i["done"])
    total = len(items)
    percent = round(done_count * 100 / total) if total else 100
    next_item = next((i for i in items if not i["done"]), None)
    return {
        "items": items,
        "done_count": done_count,
        "total": total,
        "percent": percent,
        "next": next_item,
        "all_done": next_item is None,
    }


def counts() -> dict:
    """Owner-facing numbers, all computed from the database.

    * new_enquiries — status New, spam-flagged rows excluded (the spam
      folder arrives with P3-6; until then flagged rows are not shown
      as enquiries anywhere).
    * live_listings — exactly what the public site can see right now
      (the published() chokepoint, demo switch included).
    * drafts — the owner's unfinished work (dashboards see everything).
    """
    return {
        "new_enquiries": Inquiry.objects.filter(
            status=Inquiry.Status.NEW, honeypot=""
        ).count(),
        "live_listings": Property.objects.published().count(),
        "drafts": Property.objects.filter(status=Property.Status.DRAFT).count(),
    }
