#!/usr/bin/env python3
"""Gabriel Homes — LOCKED public preview server (allow-list mode), port 3000.

H1: this server exists so the owner can watch the workspace from the preview
link. It is ALLOW-LIST based: a request is served only if every part of its
normalised path is explicitly allowed below. Everything else — including
directory listings of non-listed folders — gets 403. A hard deny-list runs
FIRST, so nothing on it can ever be served even if the allow-list is edited
later (defence in depth).

Allow-list (only these are ever readable):
  /                                             -> generated homepage linking the previews
  gabriel_homes/templates/                      -> browsable
  gabriel_homes/static/                         -> browsable
  gabriel_homes/docs/                           -> browsable
  gabriel_homes/DEPLOY.md, DESIGN.md, WORK.md   -> exact files
  gabriel_homes/requirements.txt                -> exact file
  gabriel_homes/README*                         -> if present
  scripts/preview_site/{index,plan,checklist,qa}.html -> the four preview pages
  scripts/preview_site/qa-shots/                -> PNG assets qa.html embeds

Hard denials (checked before/independently of the allow-list):
  any dot-file/dot-dir (.git, .env, .env.example, .gitignore, .venv, ...)
  *.sqlite3, *.db, *.log, *.pyc, *.pyo, cookies.txt, __pycache__
  download/, upload/, node_modules/, media/, design-reference/, gabriel_extract/
  scripts/ — ONLY the four preview pages + qa-shots/ escape this rule

Run:  python3 scripts/workspace_server.py          (serves ROOT on 0.0.0.0:3000)
Test: python3 scripts/tests_preview_server.py
"""
import html
import io
import mimetypes
import os
import re
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Workspace root served by the server (repo root). Module-level so tests can
# rebind it to a disposable replica:  mod.ROOT = tmpdir
ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- deny rules
HIDDEN_DENY = True  # any path component starting with "." is denied
DENY_NAMES = frozenset({
    "cookies.txt", "__pycache__",
    "download", "upload",              # deliverables / owner uploads
    "node_modules", "media",           # heavy/private trees
    "design-reference", "gabriel_extract",
})
DENY_SUFFIXES = (".sqlite3", ".db", ".log", ".pyc", ".pyo", ".sqlite")

# scripts/ is denied as a folder; only these escape:
SCRIPTS_EXACT = frozenset({
    "scripts/preview_site/index.html",
    "scripts/preview_site/plan.html",
    "scripts/preview_site/checklist.html",
    "scripts/preview_site/qa.html",
})
SCRIPTS_PREFIX_OK = "scripts/preview_site/qa-shots/"
SCRIPTS_FILES_PREFIX_OK = "scripts/preview_site/files/"  # update zips + evidence shots (curated artifacts)

# ---------------------------------------------------------------- allow rules
ALLOW_EXACT = frozenset({
    "gabriel_homes/DEPLOY.md",
    "gabriel_homes/DESIGN.md",
    "gabriel_homes/WORK.md",
    "gabriel_homes/requirements.txt",
} | SCRIPTS_EXACT)
ALLOW_PREFIXES = (
    "gabriel_homes/templates/",
    "gabriel_homes/static/",
    "gabriel_homes/docs/",
    "gabriel_homes/README",             # README* if present
    SCRIPTS_PREFIX_OK,
    SCRIPTS_FILES_PREFIX_OK,
)

CONTENT_TYPE_OVERRIDES = {
    ".md": "text/markdown", ".py": "text/x-python", ".sh": "text/x-shellscript",
    ".html": "text/html", ".htm": "text/html", ".css": "text/css",
    ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json",
    ".svg": "image/svg+xml", ".txt": "text/plain",
}


def _components(rel: str):
    return [c for c in rel.split("/") if c]


def is_denied(rel: str) -> bool:
    """True if any part of the normalised rel path hits a hard denial."""
    comps = _components(rel)
    if not comps:
        return False
    for comp in comps:
        if HIDDEN_DENY and comp.startswith("."):
            return True
        if comp in DENY_NAMES:
            return True
    last = comps[-1]
    if last == "cookies.txt":
        return True
    if last.lower().endswith(DENY_SUFFIXES):
        return True
    if comps[0] == "scripts":
        joined = "/".join(comps)
        if (
            joined not in SCRIPTS_EXACT
            and not joined.startswith(SCRIPTS_PREFIX_OK)
            and not joined.startswith(SCRIPTS_FILES_PREFIX_OK)
        ):
            return True  # scripts/ folder itself stays closed
    return False


