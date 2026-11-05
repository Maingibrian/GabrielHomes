"""P5-1 — motion.js smooth-scroll selector regression guard.

Run 1's audit logged P5-1: motion.js reportedly used the invalid selector
``aref^="#"]`` (a SyntaxError on every click, smooth-scroll dead). Run 8's
security pass verified at byte level that the shipped file has ALWAYS had
the correct ``a[href^="#"]`` — the audit saw a transport-mangled display of
the line, not the file. P5-1 is closed as a false positive; these tests pin
the correct selector so a real regression can never ship silently.
"""
from pathlib import Path

MOTION_JS = Path(__file__).resolve().parents[3] / "static" / "js" / "motion.js"

CORRECT = 'a[href^="#"]'
BROKEN = 'aref^="#"]'


def test_smooth_scroll_selector_is_valid():
    js = MOTION_JS.read_text(encoding="utf-8")
    assert CORRECT in js, (
        "motion.js lost the valid anchor selector a[href^=\"#\"] — "
        "smooth-scroll would silently die."
    )


def test_broken_selector_never_returns():
    js = MOTION_JS.read_text(encoding="utf-8")
    assert BROKEN not in js, (
        "motion.js contains the invalid selector aref^ — this throws a "
        "SyntaxError inside the delegated click handler on every click."
    )


def test_motion_ready_gate_still_present():
    """D-MOTION-SAFE: reveal styles only apply under html.motion-ready, set
    by motion.js itself. If the gate is removed, blocked-JS pages could go
    permanently blank — keep the contract."""
    js = MOTION_JS.read_text(encoding="utf-8")
    assert 'classList.add("motion-ready")' in js
