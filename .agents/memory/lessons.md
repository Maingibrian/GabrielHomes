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
- **Recycle-restore must seed FULLY — `--no-images` looks fine on the graphs and guts the site** (r101, 2026-11-15): after a recycle the DB was rebuilt with `seed_demo` minus images/enquiries — 80 listings, 0 `PropertyImage` rows. The homepage rendered photoless cards, the r100 sale-tile fan disappeared (its `{% if property.images.all.0.image %}` guards skipped), and the portal inbox was empty; it LOOKED like "progress lost + images broken" while git HEAD and served CSS were exactly r100. Always run step 5 as `seed_demo --clear --with-enquiries` (images are on by default — never add `--no-images` for speed on the preview DB). Health-check after any restore: `PropertyImage.objects.count() > 0` and sale listings with covers == sale listings (see `scripts/verify_after_reseed.py`; diagnosis in `scripts/diagnose_preview.py`).
- **The public gateway 403s non-browser User-Agents on /static/ + /media/** (r101): a HEAD probe with a bot UA gets 403 through `*.space-z.ai` while the same URL returns 200 with a Chrome UA. Always verify preview assets with a real browser UA or you'll chase phantom breakage.
- **The platform's `upload/` auto-commits can snapshot credentials into the tree** (r102, 2026-11-15): the owner's PAT was pasted as `upload/gabriels pat.txt`; auto-commit `15a2e2d2` tracked it; the next push shipped it to a PUBLIC repo (raw.githubusercontent served it 200 unauthenticated). Countermeasures now in place: `.gitignore` blocks token-shaped upload files (`*pat*.txt`, `*.pem`, `*.key`, `*token*`), and `scripts/push_safety_check.sh` (repo root) is a MANDATORY pre-push gate — it exits 1 on any secret pattern in the push range / HEAD tree / tracked token files / git config stores. Run it before EVERY push. If a credential has ever been pushed: tell the owner to revoke it FIRST (history rewrites don't un-leak), and never rewrite history here anyway (rule 7 — platform auto-commits must not be rebased away).
