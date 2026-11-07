#!/usr/bin/env python3
"""r60 — generate the coast palm sentinels for the listings page.

Owner request (owner round ten): "on the white sides next to each
listings generate a coconut tree... it will be stagnant parallax up to
the start of the footer."

Two coconut palms — one per white gutter of the results band — drawn
procedurally in the r46 house style (scripts/r46_palm_field.py): every
frond is an arching rachis (cubic bezier) with slender leaflets left
and right along it, leaflet length peaking mid-frond and tapering to
the tip, each with a small deterministic jitter so nothing reads
mechanical. The r46 field was a faint clay watermark; these sentinels
stand alone in the gutters, so they are real palms — but they carry
NO colours of their own: every layer is a .palm-* class hook styled in
search.css from the existing tokens (zero hex there, D-LOOP-38a).

Anatomy per tree, bottom-up:
  mound     two-hump sand mound, darker under-rim, fallen coconuts
  grass     jittered blades fanning off the mound (leaflet geometry)
  trunk     curved, tapering, ring-notched; the belly bows away from
            the lean; each tree leans TOWARD the listings (content)
  boot      dark frond-base sheath where trunk meets crown
  crown     9 fronds (left tree) / 8 (right, stockier) in three depth
            layers — back (deepest shade), mid, front (sun-lit
            droopers). Two canonical frond shapes per tree (arch +
            heavy droop) are defined ONCE in <defs> and placed with
            one-line <use> transforms (rotate / scale / mirror), the
            same economy trick as the r46 tile. Mirroring matters:
            a left-pointing frond is the ARCH MIRRORED, not rotated
            180 degrees (rotation would arch it downward).
  nuts      the coconut cluster hanging just under the crown

Byte economy: canonical fronds in <defs> + <use> placements ≈ 4 KiB
per tree inline in the page (no extra request, cache-free freshness).

Deterministic: random.seed(60) for the left palm, 61 for the right.
Output: templates/listings/_palms.html
  --preview  also write palms-preview.html beside this script —
             standalone page with BAKED preview colours, for eyeballing
             only; never shipped, never linked.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "templates" / "listings" / "_palms.html"
PREVIEW = Path(__file__).resolve().parent / "palms-preview.html"

FROND_LEN = 150.0            # canonical rachis length before scaling
LEAFLETS = 20                # sample points per rachis (x2 leaflets)

# canonical frond shapes: cubic bezier control points as fractions of L
# (base at origin, arching up, tip drooping back down — the palm arch)
ARCH = ((0.10, -0.44), (0.50, -0.82), (1.00, -0.58))
DROOP = ((0.16, -0.30), (0.58, -0.50), (1.04, -0.08))


# --------------------------------------------------------------------------
# geometry helpers (r46 lineage)
# --------------------------------------------------------------------------
def bezier(p0, p1, p2, p3, t):
    mt = 1.0 - t
    return (
        mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
        + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
        mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
        + 3 * mt * t * t * p2[1] + t ** 3 * p3[1],
    )


def qbez(p0, p1, p2, t):
    """Quadratic bezier point at t."""
    u = 1.0 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def bezier_tangent(p0, p1, p2, p3, t):
    mt = 1.0 - t
    dx = (3 * mt * mt * (p1[0] - p0[0]) + 6 * mt * t * (p2[0] - p1[0])
          + 3 * t * t * (p3[0] - p2[0]))
    dy = (3 * mt * mt * (p1[1] - p0[1]) + 6 * mt * t * (p2[1] - p1[1])
          + 3 * t * t * (p3[1] - p2[1]))
    return math.atan2(dy, dx)


def leaflet_path(ax, ay, angle, length, curl):
    """A slender pointed leaf: two quadratic curves base -> tip, bowed
    by `curl` (the natural droop of a palm leaflet). r46 verbatim."""
    tx = ax + math.cos(angle) * length
    ty = ay + math.sin(angle) * length
    mx = ax + math.cos(angle) * length * 0.45
    my = ay + math.sin(angle) * length * 0.45
    w = length * 0.062
    nx = math.cos(angle + math.pi / 2) * w
    ny = math.sin(angle + math.pi / 2) * w
    cx = math.cos(angle) * length * 0.28 + math.cos(angle + curl) * length * 0.10
    cy = math.sin(angle) * length * 0.28 + math.sin(angle + curl) * length * 0.10
    return (
        f"M{ax:.1f},{ay:.1f}"
        f"Q{mx + nx + cx:.1f},{my + ny + cy:.1f} {tx:.1f},{ty:.1f}"
        f"Q{mx - nx + cx:.1f},{my - ny + cy:.1f} {ax:.1f},{ay:.1f}Z"
    ), (tx, ty)


def build_frond(shape, rng):
    """One canonical frond, base at the origin, arching up and over to
    the right. Returns (d_strings, outline_points) — outline for the
    placement bbox math."""
    L = FROND_LEN
    p0 = (0.0, 0.0)
    p1 = (shape[0][0] * L, shape[0][1] * L)
    p2 = (shape[1][0] * L, shape[1][1] * L)
    p3 = (shape[2][0] * L, shape[2][1] * L)

    ds, outline = [], []
    for i in range(LEAFLETS):
        t = (i + 1) / (LEAFLETS + 1)
        ax, ay = bezier(p0, p1, p2, p3, t)
        theta = bezier_tangent(p0, p1, p2, p3, t)
        profile = math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.85
        length = L * 0.42 * (0.22 + 0.78 * profile)
        for side in (-1, 1):
            opening = math.radians(46 - 22 * t) + rng.uniform(-0.05, 0.05)
            sag = math.radians(6 + 10 * t) * side
            angle = theta + side * opening + sag
            jitter = rng.uniform(-0.03, 0.03)
            d, tip = leaflet_path(ax, ay, angle + jitter, length,
                                  curl=side * math.radians(18 + 8 * t))
            ds.append(d)
            outline.append(tip)

    # rachis: a tapering polygon strip along the same curve
    samples = [bezier(p0, p1, p2, p3, i / 24) for i in range(25)]
    left, right = [], []
    for i, (sx, sy) in enumerate(samples):
        t = i / 24
        theta = bezier_tangent(p0, p1, p2, p3, t)
        wdt = L * (0.017 - 0.013 * t)
        nx, ny = math.cos(theta + math.pi / 2), math.sin(theta + math.pi / 2)
        left.append((sx + nx * wdt, sy + ny * wdt))
        right.append((sx - nx * wdt, sy - ny * wdt))
        outline.append((sx + nx * wdt, sy + ny * wdt))
    rachis = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in left + right[::-1]) + "Z"
    return [rachis] + ds, outline


def trunk_geometry(base, top, w0, w1, belly):
    """Curved tapering trunk: a cubic centerline (the belly bows away
    from the lean, concentrated toward the crown, the way a leaning
    palm carries its curve), offset into a tapering polygon strip —
    the same construction as the frond rachis, so trunk and frond
    share one drawing language. Ring notches sag with gravity.
    Returns (trunk_d, rings_d, corner_points)."""
    dx, dy = top[0] - base[0], top[1] - base[1]
    h = math.hypot(dx, dy)
    d = (dx / h, dy / h)
    n = (-d[1], d[0])                       # one perpendicular
    c1 = (base[0] + d[0] * h * 0.30 + n[0] * belly * 0.10,
          base[1] + d[1] * h * 0.30 + n[1] * belly * 0.10)
    c2 = (top[0] - d[0] * h * 0.30 + n[0] * belly * 0.90,
          top[1] - d[1] * h * 0.30 + n[1] * belly * 0.90)

    samples = [bezier(base, c1, c2, top, i / 24) for i in range(25)]
    left, right = [], []
    for i, (sx, sy) in enumerate(samples):
        t = i / 24
        theta = bezier_tangent(base, c1, c2, top, t)
        wdt = (w0 + (w1 - w0) * (t ** 1.15)) / 2   # taper eases in near top
        nx, ny = math.cos(theta + math.pi / 2), math.sin(theta + math.pi / 2)
        left.append((sx + nx * wdt, sy + ny * wdt))
        right.append((sx - nx * wdt, sy - ny * wdt))
    trunk = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in left + right[::-1]) + "Z"

    rings = []
    for tt in (0.16, 0.28, 0.40, 0.52, 0.64, 0.76):
        p = bezier(base, c1, c2, top, tt)
        theta = bezier_tangent(base, c1, c2, top, tt)
        w = (w0 + (w1 - w0) * tt) / 2 * 0.68
        ux, uy = math.cos(theta + math.pi / 2), math.sin(theta + math.pi / 2)
        a = (p[0] + ux * w, p[1] + uy * w)
        b = (p[0] - ux * w, p[1] - uy * w)
        ctrl = (p[0] + d[0] * 2, p[1] + w * 0.55)   # sag with gravity
        rings.append(f"M{a[0]:.1f},{a[1]:.1f}Q{ctrl[0]:.1f},{ctrl[1]:.1f} "
                     f"{b[0]:.1f},{b[1]:.1f}")
    return trunk, "".join(rings), [left[0], right[0], left[-1], right[-1]]


def mound_geometry(x0, x1, y_base, apex_x, apex_y):
    """Two-hump sand mound. Returns (mound_d, shade_d)."""
    mid = (x0 + x1) / 2
    mound = (f"M{x0:.1f},{y_base:.1f}Q{apex_x - (x1 - x0) * 0.22:.1f},{apex_y:.1f} "
             f"{apex_x:.1f},{apex_y + 2:.1f}"
             f"Q{apex_x + (x1 - x0) * 0.24:.1f},{apex_y + 4:.1f} {x1:.1f},{y_base:.1f}Z")
    sx0 = mid + (x1 - mid) * 0.18
    shade = (f"M{sx0:.1f},{y_base:.1f}Q{(sx0 + x1) / 2:.1f},{apex_y + 12:.1f} "
             f"{x1:.1f},{y_base:.1f}Z")
    return mound, shade


def mound_surface_y(mound, x):
    """Sample the mound outline at x, so fallen coconuts and grass can
    be planted ON the sand instead of floating (VLM round-1 finding)."""
    x0, x1, y_base, apex_x, apex_y = mound
    if x <= x0 or x >= x1:
        return y_base
    # two quadratic halves; sample each and pick the point nearest x
    best = (x, y_base)
    for (p0, p1, p2) in (
        ((x0, y_base), (apex_x - (x1 - x0) * 0.22, apex_y), (apex_x, apex_y + 2)),
        ((apex_x, apex_y + 2), (apex_x + (x1 - x0) * 0.24, apex_y + 4), (x1, y_base)),
    ):
        for i in range(41):
            t = i / 40
            qx, qy = qbez(p0, p1, p2, t)
            if abs(qx - x) < abs(best[0] - x):
                best = (qx, qy)
    return best[1]


def grass_geometry(mound, blades, rng):
    """Jittered grass blades planted on the mound surface (leaflet
    geometry, r46 lineage). blades: (x, base_angle, length)."""
    ds = []
    for (bx, base_ang, length) in blades:
        by = mound_surface_y(mound, bx) + 2
        ang = base_ang + rng.uniform(-0.08, 0.08)
        d, _ = leaflet_path(bx, by, ang, length * rng.uniform(0.86, 1.12),
                            curl=rng.uniform(-0.25, 0.25))
        ds.append(d)
    return "".join(ds)


# --------------------------------------------------------------------------
# one tree
# --------------------------------------------------------------------------
# placements: (variant, tip_target_deg, scale, mirror, layer)
# rot is derived from the target tip angle so the table reads like a
# planting plan instead of raw rotation soup. Coverage is tuned to be
# radially EVEN (VLM round-1 finding: gaps read as broken fronds), and
# the two trees get deliberately different postures — left: the tall
# leaner reaching toward the listings; right: the stocky sentinel that
# carries its crown closer to vertical (distinct silhouettes, not
# mirror clones).
LEFT_TREE = dict(
    seed=60, tag="l",
    crown=(128, 96), base=(58, 540), w0=24.0, w1=8.5, belly=-14.0,
    placements=[
        ("arch", -100, 0.70, True,  "back"),
        ("arch",  -76, 0.68, False, "back"),
        ("arch",  -50, 0.66, False, "back"),
        ("arch", -165, 0.82, True,  "mid"),
        ("arch",  -18, 0.88, False, "mid"),
        ("droop", -130, 0.56, True,  "front"),
        ("droop",  150, 0.86, True,  "front"),
        ("droop",   24, 0.84, False, "front"),
        ("droop",   95, 0.55, False, "front"),
    ],
    nuts=[(121, 113, 10.0, "palm-nut"), (137, 116, 9.5, "palm-nut--lit"),
          (128, 125, 9.0, "palm-nut"), (114, 124, 8.5, "palm-nut")],
    mound=(14, 124, 552, 58, 512),
    grass=[(22, -2.05, 24), (34, -1.85, 34), (46, -1.62, 40), (58, -1.42, 38),
           (70, -1.22, 34), (84, -1.0, 30), (98, -0.8, 26), (112, -0.58, 22)],
    fallen=[(26, 8.0), (40, 6.5)],
)

RIGHT_TREE = dict(
    seed=61, tag="r",
    crown=(126, 132), base=(190, 534), w0=29.0, w1=10.0, belly=14.0,
    placements=[
        ("arch", -110, 0.60, True,  "back"),
        ("arch",  -85, 0.64, True,  "back"),
        ("arch",  -58, 0.62, False, "back"),
        ("arch", -170, 0.84, True,  "mid"),
        ("arch",  -10, 0.78, False, "mid"),
        ("droop", -130, 0.56, True,  "front"),
        ("droop",  150, 0.86, True,  "front"),
        ("droop",   22, 0.84, False, "front"),
        ("droop",   95, 0.55, False, "front"),
    ],
    nuts=[(133, 153, 10.0, "palm-nut"), (116, 156, 9.5, "palm-nut--lit"),
          (124, 166, 9.0, "palm-nut"), (138, 161, 8.5, "palm-nut")],
    mound=(124, 248, 550, 184, 512),
    grass=[(132, -1.95, 26), (146, -1.7, 34), (160, -1.45, 38), (176, -1.25, 36),
           (192, -1.02, 32), (206, -0.8, 28), (220, -0.58, 24), (236, -0.4, 20)],
    fallen=[(226, 7.5), (238, 6.0)],
)


def local_tip_angle(shape):
    """Angle (deg) of the canonical tip from the base."""
    tx, ty = shape[2][0] * FROND_LEN, shape[2][1] * FROND_LEN
    return math.degrees(math.atan2(ty, tx))


def rot_for(shape, target_deg, mirror):
    """Rotation that lands the canonical tip at target_deg. Mirrored
    fronds flip x first (arch still up), then rotate."""
    local = local_tip_angle(shape)
    if mirror:
        local = 180.0 - local
    return target_deg - local


def build_tree(spec, pad_top=0.0):
    rng = random.Random(spec["seed"])
    crown = spec["crown"]

    fronds = {"arch": build_frond(ARCH, rng), "droop": build_frond(DROOP, rng)}
    arch_d, arch_pts = fronds["arch"]
    droop_d, droop_pts = fronds["droop"]

    # --- frond placements -> <use> lines + bbox points ---
    layers = {"back": [], "mid": [], "front": []}
    pts = []
    for variant, target, scale, mirror, layer in spec["placements"]:
        shape = ARCH if variant == "arch" else DROOP
        rot = rot_for(shape, target, mirror)
        m = "-" if mirror else ""
        layers[layer].append(
            f'<use href="#palmFrond{variant.capitalize()}{spec["tag"].upper()}" '
            f'transform="translate({crown[0]},{crown[1]}) rotate({rot:.1f}) '
            f'scale({m}{scale:.2f},{scale:.2f})"/>'
        )
        src = arch_pts if variant == "arch" else droop_pts
        rad = math.radians(rot)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        sx = -1.0 if mirror else 1.0
        for (x, y) in src:
            mx, my = x * sx * scale, y * scale
            pts.append((crown[0] + mx * cos_r - my * sin_r,
                        crown[1] + mx * sin_r + my * cos_r))

    # --- trunk / mound / grass / nuts ---
    trunk, rings, tpts = trunk_geometry(
        spec["base"], (crown[0], crown[1] + 6), spec["w0"], spec["w1"], spec["belly"])
    mound, shade = mound_geometry(*spec["mound"])
    grass = grass_geometry(spec["mound"], spec["grass"], rng)

    boot = (f'M{crown[0] - 15:.1f},{crown[1] + 5:.1f}Q{crown[0]:.1f},{crown[1] - 8:.1f} '
            f'{crown[0] + 15:.1f},{crown[1] + 5:.1f}Q{crown[0] + 4:.1f},{crown[1] + 30:.1f} '
            f'{crown[0] - 15:.1f},{crown[1] + 5:.1f}Z')

    nuts_svg = [f'<circle class="{cls}" cx="{cx}" cy="{cy}" r="{r}"/>'
                for (cx, cy, r, cls) in spec["nuts"]]
    # fallen nuts: resting ON the sand (centre 0.75 r above the surface)
    # with a soft contact shadow ellipse, so they read as sitting on the
    # mound, not embedded in it (VLM round-2 finding)
    mound_spec = spec["mound"]
    fallen_svg = []
    for (fx, r) in spec["fallen"]:
        sy = mound_surface_y(mound_spec, fx)
        fallen_svg.append(
            f'<ellipse class="palm-nut-shadow" cx="{fx}" cy="{sy + 1:.1f}" '
            f'rx="{r * 1.35:.1f}" ry="{r * 0.32:.1f}"/>')
        fallen_svg.append(
            f'<circle class="palm-nut" cx="{fx}" '
            f'cy="{sy - r * 0.75:.1f}" r="{r}"/>')

    # grass tips for bbox
    for (bx, ang, length) in spec["grass"]:
        by = mound_surface_y(spec["mound"], bx) + 2
        pts.append((bx + math.cos(ang) * length, by + math.sin(ang) * length))
    pts += tpts
    pts += [(spec["mound"][0], spec["mound"][2]), (spec["mound"][1], spec["mound"][2]),
            (spec["mound"][3], spec["mound"][4])]
    for (cx, cy, r, _) in spec["nuts"]:
        pts.append((cx - r, cy - r)); pts.append((cx + r, cy + r))
    for (fx, r) in spec["fallen"]:
        pts.append((fx - r * 1.35, mound_surface_y(spec["mound"], fx) + r * 0.32))
        pts.append((fx + r, mound_surface_y(spec["mound"], fx) - r))

    # --- auto-fit viewBox to the union bbox (pad 6) ---
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    pad = 6.0
    tx, ty = -min(xs) + pad, -min(ys) + pad + pad_top
    w = max(xs) - min(xs) + 2 * pad
    h = max(ys) - min(ys) + 2 * pad + pad_top
    return (svg_text(spec, w, h, tx, ty, trunk, rings, boot, layers,
                     nuts_svg, mound, shade, grass, fallen_svg, arch_d, droop_d),
            w, h)


def svg_text(spec, w, h, tx, ty, trunk, rings, boot, layers,
             nuts_svg, mound, shade, grass, fallen_svg, arch_d, droop_d):

    def g(layer):
        inner = "\n      ".join(layers[layer])
        return f'<g class="palm-frond--{layer}">\n      {inner}\n    </g>'

    svg = f"""<svg class="palm-tree" viewBox="0 0 {w:.0f} {h:.0f}" role="presentation" aria-hidden="true" focusable="false">
    <defs>
      <g id="palmFrondArch{spec['tag'].upper()}">{''.join(f'<path d="{d}"/>' for d in arch_d)}</g>
      <g id="palmFrondDroop{spec['tag'].upper()}">{''.join(f'<path d="{d}"/>' for d in droop_d)}</g>
    </defs>
    <g transform="translate({tx:.1f},{ty:.1f})">
    {g("back")}
    <path class="palm-trunk" d="{trunk}"/>
    <path class="palm-trunk-ring" d="{rings}"/>
    <path class="palm-boot" d="{boot}"/>
    {g("mid")}
    {g("front")}
    {''.join(nuts_svg)}
    <path class="palm-mound" d="{mound}"/>
    <path class="palm-mound--shade" d="{shade}"/>
    <path class="palm-grass" d="{grass}"/>
    {''.join(fallen_svg)}
  </g>
