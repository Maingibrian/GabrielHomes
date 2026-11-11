#!/usr/bin/env python3
"""r70 — analyze the /properties/ parallax trace captured live.

Columns (17): t, y, e0_top,e0_h (site-header), e1_top,e1_h (header dup),
e2_top,e2_h (search-map-shell), e3_top,e3_h (#search-map),
e4_top,e4_h (.market-filters), e5_top,e5_h (#results-grid),
bandTop, bandH, palms
"""
import csv, sys

rows = []
with open('/tmp/trace.csv') as f:
    # the eval output is one quoted line of \n-joined rows
    raw = f.read().strip().strip('"').replace('\\n', '\n')
    for r in csv.reader(raw.splitlines()):
        if len(r) == 17:
            rows.append([float(x) for x in r])

print(f"frames: {len(rows)}  span: {rows[0][0]:.0f}..{rows[-1][0]:.0f} ms")

# 1. layout stability: does anything above/in the band ever move?
cols = {'header_top': 2, 'shell_top': 4, 'shell_h': 5, 'map_h': 7,
        'filters_top': 8, 'grid_top': 10, 'grid_h': 11,
        'bandTop': 14, 'bandH': 15}
stable = True
for name, i in cols.items():
    vals = {r[i] for r in rows}
    if len(vals) > 1:
        stable = False
        print(f"  LAYOUT SHIFT {name}: {sorted(vals)[:6]}")
print("layout above band:", "ROCK STABLE (no shifts in 12s)" if stable else "SHIFTS FOUND")

# 2. frame rate over time (rAF cadence)
print("\nframe cadence (ms between samples):")
for lo, hi in [(0, 3800), (3800, 6000), (6000, 9000), (9000, 12000)]:
    ts = [r[0] for r in rows if lo <= r[0] < hi]
    if len(ts) > 2:
        dts = [b - a for a, b in zip(ts, ts[1:])]
        dts.sort()
        med = dts[len(dts)//2]
        print(f"  t={lo:>5}-{hi:>5}: median {med:.0f}ms  -> {1000/med:.0f} fps equiv")

# 3. the chase: palms vs theoretical target over time
# entry = bandTop - vh(1000); travel = clamp(y - entry, 0, bandH + 2vh); target = travel*0.5
vh = 1000.0
print("\nchase health (scroll stops -> does palms keep drifting?):")
stops = []  # (t_start, y) where y stays constant >= 500ms
i = 0
while i < len(rows):
    j = i
    while j + 1 < len(rows) and rows[j+1][1] == rows[i][1]:
        j += 1
    if rows[j][0] - rows[i][0] >= 500 and rows[i][1] > 0:
        stops.append((i, j))
    i = j + 1
for a, b in stops:
    y = rows[a][1]
    entry = rows[a][14] - vh
    target = max(0, min(y - entry, rows[a][15] + 2*vh)) * 0.5
    p0, p1 = rows[a][16], rows[b][16]
    gap0 = target - p0
    dur = rows[b][0] - rows[a][0]
    # how long until palms got within 5% of target?
    t95 = None
    for r in rows[a:b+1]:
        if abs(target - r[16]) <= 0.05 * max(abs(target - p0), 1):
            t95 = r[0] - rows[a][0]
            break
    print(f"  y={y:>6.0f} held {dur:>5.0f}ms: palms {p0:>7.2f}->{p1:>7.2f} "
          f"(target {target:>7.2f}, gap at start {gap0:>6.1f}px, "
          f"within-5% after {t95 if t95 is not None else 'NEVER':>6}ms)")
