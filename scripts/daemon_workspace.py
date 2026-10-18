#!/usr/bin/env python3
"""Double-fork daemonizer for the :3000 delivery page (workspace_server.py).

Mirrors scripts/daemon_runserver.py: the tool harness reaps plain nohup/&
children between calls, which kept killing the download page. This daemon
detaches its session, ignores SIGHUP/SIGINT/SIGTERM, and survives.
"""
import os
import signal
import sys

ROOT = "/home/z/my-project"
SERVER = f"{ROOT}/scripts/workspace_server.py"
LOG = f"{ROOT}/scripts/workspace-server.log"


def _fork_exit():
    pid = os.fork()
    if pid > 0:
        os._exit(0)


def main():
    _fork_exit()
    os.setsid()
    _fork_exit()

    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal.SIG_IGN)

    sys.stdout.flush()
    sys.stderr.flush()
    log = open(LOG, "ab", buffering=0)
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)

    os.chdir(ROOT)
    os.execv(sys.executable, [sys.executable, SERVER])


if __name__ == "__main__":
    main()
