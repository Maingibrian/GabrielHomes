# lessons.md — append-only debugging knowledge

Seed entries: things found in the 2026-11-13 repo survey (git log, configs,
gateway code) that already cost a prior round. Append what you learn; never edit.

- **Recycle restore recipe** (cost: a full rebuild every recycle; r84 `24f33b97`, 2026-11-13):
  1. `git fetch <remote> main && git reset --hard FETCH_HEAD` (workspace rolls back to an old commit)
  2. `uv venv .venv --python 3.12 && uv pip install -r requirements.txt --python .venv/bin/python`
  3. `.venv/bin/python manage.py migrate --noinput`
  4. `.venv/bin/python manage.py bootstrap_owner --password <pw>`
  5. `.venv/bin/python manage.py seed_demo --with-enquiries` (else empty inbox — trap #4)
  6. `python3 scripts/launch_preview.py` (repo root; daemon double-fork, pidfile `/tmp/django.pid`)
- **Verify through the path the user actually uses.** The public-URL DisallowedHost bug (trap #2) shipped because verification ran on localhost/:81 only; the Host header differs per hop.
- **Preview/gateway env config belongs in the launch script, not Django settings** (pattern of `914d257a` + `33018bba`): `env.setdefault(...)` in `launch_preview.py` keeps plain local runs unaffected and survives recycles via git.
- **`bash scripts/gate.sh` is the repo's own gate** (AGENT-BRIEF "Gate" section): check + makemigrations --check + pytest + G-DEPLOY/G-SAFE/G-CDN/G-STATIC/G-COV. Run it before marking dev tasks DONE; it must exit 0.
- **Platform UUID auto-commits** (e.g. `a3dd47fe`) land between sessions — usually `upload/` snapshots. Commit on top; never rewrite or rebase them away.
- **pytest must run from the Django dir**; background shells start at git root (trap #7). `PIPESTATUS[0]` is the real pytest exit, not the `tail`'s.
- **`docs/DECISIONS.md` + `LOOP/` (in the Django tree) already record architecture decisions and design-loop state** — read before proposing anything map/animation/CSP related; several plausible approaches there are recorded as rejected.
