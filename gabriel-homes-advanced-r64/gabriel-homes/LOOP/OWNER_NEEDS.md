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
| L1 (r19) | Eyeball the restructured home + new footer rows on a phone (H1 D6 was desktop-verified only; mobile E3 covered the bento rail) | Non-blocking | Owner phone; screenshots in download/preview-screenshots/ | Desktop renders verified E3 (r18/r19) |
| L2 (r22) | Re-eyeball the mobile home on your phone after r24 — your "looks horrendous" 390px screenshot drove the H2.a fixes (stats row removed, stray scroll pill gone, marquee edge fade, search-card radius/segment) | Non-blocking | Fresh r24 build; before/after in download/preview-screenshots/ + LOOP/audit-screens/r24-e3-mobile-hero.png | Desktop + 390px E3 verified (r24, 15/15) |
| L3 (r23) | Eyeball the map on your phone: the r26 recoloured basemap (sand water / paper land / cream roads / taupe labels — D-LOOP-26b), pin tap → row flash, Map pill return (L1/L2 D6 were desktop-E3 only; touch has no hover — pin tap is the primary path) | Non-blocking | Owner phone; r23-e3-l1-*.png + r26-e3-l2-map-region.png in LOOP/audit-screens/ | Desktop E3 15/15 (r23) + 7/7 (r26) with live tiles |
| L4 (r28) | Eyeball on tablet/phone: the nav now shows the full menu from 1024px (was 1200px — G1) and hides on scroll-down / returns on scroll-up; results rows now lead with a WhatsApp pill (icon), Call/Email outlines, quiet View link (L3) | Non-blocking | Owner device; r28-g1-header-*.png + r28-l3-row.png in LOOP/audit-screens/ | Desktop E3 verified (r28: G1 10/10 incl. JS-blocked + fx=none; L3 row smoke clean) |
