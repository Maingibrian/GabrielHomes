Gabriel Homes — Run 71 data package (movement smoothness audit)
=================================================================
Exported 2026-11-11 (run 72) after the owner asked to "push the data
from the last run". No cloud remote is configured yet, so this zip is
the portable copy; the same content is also committed to the local git
repo (repo root: /home/z/my-project).

Contents
--------
r71-listings-smooth-verified.png
    Final live screenshot of /properties/ in the shipped state: palm
    drift ratio 0.497x over a 1997px scroll, transform:none on the
    palm ::before, dark footer intact past the band end, no console
    errors (agent-browser, settled readings).
r71-listings-compositor-drift.png
    Evidence shot from the compositor experiment that was built,
    proven pixel-identical, then REJECTED (Chrome hoists the
    root-negative composited layer over the site footer + mask edge
    leaks). Kept as the record of why transform-based parallax is
    banned for the palm field.
r70-listings-after-fix.png
    Screenshot after the r70 fix (frame-rate-independent easing:
    k = 1 - exp(-dt/TAU), TAU=70ms) that ended the "drops down and
    up" glitch.
scripts/r70_analyze_trace.py
scripts/r70_analyze_after.py
    The per-frame trace analysers used to diagnose r70 (frame pacing,
    stop-scroll t95 convergence, palms/scroll ratio). The raw
    /tmp/trace*.csv files did not survive the sandbox recycle; these
    scripts regenerate them on demand.
LOOP/JOURNAL.md
    Full run log including the complete Run 70 and Run 71 entries
    (diagnosis, fix, gates, evidence, and the pinned ban on
    transform-based palm parallax).

Shipped mechanism (r70/r71 final)
---------------------------------
static/js/motion.js  setupPalmParallax: time-constant chase writes
    --palms-y (in-frame measure, dt clamped 400ms, snap 0.25px).
static/css/search.css ::before: background-position 0 var(--palms-y)
    (translate3d/will-change/mask-* on this pseudo-element are banned
    by test_parallax_compositor_transform_is_banned).
templates/listings/_results_grid.html: row images decode async with
    width/height reserved boxes.

Gates at export: manage.py check 0 issues, makemigrations clean,
pytest 881 passed, preview live (80 listings, gateway 200).
