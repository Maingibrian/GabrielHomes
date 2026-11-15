#!/usr/bin/env python3
"""r103 — VLM review of the listing detail page (whole-page, component-scored).

Runs scripts/vlm.py over the review crops; writes a structured verdict per
component with 0-10 scores, then a summary. One pass, no agent looping.
"""
import sys

sys.path.insert(0, "/home/z/my-project/scripts")
from vlm import vlm  # noqa: E402

OUT = "/home/z/my-project/download/screenshots/r103"

PROMPT = """You are a world-class property-website art director reviewing a
listing detail page (Gabriel Homes, a boutique coastal-Kenya agency).
Image: a vertical slice of the full desktop page (1920px wide).

Score each component you can see in THIS slice from 0-10 and name its single
biggest styling weakness (be blunt, specific, no praise padding):
- header/intro (eyebrow, title, location, price, actions)
- gallery (main image, thumbs, nav, counter)
- facts bar (bedrooms/bathrooms/area/furnishing)
- description block
- amenities grid
- nearby amenities cards
- map section
- sidebar contact card (logo, buttons, enquiry form)
- similar properties rail
Not all components appear in every slice; only score what is visible.
Return strict JSON: {"components":[{"name":"...","score":N,"weakness":"..."}],
"overall":N,"notes":"..."} with 1-2 sentence notes on overall design quality.
"""


def run(img: str, label: str) -> None:
    print(f"===== {label} =====")
    try:
        print(vlm(img, PROMPT))
    except Exception as exc:  # noqa: BLE001
        print(f"VLM failed on {img}: {exc}")


if __name__ == "__main__":
    for slug in ["rv-desktop-a", "rv-desktop-b", "rv-desktop-c",
                 "rv-mobile-a", "rv-mobile-b"]:
        run(f"{OUT}/{slug}.jpg", slug)