</svg>"""
    return svg


TEMPLATE = """{% comment %}
  r60 (owner round ten) — coast palm sentinels.

  Owner ask: "on the white sides next to each listings generate a
  coconut tree... it will be stagnant parallax up to the start of the
  footer."

  Two coconut palms for the white gutters of the results band. Each
  .palm-sentinel column is absolutely positioned to span .listings-band
  exactly (results header -> end of related searches, i.e. straight
  down to the footer); the .palm-sentinel__stick inside is position:
  sticky, so each palm holds STILL while the listings scroll past and
  departs precisely when the footer arrives — stagnant parallax, pure
  CSS. No JS, no animation of its own: identical under fx=none,
  reduced motion, and with scripts blocked. Shown only >= 1620px,
  where the white sides are real (search.css); pointer-events: none.

  Decorative only: aria-hidden, never focusable, no text — zero
  accessibility surface (owner round nine: "ensure the website is
  accessible"). Colours are .palm-* class hooks in search.css (tokens
  only — D-LOOP-38a keeps search.css at zero hex).

  Generated by scripts/r60_gen_palms.py (deterministic, seeds 60/61,
  r46 frond lineage; the right tree's viewBox is crown-padded so both
  mounds share one ground plane) — regenerate there, never edit by hand.
{% endcomment %}
<div class="palm-sentinel palm-sentinel--left" aria-hidden="true">
  <div class="palm-sentinel__stick">
    @@LEFT@@
  </div>
