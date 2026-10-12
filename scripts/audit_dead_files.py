#!/usr/bin/env python3
"""Dead-file audit for the gabriel_homes repo (read-only; deletes nothing).

Sections:
  1. MEDIA  - every FileField/ImageField value from every model (DB truth)
              vs files on disk under media/ and property-images/.
  2. STATIC - every file under static/ checked against a reference corpus
              (templates, css, js, python, shell, makefile, docs).
  3. TEMPLATES - every template checked for a render/include/extends ref.

A file is reported dead only when NO reference matches, first by
repo-relative path tail (last 2 components), then by basename.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/gabriel_homes")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
sys.path.insert(0, str(REPO))

import django  # noqa: E402

django.setup()

from django.apps import apps  # noqa: E402
from django.db import models as djm  # noqa: E402


def db_media_refs() -> set[str]:
    """All FileField/ImageField values across every model."""
    refs: set[str] = set()
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, (djm.FileField, djm.ImageField)):
                vals = (
                    model._default_manager.exclude(**{field.name: ""})
                    .values_list(field.name, flat=True)
                    .distinct()
                )
                for v in vals:
                    if v:
                        refs.add(str(v))
    return refs


def corpus() -> str:
    """Concatenated text of every file that may reference assets."""
    chunks: list[str] = []
    patterns = ["*.html", "*.css", "*.js", "*.py", "*.sh", "*.md", "*.txt",
                "*.json", "Makefile", "*.toml", "*.cfg", "*.example"]
    roots = [
        REPO / "templates", REPO / "static", REPO / "apps", REPO / "config",
        REPO / "scripts", REPO / "docs", REPO,
    ]
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        if root == REPO:
            files = [p for p in root.iterdir() if p.is_file()]
        else:
            files = [p for p in root.rglob("*") if p.is_file()]
        for p in files:
            if p in seen or p.stat().st_size > 3_000_000:
                continue
            if any(p.match(pat) for pat in patterns):
                seen.add(p)
                try:
                    chunks.append(p.read_text(errors="ignore"))
                except OSError:
                    pass
    return "\n".join(chunks)


def tail2(rel: str) -> str:
    parts = Path(rel).parts
    return "/".join(parts[-2:]) if len(parts) >= 2 else rel


def static_audit(text: str) -> list[dict]:
    static_dir = REPO / "static"
    report = []
    for p in sorted(static_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(REPO).as_posix()          # static/img/real/real-01.jpg
        rel2 = tail2(rel)                              # real/real-01.jpg
        base = p.name                                  # real-01.jpg
        # staticv/url tags strip 'static/'; css urls use ../img/...;
        # match on tail2 and basename to cover all spellings.
        by_path = rel2 in text
        by_base = base in text
        report.append({
            "file": rel, "by_path": by_path, "by_base": by_base,
            "dead": not (by_path or by_base),
        })
    return report


def template_audit() -> list[dict]:
    tdir = REPO / "templates"
    templates = sorted(p.relative_to(tdir).as_posix() for p in tdir.rglob("*.html"))
    corpus_text = corpus()
    app_text = []
    for p in list((REPO / "apps").rglob("*.py")) + list((REPO / "config").rglob("*.py")):
        app_text.append(p.read_text(errors="ignore"))
    app_blob = "\n".join(app_text)
    report = []
    for t in templates:
        base = Path(t).name
        inc = re.search(r"[%{]\s*(?:include|extends)\s+[\"']" + re.escape(t), corpus_text)
        inc_base = re.search(r"[%{]\s*(?:include|extends)\s+[\"'][^\"']*" + re.escape(base), corpus_text)
        rendered = re.search(re.escape(t), app_blob)
        rendered_base = re.search(r"[\"'][^\"']*" + re.escape(base) + r"[\"']", app_blob)
        referenced = bool(inc or inc_base or rendered or rendered_base)
        report.append({"file": t, "referenced": referenced})
    return report


def main() -> int:
    print("=" * 70)
    print("SECTION 1 — MEDIA vs DB FileFields")
    refs = db_media_refs()
    print(f"DB-referenced media values: {len(refs)}")
    disk_media: set[str] = set()
    for root in ("media", "property-images"):
        base = REPO / root
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file():
                    disk_media.add(p.relative_to(REPO).as_posix())
    # normalize: DB values are MEDIA_ROOT-relative; disk is repo-relative
    norm_refs = set()
    for r in refs:
        norm_refs.add(r)
        norm_refs.add(f"media/{r}")
        norm_refs.add(f"property-images/{r}")
    orphans = sorted(disk_media - norm_refs)
    print(f"media/+property-images on disk: {len(disk_media)}")
    print(f"-- orphan candidates ({len(orphans)}) --")
    for o in orphans:
        sz = (REPO / o).stat().st_size
        print(f"  {o}  ({sz/1024:.0f}K)")

    print("=" * 70)
    print("SECTION 2 — STATIC asset references")
    rep = static_audit(corpus())
    dead = [r for r in rep if r["dead"]]
    print(f"static files: {len(rep)}, dead candidates: {len(dead)}")
    for d in dead:
        print(f"  {d['file']}")

    print("=" * 70)
    print("SECTION 3 — TEMPLATE orphans")
    trep = template_audit()
    orph = [t for t in trep if not t["referenced"]]
    print(f"templates: {len(trep)}, unreferenced: {len(orph)}")
    for t in orph:
        print(f"  {t['file']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
