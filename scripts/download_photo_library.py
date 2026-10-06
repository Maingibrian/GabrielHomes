#!/usr/bin/env python3
"""download_photo_library.py — pull searched images into a local library,
validate them with PIL, and emit contact sheets for visual curation."""
import json, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

BASE = "/home/z/my-project/scripts/design-audit/search-json"
LIB = "/home/z/my-project/scripts/design-audit/photo-library"
os.makedirs(LIB, exist_ok=True)

CATEGORIES = [
    "villa", "beachhouse", "apartment", "apartment2", "townhouse", "luxhouse",
    "living", "kitchen", "bedroom", "office", "garden",
    "shops", "warehouse", "officebld",
    "men", "women", "men2", "women2", "coast", "city",
]

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

def fetch(url, dest):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        f.write(r.read())

manifest = {}
total_ok = total_bad = 0
for cat in CATEGORIES:
    path = f"{BASE}/{cat}.json"
    if not os.path.exists(path):
        print(f"!! missing {path}"); continue
    data = json.load(open(path))
    if not data.get("success"):
        print(f"!! {cat}: search unsuccessful: {data.get('error')}"); continue
    manifest[cat] = []
    for i, res in enumerate(data.get("results", []), 1):
        url = res.get("original_url", "")
        if not url:
            continue
        dest = f"{LIB}/{cat}-{i:02d}.jpg"
        try:
            fetch(url, dest)
            im = Image.open(dest); im.load()
            w, h = im.size
            if w < 640 or h < 420:
                os.remove(dest); total_bad += 1
                print(f"   skip {cat}-{i:02d}: too small {w}x{h}")
                continue
            if im.mode != "RGB":
                im = im.convert("RGB")
            # cap at 1600px wide to keep the zip lean
            if w > 1600:
                nh = int(h * 1600 / w)
                im = im.resize((1600, nh), Image.LANCZOS)
            im.save(dest, "JPEG", quality=86)
            manifest[cat].append({"file": os.path.basename(dest), "w": im.size[0], "h": im.size[1],
                                  "caption": res.get("caption", ""), "source": res.get("source", "")})
            total_ok += 1
        except Exception as e:
            total_bad += 1
            print(f"   fail {cat}-{i:02d}: {e}")
    print(f"{cat}: {len(manifest[cat])} usable")

json.dump(manifest, open(f"{LIB}/manifest.json", "w"), indent=1)
print(f"\nTOTAL usable={total_ok} bad={total_bad}")

# ---- contact sheets (thumb grids with labels) ----
thumbs = []
for cat in CATEGORIES:
    for item in manifest.get(cat, []):
        thumbs.append((cat, item["file"]))
TH = 190
COLS = 6
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
rows_per_sheet = 7
per_sheet = COLS * rows_per_sheet
for s in range(0, len(thumbs), per_sheet):
    chunk = thumbs[s:s + per_sheet]
    rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * TH, rows * (TH + 26)), (245, 242, 236))
    d = ImageDraw.Draw(sheet)
    for j, (cat, fn) in enumerate(chunk):
        im = Image.open(f"{LIB}/{fn}")
        im.thumbnail((TH - 6, TH - 6))
        x = (j % COLS) * TH; y = (j // COLS) * (TH + 26)
        sheet.paste(im, (x + 3, y + 3))
        d.text((x + 6, y + TH + 2), fn.replace(".jpg", ""), fill=(30, 25, 20), font=font)
    out = f"/home/z/my-project/scripts/design-audit/contact-{s // per_sheet}.png"
    sheet.save(out)
    print("sheet:", out)
