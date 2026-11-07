"""r17 F1 survey — one-off analysis to size the token-integrity ratchets.

Reports:
  1. var(--x) usages with NO definition and NO fallback, per css file
     (definitions = tokens.css + component :root blocks)
  2. --font-body references
  3. --paper references and whether tokens.css defines it
  4. font sizes below 13px (px only — rem flows from the root scale)
  5. hard-coded hex colours outside tokens.css (the ratchet baseline)
"""
import re
from collections import Counter
from pathlib import Path

CSS = Path("/home/z/my-project/gabriel-homes/static/css")
files = sorted(CSS.glob("*.css"))

defns = set()
for f in files:
    text = f.read_text(encoding="utf-8")
    if f.name == "tokens.css":
        defns |= set(re.findall(r"(--[a-z0-9-]+)\s*:", text))
    else:
        for root in re.findall(r":root\s*\{(.*?)\}", text, re.S):
            defns |= set(re.findall(r"(--[a-z0-9-]+)\s*:", root))

print("== 1. undefined var() with no fallback:")
undef = Counter()
for f in files:
    text = f.read_text(encoding="utf-8")
    for m in re.finditer(r"var\(\s*(--[a-z0-9-]+)\s*(,[^)]*)?\)", text):
        if m.group(1) not in defns and not m.group(2):
            undef[f"{f.name} {m.group(1)}"] += 1
for k, v in sorted(undef.items()):
    print(f"   {k} x{v}")
if not undef:
    print("   (none)")

all_css = {f.name: f.read_text(encoding="utf-8") for f in files}
print("== 2. --font-body refs:")
for name, t in all_css.items():
    n = t.count("--font-body")
    if n:
        print(f"   {name} x{n}")

print("== 3. --paper: defined in tokens.css:",
      bool(re.search(r"--paper\s*:", all_css["tokens.css"])))
for name, t in all_css.items():
    n = len(re.findall(r"var\(--paper", t))
    if n:
        print(f"   var(--paper uses in {name} x{n}")

print("== 4. font sizes < 13px (px literals, font-size: and font: shorthand):")
sub = Counter()
ctx = {}
for name, t in all_css.items():
    for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", t):
        if float(m.group(1)) < 13:
            sub[f"{name} {m.group(1)}px"] += 1
            ctx.setdefault(f"{name} {m.group(1)}px", []).append(
                t[max(0, m.start() - 70):m.end() + 20].replace("\n", " "))
    for m in re.finditer(r"(?<![a-z-])font\s*:[^;{}]*?(\d+(?:\.\d+)?)px", t):
        if float(m.group(1)) < 13:
            sub[f"{name} {m.group(1)}px"] += 1
            ctx.setdefault(f"{name} {m.group(1)}px", []).append(
                t[max(0, m.start() - 70):m.end() + 20].replace("\n", " "))
for k, v in sorted(sub.items()):
    print(f"   {k} x{v}")
    for c in ctx[k][:3]:
        print(f"      ...{c.strip()}...")
print(f"   TOTAL sub-13px occurrences: {sum(sub.values())}")

print("== 5. hard-coded hex outside tokens.css (ratchet baseline):")
total = 0
for name in sorted(all_css):
    if name == "tokens.css":
        continue
    n = len(re.findall(r"#[0-9a-fA-F]{3,8}\b", all_css[name]))
    total += n
    print(f"   {name}: {n}")
print(f"   HEX BASELINE (outside tokens.css): {total}")
