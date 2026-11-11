# BACKEND-PLAN.md — closing the owner-operations gap

**Written run 72/73 (2026-11-11), after the backend completeness audit.**
Status legend: `[x]` shipped · `[~]` this run · `[ ]` planned.

The audit verdict: the visitor-facing backend (models, search, enquiries,
auth, security, deploy story — 881 tests) is production-ready. What is
missing is **owner operations**: everything the owner needs to run the
business day-to-day without a developer. This plan closes that gap in
four phases, in the order that unblocks the owner soonest.

---

## Design rules (apply to every screen — owner's own words: "SIMPLE TO USE … graphs sections … don't look too complex")

1. **Plain language.** "Enquiries", not "CRM objects". "Done", not
   "archived". Every screen answers "what is this and what do I do here"
   in one line at the top.
2. **One primary action per screen.** Secondary actions are links or
   outline buttons (existing portal pattern).
3. **Five sections, one nav** — Home · Enquiries · Listings · Site
   content · SEO. Nothing hidden behind hover or jargon.
4. **Graphs without a chart library.** CSS-only bars from token colors
   (cream/espresso/clay). No new dependencies, no JS, fast on a phone.
   Every graph degrades to a designed empty state ("No enquiries yet —
   they'll appear here when someone contacts you.").
5. **Mobile-first.** The owner uses a phone; tables become stacked
   cards, nav becomes a scrollable chip row.
6. **Honest data.** Demo-seeded rows are badged "Sample" and disappear
   everywhere the moment "hide demo data" is on (same contract as
   listings). No invented numbers in the dashboard.
7. **Every screen is gated** by OwnerRequiredMixin (anon → login,
   others → 403) and noindex.
8. **Test-first contract**: every screen ships with gate tests + data
   tests + plain-language pins. Suite only grows (881 → …).

---

## Phase 1 — Owner Hub core `[~ run 73]`

### 1A. Portal section nav
Topbar keeps brand + sign out; a sticky chip row below it links the five
sections, current section highlighted, "Enquiries" carries a red-dot
badge when there are new enquiries. Scrollable on mobile.

### 1B. Home dashboard with graphs (`/manage/`)
* Quick numbers: New enquiries · Live listings · Drafts · Total listing
  views (all database facts; demo-aware).
* **Graph: enquiries, last 30 days** — one CSS bar per day, hover
  title shows "12 Nov — 2 enquiries", axis labels first day / today.
* **Graph: enquiries by status** — five horizontal bars (New, Seen,
  Contacted, Viewing booked, Done) with counts.
* **Graph: most-viewed listings** — top 5, ranked bars, links to the
  public pages; hidden when all views are zero.
* **Latest enquiries** — 5 newest with status pills, links to detail.
* Setup checklist + quick-action cards (kept from P2-2).

### 1C. Enquiries workflow (`/manage/enquiries/`)
* **Statuses** become a simple pipeline (data-migrated, nothing lost):
  `new → seen → contacted → viewing → done` (`replied` rows become
  `contacted`). Opening an enquiry marks it **seen** automatically.
* **Tabs with counts**: All · New · Seen · Contacted · Viewing · Done ·
  Spam. Rows show who, when, which listing, status pill.
* **Detail screen**: full message, the listing it's about (with public
  link), one-tap status buttons (the five states), and **reply actions
  with prefilled templates** — WhatsApp ("Hi Amina, thanks for your
  enquiry about…"), call, email — built from the enquiry + brand row.
* **Notes**: a timeline of dated notes ("Called back, viewing Saturday
  10am") — one textarea + Add note.
* **CSV export** — one button, all non-spam enquiries, Excel-friendly
  (UTF-8 BOM), filename `gabriel-enquiries-YYYY-MM-DD.csv`.
* **Spam folder**: honeypot rows land here, read-only + one-tap delete.
  Real enquiries can never be deleted from the UI (data first).
* Demo enquiries are badged "Sample" and vanish with the demo switch.

### 1D. Brand assets (`/manage/site-content/` extended)
New "Logo, address & socials" section on the existing editor (same
screen, so there's one place to edit the public site):
`logo` · `favicon` · `address` · `opening hours` · `Instagram` ·
`Facebook` · `X` · `TikTok`. Wired:
* header swaps the SVG mark for the logo image when set (same size);
* favicon link swaps when set (PNG/JPG/WebP, ≤2 MB, validated);
* footer "Talk to us" grows the social channels when filled;
* contact page grows a "Visit" block (address + hours) when filled.
Empty fields = hidden UI (honest blank, existing pattern).

### 1E. SEO & tracking (`/manage/seo/`)
Three fields, plain help text: **Analytics ID** (GA4 `G-…`) ·
**Search Console verification token** · **default site meta
description** (overrides the coded default when filled).
Wired into `base.html`: gtag.js loads only when the ID exists, with a
**per-request CSP nonce** (the strict policy stays strict — no
`unsafe-inline`); Search Console emits the verification meta tag.

### 1F. Simple listings section (`/manage/listings/`)
Read-first list: photo-less rows (title, status pill, price, views,
updated, "Sample" badge) with status chips (All/Live/Draft/Under
offer/Sold/Archived) and **Edit** deep-linking to the existing full
editor + **View** to the public page. The heavy tools land in Phase 2
on this same screen.

---

## Phase 2 — Listing management polish (next run)

* **2A. Duplicate** (one click, "Copy of …", draft status, cover kept).
* **2B. Bulk status** (tick rows → mark Published/Under offer/Sold/Let/
  Archived) + **featured toggle** + **inline price edit**.
* **2C. Map pin picker** — click-to-set on the existing self-hosted
  MapLibre (no new deps), lat/lng never typed by hand again; keeps the
  "approximate pin" privacy note.
* **2D. Wizard + draft autosave** — Basics → Price → Details → Photos →
  Review; each step saves a draft, no lost work on a phone.

## Phase 3 — Content & taxonomy

* **3A. Taxonomy editor** — locations, property types, amenities
  (add / rename / hide; no deletes).
* **3B. Media library** — uploads, alt text, where-used, unused cleanup.
* **3C. Testimonials** — owner-entered, consent flag, hidden when none.
* **3D. Newsletter compose** — pick listings, preview, send to confirmed
  subscribers (model + double opt-in already exist).

## Phase 4 — Trust & housekeeping

* **4A. Activity log** — who changed what (listings, content, enquiries).
* **4B. One-click backup** — DB + media download button in-portal
  (restore drill already exists in DEPLOY.md).
* **4C. Saved-search alerts** — the SavedSearch model gets a UI + optional
  digest email (model exists, unused).
* **4D. Help page in-portal** — the owner-facing guide (P6-2).

**Decided against (logged, revisit only on owner request):** a REST API
(no app to feed — server-rendered is fine), a separate CMS (BrandSettings
+ templates cover it), any JS chart library, any new pip dependency.

---

## Verification per phase

Gates every phase: `manage.py check` 0 · `makemigrations --check` clean ·
full pytest green and growing · live preview screenshots (desktop +
360px) · no console errors · plain-language copy read aloud once.
