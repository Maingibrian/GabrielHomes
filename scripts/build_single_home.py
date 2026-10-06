#!/usr/bin/env python3
"""
Build a single-file, fully self-contained HTML snapshot of the Gabriel Homes
home page:
  - ALL CSS (tokens + components + base + home) inlined into ONE <style> block
  - ALL JS (motion.js) inlined into ONE <script> block at the end of <body>
  - ALL assets (fonts, favicon, hero/CTA/founder/listing/agent images)
    embedded as base64 data URIs (images resized + recompressed first)

Input : /tmp/home_rendered.html (curl'd from the live Django server)
Output: /home/z/my-project/download/gabriel-homes-homepage.html
"""
import base64
import io
import re
import sys
from pathlib import Path

from PIL import Image

GH = Path("/home/z/my-project/gabriel_homes")
SRC_HTML = Path("/tmp/home_rendered.html")
OUT_HTML = Path("/home/z/my-project/download/gabriel-homes-homepage.html")

GENERATED = "2026-10-05"

# ---------------------------------------------------------------- helpers ---
def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def encode_data_uri(img_bytes: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(img_bytes).decode('ascii')}"

def process_jpg(path: Path, max_w: int, quality: int) -> str:
    """Resize to max_w (if wider), recompress, return jpeg data URI."""
    im = Image.open(path)
    if im.mode != "RGB":
        im = im.convert("RGB")
    if im.width > max_w:
        h = round(im.height * max_w / im.width)
        im = im.resize((max_w, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return encode_data_uri(buf.getvalue(), "image/jpeg")

def process_svg(path: Path) -> str:
    raw = path.read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")

# ------------------------------------------------------------- 1. images ---
print("[1/6] processing images ...")
IMG = {
    "/static/img/hero-bg.jpg": process_jpg(GH / "static/img/hero-bg.jpg", 1600, 78),
    "/static/img/cta-bg.jpg":  process_jpg(GH / "static/img/cta-bg.jpg", 1600, 78),
    "/static/img/founder.jpg": process_jpg(GH / "static/img/founder.jpg", 640, 80),
}

# every media image referenced by the rendered page (covers + agency portraits)
html_src = read(SRC_HTML)
media_refs = sorted(set(re.findall(r'(?:src="|url\([\'"]?)(/media/[^"\')]+?\.jpg)', html_src)))
print(f"      found {len(media_refs)} media refs: {media_refs}")
for ref in media_refs:
    fs = GH / "media" / ref[len("/media/"):]
    if "agency-logos" in ref:
        IMG[ref] = process_jpg(fs, 520, 80)
    else:  # listing covers
        IMG[ref] = process_jpg(fs, 800, 75)

FAVICON = process_svg(GH / "static/img/favicon.svg")

# -------------------------------------------------------------- 2. fonts ---
print("[2/6] embedding fonts ...")
FONTS = {}
for name, fname in [
    ("Geist", "Geist-Variable.woff2"),
    ("Geist Mono", "GeistMono-Variable.woff2"),
    ("Fraunces", "Fraunces-Variable-normal.woff2"),
    ("Fraunces-italic", "Fraunces-Variable-italic.woff2"),
]:
    b = (GH / "static/fonts" / fname).read_bytes()
    FONTS[fname] = encode_data_uri(b, "font/woff2")

# --------------------------------------------------------------- 3. css ----
print("[3/6] assembling ONE <style> block (tokens -> components -> base -> home) ...")
tokens_css = read(GH / "static/css/tokens.css")
components_css = read(GH / "static/css/components.css")
base_css = read(GH / "static/css/base.css")
home_css = read(GH / "static/css/home.css")

# strip @import lines from base.css (we concatenate in exact cascade order)
base_css = re.sub(r'@import\s+url\([^)]*\);', '/* @import inlined above */', base_css)

css_all = "\n".join([
    "/* ============ tokens.css ============ */", tokens_css,
    "/* ============ components.css ============ */", components_css,
    "/* ============ base.css ============ */", base_css,
    "/* ============ home.css ============ */", home_css,
])

# fonts -> data URIs
for fname, uri in FONTS.items():
    css_all = css_all.replace(f'../fonts/{fname}', uri)
# hero/cta images referenced from home.css
css_all = css_all.replace('../img/hero-bg.jpg', IMG["/static/img/hero-bg.jpg"])
css_all = css_all.replace('../img/cta-bg.jpg', IMG["/static/img/cta-bg.jpg"])

# --------------------------------------------------------------- 4. html ---
print("[4/6] rewriting HTML (links -> style, script inline, images -> data URIs) ...")
html = html_src

# favicon
html = re.sub(
    r'(<link rel="icon"[^>]*href=")/static/img/favicon\.svg(")',
    lambda m: m.group(1) + FAVICON + m.group(2), html)

# drop preconnect + canonical (meaningless in a standalone file)
html = re.sub(r'\s*<link rel="preconnect"[^>]*>\n?', '\n', html)
html = re.sub(r'\s*<link rel="canonical"[^>]*>\n?', '\n', html)

# ONE <style> replaces both stylesheet links
style_block = "<style>\n" + css_all + "\n</style>"
html = re.sub(
    r'\s*<link rel="stylesheet" href="/static/css/base\.css">',
    lambda m: '\n  ' + style_block, html, count=1)
html = re.sub(r'\s*<link rel="stylesheet" href="/static/css/home\.css">', '', html, count=1)

# images in <img src> and inline background-image url('...')
for ref, uri in IMG.items():
    html = html.replace(f'src="{ref}"', f'src="{uri}"')
    html = html.replace(f"url('{ref}')", f"url('{uri}')")

# ONE <script> replaces the deferred external one (inline at same spot = end of body)
motion_js = read(GH / "static/js/motion.js")
# safety: avoid premature </script> inside the JS
motion_js = motion_js.replace("</script>", "<\\/script>")
html = re.sub(
    r'\s*<script src="/static/js/motion\.js" defer></script>',
    lambda m: '\n  <script>\n' + motion_js + '\n  </script>', html, count=1)

# provenance banner right after <!doctype html>
banner = (
    f"<!--\n"
    f"  Gabriel Homes — HOME PAGE, single-file edition (generated {GENERATED}).\n"
    f"  Everything is in this one file:\n"
    f"    - ALL CSS (tokens + components + base + home)  -> one <style> block in <head>\n"
    f"    - ALL JS (motion.js: counters, reveals, menu, search bar) -> one <script> block before </body>\n"
    f"    - Fonts, favicon, hero/CTA/photography  -> base64 data URIs\n"
    f"  Open directly in any browser (double-click). No server needed.\n"
    f"  Note: the location-autocomplete fetch() and links to other pages are\n"
    f"  inert in the standalone file — this is a faithful visual snapshot.\n"
    f"-->\n"
)
html = html.replace("<!doctype html>", "<!doctype html>\n" + banner, 1)

# -------------------------------------------------------------- 5. audit ---
print("[5/6] auditing for external references ...")
leftovers = []
for pat in [r'src="/static/', r'src="/media/', r'href="/static/', r'href="/media/',
            r'url\("/static/', r"url\('/static/", r'url\("/media/', r"url\('/media/",
            r'url\("\.\./', r"url\('\.\./"]:
    hits = re.findall(pat, html)
    if hits:
        leftovers.append((pat, len(hits)))
if leftovers:
    print("      !! EXTERNAL REFS REMAIN:", leftovers)
    sys.exit(1)

OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
OUT_HTML.write_text(html, encoding="utf-8")
size_mb = OUT_HTML.stat().st_size / 1e6
print(f"[6/6] OK -> {OUT_HTML}  ({size_mb:.2f} MB, {len(html):,} chars)")
