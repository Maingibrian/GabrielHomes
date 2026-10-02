"""Template tags for the core app — currently just the `kes` filter."""
from decimal import Decimal

from django import template

register = template.Library()


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
