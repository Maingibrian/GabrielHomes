"""L4 — detail gallery proving tests.

Runbook §6 L4 / SCORECARD L4: read detail-gallery.js FIRST and extend it
(no rewrite — the S10/v2 slider keeps its crossfade, thumbnail ring,
counter bump, touch swipe and keyboard arrows), then add:

  * a lightbox (click-to-zoom photo viewer) with role="dialog",
    aria-modal, a real focus trap (Tab / Shift+Tab cycle inside the
    dialog), Escape to close, arrows to navigate, and focus restored
    to the opener on close;
  * the shared-element transition wiring of G2: the per-listing
    view-transition-name stays on the gallery main (the detail-side
    half of the G2 pair), and the lightbox overlay never carries a
    name — the page-wide name stays unique (D-LOOP-32a);
  * a JS-injected "Enlarge photo" control: with JS blocked there is no
    dead control and the gallery remains the full content surface
    (Q3/D-MOTION-SAFE), and the scroll lock releases Lenis through the
    F5 public API (window.__lenis.stop()/start()) without touching the
    MET-frozen smooth-scroll.js.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test (same isolation as test_g2_view_transitions),
    then attach a small generated image to every published property so the
    gallery renders with thumbnails and the detail name sits on a real
    photo surface."""
    from django.core.cache import cache
    cache.clear()
    call_command("seed_demo", no_images=True, target=20, verbosity=0,
                 i_know_this_is_demo=True)
    _attach_tiny_images()
    yield
    cache.clear()


def _attach_tiny_images():
    """Generate a 760x520 JPEG in-memory per published property (PIL, local,
    no network — mirrors the G2 fixture)."""
    import io

    from django.core.files.base import File
    from PIL import Image as PILImage

    from apps.listings.models import Property, PropertyImage
    for p in Property.objects.published():
        buf = io.BytesIO()
        PILImage.new("RGB", (760, 520), (196, 178, 158)).save(buf, "JPEG")
        buf.seek(0)
        PropertyImage.objects.create(
            property=p, image=File(buf, name=f"l4-fix-{p.pk}.jpg"))


REPO = Path(__file__).resolve().parents[3]
JS = (REPO / "static" / "js" / "detail-gallery.js").read_text()
CSS = (REPO / "static" / "css" / "detail.css").read_text()
TPL = (REPO / "templates" / "listings" / "detail.html").read_text()


def l4_css() -> str:
    """The L4 block appended to detail.css (from its banner to EOF)."""
    marker = "L4 — gallery lightbox"
    idx = CSS.index(marker)
    return CSS[idx:]


# ---------------------------------------------------------------------------
# 1. extend-not-rewrite: the S10/v2 feature set survives intact
# ---------------------------------------------------------------------------
def test_existing_gallery_features_survive():
    for token in (
        "gallery__fade",        # crossfade layer (M2)
        "is-entering",          # fade transition class
        "is-bumping",           # counter micro-animation (M5)
        "touchstart",           # touch swipe (mobile)
        "ArrowLeft",            # original keyboard navigation
        "ArrowRight",
        "is-active",            # active thumbnail ring
        "strip.scrollTo",       # thumbnail auto-centering
    ):
        assert token in JS, f"original gallery feature lost: {token}"


# ---------------------------------------------------------------------------
# 2. the lightbox is built by JS only (no dead markup without JS)
# ---------------------------------------------------------------------------
def test_lightbox_is_built_by_js_only():
    assert "createElement('div')" in JS
    assert "className = 'lightbox'" in JS
    assert 'setAttribute(\'role\', \'dialog\')' in JS
    assert "'aria-modal', 'true'" in JS
    # The template itself must NOT ship lightbox markup.
    assert "lightbox" not in TPL, "lightbox DOM must be JS-built, not in the template"


def test_expand_control_is_js_only_and_labelled():
    assert "gallery__expand" in JS
    assert "'Enlarge photo'" in JS
    assert "gallery__expand" not in TPL, "expand control must be JS-injected"
    assert "gallery__expand" in CSS, "expand control must be styled in detail.css"


def test_single_image_listings_get_the_viewer():
    """Listings without a thumbnail strip fall back to the main frame's
    own background image, so the zoom viewer ships for every listing."""
    assert "images.length === 0 && main" in JS
    assert "images = [m0[1]]" in JS


