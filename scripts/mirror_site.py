#!/usr/bin/env python3
"""Build a self-contained, offline-browsable mirror of the Gabriel Homes site.

Fetches every sitemap URL (+ extras) from the live dev server, downloads all
referenced static/media assets, rewrites all internal links to relative paths,
and writes everything under download/site-mirror/ so the workspace file panel
can serve it like a real website.
"""
from __future__ import annotations

import posixpath
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import requests

BASE = "http://127.0.0.1:3000"
OUT = Path("/home/z/my-project/download/site-mirror")

session = requests.Session()
session.headers["User-Agent"] = "site-mirror/1.0"


def clean(path: str) -> str:
    """Path without query/fragment."""
    return urlsplit(path).path


def url_to_file(path: str) -> str:
    p = clean(path)
    p = p.lstrip("/")
    if p == "":
        return "index.html"
    if p.endswith("/"):
        return p + "index.html"
    base = posixpath.basename(p)
    if "." in base:
        return p
    return p + "/index.html"


def rel_link(target_file: str, from_file: str) -> str:
    """Relative href from a mirror file to another mirror file."""
    d = posixpath.dirname(from_file)
    if d == "":
        return target_file
    return posixpath.relpath(target_file, d)


# ---------------------------------------------------------------------------
# 1. Seed URL list
# ---------------------------------------------------------------------------
sm = session.get(BASE + "/sitemap.xml", timeout=30)
seed_paths = [urlsplit(u).path for u in re.findall(r"<loc>([^<]+)</loc>", sm.text)]
extra = ["/", "/properties/", "/agents/", "/checks/", "/services/"]
seen: set[str] = set()
queue: list[str] = []
for p in seed_paths + extra:
    if p not in seen:
        seen.add(p)
        queue.append(p)

# ---------------------------------------------------------------------------
# 2. Fetch pages
# ---------------------------------------------------------------------------
page_map: dict[str, str] = {}  # requested path -> mirror file
page_contents: dict[str, bytes] = {}
asset_paths: set[str] = set()

ATTR_RE = re.compile(r'([a-zA-Z-]+)\s*=\s*["\'](/(?:static|media)/[^"\']+)["\']')
SRCSET_RE = re.compile(r'(srcset)\s*=\s*["\']([^"\']+)["\']')
STYLE_URL_RE = re.compile(r"url\(\s*[\"']?(/(?:static|media)/[^)\"\']+)[\"']?\s*\)")
LINK_RE = re.compile(r'(href|action)\s*=\s*(["\'])(/[^"\']*)\2', re.IGNORECASE)

print(f"fetching up to {len(queue)} seeded pages (BFS over all internal links) ...")
n_fail = 0
n_fetched = 0
i = 0
while i < len(queue):
    path = queue[i]
    i += 1
    try:
        r = session.get(BASE + path, timeout=30)
    except requests.RequestException as e:
        print(f"  FAIL {path}: {e}")
        n_fail += 1
        continue
    if r.status_code != 200:
        print(f"  {r.status_code} {path} (final: {r.url})")
        n_fail += 1
        continue
    final_path = "/" + urlsplit(r.url).path.lstrip("/")
    f = url_to_file(final_path)
    page_map[path] = f
    page_map[final_path] = f
    page_contents[f] = r.content
    n_fetched += 1
    # collect assets referenced by this page
    for m in ATTR_RE.finditer(r.text):
        asset_paths.add(clean(m.group(2)))
    for m in STYLE_URL_RE.finditer(r.text):
        asset_paths.add(clean(m.group(1)))
    for m in SRCSET_RE.finditer(r.text):
        for part in m.group(2).split(","):
            u = part.strip().split(" ")[0]
            if u.startswith(("/static/", "/media/")):
                asset_paths.add(clean(u))
    # enqueue newly discovered internal pages
    for m in LINK_RE.finditer(r.text):
        p2 = clean(m.group(3))
        if p2 in seen or p2.startswith(("/static/", "/media/")):
            continue
        if p2.startswith(("/admin", "/account", "/manage", "/dashboard", "/search", "/newsletter")):
            continue
        seen.add(p2)
        queue.append(p2)

print(f"pages ok: {n_fetched} unique files: {len(page_contents)}  failed: {n_fail}")

# ---------------------------------------------------------------------------
# 3. Fetch assets
# ---------------------------------------------------------------------------
asset_map: dict[str, str] = {}  # asset path -> mirror file
asset_ok = 0
for a in sorted(asset_paths):
    f = a.lstrip("/")
    try:
        r = session.get(BASE + a, timeout=30)
        if r.status_code != 200:
            print(f"  asset {r.status_code} {a}")
            continue
        (OUT / f).parent.mkdir(parents=True, exist_ok=True)
        (OUT / f).write_bytes(r.content)
        asset_map[a] = f
        asset_ok += 1
    except requests.RequestException as e:
        print(f"  asset FAIL {a}: {e}")

print(f"assets ok: {asset_ok}/{len(asset_paths)}")

# second pass: css url() references
css_url_re = re.compile(r"url\(\s*['\"]?(/(?:static|media)/[^)'\"]+)['\"]?\s*\)")
for f in list(asset_map.values()):
    if not f.endswith(".css"):
        continue
    txt = (OUT / f).read_text(errors="replace")
    for m in css_url_re.finditer(txt):
        a = clean(m.group(1))
        if a in asset_map:
            continue
        try:
            r = session.get(BASE + a, timeout=30)
            if r.status_code == 200:
                af = a.lstrip("/")
                (OUT / af).parent.mkdir(parents=True, exist_ok=True)
                (OUT / af).write_bytes(r.content)
                asset_map[a] = af
                print(f"  css-imported {af}")
        except requests.RequestException:
            pass

