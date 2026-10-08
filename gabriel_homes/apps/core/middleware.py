"""Core middleware — CSP (S10) and small cross-cutting helpers."""
from __future__ import annotations

# Content-Security-Policy per docs/PLAN.md S10. Adjustments to this string
# must be recorded in DECISIONS.md with the reason.
#
#   default-src 'self'        — everything not listed falls back to same-origin
#   img-src 'self' data: https://*.tile.openstreetmap.org
#                             — Leaflet map tiles come from OSM; data: for
#                               inline-encoded images
#   style-src 'self' 'unsafe-inline'
#                             — the template layer emits style="" attributes
#                               (e.g. gallery thumbnails' background-image);
#                               removing them is a refactor outside S10 scope
#   script-src 'self'         — all JS is external files from our own origin;
#                               inline <script> blocks were moved to /static/js
#                               in S10. Non-executable <script
#                               type="application/ld+json"> data blocks are
#                               unaffected by CSP script-src.
#   font-src 'self'           — self-hosted fonts only
#   connect-src 'self'        — fetch/XHR (HTMX) same-origin only
#   frame-ancestors 'none'    — we are never framed (clickjacking defence,
#                               supersedes X-Frame-Options DENY)
#   base-uri 'self'           — nobody can retarget our <base>
#   form-action 'self'        — forms may only post to us (allauth, search,
#                               enquiry)
CSP_POLICY = (
    "default-src 'self'; "
    "img-src 'self' data: https://*.tile.openstreetmap.org; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


class ContentSecurityPolicyMiddleware:
    """Add a Content-Security-Policy header to every response.

    Applied in config/settings/base.py so dev, tests and prod all send it
    (misbehaviour is caught by the test suite, not first seen in prod).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Content-Security-Policy", CSP_POLICY)
        return response
