#!/usr/bin/env python3
"""r46 — generate the Mombasa palm-field background tile.

Owner request: palm leaves in the background of the RECOMMENDED IN
MOMBASA section, covering it from the section head down through the
Short stays & BnB group (implementation: home.css .home-market::before,
with a mask fade so it dissolves before the TALK TO US strip).

This draws the artwork procedurally so the fronds are botanically
structured rather than clip-art:

  frond  = one arching rachis (a cubic bezier sampled N times) with
           ~40 slender leaflets attached alternately left/right along
           it; leaflet length peaks mid-frond and tapers to nothing at
           the tip; every leaflet carries a small deterministic angle
           jitter so the silhouette reads organic, not mechanical.
  field  = a seamless WxH tile: fronds placed at varied rotations /
           scales / mirrors in TWO depth layers; anything crossing an
           edge is redrawn wrapped (+/-W, +/-H), so the tile repeats
           invisibly in both axes when the CSS background repeats.

Palette (baked, from the existing tokens — brand-consistent, no greens
anywhere in the token set):
  section sand  #f4eee6  (home.css .home-market)
  back  layer   #e7d9cd  = clay #965634 @ 14% over the sand
  front layer   #dcc6b8  = clay #965634 @ 26% over the sand
Both sit far below the white cards' contrast — a watermark, not a
competing pattern.

Deterministic: random.seed(46). Re-run to regenerate; output goes to
static/img/palm-field.svg.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

random.seed(46)

OUT = Path(__file__).resolve().parents[1] / "static" / "img" / "palm-field.svg"

W, H = 1400.0, 1600.0          # tile size (px) — tuned to section scale
BACK, FRONT = "#e7d9cd", "#dcc6b8"
LEAFLETS = 40                  # per frond
FROND_LEN = 520.0              # canonical rachis length before scaling


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------
def bezier(p0, p1, p2, p3, t):
    """Cubic bezier point at t."""
    mt = 1.0 - t
    x = (mt**3 * p0[0] + 3 * mt * mt * t * p1[0]
         + 3 * mt * t * t * p2[0] + t**3 * p3[0])
    y = (mt**3 * p0[1] + 3 * mt * mt * t * p1[1]
         + 3 * mt * t * t * p2[1] + t**3 * p3[1])
    return x, y


def bezier_tangent(p0, p1, p2, p3, t):
    """Cubic bezier tangent angle (radians) at t."""
    mt = 1.0 - t
    dx = (3 * mt * mt * (p1[0] - p0[0]) + 6 * mt * t * (p2[0] - p1[0])
          + 3 * t * t * (p3[0] - p2[0]))
    dy = (3 * mt * mt * (p1[1] - p0[1]) + 6 * mt * t * (p2[1] - p1[1])
          + 3 * t * t * (p3[1] - p2[1]))
    return math.atan2(dy, dx)


def leaflet_path(ax, ay, angle, length, curl):
    """A slender pointed leaf: two quadratic curves base -> tip, bowed
    by `curl` (the natural droop of a palm leaflet)."""
    tx = ax + math.cos(angle) * length
    ty = ay + math.sin(angle) * length
    # midpoint + perpendicular half-width, offset along the length for
    # the point of maximum width (~45% out)
    mx = ax + math.cos(angle) * length * 0.45
    my = ay + math.sin(angle) * length * 0.45
    w = length * 0.062
    nx = math.cos(angle + math.pi / 2) * w
    ny = math.sin(angle + math.pi / 2) * w
    # curl shifts both controls toward one side -> the leaf bows
    cx = math.cos(angle) * length * 0.28 + math.cos(angle + curl) * length * 0.10
    cy = math.sin(angle) * length * 0.28 + math.sin(angle + curl) * length * 0.10
    return (
        f"M{ax:.1f},{ay:.1f}"
        f"Q{mx + nx + cx:.1f},{my + ny + cy:.1f} {tx:.1f},{ty:.1f}"
        f"Q{mx - nx + cx:.1f},{my - ny + cy:.1f} {ax:.1f},{ay:.1f}Z"
    )


# --------------------------------------------------------------------------
# one frond -> list of path `d` strings (leaflets + rachis strip)
# --------------------------------------------------------------------------
def frond_paths():
    """Canonical frond drawn with its base at the origin, arching up and
    over to the right; returned as (leaflet_ds, rachis_d). Rotation,
    mirroring and scaling happen in the <g> transform, so this shape is
    drawn once and reused everywhere."""
    L = FROND_LEN
    p0 = (0.0, 0.0)
    p1 = (0.10 * L, -0.44 * L)
    p2 = (0.50 * L, -0.82 * L)
    p3 = (1.00 * L, -0.60 * L)   # tip droops back down — the palm arch

    leaflets = []
    for i in range(LEAFLETS):
        t = (i + 1) / (LEAFLETS + 1)               # skip the very base
        ax, ay = bezier(p0, p1, p2, p3, t)
        theta = bezier_tangent(p0, p1, p2, p3, t)
        # leaflet length: peaks mid-frond, short at both ends
        profile = math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.85
        length = L * 0.42 * (0.22 + 0.78 * profile)
        # leaflets open wider near the base, fold toward the tip; plus
        # the deterministic jitter that keeps it organic
        for side in (-1, 1):
            opening = math.radians(46 - 22 * t) + random.uniform(-0.05, 0.05)
            sag = math.radians(6 + 10 * t) * side      # droop off-axis
            angle = theta + side * opening + sag
            jitter = random.uniform(-0.03, 0.03)
            leaflets.append(
                leaflet_path(ax, ay, angle + jitter, length,
                             curl=side * math.radians(18 + 8 * t))
            )

    # rachis: a tapering polygon strip along the same curve
    samples = [bezier(p0, p1, p2, p3, i / 24) for i in range(25)]
    left, right = [], []
    for i, (sx, sy) in enumerate(samples):
        t = i / 24
        theta = bezier_tangent(p0, p1, p2, p3, t)
        wdt = L * (0.017 - 0.013 * t)                 # tapers to the tip
        nx, ny = math.cos(theta + math.pi / 2), math.sin(theta + math.pi / 2)
        left.append((sx + nx * wdt, sy + ny * wdt))
        right.append((sx - nx * wdt, sy - ny * wdt))
    pts = left + right[::-1]
    rachis = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
    return leaflets, rachis


# --------------------------------------------------------------------------
# the field: frond placements across one seamless tile
# --------------------------------------------------------------------------
# (x, y, scale, rotation_deg, mirror, layer) — hand-tuned so the tile
# has no dead pools and no overlaps; back layer fills, front layer
# punctuates.
PLACEMENTS = [
    (0.04, 0.46, 1.30, -14, False, "back"),
    (0.58, 0.06, 1.15, 158, True,  "back"),
    (0.30, 0.80, 1.00, -34, False, "back"),
    (0.92, 0.62, 1.05, 196, True,  "back"),
    (0.52, 0.98, 0.85, -10, False, "back"),
    (0.10, 0.92, 0.75, 18,  True,  "back"),
    (0.97, 0.05, 0.90, 132, False, "back"),
    (0.06, 0.15, 1.20, -64, True,  "front"),
    (0.66, 0.44, 1.00, 12,  True,  "front"),
    (0.36, 0.30, 0.90, -120, False, "front"),
    (0.80, 0.86, 0.95, -158, True,  "front"),
    (0.44, 0.66, 0.70, 40,  False, "front"),
]


def frond_bbox_length(scale):
    """Rough radius of a frond for wrap-around intersection tests."""
    return FROND_LEN * 1.05 * scale


def build_svg():
    leaflets, rachis = frond_paths()
    # pre-render the frond as a reusable <g> once, <use> per placement
    groups = {"back": [], "front": []}
    for fx, fy, scale, rot, mirror, layer in PLACEMENTS:
        cx, cy = fx * W, fy * H
        radius = frond_bbox_length(scale)
        # emit the placement for every tile offset whose neighbourhood
        # intersects this tile → guarantees seamless wrapping
        for ox in (-W, 0.0, W):
            for oy in (-H, 0.0, H):
                x, y = cx + ox, cy + oy
                if -radius <= x <= W + radius and -radius <= y <= H + radius:
                    m = "-" if mirror else ""
                    groups[layer].append(
                        f'<use href="#palm-frond" transform="'
                        f'translate({x:.0f},{y:.0f}) rotate({rot}) '
                        f'scale({m}{scale:.2f},{scale:.2f})"/>'
                    )

    back = "\n    ".join(groups["back"])
    front = "\n    ".join(groups["front"])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">
  <!-- Gabriel Homes — Mombasa palm field (r46). Generated by
       scripts/r46_palm_field.py (deterministic, seed 46). Two clay
       washes over the section sand #f4eee6: back #e7d9cd (14%),
       front #dcc6b8 (26%). Decorative background only. -->
  <defs>
    <g id="palm-frond">
      <path d="{rachis}"/>
      {''.join(f'<path d="{d}"/>' for d in leaflets)}
    </g>
  </defs>
  <g fill="{BACK}">
    {back}
  </g>
  <g fill="{FRONT}">
    {front}
  </g>
</svg>
"""
    return svg


if __name__ == "__main__":
    svg = build_svg()
    OUT.write_text(svg, encoding="utf-8")
    n_paths = svg.count("<path")
    print(f"wrote {OUT} ({len(svg)/1024:.1f} KiB, {n_paths} paths, "
          f"{len(PLACEMENTS)} fronds, tile {W:.0f}x{H:.0f})")
