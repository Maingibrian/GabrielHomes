# SCHEDULED TASK RUNBOOK — Gabriel Homes: Framer-Grade Design Loop

This file is the verbatim master prompt for the scheduled runs (placed by the session
owner on 2026-11-05). It is the authoritative protocol. If this file is missing, a
fallback copy lives at /home/z/my-project/RUNBOOK-gabriel-homes-design-loop.md.

## Environment (prepared and verified green at session start, 2026-11-05)

- Project tree: /home/z/my-project/gabriel-homes/ (Django project). If it is missing,
  re-extract: cd /home/z/my-project && unzip -q -o upload/gabriel-homes-mombasa-v6-slim.zip
- Python env: /home/z/my-project/.venv (Python 3.12, requirements.txt installed).
  If broken, recreate: python3 -m venv /home/z/my-project/.venv &&
  /home/z/my-project/.venv/bin/pip install -r /home/z/my-project/gabriel-homes/requirements.txt
- Gates (run from /home/z/my-project/gabriel-homes):
  /home/z/my-project/.venv/bin/python manage.py check
  /home/z/my-project/.venv/bin/python manage.py makemigrations --check --dry-run
  /home/z/my-project/.venv/bin/python -m pytest -q
- Verified baseline at session start: check green, makemigrations green, 518 passed.
- All LOOP/, docs/, apps/ paths below are relative to /home/z/my-project/gabriel-homes/.

---

# TASK

You are ONE run in a team of scheduled runs working the same project tree. Continue run numbering from LOOP/STATE.md (the last run was r13). You never work alone: other runs read what you write, so write for a stranger who has no memory of you. Goal: lift the site from "well-made template" to Framer-grade craft, measured against a written rubric, without inventing facts.

========== 0. NON-NEGOTIABLES (BRIEF.md plus the r12/r13 lessons) ==========
- Never use Framer's runtime or copy buyrentkenya.com text, images or markup. Rebuild patterns in Django templates, CSS and small vanilla JS.
- No invented data. Demo data stays labelled. Do not claim anything was tested or seen if it was not; record gate results exactly as they came out.
- Only tokens.css values. A new colour, font, radius or size needs a DECISIONS entry.
- CSP stays strict (script-src 'self'). Any new vendored library must be self-hosted, have a pinned SRI hash in the template, have no sourceMappingURL comments (the r13 MissingFileError lesson), and be covered by a test.
- Every effect must respect prefers-reduced-motion and work with JS blocked (D-MOTION-SAFE pattern: content is visible unless html.motion-ready is set).
- Views stay thin. Do not rename or refactor outside your claimed item without logging why.
- Gates must end green: python manage.py check, makemigrations --check --dry-run, pytest -q. The test count never goes down (baseline 518). Every shipped item adds tests.
- Keep OWNER_NEEDS.md to 5 lines or fewer. Prefer moving an input into the owner portal over asking the owner.

========== 1. THE TEAM'S SHARED FILES (all in LOOP/, create if missing) ==========
- PROTOCOL.md: a condensed copy of sections 2 to 6 of this prompt, so runs without this prompt can still follow the rules.
- RUBRIC.md: the grading rubric (section 4).
- SCORECARD.md: one table row per work item: ID, item, weight 1-5, needs (dependencies), target tier, status, scores (self and auditor, per dimension), evidence tier, attempts, last-touched run, one-line next step.
- LOCKS.md: who is working on what right now (section 3).
- JOURNAL.md: append-only, newest first. One entry per run in this fixed shape:
  Run N | ROLE | timestamp | items | score before to after (self) | evidence tier | gates (real results) | decisions | FOR THE NEXT RUN (one imperative line) | blockers
- NOTES/<ID>.md: deep notes, created only when an item has 2 or more failed attempts or a non-obvious decision. Cover root cause, what was tried, and what to try next.
- Existing files stay in use: STATE.md (overwrite a snapshot of 40 lines or fewer each run), BACKLOG.md, OWNER_NEEDS.md, docs/DECISIONS.md.
- docs/DESIGN-ADDENDUM.md: the motion vocabulary and section archetypes (item F4).
Docs are part of done: an item cannot reach READY-FOR-AUDIT until its SCORECARD row, JOURNAL entry and any DECISIONS entry exist.

========== 2. START OF EVERY RUN (in this order) ==========
1. Read PROTOCOL.md, STATE.md, SCORECARD.md, LOCKS.md, the last 5 JOURNAL entries, and any NOTES for items you might take.
2. Run the baseline gates and record the real results. If they are red, your role is REPAIR (fix that first, nothing else).
3. Read the previous run's "FOR THE NEXT RUN" line. Do it unless it is already locked.
4. Choose a role (section 3), claim your item in LOCKS.md, then work.

