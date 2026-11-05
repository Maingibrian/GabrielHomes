"""F1 — token integrity proving tests (the ratchet).

Closes the r13-era token findings and turns them into permanent guardrails:

  1. Every ``var(--x)`` in static/css/*.css must resolve: ``--x`` is defined
     in tokens.css, in any css custom-property declaration, via an inline
     ``style="--x: …"`` in a template (the documented per-section --bg
     pattern, home.html), or via JS ``setProperty('--x', …)`` — or the usage
     carries a fallback. Undefined + fallback-less vars silently invalidate
     the whole declaration (this is what broke the map price-pin font).
  2. ``--font-body`` is gone (it was never defined); body text uses
     ``--font-sans``. ``--paper`` IS defined in tokens.css.
  3. px font sizes below the 13px floor are only allowed inside the
     documented allowlist below (reasons in DECISIONS D-LOOP-17c and the
     tokens.css comment). The total may only go DOWN.
  4. Hard-coded hex colours outside tokens.css are recorded as a baseline
     constant and may only go DOWN (ratchet toward full tokenisation).

Counting rules (kept deliberately simple and documented so future runs can
recompute the baselines with the same numbers):
  - px literals only; rem/em sizes flow from the root scale and are out of
    scope for the floor.
  - ``font-size: 12px`` and the first px number of a ``font: 700 12px/1 …``
    shorthand both count.
  - hex regex ``#[0-9a-fA-F]{3,8}`` also counts url(#clip) / gradient stop
    references — a deliberate over-count; consistent rules are what makes a
    ratchet, not semantic perfection.
"""
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CSS = REPO / "static" / "css"
TEMPLATES = REPO / "templates"
JS = REPO / "static" / "js"
TOKENS = CSS / "tokens.css"

FONT_FLOOR_PX = 13

# --- ratchet baselines, recorded at r17 (first green F1 run) --------------
HEX_BASELINE = 240   # hard-coded hex outside tokens.css; may only go DOWN
SUB13_BASELINE = 44  # px font sizes below 13px; may only go DOWN

# (file, px) -> reason. A sub-floor size whose (file, px) pair is not listed
# here is a failure. Listed pairs also have per-pair baselines (below) so
# they cannot quietly multiply.
FONT_FLOOR_ALLOWLIST = {
    ("dashboard.css", 10): "admin/staff dashboard micro labels — staff-only "
                           "tool surface, not visitor-facing",
    ("detail.css", 9): "maplibre attribution overlay + nearby-amenity mono "
                       "type tag",
    ("detail.css", 10): "amenities/nearby eyebrow micro labels "
                        "(uppercase mono)",
    ("detail.css", 11): "nearby-amenity small print",
    ("detail.css", 12): "nearby-amenities note small print",
    ("home.css", 10): "market band eyebrow micro labels (uppercase mono)",
    ("home.css", 11): "market band eyebrows + facts (uppercase mono)",
    ("home.css", 12): "founder role, card tags, fee label — uppercase mono "
                      "micro type",
    ("search.css", 9): "map property popup micro label (mono)",
    ("search.css", 10): "map attribution + mobile reset control + map "
                        "heading eyebrow",
    ("search.css", 11): "map filter chip mono label + listing-row type "
                        "eyebrow",
    ("search.css", 12): "map popup text, listing facts chips, mobile action "
                        "buttons, map price pin",
}

