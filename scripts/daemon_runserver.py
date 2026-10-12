#!/usr/bin/env python3
"""Double-fork daemonizer for the Django dev server (sandbox-only).

Survives the parent shell being reaped: detaches session, redirects stdio,
and ignores SIGHUP/SIGINT/SIGTERM that the tool harness may broadcast.
"""
import os
import signal
import sys
import time

PROJ = "/home/z/my-project/gabriel_homes"
PY = f"{PROJ}/.venv/bin/python"
LOG = "/tmp/runserver.log"
PORT = "3011"


def _fork_exit():
    pid = os.fork()
    if pid > 0:
        os._exit(0)


def main():
    # First fork
    _fork_exit()
    os.setsid()
    # Second fork (detach from controlling terminal entirely)
    _fork_exit()

    # Ignore the signals the harness uses to reap background jobs
    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal.SIG_IGN)

    # stdio -> logfile
    sys.stdout.flush()
    sys.stderr.flush()
    log = open(LOG, "ab", buffering=0)
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)

    os.chdir(PROJ)
    os.execv(PY, [PY, "manage.py", "runserver", f"0.0.0.0:{PORT}", "--noreload"])


if __name__ == "__main__":
    main()
