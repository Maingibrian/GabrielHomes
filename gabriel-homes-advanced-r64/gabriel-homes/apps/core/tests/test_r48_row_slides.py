"""r48 — alternating listing-row slide-in (owner request).

"on the listings page when one scrolls down let the listings have
transitions alternation in different directions — the first listing
scrolls smoothly from the left to center, the second from the right
to center."

The search page's rows already alternate (odd rows media-left, even
rows --reverse media-right). r48 makes that alternation the entrance:
motion.js setupRowSlides arms each row (data-slide-row) and an
IntersectionObserver with hysteresis flips .is-slid at >=20%
visibility — odd rows glide in from the LEFT, --reverse rows from the
RIGHT, and a row that FULLY leaves the viewport re-arms so the glide
replays in both scroll directions (same hysteresis contract as the
r47 bubbly titles).

D-MOTION-SAFE: the hidden from-state needs BOTH html.motion-ready
(set by motion.js as its first statement) AND .row-armed (added per
row only AFTER io.observe succeeds). fx=none / no-JS / no-IO ->
rows render in place, fully visible.
"""
from __future__ import annotations

import re
from pathlib import Path

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
TEMPLATE = REPO / "templates" / "listings" / "_results_grid.html"
SEARCH_CSS = REPO / "static" / "css" / "search.css"
MOTION_JS = REPO / "static" / "js" / "motion.js"
ADDENDUM = REPO / "docs" / "DESIGN-ADDENDUM.md"


class RowSlideTemplateTests(SimpleTestCase):
    """Every listing row carries the hook; pinned attribute order kept."""

    def test_every_row_carries_data_slide_row(self):
        body = TEMPLATE.read_text(encoding="utf-8")
        articles = re.findall(r"<article class=\"listing-row[^>]*>", body)
        self.assertGreaterEqual(
            len(articles), 1, "the results template renders listing rows")
        for tag in articles:
            self.assertIn("data-slide-row", tag,
                          "every listing row must carry data-slide-row")
            self.assertIn("data-cursor-view", tag,
                          "G4 cursor hook must survive alongside r48")

    def test_identity_attribute_order_kept_for_l1(self):
        """L1 pins class -> id=listing-row-<pk> -> data-listing-pk; the
        hook is appended at the END of the tag so that regex (and the
        G4 article regex) keeps matching."""
        body = TEMPLATE.read_text(encoding="utf-8")
        self.assertRegex(
            body,
            r'<article class="listing-row[^"]*"\s+id="listing-row-\{\{ property\.pk \}\}"'
            r'\s+data-listing-pk="\{\{ property\.pk \}\}"[^>]*data-slide-row>')
        # alternation drives the direction: reverse stays on every 2nd row
        self.assertIn("forloop.counter|divisibleby:2", body)
        self.assertIn("listing-row--reverse", body)


class RowSlideDirectionTests(SimpleTestCase):
    """Odd rows enter from the LEFT, reverse rows from the RIGHT."""

    def setUp(self):
        self.css = SEARCH_CSS.read_text(encoding="utf-8")

    def _rule(self, selector: str) -> str:
        m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", self.css)
        self.assertTrue(m, f"rule missing: {selector}")
        return m.group(1)

    def test_base_row_slides_from_the_left(self):
        rule = self._rule("html.motion-ready .listing-row.row-armed")
        self.assertIn("opacity: 0", rule, "armed rows start invisible")
        self.assertIn(
            "transform: translateX(calc(var(--slide-dist) * -1))", rule,
            "odd rows enter from the LEFT (negative translateX)")
        self.assertIn("transition:", rule, "the glide is a transition")
        self.assertIn("var(--ease-out)", rule, "smooth ease-out glide")

    def test_reverse_row_slides_from_the_right(self):
        rule = self._rule(
            "html.motion-ready .listing-row--reverse.row-armed")
        self.assertIn(
            "transform: translateX(var(--slide-dist))", rule,
            "reverse rows enter from the RIGHT (positive translateX)")

    def test_slid_state_settles_at_rest_and_wins_the_cascade(self):
        rule = self._rule("html.motion-ready .listing-row.is-slid")
        self.assertIn("transform: translateX(0)", rule)
        self.assertIn("opacity: 1", rule)
        # same specificity as the armed rules -> must come AFTER them in
        # source order or a settled row would keep its off-side offset
        armed = self.css.index("html.motion-ready .listing-row.row-armed")
        reverse = self.css.index(
            "html.motion-ready .listing-row--reverse.row-armed")
        slid = self.css.index("html.motion-ready .listing-row.is-slid")
        self.assertLess(armed, slid)
        self.assertLess(reverse, slid)

    def test_distance_token_is_bounded(self):
        block = self.css.split("r48 — alternating row slide-in", 1)[1]
        m = re.search(re.escape(".results-grid") + r"\s*\{([^}]*)\}", block)
        self.assertTrue(m, "the r48 block must define .results-grid")
        rule = m.group(1)
        self.assertIn("--slide-dist: clamp(", rule,
                      "the travel distance must be clamped")
        self.assertIn("vw", rule, "distance scales with the viewport")

    def test_overflow_guard_stops_the_horizontal_scrollbar(self):
        """Armed rows park translated ±--slide-dist while off-screen;
        without a viewport x-clip they would open a horizontal
        scrollbar. The guard lives in search.css, which only the
        listings page loads."""
        self.assertIn("body { overflow-x: hidden; overflow-x: clip; }",
                      self.css,
                      "hidden fallback + clip override, in that order")


