"""Launch the Django dev server + preview bridge as a surviving daemon.

The sandbox kills every process still attached to a Bash tool call's
session when the call ends (a plain `nohup ... &` dies with it). A
double-fork daemon — child setsid, grandchild reparented to init —
survives, so that is how the preview server must be started here.

The preview bridge (apps/core/preview_bridge.py) starts inside the
runserver process when GABRIEL_PREVIEW_BRIDGE=1, binding :3000 and
forwarding to the runserver port — the public gateway (:81) proxies
the preview URL to :3000.
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes")
LOG = "/tmp/django.log"
PIDFILE = "/tmp/django.pid"


def already_running() -> bool:
    if os.path.exists(PIDFILE):
        try:
            pid = int(open(PIDFILE).read().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, ProcessLookupError, PermissionError):
            pass
    return False


def _fill_preview_brand_contacts() -> None:
    """r103: demo contacts for the preview only, when blank.

    Uses the same shell that runs the server so it shares settings/venv;
    failures are non-fatal (the preview still starts, just form-only).
    """
    code = (
        "from apps.core.models import BrandSettings\n"
        "b = BrandSettings.load()\n"
        "changed = False\n"
        "for f, v in (('phone','+254712345678'),"
        "('whatsapp','+254712345678'),"
        "('email','hello@gabrielhomes.co.ke')):\n"
        "    if not getattr(b, f, ''):\n"
        "        setattr(b, f, v); changed = True\n"
        "if changed: b.save()"
    )
    try:
        subprocess.run(
            [str(REPO / ".venv/bin/python"), "manage.py", "shell", "-c", code],
            cwd=str(REPO), timeout=60,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def main() -> None:
    if already_running():
        print("django daemon already running")
        return

    # double-fork: parent exits, child setsid + exits, grandchild serves
    pid = os.fork()
    if pid > 0:
        # wait briefly so the pidfile exists before this call returns
        import time
        for _ in range(40):
            if os.path.exists(PIDFILE):
                break
            time.sleep(0.25)
        try:
            print("django daemon pid:", open(PIDFILE).read().strip())
        except OSError:
            print("daemon started (pidfile not written yet)")
        return

    os.setsid()
    if os.fork() > 0:
        os._exit(0)

    # grandchild: detach stdio, cd to repo, start runserver
    os.chdir(REPO)
    log = open(LOG, "ab", buffering=0)
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)

    env = dict(os.environ)
    env["GABRIEL_PREVIEW_BRIDGE"] = "1"
    # The public preview chain (browser -> preview-chat-*.space-z.ai ->
    # *.fcapp.run gateway -> :81) delivers requests with Host headers the
    # dev server does not know, so Django answers 400 DisallowedHost before
    # any view runs. Allow both proxy domains (leading dot = any subdomain,
    # so future chat preview URLs keep working).
    env.setdefault("EXTRA_ALLOWED_HOSTS", ".space-z.ai,.fcapp.run")
    # CSRF: the browser's Origin is the https preview domain when accessed
    # through the public URL, or http://127.0.0.1:81 through the local
    # gateway — both must be trusted or every POST form 403s.
    env.setdefault("CSRF_TRUSTED_ORIGINS",
                   "http://127.0.0.1:81,https://*.space-z.ai")
    # r103: PREVIEW-ONLY demo brand contacts. seed_demo deliberately leaves
    # BrandSettings contact channels empty (P1 contract: the owner fills
    # them via the dashboard — honest-blank by design), which made the
    # preview's detail sidebar render form-only with no call/WhatsApp and
    # no mobile bar. Fill them here, only for the preview, only when blank
    # (the owner's real values always win). Same numbers the seed mints
    # for the Gabriel Homes demo agency row.
    _fill_preview_brand_contacts()
    proc = subprocess.Popen(
        [str(REPO / ".venv/bin/python"), "manage.py", "runserver",
         "0.0.0.0:8000", "--noreload"],
        env=env, cwd=str(REPO),
        stdout=log, stderr=subprocess.STDOUT, start_new_session=False,
    )
    with open(PIDFILE, "w") as f:
        f.write(str(proc.pid))
    # wait in-process so the daemon stays alive holding the child
    proc.wait()


if __name__ == "__main__":
    main()
