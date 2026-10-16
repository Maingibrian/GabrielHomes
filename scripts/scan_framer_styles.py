#!/usr/bin/env python3
"""Find framer-motion variant style objects in the export JS:
   {"Variant 1":{<styles>},"Variant 2":{<styles>}} and print the style deltas."""
import re

SRC = "/home/z/my-project/gabriel_homes/design-reference/index.html"
with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    html = f.read()

# JS uses backticks or double quotes for keys
hits = [m.start() for m in re.finditer(r'[`"\']Variant 2[`"\']\s*:\s*\{', html)]
print(f"Variant 2 style objects: {len(hits)}")

for i, pos in enumerate(hits):
    # find the matching start of the whole object (backtrack to 'Variant 1')
    v1 = html.rfind("Variant 1", max(0, pos - 60), pos)
    start = html.rfind("{", max(0, v1 - 5), v1) if v1 != -1 else pos
    chunk = html[start:pos + 900]
    # compact print
    chunk = re.sub(r"\s+", " ", chunk)
    print(f"\n=== variant obj {i} @{start} ===")
    print(chunk[:1100])
