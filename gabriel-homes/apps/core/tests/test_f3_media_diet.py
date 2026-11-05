"""F3 — image & video diet proving tests.

Binary checks (SCORECARD F3):
1. No static image over 250KB (walks static/; lists offenders).
2. WebP where practical: the search market-filter cards and the home hero
   slides ship as .webp (the two biggest wins); seed-source stock images
   stay JPG but re-encoded (documented, D-LOOP-21b).
3. Every <img> in shipped templates carries width and height.
4. static/video/hero-loop.mp4 is unreferenced (deferred to H2, D-LOOP-21a)
   OR every reference is gated fx=rich && !Save-Data with a poster.
5. HYG-1: the five home.html section blocks H1 moved (commit/faq/cta/
   cards+card/collage/about/btn-light/link) leave NO dead rules in home.css
   (ratchet: the selectors may never return without live markup).
Also a total-bytes ratchet: static image bytes may only go DOWN
(baseline recorded pre-diet at r21, tightened post-diet).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
STATIC = REPO / "static"
TEMPLATES = REPO / "templates"

MAX_IMAGE_BYTES = 250 * 1024
# Recorded 6,161,625 B pre-diet (r21 survey); tightened post-diet to the
# exact 4,185,045 B. May only go DOWN.
IMAGE_BYTES_BASELINE = 4_185_045

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}

# HYG-1: full class tokens whose markup is gone from every template.
DEAD_HV2 = {
    ".hv2-commit", ".hv2-collage", ".hv2-faq", ".hv2-cta", ".hv2-cards",
    ".hv2-card", ".hv2-about", ".hv2-btn-light", ".hv2-link",
}


def _static_images():
    return [p for p in STATIC.rglob("*")
            if p.suffix.lower() in IMG_EXTS and p.is_file()]


def test_no_static_image_over_250kb():
    offenders = sorted(
        (p for p in _static_images() if p.stat().st_size > MAX_IMAGE_BYTES),
        key=lambda p: p.stat().st_size, reverse=True)
    assert offenders == [], (
        "static images over 250KB (convert to WebP, re-encode, or delete): "
        + ", ".join(f"{p.relative_to(REPO)} {p.stat().st_size // 1024}KB"
                    for p in offenders))


def test_static_image_bytes_ratchet():
    total = sum(p.stat().st_size for p in _static_images())
    assert total <= IMAGE_BYTES_BASELINE, (
        f"static image bytes grew: {total} > baseline {IMAGE_BYTES_BASELINE}. "
        "Diet, don't add.")


def test_every_img_in_templates_has_dimensions():
    missing = []
    for p in sorted(TEMPLATES.rglob("*.html")):
        html = p.read_text(encoding="utf-8")
        for m in re.finditer(r"<img\b[^>]*>", html):
            tag = m.group(0)
            if "width=" not in tag or "height=" not in tag:
                missing.append(f"{p.relative_to(REPO)}: {tag[:80]}")
    assert missing == [], (
        "<img> without width/height (CLS risk): " + "; ".join(missing))


def test_market_filter_cards_and_hero_slides_use_webp():
    search = (TEMPLATES / "listings" / "search.html").read_text(encoding="utf-8")
    for name in ("mombasa-villa", "green-apartments", "pool-villa-night"):
        assert f"img/stock/{name}.webp" in search, (
            f"search.html must serve img/stock/{name}.webp")
        assert f"img/stock/{name}.jpg" not in search, (
            f"search.html still references the heavy JPG {name}.jpg")
    home = (TEMPLATES / "core" / "home.html").read_text(encoding="utf-8")
    for n in (1, 2, 3, 4):
        assert f"img/real/hero-slide-{n}.webp" in home, (
            f"home.html hero slide {n} must be WebP")
    assert "hero-slide-" not in re.sub(
        r"hero-slide-\d\.webp", "", home), (
        "home.html still references a non-WebP hero slide")


def test_hero_loop_video_contract():
    """Unreferenced (deferred to H2, D-LOOP-21a) — or every reference is
    gated fx=rich && !Save-Data with a poster. The gate strings must appear
    in the same file that references the video."""
    video = STATIC / "video" / "hero-loop.mp4"
    if not video.exists():
        return  # documented removal is also a valid end state
    refs = []
    for p in list((REPO / "templates").rglob("*.html")) + list(
            (STATIC / "js").glob("*.js")):
        if "hero-loop" in p.read_text(encoding="utf-8"):
            refs.append(p)
    if not refs:
        return  # deferred: unreferenced is the accepted F3 end state
    for p in refs:
        text = p.read_text(encoding="utf-8")
        assert "data-fx" in text and "Save-Data" in text, (
            f"{p.name} references hero-loop without the fx=rich && "
            "!Save-Data gate")
        assert "poster" in text, f"{p.name} references hero-loop without a poster"


def test_dead_hv2_blocks_purged():
    css = (STATIC / "css" / "home.css").read_text(encoding="utf-8")
    # class selectors only (leading dot) — @keyframes names and
    # animation: references are not classes and must not be flagged
    live = set(re.findall(r"\.hv2-[a-z0-9_-]+", css))
    tpl_classes = set()
    for p in TEMPLATES.rglob("*.html"):
        tpl_classes |= set(re.findall(r"hv2-[a-z0-9_-]+", p.read_text(
            encoding="utf-8")))
    orphaned = sorted(c for c in live if c.lstrip(".") not in tpl_classes)
    assert orphaned == [], (
        "home.css carries rules for markup that no longer exists (HYG-1): "
        + ", ".join(orphaned))
