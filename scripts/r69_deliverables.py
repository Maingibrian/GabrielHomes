"""r69 deliverables — compose the parallax proof composite + copy shots."""
from PIL import Image, ImageDraw, ImageFont

FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
FONT_B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

A = Image.open("/tmp/e3/r69-a-y2200.png").convert("RGB")
B = Image.open("/tmp/e3/r69-b-y3200.png").convert("RGB")
w, h = A.size  # 1600x1000

HEAD = 110
GAP = 8
canvas = Image.new("RGB", (w * 2 + GAP, h + HEAD), "#f4ede3")
d = ImageDraw.Draw(canvas)

title = "r69 — listings palm field: HALF-SPEED parallax (fixed-attachment 'stagnant' pass replaced)"
sub = ("Scroll +1000px between shots: listings moved 1000px, palm field moved ~450-500px — "
       "clearly moving, never with the cards")
d.text((24, 16), title, fill="#3d2b1f", font=FONT_B)
d.text((24, 56), sub, fill="#6b5344", font=FONT_S)

canvas.paste(A, (0, HEAD))
canvas.paste(B, (w + GAP, HEAD))

tag_y = HEAD + 18
d.text((24, tag_y), "A — scrollY 2200  (--palms-y: 1040px)", fill="#3d2b1f", font=FONT_S)
d.text((w + GAP + 24, tag_y), "B — scrollY 3200  (--palms-y: 1596px)", fill="#3d2b1f", font=FONT_S)

# gutter annotation boxes (the measured strips)
for x0 in (w // 2 - 440, w + GAP + w // 2 - 440):
    d.rectangle([x0, HEAD + h - 210, x0 + 880, HEAD + h - 190], outline="#b05038", width=2)
d.text((w // 2 - 436, HEAD + h - 232),
       "measured strip: field shifted UP 450px here (both gutters, r=0.76/0.61)",
       fill="#b05038", font=FONT_S)

out = "/home/z/my-project/download/r69-parallax-proof.png"
canvas.save(out, optimize=True)
print("saved", out, canvas.size)

# straight copies of the verification shots
for src, dst in (
    ("/tmp/e3/r69-desktop-midband.png",
     "/home/z/my-project/download/r69-listings-drift-desktop.png"),
    ("/tmp/e3/r69-mobile-midband-b.png",
     "/home/z/my-project/download/r69-listings-drift-mobile.png"),
):
    Image.open(src).save(dst, optimize=True)
    print("saved", dst)
