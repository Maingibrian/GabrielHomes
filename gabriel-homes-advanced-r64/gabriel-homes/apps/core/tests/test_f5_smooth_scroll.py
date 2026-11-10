"""F5 — smooth scroll (Lenis) proving tests.

Binary checks (SCORECARD F5):
1. Lenis self-hosted under static/vendor/lenis/ per the hygiene rules:
   no sourceMappingURL comment, LICENSE present, pinned SRI in base.html
   that matches the actual file bytes (recomputed here — drift fails).
2. Initialises only under fx=rich, off for touch (fine-pointer + hover
   guard runs before `new Lenis`).
3. Anchors, find-in-page, focus and keyboard scrolling still work:
   the motion.js anchor handler routes through ghScrollTo with a native
   fallback, search-map.js keeps its native fallback, and the vendored
   lib adds no keydown hijack (smooth-scroll.js never touches keydown —
   keyboard/find-in-page stay native).
"""
import base64
import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
VENDOR = REPO / "static" / "vendor" / "lenis" / "lenis.min.js"
INIT = REPO / "static" / "js" / "smooth-scroll.js"
BASE = (REPO / "templates" / "base.html").read_text(encoding="utf-8")
MOTION = (REPO / "static" / "js" / "motion.js").read_text(encoding="utf-8")
SEARCH_MAP = (REPO / "static" / "js" / "search-map.js").read_text(encoding="utf-8")
CSS = (REPO / "static" / "css" / "base.css").read_text(encoding="utf-8")


def test_vendor_selfhosted_and_hygienic():
    assert VENDOR.exists() and VENDOR.stat().st_size > 10_000, (
        "lenis.min.js must be vendored (self-hosted, non-trivial)")
    src = VENDOR.read_text(encoding="utf-8")
    assert "sourceMappingURL" not in src, "HYG: no sourceMappingURL comments"
    assert (REPO / "static" / "vendor" / "lenis" / "LICENSE").exists(), (
        "vendored library must ship its LICENSE")


def test_sri_hash_pinned_and_current():
    tag = re.search(
        r'<script[^>]*vendor/lenis/lenis\.min\.js[^>]*>', BASE)
    assert tag, "base.html must load the vendored lenis script"
    attrs = tag.group(0)
    m = re.search(r'integrity="([^"]+)"', attrs)
    assert m, "script tag must pin an integrity hash"
    algo, _, expected = m.group(1).partition("-")
    assert algo == "sha384", "SRI must be sha384"
    digest = hashlib.sha384(VENDOR.read_bytes()).digest()
    actual = base64.b64encode(digest).decode()
    assert expected == actual, (
        "pinned SRI does not match the vendored bytes — recompute or re-vendor")
    assert "crossorigin" in attrs, "crossorigin required with integrity"
    assert "defer" in attrs, "vendor script must be deferred"


def test_init_only_rich_and_no_touch():
    src = INIT.read_text(encoding="utf-8")
    rich = src.index("data-fx")
    fine = src.index("pointer: fine")
    hover = src.index("hover: hover")
    new_lenis = src.index("new Lenis")
    assert rich < new_lenis, "fx gate must run before Lenis is constructed"
    assert fine < new_lenis and hover < new_lenis, (
        "fine-pointer + hover guard (off for touch) must run before Lenis")
    assert src.count("new Lenis") == 1, "exactly one construction site"
    # D-LOOP-16a: fx-gate.js is the only script allowed to mention
    # prefers-reduced-motion — the init file must NOT re-check it.
    assert "prefers-reduced-motion" not in src, (
        "reduced-motion must stay centralised in fx-gate.js (D-LOOP-16a)")


def test_programmatic_scroll_routes_through_lenis_with_native_fallback():
    src = INIT.read_text(encoding="utf-8")
    assert "window.ghScrollTo" in src and "scrollTo" in src, (
        "helper must expose ghScrollTo and drive lenis.scrollTo")
    assert "scrollIntoView" in src and '"auto"' in src, (
        "native fallback (fx-aware behaviour) must live in the helper")
    # frozen call sites route through the helper; no direct programmatic
    # scroll and no local fx copy remains in search-map.js
    assert "ghScrollTo(row, 'center')" in SEARCH_MAP, "pin->row scroll must use the helper"
    assert "ghScrollTo(mapEl, 'start')" in SEARCH_MAP, "Map pill scroll must use the helper"
    assert "scrollIntoView(" not in SEARCH_MAP, (
        "every programmatic scroll in search-map.js goes through the helper")
    assert "smoothOk" not in SEARCH_MAP, (
        "fx awareness is centralised in the helper (dead local copy removed)")


def test_anchors_and_keyboard_untouched():
    # motion.js anchor handler: fixed selector + helper routing + native fallback
    assert "a[href^=\"#\"]" in MOTION, (
        "anchor handler must use a valid selector (weref/aref typo fixed)")
    assert "aref" not in MOTION, "invalid 'aref^' selector must be gone"
    assert "ghScrollTo(target" in MOTION, "anchor clicks route through the helper"
    assert "scrollIntoView" in MOTION, "native anchor fallback must stay"
    # keyboard / find-in-page stay native: the init file adds no key handling
    assert "keydown" not in INIT.read_text(encoding="utf-8"), (
        "Lenis init must not hijack the keyboard — find-in-page and arrow keys stay native")
    # wheel-only: no touchmove / no pointerdown listeners in our init
    src = INIT.read_text(encoding="utf-8")
    assert "touchmove" not in src and "touchstart" not in src, "touch stays native"


def test_lenis_css_rules_no_double_smooth():
    assert ".lenis.lenis-smooth" in CSS and "scroll-behavior: auto" in CSS, (
        "when Lenis drives the scroller, native smooth must stand down")
    assert "html.lenis" in CSS, "official Lenis height rules present"
