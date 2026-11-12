"""allauth adapter — keep custom User clean, mirror email as username,
apply rate limiting to login attempts.

Per WORK.md §11 Phase 7: rate limiting on auth endpoints.

r90 (backend reassessment) merges the login-redirect adapter INTO this
one: allauth reads a single ACCOUNT_ADAPTER, so the role-aware
destination (superuser → /manage/, agent → /dashboard/) lives here as
get_login_redirect_url().
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

    def get_login_redirect_url(self, request):
        """r90: after sign-in, land each role where they work.

        The owner (superuser) was landing on the public homepage with
        no link to /manage/ anywhere — the portal address had to be
        memorised. Superusers now land in the owner portal, agents in
        their dashboard, everyone else on the homepage (unchanged).
        Allauth still honours an explicit ?next= before asking here,
        so deep links like /manage/enquiries/ keep working.
        """
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            if user.is_superuser:
                return "/manage/"
            if user.is_agent:
                return "/dashboard/"
        return "/"

    def authenticate(self, request, **credentials):
        """Rate-limit login attempts before they reach the auth backend.

        5 attempts per minute per IP. Raises PermissionDenied when exceeded.
        """
        from django.core.cache import cache
        from django.core.exceptions import PermissionDenied
        import time as _time

        if request:
            # r90: key on the project's OWN client-ip helper, never the
            # client-supplied X-Forwarded-For (D-RL / apps.core.clientip
            # policy). The old XFF-first key let an attacker rotate the
            # header to dodge this layer and double-counted legitimate
            # logins across two buckets.
            from apps.core.clientip import get_client_ip

            ip = get_client_ip(request)
            key = f"auth_login_rl:{ip}"
            now_ts = _time.time()
            timestamps = cache.get(key, [])
            timestamps = [ts for ts in timestamps if now_ts - ts < 60]
            if len(timestamps) >= 5:
                raise PermissionDenied("Too many login attempts. Please wait a minute.")
            timestamps.append(now_ts)
            cache.set(key, timestamps, 60)
        return super().authenticate(request, **credentials)