class RowSlideSafetyTests(SimpleTestCase):
    """CSS alone can never hide a row; every kill switch fires."""

    def setUp(self):
        self.css = SEARCH_CSS.read_text(encoding="utf-8")

    def test_hidden_state_requires_both_js_added_gates(self):
        self.assertIn("html.motion-ready .listing-row.row-armed", self.css)
        # no attribute-selector hiding: without JS the row renders
        self.assertNotIn("[data-slide-row] { opacity: 0", self.css)
        self.assertNotIn("[data-slide-row]{opacity: 0", self.css)

    def test_reduced_motion_kills_the_glide(self):
        self.assertIn(
            "@media (prefers-reduced-motion: reduce) {\n"
            "  html.motion-ready .listing-row.row-armed,\n"
            "  html.motion-ready .listing-row.is-slid {",
            self.css)
        self.assertIn("transition: none !important", self.css)

    def test_fx_none_and_missing_gate_fail_closed(self):
        self.assertIn('html[data-fx="none"] .listing-row.row-armed', self.css)
        self.assertIn("html:not([data-fx]) .listing-row.row-armed", self.css)

    def test_zero_hex_kept(self):
        """F1 T2 pinned search.css to ZERO hex literals — the r48 block
        must not reintroduce any."""
        block = self.css.split("r48 — alternating row slide-in", 1)[1]
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", block), [])


class RowSlideEngineTests(SimpleTestCase):
    """motion.js: gate -> observe -> arm, hysteresis replay, HTMX re-arm."""

    def setUp(self):
        self.js = MOTION_JS.read_text(encoding="utf-8")

    def test_registered_in_init(self):
        init_at = self.js.index("function init()")
        self.assertIn("setupRowSlides();", self.js[init_at:])

    def test_gate_precedes_everything(self):
        fn = self.js.index("function setupRowSlides")
        gate = self.js.index('if (fxNone || !("IntersectionObserver" in window)) return;', fn)
        arm = self.js.index('el.classList.add("row-armed")', fn)
        self.assertLess(gate, arm,
                        "the fx/IO gate must come before any arming")

    def test_armed_only_after_observe(self):
        """A crash between observe and arming must leave visible rows
        (fail-closed arming order, same as r47 bt-armed)."""
        fn = self.js.index("function setupRowSlides")
        observe = self.js.index("io.observe(el);", fn)
        arm = self.js.index('el.classList.add("row-armed")', fn)
        self.assertLess(observe, arm, "arm after observe")

    def test_hysteresis_replays_both_directions(self):
        fn = self.js.index("function setupRowSlides")
        body = self.js[fn:self.js.index("function init()", fn)]
        self.assertIn("intersectionRatio >= 0.2", body, "slide at 20%")
        self.assertIn("intersectionRatio === 0", body,
                      "re-arm only once FULLY out of view")
        self.assertIn('classList.add("is-slid")', body)
        self.assertIn('classList.remove("is-slid")', body)

    def test_htmx_swap_re_arms_new_rows(self):
        fn = self.js.index("function setupRowSlides")
        body = self.js[fn:self.js.index("function init()", fn)]
        self.assertIn('"htmx:afterSwap"', body,
                      "pagination/filter/sort swaps replace the grid")
        self.assertIn(":not(.row-armed)", body,
                      "re-arm only rows that are not armed yet")


class RowSlideVocabularyTests(SimpleTestCase):
    """The slide rides the M1 rise row — the vocabulary stays at 6."""

    def test_rides_m1_and_vocabulary_unchanged(self):
        text = ADDENDUM.read_text(encoding="utf-8")
        self.assertIn("data-slide-row", text)
        self.assertIn("setupRowSlides", text)
        self.assertIn("--slide-dist", text)
        rows = re.findall(r"^\| M\d+\b", text, re.M)
        self.assertEqual(len(rows), 6, "no M7: the slide rides M1 (rise)")
