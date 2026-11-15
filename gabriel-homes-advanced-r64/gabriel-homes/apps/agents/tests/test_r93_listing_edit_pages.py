"""r93 — listings edit pages: regression tests written RED first.

Why: the owner called the listings edit experience "horrible". The audit
found one data bug and two layout defects on the pages the listings row's
Edit link leads to (/dashboard/listings/<pk>/edit/), plus the portal
wizard/listings screens that share the same CSS:

1. DATA BUG — the dashboard editor's amenities field rendered as a
   SelectMultiple (auto ModelForm widget), but the template iterated it
   as checkbox subwidgets. Each iteration emitted an orphan <option>
   tag next to the label ("Lift Lift"), and because no <select> wrapper
   existed the POST carried no amenities key — so every "Save changes"
   on a listing with amenities silently cleared them. Pinned by
   test_edit_preserves_amenities / test_editor_amenities_render_as_checkboxes.

2. MARKETING CHROME — the dashboard editor (and create/images pages via
   base.html) shipped the public site's marketing header and giant
   footer on a backend screen. Pinned by test_editor_has_no_marketing_footer
   / test_editor_has_no_marketing_header.

3. NATIVE SELECTS — manage.css styled .manage-field input/textarea but
   forgot <select>, so 4 of 6 controls on wizard step 1 were raw OS
   dropdowns (computed style: rgb(239,239,239) / 0px radius). Pinned by
   test_manage_css_styles_selects.

4. RUNAWAY WIDTH — .dashboard-form had no max-width, so on a 1440px
   desktop the inputs stretched ~1000px wide. Pinned by
   test_dashboard_form_has_width_cap.

5. The form's land/service fields rendered as bare visible inputs
   ("two empty unlabeled text inputs" in the visual audit) instead of
   staying hidden. Pinned by test_editor_hidden_fields_render_hidden.
"""
import re
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client

from apps.listings.models import Amenity, Property

REPO = Path(__file__).resolve().parents[3]
MANAGE_CSS = REPO / "static" / "css" / "manage.css"
DASH_CSS = REPO / "static" / "css" / "dashboard.css"


@pytest.fixture
def seeded(db):
    """Same seed the suite's dashboard tests use (agencies, users,
    listings, amenities) so the editor has real data to edit."""
    call_command(
        "seed_demo", no_images=True, target=20, verbosity=0,
        i_know_this_is_demo=True,
    )
    return db


def _editor_client_and_listing(seeded):
    """Owner client + a listing with amenities (superuser may edit any)."""
    owner = get_user_model().objects.create_superuser(
        email="r93-edit@example.com", password="r93-pass-123"
    )
    c = Client()
    c.force_login(owner)
    p = Property.objects.exclude(agent__isnull=True).first()
    assert p is not None, "seed must produce at least one listing"
    if not p.amenities.exists():
        p.amenities.set(Amenity.objects.order_by("pk")[:2])
    from apps.agents.tests.test_dashboard import _valid_listing_data

    return c, p, _valid_listing_data()


# ---------------------------------------------------------------------------
# 1. The amenities data bug on the dashboard editor
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("seeded")
def test_edit_preserves_amenities():
    """Saving the editor without touching amenities must not wipe them.

    RED against r92: the template rendered the SelectMultiple's options
    as orphan tags, so POST data had no amenities key → cleared.
    """
    c, p, data = _editor_client_and_listing(seeded="used")
    before = list(p.amenities.values_list("pk", flat=True))
    assert before  # the bug only bites listings that HAVE amenities
    # Post the listing's OWN amenities back (an owner who edits only the
    # title still submits the unchanged checkbox state).
    data["amenities"] = [str(pk) for pk in before]
    r = c.post(f"/dashboard/listings/{p.pk}/edit/", data)
    assert r.status_code == 302, getattr(r.context, "form", None) and r.context["form"].errors
    p.refresh_from_db()
    assert list(p.amenities.values_list("pk", flat=True)) == before


