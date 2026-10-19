# WORK.md — Gabriel Homes session state. READ FIRST, EVERY SESSION.

Full project brief (mission, design law, non-copy rules): `gabriel_homes/BRIEF.md`
— big file, read on demand only. Settled choices: `DECISIONS.md`. Code map:
`CODEMAP.md`. Recovery: `REBUILD.md`. History: `worklog.md` (tail only).

## SESSION RULES
1. Run `bash scripts/session_check.sh` FIRST. ROLLBACK = STOP, tell the user,
   restore from `download/gabriel-homes.bundle` (REBUILD.md step 1) before
   touching anything.
2. Never read worklog.md in full — read only its last ~30 lines.
3. Find code via grep + CODEMAP.md; don't open whole files unless editing.
4. Commit after every finished task. Small commits.
5. Session end: update LAST_COMMIT below, append worklog.md, run
   `bash scripts/make_bundle.sh`, tell the user to download the bundle.
6. Respect DECISIONS.md — never reverse a user decision without asking.
7. Never claim something works unless you ran it this session.
8. Reply to the user in English only. Deliverables go on the :3000 page.

LAST_COMMIT: f3d5f12 (2026-10-19 — r15: typography audit, Geist+Fraunces+Mono retained (8.7/10); 38 mono blocks re-tracked to --track-mono, sub-13px dashboard/admin text to floor, measures capped (story 47ch, prose 44ch), --leading-prose token, font preloads. Sandbox rollback 2026-10-19 05:17 wiped gitignored artifacts; media restored from r14 split-parts rejoin (md5-verified).)
NEXT:
  1) User: apply r11 zip on Windows (extract -> UPDATE-WEBSITE.bat -> START),
     and download the bundle + db backup after every session.
     r11 highlights: owner account admin@gabrielhomes.co.ke (temp password in
     OWNER-LOGIN.txt on the :3000 page — change on first login), owner
     dashboard at /dashboard/ (all-agency listings/inquiries, agency +
     account management, demo-data switch, CSV import), branded "Studio"
     admin at /admin/ (no Django skin), footer newsletter removed, and the
     r10 header-comment leak fixed (re-apply r10→r11 even if r10 applied).
  2) GitHub push LIVE: main -> github.com/Maingibrian/GabrielHomes (private) at 90a3968 (r9),
     forced over the GitHub-Desktop snapshot (994aa75). Future pushes: user edits
     the fine-grained token (same value) to keep Contents R/W active / or makes
     a fresh 7-day token, then `bash scripts/push_github.sh <PAT>`. User advised
     NEVER to push from PC GitHub Desktop (snapshot history diverged); re-clone
     instead. Token never stored locally.
     (PRIVATE, created via user's GitHub Desktop; placeholder/snapshot history).
     User must create a FINE-GRAINED PAT (7 days, only GabrielHomes, Contents:
     Read and write) at github.com/settings/personal-access-tokens/new, then
     agent runs `bash scripts/push_github.sh <PAT>`. Token never stored in git
     config; user can revoke right after. Setup steps also on the :3000 root
     page ("GitHub — one-time push permission" section). Classic tokens: refuse.
     Bundle stays the offline fallback.
  3) Backlog: password-reset pages still allauth-default styling; real agent
     portraits; demo images on reseeded sandbox DB are generated placeholders
     (run scripts/assign_demo_images.py to re-attach real photos); listing-card
     Enquire affordance; journal/blog for SEO; map search; saved-search alerts;
     bond calculator.

## HARD FACTS
- Django 5.2 + allauth 65.x, SQLite (`gabriel_homes/db.sqlite3`, gitignored).
- venv: `gabriel_homes/.venv` — system python3 has NO Django; always
  `gabriel_homes/.venv/bin/python` for manage.py / pytest.
- :3011 Django — `python3 scripts/daemon_runserver.py` FROM /home/z/my-project.
- :3000 delivery page — `python3 scripts/workspace_server.py`; page at
  `/scripts/preview_site/index.html`, artifacts in `scripts/preview_site/files/`.
- Windows deploy is OFFLINE (pypi.org blocked on user network): build zip via
  `UPDATE_TAG=rX bash scripts/build_update_zip.sh` then
  `bash scripts/sync_preview_files.sh` (CRLF-enforced, byte-verified).
- Test gate: `.venv/bin/python -m pytest` (328 green) + `manage.py check`.
- History is SLIMMED (zips/wheels/QA shots purged 2026-10-14). NEVER `git add`
  `*.zip`, `gabriel_homes/wheels/`, `db.sqlite3`, or anything under `download/`.
- Sandbox rollbacks happen (2026-10-14: disk restored to old snapshot midday,
  wiped half a session). The tripwire + bundle exist because of that.
