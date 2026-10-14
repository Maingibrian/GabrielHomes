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


PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gabriel Homes — workspace preview</title><style>
body{{font-family:Georgia,'Times New Roman',serif;background:#faf7f2;color:#221a14;
margin:0;line-height:1.6}}.wrap{{max-width:960px;margin:0 auto;padding:48px 24px 80px}}
.kicker{{font-family:Menlo,monospace;font-size:12px;letter-spacing:.22em;color:#c25e3a}}
h1{{font-size:clamp(28px,4vw,42px);margin:8px 0 12px}}p.lead{{color:#7a6f63;max-width:70ch}}
h2{{border-bottom:2px solid #221a14;padding-bottom:8px;margin-top:44px}}
a{{color:#c25e3a}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}
.card{{background:#fff;border:1px solid #e6ddd1;border-radius:10px;padding:14px 16px}}
.card b{{display:block;margin-bottom:4px}}code{{background:#f0e9df;padding:1px 6px;border-radius:4px}}
.lock{{font-family:Menlo,monospace;font-size:12px;background:#f4efe7;border-left:3px solid #c25e3a;
padding:12px 16px;margin-top:36px}}</style></head><body><div class="wrap">
<div class="kicker">GABRIEL HOMES · LIVE WORKSPACE PREVIEW</div>
<h1>The workspace, <em>on display</em>.</h1>
<p class="lead">Browsing the real repo behind gabrielhomes.co.ke — templates, styling, docs and the
loop previews. This server runs in <b>allow-list mode</b>: the paths below render,
everything else returns 403.</p>
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
.kicker{{font-family:Menlo,monospace;font-size:12px;letter-spacing:.22em;color:#c25e3a}}
h1{{font-size:26px;margin:6px 0 18px;word-break:break-all}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e6ddd1;font-size:14.5px}}
th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid #e6ddd1}}
th{{font-family:Menlo,monospace;font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;
color:#7a6f63;background:#f4efe7}}td.num{{font-family:Menlo,monospace;white-space:nowrap;color:#7a6f63}}
.badge{{font-family:Menlo,monospace;font-size:11px;border:1px solid #e6ddd1;border-radius:999px;
padding:2px 9px;background:#faf7f2}}a{{color:#c25e3a;text-decoration:none}}a:hover{{text-decoration:underline}}
.back{{font-family:Menlo,monospace;font-size:12.5px;margin-bottom:14px}}</style></head>
<body><div class="wrap"><div class="kicker">GABRIEL HOMES · WORKSPACE</div>
<h1>/{html_path}</h1><div class="back"><a href="/">← workspace home</a></div>
<table><tr><th>Name</th><th>Type</th><th>Size</th><th>Modified</th></tr>{rows}</table>
<div class="lock" style="font-family:Menlo,monospace;font-size:11.5px;color:#7a6f63;margin-top:18px">
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

    # ------------------------------------------------------------- verbs
    def do_GET(self):
        try:
            rel, full, is_dir = self._resolve(self.path)
        except PermissionError:
            return self._deny()
        except (FileNotFoundError, NotADirectoryError, OSError):
            return self._not_found()
        if rel == "":  # homepage
            return self._send_bytes(200, PAGE.format().encode("utf-8"), "text/html; charset=utf-8")
        if is_dir:
            if not self.path.split("?", 1)[0].endswith("/"):
                return self._redirect(urllib.parse.unquote(self.path.split("?", 1)[0]) + "/")
            return self._serve_listing(rel, full)
        if not full.is_file():
            return self._not_found()
        body = full.read_bytes()
        self._send_bytes(200, body, self._ctype_for(full.name))

    def do_HEAD(self):
        try:
            rel, full, is_dir = self._resolve(self.path)
        except PermissionError:
            return self._deny(head_only=True)
        except (FileNotFoundError, NotADirectoryError, OSError):
            return self._not_found(head_only=True)
        if is_dir:
            self._send_bytes(200, b"", "text/html; charset=utf-8", head_only=True)
        else:
            self._send_bytes(200, b"", self._ctype_for(full.name),
                             head_only=True) if full.is_file() else self._not_found(head_only=True)

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
