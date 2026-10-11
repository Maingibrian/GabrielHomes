#!/usr/bin/env python3
"""Port forwarder: 0.0.0.0:3000 -> 127.0.0.1:3011

Bridges the preview gateway (caddy :81 -> :3000) to the Django dev server
that the runtime supervisor auto-started on :3011.
Run detached:  setsid nohup python3 port_forward_3000.py >> pf3000.log 2>&1 < /dev/null &
"""
import asyncio
import sys

LISTEN_PORT = 3000
TARGET_PORT = 3011


async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            chunk = await reader.read(65536)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def handle(client_reader, client_writer) -> None:
    try:
        upstream_reader, upstream_writer = await asyncio.open_connection(
            "127.0.0.1", TARGET_PORT
        )
    except OSError:
        client_writer.close()
        return
    await asyncio.gather(
        pipe(client_reader, upstream_writer),
        pipe(upstream_reader, client_writer),
    )


async def main() -> None:
    server = await asyncio.start_server(handle, "0.0.0.0", LISTEN_PORT)
    print(f"forwarding 0.0.0.0:{LISTEN_PORT} -> 127.0.0.1:{TARGET_PORT}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
