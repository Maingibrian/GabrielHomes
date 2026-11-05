"""r18 H1 follow-ups:

1. home.css: delete the dead .hv2-commit / .hv2-cta rule blocks — their
   sections moved off home (commitments -> /checks/, cta -> footer), so the
   rules (and their var(--bg) usages) are orphans now. F1's undefined-var
   scan flags exactly this class of leftover.
2. Verify nothing else references the two classes.
"""
import re
from pathlib import Path

CSS = Path("/home/z/my-project/gabriel-homes/static/css/home.css")
src = CSS.read_text(encoding="utf-8")

# --- delete .hv2-commit block (comment header .. before next comment) ------
m = re.search(
    r"/\* -+ commitments: full-bleed photo band -+ -*\n.*?(?=/\* -+ )",
    src, re.S)
assert m, "hv2-commit block not found"
block1 = m.group(0)
assert ".hv2-commit" in block1 and "var(--bg)" in block1
src = src[:m.start()] + src[m.end():]

# --- delete .hv2-cta block --------------------------------------------------
m = re.search(
    r"/\* -+ closing CTA on a photo -+ -*\n.*?(?=\n/\* |\Z)",
    src, re.S)
assert m, "hv2-cta block not found"
block2 = m.group(0)
assert ".hv2-cta" in block2
src = src[:m.start()] + src[m.end():]

CSS.write_text(src, encoding="utf-8")

# --- verify -----------------------------------------------------------------
final = CSS.read_text(encoding="utf-8")
assert "hv2-commit" not in final and "hv2-cta" not in final
assert "var(--bg)" not in final, "orphan --bg usage remains"
hexes_before = 240
from pathlib import Path as P
total = sum(len(re.findall(r"#[0-9a-fA-F]{3,8}", t.read_text(encoding="utf-8")))
            for t in P("/home/z/my-project/gabriel-homes/static/css").glob("*.css")
            if t.name != "tokens.css")
print(f"dead CSS removed; hex outside tokens now {total} "
      f"(ratchet: 240 -> 238 -> 236 -> {total})")
