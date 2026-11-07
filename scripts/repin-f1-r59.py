#!/usr/bin/env python3
"""r59: re-pin the F1 ratchets after the accessibility sweep (43 -> 4)."""
from pathlib import Path

P = Path("/home/z/my-project/gabriel-homes/apps/core/tests/test_f1_token_integrity.py")
text = P.read_text(encoding="utf-8")

# --- 1. baselines -------------------------------------------------------
old_hex = 'HEX_BASELINE = 201   # hard-coded hex outside tokens.css; may only go DOWN'
assert old_hex in text
# replace the two constant lines wholesale (keep the history, append r59)
start = text.index("HEX_BASELINE = 201")
end = text.index("\n", text.index("constant re-pinned to the recorded ratchet at r34)")) + 1
new_consts = (
    'HEX_BASELINE = 198   # hard-coded hex outside tokens.css; may only go DOWN\n'
    '                           # (240 @r17, 236 @r18, 217 @r21, 215 @r24, 214 @r30,\n'
    '                           # 211 @r34, 201 @r38 — search.css fully tokenised,\n'
    '                           # D-LOOP-38a; 200 @r58; 198 @r59 — the coastal\n'
    '                           # home-nearby band swapped its 60%-alpha grey\n'
    '                           # whites for solid rgba() whites, D-LOOP-59a)\n'
    'SUB13_BASELINE = 4  # px font sizes below 13px; may only go DOWN (44 pre-r22,\n'
    '                     # corrected to 43 @r22 D-LOOP-22a, re-pinned @r34; 43 -> 4\n'
    '                     # @r59 — the owner-round-nine accessibility sweep\n'
    '                     # ("words can be read and are not too small") lifted\n'
    '                     # EVERY visitor-facing sub-13px size to the 13px\n'
    '                     # --text-xs floor: home.css 18 -> 0, search.css 13 -> 1,\n'
    '                     # detail.css 9 -> 1, components.css 1 -> 0. Survivors:\n'
    '                     # maplibre attributions + staff dashboard labels only)\n'
)
text = text[:start] + new_consts + text[end:]

# --- 2. allowlist + pair baselines --------------------------------------
start = text.index("FONT_FLOOR_ALLOWLIST = {")
end = text.index("}", text.index("FONT_FLOOR_PAIR_BASELINE = {")) + 1
new_block = '''FONT_FLOOR_ALLOWLIST = {
    ("dashboard.css", 10): "admin/staff dashboard micro labels — staff-only "
                           "tool surface, not visitor-facing",
    ("detail.css", 9): "maplibre attribution overlay — third-party license "
                       "fine print the map SDK renders itself",
    ("search.css", 10): "maplibre attribution overlay — third-party license "
                        "fine print the map SDK renders itself",
}

# per-(file, px) counts, re-pinned at r59 (owner round nine) — the
# accessibility sweep lifted every visitor-facing sub-13px size to the
# floor, so the allowlist is now only maplibre attributions and the
# staff dashboard. Listed pairs must not grow either.
FONT_FLOOR_PAIR_BASELINE = {
    ("dashboard.css", 10): 2,
    ("detail.css", 9): 1,
    ("search.css", 10): 1,
}'''
text = text[:start] + new_block + text[end:]

P.write_text(text, encoding="utf-8")
print("re-pinned; new baselines: SUB13=4, HEX=198")
