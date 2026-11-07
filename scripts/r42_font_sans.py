#!/usr/bin/env python3
"""r42 (owner request): retire the thin Geist Mono "microtext" site-wide.

The token --font-mono was repointed to the Geist sans in tokens.css (single
source of truth — covers all ~110 call sites including the 2 inline template
styles). This script floors the WEIGHTS so nothing renders thin:

  - uppercase micro labels / counters / badges  -> font-weight >= 600
  - sentence-case small print / meta            -> font-weight >= 500
  - already >= target                           -> untouched
  - punctuation-only glyph blocks               -> skipped (no visible delta)

Sizes and letter-spacing are NOT touched (sub-13px ratchet + layout pins).
Only lines/blocks referencing var(--font-mono) are modified.
"""
import re
import pathlib

ROOT = pathlib.Path("/home/z/my-project/gabriel-homes")
FILES = [
    "static/css/components.css",
    "static/css/home.css",
    "static/css/search.css",
    "static/css/detail.css",
    "static/css/pages.css",
    "static/css/dashboard.css",
    "static/css/manage.css",
]

# Blocks that are punctuation-only glyph carriers — a weight change is invisible.
SKIP = {".pagination__ellipsis", ".related__link-arrow"}

# Sentence-case small print / meta -> 500. Everything else (uppercase labels,
# counters, badges, index numbers) -> 600.
SENTENCE_500 = {
    ".agent-card__meta",
    ".agent-contact",
    ".listing-card__facts",
    ".site-footer__copyright",
    ".results-header__count",
    ".browse__link-count",
    ".prose__updated",
    ".dashboard-sidebar__count",
    ".import-columns code",
    ".manage-check__auto",
    "#detail-map > p",
    ".detail-map__error",
    ".detail-map__hint",
    ".detail-map .maplibregl-ctrl-attrib",
}

# One-liner rules in home.css/search.css/detail.css that use the `font:`
# shorthand WITH a weight already (keep) or WITHOUT (insert 600 — they are
# all uppercase eyebrows/facts/meta strips).
SHORTHAND_WANT = 600

changed = {}
for rel in FILES:
    path = ROOT / rel
    src = path.read_text()
    lines = src.split("\n")
    out = []
    i = 0
    edits = []
    n = len(lines)
    while i < n:
        ln = lines[i]
        out.append(ln)
        i += 1

    # ---- pass A: font-family blocks (multi-line rules) ----
    # Rebuild with block awareness: find rule blocks containing var(--font-mono)
    text = "\n".join(out)
    # Split into (selector, body) chunks at top level
    chunk_re = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
    # Protect @media blocks: process only leaf rules (simple split keeps media
    # wrappers intact because their inner braces nest — handle by scanning).
    # We'll operate line-wise instead — simpler and safer for this codebase
    # (every font-mono rule is a flat leaf rule; media wrappers only contain
    # complete leaf rules).

    lines = text.split("\n")
    # map: line index -> current selector stack
    out2 = list(lines)
    stack = []
    block_has_mono = {}
    for idx, ln in enumerate(lines):
        stripped = ln.strip()
        if stripped.endswith("{") and not stripped.startswith("@"):
            stack.append(stripped[:-1].strip())
        elif stripped == "}":
            if stack:
                stack.pop()
        if "var(--font-mono" in ln and stack:
            block_has_mono[idx] = list(stack)

    # For each line with font-mono, find its block boundaries (from the line
    # to the closing brace) and apply the weight floor.
    processed_blocks = set()
    for idx in sorted(block_has_mono):
        # find block start: the nearest previous line ending with '{'
        start = idx
        while start > 0 and not lines[start].strip().endswith("{"):
            start -= 1
        # find block end
        end = idx
        while end < len(lines) - 1 and lines[end].strip() != "}":
            end += 1
        if (start, end) in processed_blocks:
            continue
        processed_blocks.add((start, end))
        selector = lines[start].strip()[:-1].strip()
        # media-scoped selector: prepend parent
        sel_match = selector
        # resolve stack at block start for full selector
        stk = []
        depth = 0
        for j in range(0, start + 1):
            s = lines[j].strip()
            if s.endswith("{"):
                stk.append(s[:-1].strip())
            elif s == "}" and stk:
                stk.pop()
        full_sel = " ".join(stk)
        if sel_match in SKIP or any(s in SKIP for s in stk):
            continue

        block = lines[start : end + 1]
        block_text = "\n".join(block)
        if "var(--font-mono" not in block_text:
            continue

        is_upper = "text-transform: uppercase" in block_text or "text-transform:uppercase" in block_text
        want = 500 if any(sel in full_sel for sel in SENTENCE_500) else (600 if is_upper or full_sel in SENTENCE_500 else 600)
        # default to 600 for unknown/caseless label blocks (counters, indexes)
        if any(sel in full_sel for sel in SENTENCE_500):
            want = 500

        new_block = block_text

        # Case 1: standalone font-weight line inside the block
        mw = re.search(r"(font-weight:\s*)(\d{3})", new_block)
        # Case 2: font: shorthand carrying var(--font-mono) on that line
        shorthand_lines = [l for l in new_block.split("\n") if re.search(r"font:\s*[^;]*var\(--font-mono", l)]
        if mw and not shorthand_lines:
            cur = int(mw.group(2))
            if cur < want:
                new_block = new_block[: mw.start(2)] + str(want) + new_block[mw.end(2) :]
                edits.append(f"L{start+1} {full_sel[:56]}: font-weight {cur} -> {want}")
        elif shorthand_lines:
            for sl in shorthand_lines:
                m = re.search(r"font:\s*(\d{3})?\s*", sl)
                if m.group(1):
                    cur = int(m.group(1))
                    if cur < want:
                        new_sl = sl[: m.start(1)] + str(want) + sl[m.end(1) :]
                        new_block = new_block.replace(sl, new_sl)
                        edits.append(f"L{start+1} {full_sel[:56]}: shorthand weight {cur} -> {want}")
                else:
                    new_sl = sl.replace("font: ", f"font: {want} ", 1)
                    new_block = new_block.replace(sl, new_sl)
                    edits.append(f"L{start+1} {full_sel[:56]}: shorthand +{want} weight")
        else:
            # no weight anywhere: insert after the font-family line (or after
            # the shorthand font: line, or before the closing brace)
            fl = [l for l in new_block.split("\n") if "var(--font-mono" in l]
            if fl:
                anchor = fl[0]
                indent = anchor[: len(anchor) - len(anchor.lstrip())]
                new_block = new_block.replace(
                    anchor, anchor + f"\n{indent}font-weight: {want};", 1
                )
                edits.append(f"L{start+1} {full_sel[:56]}: + font-weight {want}")
        lines[start : end + 1] = new_block.split("\n")

    final = "\n".join(lines)
    if final != src:
        path.write_text(final)
    changed[rel] = edits

total = 0
for rel, edits in changed.items():
    print(f"\n=== {rel}: {len(edits)} edit(s) ===")
    for e in edits:
        print("   " + e)
    total += len(edits)
print(f"\nTOTAL: {total} weight edits")
