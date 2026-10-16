#!/usr/bin/env python3
"""Find every Framer variant-class map in the export JS, then diff the CSS
between Variant 1 and Variant 2 classes to reveal what each hover animates."""
import re

SRC = "/home/z/my-project/gabriel_homes/design-reference/index.html"
with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    html = f.read()

# 1) All variant -> class maps: {"Variant 1":`XXXXX`,"Variant 2":`YYYYY`}  (backticks or quotes)
pairs = re.findall(r'\{\s*[`"\']Variant 1[`"\']\s*:\s*[`"\'](\w+)[`"\']\s*,\s*[`"\']Variant 2[`"\']\s*:\s*[`"\'](\w+)[`"\']', html)
print(f"variant class pairs: {len(pairs)} -> {pairs[:20]}")

# 2) Pull the full CSS text
styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S))

# index rules by class name: selector { body }
import collections
rules_by_class = collections.defaultdict(list)
for rule in styles.split("}"):
    if "{" not in rule:
        continue
    sel, body = rule.split("{", 1)
    sel = sel.strip()
    body = body.strip()
    for m in re.finditer(r'\.([\w-]+)', sel):
        rules_by_class[m.group(1)].append((sel[:80], body))

def show(cls):
    out = []
    for sel, body in rules_by_class.get(cls, []):
        out.append(f"  {sel} {{ {body[:300]} }}")
    return "\n".join(out) if out else "  (no css rule found)"

for v1, v2 in pairs:
    print("\n" + "=" * 90)
    print(f"VARIANT PAIR: V1={v1}  V2={v2}")
    print("--- V1 css ---")
    print(show(v1))
    print("--- V2 css ---")
    print(show(v2))