# per-(file, px) counts at r17 — listed pairs must not grow either
FONT_FLOOR_PAIR_BASELINE = {
    ("dashboard.css", 10): 2,
    ("detail.css", 9): 2,
    ("detail.css", 10): 5,
    ("detail.css", 11): 1,
    ("detail.css", 12): 1,
    ("home.css", 10): 7,
    ("home.css", 11): 6,
    ("home.css", 12): 7,
    ("search.css", 9): 2,
    ("search.css", 10): 5,
    ("search.css", 11): 2,
    ("search.css", 12): 4,
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def css_files():
    return {p.name: p.read_text(encoding="utf-8") for p in CSS.glob("*.css")}


def defined_custom_properties():
    """--x names defined anywhere: css declarations, template inline
    styles, JS setProperty."""
    defined = set()
    for text in css_files().values():
        defined |= set(re.findall(r"(--[a-z0-9-]+)\s*:", text))
    for path in TEMPLATES.rglob("*.html"):
        defined |= set(re.findall(
            r"(--[a-z0-9-]+)\s*:", path.read_text(encoding="utf-8")))
    for path in JS.glob("*.js"):
        defined |= set(re.findall(
            r"setProperty\(\s*['\"](--[a-z0-9-]+)", path.read_text(
                encoding="utf-8")))
    return defined


def sub_floor_sizes(css):
    """Counter[(file, '12px')] for every px size below FONT_FLOOR_PX."""
    found = Counter()
    for name, text in css.items():
        for rx in (r"font-size\s*:\s*(\d+(?:\.\d+)?)px",
                   r"(?<![a-z-])font\s*:[^;{}]*?(\d+(?:\.\d+)?)px"):
            for m in re.finditer(rx, text):
                if float(m.group(1)) < FONT_FLOOR_PX:
                    found[(name, m.group(1))] += 1
    return found


def hex_count_outside_tokens(css):
    return sum(
        len(re.findall(r"#[0-9a-fA-F]{3,8}", text))
        for name, text in css.items() if name != "tokens.css")


# ---------------------------------------------------------------------------
# 1. every var() resolves
# ---------------------------------------------------------------------------
def test_every_var_has_a_definition_or_fallback():
    defined = defined_custom_properties()
    broken = []
    for name, text in css_files().items():
        for m in re.finditer(r"var\(\s*(--[a-z0-9-]+)\s*(,[^)]*)?\)", text):
            if m.group(1) not in defined and not m.group(2):
                broken.append(f"{name}: {m.group(1)} (no definition, "
                              f"no fallback)")
    assert broken == [], (
        "undefined CSS variables silently invalidate their whole "
        "declaration: " + "; ".join(broken)
    )


def test_font_body_token_is_gone():
    offenders = [n for n, t in css_files().items() if "--font-body" in t]
    assert offenders == [], (
        f"--font-body was never defined; use --font-sans: {offenders}"
    )
    assert "--font-sans:" in TOKENS.read_text(encoding="utf-8"), (
        "--font-sans must stay defined in tokens.css"
    )


def test_paper_token_is_defined_and_single_sourced():
    tokens = TOKENS.read_text(encoding="utf-8")
    m = re.search(r"--paper\s*:\s*(#[0-9a-fA-F]{3,8})", tokens)
    assert m, ("--paper must be defined in tokens.css (was undefined; usages "
               "relied on inline fallbacks)")
    assert m.group(1).lower() == "#f3eee6", (
        "--paper must keep the value the old inline fallbacks carried "
        "(#f3eee6) — changing it is a DECISIONS entry, not a drive-by"
    )
    lingering = [
        name for name, text in css_files().items()
        if name != "tokens.css" and re.search(r"var\(--paper\s*,", text)
    ]
    assert lingering == [], (
        f"var(--paper, fallback) defeats the single source of truth: "
        f"{lingering}"
    )


# ---------------------------------------------------------------------------
# 2. the 13px floor: allowlist + ratchets
# ---------------------------------------------------------------------------
def test_sub_floor_sizes_are_allowlisted():
    css = css_files()
    unlisted = [
        f"{name} {px}px" for (name, px) in sub_floor_sizes(css)
        if (name, float(px)) not in FONT_FLOOR_ALLOWLIST
        and (name, int(px)) not in FONT_FLOOR_ALLOWLIST
    ]
    assert unlisted == [], (
        f"font sizes below {FONT_FLOOR_PX}px outside the documented "
        f"allowlist: {unlisted}"
    )
    empty = [k for k, reason in FONT_FLOOR_ALLOWLIST.items() if not reason]
    assert empty == [], f"allowlist entries need a reason: {empty}"


def test_sub_floor_total_ratchets_down():
    total = sum(sub_floor_sizes(css_files()).values())
    assert total <= SUB13_BASELINE, (
        f"sub-13px font-size count grew: {total} > baseline "
        f"{SUB13_BASELINE}. Raise sizes to the floor or shrink the "
        f"allowlist instead."
    )


def test_sub_floor_pairs_do_not_grow():
    sizes = sub_floor_sizes(css_files())
    grew = []
    for (name, px), count in sizes.items():
        key = (name, float(px)) if "." in px else (name, int(px))
        base = FONT_FLOOR_PAIR_BASELINE.get(key)
        if base is not None and count > base:
            grew.append(f"{name} {px}px: {count} > {base}")
    assert grew == [], f"allowlisted sub-floor pairs grew: {grew}"


# ---------------------------------------------------------------------------
# 3. the hex ratchet
# ---------------------------------------------------------------------------
def test_hex_count_outside_tokens_ratchets_down():
    count = hex_count_outside_tokens(css_files())
    assert count <= HEX_BASELINE, (
        f"hard-coded hex outside tokens.css grew: {count} > baseline "
        f"{HEX_BASELINE}. Add a token instead of another hex."
    )


# ---------------------------------------------------------------------------
# 4. docs are part of done
# ---------------------------------------------------------------------------
def test_tokens_css_documents_the_allowlist_and_floor():
    tokens = TOKENS.read_text(encoding="utf-8")
    assert "13px" in tokens, (
        "tokens.css must carry the font-floor allowlist comment (docs are "
        "part of done; see DECISIONS D-LOOP-17c)"
    )
