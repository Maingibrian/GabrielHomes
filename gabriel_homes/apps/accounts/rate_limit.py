"""Rate-limiting decorator for auth endpoints.

Per WORK.md §11 Phase 7: rate limiting on auth endpoints.
The enquiry endpoint already has its own rate limiter (apps/inquiries/views.py);
this module provides a reusable decorator for login/signup/password-reset.

Uses the DB-backed LocMemCache — fine for v1 single-instance deployments.
For multi-instance, switch to Redis via django-redis-memcached.
"""
from __future__ import annotations

from functools import wraps
from time import time

from django.core.cache import cache
from django.http import HttpResponse


def rate_limit(key_func, max_requests: int = 5, window: int = 60):
    """Decorate a view to rate-limit requests.

    Args:
        key_func: callable(request) -> str — the cache key (e.g. IP + path).
        max_requests: max requests per window.
        window: window in seconds.

    Returns 429 Too Many Requests when the limit is exceeded.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            key = key_func(request)
            now_ts = time()
            timestamps = cache.get(key, [])
            timestamps = [ts for ts in timestamps if now_ts - ts < window]
            if len(timestamps) >= max_requests:
                return HttpResponse(
                    "Too many requests. Please wait a minute and try again.",
                    status=429,
                )
            timestamps.append(now_ts)
            cache.set(key, timestamps, window)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def auth_rate_limit_key(request) -> str:
    """Cache key for auth rate limiting: IP + path."""
    xff = request.headers.get("X-Forwarded-For", "")
    ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "unknown")
    return f"auth_rl:{ip}:{request.path}"


def auth_rate_limit(max_requests: int = 5, window: int = 60):
    """Convenience decorator: rate-limit an auth view by IP + path."""
    return rate_limit(auth_rate_limit_key, max_requests=max_requests, window=window)