@pytest.mark.usefixtures("seeded")
def test_editor_amenities_render_as_checkboxes():
    """GET must render real checkbox inputs, not orphan <option> tags."""
    c, p, _ = _editor_client_and_listing(seeded="used")
    r = c.get(f"/dashboard/listings/{p.pk}/edit/")
    html = r.content.decode()
    boxes = re.findall(r'<input[^>]*type="checkbox"[^>]*name="amenities"', html)
    if not boxes:
        # Django renders name before type — cover both attribute orders.
        boxes = re.findall(r'<input[^>]*name="amenities"[^>]*type="checkbox"', html)
    assert len(boxes) >= 1, "amenities should render as named checkboxes"
    # Orphan <option> tags *inside the amenities block* are the r92 bug's
    # mark (the plain <select> dropdowns elsewhere on the page are legit).
    m = re.search(
        r'class="dashboard-form__checkboxes".*?</div>', html, re.S
    )
    assert m, "amenities checkbox container must render"
    assert "<option" not in m.group(0), "no orphan <option> tags inside amenities"


# ---------------------------------------------------------------------------
# 2. Marketing chrome on backend screens
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("seeded")
def test_editor_has_no_marketing_footer():
    """Backend editor must not ship the public site's marketing footer."""
    c, p, _ = _editor_client_and_listing(seeded="used")
    r = c.get(f"/dashboard/listings/{p.pk}/edit/")
    html = r.content.decode()
    assert "<footer" not in html and 'class="site-footer' not in html


@pytest.mark.usefixtures("seeded")
def test_editor_has_no_marketing_header():
    """The public navbar (Homes Buy / Rent / …) must not render either."""
    c, p, _ = _editor_client_and_listing(seeded="used")
    r = c.get(f"/dashboard/listings/{p.pk}/edit/")
    html = r.content.decode()
    assert 'id="site-header"' not in html and 'class="site-nav' not in html


# ---------------------------------------------------------------------------
# 3. Portal selects were unstyled (wizard + every .manage-field form)
# ---------------------------------------------------------------------------
def test_manage_css_styles_selects():
    """The portal field styles must cover <select>, not just input/textarea.

    RED against r92: the shared control rule listed only input/textarea.
    """
    css = MANAGE_CSS.read_text()
    m = re.search(r"\.manage-field input,\s*\n\.manage-field select,", css)
    assert m, "the shared .manage-field control rule must list select explicitly"


def test_dashboard_css_selects_are_styled():
    """dashboard.css already styled selects; pin it so it stays true."""
    css = DASH_CSS.read_text()
    assert ".dashboard-form__select" in css


# ---------------------------------------------------------------------------
# 4. Form width sanity on the editor
# ---------------------------------------------------------------------------
def test_dashboard_form_has_width_cap():
    """The editor form must be capped so inputs don't span ~1000px."""
    css = DASH_CSS.read_text()
    m = re.search(r"\.dashboard-form\s*\{[^}]*max-width", css, re.S)
    assert m, ".dashboard-form must carry a max-width cap"


# ---------------------------------------------------------------------------
# 5. Hidden fields stay hidden
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("seeded")
def test_editor_hidden_fields_render_hidden():
    c, p, _ = _editor_client_and_listing(seeded="used")
    r = c.get(f"/dashboard/listings/{p.pk}/edit/")
    html = r.content.decode()
    for name in ("land_size_acres", "service_charge"):
        m = re.search(rf'<input[^>]*name="{name}"[^>]*>', html)
        assert m, f"{name} must render as an input"
        assert 'type="hidden"' in m.group(0), f"{name} must be type=hidden"


# ---------------------------------------------------------------------------
# 6. Wizard: portal step 1 selects sit inside the styled .manage-field scope
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_wizard_basics_selects_present():
    User = get_user_model()
    owner = User.objects.create_superuser(
        email="r93-wiz@example.com", password="r93-pass-123"
    )
    c = Client()
    c.force_login(owner)
    r = c.get("/manage/listings/new/")
    html = r.content.decode()
    assert html.count("<select") >= 3, "step 1 renders 3-4 selects"
    for sel in re.findall(r"<select[^>]*>", html):
        idx = html.find(sel)
        field_open = html.rfind('<div class="manage-field', 0, idx)
        assert field_open != -1, "select must live inside .manage-field"
        field_close = html.find("</div>", idx)
        assert field_open < idx < field_close
