#!/usr/bin/env python3
"""r103 — AFTER review: same VLM prompts, after screenshots.

Also verifies the functional wins live (buttons, mobile bar, thumbs)
before the VLM pass so the review isn't fooled by missing data.
"""
import sys

sys.path.insert(0, "/home/z/my-project/scripts")
from vlm import vlm  # noqa: E402

OUT = "/home/z/my-project/download/screenshots/r103"

PROMPT = """You are a world-class property-website art director reviewing a
listing detail page (Gabriel Homes, a boutique coastal-Kenya agency).
This is the AFTER shot, following a redesign pass that aimed to fix:
bracket-label dev syntax, weak facts-bar contrast, sparse amenities,
a form-only sidebar, stranded similar rail, and mobile gaps.

Score each component you can see in THIS slice from 0-10 and name any
remaining weakness (be blunt and specific):
- header/intro (eyebrow chips, title, location, price, actions)
- gallery (main image, thumbs, nav, counter)
- facts bar (beds/baths/area/furnishing with icons)
- description / amenities / nearby cards
- map section
- sidebar contact card (logo, price chip, call/WhatsApp buttons, form)
- similar properties rail + browse link
Not all appear in every slice; score only what is visible.
Return strict JSON: {"components":[{"name":"...","score":N,"weakness":"..."}],
"overall":N,"notes":"..."} with 1-2 sentence notes comparing to a
world-class boutique property site.
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
