# DESIGN.md — Gabriel Homes design inventory

Extracted from `design-reference/index.html` (Framer export, page title: "Gabriel Homes — Real Estate in Mombasa · Buy, Rent & Short Stays"). WORK.md section 10 holds the working tokens; this file is the full list of what makes the design good, so the Django site can match it.

**How reliable is this?** Colours, fonts, sizes, tracking, radii, shadows, breakpoints, copy, section names and the animation components were read directly from the file. Exact grid columns, spacing and which element uses which radius were not recoverable from the export (it is mostly Framer runtime), so those are marked *(inferred)*. Verify against the reference in a browser.

## 1. Brand feel
Warm, editorial, premium coastal real estate with "a human point of view". Earth tones instead of the usual blue/green property-portal look. Big, tightly-tracked headlines, lots of air, soft depth, and quiet motion.

## 2. Colour palette
| Role | Hex |
|---|---|
| Page background / light sections | `#faf8f4` cream |
| White | `#ffffff` |
| Soft borders, chips | `#d8c9b8` sand |
| Muted text, divider lines | `#8a7d70` taupe |
| Secondary accent | `#a66a4d` clay |
| Hover / secondary dark | `#5a4032` brown |
| Main dark background | `#2a211c` espresso |
| Body text on light | `#211e1b` ink |
| Primary accent | `#af4715` burnt orange |

Pattern: cream and espresso sections alternate; white text on photos and dark sections; thin taupe lines as dividers.

## 2b. Typography
- **Geist** for headings and UI, **Geist Mono** for small labels.
- OpenType features: `blwf`, `cv03`, `cv04`, `cv09`, `cv11`.
- Weight 500 for headings, 400 body, 300 occasional.
- Line-height 1.2 (headings), 1.3 (body).
- Tight tracking: -0.02em to -0.08em; the bigger the type, the tighter.
- Scale up to a 120px display wordmark.
- Bracket tags: `[STORY]`, `[NUMBERS]`, `[AGENTS]`, `[PHILOSOPHY]`, `[FOOTER]`, `[001-UNDERSTAND]`, `[002-INSIGHT]`, `[003-SUPPORT]`, `[004-RESULTS]`.
- Paired eyebrow words: VISION, FOUNDER, MILESTONES / IMPACT, EXPERTS, PRINCIPLE / DIFFERENCE.
- Index numbers on nav items (01 About … 05 Contact), agent cards (01–08) and steps.

## 3. Shape and depth
- Radii: 8, 15, 20, 40, 60, 100px and full circles. Cards and image frames lean on 40px, buttons and tags on 100px pills.
- Soft layered shadows (never harsh), 1px inset outline on outlined buttons.
- Frosted nav bar: dark translucent with 10px backdrop blur.
- Gradient overlays on photos to keep white text legible.
- Thin taupe divider lines between stats and rows.
- One image uses grayscale (probably team portraits).

## 4. Page sections (order inferred from layer and copy order)
1. **Navigation**: three variants (desktop dark bar, tablet, mobile hamburger with "Menu / Close" full-screen overlay). Numbered links, phone `+254 712 345 678`, email `hello@gabrielhomes.co.ke`.
2. **Hero**: "Real estate with a human point of view." Subtitle about curated properties, considered service and local expertise on the Kenyan coast. Three stats: 480+ properties sold, 98% list-to-sale ratio, 60+ partner landlords and hosts.
3. **Story / Vision**: "We don't just sell property. We help people move forward." Sub-line: "Our work doesn't end when the keys change hands." Founder block (Gabriel Omullu) with a long quote revealed word by word. Line: "The best comes as standard. Premium quality, verified details, and full support included across every property."
4. **Three value tabs/cards**: People First, Property Second; Radical Transparency; Support Beyond the Keys.
5. **Numbers**: "A more personal approach to real estate." 12+ years, 1.4B+ transaction value, 96% client referrals, 8 neighbourhoods.
6. **Agents** (dark espresso): "Meet the people behind your next move." Eight portrait cards numbered 01–08 (Founder & MD, Client Relations, Acquisitions Advisor, Short Stays Specialist, Sales Director, Principal Agent, Senior Property Advisor, Market Research Analyst).
7. **Philosophy**: "Smart property search, genuine human perspective." Four numbered cards: Listen first, Know the market, Stay involved, Make the right move.
8. **Blog section** (exists in the file, no visible content): reserve a slot for market notes.
9. **CTA band** (dark): "Find a home that feels like Mombasa." Pill button "Explore Properties" with arrows.
10. **Footer**: `[FOOTER]`, "Redefining how you find your next home.", newsletter "Stay in the know." with Subscribe, columns Explore / Legal / Company / Visit, address (Nyali Centre, Links Road, Mombasa), giant "Homes" wordmark, "NYALI · MOMBASA · KENYA", copyright line.

## 5. Interaction and motion
- **Lenis** smooth scrolling.
- **Animated number counters** on all stats.
- **Word-by-word reveal** on the founder quote.
- **Staggered per-letter text** on nav labels and the footer wordmark.
- **Appear-on-scroll** transitions; a sticky section.
- Hamburger to full-screen menu on mobile.
- Phosphor icons.
- Rebuild all of this in vanilla JS/CSS, with `prefers-reduced-motion` support.

## 6. Responsive behaviour
Breakpoints: desktop ≥1200px, tablet 810–1199px, mobile ≤809px. Each section has its own tablet and mobile variant in the reference.

## 7. Imagery
Architectural and interior photography, portraits for the team. The reference hotlinks Unsplash and Pexels images; replace with local, optimised, licensed or owner-supplied photos.

## 8. Things NOT to carry over
Framer's JS bundles, `framerusercontent.com` URLs, Framer analytics, the "Create a free website with Framer" badge, and unused Framer default colours.

## 9. Portal pages that need design extensions
The reference is a brochure site, so these have no source design. Build them from the same components:
- Search results (filter bar as pill controls, 40px listing cards, `[001]` index tags)
- Listing detail (large gallery in 40px frames, price in Geist 500, sticky agent card, mobile Call/WhatsApp bar)
- Agent directory and profile (reuse the portrait cards)
- Account, saved properties, agent dashboard (cream background, espresso sidebar)
- Forms (inputs use 8px radius, 16px text, burnt-orange focus ring)
