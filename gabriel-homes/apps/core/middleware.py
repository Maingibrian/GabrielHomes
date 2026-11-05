"""Core middleware — CSP (S10) and small cross-cutting helpers."""
from __future__ import annotations

# Content-Security-Policy per docs/PLAN.md S10. OpenFreeMap serves both the
# search-page map and the property-detail map (self-hosted MapLibre GL; the
# detail page's old OpenStreetMap iframe embed left in run 14, so frame-src
# could go with it — we frame nothing and nobody frames us).
#
#   default-src 'self'        — everything not listed falls back to same-origin
#   img-src 'self' data: blob: https://tiles.openfreemap.org
#                             — local assets and map sprite images
#   style-src 'self' 'unsafe-inline'
#                             — the template layer emits style="" attributes
#                               (e.g. gallery thumbnails' background-image);
#                               removing them is a refactor outside S10 scope
#   script-src 'self'         — local JS and MapLibre GL JS module
#                               inline <script> blocks were moved to /static/js
#                               in S10. Non-executable <script
#                               type="application/ld+json"> data blocks are
#                               unaffected by CSP script-src.
#   font-src 'self'           — self-hosted fonts only
#   connect-src 'self' https://tiles.openfreemap.org
#                             — HTMX and OpenFreeMap vector data
#   worker-src 'self' blob:   — MapLibre map rendering worker
#   frame-ancestors 'none'    — we are never framed (clickjacking defence,
#                               supersedes X-Frame-Options DENY)
#   base-uri 'self'           — nobody can retarget our <base>
#   form-action 'self'        — forms may only post to us (allauth, search,
#                               enquiry)
CSP_POLICY = (
    "default-src 'self'; "
    "img-src 'self' data: blob: https://tiles.openfreemap.org; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; "
    "font-src 'self'; "
    "connect-src 'self' https://tiles.openfreemap.org; "
    "worker-src 'self' blob:; "
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
