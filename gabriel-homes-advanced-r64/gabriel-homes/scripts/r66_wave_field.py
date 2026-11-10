"""r66 — the wave field tile (owner round: "remove the palm tree
background in the about us page... maybe some waves patterns").

Generates static/img/wave-field.svg: a seamless repeating pattern of calm
horizontal wave lines in the brand's two clay tones (#e7d9cd / #dcc6b8 —
the same pair the palm-field tile uses, r46 lineage), so the about
values band trades botanical texture for the sea the whole page sells.

Design rules:
- Tile 1000 x 700. Rows of sine strokes every 87.5px (8 rows, divides
  the height exactly -> vertical seams match).
- Each row is one full-width cubic path; wavelength 250px (4 cycles per
  tile width -> horizontal seams match), amplitude ~14px.
- Rows alternate between three phases (0, 2pi/3, 4pi/3) so the field
  reads as drifting water, and every 3rd row repeats -> vertical
  tiling stays seamless.
- Stroke pairs (a bright line + a dim companion 4px below) echo tide
  lines; opacities keep the whole field quieter than the palm fronds
  (the r65 lesson: texture must not compete with copy).

Seamless-ness is verified by construction here; the r66 test pins the
asset's presence and its clay palette.
"""
from __future__ import annotations

import math
from pathlib import Path

W, H = 1000, 700
N_ROWS = 9                 # multiple of 3 -> the phase rotation tiles cleanly
ROW_STEP = H / N_ROWS
WAVELENGTH = 250.0         # 4 cycles across the width
AMPLITUDE = 13.0
PHASES = (0.0, 2 * math.pi / 3, 4 * math.pi / 3)
BRIGHT = "#e7d9cd"         # palm-field pair, light clay
DIM = "#dcc6b8"            # palm-field pair, deep clay

OUT = Path(__file__).resolve().parents[1] / "static" / "img" / "wave-field.svg"


def wave_path(y: float, phase: float) -> str:
    """One full-width sine as a single cubic-approximated path.

    Four cycles; each cycle = two cubic segments (up-half + down-half)
    with control points at 1/3 and 2/3 of the half-wavelength — the
    standard smooth sine approximation. Because the cycle count is an
    integer and every row starts/ends at the same phase angle, the
    path's left and right edges join when tiled.
    """
    half = WAVELENGTH / 2
    # sample the sine at the segment edges to place the curve's mid
    # anchor exactly on the wave (keeps rows visually even)
    seg = half / 2
    d = [f"M 0 {y + AMPLITUDE * math.sin(phase):.2f}"]
    x = 0.0
    direction = 1  # alternate up/down half-waves
    while x < W - 1e-6:
        nx = min(x + half, W)
        mid1 = x + seg
        mid2 = x + half - seg
        # anchor where the sine crosses y (every half wavelength),
        # offset by the phase so the wave is continuous
        anchor = y + AMPLITUDE * math.sin(phase + 2 * math.pi * (nx / WAVELENGTH))
        d.append(
            f"C {mid1:.2f} {y + direction * AMPLITUDE * 1.35:.2f}, "
            f"{mid2:.2f} {y + direction * AMPLITUDE * 1.35:.2f}, "
            f"{nx:.2f} {anchor:.2f}"
        )
        direction *= -1
        x = nx
    return " ".join(d)


def main() -> None:
    rows = []
    n_rows = N_ROWS
    for i in range(n_rows):
        y = i * ROW_STEP
        phase = PHASES[i % 3]
        bright = f'<path d="{wave_path(y, phase)}" fill="none" stroke="{BRIGHT}" stroke-opacity="0.85" stroke-width="2"/>'
        dim = f'<path d="{wave_path(y + 4.5, phase + 0.5)}" fill="none" stroke="{DIM}" stroke-opacity="0.5" stroke-width="1.5"/>'
        rows.append(bright)
        rows.append(dim)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">\n'
        f'  <title id="wave-field-title">Calm sea wave lines, clay tones</title>\n'
        f'  <g id="wave-field" stroke-linecap="round">\n    '
        + "\n    ".join(rows)
        + "\n  </g>\n</svg>\n"
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {n_rows} wave rows x2 tones)")


if __name__ == "__main__":
    main()
