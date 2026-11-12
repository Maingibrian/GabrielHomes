"""r89 — the palm fields are STAGNANT.

Owner: "the palms in the listings page should be stagnant."

This reverses the r69-r88 motion lineage on the listings page: the
half-speed drift (r69), its frame-rate-independent chase (r70), the
viewport-sticky paint box built for it (r85) and its extension to the
map deck (r88) are all retired as MOTION — the engine is deleted
from motion.js and both fields freeze their background-position.

What survives, and why:
- The r85 sticky box: it is now the stagnation itself — the band's
  ::before holds the viewport top while the band is on screen, so
  the fronds sit perfectly still beside the scrolling rows (what the
  r68 owner pass described as calm, without the fixed-attachment
  bug that silently dies on iOS/Android).
- The r62 paint contract: field + sentinels stay root-negative
  (z-index -1), the footer still scrolls over them.
- The r65/r68 tile contracts: same palm-field-even.svg, same sizes,
  same masks, same 1020px drop.
- The r71 ban: if motion ever returns to these ::befores it must be
  background-position writes — never transform/will-change (Chrome
  hoists the root-negative layer over the static footer).
- The sentinel trees' gentle wind sway (r62 owner ask) is an idle
  animation on the TREES, not the field; it stays gated to
  html[data-fx="rich"] and is untouched by this round.

Stillness is pure CSS: every visitor — rich, lite, fx=none, scripts
blocked, prefers-reduced-motion — sees the identical still field.
"""
import re
from pathlib import Path

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text(encoding="utf-8")
MOTION_JS = (REPO / "static" / "js" / "motion.js").read_text(encoding="utf-8")

STRIPPED_CSS = re.sub(r"/\*.*?\*/", "", SEARCH_CSS, flags=re.S)
STRIPPED_JS = re.sub(r"//.*", "", MOTION_JS)


def _rule(pattern):
    m = re.search(pattern, SEARCH_CSS)
    assert m, f"rule missing: {pattern}"
    return m.group(0)


class StagnantPalms(SimpleTestCase):
    """Both fields frozen; no writer; no var."""

    def test_band_field_position_is_frozen(self):
        rule = _rule(r"\.listings-band::before \{[^}]*\}")
        body = re.sub(r"/\*.*?\*/", "", rule, flags=re.S)
        self.assertIn("background-position: 0 0", body,
                      "the band field must be frozen at 0 0 (r89)")
        self.assertNotIn("var(--palms-y", body)

    def test_deck_field_position_is_frozen(self):
        rule = _rule(r"\.search-map-shell::before \{[^}]*\}")
        body = re.sub(r"/\*.*?\*/", "", rule, flags=re.S)
        self.assertIn("background-position: 0 0", body,
                      "the deck field must be frozen at 0 0 (r89)")
        self.assertNotIn("var(--palms-y", body)

    def test_no_drift_var_anywhere_in_css(self):
        """Comments may tell the history; no declaration may read the
        retired var — nothing writes it."""
        self.assertNotIn("var(--palms-y", STRIPPED_CSS,
                         "--palms-y is retired with the r69-r88 engine")

    def test_drift_engine_is_deleted_from_js(self):
        self.assertNotIn("function setupPalmParallax", MOTION_JS,
                         "the drift engine must stay deleted (r89)")
        self.assertNotIn('"--palms-y"', STRIPPED_JS,
                         "no JS may write the retired drift var")
        self.assertNotIn("setupPalmParallax();", MOTION_JS,
                         "init() must not arm a deleted engine")

    def test_sticky_box_keeps_pinning_the_band(self):
        """The r85 sticky box is the stagnation mechanism: viewport-
        tall, negative-margin cancelled, root-negative."""
        rule = _rule(r"\.listings-band::before \{[^}]*\}")
        for needle in ("position: sticky", "height: 100vh",
                       "margin-bottom: -100vh", "top: 0", "z-index: -1"):
            self.assertIn(needle, rule, f"the sticky pin needs '{needle}'")

    def test_compositor_transform_still_banned(self):
        """The r71 ban guards the ::before regardless of what drives
        it — stillness does not license a transform."""
        rule = _rule(r"\.listings-band::before \{[^}]*\}")
        body = re.sub(r"/\*.*?\*/", "", rule, flags=re.S)
        for banned in ("translate3d", "will-change", "transform:"):
            self.assertNotIn(banned, body, f"'{banned}' is banned (r71)")

    def test_fixed_attachment_stays_banned(self):
        """The sanctioned stillness is the sticky box, not fixed
        attachment (which silently dies on iOS/Android)."""
        self.assertNotIn("background-attachment: fixed", STRIPPED_CSS)

    def test_sentinel_wind_sway_survives(self):
        """The trees' gentle sway is the r62 owner ask, an idle
        animation on the sentinels — NOT the field motion this round
        retires. It stays in the file, gated to rich."""
        self.assertIn("data-fx=\"rich\"", SEARCH_CSS,
                      "the sway gate must survive (r62 contract)")
