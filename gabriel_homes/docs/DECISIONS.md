# DECISIONS — Gabriel Homes

Append-only log. Every new dependency, every deviation from docs/PLAN.md, every
recorded exception gets one entry here. Format: date · task ID · decision · reason.

---
2026-10-08 · F3/D1 · Pulled task D1 (PostgreSQL driver) forward before F3's first green run · The gate's G-DEPLOY stage (per PLAN §5 F3 step 4) runs `check --deploy` with `DATABASE_URL=postgres://...`; base.py then imports `django.contrib.postgres`, which requires psycopg at app-load time. Without a driver the gate cannot run as specified.
2026-10-08 · D1 · Added `psycopg[binary]==3.2.13` to requirements.txt · Python 3.12 wheels; chose the mature 3.2 LTS-style line over 3.3.x for launch stability (3.2.13 is the latest 3.2 patch on PyPI at time of writing). Django 5.1's postgres backend prefers psycopg 3.
---
