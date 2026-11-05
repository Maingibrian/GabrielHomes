"""Gabriel Homes branded admin site — r11.

The owner must never see the stock Django admin skin, so the whole
admin lives on its own AdminSite instance with Gabriel Homes branding
(wordmark, colours, Geist fonts — see static/css/admin-studio.css and
templates/admin/base_site.html).

The instance keeps Django's default namespace/name ("admin"), so every
existing `{% url 'admin:index' %}`, `reverse("admin:...")` and test
keeps working — only the presentation changes.
"""
from __future__ import annotations

from django.contrib.admin import AdminSite


class GabrielHomesAdminSite(AdminSite):
    """The Gabriel Homes power area ("Studio"), fully re-skinned."""

    # Branding (rendered by our templates/admin/base_site.html + CSS)
    site_header = "Gabriel Homes"
    site_title = "Gabriel Homes"
    index_title = "Overview"

    # "View site" points at the public home page
    site_url = "/"


# Mounted at /admin/ in config/urls.py. The name stays "admin" to keep
# URL reversing identical to Django's default site.
gabriel_admin = GabrielHomesAdminSite(name="admin")