========== 3. ROLES AND LOCKS ==========
Pick the first role that applies:
a) REPAIR: gates were red at start.
b) PLANNER: SCORECARD.md does not exist (run 1 is PLAN-ONLY, no code), or the run number is a multiple of 5 (retrospective). A retrospective reads the last 5 journal entries, re-weights items, splits stuck items, adds newly found items, prunes duplicates, and logs the reasoning.
c) AUDITOR: any item is READY-FOR-AUDIT and was not built by you. Re-run the gates, re-read the code, and grade from scratch without looking at the builder's scores first. Record both scores. The lower score wins. Promote to MET-T1/MET-T2 or demote to TODO/WIP with the exact failing checks named. Max 3 audits per run.
d) BUILDER: otherwise. Take the highest-priority unblocked item (section 5). A builder can only move an item to READY-FOR-AUDIT, never to MET.
e) WATCH: runs after every retrospective. Re-verify the gates, spot-check about 20% of MET items (pick them by run number so it is deterministic), and check token drift with the F1 test. Any failure sets the item to REGRESSED.
LOCKS: before editing, append "ITEM | run-id | claimed-at | expires-at (claim plus 45 min)" and re-read the file. If another live lock covers the same item or the same file, pick a different item. Release your lock at the end. Hotspot files (home.html, home.css, search.css, motion.js, base.html): re-read the file right before editing, keep edits small, and never rewrite a whole hotspot file.

========== 4. SELF-GRADING ==========
Score 0-4 per dimension: 0 absent, 1 broken or partial, 2 works but generic or has gaps, 3 meets the benchmark (Tier 1), 4 exemplary (Tier 2).
Dimensions: D1 brief and token fidelity, D2 visual craft, D3 motion (purposeful, restrained), D4 performance, D5 accessibility, D6 mobile, D7 resilience (works with JS blocked or fx=none), D8 tests and docs.
Evidence tiers: E1 read the code, E2 test, gate or measurement, E3 rendered (screenshot or real browser).
- A score with no evidence is capped at 2.
- D2, D3 and D6 without E3 are capped at 3 and tagged "visual-unverified". Such items can still reach MET-T1, but they are batched into ONE OWNER_NEEDS line ("Please eyeball these pages on your phone: ...").
- MET-T1 means: every applicable dimension is 3 or higher, every binary check passes, gates are green, and a DIFFERENT run audited it. MET-T2 means the same at 4 for the applicable dimensions.
- Nobody may change the rubric to raise a score. Rubric changes need a DECISIONS entry.
Statuses: TODO, WIP, READY-FOR-AUDIT, MET-T1, MET-T2, REGRESSED, BLOCKED.

========== 5. PRIORITY AND ATTENTION ESCALATION ==========
priority = weight x (target score - current score) x (1 + 0.5 x failed_attempts) + 1 for every 3 runs untouched. REGRESSED items count double. Skip items whose "needs" are not MET-T1 or READY-FOR-AUDIT.
- MET items are FROZEN. Edit them only to fix a regression.
- A failed attempt (audit demotes, or gates go red) means attempts + 1 and a NOTES/<ID>.md root-cause note. The next builder must read it and try a different approach.
- At 3 attempts, decompose into sub-items (ID.a, ID.b) with narrower checks. At 5 attempts, mark BLOCKED with the exact need and add at most one line to OWNER_NEEDS.
- As the MET share rises, runs concentrate on what is left: once MET-T1 share is at least 50%, a builder takes ONE remaining item deeply instead of several lightly, and checks neighbouring MET items for conflicts.
- When every item is MET-T1, the Planner raises the top-weight items to Tier 2 and logs it. When every item is MET-T2 or BLOCKED, the project is in STEADY STATE: only WATCH runs do work, and every other run writes a one-line journal entry "steady state: nothing to do" and stops. Do not churn.

========== 6. SEED WORK ITEMS (the PLANNER turns each into SCORECARD rows with binary checks and the proving test) ==========
Findings behind the items: the home page has 12 sections and repeats the "five checks" message in 5 of them; "Talk to us" breaks the owner's order; bento-shift.js only runs on hover pointers wider than 1020px, so phones get nothing; search.css uses undefined var(--font-body) and var(--paper), which probably breaks the map price-pin font; tokens say 13px is the text floor but 9-12px is used in places; about 90 hard-coded hex values in home.css and search.css; static/video/hero-loop.mp4 (1.5MB) is unused; stock photos are up to 676KB; "smooth scroll" is only scrollIntoView; the nav collapses below 1200px; the liberty map style clashes with the palette; listing rows are about 430px tall and the three action buttons carry equal weight.

