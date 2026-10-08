"""Template tags for the core app — `kes` price filter and `json_ld_script`."""
import json
from decimal import Decimal

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe

register = template.Library()

# Same escape scheme as Django's json_script filter (django.utils.html):
# <, > and & become JSON-native unicode escapes so a user-supplied string
# like "</script>" cannot break out of an embedding <script> tag.
_JSON_SCRIPT_ESCAPES = {
    ord(">"): "\\u003E",
    ord("<"): "\\u003C",
    ord("&"): "\\u0026",
}


@register.filter
def json_ld_script(value) -> str:
    """Serialize a dict as JSON that is safe to embed in a <script> tag.

    Usage:
        <script type="application/ld+json">{{ json_ld|json_ld_script }}</script>

    Unlike `|safe`, hostile strings in user-controlled fields (e.g. a
    listing title containing `</script>`) are neutralized: `<`, `>` and `&`
    are escaped as \\u003C / \\u003E / \\u0026 inside JSON string literals,
    which parse back to the original characters. The output stays valid
    JSON for schema.org parsers.

    Safety: mark_safe is sound here because after translate() the output
    contains no raw `<`, `>` or `&` anywhere — the only sequence that can
    end a script data block is `</script`, and its `<` and `>` are gone.
    Non-ASCII (incl. U+2028/2029) is escaped by ensure_ascii=True.
    """
    json_str = json.dumps(value, cls=DjangoJSONEncoder, indent=2).translate(
        _JSON_SCRIPT_ESCAPES
    )
    return mark_safe(json_str)


@register.filter
def kes(value, period: str | None = None) -> str:
    """Format a Decimal/number as a Kenyan-shilling price.

    Usage:
        {{ property.price|kes }}
        {{ property.price|kes:"monthly" }}     -> "KES 95,000 / month"
        {{ property.price|kes:"total" }}       -> "KES 12,500,000"

    The `period` argument is optional; when given it appends "/ month"
    for rent listings and nothing for sale listings. Pass it explicitly
    from the template via `property.price_period` if you want the suffix
    to depend on the property.
    """
    if value is None or value == "":
        return ""
    try:
        amount = Decimal(str(value))
    except Exception:
        return str(value)
    formatted = f"{amount:,.0f}"
    if amount == amount.to_integral_value():
        # Integer-like amounts stay without decimals.
        pass
    else:
        formatted = f"{amount:,.2f}"
    out = f"KES {formatted}"
    if period == "monthly":
        out += " / month"
    return out


@register.filter
def kes_short(value) -> str:
    """Compact KES representation: 'KES 12M' / 'KES 95K'.

    Useful in cards where space is tight. Rounds down to the nearest
    million or thousand (no decimals).
    """
    if value is None or value == "":
        return ""
    try:
        amount = Decimal(str(value))
    except Exception:
        return str(value)
    if amount >= 1_000_000:
        return f"KES {int(amount // 1_000_000)}M"
    if amount >= 1_000:
        return f"KES {int(amount // 1_000)}K"
    return f"KES {int(amount)}"


@register.simple_tag(takes_context=True)
def absolute_url(context, path: str = "") -> str:
    """Build an absolute URL from a path, using the current request.

    Usage: {% load core_tags %}{% absolute_url property.get_absolute_url %}
    """
    request = context.get("request")
    if request:
        return request.build_absolute_uri(path)
    return path
