"""r92 — dashboard visual polish on the r91 board.

Why: the r91 board worked but read flat — four identical KPI tiles (no
entry point for the eye), a sparkline under the KPI it did NOT measure
(per_day = enquiries/day, not listing views), the checklist (the
workhorse panel) styled as the weakest element on the page, and two
full-size quick-action cards competing with it. r92 is layout-only
polish: tokens only, no JS, mobile stack untouched.

Pinned here: the hero tile, the sparkline's new home, the dark
checklist anchor, the compact quick tiles, and the guarantee that every
token the new CSS reads without a fallback exists (same mechanism as
test_portal_design_stack).
"""
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
HOME = REPO / "templates" / "manage" / "home.html"
CSS = REPO / "static" / "css" / "manage.css"

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner(client):
    from django.contrib.auth import get_user_model

    get_user_model().objects.create_superuser(
        email="owner@test.com", password="owner-pass-123"
    )
    client.force_login(get_user_model().objects.get(email="owner@test.com"))
    return client


# ---------- The hero KPI ----------

def test_first_kpi_is_the_espresso_hero_with_the_sparkline(owner):
    """The first tile is the hero: sparkline sits under the enquiry KPI
    it actually measures (per_day = enquiries per day)."""
    body = owner.get("/manage/").content.decode()
    assert 'class="manage-kpi manage-kpi--hero"' in body
    # sparkline lives INSIDE the hero tile, before the live-listings tile
    hero = body.split('manage-kpi--hero', 1)[1]
    assert "manage-kpi__spark" in hero.split('class="manage-kpi"', 1)[0]
    # and it appears exactly once on the page
    assert body.count('class="manage-kpi__spark"') == 1


# ---------- The checklist anchor ----------

def test_checklist_is_the_dark_anchor(owner):
    body = owner.get("/manage/").content.decode()
    assert "manage-check--dark" in body
    # it keeps its board zone + the progress semantics
    assert "manage-board__check" in body
    assert 'aria-label="Setup checklist"' in body
    assert 'role="progressbar"' in body


# ---------- Quick actions stay compact ----------

def test_quick_tiles_kept_their_zones_and_actions(owner):
    body = owner.get("/manage/").content.decode()
    assert body.count('class="manage-card manage-module manage-board__quick"') == 2
    assert "Edit site content" in body and "Open SEO settings" in body


# ---------- The CSS pins ----------

def test_css_defines_the_r92_polish():
    css = CSS.read_text()
    for rule in (
        ".manage-kpi--hero",
        ".manage-check--dark",
        ".manage-check--dark .manage-check__item",
        ".manage-check--dark .manage-next",
        ".manage-board__welcome",
        # welcome card flattens ONLY on desktop (mobile keeps the card)
        ".manage-kpi:hover",
    ):
        assert rule in css, f"missing r92 rule: {rule}"

    # the flatten-the-welcome-card rule must live inside the 64rem block
    desktop = css.split("@media (min-width: 64rem)", 2)[-1]
    assert ".manage-board__welcome" in desktop


def test_r92_css_reads_only_real_tokens():
    """Every token the r92 section reads without a fallback must exist in
    tokens.css (same mechanism as test_portal_charts_can_resolve_tokens,
    which already covers the whole file — this pins the r92 additions)."""
    import re

    tokens_src = (REPO / "static" / "css" / "tokens.css").read_text()
    defined = set(re.findall(r"^\s*(--[a-z0-9-]+)\s*:", tokens_src, re.M))
    css = CSS.read_text()
    r92 = css.split("r92 — dashboard visual polish", 1)[1]
    bare = set(re.findall(r"var\((--[a-z0-9-]+)\s*\)", r92))
    missing = sorted(bare - defined)
    assert missing == [], f"r92 reads undefined tokens: {missing}"


# ---------- Guarantees carried over from r91 ----------

def test_still_no_javascript_and_mobile_untouched():
    for path in (HOME, REPO / "templates" / "manage" / "base.html"):
        assert "<script" not in path.read_text(), f"{path.name} must stay script-free"
    # the <64rem mobile stack keeps the card look (hero/dark are additive)
    css = CSS.read_text()
    assert ".manage-side { display: none; }" in css
