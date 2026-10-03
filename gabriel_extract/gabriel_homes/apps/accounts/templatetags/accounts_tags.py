"""Template tags for the accounts app."""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def is_saved(context, property) -> bool:
    """Return True if the current user has saved the given property.

    Usage: {% load accounts_tags %}{% is_saved property as saved %}
    """
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False
    return request.user.saved_properties.filter(property=property).exists()
