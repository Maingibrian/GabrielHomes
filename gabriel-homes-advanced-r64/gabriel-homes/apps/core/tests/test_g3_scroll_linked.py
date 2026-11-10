"""G3 — scroll-linked effects proving tests.

Runbook §6 G3 / SCORECARD G3: CSS scroll-linked (animation-timeline: view())
reveals behind @supports for the live named surfaces — home #nearby cards,
the /services/ rows and their media frames, the /about/ story collage
figure. Falls back to the existing IntersectionObserver reveal (motion.js,
untouched). Animated properties are transform / clip-path / opacity ONLY —
no layout shift. D-LOOP-31a:

  * every g3 selector is scoped under `html.motion-ready` — with JS blocked
    nothing is ever hidden or animated (D-MOTION-SAFE);
  * `html.motion-ready[data-fx="none"]` and prefers-reduced-motion kill the
    animations (fx=none behaves exactly like reduced motion, F2);
  * the bento grid is NOT targeted (H3/M4 own it — MET-frozen);
  * true parallax is deferred: the only collage markup is dormant
    (.story__* has no template) and .svc-row__media is a background-image
    box — a clip reveal ships instead (see D-LOOP-31a).
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture
def seeded_db(db):
    """Seed demo listings so the conditional home sections render — same
    isolation as test_h1_home_order / test_h4_section_rhythm."""
    from django.core.cache import cache
    cache.clear()
    call_command("seed_demo", no_images=True, target=20, verbosity=0,
                 i_know_this_is_demo=True)
    yield
    cache.clear()

REPO = Path(__file__).resolve().parents[3]
CSS = (REPO / "static" / "css" / "components.css").read_text()

# The live G3 surfaces (D-LOOP-31a mapping).
TARGETS = [
    ".nearby-card[data-reveal]",      # home #nearby
    ".svc-row[data-reveal]",          # /services/ rows
    ".svc-row__media",                # /services/ media frames (clip)
    ".about-story__figure[data-reveal]",  # /about/ story collage figure
]


def g3_block() -> str:
    m = re.search(r"@supports \(animation-timeline: view\(\)\) \{.*", CSS, re.S)
    assert m, "components.css must carry an @supports (animation-timeline: view()) block"
    block = m.group(0)
    # cut at the block's closing brace (first "\n}\n" after the start)
    return block[: block.index("\n}\n") + 3]


# ---------------------------------------------------------------------------
# 1. the scroll-linked enhancement exists, behind @supports
# ---------------------------------------------------------------------------
def test_supports_gate_and_view_timeline_present():
    block = g3_block()
    assert "animation-timeline: view()" in block
    assert "animation-range:" in block


def test_named_surfaces_are_targeted():
    block = g3_block()
    for sel in TARGETS:
        assert sel in block, f"G3 must target the live surface {sel}"


# ---------------------------------------------------------------------------
# 2. animated properties: transform / clip-path / opacity only
# ---------------------------------------------------------------------------
def test_keyframes_animate_only_allowed_properties():
    block = g3_block()
    for kf in re.findall(r"@keyframes\s+g3-[\w-]+\s*\{(?:[^{}]*\{[^{}]*\})+[^{}]*\}", block):
        body = re.sub(r"@keyframes[\s\S]*?\{", "", kf, count=1)
        props = set(re.findall(r"([a-z-]+)\s*:", body))
        assert props <= {"transform", "clip-path", "opacity"}, (
            f"G3 keyframes animate non-whitelisted properties: {props - {'transform', 'clip-path', 'opacity'}}"
        )


def test_no_layout_shift_properties_in_g3_block():
    block = g3_block()
    for banned in ("width:", "height:", "margin", "padding", "top:", "left:", "position:"):
        assert banned not in block.replace("animation-range", ""), (
            f"G3 block must not animate/layout-shift via {banned}"
        )


# ---------------------------------------------------------------------------
# 3. the IO fallback stays; D-MOTION-SAFE scoping
# ---------------------------------------------------------------------------
def test_io_fallback_untouched():
    assert "html.motion-ready [data-reveal] {" in CSS
    assert "html.motion-ready [data-reveal].is-visible {" in CSS
    motion = (REPO / "static" / "js" / "motion.js").read_text()
    assert "new IntersectionObserver" in motion, "IO fallback must stay"


def test_every_g3_selector_is_motion_ready_scoped():
    """With JS blocked there is no `motion-ready` class and thus no g3
    animation and no hidden content — D-MOTION-SAFE."""
    block = g3_block()
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)  # strip comments
    rules = re.findall(r"([^{}]+)\{", block)
    for raw in rules:
        sel = raw.strip("}\t\n ").strip()
        if (not sel or sel.startswith(("@keyframes", "@supports", "@media"))
                or sel in ("from", "to")):
            continue
        assert "html.motion-ready" in sel, (
            f"G3 rule not scoped under html.motion-ready: {sel!r}"
        )


def test_fx_none_and_reduced_motion_kill_g3():
    block = g3_block()
    assert re.search(r'html\.motion-ready\[data-fx="none"\][^{]*\{[^}]*animation:\s*none', block), (
        "fx=none must disable every g3 animation"
    )
    assert "animation: none" in block


def test_bento_is_never_targeted():
    block = g3_block()
    assert "bento" not in block, "H3/M4 own the bento grid — G3 must not touch it"


# ---------------------------------------------------------------------------
# 4. the named surfaces really exist in the rendered pages
# ---------------------------------------------------------------------------
def _get(path: str) -> str:
    r = Client().get(path)
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    return r.content.decode()


def test_surfaces_render_on_their_pages(seeded_db):
    home, services, about = _get("/"), _get("/services/"), _get("/about/")
    assert re.search(r'class="nearby-card[^"]*"[^>]*data-reveal', home)
    assert 'class="svc-row" data-reveal' in services
    assert re.search(r'class="about-story__figure[^"]*"[^>]*data-reveal', about)
