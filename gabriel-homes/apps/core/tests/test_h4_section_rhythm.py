"""H4 — section rhythm proving tests.

The home page reads as a deliberate rhythm of section archetypes
(runbook §6 H4; docs/DESIGN-ADDENDUM.md "Section archetypes"):

  full-bleed   — imagery owns the stage (hero, showcase bento)
  type-led     — the heading carries the section (recommended, nearby)
  edge strip   — narrow full-width stitch band (the five-checks marquee)

Every top-level band on home carries its archetype as `data-archetype`
in DOM order, at least 3 distinct archetypes are used on home, and
never more than 2 consecutive bands share one archetype.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db

REPO = Path(__file__).resolve().parents[3]
ADDENDUM = REPO / "docs" / "DESIGN-ADDENDUM.md"

ALLOWED = {"full-bleed", "type-led", "edge-strip"}

# The documented home mapping (addendum, "Home mapping"), in flow order.
EXPECTED_BANDS = [
    ("hero", "full-bleed"),
    ("checks", "edge-strip"),
    ("bento", "full-bleed"),
    ("recommended", "type-led"),
    ("nearby", "type-led"),
]


@pytest.fixture(autouse=True)
def seeded_db(db):
    """Seed before each test so the conditional sections (recommended /
    nearby) render — same isolation as test_h1_home_order."""
    from django.core.cache import cache
    cache.clear()
    call_command("seed_demo", no_images=True, target=20, verbosity=0,
                 i_know_this_is_demo=True)
    yield
    cache.clear()


def home() -> str:
    r = Client().get("/")
    assert r.status_code == 200, f"/ -> {r.status_code}"
    return r.content.decode()


def band_pairs() -> list:
    out = []
    for m in re.finditer(r'<(section|div)\b([^>]+)>', home()):
        attrs = m.group(2)
        aid = re.search(r'\bid="([^"]+)"', attrs)
        aar = re.search(r'data-archetype="([a-z-]+)"', attrs)
        if aid and aar:
            out.append((aid.group(1), aar.group(1)))
    return out


# ---------------------------------------------------------------------------
# 1. the addendum documents the archetypes and the rhythm rule
# ---------------------------------------------------------------------------
def test_addendum_documents_three_archetypes_and_rule():
    doc = ADDENDUM.read_text()
    for name in ("**full-bleed**", "**type-led**", "**edge strip**"):
        assert name in doc, f"addendum must document archetype {name}"
    assert "never more than 2" in doc, "addendum must state the rhythm rule"
    assert "at least 3 archetypes" in doc, "addendum must state the ≥3 rule"


def test_addendum_documents_the_home_mapping():
    doc = ADDENDUM.read_text()
    assert "Home mapping" in doc, "addendum must pin the concrete home mapping"
    for token in ("`#hero` full-bleed", "`#checks` edge strip",
                  "`#bento` full-bleed", "`#recommended` type-led",
                  "`#nearby` type-led"):
        assert token in doc, f"addendum home mapping missing {token!r}"


# ---------------------------------------------------------------------------
# 2. the bands on home are tagged, in order, with allowed archetypes
# ---------------------------------------------------------------------------
def test_home_bands_tagged_in_expected_order():
    pairs = band_pairs()
    assert pairs == EXPECTED_BANDS, (
        f"home flow bands must be {EXPECTED_BANDS} — got {pairs}"
    )


def test_every_archetype_is_from_the_documented_set():
    for _id, arche in band_pairs():
        assert arche in ALLOWED, f"#{_id} carries undocumented archetype {arche!r}"


# ---------------------------------------------------------------------------
# 3. the rhythm rules themselves
# ---------------------------------------------------------------------------
def test_at_least_three_archetypes_used_on_home():
    used = {a for _i, a in band_pairs()}
    assert len(used) >= 3, (
        f"home must use at least 3 distinct archetypes — got {sorted(used)}"
    )


def test_never_more_than_two_consecutive_bands_share_one_archetype():
    seq = [a for _i, a in band_pairs()]
    run, best = 1, 1
    for prev, cur in zip(seq, seq[1:]):
        run = run + 1 if cur == prev else 1
        best = max(best, run)
    assert best <= 2, (
        f"rhythm broken: {best} consecutive bands share one archetype — {seq}"
    )
