#!/usr/bin/env python3
"""Globally de-duplicate a11y findings into distinct component-level issues."""
import json
from collections import defaultdict

data = json.load(open("/home/z/my-project/gabriel_homes/docs/a11y/findings.json"))
g = defaultdict(lambda: {"pages": set(), "vp": set(), "texts": set(), "min": 21, "rec": None})
for page, rows in data.items():
    if page.startswith("_"): continue
    for r in rows:
        if not isinstance(r, dict): continue
        kind = r.get("kind")
        if kind in ("nav-error", "eval-error", "login-failed", "h-overflow", "console"):
            k = (kind, page, r.get("t","")[:60])
            g[k]["pages"].add(page)
            g[k]["rec"] = r
            continue
        if kind == "contrast":
            # bucket by component signature: fg+bg colors + class prefix + size class
            cls = (r.get("cls","") or "").split()[0:2]
            sig = (r.get("fg"), r.get("bg"), tuple(cls), r.get("tag"), r.get("imageBg"))
            k = ("contrast", sig)
            gg = g[k]
            gg["pages"].add(page); gg["vp"].add(r.get("vp"))
            gg["texts"].add(r.get("t","")[:45]); gg["min"] = min(gg["min"], r.get("ratio",21))
            gg["rec"] = r
        elif kind in ("unlabeled", "img-alt", "no-name", "tiny"):
            sig = (kind, tuple((r.get("cls","") or "").split()[0:2]), r.get("tag"), r.get("t","")[:30] if kind!="img-alt" else "")
            k = sig
            g[k]["pages"].add(page); g[k]["vp"].add(r.get("vp"))
            g[k]["texts"].add(r.get("t","")[:45]); g[k]["rec"] = r

rows = []
for k, v in g.items():
    rec = v["rec"]
    rows.append({
        "issue": k[0],
        "where": ", ".join(sorted(v["pages"]))[:80],
        "n_pages": len(v["pages"]),
        "vp": "/".join(sorted(v["vp"])),
        "min_ratio": v["min"] if k[0]=="contrast" else "",
        "sample_text": (list(v["texts"])[0] if v["texts"] else "")[:45],
        "detail": rec,
    })

contrast = sorted([r for r in rows if r["issue"]=="contrast"], key=lambda r: r["min_ratio"])
others = sorted([r for r in rows if r["issue"]!="contrast"], key=lambda r: (-r["n_pages"], r["issue"]))

print(f"== DISTINCT contrast issues: {len(contrast)} ==")
for r in contrast:
    d = r["detail"]
    print(f"  ratio {r['min_ratio']:<5} need {d.get('need')}  [{d.get('tag')}.{(d.get('cls') or '')[:38]}]  vp:{r['vp']}")
    print(f"      fg={d.get('fg')}  bg={d.get('bg')}  imgBg={d.get('imageBg')}  fs={d.get('fs')}px")
    print(f"      text=\"{r['sample_text']}\"  on {r['n_pages']} page(s): {r['where'][:70]}")
print(f"\n== OTHER distinct issues: {len(others)} ==")
for r in others:
    d = r["detail"]
    print(f"  [{r['issue']}] vp:{r['vp']}  {r['sample_text'][:40]}  tag={d.get('tag')} cls={(d.get('cls') or '')[:40]}  on {r['n_pages']}p: {r['where'][:60]}")
