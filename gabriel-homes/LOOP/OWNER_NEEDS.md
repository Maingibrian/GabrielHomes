# LOOP/OWNER_NEEDS.md — kept SHORT (protocol §7)

Filter before adding: can the portal collect it? can a safe default cover it? can it be derived from the DB? If yes → build it, don't list it.

## Section A — Needs from Brian (max 10, blocking first)

| ID | What | Why | Blocking? | Where to supply | Until then, the site… |
|---|---|---|---|---|---|
| A1 | Production hosting + domain/DNS | Site currently runs local-only (one-click launcher / dev server) | **Blocking launch** | DNS panel + server access per DEPLOY.md | Runs locally; demo data hidden switch available |
| A2 | SMTP credentials (provider, user, pass, from-domain) | Enquiry emails, newsletter, password reset | **Blocking launch** | `.env` EMAIL_* vars (never in code) | Console backend; enquiries land in dashboard inbox only |
| A3 | Owner's real phone + WhatsApp number to publish | No contact channel is shown today (honest blank by design) | **Blocking launch** | Portal Brand & contact editor (P3-8) once built; interim: tell Brian | Contact page shows enquiry form; no call/WhatsApp buttons |
| A4 | Real listings + owner-owned photos | All 80 listings are fictional seed data | **Blocking launch** | Portal listing wizard / CSV import | Demo mode stays hidden; empty states are designed |
| A5 | Legal review of Privacy & Terms (Kenya DPA 2019) | Compliance; not something code can decide | Blocking go-live decision | Lawyer review of /privacy/ + /terms/ | Pages live with careful wording, no claims of certification |
| A6 | Analytics + Search Console property IDs | Needs the owner's Google account | Non-blocking | Portal SEO editor (P3-11) | Fields empty; zero tracking shipped |
| A7 | Final logo / favicon artwork | Current identity is a text wordmark + simple mark | Non-blocking | Portal Brand editor (P3-8) | Text wordmark "Gabriel Homes" renders fine |
| A8 | Buyer-fee payment method (e.g. M-Pesa paybill) | Site says buyers pay a fee; collection is undefined | Non-blocking (v1 "Later" per BRIEF) | Owner decision; Daraja = Later phase | Copy states fee is disclosed before commitment; no online payment |

Open: **8** · Resolved this run: 0

## Section B — Client fills in via the portal (mirror of Setup Checklist; reference only until P2-2/P3-8 ship)
- Brand: logo, favicon, phone, WhatsApp, email, address, office hours, socials, map pin
- Confirm founder name spelling (site currently "Gabriel Omulu"; Framer reference said "Gabriel Omullu")
- Hero image or video choice; homepage section order; featured-listing picks
- Story / values / philosophy / FAQ copy review (all become editable fields in P2)
- Real listings via wizard or CSV; photos with alt text
- Testimonials (each with written consent flag) — hidden while none exist
- SEO defaults: per-page titles/descriptions, share image
- Which of A1–A8 remain open (checklist mirrors them)

## Section C — Decisions with a default (if no answer after 3 runs, apply default and log under Assumptions in BRIEF.md)
| ID | Question | Recommended default | Deadline run |
|---|---|---|---|
| ~~C1~~ | Replace "Verified" badges/claims with "Checked" (only when owner flagged the listing checked)? | **Yes** | **RESOLVED run 4** — default applied (runs 2–3; logged in BRIEF Assumptions) |
| ~~C2~~ | Redirect /agents/* → /about/ (remove agency concept from public UI)? | **Yes** | **RESOLVED run 4** — default accepted; implementation = P1-1 (next slice) |
| ~~C3~~ | Founder name spelling: "Gabriel Omulu" (current site) vs "Gabriel Omullu" (Framer reference)? | Keep site spelling; make it an editable field | **RESOLVED run 6** — default applied: site keeps "Gabriel Omulu"; spelling becomes an owner-editable SiteContent field at P2-6 (logged in BRIEF Assumptions) |
| ~~C4~~ | Add DB-driven "Latest checked listings" + "Areas we serve" sections to home? | **Yes** (hide cleanly at zero) | **RESOLVED run 6** — default accepted; implementation = P4-4 (queued in BACKLOG) |
| ~~C5~~ | Should the enquiry auto-reply email exist, and in which tone? | Simple acknowledgment, plain language | **RESOLVED run 7** — default accepted; implementation = P3-6 (enquiries inbox; needs A2 SMTP to actually send) |
