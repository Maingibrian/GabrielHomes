"""Screenshot key pages through the preview gateway to see what the user sees."""
import sys
from playwright.sync_api import sync_playwright

HOST = "preview-361b2cc9.space-z.ai"
BASE = f"http://localhost:81"
OUT = "/home/z/my-project/scripts/shots"

PAGES = {
    "home": "/",
    "services": "/agents/",
    "detail": "/listing/modern-beachfront-apartment-nyali-81/",
}

def main():
    only = sys.argv[1:] or list(PAGES)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        pass
        for name in only:
            path = PAGES.get(name)
            if not path:
                print(f"unknown page {name}")
                continue
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            try:
                resp = page.goto(BASE + path, wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(1800)
                page.screenshot(path=f"{OUT}/{name}-full.png", full_page=True)
                page.screenshot(path=f"{OUT}/{name}-fold.png", full_page=False)
                print(f"[{name}] {resp.status if resp else '???'} {BASE+path} -> {OUT}/{name}-full.png  scrollW={page.evaluate('document.documentElement.scrollWidth')}")
                for e in errors[:12]:
                    print("   ", e)
            except Exception as exc:
                print(f"[{name}] FAILED: {exc}")
            page.close()
        browser.close()

if __name__ == "__main__":
    main()
