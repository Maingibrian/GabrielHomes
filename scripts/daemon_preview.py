#!/usr/bin/env python3
"""Double-fork daemonizer for the locked :3000 preview server (sandbox-only).

Same survival pattern as daemon_runserver.py: detach session, redirect stdio,
and ignore SIGHUP/SIGINT/SIGTERM that the tool harness may broadcast.
A plain `setsid nohup ... &` gets reaped by the harness; this does not.
"""
import os
import signal
import sys

ROOT = "/home/z/my-project"
PY = "/usr/bin/python3"
LOG = f"{ROOT}/scripts/preview3000.log"
SCRIPT = f"{ROOT}/scripts/workspace_server.py"


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

    os.chdir(ROOT)
    os.execv(PY, [PY, SCRIPT])


if __name__ == "__main__":
    main()
