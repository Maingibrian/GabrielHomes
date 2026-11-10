"""r51 — hero third pass: market stat out, bubble shrunk, livelier hero.

Owner round three, three asks:

1. "the bubble containing the above [Checked listings / Prices in
   writing / A person replies] is too large" — the frosted strip
   stretched across the whole text column with ~250px of dead glass
   after the last label (VLM-measured on the r50 screenshot). The
   pill is now inline-flex: it hugs its content, and its paddings,
   icons and metrics are tightened with it (~56px tall -> ~40px).

2. "you dint remove the Mombasa property market Growing demand
   +12% YoY" — the bottom-left market stat this repo carried since
   r49 is now REMOVED: template block, CSS rules and the 1020px
   hide block are all gone. The bottom band keeps only the search
   pill, the chips and the scroll cue.

3. "again with some animations improve the hero further" — four
   new moves, every one fail-open (no hidden state in any base
   rule; the reduced-motion kill list drops the animation and
   leaves the content fully visible):

     - the three assurance items pop in one by one (ha-pop:
       rise -> tiny overshoot -> settle, 90ms stagger);
     - the popular-area chips rise in one by one after the pill
       settles (ha-chip, 70ms stagger, the label leads);
     - the featured-card swap drifts left as it fades instead of
       a plain fade (the outgoing pane takes a translateX on
       .is-leaving; every r50-pinned prefix survives verbatim);
     - the search pill leans in 2px on :focus-within (transform
       only, gated behind html.motion-ready so no-JS never moves).

   The block-level hv2-rise on the strip and the chips is retired —
   the per-item entrances own that beat now. Zero new hex (F1).
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


def _block() -> str:
    css = HOME_CSS.read_text(encoding="utf-8")
    return css[css.index("r50 — HERO"):css.index("3. Featured properties",
                                                 css.index("r50 — HERO"))]


# ---------------------------------------------------------------------------
# Markup — the stat is gone, the strip is per-item, nothing else moved
# ---------------------------------------------------------------------------
class R51MarkupTests(SimpleTestCase):

    def setUp(self):
        self.html = HOME_HTML.read_text(encoding="utf-8")

    def test_market_stat_block_deleted(self):
        for gone in ('class="hero__market"', "Mombasa property market",
                     "Growing demand", "+12% YoY", "hero__market-text"):
            self.assertNotIn(gone, self.html)
        # the section now flows straight from the search zone to the cue
        self.assertIn('class="hv2-scroll"', self.html)

    def test_strip_and_chips_lose_their_block_level_rise(self):
        """The per-item entrances own the beat — the ul/nav no longer
        carry hv2-rise (exact-match pins, not prefixes)."""
        self.assertIn('<ul class="hero__assurances" aria-label=', self.html)
        self.assertIn('<nav class="hero__locations" aria-label=', self.html)
        self.assertNotIn("hero__assurances hv2-rise", self.html)
        self.assertNotIn("hero__locations hv2-rise", self.html)
        # the words themselves stay (r56 comfort labels, pinned by
        # r49/r50/r56)
        for label in ("Homes with character", "Sea-breeze mornings",
                      "Coastal short stays"):
            self.assertIn(label, self.html)


# ---------------------------------------------------------------------------
# CSS — the shrink, the four moves, the kill switches, no new hex
# ---------------------------------------------------------------------------
class R51StripTests(SimpleTestCase):
    """The bubble, shrunk to its content."""

    def setUp(self):
        self.block = _block()

    def test_pill_hugs_its_content(self):
        """inline-flex sizes the pill to its labels — the full-column
        stretch (the 'too large' defect) is gone."""
        rule = re.search(r"^\.hero__assurances \{[^}]*\}", self.block, re.M)
        self.assertTrue(rule, ".hero__assurances rule missing")
        body = rule.group(0)
        self.assertIn("display: inline-flex", body)
        self.assertIn("max-width: 100%", body)
        self.assertNotIn("align-items: stretch", body,
                         "stretch belongs to the full-column pill")

    def test_metrics_tightened(self):
        li = re.search(r"^\.hero__assurances li \{[^}]*\}", self.block, re.M)
        self.assertTrue(li)
        self.assertIn("padding: 4px 14px", li.group(0))
        svg = re.search(r"^\.hero__assurances svg \{[^}]*\}", self.block, re.M)
        self.assertTrue(svg)
        self.assertIn("width: 15px; height: 15px", svg.group(0))
        pill = re.search(r"^\.hero__assurances \{[^}]*\}", self.block, re.M)
        self.assertIn("padding: 4px 6px", pill.group(0))

    def test_per_item_pop_with_stagger(self):
        self.assertIn("@keyframes ha-pop", self.block)
        # rise -> overshoot -> settle: the r47 bubbly language at pill scale
        self.assertRegex(
            self.block,
            r"from \{ opacity: 0; transform: translateY\(12px\) scale\(\.92\); \}")
        self.assertRegex(
            self.block,
            r"70%\s*\{ opacity: 1; transform: translateY\(-2px\) scale\(1\.02\); \}")
        self.assertIn("animation: ha-pop .7s", self.block)
        self.assertIn("both", self.block)  # backwards fill covers the delays
        self.assertIn(".hero__assurances li:nth-child(1) { animation-delay: .36s; }", self.block)
        self.assertIn(".hero__assurances li:nth-child(2) { animation-delay: .45s; }", self.block)
        self.assertIn(".hero__assurances li:nth-child(3) { animation-delay: .54s; }", self.block)

    def test_pop_fails_open(self):
        """No hidden state in any base rule: the entrance lives only in
        the animation, so killing it (reduced-motion) leaves the items
        fully visible — and no-JS still gets the CSS animation."""
        base = re.search(r"^\.hero__assurances li \{[^}]*\}$", self.block, re.M)
        self.assertTrue(base)
        self.assertNotIn("opacity: 0", base.group(0),
                         "a base hidden state would trap content")


class R51ChipTests(SimpleTestCase):

    def setUp(self):
        self.block = _block()

    def test_chips_rise_one_by_one(self):
        self.assertIn("@keyframes ha-chip", self.block)
        self.assertIn("animation: ha-chip .6s", self.block)
        self.assertIn(
            ".hero__locations-label { animation: ha-chip .6s", self.block)
        self.assertIn("animation-delay: .62s", self.block)
        for i, delay in ((1, ".69s"), (2, ".76s"), (3, ".83s"), (4, ".90s")):
            self.assertIn(
                f".hero__loc:nth-of-type({i}) {{ animation-delay: {delay}; }}",
                self.block)


class R51CardDriftTests(SimpleTestCase):

    def setUp(self):
        self.block = _block()

    def test_outgoing_pane_drifts_as_it_fades(self):
        rule = re.search(r"^\.hero-card__pane\.is-leaving \{[^}]*\}",
                         self.block, re.M)
        self.assertTrue(rule)
        self.assertIn("transform: translateX(-16px) scale(.99)",
                      rule.group(0))
        # the r50-pinned prefix survives verbatim in front of the drift
        self.assertRegex(
            self.block,
            r"\.hero-card__pane\.is-leaving \{\s*display: grid; position: absolute; inset: 0; z-index: 2; opacity: 0;")

    def test_transition_covers_the_drift(self):
        self.assertIn(
            "html.motion-ready .hero-card__pane { transition: opacity .55s"
            " var(--ease-out), transform .55s var(--ease-out);",
            self.block)
        # the r48 triple kill switches stay (r50 pins them; r51 re-checks)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.block)
        self.assertIn('.hero-card__pane { transition: none !important; }',
                      self.block)


class R51PillLiftTests(SimpleTestCase):

    def setUp(self):
        self.block = _block()
        self.css = HOME_CSS.read_text(encoding="utf-8")

    def test_focus_lift_gated_behind_motion_ready(self):
        self.assertIn("html.motion-ready .hero__search {", self.block)
        self.assertIn(
            "html.motion-ready .hero__search:focus-within {\n"
            "  transform: translateY(-2px);",
            self.block)

    def test_lift_dies_under_reduced_motion(self):
        rm = self.css.split("prefers-reduced-motion: reduce", 1)[1]
        self.assertIn(".hero__search:focus-within { transform: none !important; }",
                      rm)


class R51KillSwitchTests(SimpleTestCase):

    def setUp(self):
        self.css = HOME_CSS.read_text(encoding="utf-8")
        self.block = _block()

    def test_reduced_motion_kills_all_four_new_moves(self):
        rm = self.css.split("---- reduced motion", 1)[1]
        for selector in (".hero__assurances li", ".hero__loc",
                         ".hero__locations-label"):
            self.assertIn(selector, rm)
        # ha-pop/ha-chip/pane-drift/pill-lift all die as one list
        self.assertIn(".hv2-rise, .hv2-marquee__track, .hv2-scroll span,",
                      rm)

    def test_r51_block_adds_no_hex(self):
        """F1 ratchet: tokens, color-mix and rgba only."""
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", self.block), [])


# ---------------------------------------------------------------------------
# Rendered page — the stat is really gone from the DOM, the strip survives
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestR51Rendered:

    @pytest.fixture(autouse=True)
    def seeded_db(self, db):
        from django.core.cache import cache
        cache.clear()
        call_command("seed_demo", no_images=True, target=20, verbosity=0,
                     i_know_this_is_demo=True)
        yield
        cache.clear()

    def test_rendered_home_has_no_market_stat(self):
        html = Client().get("/").content.decode()
        for gone in ("Mombasa property market", "Growing demand",
                     "+12% YoY", 'class="hero__market"'):
            assert gone not in html
        # the strip and its r56 comfort wording survive the shrink
        assert "Homes with character" in html
        assert "Sea-breeze mornings" in html
        assert "Coastal short stays" in html
        assert 'class="hero__assurances"' in html

    def test_rendered_home_keeps_the_h2_contracts(self):
        """One gesture, no stats markup, no CTA buttons — the r51 removal
        re-aligns the hero with the h2 contract (the market stat was the
        only stats-shaped thing left)."""
        html = Client().get("/").content.decode()
        hero = html.split('class="hero"', 1)[1].split("</section>", 1)[0]
        assert hero.count("<form") == 1
        assert "hero__stats" not in hero and "stat__number" not in hero
