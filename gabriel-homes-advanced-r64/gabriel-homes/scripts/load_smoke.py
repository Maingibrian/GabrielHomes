#!/usr/bin/env python3
"""load_smoke.py — minimal load smoke for Gabriel Homes (docs/PLAN.md task V3).

PLAN wants `hey` or `ab` (20 concurrent, 60s) against staging. Neither tool is
available in this environment and there is no sudo, so this stdlib driver
produces the same metrics locally: requests/sec, p50/p95/p99 latency, and any
non-200 response. The `hey` run belongs to the staging rehearsal (task R1 / O7).

Usage:
    python scripts/load_smoke.py BASE_URL PATH [--workers 20] [--seconds 60]

Exit 0 only if there were zero non-200 responses.
"""
import argparse
import http.client
import statistics
import threading
import time
from collections import Counter
import urllib.parse as urlparse


def worker(base_parsed: urlparse.urlsplit, path: str,
           deadline: float, latencies: list, statuses: Counter,
           lock: threading.Lock, host_header: str) -> None:
    conn = http.client.HTTPConnection(base_parsed.hostname, base_parsed.port, timeout=10)
    try:
        while time.monotonic() < deadline:
            t0 = time.perf_counter()
            try:
                conn.request("GET", path, headers={"Host": host_header})
                resp = conn.getresponse()
                resp.read()
                status = resp.status
            except Exception:
                status = 0  # connection-level failure
                try:
                    conn.close()
                except Exception:
                    pass
                conn = http.client.HTTPConnection(
                    base_parsed.hostname, base_parsed.port, timeout=10)
            dt = time.perf_counter() - t0
            with lock:
                latencies.append(dt)
                statuses[status] += 1
    finally:
        conn.close()


def percentile(sorted_vals: list, p: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, max(0, round(p / 100 * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base_url")
    ap.add_argument("path")
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--seconds", type=int, default=60)
    args = ap.parse_args()

    parsed = urlparse.urlsplit(args.base_url)
    path = args.path
    duration = args.seconds

    latencies: list = []
    statuses: Counter = Counter()
    lock = threading.Lock()
    deadline = time.monotonic() + duration

    threads = [
        threading.Thread(target=worker, args=(parsed, path, deadline, latencies,
                                              statuses, lock, parsed.netloc),
                         daemon=True)
        for _ in range(args.workers)
    ]
    t_start = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.monotonic() - t_start

    lat_sorted = sorted(latencies)
    total = len(lat_sorted)
    non200 = {s: c for s, c in statuses.items() if s != 200}

    print(f"target          : {args.base_url}{path}")
    print(f"workers / window: {args.workers} / {duration}s (actual {elapsed:.1f}s)")
    print(f"requests        : {total}")
    print(f"throughput      : {total / elapsed:.1f} req/s")
    if lat_sorted:
        print(f"latency p50     : {percentile(lat_sorted, 50) * 1000:.0f} ms")
        print(f"latency p95     : {percentile(lat_sorted, 95) * 1000:.0f} ms")
        print(f"latency p99     : {percentile(lat_sorted, 99) * 1000:.0f} ms")
        print(f"latency mean    : {statistics.fmean(lat_sorted) * 1000:.0f} ms")
    print(f"status codes    : {dict(sorted(statuses.items()))}")
    if non200:
        print(f"NON-200 RESPONSES: {non200}")
        return 1
    print("non-200 count   : 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
