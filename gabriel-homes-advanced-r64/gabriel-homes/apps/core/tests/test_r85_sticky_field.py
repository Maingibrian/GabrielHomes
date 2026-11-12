"""r85 — the viewport-sized sticky palm field (jank regression guard).

Owner: "the listings page is back with the laggy motion... when
scrolling it, it has this jerking motion."

Root cause (measured at 4x CPU throttle, 12s wheel scroll):
the drift rewrote background-position on a BAND-SIZED masked
::before — 1280x14000px — so every chase frame re-rastered the
whole band (59ms avg frames, 334 longtasks, 28.7s of longtask
time). Hiding the field dropped the same scroll to 24.6ms; the
SVG tile and the mask were each ~free (unmasked 55.5ms, flat-bg
40.5ms); shrinking ONLY the paint box to a viewport-sticky layer
matched the field-hidden baseline (23.6ms) at identical pixels.

The fix keeps every r69-r71 contract: background-position drift
(no transform/will-change — the r71 ban), half-speed screen
motion, z-index -1 in the root negative layer (footer scrolls
over the field, r62), and the 84% mask dissolve. This test pins
the geometry so the band-sized box cannot silently return.
"""
import re
from pathlib import Path

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
SEARCH_CSS = (REPO / "static" / "css" / "search.css").read_text(encoding="utf-8")
MOTION_JS = (REPO / "static" / "js" / "motion.js").read_text(encoding="utf-8")


def _band_before_rule():
    m = re.search(r"\.listings-band::before \{[^}]*\}", SEARCH_CSS)
    assert m, ".listings-band::before rule missing"
    return m.group(0)


class StickyFieldGeometry(SimpleTestCase):
    """The paint box is viewport-sized and sticky — never band-sized."""

    def test_field_box_is_viewport_sticky_not_band_sized(self):
        rule = _band_before_rule()
        self.assertIn("position: sticky", rule,
                      "the field must be a sticky layer (the r85 fix)")
        self.assertIn("height: 100vh", rule,
                      "viewport-tall box: the drift repaints 1280x800, "
                      "not the whole 14,000px band (the measured jank)")
        self.assertIn("margin-bottom: -100vh", rule,
                      "the negative margin cancels the sticky box's "
                      "flow footprint — band geometry is unchanged")
        self.assertIn("top: 0", rule,
                      "pins the viewport top while the band is on screen")
        # r65/r68 contracts still hold on the same rule
        self.assertIn('url("../img/palm-field-even.svg")', rule)
        self.assertIn("background-position: 0 var(--palms-y, 0px)", rule)
        self.assertIn("background-attachment: scroll", rule)
        self.assertIn("z-index: -1", rule)
        for banned in ("translate3d", "will-change", "transform:"):
            self.assertNotIn(banned, re.sub(r"/\*.*?\*/", "", rule, flags=re.S),
                             f"'{banned}' on the ::before is banned (r71)")

    def test_band_is_not_a_stacking_context(self):
        base = re.search(r"\.listings-band \{[^}]*\}", SEARCH_CSS).group(0)
        self.assertNotIn("isolation", base)
        self.assertNotIn("z-index", base)


class ThreePhaseDriftMath(SimpleTestCase):
    """motion.js: the sticky geometry's three-phase target.

    While the box is PINNED it does not move, so the position alone
    must descend at DRIFT; while it rides the band (entry/release)
    the position climbs at (1 - DRIFT). Joined continuously, the
    tile's SCREEN speed is exactly -0.5x scroll everywhere — the r69
    half-speed contract restated for the sticky box.
    """

    def test_measure_has_three_phases(self):
        m = re.search(r"function measure\(\) \{(.*?)\n    \}", MOTION_JS, re.S)
        assert m, "measure() missing from setupPalmParallax"
        body = m.group(1)
        for needle in ("pinEnd", "1 - DRIFT", "vh * (1 - DRIFT) - DRIFT"):
            self.assertIn(needle, body,
                          f"the three-phase target needs '{needle}'")
        # half speed is still the constant
        drift = re.search(r"var DRIFT = ([\d.]+);", MOTION_JS)
        self.assertTrue(drift and abs(float(drift.group(1)) - 0.5) < 1e-9)
        # r70 chase contracts intact
        self.assertIn("1 - Math.exp(-dt / TAU)", MOTION_JS)
        self.assertIn("var MAXDT", MOTION_JS)
