"""F2 — capability gate proving tests.

fx-gate.js decides ONCE what a device gets: html[data-fx] = rich | lite |
none, plus html[data-fine] on (hover: hover) and (pointer: fine). Every
effect keys off those attributes; none behaves exactly like the old
reduced-motion path; a missing attribute fails CLOSED (no effects).

The decision table in fx-gate.js computeFx() is mirrored 1:1 by
compute_fx() below — the test docstrings say which side each check pins.
Keep both in sync (the JS file carries the same warning).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "static" / "js"
FX_GATE = JS / "fx-gate.js"
MOTION = JS / "motion.js"
BENTO = JS / "bento-shift.js"
BASE_HTML = REPO / "templates" / "base.html"


# ---------------------------------------------------------------------------
# Mirror of fx-gate.js computeFx(mq, nav) — keep in sync with the JS.
# mq: a callable(query) -> bool, as window.matchMedia(q).matches.
# nav: dict with optional connection/hardwareConcurrency/deviceMemory.
# ---------------------------------------------------------------------------
def compute_fx(mq, nav):
    if mq("(prefers-reduced-motion: reduce)"):
        return "none"
    cap = "rich"
    connection = nav.get("connection") or {}
    if connection.get("saveData"):
        cap = "lite"
    hc = nav.get("hardwareConcurrency")
    if isinstance(hc, (int, float)) and not isinstance(hc, bool) and hc <= 4:
        cap = "lite"
    dm = nav.get("deviceMemory")
    if isinstance(dm, (int, float)) and not isinstance(dm, bool) and dm <= 4:
        cap = "lite"
    return cap


def make_mq(reduced=False):
    queries = set()
    if reduced:
        queries.add("(prefers-reduced-motion: reduce)")
    return lambda q: q in queries


# ---------------------------------------------------------------------------
# 1. The gate script itself: self-hosted, CSP-clean, right inputs.
# ---------------------------------------------------------------------------
def test_fx_gate_exists_and_is_csp_clean():
    js = FX_GATE.read_text(encoding="utf-8")
    assert js.strip(), "fx-gate.js is empty"
    assert "sourceMappingURL" not in js, "fx-gate.js must not reference .map files"
    assert not re.search(r"https?://", js), (
        "fx-gate.js must be fully self-hosted — no CDN/absolute URLs"
    )


def test_fx_gate_reads_the_five_runbook_inputs():
    js = FX_GATE.read_text(encoding="utf-8")
    for needle in (
        "(prefers-reduced-motion: reduce)",   # reduced motion -> none
        "saveData",                            # Save-Data -> no richer than lite
        "hardwareConcurrency",                 # <= 4 cores -> lite
        "deviceMemory",                        # <= 4 GB -> lite
        "(hover: hover) and (pointer: fine)",  # -> data-fine
        '"rich"', '"lite"', '"none"',          # exactly the three tiers
    ):
        assert needle in js, f"fx-gate.js lost input/tier token: {needle}"


def test_fx_gate_sets_data_fine_only_for_fine_pointers():
    js = FX_GATE.read_text(encoding="utf-8")
    assert 'setAttribute("data-fine"' in js, (
        "fx-gate.js must expose the fine-pointer flag as html[data-fine]"
    )


# ---------------------------------------------------------------------------
# 2. Decision table (Python mirror — same comparisons as computeFx).
# ---------------------------------------------------------------------------
def test_reduced_motion_always_wins_as_none():
    nav = {"connection": {"saveData": True}, "hardwareConcurrency": 2,
           "deviceMemory": 2}
    assert compute_fx(make_mq(reduced=True), nav) == "none"


def test_healthy_device_is_rich():
    nav = {"hardwareConcurrency": 8, "deviceMemory": 8}
    assert compute_fx(make_mq(), nav) == "rich"
    assert compute_fx(make_mq(), {}) == "rich"  # unknowns must not demote


def test_save_data_caps_at_lite():
    assert compute_fx(make_mq(), {"connection": {"saveData": True},
                                  "hardwareConcurrency": 8}) == "lite"


def test_weak_hardware_caps_at_lite_boundary_is_four():
    assert compute_fx(make_mq(), {"hardwareConcurrency": 4}) == "lite"
    assert compute_fx(make_mq(), {"hardwareConcurrency": 5}) == "rich"
    assert compute_fx(make_mq(), {"deviceMemory": 4}) == "lite"
    assert compute_fx(make_mq(), {"deviceMemory": 8}) == "rich"


def test_unknown_hardware_types_do_not_demote():
    assert compute_fx(make_mq(), {"hardwareConcurrency": "many"}) == "rich"
    assert compute_fx(make_mq(), {"deviceMemory": None}) == "rich"


# ---------------------------------------------------------------------------
# 3. D-FX-GATE: the gate is the SINGLE source of capability decisions.
# ---------------------------------------------------------------------------
def test_gate_is_the_only_reduced_motion_check_in_js():
    offenders = []
    for path in sorted(JS.glob("*.js")):
        if "prefers-reduced-motion" in path.read_text(encoding="utf-8") \
                and path.name != "fx-gate.js":
            offenders.append(path.name)
    assert offenders == [], (
        f"effects must key off html[data-fx], not re-check reduced motion: "
        f"{offenders}"
    )


def test_effects_reference_the_gate_attributes():
    motion = MOTION.read_text(encoding="utf-8")
    bento = BENTO.read_text(encoding="utf-8")
    assert 'getAttribute("data-fx")' in motion
    assert 'getAttribute("data-fx")' in bento
    assert 'hasAttribute("data-fine")' in bento, (
        "bento shape-shift is pointer-driven: it must require [data-fine]"
    )


def test_bento_shift_is_rich_and_fine_pointer_only():
    bento = BENTO.read_text(encoding="utf-8")
    assert 'FX !== "rich"' in bento, (
        "decorative shape-shift must be rich-tier only (lite/none: off)"
    )
    # Fail-closed: a missing data-fx attribute must read as "none".
    assert '|| "none"' in bento


def test_motion_none_behaves_like_old_reduced_motion():
    """Under data-fx=none motion.js must take the exact paths the old
    prefersReduced flag took: no smooth-scroll handler, counters/quote/
    reveal rendered instantly (content visible, nothing animated)."""
    motion = MOTION.read_text(encoding="utf-8")
    assert motion.count("fxNone") >= 5, (
        "motion.js no longer branches every effect on the gate tier"
    )
    assert '|| "none"' in motion, (
        "motion.js must fail CLOSED when fx-gate.js is missing/blocked"
    )


# ---------------------------------------------------------------------------
# 4. Wiring: gate loads first, on every page, and cannot be dropped.
# ---------------------------------------------------------------------------
def test_fx_gate_loads_before_motion_outside_scripts_block():
    html = BASE_HTML.read_text(encoding="utf-8")
    gate_at = html.find("js/fx-gate.js")
    motion_at = html.find("js/motion.js")
    block_at = html.find("{% block scripts %}")
    assert gate_at != -1, "base.html must load fx-gate.js"
    assert motion_at != -1 and block_at != -1
    assert gate_at < block_at < motion_at, (
        "fx-gate.js must sit OUTSIDE {% block scripts %} (child overrides "
        "call block.super but must never be able to drop the gate) and "
        "before motion.js"
    )
    gate_tag = html[html.rfind("<script", 0, gate_at):gate_at]
    assert "defer" in html[html.rfind("<script", 0, gate_at): html.find(">", gate_at)], (
        "fx-gate.js must load deferred (CSP-safe external file, no inline)"
    )


def test_html_tag_carries_no_hardcoded_gate_attributes():
    """D-MOTION-SAFE: without JS no gate attribute may exist. Hardcoding
    data-fx on <html> would fake a capability decision for JS-blocked
    visitors and CSS keyed on [data-fx] could hide content."""
    html = BASE_HTML.read_text(encoding="utf-8")
    html_tag = html[html.find("<html"): html.find(">", html.find("<html")) + 1]
    assert "data-fx" not in html_tag and "data-fine" not in html_tag
