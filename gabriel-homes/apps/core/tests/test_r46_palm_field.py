"""r46 — the Mombasa palm field behind the recommended section.

Owner request: "palm leaves in svg in the background... it covers the
background from the RECOMMENDED IN MOMBASA down to the Short stays &
BnB". The field is one seamless tile (static/img/palm-field.svg, drawn
by scripts/r46_palm_field.py) carried by .home-market::before at
z-index:-1 inside the section's own stacking context, faded out just
past the short-stays group.

r65 (owner round thirteen) re-platformed the same stills for the
palm-field parallax: the ::before is now an OVERFILLED traveler
(inset -170px 0, clipped by overflow: clip on the section) and the
bottom fade moved to a STATIC .home-market::after veil so the TALK
TO US strip keeps its clean sand at every drift offset. The r46
contract tests below pin the new wiring; the parallax itself is
pinned by test_r65_palm_parallax.py. The artwork contract (tiny
seamless <use> tile, brand washes, deterministic seed) is untouched.
"""
from __future__ import annotations

import re
from pathlib import Path

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = REPO / "static" / "css" / "home.css"
PALM_SVG = REPO / "static" / "img" / "palm-field.svg"
GENERATOR = REPO / "scripts" / "r46_palm_field.py"
HOME_HTML = REPO / "templates" / "core" / "home.html"


def _palm_block() -> str:
    """The r46 palm-field block in home.css, from the section comment
    to the end of the mobile media query."""
    css = HOME_CSS.read_text(encoding="utf-8")
    return css.split("r46: the palm field", 1)[1].split(
        ".home-market__title", 1)[0]


class PalmFieldAssetTests(SimpleTestCase):
    """The SVG asset: seamless-tile structure + hygiene."""

    def setUp(self):
        self.svg = PALM_SVG.read_text(encoding="utf-8")

    def test_asset_exists_and_is_tiny(self):
        # one <g id="palm-frond"> reused via <use> — a few KiB, not a
        # photo-sized download
        self.assertLess(len(self.svg), 40 * 1024, "palm tile should stay tiny")
        self.assertIn('<g id="palm-frond">', self.svg)
        self.assertGreaterEqual(self.svg.count("<use "), 10,
                                "fronds must be <use> instances, not copies")

    def test_no_scripts_or_remote_refs_in_svg(self):
        """SVG served from /static/ — no scripts, no external fetches,
        nothing for CSP to worry about. (The xmlns declaration itself
        is the mandatory XML namespace, not a fetch.)"""
        stripped = self.svg.replace(
            'xmlns="http://www.w3.org/2000/svg"', "")
        self.assertNotIn("<script", stripped.lower())
        self.assertNotIn("http://", stripped)
        self.assertNotIn("https://", stripped)
        self.assertNotIn("xlink:href", stripped)

    def test_brand_washes_only(self):
        """Two depth layers, both clay washed over the section sand —
        the exact hexes the generator computes from the tokens."""
        self.assertIn("#e7d9cd", self.svg)   # back  = clay @ 14% over sand
        self.assertIn("#dcc6b8", self.svg)   # front = clay @ 26% over sand
        # and nothing loud: no other fill colours sneak in
        fills = set(re.findall(r'fill="([^"]+)"', self.svg))
        self.assertEqual(fills, {"#e7d9cd", "#dcc6b8"})

    def test_generator_is_deterministic_and_pinned(self):
        gen = GENERATOR.read_text(encoding="utf-8")
        self.assertIn("random.seed(46)", gen,
                      "the seed is the artwork's identity — do not change "
                          "it casually; regenerate + re-review if you do")

    def test_seamless_wrapping_is_structural(self):
        """Placements near tile edges are re-emitted wrapped +/-W/+/-H
        (the generator always emits all 9 offsets that intersect), so
        the tile cannot seam. Pin the mechanism, not the placement
        list."""
        gen = GENERATOR.read_text(encoding="utf-8")
        self.assertIn("for ox in (-W, 0.0, W)", gen)
        self.assertIn("for oy in (-H, 0.0, H)", gen)


