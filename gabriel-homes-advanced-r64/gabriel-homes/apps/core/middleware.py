"""Core middleware — CSP (S10) and small cross-cutting helpers."""
from __future__ import annotations

import os
import sys

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

# Sandbox live-preview variant: the workspace preview panel renders the
# site inside an iframe, so frame-ancestors must open up (and the
# X-Frame-Options header must be dropped) *there and only there*.
# Tests and production keep the strict policy — see
# _preview_framing_allowed() for the triple gate.
CSP_POLICY_PREVIEW = CSP_POLICY.replace(
    "frame-ancestors 'none';", "frame-ancestors *;"
)


def _preview_framing_allowed() -> bool:
    """True only inside the sandbox live-preview runserver process.

    Triple-gated so the loosened framing can never leak elsewhere:
      1. Not under pytest (PYTEST_CURRENT_TEST is set per-test by pytest;
         a module-level env check keeps the whole suite strict).
      2. GABRIEL_PREVIEW_BRIDGE=1 — present only in the sandbox .env,
         which is excluded from every shipped zip.
      3. This process is `manage.py runserver` — never test/shell/
         migrate/gunicorn.
    """
    if "PYTEST_CURRENT_TEST" in os.environ:
        return False
    if os.environ.get("GABRIEL_PREVIEW_BRIDGE") != "1":
        return False
    return len(sys.argv) >= 2 and sys.argv[1] == "runserver"


class ContentSecurityPolicyMiddleware:
    """Add a Content-Security-Policy header to every response.

    Applied in config/settings/base.py so dev, tests and prod all send it
    (misbehaviour is caught by the test suite, not first seen in prod).
    In the sandbox preview process only (triple gate above) the preview
    policy is sent instead and X-Frame-Options is exempted, so the
    workspace's iframe preview panel can render the site.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if _preview_framing_allowed():
            response.headers.setdefault(
                "Content-Security-Policy", CSP_POLICY_PREVIEW
            )
            # Django's XFrameOptionsMiddleware (listed before us, so it
            # runs after us on the response path) honours this attribute
            # and skips the X-Frame-Options header.
            response.xframe_options_exempt = True
        else:
            response.headers.setdefault("Content-Security-Policy", CSP_POLICY)
        return response