ID  Item (weight) [needs]: key binary checks
F1  Token integrity (5): pytest fails on any var(--x) with no definition and no fallback; fix --font-body to --font-sans and define --paper; font-size under 13px only via an allowlist; the hard-coded hex count outside tokens.css is recorded as a baseline and may only go down (a ratchet).
F2  Capability gate (5): one tiny script sets html[data-fx] to rich, lite or none from reduced-motion, Save-Data and pointer/hover (r58: hardware proxies removed — they demoted the owner's 4-core machine and killed the bento animation). Every effect keys off it. none behaves like today's reduced-motion. Test: no effect runs under none.
F3  Image and video diet (4): no static image over 250KB; WebP/AVIF with srcset where practical (Pillow script); width/height always set; hero-loop.mp4 loads only under fx=rich and not Save-Data, with a poster.
F4  Motion vocabulary (4): docs/DESIGN-ADDENDUM.md names 6 effects or fewer (mask-reveal, clip-reveal, parallax, spotlight-shift, cursor-view, magnetic) with purpose, where used, tier, and "max 2 at once per viewport". Every shipped effect maps to an entry. Rule: if an effect does not orient, confirm or earn its keep, cut it.
F5  Smooth scroll (3) [F2]: self-hosted Lenis vendored under the hygiene rules; fx=rich only; off for touch; anchors, find-in-page, focus and keyboard scrolling still work; replaces the scrollIntoView hack.
H1  Home order and diet (5): order exactly hero, bento (colour, shift kept), recommended (about 2 sale, rent, to let; short description plus WhatsApp/phone/email), nearby; 7 or fewer top-level sections; the trust message appears in 2 places or fewer; About/Services/Commitments/FAQ/Browse/Newsletter content is MOVED to its page or the footer, not deleted; a test asserts the section id order.
H2  Hero (5) [F2,F3]: one gesture; video under fx=rich else slide 1; split-text mask headline; frosted floating search pill keeping the Buy/Rent segment; stats row removed or limited to facts from brand settings (no "Kenya" filler); LCP image preloaded.
H3  Mobile bento (5) [F2]: under 1021px or on touch, a horizontal scroll-snap carousel with the centred card scaled up; swipe and keyboard work; scrolls without JS; the desktop shape-shift and its tests stay untouched.
H4  Section rhythm (3) [H1]: at least 3 distinct section archetypes (full-bleed, type-led, edge strip) documented in the addendum and used; never more than 2 neighbours share one.
G1  Floating pill nav (4) [F2]: hides on scroll-down and returns on scroll-up (fx lite or rich); full nav from 1024px up; mobile-menu inline styles moved to CSS; Escape closes; skip link.
G2  Shared-element page transitions (5) [F2]: @view-transition { navigation: auto } under @supports; a unique per-listing view-transition-name on the card/row image and the detail hero; off under fx=none; HTMX pagination unaffected; a test asserts the names are present and unique.
G3  Scroll-linked effects (3) [F2,F4]: CSS animation-timeline: view() behind @supports for parallax and clip-path reveals on collage, services and nearby; falls back to the existing IntersectionObserver reveal; no layout shift.
G4  Pointer polish (2) [F2,F4]: cursor "View" bubble on listing rows and cards, plus magnetic primary CTAs; fx=rich and fine pointer only; hidden for keyboard users; carries no information that exists only on hover.
L1  Map and list sync (5): keep the owner's layout (map on top, three filter cards, alternating rows); add two-way highlight (row hover highlights the pin, pin click scrolls to and flashes its row); keyboard operable; aria-live result count; a floating "Map" pill returns to the map.
L2  Basemap palette (4): after the style loads, recolour land, water, roads and labels to tokens through getMaplibreMap().setPaintProperty with a guarded layer list that skips missing ids; the SVG fallback and the single attribution copy are unchanged; the pin font is fixed; the r13 map tests stay green.
L3  Row conversion and density (4): WhatsApp is the primary action (icon), Call and Email secondary, using the existing brand-channel logic; row min-height 320px or less on desktop; description 28 words or fewer; alternating sides kept; stacks on mobile.
L4  Detail gallery (3) [G2]: read detail-gallery.js first; add swipe, a lightbox with focus trap and keyboard control, and the shared-element transition.
Cross-cutting, graded by WATCH and enforced on every item: Q1 performance budget (home first-view CSS+JS+fonts+LCP image 400KB or less, all new JS deferred, CLS 0; measurement method recorded); Q2 accessibility (reduced-motion parity test for every effect, 4.5:1 contrast on new text, visible focus, carousel and map keyboard operable); Q3 resilience (all content visible with JS blocked and under fx=none); Q4 docs (PROTOCOL matches practice, addendum current, DECISIONS entries made).

========== 7. END OF EVERY RUN ==========
1. Re-run all gates. If red and you cannot fix it quickly, REVERT your own change, log it, and count a failed attempt. Never leave the tree red.
2. Update SCORECARD, JOURNAL (with a clear FOR THE NEXT RUN line), STATE (snapshot), DECISIONS, and OWNER_NEEDS (5 lines or fewer, batched).
3. Release your lock.
4. Final message, 8 lines or fewer: role, item(s), score movement, real gate results, MET-T1 count out of total, what the next run should do.

Time-box: about 25 minutes. One deep item, or up to 3 trivial ones. Stop when the box is up. Do not start work you cannot finish and document.
