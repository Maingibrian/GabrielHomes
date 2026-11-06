# DESIGN-ADDENDUM — motion vocabulary & section archetypes

F4 contract: this document names **at most 6 motion effects**. Every shipped
effect in the codebase maps to one entry below. The keep-alive rule: if an
effect does not orient, confirm, or earn its keep, it gets cut — not added to
this list.

## The stacking rule (max 2 at once per viewport)

At most two entries animate in the same viewport at the same time:

- The hero pairs M2's ambient slide rotation (background slot) with M1's
  entry rise (gesture slot) — that is the only place an ambient effect runs.
- Everywhere else, entries are one-shot (M1 reveals finish before the next
  section enters) or interaction-scoped (M4/M5 animate only while the
  visitor is engaged with the element), so they never stack with each other.
- The capability gate (`html[data-fx]` = rich / lite / none, F2) tiers every
  entry; `none` behaves like `prefers-reduced-motion: reduce` everywhere.

## Vocabulary (6 effects)

| ID | Effect (hooks) | Purpose | Where used | Tier | Reduced-motion / fx=none behaviour |
|---|---|---|---|---|---|
| M1 | **rise** — `hv2-rise` stagger, `data-reveal` IntersectionObserver fade-ups; G3 scroll-linked delivery `g3-rise`/`g3-clip` (nearby cards, services rows+media, about figure — @supports view(), reversible) | Orient: content arrives in reading order, once | Hero tag/title/subtitle/search; section headers, cards, rows (motion.js); scroll-linked surfaces (components.css 12b) | lite + rich (scroll-linked: kill under fx=none/reduced-motion/no-JS) | Content fully visible instantly; `animation: none` kills rise/marquee/cue; reveals fire visible with no transition |
| M2 | **crossfade** — `view-transition` shared-element pair (G2); `hero-fade` + `hero-drift` slide rotation; L4 lightbox open/close fade (`.lightbox.is-open`, JS-built overlay — the G2 name stays on the gallery main, D-LOOP-32a) | Continuity: the listing image carries from grid to detail; the hero stays alive without competing | Listing card/row img → detail hero; `.hero__bg` slide stack (24s); `/listing/` gallery lightbox (detail.css) | lite + rich (view-transition off under none via the CSS `html { view-transition-name: none }` fail-closed rule) | Navigation is an instant swap; hero shows slide 1 static (no rotation, no drift); lightbox opens/closes with no fade |
| M3 | **marquee** — `hv2-marquee` track + edge fade mask + hover pause | Confirm: the five checks stay present without a trust-badges wall | `#checks` strip on home | lite + rich | Track static (`animation: none`); edge mask survives (it is a fade, not motion); full text still readable |
| M4 | **spotlight** — `bento-shift` desktop hover morph; `h3-card-grow` scroll-driven centre scale | Orient: the engaged card is unmistakable | Bento grid (desktop, rich + fine pointer); mobile bento rail (scroll-driven CSS, @supports-guarded) | bento: rich + fine · rail: lite + rich | Shape-shift off (`is-live` never set); rail cards render at base scale; all cards reachable |
| M5 | **confirm** — L1 sync: `is-flashed` pin→row flash, fx-aware smooth scroll, `data-map-return` pill glide; detail gallery `gallery-count-bump` on slide change | Confirm: the map↔list link answers "which row is this pin?"; the gallery counter answers "which image am I on?" | Search page map + results grid + pill; detail gallery count | lite + rich (scroll reads `data-fx`; flash killed under both reduced-motion CSS and `data-fx="none"`) | Scroll jumps (`auto`); row still scrolls into view and the popup takes focus — the keyboard path never depends on motion |
| M6 | **invite** — `hv2-scroll` wheel pulse cue | Invite: signals more content below the fold | Hero, fine-pointer screens wider than 809px only | lite + rich, fine pointer | Cue hidden on touch/small viewports by media query; pulse `animation: none` under reduced-motion |

## Cut / dormant

- `data-count` (motion.js counter): **dormant** — no template uses it; it is
  not a shipped effect and must not be re-activated without an entry here.
- `manage-card-in` (manage.css `.manage-card` entrance): **portal-scoped** —
  the /manage/ owner dashboard is utility UI outside the Framer-grade public
  vocabulary; declared here so the effect hunt stays exhaustive, not mapped.
- Anything not in the table above is outside the vocabulary; adding an effect
  means editing this table (still ≤6) or cutting one first.

## Section archetypes (for H4 rhythm)

1. **full-bleed** — an edge-to-edge media band where imagery owns the stage:
   the hero (owns the viewport), the showcase bento (media fills every tile
   and the text rides on the image). One per screenful; never two neighbours.
2. **type-led** — a text-led block where the heading carries the section
   (recommended/nearby headers, the philosophy lines on /about/).
3. **edge strip** — a narrow full-width band stitching sections together
   (the five-checks marquee, the channels strip inside recommended).

Home mapping (top-level flow order — r30 H4; each band carries its
archetype as `data-archetype`, asserted by test_h4_section_rhythm.py):
`#hero` full-bleed → `#checks` edge strip → `#bento` full-bleed →
`#recommended` type-led → `#nearby` type-led. The marquee is an edge strip,
not a second full-bleed (r30 resolves the r25 double-listing).

Rule: at least 3 archetypes in use site-wide; never more than 2 neighbouring
sections share one archetype.