# ---------------------------------------------------------------------------
# 3. focus trap + keyboard control
# ---------------------------------------------------------------------------
def test_lightbox_focus_trap_and_keyboard():
    assert "e.key === 'Escape'" in JS            # Escape closes
    assert "if (e.key !== 'Tab') return;" in JS  # Tab is trapped
    assert "e.shiftKey" in JS                    # Shift+Tab wraps backwards
    assert "lastFocus" in JS and "lastFocus.focus()" in JS   # focus restore
    assert "removeEventListener('keydown', lbKeys, true)" in JS
    # Arrows navigate while the viewer is open (lightbox-owned handler).
    assert "if (e.key === 'ArrowLeft') { show(current - 1); lbSync(); return; }" in JS
    assert "if (e.key === 'ArrowRight') { show(current + 1); lbSync(); return; }" in JS
    # The gallery's own arrow handler yields while the lightbox is open.
    assert "if (lb && lb.classList.contains('is-open')) return;" in JS


# ---------------------------------------------------------------------------
# 4. scroll lock releases Lenis via the F5 public API
# ---------------------------------------------------------------------------
def test_scroll_lock_and_lenis_handshake():
    assert "window.__lenis" in JS
    assert "window.__lenis.stop" in JS and "window.__lenis.start" in JS
    assert "classList.add('lb-open')" in JS
    assert "classList.remove('lb-open')" in JS
    assert re.search(r"html\.lb-open\s*\{[^}]*overflow:\s*hidden", CSS), (
        "detail.css must lock scrolling while the lightbox is open"
    )


# ---------------------------------------------------------------------------
# 5. shared-element wiring: unique G2 name on the gallery main; the
#    lightbox overlay never carries it (D-LOOP-32a)
# ---------------------------------------------------------------------------
def test_shared_element_name_wired_and_unique(seeded_db):
    """The per-listing G2 name stays on the gallery main and stays unique
    page-wide (similar-listing cards carry names of OTHER pks)."""
    from apps.listings.models import Property
    p = Property.objects.published().first()
    assert p is not None, "migrated demo data must include a published property"
    html = Client().get(p.get_absolute_url()).content.decode()
    names = re.findall(r"view-transition-name:\s*(prop-\d+)", html)
    assert f"prop-{p.pk}" in names, (
        f"the detail page must carry the per-listing shared-element name prop-{p.pk}"
    )
    assert len(names) == len(set(names)), f"duplicate shared-element names on detail: {names}"
    assert names.count(f"prop-{p.pk}") == 1, (
        "this pk's name must appear exactly once — on the gallery main"
    )
    # It lives on the gallery main (the data-gallery-main element).
    main_tag = re.search(r"<div class=\"gallery gallery--revamp\" data-gallery>.*?data-gallery-main[^>]*", html, re.S)
    assert main_tag, "gallery main element missing"
    assert "view-transition-name: prop-" in main_tag.group(0)


def test_lightbox_never_carries_the_shared_name():
    # CSS: the lightbox main frame opts out explicitly.
    assert re.search(r"\.lightbox__main\s*\{[^}]*view-transition-name:\s*none", CSS, re.S)
    # JS: no per-listing name is ever set on the lightbox DOM.
    lb_code = JS[JS.index("L4: lightbox"):]
    assert "view-transition-name: prop-" not in lb_code
    assert "prop-" + "' +" not in lb_code and "' + property" not in lb_code


# ---------------------------------------------------------------------------
# 6. CSS hygiene: tokens only, motion parity (F2), no hex ratchet debt
# ---------------------------------------------------------------------------
def test_lightbox_css_tokens_and_motion_parity():
    block = l4_css()
    assert "#" not in re.sub(r"/\*.*?\*/", "", block, flags=re.S), (
        "the L4 CSS block must use tokens only — no raw hex"
    )
    assert "var(--" in block
    # F2 parity: fx=none and reduced-motion kill the fade exactly alike.
    assert re.search(r'html\[data-fx="none"\] \.lightbox[^{]*\{[^}]*transition:\s*none', block)
    assert re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{[^@]*\.lightbox[^{]*\{[^}]*transition:\s*none", block, re.S)
    # The overlay sits on the modal z-layer token.
    assert "z-index: var(--z-modal)" in block
