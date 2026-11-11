#!/usr/bin/env python3
"""r68 — generate the EVEN palm-field tile for the listings band.

Owner request (round twelve): "the listings page palms need to be spread
out evenly to look less bushy in some areas than others and maximise
the parallax effect they give out."

Diagnosis first (measured, sand-composited heat-map of the shipped r46
tile): the hand-tuned 12-frond placement clumps — per-cell wash
coverage across a 4×4 grid runs 1.2% to 9.9%, an 8.06× spread. The top
band arches into a heavy clump while the middle-right goes almost
bare. That is exactly the "bushy in some areas" the owner sees.

The fix is structural, not another hand-tune. Three rules place the
fronds, so even coverage is guaranteed by construction:

  grid     = 5×5 over the same 1400×1600 tile — one frond per cell,
             jittered ±0.16 cell so the bases never align into rows
  anchor   = each frond's ink CENTROID lands on its cell centre (the
             base is offset opposite the aim by the local centroid
             ~(0.48L, -0.55L)); without this the arch bleeds all its
             ink into the neighbouring cell in the aim direction and
             the grid pattern comes back as coverage stripes
  aim      = golden-angle sweep (i × 137.508°) ± 12° — consecutive
             fronds point in maximally different directions, so no two
             neighbours push ink the same way
  layers   = checkerboard ((col+row) % 2): 13 back (14% wash) / 12
             front (26% wash) — the stronger front fronds never share
             an edge, so the visible punctuation is spread as widely
             as the grid allows
  scale    = back 0.66–0.82, front 0.60–0.76 (back is fainter and
             fills, front is stronger and punctuates). Measured result
             (seed 868, sand-composited): per-cell coverage 4.6%–6.6%,
             a 1.43× spread — versus the r46 tile's 8.06×. Mean
             coverage rises 4.5% → 5.9% because the same total ink now
             reaches everywhere instead of stacking in clumps; the
             busiest even cell (7.1%) is still well under the old
             clump peak (9.9%).

Frond art: the r46 frond VERBATIM (same bezier rachis, same 40
leaflets, same curl) — the same botanical drawing, placed evenly. Two
depth washes unchanged (back #e7d9cd = clay 14% over sand, front
#dcc6b8 = clay 26%). Seamless in both axes: anything crossing an edge
is redrawn wrapped (±W/±H), the r46 wrap logic untouched.

Home keeps the r46 tile (palm-field.svg, .home-market::before) — the
owner asked about the LISTINGS page; the home field is not touched.
This tile is a NEW asset so the two pages can diverge freely.

Deterministic: random.seed(868). Re-run to regenerate; output goes to
static/img/palm-field-even.svg.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

random.seed(868)

OUT = (Path(__file__).resolve().parents[1] / "static" / "img"
       / "palm-field-even.svg")

W, H = 1400.0, 1600.0          # tile size (px) — same as r46
BACK, FRONT = "#e7d9cd", "#dcc6b8"
LEAFLETS = 40                  # per frond (r46)
FROND_LEN = 520.0              # canonical rachis length before scaling

GRID = 5                       # 5×5 jittered grid → 25 even bases
GOLDEN = 137.508               # golden angle (deg) — even rotation sweep
JITTER = 0.16                  # of a cell — organic, never aligned
SCALE_BACK = (0.66, 0.82)      # faint layer fills
SCALE_FRONT = (0.60, 0.76)     # strong layer punctuates
CENTROID = (0.48, -0.55)       # local ink centroid, in units of L·scale


# --------------------------------------------------------------------------
# geometry helpers (r46, verbatim)
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
    )


# --------------------------------------------------------------------------
# one frond -> list of path `d` strings (r46, verbatim)
# --------------------------------------------------------------------------
def frond_paths():
    """Canonical frond drawn with its base at the origin, arching up and
    over to the right; returned as (leaflet_ds, rachis_d)."""
    L = FROND_LEN
    p0 = (0.0, 0.0)
    p1 = (0.10 * L, -0.44 * L)
    p2 = (0.50 * L, -0.82 * L)
    p3 = (1.00 * L, -0.60 * L)   # tip droops back down — the palm arch

    leaflets = []
    for i in range(LEAFLETS):
        t = (i + 1) / (LEAFLETS + 1)
        ax, ay = bezier(p0, p1, p2, p3, t)
        theta = bezier_tangent(p0, p1, p2, p3, t)
        profile = math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.85
        length = L * 0.42 * (0.22 + 0.78 * profile)
        for side in (-1, 1):
            opening = math.radians(46 - 22 * t) + random.uniform(-0.05, 0.05)
            sag = math.radians(6 + 10 * t) * side
            angle = theta + side * opening + sag
            jitter = random.uniform(-0.03, 0.03)
            leaflets.append(
                leaflet_path(ax, ay, angle + jitter, length,
                             curl=side * math.radians(18 + 8 * t))
            )

    samples = [bezier(p0, p1, p2, p3, i / 24) for i in range(25)]
    left, right = [], []
    for i, (sx, sy) in enumerate(samples):
        t = i / 24
        theta = bezier_tangent(p0, p1, p2, p3, t)
        wdt = L * (0.017 - 0.013 * t)
        nx, ny = math.cos(theta + math.pi / 2), math.sin(theta + math.pi / 2)
        left.append((sx + nx * wdt, sy + ny * wdt))
        right.append((sx - nx * wdt, sy - ny * wdt))
    pts = left + right[::-1]
    rachis = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
    return leaflets, rachis


# --------------------------------------------------------------------------
# the r68 field: one jittered-grid base per cell, even by construction
# --------------------------------------------------------------------------
def placements():
    """25 placements on a jittered 5×5 grid.

    Returns (fx, fy, scale, rotation_deg, layer) with fx/fy in tile
    fractions. The base point can fall outside [0, 1] — the centroid
    anchoring pushes it opposite the aim — which is fine: the wrap
    pass in build_svg() redraws every tile-offset copy that intersects
    the tile, so edge bases still seam correctly.
    """
    out = []
    cw, ch = W / GRID, H / GRID
    i = 0
    for row in range(GRID):
        for col in range(GRID):
            cx = (col + 0.5 + random.uniform(-JITTER, JITTER)) * cw
            cy = (row + 0.5 + random.uniform(-JITTER, JITTER)) * ch
            layer = "back" if (col + row) % 2 == 0 else "front"
            scale = random.uniform(*(SCALE_BACK if layer == "back"
                                     else SCALE_FRONT))
            rot = (i * GOLDEN + random.uniform(-12.0, 12.0)) % 360.0
            # centroid anchoring: place the BASE so the frond's ink
            # centroid lands on the cell centre — the arch then bleeds
            # evenly into ALL neighbouring cells instead of only the
            # one it aims at
            cxd = CENTROID[0] * FROND_LEN * scale
            cyd = CENTROID[1] * FROND_LEN * scale
            a = math.radians(rot)
            cx -= cxd * math.cos(a) - cyd * math.sin(a)
            cy -= cxd * math.sin(a) + cyd * math.cos(a)
            out.append((cx / W, cy / H, scale, rot, layer))
            i += 1
    return out


def frond_bbox_length(scale):
    """Rough radius of a frond for wrap-around intersection tests."""
    return FROND_LEN * 1.05 * scale


def build_svg():
    leaflets, rachis = frond_paths()
    groups = {"back": [], "front": []}
    for fx, fy, scale, rot, layer in placements():
        cx, cy = fx * W, fy * H
        radius = frond_bbox_length(scale)
        # emit the placement for every tile offset whose neighbourhood
        # intersects this tile → guarantees seamless wrapping (r46)
        for ox in (-W, 0.0, W):
            for oy in (-H, 0.0, H):
                x, y = cx + ox, cy + oy
                if -radius <= x <= W + radius and -radius <= y <= H + radius:
                    groups[layer].append(
                        f'<use href="#palm-frond" transform="'
                        f'translate({x:.0f},{y:.0f}) rotate({rot:.1f}) '
                        f'scale({scale:.2f})"/>'
                    )

    back = "\n    ".join(groups["back"])
    front = "\n    ".join(groups["front"])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">
  <!-- Gabriel Homes — Mombasa palm field, EVEN variant (r68). Generated
       by scripts/r68_palm_field_even.py (deterministic, seed 868; frond
       art and washes from the r46 lineage). One frond per cell of a
       jittered 5×5 grid, centroid-anchored, golden-angle aim,
       checkerboard layers — even coverage by construction: per-cell
       wash coverage 4.6%–6.6% (1.43× spread) versus the r46 hand-tuned
       tile's 1.2%–9.9% (8.06×). Back #e7d9cd (clay 14% over sand),
       front #dcc6b8 (26%). Used by the LISTINGS band only
       (.listings-band::before, search.css) — home keeps the r46 tile.
       Decorative background only. -->
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
    n_use = svg.count("<use")
    print(f"wrote {OUT} ({len(svg)/1024:.1f} KiB, {n_paths} paths, "
          f"{n_use} uses (25 bases + wrapped copies), tile {W:.0f}x{H:.0f})")
