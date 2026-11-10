"""r65 — palm-field parallax on the home market band (owner round
thirteen).

Owner ask: "make the palm leaves svg in the index have a parallax
effect" — the r46 palm field (the seamless frond tile behind the
curated Mombasa listings band) now drifts against the page on a
scroll-linked timeline.

The contract pinned here (grep-level, same style as test_r46):

* transform-only keyframes, symmetric ±140px — no layout shift, GPU
  compositable (r58 gate philosophy);
* delivered ONLY under @supports (animation-timeline: view()) and
  ONLY to html[data-fx="rich"] — reduced-motion (none), Save-Data
  (lite) and JS-blocked (no attribute) all fail closed to the r46
  stills, exactly like the palm wind sway in search.css;
* the full cover range (the band is taller than any viewport; an
  entry/exit range would stall mid-band);
* the ::before traveler is overfilled past the travel (inset -170px
  vs ±140px drift) and the section clips it, so no gap can open and
  nothing paints outside the band;
* the bottom fade is a STATIC ::after veil — it never rides the
  drift (the TALK TO US strip keeps its clean sand);
* no script is involved: the effect is pure CSS, so there is no
  no-JS leg to test — a missing data-fx attribute IS the no-JS leg;
* the band sand is the --sand-band token (D-LOOP-65a) — home.css
  carries no #f4eee6 hex any more, so the F1 ratchet fell 198 → 197.

The addendum grep bridge (SHIPPED_TOKENS stays frozen, D-LOOP-32a
precedent): DESIGN-ADDENDUM.md names palm-field-parallax under the M1
scroll-linked family — no new vocabulary row, the cap stays 6.
"""
from __future__ import annotations

import re
from pathlib import Path

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = REPO / "static" / "css" / "home.css"
TOKENS_CSS = REPO / "static" / "css" / "tokens.css"
ADDENDUM = REPO / "docs" / "DESIGN-ADDENDUM.md"

TRAVEL = 140      # px, the ± drift in the keyframes
MARGIN = 170      # px, the ::before overfill past the section edges


def _css() -> str:
    return HOME_CSS.read_text(encoding="utf-8")


def _supports_blocks(css: str) -> list[str]:
    """Every animation-timeline @supports block in home.css (there
    are two shippers: the r20 bento rail and the r65 palm field —
    inner braces are indented, block closers sit at column 0)."""
    return re.findall(
        r"@supports \(animation-timeline: view\(\)\) \{(.*?)\n\}",
        css, re.S)


def _palm_supports_block(css: str) -> str:
    """The palm-parallax @supports block specifically."""
    for block in _supports_blocks(css):
        if ".home-market::before" in block:
            return block
    raise AssertionError(
        "no animation-timeline @supports block targets .home-market::before")


