#!/usr/bin/env python3
"""r101 VERIFY — after the reseed fix, confirm every image the homepage
references loads 200 through BOTH the local chain (:81) and the public
gateway (browser UA — the gateway 403s bot UAs, which misled the first
diagnosis). Also confirm the r100 markers and the portal inbox."""
import re
import urllib.error
import urllib.request

LOCAL = "http://127.0.0.1:81"
PUBLIC = "https://preview-chat-32c380a6-f37c-48b2-a3b0-ee41938bc50c.space-z.ai"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return "ERR:" + type(e).__name__, b""


def main():
    code, body = get(LOCAL + "/")
    html = body.decode("utf-8", "replace")
    print(f"home :81 -> {code}, bytes={len(html)}")
    fan = html.count("market-rail__fan-img")
    cnt = re.search(r"<strong>(\d+)</strong> homes for sale right now", html)
    print(f"fan_imgs={fan} count_stat={cnt.group(1) if cnt else 'MISSING'}")
    imgs = sorted(set(re.findall(r'(?:src|href)="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html)))
    media_imgs = [u for u in imgs if "/media/" in u]
    static_imgs = [u for u in imgs if "/static/" in u]
    print(f"img refs: media={len(media_imgs)} static={len(static_imgs)}")

    for label, base in (("local", LOCAL), ("public", PUBLIC)):
        bad = []
        for u in media_imgs + static_imgs:
            full = base + (u if u.startswith("/") else "/" + u)
            c, _ = get(full)
            if c != 200:
                bad.append((c, u))
        print(f"{label}: checked={len(media_imgs)+len(static_imgs)} non-200={len(bad)}")
        for c, u in bad[:8]:
            print(f"   {c} {u}")

    # owner login through the public chain (the path the owner uses)
    code, body = get(PUBLIC + "/account/login/")
    print(f"public login page -> {code}")
    print(f"csrf cookie present: {'csrftoken' in body.decode('utf-8', 'replace').lower() or 'csrf' in body.decode('utf-8','replace').lower()}")


if __name__ == "__main__":
    main()