# third pass: ES module worker/sibling imports inside .mjs files
MJS_SIB_RE = re.compile(r"[\w-]+\.(?:mjs|js|css|wasm)")
for f in list(asset_map.values()):
    if not f.endswith(".mjs"):
        continue
    txt = (OUT / f).read_text(errors="replace")
    base_dir = posixpath.dirname(f)
    for name in set(MJS_SIB_RE.findall(txt)):
        a = "/" + posixpath.join(base_dir, name) if base_dir else "/" + name
        if a in asset_map:
            continue
        if (OUT / a.lstrip("/")).exists():
            continue
        try:
            r = session.get(BASE + a, timeout=30)
            if r.status_code == 200:
                af = a.lstrip("/")
                (OUT / af).parent.mkdir(parents=True, exist_ok=True)
                (OUT / af).write_bytes(r.content)
                asset_map[a] = af
                print(f"  mjs-imported {af}")
        except requests.RequestException:
            pass
OFFLINE = Path("offline.html")
page_contents[OFFLINE.as_posix()] = (
    """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Not in the offline mirror</title>
<style>
body{margin:0;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:#faf9f7;
display:flex;align-items:center;justify-content:center;min-height:100vh;color:#1f2937}
.card{max-width:480px;padding:40px;background:#fff;border:1px solid #e5e7eb;border-radius:12px}
h1{font-size:20px;margin:0 0 10px}p{line-height:1.6;color:#6b7280;margin:0 0 18px}
a{color:#e8590c;font-weight:600;text-decoration:none}
</style></head><body><div class="card">
<h1>This page isn't part of the offline mirror</h1>
<p>Login, dashboard and form-submission pages need the live server. Browse the
mirrored public pages instead — listings, locations, about, contact.</p>
<a href="index.html">&larr; Back to the homepage</a>
</div></body></html>
""".encode()
)

# ---------------------------------------------------------------------------
# 5. Write pages with rewritten links
# ---------------------------------------------------------------------------
ALL_FILES = set(page_contents.keys()) | set(asset_map.values())

unmapped: set[str] = set()


def rewrite_html(html: str, fname: str) -> str:
    def to_rel(target: str) -> str:
        return rel_link(target, fname)

    # asset attributes (any attribute whose value is /static/... or /media/...)
    def attr_sub(m):
        attr, val = m.group(1), m.group(2)
        key = clean(val)
        # JS module specifiers are resolved relative to the *script* that
        # imports them (static/js/*.js), not the page — special-case these.
        if attr in ("data-maplibre-src", "data-module-src"):
            tgt = asset_map.get(key, key.lstrip("/"))
            if (OUT / tgt).exists():
                # base = static/js/ (dirname of the importing script)
                return f'{attr}="{rel_link(tgt, "static/js/_module.js")}"'
        if key in asset_map:
            return f'{attr}="{to_rel(asset_map[key])}"'
        # undownloaded asset variant (e.g. 2x srcset) -> drop query, best effort
        af = key.lstrip("/")
        if (OUT / af).exists():
            return f'{attr}="{to_rel(af)}"'
        unmapped.add(val)
        return m.group(0)

    html = ATTR_RE.sub(attr_sub, html)

    # inline style url('...') references
    def style_sub(m):
        key = clean(m.group(1))
        if key in asset_map:
            return f"url({to_rel(asset_map[key])})"
        af = key.lstrip("/")
        if (OUT / af).exists():
            return f"url({to_rel(af)})"
        unmapped.add(m.group(1))
        return m.group(0)

    html = STYLE_URL_RE.sub(style_sub, html)

    # srcset lists
    def srcset_sub(m):
        parts = []
        for part in m.group(2).split(","):
            u = part.strip().split(" ")
            key = clean(u[0])
            if key in asset_map or (OUT / key.lstrip("/")).exists():
                tgt = asset_map.get(key, key.lstrip("/"))
                u[0] = to_rel(tgt)
            parts.append(" ".join(u))
        return f'srcset="{" ,".join(parts)}"'

    html = SRCSET_RE.sub(srcset_sub, html)

    # internal page links & form actions
    def link_sub(m):
        attr, q, val = m.group(1), m.group(2), m.group(3)
        key = clean(val)
        if key in page_map:
            return f'{attr}={q}{to_rel(page_map[key])}{q}'
        if key in asset_map:
            return f'{attr}={q}{to_rel(asset_map[key])}{q}'
        if key in ("", "/"):
            return f'{attr}={q}{to_rel("index.html")}{q}'
        # known-live-page shapes that need the server
        if key.startswith(("/admin", "/account", "/manage", "/dashboard", "/search", "/newsletter")):
            unmapped.add(val)
            return f'{attr}={q}{to_rel("offline.html")}{q}'
        af = url_to_file(key)
        if af in ALL_FILES:
            return f'{attr}={q}{to_rel(af)}{q}'
        # a page we never fetched (non-200 seed etc.)
        unmapped.add(val)
        return f'{attr}={q}{to_rel("offline.html")}{q}'

    html = LINK_RE.sub(link_sub, html)
    # anchors with only query (#...)
    return html


written = 0
for fname, content in page_contents.items():
    if fname == "offline.html":
        (OUT / fname).write_bytes(content)
        written += 1
        continue
    html = content.decode("utf-8", errors="replace")
    (OUT / fname).parent.mkdir(parents=True, exist_ok=True)
    (OUT / fname).write_text(rewrite_html(html, fname), encoding="utf-8")
    written += 1

print(f"wrote {written} pages + {len(asset_map)} assets -> {OUT}")
if unmapped:
    print(f"unmapped internal refs ({len(unmapped)}):")
    for u in sorted(unmapped)[:25]:
        print("   ", u)
