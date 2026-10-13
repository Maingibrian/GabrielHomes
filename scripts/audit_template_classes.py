"""audit_template_classes.py — find template classes with NO CSS rules.

For each template, extracts every class token from class="..." attributes
and checks whether any stylesheet defines a selector containing it.
Special-cases Django-with-classes inside {% if %} etc. Reports tokens that
appear in NO css file (potential invisible/broken styling).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

GH = Path("/home/z/my-project/gabriel_homes")
CSS_DIR = GH / "static" / "css"

# tokens that are state hooks / JS hooks / shared utilities known-good
KNOWN_STATE = {
    "is-open", "is-visible", "is-lit", "is-active", "is-hidden", "is-collapsed",
    "motion-ready", "site-header--scrolled", "hero--compact",
}

def css_text() -> str:
    return "\n".join(p.read_text() for p in sorted(CSS_DIR.glob("*.css")))

def class_tokens(template_text: str) -> set[str]:
    toks: set[str] = set()
    for m in re.finditer(r'class="([^"{}]+)"', template_text):
        for t in m.group(1).split():
            t = t.strip()
            if t and not t.startswith("{"):
                toks.add(t)
    # class="{{ ... }}" or class="x {{ var }}" — skip purely dynamic
    return toks

def main() -> int:
    css = css_text()
    failures = 0
    templates = sys.argv[1:] or [
        "templates/core/about.html",
        "templates/core/services.html",
        "templates/listings/listing_detail.html",
        "templates/listings/search.html",
        "templates/agents/agent_directory.html",
        "templates/core/contact.html",
    ]
    for rel in templates:
        p = GH / rel
        if not p.exists():
            print(f"SKIP missing: {rel}")
            continue
        toks = class_tokens(p.read_text())
        missing = []
        for t in sorted(toks):
            if t in KNOWN_STATE:
                continue
            # a class is "defined" if it appears in css as .t (word-boundary)
            if not re.search(r"\." + re.escape(t) + r"(?![\w-])", css):
                missing.append(t)
        status = "OK " if not missing else "GHOST"
        print(f"{status} {rel}: {len(toks)} classes, {len(missing)} undefined")
        for t in missing:
            failures += 1
            print(f"    - .{t}")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
