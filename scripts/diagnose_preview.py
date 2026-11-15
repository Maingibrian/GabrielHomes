#!/usr/bin/env python3
"""r101 DIAGNOSIS — the owner's review reports (a) progress lost and
(b) images not loading. Establish what the preview actually serves
BEFORE touching anything: the local chain (:81), the public gateway
chain, the served CSS vs disk, DB-vs-disk media agreement, and the
daemon's identity (which tree, which interpreter)."""
import glob
import os
import re
import subprocess
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:81"
PUBLIC = "https://preview-chat-32c380a6-f37c-48b2-a3b0-ee41938bc50c.space-z.ai"
DJ = "/home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes"
UA = {"User-Agent": "Mozilla/5.0 (compatible; diag/1.0)"}


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace"), {k.lower(): v for k, v in r.headers.items()}


def status(url, timeout=12):
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return "ERR:" + type(e).__name__


def page_report(label, base, img_cap):
    print(f"===== PAGE {label} =====")
    try:
        html, hdr = fetch(base + "/")
    except Exception as e:
        print(f"  FETCH FAILED: {type(e).__name__}: {e}")
        return None
    print(f"  bytes={len(html)} cache_control={hdr.get('cache-control', '-')} "
          f"age={hdr.get('age', '-')} etag={hdr.get('etag', '-')[:24]}")
    print(f"  video_tags={html.count('<video')} hero_slides={html.count('hero__slide')}")
    m = re.search(r"(\d+) homes for sale right now", html)
    print(f"  count_stat={m.group(0) if m else 'MISSING'}")
    css = re.search(r'href="([^"]+home\.css[^"]*)"', html)
    print(f"  css_href={css.group(1) if css else 'MISSING'}")
    urls = sorted(set(re.findall(r'[^"\'\s()>,]+\.(?:jpg|jpeg|png|webp)[^"\'\s()>,]*', html)))
    print(f"  image_urls_on_page={len(urls)}")
    codes = {}
    for u in urls[:img_cap]:
        full = u if u.startswith("http") else base + (u if u.startswith("/") else "/" + u)
        codes.setdefault(str(status(full)), []).append(u)
    for c in sorted(codes):
        print(f"  img_http_{c}={len(codes[c])}")
        if c != "200":
            for u in codes[c][:6]:
                print(f"      {u}")
    return html, css


DB_CODE = """
from django.conf import settings
from apps.listings.models import Property, PropertyImage
from django.db.models import Count
import os
print("listings_total", Property.objects.count())
print("published", Property.objects.published().count())
print("sale_published", Property.objects.published().filter(listing_type=Property.ListingType.SALE).count())
print("image_rows", PropertyImage.objects.count())
miss = [p.image.name for p in PropertyImage.objects.all() if not os.path.exists(os.path.join(settings.MEDIA_ROOT, p.image.name))]
print("image_rows_missing_on_disk", len(miss))
for n in miss[:8]:
    print("  missing:", n)
print("duplicate_titles", Property.objects.values("title").annotate(n=Count("id")).filter(n__gt=1).count())
print("demo_flagged", Property.objects.filter(is_demo=True).count())
"""


def main():
    local = page_report("LOCAL :81", BASE, 60)
    page_report("PUBLIC GATEWAY", PUBLIC, 10)

    print("===== CSS served vs disk =====")
    if local and local[1]:
        u = local[1].group(1)
        full = u if u.startswith("http") else BASE + (u if u.startswith("/") else "/" + u)
        try:
            served, _ = fetch(full)
            disk = open(os.path.join(DJ, "static/css/home.css"), encoding="utf-8").read()
            print(f"  served_bytes={len(served)} disk_bytes={len(disk)} identical={served == disk}")
            print(f"  kb_from served={served.count('--kb-from')} disk={disk.count('--kb-from')} "
                  f"62svh served={served.count('62svh')} disk={disk.count('62svh')}")
        except Exception as e:
            print(f"  CSS FETCH FAILED: {type(e).__name__}: {e}")
    else:
        print("  skipped (no local page/css)")

    print("===== DB vs DISK =====")
    try:
        r = subprocess.run([os.path.join(DJ, ".venv/bin/python"), "manage.py", "shell", "-c", DB_CODE],
                           cwd=DJ, capture_output=True, text=True, timeout=180)
        out = (r.stdout + r.stderr).strip()
        print("\n".join("  " + line for line in out.splitlines()[:24]))
    except Exception as e:
        print(f"  DB CHECK FAILED ({type(e).__name__}: {e}) — .venv gone?")

    print("===== DAEMON / TREE / MEDIA =====")
    ps = subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout
    for line in ps.splitlines():
        if ("runserver" in line or "launch_preview" in line) and "grep" not in line:
            print("  proc: " + " ".join(line.split()[1:])[:170])
    for cmd in (["git", "log", "--oneline", "-1"], ["git", "status", "--porcelain"]):
        r = subprocess.run(cmd, cwd=DJ, capture_output=True, text=True)
        print(f"  {' '.join(cmd)} -> {r.stdout.strip()[:80] or '(clean)'}")
    total = sum(len(files) for _, _, files in os.walk(os.path.join(DJ, "media")))
    dp = os.path.join(DJ, "media", "demo-photos")
    print(f"  media_files={total} demo_photos={len(os.listdir(dp)) if os.path.isdir(dp) else 'DIR MISSING'}")

    print("===== /tmp LOGS (tails) =====")
    for f in sorted(glob.glob("/tmp/*.log"))[:6]:
        r = subprocess.run(["tail", "-n", "8", f], capture_output=True, text=True)
        print(f"  -- {f}")
        for line in r.stdout.splitlines()[-8:]:
            print("    " + line[:150])


if __name__ == "__main__":
    main()
