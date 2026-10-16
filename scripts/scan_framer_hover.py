#!/usr/bin/env python3
"""Extract all :hover CSS rules (and keyframe/animation rules) from the
Framer design-reference export, so we can see the card hover animation
the owner's reference actually ships with."""
import re

SRC = "/home/z/my-project/gabriel_homes/design-reference/index.html"

with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    html = f.read()

# Grab <style> blocks
styles = re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S)
css = "\n".join(styles)
print(f"style blocks: {len(styles)}, total css chars: {len(css)}")

# Split into rules on '}' (works even for minified single-line CSS)
rules = [r.strip() for r in css.split("}") if r.strip()]
hover_rules = [r for r in rules if ":hover" in r]
anim_rules = [r for r in rules if "@keyframes" in r or "animation" in r]

print(f"\n--- :hover rules ({len(hover_rules)}) ---")
seen = set()
for r in hover_rules:
    sel = r.split("{")[0].strip()[:100]
    body = r[r.find("{") + 1:].strip()
    key = (sel, body[:80])
    if key in seen:
        continue
    seen.add(key)
    print(f"{sel} {{ {body[:220]} }}")

print(f"\n--- keyframes/animations ({len(anim_rules)}) ---")
for r in anim_rules[:10]:
    print(r[:200])

# Also: any 'scale(' or 'translateY(' inside hover rules is the smoking gun
print("\n--- hover rules that transform/scale/filter ---")
for r in hover_rules:
    if any(k in r for k in ("scale(", "translate", "filter", "opacity", "grayscale")):
        sel = r.split("{")[0].strip()[:110]
        body = r[r.find("{") + 1:].strip()
        print(f"{sel} {{ {body[:260]} }}\n")
