"""Run 14 — OpenFreeMap basemap on BOTH maps (search + detail).

The owner's tile provider is OpenFreeMap (free, no API key). Both the
/properties/ map and the property-detail map render OpenFreeMap's positron
style with self-hosted MapLibre GL 6.16 (ESM build) vendored into
static/vendor/maplibre-gl/ — no renderer CDN, no iframe embed. These tests
pin the wiring end to end so neither map can silently regress to an
illustrated canvas, an external embed or a CDN script: page markup, the
vendored files on disk, the JS contract, and the vendoring hygiene lesson
from G-STATIC (sourceMappingURL comments pointing at unshipped .map files
break collectstatic under the manifest storage).
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]  # .../gabriel_homes root
VENDOR = REPO / "static" / "vendor" / "maplibre-gl"


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=12, verbosity=0, i_know_this_is_demo=True)
    yield


# ---------------------------------------------------------------------------
# Page wiring — the search page must ship the whole GL stack
# ---------------------------------------------------------------------------
def test_search_page_wires_the_maplibre_stack():
    html = Client().get("/properties/").content.decode()
    # The stylesheet is a plain tag...
    assert "/static/vendor/maplibre-gl/maplibre-gl.css" in html
    # ...and the GL module URL is stamped on the map div as data-maplibre-src
    # (search-map.js import()s it — same-origin, so script-src 'self' holds).
    m = re.search(r'id="search-map"[^>]*data-maplibre-src="([^"]+)"', html)
    assert m, "the map div must stamp the vendored GL module URL"
    assert "maplibre-gl.mjs" in m.group(1)
    # The init script and the map_listings json_script feed are both present.
    assert "/static/js/search-map.js" in html
    assert 'id="search-map-data"' in html


def test_vendored_maplibre_files_exist_on_disk():
    for name in (
        "maplibre-gl.mjs",
        "maplibre-gl-worker.mjs",
        "maplibre-gl.css",
        "LICENSE.txt",
    ):
        path = VENDOR / name
        assert path.is_file(), f"vendored {name} missing from static/vendor/maplibre-gl/"
        assert path.stat().st_size > 0, f"vendored {name} is empty"


def test_csp_allows_openfreemap_on_the_page_that_needs_it():
    r = Client().get("/properties/")
    csp = r.headers.get("Content-Security-Policy", "")
    # Vector style + tiles + glyphs go through fetch() → connect-src;
    # sprites ride img-src. The render worker is same-origin (worker-src).
    assert "connect-src 'self' https://tiles.openfreemap.org" in csp
    assert "img-src 'self' data: blob: https://tiles.openfreemap.org" in csp
    assert "unpkg.com" not in csp
    assert "jsdelivr" not in csp


# ---------------------------------------------------------------------------
# JS contract — basemap, pins, popups, reset, fallback
# ---------------------------------------------------------------------------
def test_search_map_js_contract():
    js = (REPO / "static" / "js" / "search-map.js").read_text()
    # OpenFreeMap positron is the basemap (the owner's provider, no API key).
    assert "https://tiles.openfreemap.org/styles/positron" in js
    # The GL module is imported from the template-stamped URL — never a CDN.
    assert "mapEl.dataset.maplibreSrc" in js
    assert "unpkg.com" not in js
    assert "cdn.jsdelivr" not in js
    # On-map chrome.
    assert "NavigationControl" in js
    # Price pins keep their market colouring, popups and the duplicate spread.
    assert "map-price-pin--" in js
    assert "map-property-popup" in js
    assert "View home" in js
    # Auto-framing on load + the "Show all homes" reset (run 14).
    assert "fitBounds" in js
    assert "Show all homes" in js
    # Graceful degradation: a failed GL load explains itself instead of
    # leaving the "Loading…" text on screen forever.
    assert "could not load" in js


def test_detail_map_js_contract():
    js = (REPO / "static" / "js" / "detail-map.js").read_text()
    assert "https://tiles.openfreemap.org/styles/positron" in js
    assert "mapEl.dataset.maplibreSrc" in js
    assert "maplibregl.Marker" in js  # the approximate-location pin
    assert "arcgisonline.com" not in js
    assert "basemaps.cartocdn.com" not in js
    assert "tile.openstreetmap.org" not in js
    assert "could not load" in js  # graceful fallback text


# ---------------------------------------------------------------------------
# Vendoring hygiene — the G-STATIC lesson, pinned for future re-vendoring
# ---------------------------------------------------------------------------
def test_vendored_maplibre_references_no_missing_map_files():
    """Whitenoise's manifest storage post-processes every static file and
    fails collectstatic (MissingFileError) on sourceMappingURL comments
    whose .map file is not shipped. The vendored MapLibre ESM bundles had
    them; they were stripped in run 14 — this keeps them stripped."""
    for path in VENDOR.iterdir():
        if path.suffix in {".mjs", ".js", ".css"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"sourceMappingURL=\S+", text)
            assert m is None, f"{path.name} still references a missing .map file (G-STATIC)"
