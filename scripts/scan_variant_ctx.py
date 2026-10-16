#!/usr/bin/env python3
"""Show every occurrence of 'Variant' in the JS with surrounding context."""
import re

SRC = "/home/z/my-project/gabriel_homes/design-reference/index.html"
with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    html = f.read()

hits = [m.start() for m in re.finditer(r"Variant", html)]
print(f"'Variant' occurrences: {len(hits)}")
for i, pos in enumerate(hits):
    chunk = html[max(0, pos - 160):pos + 240]
    chunk = re.sub(r"\s+", " ", chunk)
    print(f"\n[{i}] @{pos}: {chunk}")
