"""Convert {% static %} -> {% staticv %} for .css/.js assets in all templates."""
import re
from pathlib import Path

ROOT = Path("/home/z/my-project/gabriel_homes/templates")

pat_load = re.compile(r"\{%\-?\s*load\s+static\s+([a-z_ ]*?)\s*-?%\}")
pat_ref = re.compile(r"\{%\-?\s*static\s+(['\"])([^'\"]+\.(?:css|js))\1\s*-?%\}")

changed = []
for f in sorted(ROOT.rglob("*.html")):
    src = f.read_text()
    orig = src

    def fix_load(m):
        rest = m.group(1).strip()
        mods = {"static"} | set(rest.split())
        if "core_tags" not in mods:
            mods.add("core_tags")
        return "{% load " + " ".join(sorted(mods)) + " %}"

    src = pat_load.sub(fix_load, src)
    src = pat_ref.sub(lambda m: f"{{% staticv '{m.group(2)}' %}}", src)
    if src != orig:
        f.write_text(src)
        changed.append(str(f.relative_to(ROOT)))

print("changed:", len(changed))
for c in changed:
    print(" -", c)
# sanity: any leftover plain static css/js refs?
left = []
for f in ROOT.rglob("*.html"):
    for m in pat_ref.finditer(f.read_text()):
        left.append(f"{f}: {m.group(0)}")
print("leftover plain static css/js:", len(left))
for l in left:
    print(" !", l)
