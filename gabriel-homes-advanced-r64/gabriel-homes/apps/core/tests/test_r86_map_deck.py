"""r86 — the map deck carries the home 'nearby' treatment.

Owner: "the listings page has a blank background behind the map just
before the palm leaves start.... give it the same image background as
the Homes close to what matters. section in the index page."

The recipe is copied from .home-nearby (home.css): coast-dhow.jpg
cover under the near-ink gradient scrim, light type. Difference: this
section contains the FIXED .map-return-pill, so the pseudos are
ROOT-NEGATIVE and the section gets NO isolation (isolation would
stack the pill's z-index INSIDE this section, dragging it under the
later in-flow listing rows).
"""
import re
from pathlib import Path

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text(encoding="utf-8")
HOME_CSS = (REPO / "static" / "css" / "home.css").read_text(encoding="utf-8")


def _shell_rule():
    m = re.search(r"\.search-map-shell \{[^}]*\}", SEARCH_CSS)
    assert m, ".search-map-shell rule missing"
    return m.group(0)


class MapDeckBackground(SimpleTestCase):
    def test_deck_carries_the_dhow_photo(self):
        before = re.search(r"\.search-map-shell::before \{[^}]*\}", SEARCH_CSS)
        assert before, ".search-map-shell::before missing"
        body = before.group(0)
        self.assertIn('url("../img/real/coast-dhow.jpg")', body,
                      "same image as the home nearby section")
        self.assertIn("background-size: cover", body)
        self.assertIn("z-index: -2", body,
                      "root-negative: below the section's in-flow content")

    def test_deck_scrim_matches_the_home_recipe(self):
        after = re.search(r"\.search-map-shell::after \{[^}]*\}", SEARCH_CSS)
        assert after, ".search-map-shell::after missing"
        body = after.group(0)
        self.assertIn("z-index: -1", body)
        self.assertIn("linear-gradient", body)
        self.assertIn("rgba(24, 17, 13, 0.93)", body,
                      "near-ink scrim, same family as home-nearby")

    def test_section_has_no_isolation_but_keeps_relative(self):
        """isolation here would trap the fixed map-return-pill's
        z-index inside the section — it must stay root-scoped."""
        rule = _shell_rule()
        self.assertIn("position: relative", rule)
        self.assertNotIn("isolation", rule)

    def test_heading_switches_to_light_type(self):
        h1 = re.search(r"\.search-map-heading h1 \{[^}]*\}", SEARCH_CSS)
        assert h1, ".search-map-heading h1 missing"
        self.assertIn("var(--cream)", h1.group(0))
        eyebrow = re.search(r"\.search-map-heading p \{[^}]*\}", SEARCH_CSS)
        assert eyebrow
        self.assertIn("var(--ember)", eyebrow.group(0),
                      "eyebrow on dark uses the ember token, like home")

    def test_market_cards_gained_the_light_outline(self):
        m = re.search(r"\.market-filter \{[^}]*\}", SEARCH_CSS)
        assert m, ".market-filter rule missing"
        self.assertIn("rgba(250,248,244,.4)", m.group(0),
                      "photo cards need edge separation on the dark deck")

    def test_home_section_untouched(self):
        """The source recipe on the index page must still exist
        unchanged — this run copies it, never moves it."""
        rule = re.search(r"\.home-nearby::before \{[^}]*\}", HOME_CSS)
        assert rule
        self.assertIn('url("../img/real/coast-dhow.jpg")', rule.group(0))
