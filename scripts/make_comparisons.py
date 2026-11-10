#!/usr/bin/env python3
"""Build before/after comparison sheets for the user deliverables."""
from PIL import Image, ImageDraw, ImageFont
import os

DL = '/home/z/my-project/download'
os.makedirs(DL, exist_ok=True)

FONT = None
for cand in ['/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']:
    if os.path.exists(cand):
        FONT = ImageFont.truetype(cand, 28)
        break

def label(img, text, fill=(255, 255, 255)):
    d = ImageDraw.Draw(img)
    if FONT:
        tw = d.textlength(text, font=FONT)
        d.rectangle([(0, 0), (tw + 36, 56)], fill=(28, 21, 17))
        d.text((18, 12), text, font=FONT, fill=fill)
    return img

def side_by_side(a_path, b_path, out, la, lb, target_h=1100):
    a = Image.open(a_path).convert('RGB')
    b = Image.open(b_path).convert('RGB')
    def fit(img):
        w, h = img.size
        return img.resize((int(w * target_h / h), target_h), Image.LANCZOS)
    a, b = fit(a), fit(b)
    gap = 24
    sheet = Image.new('RGB', (a.width + b.width + gap, target_h), (28, 21, 17))
    sheet.paste(label(a, la), (0, 0))
    sheet.paste(label(b, lb), (a.width + gap, 0))
    sheet.save(out, quality=88, optimize=True)
    print(out, sheet.size)

# 1. Listings band before/after (viewport shots at same scroll depth)
side_by_side('/tmp/shots/listings-viewport.png', '/tmp/shots/listings-after-vp.png',
             f'{DL}/listings-palm-background-before-after.jpg',
             'BEFORE - flat cream results band', 'AFTER - palm field adds depth')

# 2. About page: quote band + coast strip + values (before ~ quote band area; after same region)
# Before: about-full.png captured pre-change; After: about-final.png
def crop_frac(path, top_frac, bot_frac, x_frac=1.0):
    img = Image.open(path).convert('RGB')
    w, h = img.size
    return img.crop((0, int(h * top_frac), int(w * x_frac), int(h * bot_frac)))

# before: sections 2 (quote+values) — from about-full.png (1700w? it was 1600w)
b_img = crop_frac('/tmp/shots/about-full.png', 0.30, 0.62)
b_img.save('/tmp/shots/_about-b-mid.png')
a_img = crop_frac('/tmp/shots/about-final.png', 0.32, 0.70)
a_img.save('/tmp/shots/_about-a-mid.png')
side_by_side('/tmp/shots/_about-b-mid.png', '/tmp/shots/_about-a-mid.png',
             f'{DL}/about-quote-coast-values-before-after.jpg',
             'BEFORE - empty quote band, flat principles', 'AFTER - ghost 10, coast strip, palm field')

# 3. About top: hero + ticker + story
b_top = crop_frac('/tmp/shots/about-full.png', 0.0, 0.30)
b_top.save('/tmp/shots/_about-b-top.png')
a_top = crop_frac('/tmp/shots/about-final.png', 0.0, 0.32)
a_top.save('/tmp/shots/_about-a-top.png')
side_by_side('/tmp/shots/_about-b-top.png', '/tmp/shots/_about-a-top.png',
             f'{DL}/about-hero-ticker-before-after.jpg',
             'BEFORE - hero straight into cream story', 'AFTER - coast ticker breaks the cream')

print('done')
