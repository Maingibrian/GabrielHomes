"""r69 E3 — pixel proof of the half-speed palm drift.

Screenshots A (y=2200) and B (y=3200), viewport 1600x1000 (sentinels
off below 1620px, so the gutters are pure palm field over cream).

Expected: the CONTENT moved up exactly 1000px between the shots; the
FIELD moved up by (1000 - drift_delta) = ~444-556px depending on the
late layout shifts measured during the session. Anything firmly
between "0" (stagnant, the r68 fixed pass) and "1000" (glued to the
listings) is the parallax; the correlation finds the exact figure.
"""
import numpy as np
from PIL import Image

A = np.asarray(Image.open("/tmp/e3/r69-a-y2200.png").convert("L"), dtype=float)
B = np.asarray(Image.open("/tmp/e3/r69-b-y3200.png").convert("L"), dtype=float)
H, W = A.shape
print(f"shots {W}x{H}")

# gutter strips: left 0..150, right W-150..W (container is 1280 wide,
# centered -> gutters are (1600-1280)/2 = 160px each side)
strips = {}
for name, x0, x1 in (("left", 0, 150), ("right", W - 150, W)):
    pa = A[:, x0:x1].mean(axis=1)   # per-row mean intensity profile
    pb = B[:, x0:x1].mean(axis=1)
    strips[name] = (pa, pb)

for name, (pa, pb) in strips.items():
    # normalised cross-correlation over vertical shifts 0..900:
    # shift s means B[y] ~= A[y + s]  (field moved UP by s)
    best_s, best_c = 0, -2.0
    for s in range(0, 900):
        a = pa[s:] - pa[s:].mean()
        b = pb[: H - s] - pb[: H - s].mean()
        denom = np.sqrt((a * a).sum() * (b * b).sum())
        if denom == 0:
            continue
        c = (a * b).sum() / denom
        if c > best_c:
            best_c, best_s = c, s
    print(f"{name:>5} gutter: field moved UP {best_s}px  (r={best_c:.3f})")

# control: the card column (centre) must have moved the full 1000px —
# different cards are in view, so the strip is simply DIFFERENT (mean
# abs diff high), while the gutters stay same-pattern.
centre_a = A[:, 300:1300]
centre_b = B[:, 300:1300]
print(f"centre column mean|diff| = {np.abs(centre_a - centre_b).mean():.1f} (content fully changed)")
for name, (pa, pb) in strips.items():
    print(f"{name:>5} gutter  mean|diff| = {np.abs(pa - pb).mean():.1f} (same pattern, shifted)")
