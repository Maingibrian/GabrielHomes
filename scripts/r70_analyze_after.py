#!/usr/bin/env python3
"""r70 — AFTER-fix trace analysis: settle time at scroll stops."""
import csv

rows = []
raw = open('/tmp/trace_after.csv').read().strip().strip('"').replace('\\n', '\n')
for r in csv.reader(raw.splitlines()):
    if len(r) == 5:
        rows.append([float(x) for x in r])
print(f"frames: {len(rows)}")

# frame cadence during scroll (did the dip still happen?)
for lo, hi in [(0, 3800), (3800, 6000), (6000, 9000), (9000, 12000)]:
    ts = [r[0] for r in rows if lo <= r[0] < hi]
    if len(ts) > 2:
        dts = sorted(b - a for a, b in zip(ts, ts[1:]))
        med = dts[len(dts)//2]
        print(f"  t={lo:>5}-{hi:>5}: median frame {med:.0f}ms ({1000/med:.0f} fps)")

vh = 1000.0
print("\nsettle health at each scroll stop (was: NEVER within 5%):")
i = 0
worst = 0
while i < len(rows):
    j = i
    while j + 1 < len(rows) and rows[j+1][1] == rows[i][1]:
        j += 1
    if rows[j][0] - rows[i][0] >= 400 and rows[i][1] > 0:
        y = rows[i][1]
        entry = rows[i][2] - vh
        target = max(0, min(y - entry, rows[i][3] + 2*vh)) * 0.5
        p0 = rows[i][4]
        gap0 = target - p0
        # time to close 95% of the gap
        t95 = None
        for r in rows[i:j+1]:
            if abs(target - r[4]) <= 0.05 * max(abs(gap0), 1):
                t95 = r[0] - rows[i][0]
                break
        if t95 is not None:
            worst = max(worst, t95)
        print(f"  y={y:>6.0f} held {rows[j][0]-rows[i][0]:>5.0f}ms: "
              f"gap {gap0:>6.1f}px -> settled 95% in "
              f"{('%.0fms' % t95) if t95 is not None else 'NEVER':>8}")
    i = j + 1
print(f"\nWORST 95%-settle: {worst:.0f}ms" if worst else "\nno stop measured")

# overall ratio check: palms delta vs scroll delta between settled points
print("\nhalf-speed ratio at settled points:")
settle = [r for r in rows if r[4] > 0]
first, last = rows[5], rows[-1]
d_scroll = last[1] - first[1]
d_palms = last[4] - first[4]
print(f"  scroll {first[1]:.0f}->{last[1]:.0f} ({d_scroll:.0f}px), "
      f"palms {first[4]:.1f}->{last[4]:.1f} ({d_palms:.1f}px) "
      f"-> ratio {d_palms/d_scroll:.3f}")
