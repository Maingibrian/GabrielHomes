"""r88 — the map deck carries the palm field, drifting with scroll.

Owner: "the ocean background in the listings page doesnt look well
when contrasted to the map and objects before it.... return the palm
tree background but peg it to the listings so one can scroll and them
move so they dont seem stagnant.... simple motion."

The r88 vision review confirmed the r86 ocean clash: the near-ink
scrim faded unevenly down the deck (0.93 top, 0.55 middle), so the
outlined market cards sat on busy mid-tone photo texture with mushy
edges, and the photo's greens/teals fought the cream map tile and the
brand palette. The deck now repeats the SAME palm field the listings
band introduces (palm-field-even.svg under a soft cream veil, ink
type back to the pre-r86 values), and motion.js setupPalmParallax
writes --palms-y on the shell too, so deck and band drift as one
continuous half-speed motion.

The r86 stacking contract is unchanged: the pseudos stay
ROOT-NEGATIVE and the section keeps NO isolation, because the fixed
.map-return-pill (z-index var(--z-modal)) must stay above the later
in-flow listing rows.
"""
import re
from pathlib import Path

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text(encoding="utf-8")
MOTION_JS = (REPO / "static" / "js" / "motion.js").read_text(encoding="utf-8")


def _shell_rule():
    m = re.search(r"\.search-map-shell \{[^}]*\}", SEARCH_CSS)
    assert m, ".search-map-shell rule missing"
    return m.group(0)


class DeckPalmField(SimpleTestCase):
    def test_deck_carries_the_palm_field_tile(self):
        before = re.search(r"\.search-map-shell::before \{[^}]*\}", SEARCH_CSS)
        assert before, ".search-map-shell::before missing"
        body = before.group(0)
        self.assertIn('url("../img/palm-field-even.svg")', body,
                      "same tile as the listings band field")
        self.assertIn("background-repeat: repeat", body,
                      "the deck is a pattern, not a cover photo")
        self.assertIn("z-index: -2", body,
                      "root-negative: below the section's in-flow content")
        self.assertNotIn("coast-dhow", body,
                         "the ocean photo is retired from the deck")

    def test_deck_tile_matches_the_band_field_scale(self):
        """One continuous field: the deck uses the band's exact tile
        size (and its 1020px drop), so the dissolve hands over
        without a scale seam."""
        before = re.search(r"\.search-map-shell::before \{[^}]*\}", SEARCH_CSS)
        band = re.search(r"\.listings-band::before \{[^}]*\}", SEARCH_CSS)
        assert before and band
        self.assertIn("background-size: 1400px 1600px", before.group(0))
        self.assertIn("background-size: 1400px 1600px", band.group(0))

    def test_deck_veil_is_cream_not_ink(self):
        after = re.search(r"\.search-map-shell::after \{[^}]*\}", SEARCH_CSS)
        assert after, ".search-map-shell::after missing"
        body = after.group(0)
        self.assertIn("z-index: -1", body)
        self.assertIn("color-mix(in srgb, var(--cream) 72%, transparent)", body,
                      "the veil keeps the pattern a whisper behind the map")
        self.assertNotIn("rgba(24, 17, 13", body,
                         "the near-ink scrim is retired with the photo")

    def test_deck_pattern_rides_the_drift_var(self):
        """Pegged to the listings: the deck's background-position Y
        reads the same var motion.js advances, with the 0px fallback
        for every visitor the gate excludes."""
        before = re.search(r"\.search-map-shell::before \{[^}]*\}", SEARCH_CSS)
        assert before
        body = before.group(0)
        self.assertIn("background-position: 0 var(--palms-y, 0px)", body)
        self.assertIn("background-attachment: scroll", body,
                      "scroll stays the declared safe default (fail-closed)")
        self.assertNotIn("background-attachment: fixed", SEARCH_CSS,
                         "fixed attachment pins the pattern — stagnant")

    def test_motion_js_drives_the_deck_var(self):
        """setupPalmParallax writes --palms-y on the map shell too,
        under the same gate as the band field (one continuous motion)."""
        setup = re.search(
            r"function setupPalmParallax\(\) \{(.*?)\n  \}", MOTION_JS, re.S)
        assert setup, "setupPalmParallax missing from motion.js"
        body = setup.group(1)
        self.assertIn('.search-map-shell', body,
                      "the setup must resolve the deck element")
        self.assertIn('if (deck) deck.style.setProperty("--palms-y", val)',
                      body or "", "the deck var is written with the band's")

    def test_heading_is_ink_again(self):
        """Back to the pre-r86 light-page palette: burnt eyebrow, ink
        h1, taupe subline — AA over the cream veil."""
        h1 = re.search(r"\.search-map-heading h1 \{[^}]*\}", SEARCH_CSS)
        assert h1, ".search-map-heading h1 missing"
        self.assertNotIn("var(--cream)", h1.group(0))
        eyebrow = re.search(r"\.search-map-heading p \{[^}]*\}", SEARCH_CSS)
        assert eyebrow
        self.assertIn("var(--burnt)", eyebrow.group(0))
        sub = re.search(r"\.search-map-heading > span \{[^}]*\}", SEARCH_CSS)
        assert sub
        self.assertIn("var(--taupe)", sub.group(0))

    def test_market_cards_dropped_the_white_outline(self):
        """The r86 outline existed to separate photo cards from the
        dark photo deck; on the cream field the plain shadow is the
        crisper edge again."""
        m = re.search(r"\.market-filter \{[^}]*\}", SEARCH_CSS)
        assert m, ".market-filter rule missing"
        self.assertNotIn("rgba(250,248,244,.4)", m.group(0))

    def test_section_has_no_isolation_but_keeps_relative(self):
        """isolation here would trap the fixed map-return-pill's
        z-index inside the section — it must stay root-scoped."""
        rule = _shell_rule()
        self.assertIn("position: relative", rule)
        self.assertNotIn("isolation", rule)

    def test_home_section_untouched(self):
        """The home page's own coast-dhow recipe must still exist
        unchanged — the photo lives on, just not on this deck."""
        home = (REPO / "static" / "css" / "home.css").read_text(encoding="utf-8")
        rule = re.search(r"\.home-nearby::before \{[^}]*\}", home)
        assert rule
        self.assertIn('url("../img/real/coast-dhow.jpg")', rule.group(0))