class PalmFieldParallaxTests(SimpleTestCase):
    """The shipped contract."""

    def setUp(self):
        self.css = _css()

    def test_keyframes_are_transform_only_and_symmetric(self):
        m = re.search(
            r"@keyframes palm-field-parallax \{(.*?)\n\}", self.css, re.S)
        assert m, "palm-field-parallax keyframes not found"
        body = m.group(1)
        # transform-only: translateY is the sole animated property —
        # GPU-compositable, zero layout shift (Q1/CLS)
        decls = re.findall(r"([a-z-]+)\s*:\s*[^;]+;", body)
        self.assertEqual(decls, ["transform", "transform"],
                         "the parallax must animate transform only — "
                         "no layout, no opacity, no paint properties")
        self.assertIn(f"translateY(-{TRAVEL}px)", body)
        self.assertIn(f"translateY({TRAVEL}px)", body)
        # the drift is symmetric around the section's rest position,
        # so the field enters and exits the band offset by the same
        # amount (no net displacement at rest mid-band)
        self.assertEqual(body.count("translateY("), 2)

    def test_delivery_is_supports_guarded_and_rich_gated(self):
        block = _palm_supports_block(self.css)
        self.assertIn('html[data-fx="rich"] .home-market::before', block,
                      "the traveler animation must key off the fx gate")
        self.assertIn("animation: palm-field-parallax linear both", block)
        self.assertIn("animation-timeline: view()", block)
        # the FULL cover range: the band is taller than any viewport,
        # so entry/exit ranges would freeze mid-drift
        self.assertIn("animation-range: cover 0% cover 100%", block)

    def test_fails_closed_everywhere_else(self):
        """The ONLY rule that animates the ::before is the rich-gated
        one inside @supports. fx=none (reduced motion), lite
        (Save-Data) and no-attribute (JS blocked / gate never ran)
        can never match it — the r46 stills stand."""
        block = _palm_supports_block(self.css)
        # exactly one animated selector, and it is the rich one
        animated = re.findall(
            r"([^{}\n]+)\{[^}]*animation:[^}]*\}", block)
        self.assertEqual(
            [a.strip() for a in animated],
            ['html[data-fx="rich"] .home-market::before'],
            "nothing but the rich-gated traveler may animate here")
        # and with EVERY animation-timeline @supports block removed
        # (the bento rail ships one too), no ::before rule animates
        stripped = re.sub(
            r"@supports \(animation-timeline: view\(\)\) \{.*?\n\}",
            "", self.css, flags=re.S)
        before_rules = re.findall(
            r"\.home-market::before \{([^}]*)\}", stripped)
        self.assertTrue(before_rules,
                        "the ::before rule must exist outside supports blocks")
        for rule in before_rules:
            self.assertNotIn(
                "animation", rule,
                "an un-gated ::before animation would move the field "
                "under reduced-motion / Save-Data / no-JS")

    def test_drift_margin_exceeds_travel(self):
        """The ::before is overfilled past the travel so the tile can
        never expose a gap at either end of the drift."""
        m = re.search(r"\.home-market::before \{([^}]*)\}", self.css)
        assert m, ".home-market::before rule not found"
        self.assertIn(f"inset: -{MARGIN}px 0", m.group(1))
        self.assertGreater(MARGIN, TRAVEL,
                           "the overfill must exceed the drift travel")

    def test_the_fade_veil_is_static(self):
        """The bottom fade lives on the ::after and never animates —
        a traveling fade would drag the TALK TO US clear-zone with
        the drift."""
        m = re.search(r"\.home-market::after \{([^}]*)\}", self.css)
        assert m, ".home-market::after veil not found"
        self.assertNotIn("animation", m.group(1))
        self.assertNotIn("translate", m.group(1))

    def test_no_new_script_is_involved(self):
        """Pure CSS delivery — no script drives the parallax or the
        band (scroll-linked by the UA itself; the r46 placement was
        already CSS-only and stays that way)."""
        for js in (REPO / "static" / "js").glob("*.js"):
            text = js.read_text(encoding="utf-8")
            self.assertNotIn(
                "palm-field-parallax", text,
                f"{js.name} must not drive the CSS-owned parallax")
            self.assertNotIn(
                "home-market", text,
                f"{js.name} must not reach into the market band")

    def test_addendum_maps_the_effect(self):
        """Grep bridge (D-LOOP-32a precedent): the M1 scroll-linked
        family row names palm-field-parallax — the vocabulary cap
        stays 6, no new row."""
        text = ADDENDUM.read_text(encoding="utf-8")
        self.assertIn("palm-field-parallax", text,
                      "the addendum must name the shipped hook")


class SandBandTokenTests(SimpleTestCase):
    """D-LOOP-65a: the band sand is a token now — the F1 ratchet
    fell 198 → 197 (home.css's last one-off hex left the file)."""

    def test_token_is_defined_with_the_exact_value(self):
        css = TOKENS_CSS.read_text(encoding="utf-8")
        m = re.search(r"--sand-band:\s*(#[0-9a-fA-F]{6})", css)
        assert m, "--sand-band token not defined in tokens.css"
        self.assertEqual(m.group(1).lower(), "#f4eee6",
                         "the token must carry the exact band sand value "
                         "the section always used (render-invisible swap)")

    def test_home_css_uses_the_token_and_carries_no_hex(self):
        css = _css()
        self.assertGreaterEqual(css.count("var(--sand-band)"), 2,
                                "section background + fade veil both use it")
        self.assertNotIn("#f4eee6", css,
                         "the raw band sand must not linger in home.css")
