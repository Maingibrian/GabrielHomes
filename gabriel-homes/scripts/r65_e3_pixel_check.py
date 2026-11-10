#!/usr/bin/env python3
"""r65 E3 owner-round pixel check — palm-field parallax screenshots.

PIL only (no browser). Shots live in LOOP/audit-screens (viewport 1600x900).

1. r65-e3-palm-rich-2.png gutters (x=20..120 and x=1480..1580, y=200..700):
   fronds textured in the side gutters — per-channel stddev max > 6 in
   each crop (a flat fill would be ~0).
2. r65-e3-palm-rich-3.png veil clears the band end: crop x=0..200,
   y=830..898 (left gutter only — no text there). The static ::after veil
   fades to band sand at the band end — mean RGB within 10 of
   (244, 238, 230) AND per-channel stddev < 7.
3. the veil never rides the drift (the core r65 concern): the same crop
   x=0..200, y=830..898 on r65-e3-palm-rich-3.png vs r65-e3-palm-none.png
   (both shot at cover 0.76; rich has the field at translateY≈+73px, none
   has it static — if the fade rode the traveler these crops would
   differ) — mean absolute per-pixel difference < 4 per channel.
4. r65-e3-palm-nojs.png gutters (x=20..120 and x=1480..1580, y=200..700):
   the field renders without JS — mean brightness (mean of all RGB) > 180
   AND per-channel stddev max > 6 in each crop (bright sand+fronds =
   inside the band; the old scroll-0 shot showed dark hero imagery ≈ 60).

Prints PASS/FAIL per check with measured numbers, then a single verdict:
    R65-PIXEL-VERDICT: PASS | FAIL
"""

import sys
from pathlib import Path

from PIL import Image, ImageChops

SCREENS = Path("/home/z/my-project/gabriel-homes/LOOP/audit-screens")

SAND = (244, 238, 230)       # #f4eee6 — band sand, the veil's fade target
SAND_TOL = 10.0              # check 2: per-channel |mean - sand| max
VEIL_STDDEV_MAX = 7.0        # check 2: near-clean sand at the band end
FROND_STDDEV_MIN = 6.0       # checks 1 & 4: gutters textured, not flat
DRIFT_DIFF_MAX = 4.0         # check 3: veil crop may not differ rich vs none
NOJS_BRIGHT_MIN = 180.0      # check 4: bright band, not the dark hero

GUTTERS = (("LEFT", 20, 120), ("RIGHT", 1480, 1580))
GY0, GY1 = 200, 700            # gutter crop rows
VEIL_BOX = (0, 830, 200, 898)  # left-gutter strip at the band end, no text

fails = []
checks = 0


def ok(cond, label, detail=""):
    global checks
    checks += 1
    print(f"[{'PASS' if cond else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(label)


def channel_stats(im):
    """(means, stddevs) per RGB channel for a PIL image."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    n = w * h
    totals = [0, 0, 0]
    squares = [0, 0, 0]
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            totals[0] += r
            totals[1] += g
            totals[2] += b
            squares[0] += r * r
            squares[1] += g * g
            squares[2] += b * b
    means = [t / n for t in totals]
    stddevs = [(max(s / n - m * m, 0.0)) ** 0.5 for s, m in zip(squares, means)]
    return means, stddevs


def fmt(values):
    return "(" + ", ".join(f"{v:.2f}" for v in values) + ")"


def crop_of(name, box):
    return Image.open(SCREENS / name).convert("RGB").crop(box)


def gutter_lines(fname, short, bright_min=None):
    """Checks 1 and 4: side gutters must show textured fronds (and, for
    check 4, bright band sand — not the dark hero of the old scroll-0
    shot, which measured a mean of ~60)."""
    for tag, x0, x1 in GUTTERS:
        means, stddevs = channel_stats(crop_of(fname, (x0, GY0, x1, GY1)))
        max_std = max(stddevs)
        textured = max_std > FROND_STDDEV_MIN
        if bright_min is None:
            good, extra = textured, ""
        else:
            brightness = sum(means) / 3.0
            good = textured and brightness > bright_min
            extra = f"brightness={brightness:.2f} (need > {bright_min}) | "
        ok(good,
           f"{short} {tag} gutter x={x0}..{x1}, y={GY0}..{GY1}",
           f"{extra}stddev R/G/B={fmt(stddevs)} (max {max_std:.2f}, "
           f"need > {FROND_STDDEV_MIN})")


def main() -> int:
    print("== r65 E3 pixel check — palm-field parallax (owner round thirteen) ==")
    print()

    print("-- Check 1: r65-e3-palm-rich-2.png — fronds textured in the side gutters --")
    gutter_lines("r65-e3-palm-rich-2.png", "rich-2")
    print()

    print("-- Check 2: r65-e3-palm-rich-3.png — the veil clears the band end --")
    means, stddevs = channel_stats(crop_of("r65-e3-palm-rich-3.png", VEIL_BOX))
    deltas = [abs(m - s) for m, s in zip(means, SAND)]
    max_delta = max(deltas)
    max_std = max(stddevs)
    ok(max_delta <= SAND_TOL and max_std < VEIL_STDDEV_MAX,
       "rich-3 veil crop x=0..200, y=830..898 (left gutter, no text)",
       f"mean R/G/B={fmt(means)} vs sand {SAND} (max |delta|={max_delta:.2f}, "
       f"need <= {SAND_TOL}) | stddev R/G/B={fmt(stddevs)} "
       f"(max {max_std:.2f}, need < {VEIL_STDDEV_MAX})")
    print()

    print("-- Check 3: the veil never rides the drift (rich-3 vs none, cover 0.76) --")
    rich_veil = crop_of("r65-e3-palm-rich-3.png", VEIL_BOX)
    none_veil = crop_of("r65-e3-palm-none.png", VEIL_BOX)
    diff_means, _ = channel_stats(ImageChops.difference(rich_veil, none_veil))
    ok(all(d < DRIFT_DIFF_MAX for d in diff_means),
       "rich-3 vs none, veil crop x=0..200, y=830..898",
       f"mean abs diff R/G/B={fmt(diff_means)} (need < {DRIFT_DIFF_MAX} per "
       f"channel); rich field at translateY≈+73px, none static")
    print()

    print("-- Check 4: r65-e3-palm-nojs.png — the field renders without JS --")
    gutter_lines("r65-e3-palm-nojs.png", "nojs", bright_min=NOJS_BRIGHT_MIN)
    print()

    if fails:
        print(f"R65-PIXEL-VERDICT: FAIL ({len(fails)} of {checks} checks failed)")
        return 1
    print("R65-PIXEL-VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
