#!/usr/bin/env python3
"""Scan the Framer design-reference export for hover-variant transitions.
Framer sites encode hover effects as "Variant 1" -> "Variant 2" switches with
transition JSON (spring/tween). This prints the transition payloads and the
style deltas around each Variant 2 hit, so we can rebuild the hover in CSS.
"""
import re
import json

SRC = "/home/z/my-project/gabriel_homes/design-reference/index.html"

with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    html = f.read()

print(f"file chars: {len(html)}")

# 1) All transition-looking JSON payloads
trans = re.findall(r'"type":"(spring|tween)"[^}]{0,200}', html)
from collections import Counter
c = Counter(trans)
print("\n--- transition payloads (count x sample) ---")
for payload, n in c.most_common(12):
    print(f"x{n}: {payload[:180]}")

# 2) Context around each "Variant 2" occurrence
print("\n--- Variant 2 contexts (300 chars before, 700 after) ---")
for i, m in enumerate(re.finditer(r'"Variant 2"|data-framer-name="Variant 2"', html)):
    if i >= 6:
        break
    s = max(0, m.start() - 300)
    e = min(len(html), m.end() + 700)
    ctx = html[s:e]
    # strip nothing; just show it compactly
    print(f"\n[hit {i}] @{m.start()}\n{ctx}\n{'='*80}")

# 3) Framer appear/hover animation blocks: look for "animations" with trigger
trigs = re.findall(r'"trigger":"[^"]+"', html)
print("\n--- triggers ---")
print(Counter(trigs).most_common(10))
