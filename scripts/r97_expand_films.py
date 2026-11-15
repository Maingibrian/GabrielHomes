"""r97 — regenerate both flank-reel films with 7 sets (21 frames).

The loop math (r95) translates exactly one --reel-set-h = 3 frames +
3 gaps, so the set is the 3-photo cycle; the film ships the cycle 7x
so the word→edge window (worst case ~1137px @1440) is always covered
with one full set to spare. Keeps each frame's exact attrs (staticv,
lazy, 180x120) — only the repetition changes.
"""
import re
from pathlib import Path

TPL = Path(__file__).resolve().parents[1] / "gabriel-homes-advanced-r64" / "gabriel-homes" / "templates" / "core" / "home.html"
html = TPL.read_text(encoding="utf-8")

SET = 7   # sets per reel (21 frames)

films = re.findall(r'<div class="flank-reel__film">(.*?)</div>', html, re.S)
assert len(films) == 2, f"expected 2 films, found {len(films)}"

for film in films:
    frames = re.findall(r'<img class="flank-reel__frame"[^>]*>', film)
    assert len(frames) == 6 and frames[0] == frames[3], (
        f"expected the r95 set x2 (6 frames, first repeats 4th), found {len(frames)}"
    )
    cycle = frames[:3]   # the 3-photo set the loop translates
    new_film = "\n" + "\n".join(
        f"        {f}" for _ in range(SET) for f in cycle) + "\n      "
    html = html.replace(film, new_film, 1)

TPL.write_text(html, encoding="utf-8")

# verify
html2 = TPL.read_text(encoding="utf-8")
for block in re.findall(r'<div class="flank-reel__film">(.*?)</div>', html2, re.S):
    n = block.count("flank-reel__frame")
    print(f"film frames: {n}")
    assert n == 21
print("OK: both reels now ship 7 sets (21 frames)")
