"""Compose the r66 delivery images: accordion states + closing band."""
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf"


def label(img, text, y=18):
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(FONT, 26)
    except OSError:
        f = ImageFont.load_default()
    d.rectangle([16, y - 4, 16 + d.textlength(text, font=f) + 20, y + 34],
                fill=(42, 33, 28))
    d.text((26, y), text, fill=(250, 248, 244), font=f)
    return img


def stack(paths, labels, out, target_w=1200):
    imgs = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        r = target_w / im.width
        imgs.append(im.resize((target_w, int(im.height * r))))
    total_h = sum(i.height for i in imgs) + 14 * (len(imgs) + 1)
    canvas = Image.new("RGB", (target_w + 28, total_h), (250, 248, 244))
    y = 14
    for im, lab in zip(imgs, labels):
        canvas.paste(im, (14, y))
        label(canvas, lab, y + 14)
        y += im.height + 14
    canvas.save(out, quality=88)
    print(f"wrote {out} ({canvas.width}x{canvas.height})")


# 1. the accordion: collapsed + hover-expanded
stack(
    ["/tmp/r66-final-collapsed.png", "/tmp/r66-final-hover.png"],
    ["Collapsed — book-spine panels over the wave field",
     "Hover — the first panel blooms open, detail follows"],
    "/home/z/my-project/download/r66-values-accordion.jpg",
)

# 2. the closing band, after
band = Image.open("/tmp/r66-about-full-desktop.png").convert("RGB")
w = band.width
# the closing band is the last ~1100px of the full page
crop = band.crop((0, band.height - 1150, w, band.height))
crop = crop.resize((1200, int(crop.height * 1200 / crop.width)))
label(crop, "The closing band after — no shaded photos, just the CTA")
crop.save("/home/z/my-project/download/r66-cta-band-after.jpg", quality=88)
print("wrote r66-cta-band-after.jpg")

# 3. full pages
for src, dst in (
        ("/tmp/r66-about-full-desktop.png",
         "/home/z/my-project/download/about-page-r66-desktop.png"),
        ("/tmp/r66-about-full-mobile.png",
         "/home/z/my-project/download/about-page-r66-mobile.png")):
    im = Image.open(src).convert("RGB")
    if im.width > 1200:
        im = im.resize((1200, int(im.height * 1200 / im.width)))
    im.save(dst, quality=88)
    print(f"wrote {dst} ({im.width}x{im.height})")
