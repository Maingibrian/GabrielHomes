#!/usr/bin/env python3
"""Compare upload/bento-shift.patch's intended content vs the current tree.

- bento-shift.js: patch carries the FULL new file (/dev/null -> file), so
  reconstruct it from the '+' lines and diff against static/js/bento-shift.js.
- home.css / components.css / home.html: the patch's '+' lines describe the
  added content; check each added snippet for a verbatim home in the tree.
"""
import pathlib, re, sys

ROOT = pathlib.Path("/home/z/my-project")
PATCH = (ROOT / "upload/bento-shift.patch").read_text(errors="replace")
GH = ROOT / "gabriel_homes"

# --- split the patch into per-file sections ---
sections = re.split(r"^--- ", PATCH, flags=re.M)[1:]  # drop preamble


def plus_lines(section: str) -> list[str]:
    out = []
    for ln in section.splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            out.append(ln[1:])
    return out


def target_of(section: str) -> str:
    m = re.search(r"^\+\+\+ (\S+)", section, flags=re.M)
    return m.group(1) if m else "?"


for sec in sections:
    tgt = target_of(sec)
    adds = plus_lines(sec)
    print(f"== {tgt}: {len(adds)} added lines")
    if tgt.endswith("/dev/null") or "bento-shift.js" in tgt and "/dev/null" in sec:
        continue

# bento-shift.js full content = plus lines of its section
js_sec = next((s for s in sections if "bento-shift.js" in s and "/dev/null" in s), None)
if js_sec:
    patched_js = "\n".join(plus_lines(js_sec)) + "\n"
    cur_js = (GH / "static/js/bento-shift.js").read_text()
    if patched_js == cur_js:
        print("bento-shift.js: IDENTICAL to patch")
    else:
        import difflib
        d = list(difflib.unified_diff(cur_js.splitlines(), patched_js.splitlines(),
                                      "tree", "patch", lineterm="", n=1))
        print(f"bento-shift.js DIFFERS ({len(d)} diff lines):")
        print("\n".join(d[:40]))

# home.css appended block: compare as normalized text
home_css = (GH / "static/css/home.css").read_text()
css_sec = next((s for s in sections if s.startswith("a/static/css/home.css") or "b/static/css/home.css" in s.splitlines()[0]), None)
if css_sec:
    block = "\n".join(plus_lines(css_sec))
    # check a few sentinel lines verbatim
    sentinels = ["3c. Homes bento", ".bento-grid--shift { position: relative; }",
                 "corner-shape: superellipse(1.6);", "--spot-row, 1) / span 2;",
                 "saturate(0);", "prefers-reduced-motion: reduce"]
    for s in sentinels:
        print(f"home.css has {s!r}: {s in home_css}")

# components.css comment
comp_css = (GH / "static/css/components.css").read_text()
print("components.css has 'shared base stays photo-only':", "shared base stays photo-only" in comp_css)
print("components.css has old r8 line:", "r8's desaturate-reveal was a" in comp_css)

# home.html scripts block
home_html = (GH / "templates/core/home.html").read_text()
print("home.html has scripts block:", "{% block scripts %}" in home_html)
print("home.html has grid--shift:", "bento-grid--shift" in home_html)
base_html = (GH / "templates/base.html").read_text()
print("base.html includes bento-shift.js:", "bento-shift.js" in base_html)
