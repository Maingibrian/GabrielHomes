from PIL import Image
import statistics

for name in ["home", "about", "listings"]:
    img = Image.open(f"/tmp/preview-{name}.png").convert("RGB")
    small = img.resize((100, 60))
    px = list(small.getdata())
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]
    uniq = len(set(px))
    print(
        f"{name}: size={img.size} unique-colors={uniq} "
        f"lum-mean={statistics.mean(lum):.1f} lum-stdev={statistics.stdev(lum):.1f}"
    )