class PalmFieldCSSTests(SimpleTestCase):
    """The wiring: stacking order, coverage range, fade, no DOM change."""

    def test_section_becomes_the_stacking_context(self):
        """The ::before rides at z-index:-1 — without isolation the
        palms would paint behind the section's own sand background and
        vanish. This pair is the load-bearing contract."""
        css = HOME_CSS.read_text(encoding="utf-8")
        m = re.search(r"\.home-market \{([^}]*)\}", css)
        assert m, ".home-market rule not found"
        self.assertIn("isolation: isolate", m.group(1))
        self.assertIn("position: relative", m.group(1))

    def test_before_layer_contract(self):
        block = _palm_block()
        m = re.search(r"\.home-market::before \{([^}]*)\}", block)
        assert m, ".home-market::before rule not found"
        rule = m.group(1)
        self.assertIn('url("../img/palm-field.svg")', rule)
        self.assertIn("background-repeat: repeat", rule)
        self.assertIn("z-index: -1", rule)
        self.assertIn("pointer-events: none", rule)
        # r65: the traveler is OVERFILLED past the ±140px drift (inset
        # -170px top/bottom) so the tile can never expose a gap while
        # the parallax runs — the section's overflow: clip trims it.
        self.assertIn("inset: -170px 0", rule)
        # r65: the mask is GONE from the traveler — the fade must never
        # ride the drift (it lives on the static ::after veil).
        self.assertNotIn("mask", rule)

    def test_section_clips_the_traveling_field(self):
        """r65: the overfilled ::before must be clipped by the section
        itself, or the ±170px overfill would paint over the bands
        above and below the market section (positioned z:-1 content
        of a LATER stacking context paints over an earlier sibling's
        text). overflow: clip, not hidden — no scroll container is
        created and nothing sticky lives in this band."""
        css = HOME_CSS.read_text(encoding="utf-8")
        m = re.search(r"\.home-market \{([^}]*)\}", css)
        assert m, ".home-market rule not found"
        self.assertIn("overflow: clip", m.group(1))

    def test_coverage_runs_through_short_stays(self):
        """Fade holds solid to 84% and clears by 100% — live-measured
        (1600px viewport): the Short stays & BnB group ends at ~97% of
        the section height, so coverage spans head → short stays and
        only the TALK TO US strip sits on clean sand. r65: the fade is
        the STATIC ::after veil (transparent → --sand-band), so it
        stays glued to the section while the ::before drifts."""
        block = _palm_block()
        m = re.search(r"\.home-market::after \{([^}]*)\}", block)
        assert m, ".home-market::after veil rule not found"
        rule = m.group(1)
        self.assertIn("linear-gradient", rule)
        self.assertIn("transparent 84%", rule)
        self.assertIn("var(--sand-band) 100%", rule)
        self.assertIn("z-index: -1", rule)
        self.assertIn("pointer-events: none", rule)
        # the veil is glued to the section box, not overfilled
        self.assertIn("inset: 0", rule)

    def test_head_veil_present(self):
        """The design-sheet review asked for a soft veil behind the
        head's mid-grey body copy where fronds pass behind it."""
        css = HOME_CSS.read_text(encoding="utf-8")
        m = re.search(r"\.home-market__head::before \{([^}]*)\}", css)
        assert m, ".home-market__head::before rule not found"
        rule = m.group(1)
        self.assertIn("radial-gradient", rule)
        self.assertIn("var(--cream)", rule)
        self.assertIn("z-index: -1", rule)

    def test_mobile_tile_is_finer(self):
        """≤1020px: smaller tile so phone widths see fronds, not
        slivers — and it must sit inside a ≤1020px media query (the
        file has several; find the one that owns the palm rule)."""
        css = HOME_CSS.read_text(encoding="utf-8")
        self.assertIn("background-size: 860px 985px", css,
                      "mobile palm tile size not pinned")
        at = css.index("background-size: 860px 985px")
        media = css.rfind("@media (max-width: 1020px)", 0, at)
        assert media != -1, "the palm tile resize must be media-gated"
        self.assertLess(at - media, 400,
                        "the palm resize and its media query drifted apart")

    def test_palm_block_adds_no_hex(self):
        """The F1 hex ratchet holds block-locally too — every colour
        the palm wiring introduces is a token or a keyword. r65
        tokenised the section sand (#f4eee6 → var(--sand-band),
        D-LOOP-65a), so the block now carries ZERO hex at all."""
        block = _palm_block().replace("../img/palm-field.svg", "")
        hexes = set(re.findall(r"#[0-9a-fA-F]{3,8}", block))
        self.assertEqual(hexes, set(),
                         "the palm block is fully tokenised — use "
                         "tokens/color-mix for anything new")

    def test_no_dom_change_for_the_field(self):
        """The field is CSS-only — no palm markup snuck into the
        template (nothing for screen readers to trip over; the SVG is
        an image asset, never inline content)."""
        html = HOME_HTML.read_text(encoding="utf-8")
        self.assertNotIn("palm", html.lower())
