# Gabriel Homes

A Django 5.2 real-estate listings site for Kenyan coastal agencies (Kilifi, Nyali, Mombasa area), with multi-agency listings, image galleries, enquiry flow, and a WhatsApp/Call contact layer.

## What's inside

- **Django 5.2** app (`gabriel_homes/`) — listings, agencies, enquiries, sitemap, admin
- **6 agencies / 80 seeded listings** (`seed_demo` management command) with generated placeholder imagery
- **Vendored Windows wheels** (`gabriel_homes/wheels/`) — offline install on Windows, no internet needed
- **One-click launcher** (`UPDATE-WEBSITE.bat` at the zip root) for non-technical users
- **331 passing tests** (`pytest`) as the change gate

## Quick start (Windows)

1. Download the latest update zip, e.g. `gabriel-homes-update-r7.zip`.
2. Unzip anywhere, double-click `UPDATE-WEBSITE.bat`.
3. Open `http://127.0.0.1:8000` in your browser.

The script creates a virtualenv from the vendored wheels, applies migrations, seeds demo data, and starts the dev server.

## Quick start (macOS / Linux)

```bash
cd gabriel_homes
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver
```

## Repo layout

| Path | Purpose |
|------|---------|
| `gabriel_homes/` | The Django project (apps: `listings`, `core`, …) |
| `gabriel_homes/wheels/` | Vendored wheels for offline Windows install |
| `scripts/` | Build, delivery, watchdog, and audit tooling |
| `scripts/preview_site/` | The delivery page served on port 3000 |
| `REBUILD.md` | Playbook for restoring a wiped/rolled-back sandbox |
| `WORK.md` | Session log + `LAST_COMMIT` rollback fingerprint |

## Tests

```bash
cd gabriel_homes
.venv/bin/python -m pytest -q
```

331 tests must pass before any release zip is built.

## Release zips

Update zips are named `gabriel-homes-update-<TAG>.zip` (dateless, so links never 404 on date drift). Build one with:

```bash
UPDATE_TAG=r8 bash scripts/build_update_zip.sh
bash scripts/sync_preview_files.sh
```