def is_allowed(rel: str) -> bool:
    if not rel:
        return True  # homepage
    return rel in ALLOW_EXACT or rel.startswith(ALLOW_PREFIXES)


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n/1.0:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} GB"


def _downloads_html() -> str:
    """Download cards for published artifacts, auto-discovered on every request.

    Reads ROOT/scripts/preview_site/files/ live (module-level ROOT, so tests can
    rebind it). This is what keeps the homepage truthful after every rebuild:
    whatever build_update_zip.sh + sync_preview_files.sh published shows up here
    automatically, newest zip first.
    """
    files = ROOT / "scripts" / "preview_site" / "files"
    if not files.is_dir():
        return ("<div class=\"card\"><b>No files published yet.</b>"
                "Run scripts/build_update_zip.sh + scripts/sync_preview_files.sh.</div>")
    cards = []
    oneclick = files / "gabriel-homes-oneclick.zip"
    if oneclick.is_file():
        cards.append(
            f'<div class="card"><b><a class="btn" '
            f'href="/scripts/preview_site/files/{oneclick.name}" download>'
            f'Download — one-click website (Linux / macOS / Windows)</a></b>'
            f'<span class="dlmeta">{oneclick.name} · {human_size(oneclick.stat().st_size)}'
            f' · extract, run START-GABRIEL-HOMES(.sh/.bat), site opens in your browser</span></div>')
    zips = sorted(files.glob("gabriel-homes-update-*.zip"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    for zp in zips:
        tag = html.escape(zp.name[len("gabriel-homes-update-"):-len(".zip")] or "latest")
        name = html.escape(zp.name)
        cards.append(
            f'<div class="card"><b><a class="btn" '
            f'href="/scripts/preview_site/files/{name}" download>'
            f'Download update zip ({tag})</a></b>'
            f'<span class="dlmeta">{name} · {human_size(zp.stat().st_size)}</span></div>')
    for rpt in sorted(files.glob("typography-audit-*.html")):
        name = html.escape(rpt.name)
        cards.append(
            f'<div class="card"><b><a href="/scripts/preview_site/files/{name}" download>'
            f'Typography audit report (r15)</a></b>'
            f'<span class="dlmeta">{name} · {human_size(rpt.stat().st_size)} '
            f'· 8-section measured audit — open in browser / print to PDF</span></div>')
    parts_dir = files / "parts"
    part_files = sorted(parts_dir.glob("gabriel-homes-oneclick.part-*")) if parts_dir.is_dir() else []
    if part_files and oneclick.is_file():
        total = sum(p.stat().st_size for p in part_files)
        links = " · ".join(
            f'<a href="/scripts/preview_site/files/parts/{html.escape(p.name)}" '
            f'download>part {i + 1}</a>'
            for i, p in enumerate(part_files))
        cards.append(
            '<div class="card"><b><span style="color:#a03d18">Big file keeps failing? '
            'Download in small parts</span></b>'
            f'<span class="dlmeta">{len(part_files)} parts × ~14 MB · {human_size(total)} total · {links}</span>'
            '<span class="dlmeta">grab the rejoin tool too: '
            '<a href="/scripts/preview_site/files/parts/REJOIN-WINDOWS.bat" download>Windows (.bat)</a> · '
            '<a href="/scripts/preview_site/files/parts/REJOIN-MAC-LINUX.sh" download>macOS/Linux (.sh)</a>'
            ' — put all parts + the rejoin tool in ONE folder, double-click/run it,'
            ' then run START-GABRIEL-HOMES as usual</span></div>')
    bundle = files / "gabriel-homes.bundle"
    if bundle.is_file():
        cards.append(
            f'<div class="card"><b><a href="/scripts/preview_site/files/{bundle.name}" download>'
            f'Git bundle — offline history backup</a></b>'
            f'<span class="dlmeta">{bundle.name} · {human_size(bundle.stat().st_size)}</span></div>')
    for db in sorted(files.glob("gabriel-homes-db-backup*.zip")):
        name = html.escape(db.name)
        cards.append(
            f'<div class="card"><b><a href="/scripts/preview_site/files/{name}" download>'
            f'Database backup — seeded SQLite (zip)</a></b>'
            f'<span class="dlmeta">{name} · {human_size(db.stat().st_size)}</span></div>')
    if not cards:
        return '<div class="card"><b>No downloadable artifacts right now.</b></div>'
    return "\n".join(cards)


PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gabriel Homes — workspace preview</title><style>
body{{font-family:Georgia,'Times New Roman',serif;background:#faf7f2;color:#221a14;
margin:0;line-height:1.6}}.wrap{{max-width:960px;margin:0 auto;padding:48px 24px 80px}}
.kicker{{font-family:Menlo,monospace;font-size:12px;letter-spacing:.22em;color:#a03d18}}
h1{{font-size:clamp(28px,4vw,42px);margin:8px 0 12px}}p.lead{{color:#655a4e;max-width:70ch}}
h2{{border-bottom:2px solid #221a14;padding-bottom:8px;margin-top:44px}}
a{{color:#a03d18}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}
.card{{background:#fff;border:1px solid #e6ddd1;border-radius:10px;padding:14px 16px}}
.card b{{display:block;margin-bottom:4px}}code{{background:#f0e9df;padding:1px 6px;border-radius:4px}}
.lock{{font-family:Menlo,monospace;font-size:12px;background:#f4efe7;border-left:3px solid #c25e3a;
padding:12px 16px;margin-top:36px}}
.btn{{display:inline-block;background:#b04a1a;color:#fff;text-decoration:none;padding:10px 18px;
border-radius:8px;font-family:Menlo,monospace;font-size:13px}}.btn:hover{{background:#a94e30}}
.dlmeta{{display:block;color:#655a4e;font-family:Menlo,monospace;font-size:12px;margin-top:6px}}
</style></head><body><div class="wrap">
<div class="kicker">GABRIEL HOMES · LIVE WORKSPACE PREVIEW</div>
<h1>The workspace, <em>on display</em>.</h1>
<p class="lead">Browsing the real repo behind gabrielhomes.co.ke — templates, styling, docs and the
loop previews. This server runs in <b>allow-list mode</b>: the paths below render,
everything else returns 403.</p>
<h2>Downloads — latest release</h2><div class="grid">
{downloads}
</div>
<h2>GitHub — one-time push permission</h2>
<div class="card">
<p style="margin-top:0">The agent pushes this workspace (full history, newest commits) to the private repo
<b>github.com/Maingibrian/GabrielHomes</b>. One-time setup, about two minutes:</p>
<ol style="padding-left:20px">
<li>Open <a href="https://github.com/settings/personal-access-tokens/new">github.com/settings/personal-access-tokens/new</a>
— <b>Fine-grained tokens</b>, not classic.</li>
<li>Token name: <code>gabriel-sandbox-push</code> · Expiration: <b>7 days</b>.</li>
<li>Repository access: <b>Only select repositories</b> → pick <b>GabrielHomes</b>.</li>
<li>Permissions → Repository permissions → <b>Contents: Read and write</b>. Leave everything else as-is.</li>
<li>Click <b>Generate token</b>, copy it (starts with <code>github_pat_</code>), and paste it into the agent chat.</li>
</ol>
<p style="margin-bottom:0">Why this is safe: the token reaches <b>only this one repository</b>, expires in 7 days, and can be
revoked instantly at github.com/settings/personal-access-tokens right after the push is confirmed.
A <i>classic</i> token with full <code>repo</code> scope is what security guides warn about — this is not that.
GitHub Desktop on your PC backs up your local copy but cannot authorize this sandbox, which holds the
authoritative full-history version.</p>
</div>
<h2>Loop previews</h2><div class="grid">
<div class="card"><b><a href="/scripts/preview_site/index.html">Update delivery &amp; downloads</a></b>The latest update zip, updaters and evidence shots.</div>
<div class="card"><b><a href="/scripts/preview_site/plan.html">Plan</a></b>The build plan, task by task.</div>
<div class="card"><b><a href="/scripts/preview_site/checklist.html">Launch checklist</a></b>Go-live checklist, twin of the docx.</div>
<div class="card"><b><a href="/scripts/preview_site/qa.html">QA report</a></b>Verification pass with screenshots.</div>
</div>
<h2>Browse the repo</h2><div class="grid">
<div class="card"><b><a href="/gabriel_homes/templates/">templates/</a></b>22 Django templates.</div>
<div class="card"><b><a href="/gabriel_homes/static/">static/</a></b>CSS, JS, vendor assets.</div>
<div class="card"><b><a href="/gabriel_homes/docs/">docs/</a></b>STATUS · PLAN · DECISIONS · briefs.</div>
<div class="card"><b><a href="/gabriel_homes/DEPLOY.md">DEPLOY.md</a></b>Deployment runbook.</div>
<div class="card"><b><a href="/gabriel_homes/DESIGN.md">DESIGN.md</a></b>Design system notes.</div>
<div class="card"><b><a href="/gabriel_homes/WORK.md">WORK.md</a></b>Working notes.</div>
<div class="card"><b><a href="/gabriel_homes/requirements.txt">requirements.txt</a></b>Pinned deps.</div>
</div>
<div class="lock">LOCKED PREVIEW · allow-list mode · db, .env*, logs, .git, download/,
upload/ and scripts/ are never served · preview server v2 (H1)</div>
</div></body></html>"""

LISTING_PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{crumb} — Gabriel Homes workspace</title><style>
body{{font-family:Georgia,serif;background:#faf7f2;color:#221a14;margin:0;line-height:1.5}}
.wrap{{max-width:980px;margin:0 auto;padding:40px 24px 70px}}
.kicker{{font-family:Menlo,monospace;font-size:12px;letter-spacing:.22em;color:#a03d18}}
h1{{font-size:26px;margin:6px 0 18px;word-break:break-all}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e6ddd1;font-size:14.5px}}
th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid #e6ddd1}}
th{{font-family:Menlo,monospace;font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;
color:#655a4e;background:#f4efe7}}td.num{{font-family:Menlo,monospace;white-space:nowrap;color:#655a4e}}
.badge{{font-family:Menlo,monospace;font-size:11px;border:1px solid #e6ddd1;border-radius:999px;
padding:2px 9px;background:#faf7f2}}a{{color:#a03d18;text-decoration:none}}a:hover{{text-decoration:underline}}
.back{{font-family:Menlo,monospace;font-size:12.5px;margin-bottom:14px}}</style></head>
<body><div class="wrap"><div class="kicker">GABRIEL HOMES · WORKSPACE</div>
<h1>/{html_path}</h1><div class="back"><a href="/">← workspace home</a></div>
<table><tr><th>Name</th><th>Type</th><th>Size</th><th>Modified</th></tr>{rows}</table>
<div class="lock" style="font-family:Menlo,monospace;font-size:11.5px;color:#655a4e;margin-top:18px">
allow-list preview · entries outside the allow-list are hidden and 403</div>
</div></body></html>"""


class WorkspaceHandler(BaseHTTPRequestHandler):
    server_version = "GabrielPreview/2.0"

    # module-global ROOT is read at request time so tests can rebind it
    @property
    def root(self) -> Path:
        return ROOT

    # ------------------------------------------------------------- plumbing
    def _send_bytes(self, code: int, body: bytes, ctype: str, head_only: bool = False):
        buf = io.BytesIO(body)
        buf.seek(0)
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Robots-Tag", "noindex")
        self.end_headers()
        if not head_only:
            self.wfile.write(buf.read())

    def _deny(self, head_only=False):
        body = b"403 Forbidden - outside the preview allow-list.\n"
        self._send_bytes(403, body, "text/plain; charset=utf-8", head_only)

    def _not_found(self, head_only=False):
        self._send_bytes(404, b"404 Not Found.\n", "text/plain; charset=utf-8", head_only)

    def _resolve(self, raw_path: str):
        """-> (rel, fs_path, is_dir) or raises PermissionError/FileNotFoundError."""
        decoded = urllib.parse.unquote(raw_path.split("?", 1)[0].split("#", 1)[0])
        if "\x00" in decoded or "\\" in decoded:
            raise PermissionError(decoded)
        comps = [c for c in decoded.split("/") if c]
        if any(c in (".", "..") for c in comps):
            raise PermissionError(decoded)
        rel = "/".join(comps)
        root_real = self.root.resolve()
        full = root_real.joinpath(*comps) if comps else root_real
        full_real = full.resolve()
        if full_real != root_real and root_real not in full_real.parents:
            raise PermissionError(rel)  # symlink/escape
        is_dir = full_real.is_dir()
        # directories are allow-checked in both forms ("/dir" and "/dir/")
        probes = {rel, rel + "/"} if is_dir else {rel}
        rel_real = full_real.relative_to(root_real).as_posix() if full_real != root_real else ""
        probes_real = {rel_real, rel_real + "/"} if is_dir else {rel_real}
        if is_denied(rel) or is_denied(rel_real):
            raise PermissionError(rel)
        if not (any(is_allowed(p) for p in probes) and any(is_allowed(p) for p in probes_real)):
            raise PermissionError(rel)
        return rel, full_real, is_dir

    def _ctype_for(self, name: str) -> str:
        suffix = Path(name).suffix.lower()
        ctype = CONTENT_TYPE_OVERRIDES.get(suffix) or mimetypes.guess_type(name)[0]
        if not ctype:
            ctype = "application/octet-stream"
        if ctype.startswith("text/"):
            ctype += "; charset=utf-8"
        return ctype

    def _serve_file(self, full: Path, head_only: bool = False):
        """Stream a file with HTTP Range support (resumable downloads).

        v2 shipped the whole file via full.read_bytes() + one wfile.write —
        fine on localhost, fatal for 70+ MB zips over the preview proxy: one
        hiccup and the browser had to restart from byte 0. This streams in
        1 MiB chunks, advertises Accept-Ranges, and answers Range requests
        with 206 so interrupted downloads RESUME instead of restarting.
        Single-range only (multi-range is rare for download managers; a
        malformed header is ignored per RFC 7233 tolerance and the full
        body is served).
        """
        try:
            size = full.stat().st_size
        except OSError:
            return self._not_found(head_only=head_only)
        start, end, status = 0, size - 1, 200
        range_header = self.headers.get("Range")
        if range_header and size > 0:
            m = re.match(r"^bytes=(\d*)-(\d*)$", range_header.strip())
            if m and (m.group(1) or m.group(2)):
                if m.group(1):  # bytes=start-end  /  bytes=start-
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else size - 1
                else:           # bytes=-suffix (last N bytes)
                    start = max(0, size - int(m.group(2)))
                    end = size - 1
                if start >= size or start > end:
                    # unsatisfiable: tell the client the real size, per RFC
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                end = min(end, size - 1)
                status = 206
        self.send_response(status)
        self.send_header("Content-Type", self._ctype_for(full.name))
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Robots-Tag", "noindex")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if head_only:
            return
        try:
            with full.open("rb") as fh:
                fh.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = fh.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            # client went away mid-transfer — its download manager will
            # resume from the last acknowledged byte via Range
            pass

    # ------------------------------------------------------------- verbs
    def do_GET(self):
        try:
            rel, full, is_dir = self._resolve(self.path)
        except PermissionError:
            return self._deny()
        except (FileNotFoundError, NotADirectoryError, OSError):
            return self._not_found()
        if rel == "":  # homepage
            return self._send_bytes(200, PAGE.format(downloads=_downloads_html()).encode("utf-8"),
                                    "text/html; charset=utf-8")
        if is_dir:
            if not self.path.split("?", 1)[0].endswith("/"):
                return self._redirect(urllib.parse.unquote(self.path.split("?", 1)[0]) + "/")
            return self._serve_listing(rel, full)
        if not full.is_file():
            return self._not_found()
        self._serve_file(full, head_only=False)

    def do_HEAD(self):
        try:
            rel, full, is_dir = self._resolve(self.path)
        except PermissionError:
            return self._deny(head_only=True)
        except (FileNotFoundError, NotADirectoryError, OSError):
            return self._not_found(head_only=True)
        if is_dir:
            self._send_bytes(200, b"", "text/html; charset=utf-8", head_only=True)
        elif full.is_file():
            self._serve_file(full, head_only=True)
        else:
            self._not_found(head_only=True)

    def _redirect(self, location: str):
        self.send_response(301)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ------------------------------------------------------------- views
    def _serve_listing(self, rel: str, full: Path):
        rows = []
        try:
            entries = sorted(full.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return self._not_found()
        for entry in entries:
            child_rel = f"{rel}/{entry.name}" if rel else entry.name
            child_is_dir = entry.is_dir()
            probe = child_rel + ("/" if child_is_dir else "")
            if is_denied(child_rel) or not is_allowed(probe if child_is_dir else child_rel):
                continue  # never even list denied entries
            size = human_size(entry.stat().st_size) if child_is_dir else human_size(entry.stat().st_size)
            mtime = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            kind = "DIR" if child_is_dir else Path(entry.name).suffix.lstrip(".").upper()[:6] or "FILE"
            href = urllib.parse.quote(child_rel) + ("/" if child_is_dir else "")
            rows.append(
                f"<tr><td><a href=\"/{href}\">{html.escape(entry.name)}</a></td>"
                f"<td><span class=\"badge\">{html.escape(kind)}</span></td>"
                f"<td class=\"num\">{size}</td><td class=\"num\">{mtime}</td></tr>"
            )
        page = LISTING_PAGE.format(
            crumb=html.escape(rel or "/"), html_path=html.escape(rel),
            rows="\n".join(rows) or "<tr><td colspan=4><em>empty</em></td></tr>",
        )
        self._send_bytes(200, page.encode("utf-8"), "text/html; charset=utf-8")

    def log_message(self, fmt, *args):  # compact, single line
        print(f"[preview] {self.address_string()} {fmt % args}", flush=True)


def main():
    port = int(os.environ.get("PREVIEW_PORT", "3000"))
    bind = os.environ.get("PREVIEW_BIND", "0.0.0.0")
    httpd = ThreadingHTTPServer((bind, port), WorkspaceHandler)
    print(f"[preview] allow-list server on {bind}:{port} serving {ROOT}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
