"""Print the first free TCP port in 8000-8010, or 0 if all are busy.

Used by the one-click launchers (START-GABRIEL-HOMES.bat/.command/.sh)
so port handling behaves identically on Windows, macOS and Linux.
Run directly with the venv python — no Django needed:

    python scripts/find_free_port.py
"""
from __future__ import annotations

import socket


def first_free_port(start: int = 8000, end: int = 8010) -> int:
    for port in range(start, end + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            return port
        except OSError:
            continue
        finally:
            sock.close()
    return 0


if __name__ == "__main__":
    print(first_free_port())
