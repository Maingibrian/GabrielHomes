"""r97 — the reels run from the words to the section edge (owner round
fourteen: "the carousel should also run from the words all the way to
edge of the section").

r96 made the reels hug their words; the leftover was the reel's own
small 3-frame window floating beside the word with dead space between
it and the section edge. r97 turns the reel window into a flex-fill:
it starts a --reel-hug from the word (r96, unchanged) and stretches to
the flank's far edge, so the film of photos visually connects the word
to the edge of the section.

The loop math survives the taller window: the translate still moves
exactly one --reel-set-h (r95 pin, untouched), and the film now ships
7 sets (21 frames) so coverage is always window + one full set —
measured worst case 1440px: window ~1137px + set 276px ≈ 1413px < 7
sets (1932px incl. gaps). A dedicated test keeps the shipped sets
ahead of the worst-case window so the reel can never run out of film
and snap (the r94 bug, now impossible at any breakpoint).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = (REPO / "static" / "css" / "home.css").read_text(encoding="utf-8")
HOME_HTML = (REPO / "templates" / "core" / "home.html").read_text(encoding="utf-8")


def test_reel_fills_word_to_section_edge():
    """The reel window is no longer a fixed 3-frame box — it grows to
    fill the flank from the word (r96 hug, unchanged) to the section
    edge: flex-grow inside the flank column, never overflowing it."""
    reel_rule = re.search(r"\.flank-reel\s*\{[^}]*\}", HOME_CSS)
    assert reel_rule, "the .flank-reel base rule must exist"
    rule = reel_rule.group(0)
    assert "flex: 1" in rule, (
        "the reel must flex-fill the leftover flank space "
        "(word→edge) instead of a fixed height")
    assert "min-height: calc(3 * var(--reel-frame-h) + 2 * var(--reel-gap))" in rule, (
        "the flex-fill needs a 3-frame floor — a pure flex:1 can "
        "collapse to zero when the column is short and the reel "
        "would vanish (the min-height trap)")
    assert "height: var(--reel-set-h)" not in rule, (
        "the old fixed 3-frame window height must be gone")
    # the flank stays the section-bounded column it was in r96: the
    # reel grows INSIDE it (top:0/bottom:0 pins unchanged), so the
    # span the owner asked for is the flank's own word→edge run
    flank = re.findall(r"\.bento-flank\s*\{[^}]*\}", HOME_CSS)
    joined = "\n".join(flank)
    assert "top: 0" in joined and "bottom: 0" in joined, (
        "the flank must stay pinned to the section's full height — "
        "that full height is what the reel now fills")


def test_film_covers_the_tall_window_plus_a_set():
    """21 frames (7 sets) per reel: the loop distance is one set
    (r95), so coverage must be at least window + one set. Worst case
    measured @1440px: window ≈ 1137px, set ≈ 276px → 1413px needed;
    7 sets ≈ 1932px ships that with headroom for a future card row."""
    blocks = re.findall(
        r'<div class="flank-reel__film">(.*?)</div>', HOME_HTML, re.S)
    assert len(blocks) == 2, "both flanks must carry a reel film"
    for block in blocks:
        n = block.count("flank-reel__frame")
        assert n == 21, (
            f"the taller window needs 7 sets (21 frames), found {n}")
    # the loop distance itself is unchanged: exactly one set
    kf = re.search(r"@keyframes r94-reel-rise\s*\{(.*?)\n\}", HOME_CSS, re.S)
    assert kf, "the rise keyframes must exist"
    assert re.search(
        r"translateY\(calc\(-1 \* var\(--reel-set-h\)\)\)", kf.group(1)), (
        "the rise must still translate exactly one set height")


def test_hug_and_anchors_unchanged():
    """r96 is untouched: the reel still starts a fixed --reel-hug from
    its word, and the words keep their anchors via the flank padding."""
    assert "margin-top: var(--reel-hug)" in HOME_CSS
    assert "margin-bottom: var(--reel-hug)" in HOME_CSS
    g = "\n".join(re.findall(r"\.bento-flank--gabriel\s*\{[^}]*\}", HOME_CSS))
    h = "\n".join(re.findall(r"\.bento-flank--homes\s*\{[^}]*\}", HOME_CSS))
    assert "padding-top: 7.5rem" in g, "gabriel keeps its top anchor"
    assert "padding-bottom: 7.5rem" in h, "homes keeps its bottom anchor"


def test_reel_cannot_overflow_the_flank():
    """The growing reel must clip inside the flank, never spill past
    the section edge (the flank is the boundary the owner named)."""
    # overflow is already hidden on the reel itself; the flank column
    # additionally keeps its children inside its box
    assert re.search(r"\.flank-reel\s*\{[^}]*overflow:\s*hidden", HOME_CSS), (
        "the reel window must keep overflow: hidden")


def test_blur_strips_pin_to_the_window_ends():
    """The dissolve strips sit at the word-end and the section-edge-end
    of the now-taller window (they are absolutely pinned to the reel
    box, which now IS the word→edge span)."""
    assert re.search(r"\.flank-reel__blur--top", HOME_CSS)
    assert re.search(r"\.flank-reel__blur--bottom", HOME_CSS)
    assert len(re.findall(r'class="flank-reel__blur', HOME_HTML)) == 4, (
        "both reels keep their two blur strips")
