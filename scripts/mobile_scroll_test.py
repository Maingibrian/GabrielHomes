#!/usr/bin/env python3
"""Check REAL horizontal scrollability (not just scrollWidth) on flagged pages."""
import subprocess, time, json

BASE = "http://127.0.0.1:8000"
PAGES = [("home", "/"), ("properties", "/properties/"), ("sale-nyali", "/property-for-sale/nyali/"), ("agents", "/agents/")]

JS = """(() => {
  const res = {};
  res.scrollW = document.documentElement.scrollWidth;
  res.clientW = document.documentElement.clientWidth;
  res.innerW = window.innerWidth;
  window.scrollTo(60, 0);
  res.scrollXAfter = window.scrollX;
  res.bodyClip = getComputedStyle(document.body).overflowX;
  res.htmlClip = getComputedStyle(document.documentElement).overflowX;
  window.scrollTo(0, 0);
  return JSON.stringify(res);
})()"""

def ab(*args, timeout=60):
    r = subprocess.run(["agent-browser", *args], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

for name, path in PAGES:
    ab("open", BASE + path, timeout=45)
    ab("wait", "--load", "networkidle", timeout=30)
    time.sleep(0.8)
    raw = ab("eval", JS, timeout=45)
    try:
        d = json.loads(raw.strip('"').replace('\\"', '"'))
        really = d["scrollXAfter"] > 0
        print(f"{name:12s} scrollW={d['scrollW']:4d} clientW={d['clientW']} body={d['bodyClip']:8s} html={d['htmlClip']:8s} -> {'REALLY SCROLLS (%dpx)' % d['scrollXAfter'] if really else 'clipped (safe)'}")
    except Exception as e:
        print(f"{name:12s} parse fail: {raw[:150]}")
