# Spec — owner-portal desktop dashboard (r91)

## Goal
The owner portal looks simplistic on desktop because `manage.css:79` caps every
screen at `max-width: 44rem` — a 704px centered column on a 1920px display — and
the shell is a mobile-style topbar + chip nav. `DESIGN.md` §9 mandates "agent
dashboard (cream background, espresso sidebar)" and was never built. Rebuild the
portal shell and home screen as a real desktop dashboard while keeping the
existing mobile layout and every pinned test green.

## Scope
**Change:**
- `templates/manage/base.html` — add the sidebar shell (desktop) alongside the
  existing topbar + chip nav (kept for <64rem); nav links via one shared partial
  so the sidebar and chip nav can never drift apart.
- `templates/manage/home.html` — restructure into a desktop dashboard grid:
  header row, KPI strip (4 tiles + micro-sparkline), 30-day chart + enquiry
  pipeline, recent enquiries + most-viewed, checklist + quick actions.
- `static/css/manage.css` — sidebar, dashboard grid, richer KPI/chart/pipeline
  styling; widen `.manage-main` content column on desktop; all rules scoped to
  the new classes or behind `min-width: 64rem`.
- `apps/manage/tests/test_r91_desktop_dashboard.py` — NEW: pins the shell
  (sidebar + both navs in the DOM), the dashboard grid structure, and that the
  mobile nav still renders.

**Do NOT change:** any view/URL/model logic, `stats.py` data shapes (pinned by
test_dashboard_graphs.py), the four-file stylesheet list (pinned by
test_portal_design_stack.py), migrations, settings, public-site templates.

## Design decisions (from the audit)
- Breakpoint 64rem (1024px): sidebar + dashboard grid above; current stack below.
- Sidebar = espresso, numbered nav items (01–05, DESIGN.md §2b), brand mark at
  top, account links (Password / Studio / Sign out) pinned at the bottom.
- Home grid at ≥64rem: 12-col; chart spans 8, pipeline 4; recent 7, top-viewed 5;
  checklist 7, quick actions 5. Same DOM order on mobile (single column).
- KPI tiles gain a micro-sparkline (CSS bars from `stats.per_day`, no JS) and a
  context line ("in the last 30 days" / "across live listings").
- All colors/fonts/radii from existing tokens only (design-stack test scans for
  bare `var()` reads); no new CSS file; no JS added (CSP stays strict).
- Template comments: `{% comment %}` blocks only — never multi-line `{# #}`
  (comment-leak guard sweeps every portal page).

## Acceptance criteria (binary)
1. ≥64rem viewport: portal renders an espresso sidebar with all five sections,
   numbered, current section highlighted; account tools at its foot.
2. ≥64rem viewport: `/manage/` is a multi-zone dashboard grid (KPI strip,
   chart+pipeline, recent+top-viewed, checklist+quick-actions) wider than 704px.
3. <64rem viewport: layout is byte-equivalent in structure to today (topbar +
   chip nav + single column; no sidebar visible).
4. `manage.py check` → 0 issues; full suite green (1102 + new tests).
5. Design-stack test still passes: stylesheet list unchanged, no missing tokens.
6. No JS added; no dependencies added; no migrations; `git status` shows only
   the four files above.
7. Visual check: rendered desktop screenshot shows sidebar + grid, no blank
   zones, no overlapping text; mobile screenshot unchanged shape.

## Plan (planning-loop output — ordered, binary checks)
1. `templates/manage/_nav.html` NEW partial: the five section links, one source
   for both variants; `variant="sidebar"` adds `01–05` index numbers; badge +
   `is-current` logic identical to today. Check: base.html includes it twice.
2. `templates/manage/base.html`: add `<aside class="manage-side">` (brand, nav
   partial with variant=sidebar, account tools, sign-out) BEFORE the existing
   topbar; keep topbar + chip nav markup unchanged (mobile). Check: chip nav
   still in DOM; sidebar in DOM; no `<script>` added.
3. `templates/manage/home.html`: wrap in `manage-board`; KPI strip
   (`manage-kpis` > 4 `manage-kpi` + hint lines + `manage-spark` on the
   enquiries tile); zones: `--chart`(8) `--pipe`(4) `--recent`(7) `--top`(5)
   `--check`(7) `--actions`(5); inner chart/hbar/rows/checklist markup reused.
   Check: all existing data bindings (`counts.*`, `stats.*`, `checklist.*`)
   unchanged.
4. `static/css/manage.css` append r91 section: mobile-first `.manage-side
   { display:none }`; `@media (min-width: 64rem)` body grid `16.5rem 1fr`,
   sidebar sticky 100vh, topbar+chip-nav hidden, main column widened (60rem
   for non-board children, board full-width); board 12-col grid; KPI/spark/
   zone polish — tokens only, every bare `var()` must exist. Check:
   design-stack token test green.
5. `apps/manage/tests/test_r91_desktop_dashboard.py` NEW: sidebar+chip nav in
   DOM, five sections + indexes, board structure, CSS 64rem rules present +
   `.manage-side` hidden by default, no `<script>` in base/home.
6. Verify: `manage.py check` 0 issues; full `pytest -q` green; screenshots
   (1440px + 390px) reviewed; receipts into test-evidence.md; handoff;
   commit + push.

## Done-when
From `gabriel-homes-advanced-r64/gabriel-homes/`:
```
.venv/bin/python manage.py check
.venv/bin/python -m pytest -q 2>&1 | tail -5     # all green
```
plus desktop + mobile screenshots reviewed via the preview, receipts pasted
into `.agents/reports/test-evidence.md` and the AGENTS-COLLAB.md handoff.
