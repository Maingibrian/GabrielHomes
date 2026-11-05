# LOOP/STATE.md — Gabriel Homes agent loop state

- **Run number:** 14
- **Run type:** Owner-directed merge + map completion — the owner's Codex tree
  (their newest working state, uploaded as gabriel-homes-latest.part01-08.rar)
  adopted as the base, the r12 hardening ported into it, and the detail map
  finished on the owner's tile provider (OpenFreeMap)
- **Timestamp:** 2026-11-01 ~13:00 +03:00 (session tz Africa/Nairobi)
- **Workspace:** /home/z/my-project/upload/gabriel-codex-latest/gabriel-homes-latest/

## Baseline + end-of-run gates (real results)
| Gate | Start of run | End of run |
|---|---|---|
| `python manage.py check` | OK — 0 issues | OK — 0 issues |
| `python manage.py makemigrations --check --dry-run` | OK — no changes | OK — no changes |
| `pytest -q` | 490 collected: **482 passed, 8 failed** (4 stale tests the Codex tree left behind after its own detail-map switchover + 4 prod-settings tests that only needed psycopg/gunicorn added to this sandbox's venv) | **518 passed** |

## Slice done this run
**r14 — both maps on OpenFreeMap, the r12 hardening landed in the owner's tree, records straightened:**
1. **The owner's Codex lineage adopted as the shipped base.** Their tree already
   carried the OpenFreeMap switchover on /properties/ (self-hosted MapLibre GL
   6.16 ESM in static/vendor/maplibre-gl/, positron style, price pins, popups,
   duplicate-pin spread, CSP widened for tiles.openfreemap.org) plus newer data
   work the r12/r13 tree never had: the lead Nyali gallery + video in the seed,
   demo nearby-amenities on the detail page, and the freshest dev DB. All kept.
   The r13 Leaflet-bridge implementation from the parallel tree is superseded —
   one renderer, one vendoring approach, and the detail map can share it.
2. **Detail map finished.** The Codex tree shipped an OpenStreetMap *iframe*
   embed plus an orphaned MapLibre detail-map.js (its target element was the
   iframe, and the script wasn't even loaded — an empty `{% if %}` stub marked
   where its tag had been). The page now renders the same GL stack as the
   search map: `div#detail-map` + data attrs, marker + popup, graceful
   could-not-load fallback, MapLibre css/js wired, Leaflet control CSS
   replaced by MapLibre theming, `_openstreetmap_embed_url` +
   `map_embed_url` deleted — and with the iframe gone, CSP drops `frame-src`
   entirely (we frame nothing and nobody frames us).
3. **"Show all homes" reset restored** on the search map (lost in the Codex
   rewrite): a pill over the tiles re-fits the map to every pin; shown only
   when more than one home is on the map.
4. **r12 hardening ported (11 files):** BrandSettings Mombasa-first defaults +
   the core.0006 exact-match healing migration; footer "Talk to us" column;
   home Talk-to-us band (gated on the brand row); "How buying works" moved to
   /services/; the bento saturate(0) pass dropped (photos rest in colour);
   bento-shift comment; and the four r12 test files
   (test_phase2_home, three-state harness, test_market_filters,
   test_short_stay_model).
5. **Vendoring hygiene:** sourceMappingURL comments stripped from
   maplibre-gl.mjs + maplibre-gl-worker.mjs (the G-STATIC lesson — they
   pointed at unshipped .map files).
6. **Tests:** 4 stale tests updated to the shipped reality (checked-badge class
   `detail-intro__checked`; CSP tile-host set is OpenFreeMap-only; detail-map
   JS contract positron; detail page MapLibre self-hosted) and a NEW
   test_search_map_layer.py (6) adapted to the ESM wiring.

## Dev DB (shipped)
core.0006 applied to the owner's dev DB — healing verified live: hero_tag,
about_heading, hero_subtitle and footer_lead refreshed to the Mombasa-first
copy (exact-match only; nothing the owner had edited would have been touched).
The brand channel fields are empty in this DB, so the Talk-to-us band and
footer column stay hidden until the owner fills them in /manage/ — verified
rendering live with temporary values, then reverted to empty.

## Visual smoke (runserver, dev DB — `LOOP/audit-screens/run14-*.png`)
- `run14-home-1280.png` / `run14-home-social-390.png`: 7 bento cards resting
  IN COLOUR (computed filter: none), Talk-to-us band with 3 channel links,
  RECOMMENDED IN MOMBASA + nearby band close the listings flow, DEMO chips on
  fallback rows, no #process section, no founding FAQ, footer Talk-to-us
  column; healed hero/footer copy live.
- `run14-properties-map-1280.png` / `run14-properties-popup-1280.png` /
  `run14-properties-bnb-390.png`: 1 MapLibre canvas, 8 price pins (3 rent /
  2 BnB / 3 sale), reset pill visible, popup opens on pin click ("FOR SALE ·
  3BR Home near Haller Park, Bamburi · KES 15,800,000"), mobile ?market=bnb
  view h1 + 2 BnB pins + 2 rows. Paint proven by pixels: 2,299 distinct
  colours in the map region (the empty state is a single flat #e7e4df).
- `run14-detail-map-1280.png`: `div#detail-map` (no iframe anywhere on the
  page), 1 canvas + 1 marker, popup "Nyali Centre — approximate location",
  4 nearby amenities, OpenStreetMap outbound link; 1,091 distinct colours in
  the map region.
- `run14-services-process-1280.png`: #process section with the 4 steps + fee
  note, moved from the home page.
- Zero console messages and zero page errors on every view.

## Decisions
- Full r14 decision log: docs/DECISIONS.md → "Loop 14". Highlights: the
  owner's Codex map implementation over the r13 Leaflet-bridge one; GL over
  the iframe embed for the detail map (one stack, one CSP host, no external
  frame dependency); SRI deliberately NOT pinned on the vendored ESM module —
  dynamic import() bypasses SRI, so a hash would be theatre; the vendoring
  hygiene test is the real guard.

## Next slice
**Run 15 = P2-3** — `SiteContent` typed model + code-defaults registry +
idempotent data migration (backlog order unchanged; owner slices keep taking
the next number). The QA cadence run shifts to run 17.
