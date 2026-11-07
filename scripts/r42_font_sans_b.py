#!/usr/bin/env python3
"""r42 pass B: weight floor for the remaining font-mono rules — this pass
matches ALL leaf rules (selector { body }) via regex, so one-liner rules and
rules inside @media wrappers are caught too. Blocks already floored by pass A
carry a weight >= target and are skipped."""
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

SKIP = {".pagination__ellipsis", ".related__link-arrow"}
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

LEAF = re.compile(r"([^{}]+?)\{\s*([^{}]*?var\(--font-mono[^{}]*?)\s*\}", re.S)

def want_for(sel, body):
    if any(s in sel for s in SENTENCE_500):
        return 500
    return 600

total = 0
for rel in FILES:
    path = ROOT / rel
    src = path.read_text()
    edits = []

    def fix(m):
        global total
        sel = " ".join(m.group(1).split())
        body = m.group(2)
        if any(s in sel for s in SKIP):
            return m.group(0)
        want = want_for(sel, body)

        # 1) standalone font-weight in body
        mw = re.search(r"font-weight:\s*(\d{3})", body)
        # 2) font: shorthand that references the mono token
        msh = re.search(r"font:\s*(\d{3})?\s*[^;{}]*var\(--font-mono[^;{}]*;?", body)
        if msh:
            if msh.group(1):
                cur = int(msh.group(1))
                if cur >= want:
                    return m.group(0)
                new = body[: msh.start(1)] + str(want) + body[msh.end(1) :]
                edits.append(f"{sel[:58]}: shorthand {cur} -> {want}")
                return m.group(1).join([]) or None  # unreachable
            # no weight in shorthand -> insert
            new_body = re.sub(r"font:\s*", f"font: {want} ", body, count=1)
            new_body = new_body.replace(f"font: {want} ", f"font: {want} ", 1)
            # ensure only the shorthand line got the weight (font-family: must not match)
            if "font-family" in body and "font-family: var(--font-mono" in body:
                # block has both: only add weight line, don't touch shorthand-less family
                pass
            edits.append(f"{sel[:58]}: shorthand +{want}")
            return m.group(1) + "{" + new_body + "}"
        if mw:
            cur = int(mw.group(1))
            if cur >= want:
                return m.group(0)
            new = body[: mw.start(1)] + str(want) + body[mw.end(1) :]
            edits.append(f"{sel[:58]}: font-weight {cur} -> {want}")
            return m.group(1) + "{" + new + "}"
        # no weight anywhere -> insert after font-family line
        mff = re.search(r"font-family:\s*var\(--font-mono[^;]*;", body)
        if mff:
            new = body[: mff.end()] + f" font-weight: {want};" + body[mff.end() :]
            edits.append(f"{sel[:58]}: + font-weight {want}")
            return m.group(1) + "{" + new + "}"
        return m.group(0)

    # Simpler, robust approach: iterate leaf matches and rebuild manually
    out = []
    pos = 0
    for m in LEAF.finditer(src):
        sel = " ".join(m.group(1).split())
        body = m.group(2)
        if any(s in sel for s in SKIP):
            continue
        want = want_for(sel, body)
        new_body = body
        changed = False

        msh = re.search(r"(?<![-a-z])font:\s*(\d{3})?\s*[^;{}]*var\(--font-mono[^;{}]*", body)
        mw = re.search(r"font-weight:\s*(\d{3})", body)
        if msh and not mw:
            if msh.group(1) and int(msh.group(1)) >= want:
                pass
            elif msh.group(1):
                new_body = body[: msh.start(1)] + str(want) + body[msh.end(1) :]
                edits.append(f"{sel[:58]}: shorthand {msh.group(1)} -> {want}")
                changed = True
            else:
                new_body = body[: msh.start()] + msh.group(0).replace("font:", f"font: {want} ", 1) + body[msh.end() :]
                edits.append(f"{sel[:58]}: shorthand +{want}")
                changed = True
        elif mw:
            cur = int(mw.group(1))
            if cur < want:
                new_body = body[: mw.start(1)] + str(want) + body[mw.end(1) :]
                edits.append(f"{sel[:58]}: font-weight {cur} -> {want}")
                changed = True
        elif msh is None and mw is None:
            mff = re.search(r"font-family:\s*var\(--font-mono[^;]*;", body)
            if mff:
                new_body = body[: mff.end()] + f" font-weight: {want};" + body[mff.end() :]
                edits.append(f"{sel[:58]}: + font-weight {want}")
                changed = True
        if changed:
            out.append((m.start(), m.end(), m.group(1) + "{" + new_body + "}"))
    # apply edits back-to-front
    result = src
    for start, end, replacement in reversed(out):
        result = result[:start] + replacement + result[end:]
    if result != src:
        path.write_text(result)
    total += len(edits)
    print(f"\n=== {rel}: {len(edits)} edit(s) ===")
    for e in edits:
        print("   " + e)

print(f"\nTOTAL pass B: {total} edits")
