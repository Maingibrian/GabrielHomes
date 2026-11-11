"""r47 — location bubbles + bubbly topic-title reveals.

Two owner requests in one round:

1. "the demo listing bubble on the website should be used to indicate
   the location of the listing" — the on-media pill that said
   "Demo listing" now leads with a pin glyph + the listing's area name
   (on EVERY card, real or demo); demo rows keep their disclosure as a
   quieter "demo" flag on the same chip.

2. "every topic should have a reveal animation that is triggered
   whenever scrolling down and up and the title comes into view...
   something bubbly" — data-bubble-title: motion.js splits the title
   into words/letters (DOM APIs only), an IntersectionObserver with
   hysteresis pops it (bt-pop: rise → overshoot → wobble → settle) at
   ≥30% visibility and re-arms it only once FULLY out of view, so the
   bubble replays in both scroll directions.
"""
from __future__ import annotations

import re
from pathlib import Path

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
HOME_HTML = REPO / "templates" / "core" / "home.html"
HOME_CSS = REPO / "static" / "css" / "home.css"
MOTION_JS = REPO / "static" / "js" / "motion.js"
ADDENDUM = REPO / "docs" / "DESIGN-ADDENDUM.md"

CARD_TEMPLATES = [
    REPO / "templates" / "includes" / "_home_card_feature.html",
    REPO / "templates" / "includes" / "_home_card_rail.html",
    REPO / "templates" / "includes" / "_home_card_banner.html",
    REPO / "templates" / "includes" / "_home_card_stay.html",
    REPO / "templates" / "includes" / "_home_property_card.html",
]

PIN_SVG = '<svg class="loc-chip__pin"'


class LocationBubbleTests(SimpleTestCase):
    """The on-media bubble indicates the listing's location."""

    def test_every_card_template_leads_with_the_location(self):
        for path in CARD_TEMPLATES:
            body = path.read_text(encoding="utf-8")
            self.assertIn(PIN_SVG, body, f"{path.name}: pin glyph missing")
            self.assertIn("{{ property.location.name }}", body,
                          f"{path.name}: the bubble must carry the location")
            self.assertNotIn("Demo listing", body,
                             f"{path.name}: the bubble is location-first now")

    def test_demo_disclosure_survives_as_the_flag(self):
        """Honest-labelling intent (test_p0/test_phase2): demo rows still
        say so — as the chip's flag, only when the row IS a demo."""
        for path in CARD_TEMPLATES:
            body = path.read_text(encoding="utf-8")
            self.assertIn(
                '{% if property.is_demo %}<span class="loc-chip__flag">demo'
                "</span>{% endif %}", body,
                f"{path.name}: the demo flag must be conditional")

    def test_bubble_is_decorative_for_assistive_tech(self):
        """The pin glyph carries no meaning on its own; the location text
        is real text. The SVG is aria-hidden + not focusable (the
        established header-logo pattern)."""
        for path in CARD_TEMPLATES:
            body = path.read_text(encoding="utf-8")
            self.assertIn('aria-hidden="true" focusable="false"', body,
                          f"{path.name}: pin svg must be aria-hidden")

    def test_chip_css_grammar_renamed_and_flexed(self):
        css = HOME_CSS.read_text(encoding="utf-8")
        self.assertNotIn(".demo-chip", css, "old chip class fully renamed")
        self.assertNotIn(".market-stay__chip--demo", css)
        for hook in (".loc-chip", ".loc-chip--on-media",
                     ".market-stay__chip--loc", ".loc-chip__pin",
                     ".loc-chip__flag"):
            self.assertIn(hook, css, f"missing chip hook: {hook}")
        # flex so pin + name + flag sit on one line
        chip = re.search(r"\.loc-chip \{[^}]*\}", css)
        assert chip, ".loc-chip rule not found"
        self.assertIn("inline-flex", chip.group(0))


