# REBUILD — restore a wiped / rolled-back sandbox. Read top to bottom.

## 0. Detect first
    bash scripts/session_check.sh
If it reports ROLLBACK (recorded commit missing / HEAD not a descendant):

## 1. Restore history from the bundle (user uploads gabriel-homes.bundle)
    cd /home/z/my-project
    git fetch /path/to/gabriel-homes.bundle 'main:refs/bundle-main'
    git reset --hard refs/bundle-main
    git update-ref -d refs/bundle-main
If the bundle is OLDER than work the user remembers, SAY SO — never rebuild
silently and never guess at lost work.

## 2. Restore the database (a rollback empties SQLite -> stats show 0)
    # from the downloaded backup (zip; the :3000 server denies raw .sqlite3):
    python3 -m zipfile -e /path/to/gabriel-homes-db-backup.zip scripts/stage/ 2>/dev/null \
      || unzip -o /path/to/gabriel-homes-db-backup.zip -d scripts/stage/
    cp scripts/stage/gabriel-homes-db-backup.sqlite3 gabriel_homes/db.sqlite3
    # no backup? reseed from scratch:
    cd /home/z/my-project/gabriel_homes
    .venv/bin/python manage.py migrate && .venv/bin/python manage.py seed_demo

## 3. Python env (if .venv is missing)
    cd /home/z/my-project/gabriel_homes
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    # system python3 has NO django — always .venv/bin/python for manage.py

## 4. Windows wheels (if gabriel_homes/wheels/ is empty — needs network)
    bash /home/z/my-project/scripts/vendor_wheels.sh   # 30 wheels, CPython 3.10-3.13

## 5. Start servers
    bash /home/z/my-project/scripts/start-servers.sh   # :3011 + :3000, idempotent

## 6. Verify before working
    cd /home/z/my-project/gabriel_homes
    .venv/bin/python manage.py check && .venv/bin/python -m pytest -q
    curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3011/
    curl -s -o /dev/null -w '%{http_code}\n' \
      http://127.0.0.1:3000/scripts/preview_site/index.html

## 7. Rebuild the delivery zip (when the user asks for a new one)
    cd /home/z/my-project
    UPDATE_TAG=r6 bash scripts/build_update_zip.sh
    bash scripts/sync_preview_files.sh     # CRLF-enforced, byte-verified

## 8. Session end (EVERY session)
    bash /home/z/my-project/scripts/make_bundle.sh
    # then tell the user to download gabriel-homes.bundle (+ db backup)
    # from the :3000 page — that copy survives any rollback.
