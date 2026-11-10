"""r38 — F1 tokenisation pass over search.css (one-shot, idempotence-checked).

Replaces the 10 hard-coded hex literals in static/css/search.css:
  8x #fff     -> var(--white)      (token exists: --white #ffffff)
  2x #e7e4df  -> var(--map-stage)  (new token added to tokens.css this run)

Prints the exact replacement counts; refuses to run twice (exits 1 if no
hex remains, so the file cannot be double-processed by accident).
"""
import re
import sys
from pathlib import Path

CSS = Path("static/css/search.css")
text = CSS.read_text(encoding="utf-8")

before_hex = re.findall(r"#[0-9a-fA-F]{3,8}", text)
if not before_hex:
    print("search.css already has zero hex literals — nothing to do")
    sys.exit(1)

n_white = len(re.findall(r"#fff\b", text))
n_stage = len(re.findall(r"#e7e4df\b", text))
text = re.sub(r"#fff\b", "var(--white)", text)
text = re.sub(r"#e7e4df\b", "var(--map-stage)", text)

after_hex = re.findall(r"#[0-9a-fA-F]{3,8}", text)
if after_hex:
    print("UNEXPECTED residual hex:", after_hex)
    sys.exit(1)

CSS.write_text(text, encoding="utf-8")
print(f"replaced: {n_white}x #fff -> var(--white), "
      f"{n_stage}x #e7e4df -> var(--map-stage); "
      f"search.css now has 0 hex literals (was {len(before_hex)})")
assert (n_white, n_stage) == (8, 2), "expected exactly 8 + 2 replacements"
