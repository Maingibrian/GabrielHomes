# OWNER INPUTS — what Brian needs to answer (one page)

Twelve decisions (O1–O12) are the only things standing between the finished
build and go-live. Answer them in any order; each entry says what it unblocks
and what happens if you skip it for now. Nothing here is a code task — replies
in plain email/chat are fine.

## The twelve questions

### O1 — Who owns the photos?
**Plain English:** the site currently uses 240+ demo photos (media/demo-photos/
and media/property-images/). Did you take them, buy them, or license them? If
not, we swap in your own photos before launch.
**Unblocks:** C1 (media archive), C4 (launch checklist), go-live.
**Answer must contain:** the source/license for each pool, or "replace them".
**Safe default:** keep media in the repo, do not publish until O1 is answered.

### O2 — Move unused media out of the repo?
**Plain English:** 847 image files are on disk but no listing uses them. Want
them archived out of the repo (nothing is deleted — moved to a sibling folder)?
**Unblocks:** C1.
**Answer must contain:** yes/no (and a preferred archive location if yes).
**Safe default:** keep everything where it is until launch week.

### O3 — Lawyer review of the privacy + terms pages
**Plain English:** a Kenyan lawyer should check the privacy policy and terms
(Data Protection Act, 2019) before you go live.
**Unblocks:** C4, go-live.
**Answer must contain:** the lawyer's name and the date of review, plus any
edits they want.
**Safe default:** pages stay up marked "under review"; no marketing spend until
signed off.

### O4 — How long do we keep enquiry messages?
**Plain English:** enquiries (name, phone, email, message) sit in the database.
Keep them for 365 days (current default) or another period? Also: who deletes a
person's data if they ask?
**Unblocks:** C3 (retention job).
**Answer must contain:** the number of days + the person responsible for
deletion requests.
**Safe default:** keep the 365-day purge that is already coded and documented.

### O5 — Who watches the site when it's live?
**Plain English:** pick a free uptime checker (e.g. UptimeRobot) pointed at
/healthz/, and say where alerts should land.
**Unblocks:** monitoring step O-a.
**Answer must contain:** the service chosen + the alert email/phone.
**Safe default:** none — this one takes five minutes and needs no money.

### O6 — Email sending (SMTP)
**Plain English:** enquiry emails need a sending account (e.g. Brevo) for
hello@gabrielhomes.co.ke, plus SPF/DKIM records on the domain so mail doesn't
land in spam.
**Unblocks:** S9 email test on staging, go-live.
**Answer must contain:** SMTP host/port/user + password (sent securely), and
whether SPF/DKIM are set.
**Safe default:** enquiries keep saving to the dashboard with email delivery
marked "not configured"; nothing breaks.

### O7 — Server + domain
**Plain English:** which VPS provider and Ubuntu version, and the DNS for
gabrielhomes.co.ke (an A record pointing at the server).
**Unblocks:** R1 (deploy rehearsal), V3 (real load numbers), R3 (sign-off).
**Answer must contain:** provider, Ubuntu LTS version, IP/hostname, and who
manages DNS.
**Safe default:** stay on the preview environment until this lands.

### O8 — Off-site backups
**Plain English:** backups currently gzip locally with 30-day retention. Where
should copies live off the machine (e.g. Backblaze B2 or Amazon S3)?
**Unblocks:** D5 off-site step.
**Answer must contain:** the destination + where its credentials will live.
**Safe default:** local backups only; off-site added the week the VPS exists.

### O9 — Who can create agent accounts?
**Plain English:** the plan assumes only you (admin) create agent logins — no
public sign-up. Confirm.
**Unblocks:** security review sign-off.
**Answer must contain:** yes/no.
**Safe default:** yes — admin-only (as built).

### O10 — Error reporting
**Plain English:** do we start with plain logs only (recommended) or add a
hosted error tracker (e.g. Sentry) from day one?
**Unblocks:** O-a monitoring config.
**Answer must contain:** logs-only or the tracker you want.
**Safe default:** logs only at launch; add a tracker after the first month.

### O11 — Run the PostgreSQL test suite
**Plain English:** dev runs on SQLite; a 5-minute command run on any machine
with PostgreSQL proves the prod database setup. The command is in the next
section — paste the last line back.
**Unblocks:** D2.
**Answer must contain:** the pytest summary line.
**Safe default:** skip until the VPS exists (it has PostgreSQL anyway).

### O12 — One-click launcher on a clean machine
**Plain English:** double-click START-GABRIEL-HOMES on a Windows/Mac machine
that has never seen the project, and confirm the site opens.
**Unblocks:** S4 manual check.
**Answer must contain:** which OS it was tried on + whether the browser opened.
**Safe default:** any second-hand laptop test before go-live week.

## Commands Brian runs himself

**PostgreSQL suite (D2)** — on any machine with PostgreSQL 15+ (and the repo
checked out with its venv built):

```bash
createdb gabriel_test
GABRIEL_TEST_DB_URL=postgres://postgres:postgres@localhost:5432/gabriel_test \
  DJANGO_SETTINGS_MODULE=config.settings.test_pg \
  .venv/bin/python -m pytest -q
```

A pass looks like: a final line such as `298 passed in 40s` (number may drift
up as tests are added) and exit code 0.

**Restore drill (D5)** — after running `make backup-db` once on the same
machine:

```bash
set -a && . ./.env && set +a && ./scripts/restore-drill.sh
```

A pass looks like: the script restores the newest backup into a scratch
database, prints the migration list, drops the scratch database, and exits 0
with no traceback.
