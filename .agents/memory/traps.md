# traps.md — project-specific pitfalls (do not repeat)

Each entry: Symptom / Root cause / Fix / Commit / Applies to. Append-only.

1. **CSRF 403 through the gateway**
   Symptom: every POST form (login, enquiries, portal actions) 403s via :81 while :8000 works.
   Root cause: browser Origin (`http://127.0.0.1:81` or `https://…space-z.ai`) never matches the serving host.
   Fix: `scripts/launch_preview.py` sets `CSRF_TRUSTED_ORIGINS=http://127.0.0.1:81,https://*.space-z.ai`.
   Commit: `914d257a`. Applies to: any new gateway/port/proxy path; any change to CSRF settings.

2. **DisallowedHost 400 on the public preview URL**
   Symptom: public URL (`preview-chat-*.space-z.ai`) returns 400 before any view runs; localhost fine.
   Root cause: proxy chain space-z.ai → fcapp.run delivers Host headers unknown to Django.
   Fix: `EXTRA_ALLOWED_HOSTS=.space-z.ai,.fcapp.run` in the launch script.
   Commit: `33018bba`. Applies to: public preview access. NOTE: this bug shipped masked because prior verification used localhost only — always verify through the public URL too.

3. **Rate-limit key on raw X-Forwarded-For**
   Symptom: enquiry rate limit bypassable (10 instead of 3 in the reproduced bug).
   Root cause: first XFF entry is client-controlled → fresh bucket per forged header.
   Fix: `apps/core/clientip.py::get_client_ip()`; `X-Real-IP` only when `TRUST_X_REAL_IP=True` (prod).
   Commit: `19f67359` (r90, defect D-RL in PLAN S2). Applies to: any middleware or view keying on client IP.

4. **`seed_demo` without `--with-enquiries` silently seeds an empty inbox**
   Symptom: portal enquiries page shows "Nothing here" after a fresh reseed.
   Root cause: enquiries (and view counts for graphs) are opt-in via the flag (r73); the command prints "Sample enquiries: 0" but exits 0.
   Fix: `manage.py seed_demo --with-enquiries` (plus `--i-know-this-is-demo` required when DEBUG=False, guard C2).
   Commit: flag introduced r73 (`7c4978c1` lineage); bitten 2026-11-13 session. Applies to: every DB reseed after a recycle.

5. **Sandbox recycle wipes db.sqlite3 / .venv / daemon / unpushed work**
   Symptom: next session starts at an old commit, venv and DB missing, ports dead.
   Root cause: sandbox instances are recycled between sessions; only committed-and-pushed trees survive.
   Fix: push to GitHub before stopping; restore recipe in lessons.md.
   Commits: `24f33b97` (r84 restore), restorals on 2026-11-13. Applies to: end of every session.

6. **Untracked `media/demo-photos/` → "cards are back" regression**
   Symptom: listings fall back to Pillow gradient cards after a recycle.
   Root cause: demo-photo pools lived only on disk; recycle wiped them (bit three times).
   Fix: pools bundled in git (`.gitignore` keeps `!/media/demo-photos/`).
   Commit: `6534a273` (r57). Applies to: any .gitignore/media change.

7. **Background shells in this sandbox start at the git root**
   Symptom: `pytest` receipt shows `.venv/bin/python: No such file or directory` (exit 127) though the same line works in a foreground call.
   Root cause: background Bash calls do not inherit the previous `cd`; they start at `/home/z/my-project`.
   Fix: put `cd /home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes &&` inside the background command itself.
   Commit: observed 2026-11-13 (two failed receipts). Applies to: every background command in this workspace.
