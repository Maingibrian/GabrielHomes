#!/usr/bin/env python3
"""Measure how far down real data appears on key mobile pages (390px)."""
import subprocess, json, time

BASE = "http://127.0.0.1:8000"

PAGES = [
    ("home", "/", """(() => {
      const out = {};
      const vh = window.innerHeight;
      const find = (sel) => { const el = document.querySelector(sel); return el ? Math.round(el.getBoundingClientRect().top + window.scrollY) : null; };
      out.heroSearch = find('.hero-search, .search-card, form[action*="properties"]');
      out.firstSection = find('main > section:nth-of-type(2), main section:not(:first-child)');
      out.firstCards = find('.bento-grid, .card-grid, .listing-card');
      out.vh = vh;
      return JSON.stringify(out);
    })()"""),
    ("properties", "/properties/", """(() => {
      const out = {};
      const vh = window.innerHeight;
      const cards = document.querySelectorAll('.card, .listing-card, article');
      out.vh = vh;
      out.firstCardTop = cards.length ? Math.round(cards[0].getBoundingClientRect().top + window.scrollY) : null;
      out.cardCount = cards.length;
      const h1 = document.querySelector('h1');
      out.h1Top = h1 ? Math.round(h1.getBoundingClientRect().top + window.scrollY) : null;
      return JSON.stringify(out);
    })()"""),
    ("detail", "/listing/3br-home-near-haller-park-bamburi-8/", """(() => {
      const out = {};
      out.vh = window.innerHeight;
      const price = [...document.querySelectorAll('*')].find(el => el.children.length === 0 && /KSh|\\.00|M\\/o|month/i.test(el.textContent) && el.textContent.trim().length < 40);
      out.priceTop = price ? Math.round(price.getBoundingClientRect().top + window.scrollY) : null;
      return JSON.stringify(out);
    })()"""),
    ("portal", "/manage/", """(() => {
      const out = {};
      out.vh = window.innerHeight;
      const g = document.querySelector('[class*="graph"], [class*="bar"], svg');
      out.graphTop = g ? Math.round(g.getBoundingClientRect().top + window.scrollY) : null;
      const nums = document.querySelector('[class*="stat"], [class*="count"]');
      out.statTop = nums ? Math.round(nums.getBoundingClientRect().top + window.scrollY) : null;
      return JSON.stringify(out);
    })()"""),
]

def ab(*args, timeout=60):
    r = subprocess.run(["agent-browser", *args], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

for name, path, js in PAGES:
    ab("open", BASE + path, timeout=45)
    ab("wait", "--load", "networkidle", timeout=30)
    time.sleep(0.6)
    raw = ab("eval", js, timeout=45)
    try:
        s = raw.strip('"').replace('\\"', '"')
        print(f"{name:12s}", json.dumps(json.loads(s), ensure_ascii=False))
    except Exception:
        print(f"{name:12s} RAW: {raw[:200]}")
