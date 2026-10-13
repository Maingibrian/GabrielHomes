"""capture_audit_shots.py — full visual audit capture for the user's
"about + property pages are still broken, use vision, be very critical".

Captures, per page:
  - full-page screenshot (desktop 1440 and mobile 390)
  - console errors / page errors
  - failed network responses (4xx/5xx)
Then runs a link audit: every internal href on home/about/detail is
requested and non-200s are reported.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3011"
OUT = Path("/home/z/my-project/scripts/shots/audit-2026-10-13")
OUT.mkdir(parents=True, exist_ok=True)

PAGES = {
    "home": "/",
    "about": "/about/",
    "detail": "/listing/3br-bungalow-in-nyali-77/",
    "services": "/services/",
    "search": "/property-for-sale/",
}

REPORT: dict[str, dict] = {}


def capture(page, name: str, path: str, width: int, height: int) -> dict:
    ctx_errors: list[str] = []
    failed: list[str] = []

    def on_console(m):
        if m.type in ("error", "warning"):
            ctx_errors.append(f"console.{m.type}: {m.text[:200]}")

    def on_response(r):
        if r.status >= 400:
            failed.append(f"{r.status} {r.url[:140]}")

    page.on("console", on_console)
    page.on("response", on_response)
    page.on("pageerror", lambda e: ctx_errors.append(f"pageerror: {str(e)[:200]}"))
    try:
        page.set_viewport_size({"width": width, "height": height})
        page.goto(BASE + path, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1200)
        # force lazy content to load for full-page truth
        page.mouse.wheel(0, 20000)
        page.wait_for_timeout(600)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        scroll_w = page.evaluate("document.documentElement.scrollWidth")
        view_w = page.evaluate("window.innerWidth")
        shot = OUT / f"{name}-{width}.png"
        page.screenshot(path=str(shot), full_page=True)
        result = {
            "shot": str(shot),
            "console": ctx_errors,
            "failed_requests": failed,
            "horizontal_overflow": scroll_w > view_w,
            f"scrollW": scroll_w,
            "viewportW": view_w,
        }
    except Exception as exc:  # noqa: BLE001
        result = {"shot": None, "error": str(exc)[:300]}
    page.remove_listener("console", on_console)
    page.remove_listener("response", on_response)
    return result


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # fresh context, no cache — what a first-time visitor sees
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        for name, path in PAGES.items():
            REPORT[name] = {
                "desktop": capture(page, name, path, 1440, 900),
                "mobile": capture(page, name, path, 390, 844),
            }

        # ---- link audit on the three key pages ----
        link_report = {}
        for name in ("home", "about", "detail"):
            page.goto(BASE + PAGES[name], wait_until="networkidle")
            hrefs = page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.getAttribute('href'))",
            )
            internal = sorted(
                {
                    h
                    for h in hrefs
                    if h and h.startswith("/")
                    and not h.startswith("//")
                    and not h.startswith("/static/")
                    and not h.startswith("/media/")
                }
            )
            bad = []
            for h in internal:
                r = page.request.get(BASE + h)
                if r.status >= 400:
                    bad.append(f"{r.status} {h}")
            link_report[name] = {"internal_links": len(internal), "broken": bad}
        REPORT["link_audit"] = link_report
        browser.close()

    (OUT / "report.json").write_text(json.dumps(REPORT, indent=2))
    print(json.dumps(REPORT, indent=2))


if __name__ == "__main__":
    main()
