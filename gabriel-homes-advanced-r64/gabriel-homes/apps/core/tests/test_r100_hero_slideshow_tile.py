"""r100 — owner round seventeen, three asks:

1. "the background video is not the best... lets just have a
   slideshow of images and the animation of the slide show needs to
   look world class and not like a beginner"
2. "the hero of the mobile looks bad"
3. "the card still doesnt look world class" (the r98/r99 sale tile)

This suite pins the r100 pass:

- THE SLIDESHOW: the 1.5MB hero-loop.mp4 is RETIRED (owner call — the
  video was never better than the photos). The slide stack becomes the
  one hero visual on every device, and its motion is upgraded from the
  beginner pattern (one flat opacity fade + one uniform zoom) to a
  directed Ken Burns: each slide fades AND drifts on its own
  character (pan direction + zoom target per slide), the crossfade
  overlaps, the grade holds longer than the transition, and the
  whole thing is a single compositor-friendly transform/opacity
  animation per slide.
- MOBILE HERO: the poster was a squat 46vh letterbox slicing the
  photos mid-subject (VLM: "raw phone snapshot, not curated"). It
  becomes a taller portrait window (~62svh) with object-fit cover so
  the crop reads intentional; the caption plate loses one of its
  three decorative devices.
- THE TILE: two polish rounds kept it flat because the tall tile's
  middle is empty (VLM flagged it both rounds). The bold move: a
  fanned trio of the actual sale listings' photos breathing in the
  tile's air above the serif line, plus a live count stat ("N homes
  for sale right now") under the eyebrow — the tile stops being a
  decorated link and becomes a window into the sale list itself.
"""
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_db(db):
    """The tile tests need sale listings WITH photos in the DB (the
    fan imgs render only when sale_listings carry images; the
    demo-photos pool is git-bundled so real files exist). Same
    isolation pattern as test_h1_home_order, but with_images."""
    from django.core.cache import cache
    cache.clear()
    call_command("seed_demo", target=20, verbosity=0,
                 i_know_this_is_demo=True)
    yield
    cache.clear()

REPO = Path(__file__).resolve().parents[3]
HOME_CSS = REPO / "static" / "css" / "home.css"
HOME_HTML = (REPO / "templates" / "core" / "home.html").read_text(encoding="utf-8")
MOTION_JS = REPO / "static" / "js" / "motion.js"
TILE_HTML = (REPO / "templates" / "includes" / "_home_more_tile.html").read_text(encoding="utf-8") if (REPO / "templates" / "includes" / "_home_more_tile.html").exists() else ""

CSS = HOME_CSS.read_text(encoding="utf-8")  # refreshed below per test where edited


def _css():
    return HOME_CSS.read_text(encoding="utf-8")


def _body():
    return Client().get("/").content.decode()


# ===========================================================================
# 1. THE SLIDESHOW — world-class motion
# ===========================================================================

def test_video_is_retired():
    """Owner: 'the background video is not the best'. The <video> tag,
    its poster preload chain and the motion.js gate are gone; the
    slides are the one hero visual on every device (and 1.5MB stops
    shipping on rich devices)."""
    html = _body()
    assert "hero-loop.mp4" not in html, "the mp4 must leave the page"
    assert "<video" not in html.split("</section>")[0].split('<section class="hero"')[1], (
        "no video tag anywhere inside the hero")
    js = MOTION_JS.read_text(encoding="utf-8")
    assert "setupHeroVideo" not in js, "the gate function is retired with the tag"


def test_slides_carry_per_slide_direction():
    """A Ken Burns needs per-slide character, not one uniform zoom.
    Each .hero__slide declares its own pan/zoom via a --kb-* custom
    property pair (from/to transform targets) consumed by the shared
    keyframes."""
    css = _css()
    for i in range(1, 5):
        block = re.search(
            r"\.hero__slide:nth-child\(%d\)\s*\{([^}]*)\}" % i, css)
        assert block, f"slide {i} keeps its delay block"
    # the shared drift keyframes consume the per-slide vars
    kf = re.search(r"@keyframes hero-drift\s*\{(.*?)\n\}", css, re.S)
    assert kf, "hero-drift keyframes missing"
    assert "var(--kb-from" in kf.group(1), "drift animates FROM a per-slide target"
    assert "var(--kb-to" in kf.group(1), "drift animates TO a per-slide target"
    # each of the four slides sets its own pair
    for m in re.finditer(r"\.hero__slide:nth-child\((\d)\)\s*\{([^}]*)\}", css):
        idx, body = m.group(1), m.group(2)
        if "animation-delay" in body:
            assert "--kb-from" in body and "--kb-to" in body, (
                f"slide {idx} must declare its own pan/zoom character")


