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
                      "viewport-tall box: the paint box stays cheap even "
                      "if a future pass re-arms motion (the measured jank)")
        self.assertIn("margin-bottom: -100vh", rule,
                      "the negative margin cancels the sticky box's "
                      "flow footprint — band geometry is unchanged")
        self.assertIn("top: 0", rule,
                      "pins the viewport top while the band is on screen")
        # r65/r68 contracts still hold on the same rule
        self.assertIn('url("../img/palm-field-even.svg")', rule)
        # r89: the position is FROZEN — stagnation is the sticky box
        # itself, no drift var, no writer
        self.assertIn("background-position: 0 0", rule)
        self.assertNotIn("var(--palms-y", rule,
                         "the r69-r88 drift var is retired (r89)")
        self.assertIn("background-attachment: scroll", rule)
        self.assertIn("z-index: -1", rule)
        for banned in ("translate3d", "will-change", "transform:"):
            self.assertNotIn(banned, re.sub(r"/\*.*?\*/", "", rule, flags=re.S),
                             f"'{banned}' on the ::before is banned (r71)")

    def test_band_is_not_a_stacking_context(self):
        base = re.search(r"\.listings-band \{[^}]*\}", SEARCH_CSS).group(0)
        self.assertNotIn("isolation", base)
        self.assertNotIn("z-index", base)


class StagnantField(SimpleTestCase):
    """r89 (owner: "the palms in the listings page should be stagnant").
    The r85 sticky box is now the stagnation mechanism itself: the
    tile is frozen at 0 0 and holds the viewport while the band is on
    screen, so the fronds sit dead still beside the scrolling rows.
    The three-phase drift math that used to live here (entry/pinned/
    release targets keeping the tile at -0.5x screen speed) is retired
    with the engine — motion.js has no setupPalmParallax and no
    --palms-y writer. Any future motion must come back as
    background-position writes on this same cheap sticky box (r71
    bans compositor transforms outright)."""

    def test_no_drift_engine_or_var_writer_remains(self):
        self.assertNotIn("function setupPalmParallax", MOTION_JS,
                         "the drift engine is deleted (r89)")
        self.assertNotIn('"--palms-y"', MOTION_JS,
                         "nothing may write the retired drift var")
        self.assertNotIn("--palms-y", re.sub(
            r"/\*.*?\*/", "", SEARCH_CSS, flags=re.S),
            "no rule may read the drift var — nothing writes it")
