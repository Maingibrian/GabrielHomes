#!/usr/bin/env python3
"""H1 regression tests — locked public preview server (scripts/workspace_server.py).

stdlib only (no Django). Builds a disposable workspace REPLICA in a temp dir
(dummy db.sqlite3 bytes — never touches the real database), starts the real
handler in a thread on a free port, and asserts the security matrix:

  403 (denied):  db.sqlite3, scripts/server.log, download/, .git/config,
                 .env.example, .env, upload/, manage.py, media/, any file that
                 is not on the allow-list, raw and percent-encoded traversal,
                 the scripts/ folder itself
  200 (allowed): / (homepage), gabriel_homes/templates/ (listing),
                 gabriel_homes/static, gabriel_homes/docs/STATUS.md,
                 gabriel_homes/requirements.txt, the four preview pages
                 (index/plan/checklist/qa) + qa-shots assets

Run:  python3 scripts/tests_preview_server.py
"""
import importlib.util
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

SERVER_FILE = Path(__file__).resolve().parent / "workspace_server.py"


def load_server_module():
    spec = importlib.util.spec_from_file_location("workspace_server", SERVER_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_fake_workspace(root: Path) -> None:
    """Replica good enough for routing tests; all content is dummy bytes."""
    gh = root / "gabriel_homes"
    (gh / "templates").mkdir(parents=True)
    (gh / "static" / "css").mkdir(parents=True)
    (gh / "docs").mkdir(parents=True)
    (gh / "media" / "property-images").mkdir(parents=True)
    (root / "scripts" / "preview_site" / "qa-shots").mkdir(parents=True)
    (root / "download").mkdir()
    (root / "upload").mkdir()
    (root / ".git").mkdir()

    (root / ".git" / "config").write_text("[core]\n\trepositoryformat = 0\n")
    (root / ".env").write_text("DATABASE_URL=sqlite:///dummy\n")
    (gh / "db.sqlite3").write_bytes(b"SQLite format 3\x00" + b"\x00" * 64)  # dummy, NOT the real db
    (gh / ".env.example").write_text("SECRET_KEY=placeholder-not-a-real-key\n")
    (gh / ".gitignore").write_text(".env\n")
    (gh / "requirements.txt").write_text("Django==5.2.18\n")
    (gh / "manage.py").write_text("#!/usr/bin/env python\n")
    (gh / "DEPLOY.md").write_text("# deploy\n")
    (gh / "templates" / "base.html").write_text("<html>base</html>")
    (gh / "static" / "css" / "site.css").write_text("body{margin:0}")
    (gh / "docs" / "STATUS.md").write_text("# STATUS\n")
    (gh / "docs" / "AGENT-BRIEF.md").write_text("# brief\n")
    (gh / "media" / "property-images" / "x.jpg").write_bytes(b"\xff\xd8dummy")
    (root / "scripts" / "server.log").write_text("old django dev log\n")
    (root / "scripts" / "workspace_server.py").write_text("# the server code itself\n")
    ps = root / "scripts" / "preview_site"
    (ps / "index.html").write_text("<html>home</html>")
    (ps / "plan.html").write_text("<html>plan</html>")
    (ps / "checklist.html").write_text("<html>checklist</html>")
    (ps / "qa.html").write_text('<html><img src="qa-shots/home-1280.png"></html>')
    (ps / "deployment-checklist.html").write_text("<html>extra - not one of the four</html>")
    (ps / "qa-shots" / "home-1280.png").write_bytes(b"\x89PNG dummy")
    (root / "download" / "snapshot.zip").write_bytes(b"PK\x03\x04dummy")
    (root / "upload" / "notes.txt").write_text("owner upload\n")


class PreviewServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ws = Path(tempfile.mkdtemp(prefix="preview-ws-"))
        build_fake_workspace(cls.ws)
        if not SERVER_FILE.exists():
            raise AssertionError(
                "scripts/workspace_server.py does not exist — the preview "
                "server is not implemented (H1 red phase)."
            )
        cls.mod = load_server_module()
        cls.mod.ROOT = cls.ws  # point the handler at the disposable replica
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), cls.mod.WorkspaceHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        shutil.rmtree(cls.ws, ignore_errors=True)

    def fetch(self, path):
        req = urllib.request.Request(self.base + path, headers={"User-Agent": "preview-test"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as err:
            return err.code, err.read()

    # ------------------------------------------------------------ denied
    def test_denied_matrix_returns_403(self):
        denied = (
            "/gabriel_homes/db.sqlite3",            # database never reachable
            "/scripts/server.log",                   # logs never reachable
            "/download/",                            # deliverables never reachable
            "/download/snapshot.zip",
            "/.git/config",                          # repo internals never reachable
            "/gabriel_homes/.env.example",           # .env* family denied
            "/.env",
            "/upload/notes.txt",
            "/gabriel_homes/manage.py",              # code: not on the allow-list
            "/gabriel_homes/media/property-images/x.jpg",
            "/scripts/preview_site/deployment-checklist.html",  # not one of the four pages
            "/gabriel_homes/templates/../.env.example",          # raw traversal
            "/gabriel_homes/templates/%2e%2e/.env.example",      # encoded traversal
        )
        for path in denied:
            with self.subTest(path=path):
                status, _ = self.fetch(path)
                self.assertEqual(status, 403, f"{path} must be 403")

    def test_scripts_folder_itself_is_denied(self):
        for path in ("/scripts/", "/scripts/workspace_server.py"):
            with self.subTest(path=path):
                status, _ = self.fetch(path)
                self.assertEqual(status, 403)

    # ------------------------------------------------------------ allowed
    def test_allowed_matrix_returns_200(self):
        allowed = (
            "/",                                              # homepage
            "/gabriel_homes/templates/",                      # directory listing UI
            "/gabriel_homes/static/css/site.css",
            "/gabriel_homes/docs/STATUS.md",
            "/gabriel_homes/requirements.txt",
            "/scripts/preview_site/index.html",               # the four preview pages
            "/scripts/preview_site/plan.html",
            "/scripts/preview_site/checklist.html",
            "/scripts/preview_site/qa.html",
            "/scripts/preview_site/qa-shots/home-1280.png",   # qa.html assets
        )
        for path in allowed:
            with self.subTest(path=path):
                status, _ = self.fetch(path)
                self.assertEqual(status, 200, f"{path} must be 200")

    def test_homepage_links_the_preview_pages(self):
        _, body = self.fetch("/")
        text = body.decode("utf-8", "replace")
        for needle in ("plan.html", "checklist.html", "qa.html"):
            self.assertIn(needle, text, f"homepage must link {needle}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
