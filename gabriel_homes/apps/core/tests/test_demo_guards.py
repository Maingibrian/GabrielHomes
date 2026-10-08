"""S4 / defects D-CRED + D-LAUNCH: demo credentials never reach production.

setup_accounts.py must:
  1. Refuse to run when settings.DEBUG is False (prod).
  2. Set a password only when it CREATES an account (or when the account has
     no usable password yet, e.g. freshly seeded) — never reset an existing
     password, so changing a password in prod/dev is never silently undone.
  3. Stay safe for the dev launcher to run on every start.
"""
import pytest

from apps.accounts.models import User

SCRIPT_PATH = "scripts/setup_accounts.py"

pytestmark = pytest.mark.django_db


def _run_setup_script():
    with open(SCRIPT_PATH) as fh:
        code = fh.read()
    exec(compile(code, SCRIPT_PATH, "exec"), {"__name__": "__main__"})


def _make_user(email, password, **flags):
    u = User.objects.create(email=email, full_name="X", **flags)
    if password is None:
        u.set_unusable_password()
    else:
        u.set_password(password)
    u.save()
    return u


def test_setup_accounts_refuses_to_run_when_debug_false(settings):
    settings.DEBUG = False
    admin = _make_user("admin@gabrielhomes.co.ke", "real-prod-secret-123",
                       is_staff=True, is_superuser=True)
    agent = _make_user("agent@gabrielhomes.co.ke", "agent-prod-secret-456", is_agent=True, is_staff=True)
    with pytest.raises(SystemExit):
        _run_setup_script()
    admin.refresh_from_db()
    agent.refresh_from_db()
    assert admin.check_password("real-prod-secret-123")
    assert agent.check_password("agent-prod-secret-456")


def test_setup_accounts_never_resets_changed_passwords(settings):
    """(b) Existing users whose passwords were changed keep their passwords."""
    settings.DEBUG = True
    _make_user("admin@gabrielhomes.co.ke", "changed-admin-pass-1",
               is_staff=True, is_superuser=True)
    _make_user("agent@agency.example", "changed-agent-pass-2", is_agent=True, is_staff=True)
    _run_setup_script()
    admin = User.objects.get(email="admin@gabrielhomes.co.ke")
    agent = User.objects.get(email="agent@agency.example")
    assert admin.check_password("changed-admin-pass-1")
    assert agent.check_password("changed-agent-pass-2")


def test_setup_accounts_sets_password_for_seeded_unusable_agent(settings):
    """A freshly seeded agent (unusable password) gets the initial demo
    password — an initial set, not a reset of an existing password."""
    settings.DEBUG = True
    _make_user("admin@gabrielhomes.co.ke", None, is_staff=True, is_superuser=True)
    _make_user("seeded@gabrielhomes.co.ke", None, is_agent=True)
    _run_setup_script()
    agent = User.objects.get(email="seeded@gabrielhomes.co.ke")
    assert agent.has_usable_password()
    assert agent.check_password("gabriel2026")


def test_setup_accounts_creates_missing_accounts_on_clean_copy(settings):
    """Launcher path: on a fresh copy, setup creates admin + agent with
    working demo logins."""
    settings.DEBUG = True
    assert User.objects.count() == 0
    _run_setup_script()
    admin = User.objects.get(email="admin@gabrielhomes.co.ke")
    agent = User.objects.get(email="hello@gabrielhomes.co.ke")
    assert admin.check_password("gabriel2026")
    assert agent.check_password("gabriel2026")
    assert admin.is_superuser and admin.is_staff
    assert agent.is_agent and agent.is_staff
