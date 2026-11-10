"""Client IP resolution for rate limiting (PLAN task S2, defect D-RL).

A client fully controls the first X-Forwarded-For entry, so that header
must NEVER be trusted for rate limiting: rotating it gives an attacker a
fresh bucket per request (10 enquiries instead of 3 in the reproduced bug).

Behind the production nginx (DEPLOY.md, task D4) the proxy sets
`X-Real-IP $remote_addr` from the real socket address, which the client
cannot forge through the proxy. We trust that header only when the
TRUST_X_REAL_IP setting is on (True in prod, False in dev).
"""
from __future__ import annotations

from django.conf import settings


def get_client_ip(request) -> str:
    """Return the best-available client IP for rate-limiting decisions.

    TRUST_X_REAL_IP on  -> X-Real-IP when present (set by our own nginx),
                           otherwise REMOTE_ADDR.
    TRUST_X_REAL_IP off -> REMOTE_ADDR only.

    X-Forwarded-For is never read: its first entry is client-controlled.
    """
    if getattr(settings, "TRUST_X_REAL_IP", False):
        real = (request.headers.get("X-Real-IP") or "").strip()
        if real:
            return real
    return request.META.get("REMOTE_ADDR", "")
