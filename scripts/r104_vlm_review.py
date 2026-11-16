#!/usr/bin/env python3
"""r104 — VLM AFTER review of the redesigned Edit-listing page."""
import sys

sys.path.insert(0, "/home/z/my-project/scripts")
from vlm import vlm  # noqa: E402

OUT = "/home/z/my-project/download/screenshots/r104"

PROMPT = """You are a world-class product designer reviewing the BACKEND
"Edit listing" form of Gabriel Homes. This is the AFTER shot of a redesign
that aimed to fix: placeholder [ EDIT ] tag, dead sidebar, ghosting sticky
actions bar, clipped legends, one-per-row mobile amenities, missing field
help, weak selected-tile states.

Score each element you can see in THIS slice 0-10 and name its single
biggest weakness (blunt, specific):
- page shell (sidebar, header, title area)
- form sections/legends (grouping, card treatment)
- field rows (labels, inputs, selects, spacing)
- textarea/description field
- checkbox tiles (amenities)
- actions bar (save/cancel)
Not all appear in every slice; score only what is visible.
Return strict JSON: {"elements":[{"name":"...","score":N,"weakness":"..."}],
"overall":N,"notes":"1-2 sentences"}.
"""


def run(img: str, label: str) -> None:
    print(f"===== {label} =====")
    try:
        print(vlm(img, PROMPT))
    except Exception as exc:  # noqa: BLE001
        print(f"VLM failed on {img}: {exc}")


if __name__ == "__main__":
    for slug in ["rv-desktop-a", "rv-desktop-b", "rv-mobile-a", "rv-mobile-b"]:
        run(f"{OUT}/{slug}.jpg", slug)
