"""r49 — uniform listing cards + hero remodel (owner request).

Two owner asks in one round:

1. "ensure all listing cards are the same size" — search-page rows had
   height:auto, so each grid track sized itself to the photo's natural
   aspect ratio (one portrait 942x1280 image made its card 883px tall
   against 397px neighbours). The rule now declares a definite 460px
   height (measured worst-case content stack 456px + slack, overflow
   verified on every seeded row); the definite track also makes
   .listing-row__media's height:100% resolve so every media cell is
   identical. Mobile keeps its own fixed 680px stack.

2. "remodel the bland hero section to look more like the attached
   image" — per the owner's reference: two-column hero (text stack +
   floating listing card), orange accent bar on the headline, frosted
   service-assurance strip, popular-area chips under the search pill,
   bottom-left market stat, and a lighter scrim so the room reads warm.

r50 second pass (owner round two, see test_r50_hero_card_cycle): the
strip is reworded (no agents on this site, no banned "verified"), the
card became a dynamic pane carousel pinned top-right, the search pill
moved to a lower hero__search-zone band, and the eyebrow tag is gone.
The r49 pins below are updated to the r50 reality; the ones the r50
pass did not touch (uniform rows, scrim, accent bar, sides hiding,
market stat, chips) still pin their r49 contracts.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
HOME_HTML = REPO / "templates" / "core" / "home.html"
HOME_CSS = REPO / "static" / "css" / "home.css"
SEARCH_CSS = REPO / "static" / "css" / "search.css"


class UniformCardTests(SimpleTestCase):
    """All listing cards the same size (search page)."""

    def setUp(self):
        self.css = SEARCH_CSS.read_text(encoding="utf-8")

    def test_desktop_row_declares_a_definite_height(self):
        rule = re.search(r"^\.listing-row \{[^}]*\}", self.css, re.M)
        self.assertTrue(rule, ".listing-row rule must exist")
        body = rule.group(0)
        self.assertIn("height: 460px", body,
                      "uniform 460px height (measured worst content 456)")
        self.assertNotIn("height: auto", body,
                         "auto lets photo aspect drive the row height")

    def test_media_cell_fills_the_now_definite_track(self):
        """The mechanism: media height:100% only resolves once the track
        is definite — that is what makes every image cell identical."""
        media = re.search(r"^\.listing-row__media \{[^}]*\}", self.css, re.M)
        self.assertTrue(media)
        self.assertIn("height: 100%", media.group(0))
        self.assertIn("min-height: 0", media.group(0))

    def test_mobile_keeps_its_own_uniform_stack(self):
        self.assertIn("height:680px", self.css,
                      "mobile rows keep the fixed 680px stack")


class HeroMarkupTests(SimpleTestCase):
    """The remodelled hero carries every reference element."""

    def setUp(self):
        self.html = HOME_HTML.read_text(encoding="utf-8")

    def test_two_column_grid_wraps_the_hero(self):
        self.assertIn('class="hero__grid"', self.html)
        self.assertIn('class="hero__main"', self.html)

    def test_headline_unchanged_and_contract_kept(self):
        """The word-mask headline contract (test_h2_hero) must survive
        the remodel: data-hero-headline on the h1, no templated masks."""
        self.assertRegex(
            self.html,
            r'<h1 class="hero__title[^"]*"[^>]*data-hero-headline>')
        self.assertNotIn("hero__w", self.html)

    def test_assurance_strip_three_items(self):
        """r50: reworded — no agents on this site (owner: none of the team
        are agents), no banned "verified". The strip states what actually
        happens; the old r49 labels are gone."""
        self.assertIn('class="hero__assurances', self.html)
        for label in ("Checked listings", "Prices in writing",
                      "A person replies"):
            self.assertIn(label, self.html)
        for banned in ("Local agents", "Dedicated support",
                       "Trusted listings"):
            self.assertNotIn(banned, self.html)

    def test_search_pill_still_the_single_hero_gesture(self):
        hero = self.html.split("</section>", 1)[0]
        self.assertEqual(hero.count("<form"), 1,
                         "exactly one form — the search pill")

    def test_popular_area_chips_are_conditional_and_live(self):
        self.assertIn("{% if popular_areas %}", self.html)
        self.assertIn("{% for area in popular_areas %}", self.html)
        self.assertIn("{{ area.url }}", self.html)
        self.assertIn("{{ area.name }}", self.html)
        self.assertIn("{{ area.count }}", self.html)

    def test_hero_card_is_conditional_and_content_complete(self):
        """r50: the card is a pane carousel (hero_card_listings, plural —
        the view's r49 singular key is retired)."""
        self.assertIn("{% if hero_card_listings %}", self.html)
        for hook in ("hero-card__track", "data-hero-card-pane",
                     "hero-card__media", "hero-card__badge",
                     "hero-card__title", "hero-card__loc",
                     "hero-card__price", "hero-card__link",
                     "hero-card__dots", "data-hero-card-dot"):
            self.assertIn(hook, self.html)
        self.assertIn("{{ listing.price|kes }}", self.html)
        self.assertIn("{{ listing.get_absolute_url }}", self.html)
        # pane #1 is active in the served HTML — no-JS shows listing #1
        self.assertIn(
            'class="hero-card__pane{% if forloop.first %} is-active{% endif %}"',
            self.html)
        # the dots only render when there is something to rotate
        self.assertIn("{% if hero_card_listings|length > 1 %}", self.html)

    def test_market_stat_carries_the_owner_figure(self):
        self.assertIn('class="hero__market"', self.html)
        self.assertIn("Mombasa property market", self.html)
        self.assertIn("+12% YoY", self.html)


class HeroCSSTests(SimpleTestCase):
    """The r49 block: every element styled, scrim warm, zero new hex."""

    def setUp(self):
        css = HOME_CSS.read_text(encoding="utf-8")
        start = css.index("r50 — HERO")
        end = css.index("3. Featured properties", start)
        self.block = css[start:end]

    def test_accent_bar_beside_the_headline(self):
        css = HOME_CSS.read_text(encoding="utf-8")
        rules = re.findall(r"^\.hero__title \{[^}]*\}", css, re.M)
        self.assertTrue(rules, ".hero__title rule must exist")
        # the r49 remodel restates the title rule to add the accent bar —
        # at least one .hero__title rule must carry it
        self.assertTrue(
            any("border-left: 4px solid var(--burnt)" in r for r in rules),
            "the reference's orange accent bar must be styled")

    def test_frosted_assurance_strip(self):
        self.assertIn("backdrop-filter: blur(10px)", self.block)
        self.assertIn(".hero__assurances li + li { border-left:", self.block)

    def test_chips_and_card_and_stat_present(self):
        for hook in (".hero__loc ", ".hero-card ", ".hero__market "):
            self.assertIn(hook, self.block)

    def test_sides_hide_gracefully_off_desktop(self):
        self.assertIn("@media (max-width: 1199px)", self.block)
        self.assertIn(".hero-card { display: none; }", self.block)
        self.assertIn("@media (max-width: 1020px)", self.block)
        self.assertIn(".hero__market { display: none; }", self.block)

    def test_scrim_rebalanced_toward_warm(self):
        """The old near-black band (0.72 -> 0.48 left-to-right, 0.34 mid)
        made the room unreadable; the r49 scrim opens the right side to
        the photo (0.06) while the title band keeps its legibility."""
        scrim = HOME_CSS.read_text(encoding="utf-8").split(
            ".hero__bg::after", 1)[1][:900]
        self.assertIn("rgba(28,21,17,.66) 0%", scrim)
        self.assertIn("rgba(28,21,17,.06) 82%", scrim)
        self.assertNotIn("0.72) 0%", scrim, "the old dead-dark band is gone")

    def test_r50_block_adds_no_hex(self):
        """F1 ratchet: home.css hex count may only go down — the r50
        block must be hex-free (tokens, color-mix, rgba only)."""
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", self.block), [])


# ---------------------------------------------------------------------------
# Live-data view tests (seeded, same isolation pattern as test_h1_home_order)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestHeroViewData:
    """popular_areas + hero_card_listing are live-data driven."""

    @pytest.fixture(autouse=True)
    def seeded_db(self, db):
        from django.core.cache import cache
        cache.clear()
        call_command("seed_demo", no_images=True, target=20, verbosity=0,
                     i_know_this_is_demo=True)
        yield
        cache.clear()

    def test_home_renders_chips_and_card(self):
        html = Client().get("/").content.decode()
        chips = re.findall(r'class="hero__loc" href="(/property-for-sale/[^"]+)"', html)
        # the contract is "the top areas" — up to four, and only areas
        # that actually carry published listings (test DB ordering can
        # shift the seeded distribution, so 1..4 is the honest pin)
        assert 1 <= len(chips) <= 4, f"popular-area chips, got {chips}"
        for url in chips:
            assert re.match(r"^/property-for-sale/[a-z-]+/$", url)
        assert 'class="hero-card' in html
        assert "hero-card__price" in html

    def test_chips_carry_live_counts(self):
        html = Client().get("/").content.decode()
        assert re.search(r'hero__loc-count">\d+<', html)

    def test_rendered_hero_copy_is_checked_language(self):
        """No "verified" on public pages (p0) and no agent wording (the
        site has none); the strip reads Checked/Prices/A person."""
        html = Client().get("/").content.decode()
        assert "Checked listings" in html
        assert "Prices in writing" in html
        assert "A person replies" in html
        assert "Local agents" not in html
        assert "verified" not in html.lower()