class BubblyTitleTests(SimpleTestCase):
    """data-bubble-title: every home topic pops, replays both ways."""

    def test_every_home_topic_title_carries_the_hook(self):
        """Featured, recommended, the three market groups, talk,
        nearby and the quotes band — all eight topics (r75 grew it
        from seven when testimonials landed on the home page)."""
        html = HOME_HTML.read_text(encoding="utf-8")
        self.assertEqual(html.count("data-bubble-title"), 8,
                         "every topic title must carry data-bubble-title")
        for anchor in ('class="featured__title" data-bubble-title',
                       'class="home-market__title" data-bubble-title',
                       "<h3 data-bubble-title>Homes for sale</h3>",
                       "<h3 data-bubble-title>Long-term rentals</h3>",
                       "<h3 data-bubble-title>Short stays",
                       'class="home-social__title" data-bubble-title',
                       "<h2 data-bubble-title>Homes close to what matters.",
                       "<h2 data-bubble-title>What clients say."):
            self.assertIn(anchor, html, f"missing bubbly topic: {anchor}")

    def test_bubbly_titles_are_never_masked_by_a_parent_fade(self):
        """The bubble replaces the container fade for topic rows — a
        parent [data-reveal] would leave the title area empty (letters
        hidden) while the row itself fades in. The topic containers
        must NOT carry data-reveal."""
        html = HOME_HTML.read_text(encoding="utf-8")
        for container in ('class="featured__header" data-reveal',
                          'class="home-market__heading" data-reveal',
                          'class="home-market__talk" data-reveal',
                          'class="home-market__title" data-reveal'):
            self.assertNotIn(container, html,
                             f"masked bubble: {container} still reveals")

    def test_motion_engine_pops_rearms_and_fails_closed(self):
        js = MOTION_JS.read_text(encoding="utf-8")
        self.assertIn("setupBubbleTitles", js)
        self.assertIn('querySelectorAll("[data-bubble-title]")', js)
        # both directions: re-arm only when FULLY out (ratio 0)
        self.assertIn("intersectionRatio >= 0.3", js)
        self.assertIn("intersectionRatio === 0", js)
        self.assertIn('classList.remove("is-bubbled")', js)
        # D-MOTION-SAFE: the gate check comes before the split…
        self.assertLess(
            js.index('if (fxNone || !("IntersectionObserver" in window)) return;',
                     js.index("function setupBubbleTitles")),
            js.index("splitTitle(el);", js.index("function setupBubbleTitles")),
            "the fx/IO gate must precede the split")
        # …and arming happens only AFTER observe succeeds
        armed_at = js.index('el.classList.add("bt-armed")',
                            js.index("function setupBubbleTitles"))
        observe_at = js.index("io.observe(el);",
                              js.index("function setupBubbleTitles"))
        self.assertLess(observe_at, armed_at,
                        "arm after observe: a crash must leave visible text")
        # S11: the split is DOM-APIs-only
        split_src = js[js.index("function splitTitle"):armed_at]
        self.assertNotIn("innerHTML", split_src)

    def test_css_carries_the_bubble_and_fails_safe(self):
        css = HOME_CSS.read_text(encoding="utf-8")
        self.assertIn("@keyframes bt-pop", css)
        # the bubbly arc: rise from below, overshoot, wobble, settle
        # (slice past the keyframes header — the whole block is short)
        keyframes = css.split("@keyframes bt-pop", 1)[1][:500]
        self.assertIn("scale(.3)", keyframes)
        self.assertIn("scale(1.16)", keyframes)
        self.assertIn("scale(.965)", keyframes)
        # letters hidden ONLY under .bt-armed (a JS-added class)
        self.assertIn(".bt-armed .bt-l { opacity: 0; }", css)
        self.assertNotIn("[data-bubble-title] { opacity: 0", css,
                         "CSS alone must never hide the title")
        # belt-and-braces reduce pin
        self.assertIn(".bt-armed .bt-l { opacity: 1; transform: none; "
                      "animation: none !important; }", css)

    def test_effect_registered_in_the_motion_vocabulary(self):
        """F4: every shipped hook maps to an addendum entry — the bubble
        rides the M1 rise row (vocabulary stays ≤6)."""
        text = ADDENDUM.read_text(encoding="utf-8")
        self.assertIn("data-bubble-title", text)
        self.assertIn("bt-pop", text)
        self.assertIn("hysteresis", text.lower())
        rows = re.findall(r"^\| M\d+\b", text, re.M)
        self.assertLessEqual(len(rows), 6, "vocabulary must stay at most 6")
