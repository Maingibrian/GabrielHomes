#!/usr/bin/env python3
"""Search for East African coastal background candidates via z-ai image-search.
Prints candidate URLs (one per line) for a given query."""
import json
import subprocess
import sys


def search(query: str, count: int = 4) -> list[str]:
    """Run z-ai image-search, capture stdout, extract the JSON blob."""
    proc = subprocess.run(
        ["z-ai", "image-search", "-q", query, "-n", str(count)],
        capture_output=True, text=True, timeout=180,
    )
    out = proc.stdout or ""
    # The CLI prefixes output with emoji status lines; JSON starts at first '{'
    start = out.find("{")
    if start == -1:
        sys.stderr.write(f"no JSON in output:\n{out[:400]}\n{proc.stderr[:400]}\n")
        return []
    # find matching end
    try:
        data = json.loads(out[start:])
    except json.JSONDecodeError:
        # maybe trailing text; try trimming to last '}'
        end = out.rfind("}")
        try:
            data = json.loads(out[start:end + 1])
        except json.JSONDecodeError:
            sys.stderr.write(f"unparseable JSON:\n{out[:600]}\n")
            return []
    urls = []
    items = data if isinstance(data, list) else data.get("results", data.get("data", []))
    for item in items:
        url = item.get("image_url") or item.get("url") or item.get("oss_url")
        if url:
            urls.append(url)
    return urls


if __name__ == "__main__":
    query = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    for u in search(query, count):
        print(u)
