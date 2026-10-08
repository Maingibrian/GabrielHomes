"""S10 — Content-Security-Policy and self-hosted Leaflet.

Spec (docs/PLAN.md S10):
  * The CSP header is present on the home page and a listing (detail) page.
  * The detail page loads no script from an external host (parsed HTML check).
  * G-CDN (gate): no unpkg/jsdelivr/framerusercontent references in
    templates/ or static/ — covered by scripts/gate.sh, mirrored here as
    a repo-scan test so CI catches it even outside the gate.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

from apps.listings.models import Property

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]  # .../gabriel_homes


@pytest.fixture(autouse=True)
def seeded_db(db):
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)
    yield


# ---------------------------------------------------------------------------
# CSP header
# ---------------------------------------------------------------------------
def test_csp_header_on_home_page():
    r = Client().get("/")
    assert r.status_code == 200
    csp = r.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "form-action 'self'" in csp


def test_csp_header_on_detail_page():
    p = Property.objects.published().first()
    r = Client().get(p.get_absolute_url())
    assert r.status_code == 200
    assert "Content-Security-Policy" in r.headers


def test_csp_allows_openstreetmap_tiles_only():
    r = Client().get("/")
    csp = r.headers.get("Content-Security-Policy", "")
    assert "https://*.tile.openstreetmap.org" in csp
    # No other external hosts are whitelisted.
    assert "unpkg.com" not in csp
    assert "jsdelivr" not in csp


# ---------------------------------------------------------------------------
# No external scripts on the detail page
# ---------------------------------------------------------------------------
def test_detail_page_loads_no_external_script():
    p = Property.objects.published().first()
    html = Client().get(p.get_absolute_url()).content.decode()
    for src in re.findall(r'<script[^>]*\bsrc="([^"]+)"', html):
        assert src.startswith("/") or src.startswith("http://testserver"), (
            f"external script reference found: {src}"
        )


def test_detail_page_leaflet_is_self_hosted():
    p = Property.objects.published().first()
    html = Client().get(p.get_absolute_url()).content.decode()
    assert "unpkg.com" not in html
    assert "/static/vendor/leaflet/leaflet.js" in html
    assert "/static/vendor/leaflet/leaflet.css" in html


# ---------------------------------------------------------------------------
# Repo scan — mirrors gate stage G-CDN
# ---------------------------------------------------------------------------
def test_repo_has_no_cdn_references():
    banned = re.compile(r"unpkg\.com|cdn\.jsdelivr\.net|framerusercontent\.com")
    hits = []
    for root in ("templates", "static"):
        base = REPO / root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in {".html", ".js", ".css"}:
                if banned.search(path.read_text(encoding="utf-8", errors="ignore")):
                    hits.append(str(path))
    assert hits == [], f"CDN references found in: {hits}"


def test_templates_have_no_executable_inline_script_or_handlers():
    """Executable inline scripts and on*= handlers break under CSP
    script-src 'self'. JSON-LD data blocks are data, not code, and are fine."""
    executable = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>", re.I)
    json_ld = re.compile(r'<script[^>]*type="application/ld\+json"', re.I)
    handler = re.compile(r"\son(click|change|submit|load|error|mouseover)=")
    hits = []
    for path in (REPO / "templates").rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if executable.search(line) and not json_ld.search(line):
                hits.append(f"{path.relative_to(REPO)}:{i}: executable inline <script>")
            if handler.search(line):
                hits.append(f"{path.relative_to(REPO)}:{i}: inline on*= handler")
    assert hits == [], "Inline JS found (breaks CSP):\n" + "\n".join(hits)
