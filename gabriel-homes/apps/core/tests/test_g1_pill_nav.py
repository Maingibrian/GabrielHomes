"""G1 — floating pill nav proving tests.

Binary checks (SCORECARD G1):
1. Hides on scroll-down, returns on scroll-up; the behaviour is active
   under fx lite or rich only (fx-none / missing gate keeps the header
   permanently visible — D-MOTION-SAFE).
2. Full nav from 1024px up (hamburger hands over at the same width).
3. Mobile-menu inline styles moved to CSS classes (no style= in the
   header include).
4. Escape closes the menu; skip link present and first focusable.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MOTION = (REPO / "static" / "js" / "motion.js").read_text(encoding="utf-8")
COMPONENTS = (REPO / "static" / "css" / "components.css").read_text(encoding="utf-8")
BASE = (REPO / "templates" / "base.html").read_text(encoding="utf-8")
HEADER = (REPO / "templates" / "includes" / "_header.html").read_text(encoding="utf-8")

HIDDEN_CLASS = "nav--hidden"
AUTOHIDE_FN = "setupNavAutoHide"


def test_hide_return_is_fx_gated():
    # The scroll-direction logic must sit behind the capability gate:
    # lite or rich get the behaviour, none (and a missing gate) never do.
    assert "fxNone" in MOTION, "motion.js must keep the F2 gate variable"
    setup = re.search(r"function %s\(\) \{.*?\n  \}" % AUTOHIDE_FN, MOTION, re.S)
    assert setup, "setupNavAutoHide must exist"
    body = setup.group(0)
    assert HIDDEN_CLASS in body, "hide/return must toggle the nav hidden class"
    assert "lastY" in body and "scrollY" in body, (
        "hide/return must compare scroll direction")
    # Strict gate: the auto-hide setup is called behind an fxNone check.
    assert re.search(
        r"if\s*\(\s*!?fxNone[^)]*\)\s*%s\(\)" % AUTOHIDE_FN, MOTION
    ), "setupNavAutoHide() must be called behind the fx gate (lite/rich only)"


def test_hide_is_transform_only_and_css_backed():
    # CSS: the hidden state is a transform on the sticky header, never
    # display:none (keeps focusability and avoids layout shift).
    assert re.search(
        r"\.site-header\.%s\s*\{[^}]*transform:[^;]*translateY\(-100%%\)" % HIDDEN_CLASS,
        COMPONENTS), "CSS must define .site-header.nav--hidden as translateY(-100%)"
    header_rule = re.search(r"^\.site-header \{[^}]*\}", COMPONENTS, re.M | re.S)
    assert header_rule and "transform" in header_rule.group(0), (
        "the header transition must cover transform (smooth hide/return)")
    # D-MOTION-SAFE: without JS the class is never present, so the header
    # stays visible — assert the CSS never hides the header unconditionally.
    assert not re.search(r"^\.site-header \{[^}]*display:\s*none", COMPONENTS, re.M | re.S)


def test_full_nav_from_1024px():
    # Full nav (and hamburger handover) at 1024px, not 1200px.
    nav_block = re.search(
        r"@media \(min-width: (\d+)px\) \{\s*\.site-header__nav \{ display: flex; \}",
        COMPONENTS)
    assert nav_block, "the nav display:flex media query must exist"
    assert nav_block.group(1) == "1024", (
        f"full nav must start at 1024px, got {nav_block.group(1)}px")
    burger_block = re.search(
        r"@media \(min-width: (\d+)px\) \{\s*\.site-header__hamburger \{ display: none; \}",
        COMPONENTS)
    assert burger_block and burger_block.group(1) == "1024", (
        "hamburger must hand over to the full nav at the same 1024px")


def test_mobile_menu_inline_styles_moved_to_css():
    # No style= attributes anywhere in the header include.
    styles = re.findall(r'style="[^"]*"', HEADER)
    assert not styles, f"inline styles must move to CSS classes: {styles}"
    # The classes that replaced them exist in components.css.
    for cls in ("mobile-menu__index", "mobile-menu__signout"):
        assert f".{cls}" in COMPONENTS, f"components.css must define .{cls}"


def test_escape_closes_menu():
    assert re.search(
        r'key === "Escape"[^;]*menu\.classList\.contains\("is-open"\)', MOTION
    ) or ('"Escape"' in MOTION and "is-open" in MOTION), (
        "Escape must close the open mobile menu")


def test_skip_link_first_focusable():
    assert 'class="skip-link"' in BASE and 'href="#main"' in BASE
    assert 'id="main"' in BASE, "the skip target must exist"
    # The skip link sits before the header include — first focusable element.
    assert BASE.index('class="skip-link"') < BASE.index("{% block header %}"), (
        "skip link must precede the header include in the DOM")
