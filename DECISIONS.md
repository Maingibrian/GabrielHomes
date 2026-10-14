# DECISIONS — settled by the user. Never reverse without asking.

1. AGENTS-ONLY ACCOUNTS (2026-10-14): normal users get NO accounts. Signup is
   closed via `apps/accounts/adapters.py` `is_open_for_signup()` -> False
   (renders `account/signup_closed.html`, POST mints nothing). Accounts =
   agents + superusers only. Provisioning: /admin/ -> User (staff + password)
   -> AgencyProfile.
2. HEADER = PLAN A (user-approved, DONE in r5): desktop top bar shows phone +
   email ONLY. No sign-in link in the header, no extra CSS. Agent access =
   footer "Company" column "Agent sign in" + mobile-menu link.
3. OFFLINE WINDOWS DEPLOYMENT: user's corporate network blocks pypi.org.
   Delivery = update zips on the :3000 page. Zip carries wheels/ so the
   updater self-repairs .venv with no internet. Bats: CRLF-only, ASCII
   prompts, idempotent markers, no parenthesized blocks; .gitattributes
   enforces CRLF at source.
4. PROPERTIES "ENDLESS LOADING" root cause: SQLite on mapped network drive
   Z: stalls — not a code bug. Fix v5.1: launcher relocates the site to
   %LOCALAPPDATA%\GabrielHomes; drive detection is locale-proof (PowerShell
   Win32_LogicalDisk DriveType -eq 4 fallback, numeric).
5. PORTS: Django :3011 (daemon_runserver.py from repo root, system python3),
   delivery page :3000 (workspace_server.py). Never hand localhost URLs to
   the user; deliverables go on the :3000 download page.
6. ROLLBACK DEFENSES (2026-10-14, after a real snapshot rollback): git
   history slimmed (zips/wheels/QA shots purged); session tripwire
   scripts/session_check.sh runs FIRST; session backup = git bundle + db
   snapshot published to :3000; docs split small (WORK/CODEMAP/DECISIONS/
   REBUILD + tail-only worklog). GitHub push is allowed and verified
   reachable — needs the user's repo + token.
7. NO graph/code-index plugin: ~300-file repo, grep + CODEMAP is enough;
   plugin indexes would live on the same rollback-able disk; Flash-tier
   reliability with extra tools is a risk.
8. TEST GATE before any delivery: full pytest via .venv + manage.py check.
9. DB re-seed after a wipe: `migrate` + `manage.py seed_demo` (80 listings,
   6 users as of 2026-10-14); scripts/setup_accounts.py for accounts.
