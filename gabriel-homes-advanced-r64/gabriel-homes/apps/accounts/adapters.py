"""allauth adapter — keep custom User clean, mirror email as username,
apply rate limiting to login attempts.

Per WORK.md §11 Phase 7: rate limiting on auth endpoints.
"""
from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """Gabriel Homes allauth adapter.

    Email is the only login field (see settings.ACCOUNT_*), so we make
    sure signup doesn't try to populate a username column.
    """

    def is_open_for_signup(self, request):
        """Public sign-up is closed by product decision (2026-10-14).

        Only agents and superusers hold accounts; agents are provisioned
        by an admin via Django admin (create User + AgencyProfile, set
        password). With this returning False, allauth renders
        account/signup_closed.html for anyone hitting /account/signup/.
        """
        return False

    def save_user(self, request, user, form, commit=True):
        # Populate `full_name` from the form if the field is present.
        full_name = form.cleaned_data.get("full_name") if form else None
        if full_name:
            user.full_name = full_name
        return super().save_user(request, user, form, commit=commit)

    def authenticate(self, request, **credentials):
        """Rate-limit login attempts before they reach the auth backend.

        5 attempts per minute per IP. Raises PermissionDenied when exceeded.
        """
        from django.core.cache import cache
        from django.core.exceptions import PermissionDenied
        import time as _time

        if request:
            xff = request.headers.get("X-Forwarded-For", "")
            ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "unknown")
            key = f"auth_login_rl:{ip}"
            now_ts = _time.time()
            timestamps = cache.get(key, [])
            timestamps = [ts for ts in timestamps if now_ts - ts < 60]
            if len(timestamps) >= 5:
                raise PermissionDenied("Too many login attempts. Please wait a minute.")
            timestamps.append(now_ts)
            cache.set(key, timestamps, 60)
        return super().authenticate(request, **credentials)
