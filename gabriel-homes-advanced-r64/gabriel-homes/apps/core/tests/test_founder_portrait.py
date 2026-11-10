"""r24 — the owner-supplied founder portrait (Gabriel Omulu).

Owner upload 2026-11-05 (studio portrait) processed by
scripts/r24_founder_portrait.py into static/img/real/founder-portrait.webp.
Contract (F3-aligned): the /about/ founder card shows the photo with
width/height set, a real alt text, lazy loading, and the asset itself
respects the 250KB image budget as WebP.
"""
import re
from pathlib import Path

import pytest
from django.contrib.staticfiles import finders
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]


def _body():
    return Client().get("/about/").content.decode()


def test_about_founder_card_shows_the_portrait():
    body = _body()
    m = re.search(
        r'<img class="hv2-founder__photo"([^>]+)>', body)
    assert m, "founder photo img missing on /about/"
    attrs = m.group(1)
    assert "founder-portrait.webp" in attrs
    # r52: the founder band is an editorial portrait now — 160px display
    # inside the offset frame (was a 120px chip). Source is 240px, so the
    # 1.5x density still carried it; F3 attrs unchanged.
    # r53: the portrait leads the three-column lockup — display grown to
    # 200px (density 240/200 = 1.2x; acceptable at 1x viewing, noted in
    # pages.css). F3 attrs still width/height/loading/alt.
    assert re.search(r'width="200"', attrs), "width attribute required (F3)"
    assert re.search(r'height="200"', attrs), "height attribute required (F3)"
    assert 'alt="Gabriel Omulu, founder of Gabriel Homes"' in attrs
    assert 'loading="lazy"' in attrs
    # the initials mark is gone
    assert "hv2-founder__mark" not in body
    # name block unchanged
    assert "Gabriel Omulu" in body and "Founder" in body


def test_portrait_asset_exists_webp_and_under_budget():
    path = finders.find("img/real/founder-portrait.webp")
    assert path, "founder-portrait.webp missing from static files"
    data = Path(path).read_bytes()
    assert len(data) <= 250 * 1024, (
        f"founder portrait is {len(data)} bytes — over the 250KB F3 budget")
    assert data[:4] == b"RIFF" and data[8:12] == b"WEBP", (
        "founder portrait must be WebP (F3 diet)")