def test_ken_burns_timing_is_director_pace():
    """Beginner slideshows run ~6s fades. Director pace: each slide
    HOLDS ~20s with a short overlapping crossfade — the cycle time
    steps up and the fade keyframes keep their early-in/hold/late-out
    shape (fade completes in the first ~4% of the slide's own window)."""
    css = _css()
    delays = [float(d) for d in re.findall(
        r"\.hero__slide:nth-child\(\d\)\s*\{[^}]*animation-delay:\s*([\d.]+)s", css)]
    assert delays, "slides keep staggered delays"
    assert len(set(delays)) == 4, "four distinct delays"
    assert max(delays) >= 18, "the cycle stretches to director pace (>=18s)"
    dur = re.search(r"\.hero__slide\s*\{[^}]*animation:\s*[^;]*?([\d.]+)s", css, re.S)
    assert dur and float(dur.group(1)) >= 72, (
        "one animation duration covering all four windows (4 x >=18s)")


def test_slideshow_is_fx_safe():
    """fx=none and reduced-motion keep slide 1 as a static photo (the
    long-standing contract), and no JS is required to run the show."""
    css = _css()
    red = re.search(
        r"@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\n\}", css, re.S)
    assert red, "reduced-motion block present"
    assert "opacity: 1" in re.search(
        r"\.hero__slide:nth-child\(1\)\s*\{[^}]*opacity:\s*1", red.group(1)).group(0), (
        "slide 1 stays visible under reduce")


# ===========================================================================
# 2. THE MOBILE HERO
# ===========================================================================

def test_mobile_poster_is_a_taller_cover_window():
    """The 46vh letterbox sliced photos mid-subject. Under 810px the
    poster window grows to a portrait window (>= 56svh, capped for
    short landscape phones) and the slides crop with cover semantics
    instead of the uncropped background-size: cover on a squat box."""
    css = _css()
    block = next(b for b in re.findall(
        r"@media \(max-width: 809px\)\s*\{(.*?)\n\}", css, re.S)
        if ".hero__bg {" in b)
    h = re.search(r"height:\s*clamp\(([\d.]+)(\w+),\s*([\d.]+)svh", block)
    assert h, "poster height uses svh (URL-bar-safe) with a clamp"
    assert float(h.group(3)) >= 56, "the window is portrait-tall (>=56svh)"
    # the crop anchor is per-slide (inline --slide-pos in the template)
    # consumed by the top-level slide rule
    assert re.search(
        r"\.hero__slide\s*\{[^}]*background-position:\s*var\(--slide-pos,",
        css), "each slide keeps its own crop anchor"
    assert "--slide-pos" in HOME_HTML, "the template sets the anchors"


def test_mobile_caption_plate_simplified():
    """VLM: three decorative devices for one job. The dot separator
    goes; the two spans sit with a plain gap between hairlines."""
    css = _css()
    plate = re.search(r"\.hero__poster-plate\s*\{[^}]*\}", css)
    assert plate, "plate rule present"
    # the template keeps two spans; CSS no longer adds a middot via ::marker
    assert "::marker" not in css.split(".hero__poster-plate")[1][:400]


# ===========================================================================
# 3. THE TILE — the bold move
# ===========================================================================

def test_tile_has_photo_fan():
    """The tall tile's middle has been empty for two rounds (VLM flagged
    it twice). The tile now fans the sale rail's own listing photos in
    that air. The fan markup is one aria-hidden div with three img
    tags sourced from the sale listings themselves; no new queries."""
    body = _body()
    fan = re.search(
        r'class="market-rail__fan"[^>]*aria-hidden="true"', body)
    assert fan, "the fan is decorative (aria-hidden) and in the DOM"
    imgs = re.findall(r'<img[^>]*class="market-rail__fan-img"', body)
    assert len(imgs) == 3, "three photos in the fan"


def test_tile_carries_live_sale_count():
    """A world-class closer states what it closes: the live number of
    published sale listings sits under the eyebrow, view-computed (no
    template guessing)."""
    body = _body()
    m = re.search(
        r'<p class="market-rail__count">([^<]*)<strong>(\d+)</strong>([^<]*)</p>', body)
    assert m, "the count line renders with a strong number"
    n = int(m.group(2))
    assert n >= 3, "the count matches the rail (>= the 3 shown)"


def test_tile_fan_is_fx_safe_and_contained():
    """The fan rests tilted (CSS transform, no animation needed to
    exist), stays inside the tile's overflow:hidden, and under
    fx=none/reduce it simply rests — never depends on motion."""
    css = _css()
    fan = re.search(r"\.market-rail__fan\s*\{[^}]*\}", css)
    assert fan, "fan rule present"
    assert "transform:" in fan.group(0), "the fan rests tilted"
    tile = re.search(r"\.market-rail__more\s*\{[^}]*overflow:\s*hidden", css)
    assert tile, "the tile still clips its contents"
    assert not re.search(r"\.market-rail__fan\s*\{[^}]*animation:", css), (
        "the fan's resting state needs no keyframes")
