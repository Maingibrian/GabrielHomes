"""r96 — the reels hug their words (owner round thirteen).

The owner looked at the r95 reels and asked for the reels to sit CLOSE
to the words ("the carousels are way too far from the words"). Measured
live at 1920px before this round: gabriel→reel 234px, homes→reel 303px
— because the reels were pinned to the SECTION's far edges
(bottom/top: 6rem) while the words anchor from the opposite ends
(gabriel: top 7.5rem; homes: bottom 7.5rem), so the gap grew with the
section height instead of tracking the word.

r96 re-anchors: each flank becomes a flex COLUMN anchored exactly where
its word is anchored today, with the reel in flow next to the word at a
fixed gap. The distance is a CSS variable (--reel-hug) so the pin is
explicit, and the words keep their exact anchor offsets (7.5rem from
their edges) — the SECTION-relative pins are retired.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = (REPO / "static" / "css" / "home.css").read_text(encoding="utf-8")
HOME_HTML = (REPO / "templates" / "core" / "home.html").read_text(encoding="utf-8")


def test_reel_gap_is_a_fixed_hug_var():
    """The reel-to-word distance is a single small custom property used
    by both flanks — not a section-edge offset that grows with page
    height."""
    assert "--reel-hug" in HOME_CSS, (
        "the reel-to-word gap must be pinned in a custom property")
    # a small gap: at most 3rem (48px) — a hug, not a stretch
    m = re.search(r"--reel-hug:\s*([^;]+);", HOME_CSS)
    assert m, "--reel-hug must be defined"
    val = m.group(1).strip()
    if val.endswith("rem"):
        assert float(val[:-3]) <= 3, (
            f"--reel-hug must stay small (<= 3rem), got {val}")


def test_flanks_are_hug_columns():
    """Each flank is a flex column so the word and its reel move as one
    unit, anchored from the word's own edge (not the section's)."""
    base = re.search(r"@media \(min-width: 1440px\)\s*\{"
                     r"[^@]*?\.bento-flank\s*\{[^}]*\}", HOME_CSS)
    assert base, "the >=1440px .bento-flank rule must exist"
    rule = base.group(0)
    assert "display: flex" in rule, (
        "the flank must be a flex column (word + reel in flow)")
    assert "flex-direction: column" in rule


def test_reels_are_in_flow_next_to_words():
    """The reels drop their own absolute section-edge pins — they sit in
    the flank's column flow, a --reel-hug away from the word."""
    gab = re.findall(r"\.bento-flank--gabriel\s+\.flank-reel\s*\{[^}]*\}",
                     HOME_CSS)
    hom = re.findall(r"\.bento-flank--homes\s+\.flank-reel\s*\{[^}]*\}",
                     HOME_CSS)
    for rules in (gab, hom):
        assert rules, "each flank needs a reel placement rule"
        joined = "\n".join(rules)
        assert "position: absolute" not in joined, (
            "the reel must not be absolutely pinned to the flank anymore")
        # the hug: one flank pads above its reel, the other below —
        # each side sets exactly one of the two
        assert ("margin-top: var(--reel-hug)" in joined
                or "margin-bottom: var(--reel-hug)" in joined), (
            "the reel must sit a --reel-hug from its word")


def test_words_keep_their_anchors():
    """The words keep their exact anchors, now expressed as the flank's
    own padding (gabriel hangs 7.5rem from the top, homes rises 7.5rem
    from the bottom) — same offsets the old absolute word pins held."""
    g = "\n".join(re.findall(r"\.bento-flank--gabriel\s*\{[^}]*\}",
                             HOME_CSS))
    h = "\n".join(re.findall(r"\.bento-flank--homes\s*\{[^}]*\}",
                             HOME_CSS))
    assert "padding-top: 7.5rem" in g, (
        "gabriel keeps its top anchor (flank padding-top)")
    assert "padding-bottom: 7.5rem" in h, (
        "homes keeps its bottom anchor (flank padding-bottom)")
    # and the word itself is no longer absolutely pinned
    w = re.search(r"\.bento-flank__word\s*\{[^}]*\}", HOME_CSS)
    assert w and "position:" not in w.group(0), (
        "the word is static in the column flow now")


def test_template_reel_markup_unchanged():
    """Scope check: r96 (the hug) touched ONLY placement CSS — the
    template markup kept its r95 shape. r97 later grew the films to 21
    frames for the word→edge span (see test_r97_reel_span.py); this
    pin now guards the r97 shape against accidental shrinkage."""
    assert HOME_HTML.count("flank-reel__frame") == 42, (
        "both reels keep their 21 frames (42 total)")
    assert len(re.findall(r'class="flank-reel__blur', HOME_HTML)) == 4, (
        "both reels keep their blur strips (4 divs total)")
