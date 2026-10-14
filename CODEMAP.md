# CODEMAP — one line per thing. Read when navigating, not every session.

## Repo root (/home/z/my-project = git root)
- WORK.md / DECISIONS.md / CODEMAP.md / REBUILD.md — session docs (this system)
- worklog.md — append-only history (tail -30 only, never read fully)
- scripts/ — sandbox tooling; scripts/preview_site/ — :3000 delivery page
- download/ — user deliverables (gitignored; bundle + db backup + update zip)

## Django project (gabriel_homes/)
- config/settings/{base,dev,prod,test_pg}.py — settings split; dev default
- apps/core/ — home/about/services/contact pages, middleware, KES filter
- apps/listings/ — Property + PropertyImage, search/filters, `seed_demo` cmd
- apps/agents/ — AgencyProfile, agent directory + agent dashboard
- apps/accounts/ — custom User (email login); adapters.py CLOSES signup
  (agents-only); saved searches/properties; rate_limit.py
- apps/inquiries/ — enquiry form + email; `purge_inquiries` cmd
- apps/locations/ — location models
- templates/includes/_header.html — top bar: phone + email ONLY (Plan A);
  mobile menu has the "Agent sign in" link
- templates/includes/_footer.html — footer "Agent sign in" (anonymous only)
- templates/account/ — login (styled "[ Agent access ]"), signup_closed,
  logout, _auth_styles.html
- static/css/ tokens|base|components|pages|home|search|detail|dashboard
- static/vendor/leaflet/ — map; static/img, static/video — real site media
- gabriel_homes/wheels/ — Windows wheels for offline zips (gitignored;
  rebuild: `bash scripts/vendor_wheels.sh` — needs network)
- requirements.txt — pinned deps; also the source for wheel vendoring
- gabriel_homes/BRIEF.md — the full original build brief (was WORK.md; big)

## Sandbox scripts (scripts/)
- daemon_runserver.py — :3011 Django daemon (start from repo root, python3)
- workspace_server.py — :3000 locked delivery server
- start-servers.sh — starts/health-checks both (idempotent)
- build_update_zip.sh / sync_preview_files.sh — update zip build + publish
- vendor_wheels.sh — re-download the 30 win_amd64 wheels (CPython 3.10–3.13)
- patch_bats_v51.py — idempotent CRLF patcher for the Windows bats (v5.1)
- session_check.sh — ROLLBACK tripwire (run first every session)
- make_bundle.sh — session-end backup: bundle + db snapshot + :3000 publish
- slim_history.sh — one-pass history slim-down (2026-10-14; do not re-run)
- capture_auth_shots.py — Playwright screenshots (use SYSTEM python3)
- launcher/ — Windows START/STOP bats (v5.1: local-disk relocation +
  locale-proof network-drive detection)

## Docs (historical)
- gabriel_homes/docs/{PLAN,STATUS,DECISIONS,AGENT-BRIEF,OWNER-INPUTS}.md —
  build-phase documents; gabriel_homes/docs/shots/ — evidence screenshots
