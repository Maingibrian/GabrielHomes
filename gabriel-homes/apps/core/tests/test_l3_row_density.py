"""L3 — row conversion & density proving tests.

Binary checks (SCORECARD L3):
1. WhatsApp is the primary action (icon) — wa.me links carry the
   listing-row__whatsapp class and an inline SVG icon, and appear before
   Call/Email in the actions block.
2. Call and Email stay secondary via the existing brand-channel logic
   (brand first, agent fallback, hidden when unfilled).
3. Row min-height <= 320px on desktop (CSS).
4. Description truncated to 28 words.
5. Alternating sides kept (reverse row on every 2nd card).
6. Rows stack on mobile (single-column media query).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TEMPLATE = (REPO / "templates" / "listings" / "_results_grid.html").read_text(encoding="utf-8")
CSS = (REPO / "static" / "css" / "search.css").read_text(encoding="utf-8")

ACTIONS = re.search(
    r'<div class="listing-row__actions">(.*?)</div>\s*</div>\s*</article>',
    TEMPLATE, re.S).group(1)


def test_whatsapp_primary_with_icon():
    wa_links = re.findall(r'<a class="listing-row__whatsapp"[^>]*>', ACTIONS)
    assert len(wa_links) == 2, (
        "both brand and agent WhatsApp branches must carry the primary class")
    assert "wa.me/" in ACTIONS and ACTIONS.index("wa.me/") < ACTIONS.index("tel:")
    # icon: an inline svg inside the WhatsApp link
    assert re.search(
        r'listing-row__whatsapp"[^>]*>\s*<svg', ACTIONS, re.S), (
        "the WhatsApp primary action must carry an inline SVG icon")


def test_call_email_secondary_brand_channel_logic():
    # brand first, agent fallback — the existing channel logic, unchanged.
    assert '{% if brand.whatsapp %}' in ACTIONS and (
        '{% elif property.agent.display_whatsapp %}' in ACTIONS)
    assert '{% if brand.phone %}' in ACTIONS and (
        '{% elif property.agent.display_phone %}' in ACTIONS)
    assert '{% if brand.email %}' in ACTIONS and (
        '{% elif property.agent.display_email %}' in ACTIONS)
    # call/email keep the default (secondary) outline style — no primary class
    assert 'listing-row__whatsapp' not in ACTIONS.split('tel:')[1].split('{% endif %}')[0]


def test_row_min_height_320_desktop():
    rule = re.search(r"\.listing-row \{[^}]*\}", CSS)
    assert rule, ".listing-row rule must exist"
    body = rule.group(0)
    assert "min-height" in body, "desktop row must declare a min-height"
    m = re.search(r"min-height:\s*(\d+)px", body)
    assert int(m.group(1)) <= 320, (
        f"row min-height must be <= 320px on desktop, got {m.group(1)}px")


def test_description_truncated_28_words():
    assert "truncatewords:28" in TEMPLATE, (
        "description must be clamped to 28 words (was 34)")


def test_alternating_sides_kept():
    assert "forloop.counter|divisibleby:2" in TEMPLATE and "listing-row--reverse" in TEMPLATE
    assert ".listing-row--reverse" in CSS, "reverse-row CSS must stay"


def test_rows_stack_on_mobile():
    stack = re.search(r"\.listing-row,\.listing-row--reverse \{[^}]*grid-template-columns:\s*1fr", CSS)
    assert stack, "mobile media query must stack rows to one column"