</div>
<div class="palm-sentinel palm-sentinel--right" aria-hidden="true">
  <div class="palm-sentinel__stick">
    @@RIGHT@@
  </div>
</div>
"""

# baked preview colours (approximations of the search.css mixes) — the
# standalone preview page only; the shipped template carries classes.
PREVIEW_COLORS = {
    "palm-frond--back": "#135848",
    "palm-frond--mid": "#0b6b52",
    "palm-frond--front": "#5c9b89",
    "palm-trunk": "#b2866b",
    "palm-trunk-ring": "#623d29",
    "palm-boot": "#473429",
    "palm-nut": "#5a4032",
    "palm-nut--lit": "#774b33",
    "palm-nut-shadow": "#c4b4a2",
    "palm-mound": "#d8c9b8",
    "palm-mound--shade": "#aea092",
    "palm-grass": "#4e937f",
}
PREVIEW_STROKE = {  # stroke rules the template gets from CSS classes
    "palm-trunk-ring": ("#623d29", 2.4),
}


def main(preview: bool) -> None:
    # Shared ground plane (VLM round-4 finding): both stickers render at
    # the same width, so the two mounds bottom-align only when the two
    # viewBox ASPECTS match. The right tree is shorter by nature — pad
    # its crown side until its box has the left tree's aspect, then the
    # mounds land on one baseline (and the crown offset stays as the
    # deliberate height difference between the two characters).
    left, lw, lh = build_tree(LEFT_TREE)
    _, rw, rh = build_tree(RIGHT_TREE)
    pad_top = max(0.0, rw * lh / lw - rh)
    right, _, _ = build_tree(RIGHT_TREE, pad_top=round(pad_top, 1))
    OUT.write_text(
        TEMPLATE.replace("@@LEFT@@", left).replace("@@RIGHT@@", right),
        encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KiB, "
          f"right-tree crown pad {pad_top:.1f}")

    if preview:
        rules = "\n".join(
            f"    .{cls} {{ fill: {col}; }}" for cls, col in PREVIEW_COLORS.items())
        rules += ("\n    .palm-trunk-ring { fill: none; stroke: #623d29; "
                  "stroke-width: 2.4; stroke-linecap: round; }")
        page = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>palms preview</title>
<style>
  body {{ margin: 0; background: #faf8f4; font: 14px/1.4 system-ui; }}
  .stage {{ display: flex; justify-content: center; gap: 240px; padding: 60px 40px; }}
  .palm {{ width: 188px; }}
  .palm svg {{ width: 100%; height: auto; display: block; }}
{rules}
</style></head>
<body>
  <div class="stage">
    <div class="palm">{left}</div>
    <div class="palm">{right}</div>
  </div>
</body></html>"""
        PREVIEW.write_text(page, encoding="utf-8")
        print(f"wrote {PREVIEW}")


if __name__ == "__main__":
    main(preview="--preview" in sys.argv)
