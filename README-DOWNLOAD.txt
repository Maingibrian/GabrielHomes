GABRIEL HOMES - WORKSPACE DOWNLOAD
Generated: 2026-10-09 (UTC)

WHAT'S INSIDE
==============
gabriel_homes/          The complete Django real-estate website project
                        (apps, templates, static assets, docs, tests, scripts)
scripts/launcher/       One-click start/stop launchers for Mac, Linux & Windows

QUICK START (local run)
=======================
1. Open a terminal in this folder.

2. Create a virtual environment and install dependencies:

   Python 3.11+ required.

   Mac / Linux:
     cd gabriel_homes
     python3 -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     python manage.py migrate
     python manage.py seed_demo        (optional: loads demo listings)
     python manage.py runserver

   Windows:
     cd gabriel_homes
     python -m venv .venv
     .venv\Scripts\activate
     pip install -r requirements.txt
     python manage.py migrate
     python manage.py seed_demo
     python manage.py runserver

3. Open http://127.0.0.1:8000/ in your browser.

   Admin:  http://127.0.0.1:8000/admin/
   Create an agent account:  python manage.py setup_accounts  (see gabriel_homes/scripts/)

ONE-CLICK LAUNCHERS
===================
scripts/launcher/START-GABRIEL-HOMES.sh   (Mac / Linux)
scripts/launcher/START-GABRIEL-HOMES.bat  (Windows)
scripts/launcher/RUN-ME-FIRST.txt         (read this first)

DOCUMENTATION
=============
gabriel_homes/DEPLOY.md        Deployment guide (production)
gabriel_homes/DESIGN.md        Design system reference
gabriel_homes/docs/STATUS.md   Current project status
gabriel_homes/docs/PLAN.md     Build plan / roadmap
gabriel_homes/Makefile         Common commands (make test, make gate, ...)

NOTES
=====
- No virtualenv, cache files, or local database are included - the project
  is a clean source tree, ready to run.
- Copy .env.example to .env and fill in values before production deployment.
