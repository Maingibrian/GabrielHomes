"""Sandbox-only live-preview bridge.

The workspace preview gateway (caddy :81) proxies to port 3000, but the
sandbox runtime auto-starts the Django dev server on a different port
(currently 3011). This module — loaded inside the *supervisor-started*
Django process, which is the only kind of process that survives in the
sandbox — binds port 3000 in a background thread and forwards every
connection to the port runserver is actually using.

Activation is triple-guarded so it can never affect normal users:
  1. GABRIEL_PREVIEW_BRIDGE=1 must be present (sandbox .env sets it;
     .env is excluded from every shipped zip, .env.example omits it).
  2. Only under `manage.py runserver` (not migrate/test/shell/gunicorn).
  3. Only when runserver itself is NOT already on port 3000.

Every failure is swallowed: the bridge must never break Django.
"""
from __future__ import annotations

import asyncio
import os
import sys
import threading
import time

BRIDGE_PORT = 3000
LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "preview_bridge.log",
)


def _log(msg: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%H:%M:%S')} pid={os.getpid()} {msg}\n")
    except OSError:
        pass


def _flag_enabled() -> bool:
    if os.environ.get("GABRIEL_PREVIEW_BRIDGE") == "1":
        return True
    # Fallback: read the sandbox .env directly (defensive — read_env normally
    # exports it into os.environ anyway).
    try:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with open(os.path.join(base, ".env"), "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("GABRIEL_PREVIEW_BRIDGE") and line.split("=", 1)[1].strip() == "1":
                    return True
    except OSError:
        pass
    return False


def _runserver_port() -> int | None:
    """Extract the port the dev server is going to listen on from argv."""
    if len(sys.argv) < 2 or sys.argv[1] != "runserver":
        return None
    addr = next((a for a in sys.argv[2:] if not a.startswith("-")), None)
    if not addr:  # plain `runserver` -> Django default 127.0.0.1:8000
        return 8000
    host, _, port = addr.rpartition(":")
    if not port.isdigit():
        return 8000  # '0.0.0.0' style typo safety; Django would reject anyway
    return int(port)


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            chunk = await reader.read(65536)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError, OSError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def _handle(client_reader, client_writer, target_port: int) -> None:
    try:
        up_r, up_w = await asyncio.open_connection("127.0.0.1", target_port)
    except OSError:
        try:
            client_writer.close()
        except Exception:
            pass
        return
    await asyncio.gather(
        _pipe(client_reader, up_w),
        _pipe(up_r, client_writer),
    )


def _serve(target_port: int) -> None:
    async def _main() -> None:
        server = await asyncio.start_server(
            lambda r, w: _handle(r, w, target_port), "0.0.0.0", BRIDGE_PORT
        )
        _log(f"bridge LISTENING 0.0.0.0:{BRIDGE_PORT} -> 127.0.0.1:{target_port}")
        print(f"[preview-bridge] 0.0.0.0:{BRIDGE_PORT} -> 127.0.0.1:{target_port}", flush=True)
        async with server:
            await server.serve_forever()

    try:
        asyncio.run(_main())
    except OSError as exc:
        _log(f"bridge bind failed: {exc}")
    except Exception as exc:  # never break Django over an infra nicety
        _log(f"bridge crashed: {exc!r}")


def maybe_start() -> None:
    try:
        flag = _flag_enabled()
        target = _runserver_port()
        _log(f"ready() evaluated: flag={flag} argv={sys.argv[1:3]!r} target={target}")
        if not flag:
            return
        if target is None or target == BRIDGE_PORT:
            return
        thread = threading.Thread(
            target=_serve, args=(target,), name="preview-bridge", daemon=True
        )
        thread.start()
    except Exception as exc:
        _log(f"maybe_start crashed: {exc!r}")
