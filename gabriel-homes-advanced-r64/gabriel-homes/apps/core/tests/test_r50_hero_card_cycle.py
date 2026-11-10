"""r50 — hero second pass: dynamic card, reference geometry, honest strip.

Owner round two on the r49 hero, three asks:

1. "the card placement is also wrong... it also needs to be dynamic
   changing from listing to listing" — the floating card is now a
   carousel: the view passes hero_card_listings (up to five showcase
   entries, featured first), the template renders one pane per
   listing with pane #1 active SERVER-SIDE (no-JS shows listing #1,
   fail-closed), and js/hero-card.js rotates them every 6s. The
   rotation is CONTENT — it runs in every fx tier and under
   reduced-motion; only the crossfade is motion (html.motion-ready
   gate + the r48 triple kill switches). Pause contract: hover,
   focus and hidden tabs stop the timer; the dots navigate directly.

2. "kindly reference the image, it was much cleaner" — the geometry
   returns to the reference bands: the card pins TOP-RIGHT as a
   HORIZONTAL pane (photo left ~44%, details right, the on-photo
   badge at the image's top-left); the search pill drops into a
   lower hero__search-zone band that spans the container with the
   popular-area chips under it; the eyebrow tag is gone — the
   headline opens the page like the reference. (r51: the market
   stat this pass kept bottom-left is now REMOVED — see
   test_r51_hero_polish; the pane swap also gained a drift, but
   every r50-pinned prefix below survives verbatim.)

3. "better wording (no agents in this website) and better icons" —
   the strip reads "Checked listings / Prices in writing / A person
   replies" (site-true, p0-clean, agent-free), with an everyday-
   object icon family (house / price tag / chat bubble) replacing
   the AI-looking shield-check, two-people and headset set.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

from django.test import SimpleTestCase

REPO = Path(__file__).resolve().parents[3]
HOME_HTML = REPO / "templates" / "core" / "home.html"
HOME_CSS = REPO / "static" / "css" / "home.css"
HERO_JS = REPO / "static" / "js" / "hero-card.js"
VIEWS_PY = REPO / "apps" / "core" / "views.py"


def _block() -> str:
    css = HOME_CSS.read_text(encoding="utf-8")
    return css[css.index("r50 — HERO"):css.index("3. Featured properties",
                                                 css.index("r50 — HERO"))]


# ---------------------------------------------------------------------------
# Markup
# ---------------------------------------------------------------------------
class R50MarkupTests(SimpleTestCase):

    def setUp(self):
        self.html = HOME_HTML.read_text(encoding="utf-8")

    def test_eyebrow_tag_is_gone(self):
        """The reference has no eyebrow — the headline opens the page."""
        self.assertNotIn("hero__tag", self.html)
        css = HOME_CSS.read_text(encoding="utf-8")
        self.assertNotIn(".hero__tag", css, "the dead rule must go too")

    def test_search_pill_moves_to_a_lower_band(self):
        """The reference's wide lower pill: the form and the chips leave
        the text column and sit in their own hero__search-zone band."""
        self.assertIn('class="hero__search-zone"', self.html)
        zone = self.html.split('class="hero__search-zone"', 1)[1]
        self.assertIn('id="hero-search-form"', zone)
        self.assertIn('class="hero__locations', zone)
        # the form keeps every h2 contract hook
        self.assertIn('data-search-bar', zone)
        self.assertIn('data-segment="sale"', zone)
        self.assertIn('data-segment="rent"', zone)
        # and neither the form nor the pill class lives in the headline
        # column any more (the slice spans main + card, up to the zone)
        main = self.html[
            self.html.index('class="hero__main"'):
            self.html.index('class="hero__search-zone"')]
        self.assertNotIn("<form", main)
        self.assertNotIn("hero__search ", main)

    def test_dynamic_card_pane_markup(self):
        self.assertIn("{% if hero_card_listings %}", self.html)
        self.assertIn('data-hero-card-track', self.html)
        self.assertIn('data-hero-card-pane', self.html)
        self.assertIn(
            'class="hero-card__pane{% if forloop.first %} is-active{% endif %}"',
            self.html)
        # the dots render only when there is something to rotate
        self.assertIn("{% if hero_card_listings|length > 1 %}", self.html)
        self.assertIn('data-hero-card-dot="{{ forloop.counter0 }}"', self.html)
        self.assertIn('aria-label="Show featured listing {{ forloop.counter }}', self.html)
        # every pane is links only — no forms, no CTA button classes
        self.assertNotIn("btn--", self.html.split("</section>", 1)[0])

    def test_strip_reworded_agent_free(self):
        # r56: comfort-led labels (owner round seven); the r50 check-ledger
        # labels are retired with the how-we-check story (→ /checks/).
        for label in ("Homes with character", "Sea-breeze mornings",
                      "Coastal short stays"):
            self.assertIn(label, self.html)
        for banned in ("Local agents", "Trusted listings",
                       "Dedicated support", "Verified Agents",
                       "Checked listings", "Prices in writing"):
            self.assertNotIn(banned, self.html)

    def test_new_icon_family_everyday_objects(self):
        """r56: house / sun / waves — one 1.7px stroke family for the
        comfort-led labels (character, sea-breeze mornings, short
        stays); the old compound-metaphor pictograms are gone (the
        headless shield-with-check, the two-people and the headset)."""
        ul = self.html.split('class="hero__assurances', 1)[1].split("</ul>", 1)[0]
        self.assertEqual(ul.count("<svg"), 3, "exactly three strip icons")
        # house: gable roofline
        self.assertIn('d="M4.6 10.9 12 4.4l7.4 6.5"', ul)
        # sun: core circle + eight rays
        self.assertIn('<circle cx="12" cy="12" r="4"', ul)
        self.assertIn('d="M12 3v2M12 19v2M3 12h2M19 12h2', ul)
        # waves: two breaking swell lines
        self.assertIn('d="M3 10.5c2.2 0 2.2-1.6 4.5-1.6', ul)
        self.assertIn('d="M3 15.5c2.2 0 2.2-1.6 4.5-1.6', ul)
        # the r49 pictograms and the r50 ledger icons are gone
        self.assertNotIn("M12 3 5 5.8", ul)      # old shield
        self.assertNotIn('cx="9" cy="8.4" r="3.1"', ul)  # old two-people
        self.assertNotIn("M4.5 13v-1.6a7.5", ul)  # old headset
        self.assertNotIn('d="M4.5 12.5 12 5h8v8l-7.5 7.5-8-8Z"', ul)  # price tag
        self.assertNotIn('d="M7 5h10a3 3 0 0 1 3 3v6', ul)  # chat bubble


# ---------------------------------------------------------------------------
# CSS — reference geometry, crossfade states, kill switches
# ---------------------------------------------------------------------------
class R50CSSTests(SimpleTestCase):

    def setUp(self):
        self.block = _block()
        self.css = HOME_CSS.read_text(encoding="utf-8")

    def test_card_pins_top_right_with_no_push(self):
        """The r49 defect the owner called out: the card hung mid-hero
        (margin-top clamp) in a fixed 400px column. The r50 block pins
        it top-right in an auto column."""
        wide = re.search(
            r"@media \(min-width: 1200px\) \{(.*?)\n\}", self.block, re.S)
        self.assertTrue(wide, "the >=1200 block must exist")
        self.assertIn("align-items: start", wide.group(1))
        self.assertIn("justify-self: end", wide.group(1))
        self.assertIn("width: clamp(320px, 30vw, 420px)", wide.group(1))
        # the r49 push is gone
        self.assertNotIn("clamp(0px, 4vw, 56px)", self.css)
        self.assertNotIn("400px; gap: 4rem", self.css)

    def test_pane_is_horizontal_like_the_reference(self):
        self.assertIn("grid-template-columns: 44% minmax(0, 1fr)", self.block)
        self.assertIn("min-height: 176px", self.block)

    def test_pane_crossfade_states(self):
        self.assertRegex(
            self.block,
            r"\.hero-card__pane\.is-active \{\s*display: grid; position: relative; z-index: 1; opacity: 1;")
        self.assertRegex(
            self.block,
            r"\.hero-card__pane\.is-leaving \{\s*display: grid; position: absolute; inset: 0; z-index: 2; opacity: 0;")
        self.assertIn("html.motion-ready .hero-card__pane { transition: opacity .55s",
                      self.block)

    def test_pane_kill_switches(self):
        """r48 triple: the swap is content and keeps running; the fade
        dies under reduced-motion, fx=none and a missing gate."""
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.block)
        self.assertIn('.hero-card__pane { transition: none !important; }',
                      self.block)
        self.assertIn('html[data-fx="none"] .hero-card__pane', self.block)
        self.assertIn("html:not([data-fx]) .hero-card__pane", self.block)

    def test_title_two_line_slot_keeps_panes_equal_height(self):
        rule = re.search(r"^\.hero-card__title \{[^}]*\}", self.block, re.M)
        self.assertTrue(rule)
        self.assertIn("min-height: 2.6em", rule.group(0))
        self.assertIn("-webkit-line-clamp: 2", rule.group(0))
        # r50 QA (VLM): without an explicit colour the title inherited
        # the hero's cream and ghosted on the white card
        self.assertIn("color: var(--ink)", rule.group(0))

    def test_badge_sits_on_the_photo_top_left(self):
        rule = re.search(r"^\.hero-card__badge \{[^}]*\}", self.block, re.M)
        self.assertTrue(rule)
        self.assertIn("top: 10px; left: 10px", rule.group(0))
        self.assertNotIn("bottom: 14px", rule.group(0))

    def test_search_zone_owns_the_lower_band(self):
        rule = re.search(r"^\.hero__search-zone \{[^}]*\}", self.block, re.M)
        self.assertTrue(rule, ".hero__search-zone rule missing")
        self.assertIn("margin-top: clamp(1.7rem, 4vh, 3rem)", rule.group(0))
        # capped near the reference's ~74% proportion (VLM-measured)
        self.assertIn("max-width: 1080px", rule.group(0))
        # the chips' r49 top margin is retired — the zone gap owns it
        self.assertRegex(self.block, r"\.hero__locations \{[^}]*margin-top: 0;")

    def test_dots_are_plain_controls(self):
        rule = re.search(r"^\.hero-card__dot \{[^}]*\}", self.block, re.M)
        self.assertTrue(rule)
        self.assertIn("width: 7px; height: 7px", rule.group(0))

    def test_r50_block_adds_no_hex(self):
        """F1 ratchet: tokens, color-mix and rgba only."""
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", self.block), [])


# ---------------------------------------------------------------------------
# JS — rotation contracts (content, not decoration)
# ---------------------------------------------------------------------------
class R50JsTests(SimpleTestCase):

    def setUp(self):
        self.js = HERO_JS.read_text(encoding="utf-8")

    def test_rotation_is_content_and_never_reads_the_fx_gate(self):
        """The swap must run in every tier — the file must not gate on
        data-fx / matchMedia at all (only the CSS fade is motion)."""
        self.assertIn("use strict", self.js)
        self.assertNotIn("data-fx", self.js)
        self.assertNotIn("matchMedia", self.js)

    def test_beats_and_guards(self):
        self.assertIn("INTERVAL = 6000", self.js)
        self.assertIn("FADE_MS = 700", self.js)
        self.assertIn("panes.length < 2) return", self.js)
        # never start a timer for a display:none card (<1200px)
        self.assertIn("root.offsetParent === null) return", self.js)

    def test_swap_is_leaving_over_active(self):
        self.assertIn('old.classList.remove("is-active")', self.js)
        self.assertIn('old.classList.add("is-leaving")', self.js)
        self.assertIn('fresh.classList.add("is-active")', self.js)
        # the sweeper is a timeout (transitionend never fires under
        # transition: none), FADE_MS after every swap
        self.assertIn(
            'setTimeout(function () { old.classList.remove("is-leaving"); }, FADE_MS)',
            self.js)

    def test_pause_contract(self):
        self.assertIn('"mouseenter"', self.js)
        self.assertIn('"mouseleave"', self.js)
        self.assertIn('"focusin"', self.js)
        self.assertIn('"focusout"', self.js)
        self.assertIn("e.relatedTarget", self.js)
        self.assertIn('"visibilitychange"', self.js)

    def test_dots_navigate_and_sync_aria(self):
        self.assertIn('"data-hero-card-dot"', self.js)
        self.assertIn('setAttribute("aria-current", "true")', self.js)
        self.assertIn('removeAttribute("aria-current")', self.js)


# ---------------------------------------------------------------------------
# View — the carousel is live showcase data
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestR50ViewData:

    @pytest.fixture(autouse=True)
    def seeded_db(self, db):
        from django.core.cache import cache
        cache.clear()
        call_command("seed_demo", no_images=True, target=20, verbosity=0,
                     i_know_this_is_demo=True)
        yield
        cache.clear()

    def test_view_passes_the_carousel_set(self):
        response = Client().get("/")
        ctx = response.context
        listings = ctx["hero_card_listings"]
        assert 1 <= len(listings) <= 5
        # the carousel is the showcase's head, featured first
        assert [p.pk for p in listings] == [
            p.pk for p in ctx["showcase_listings"][:5]]
        assert "hero_card_listing" not in ctx, "the r49 singular key is retired"

    def test_rendered_panes_match_the_set(self):
        html = Client().get("/").content.decode()
        panes = re.findall(r'data-hero-card-pane', html)
        assert 2 <= len(panes) <= 5, f"pane count, got {len(panes)}"
        # exactly one pane is active in the served HTML (pane #1)
        assert len(re.findall(r'class="hero-card__pane is-active"', html)) == 1
        # one dot per pane, first active, each labelled
        dots = re.findall(r'data-hero-card-dot="(\d+)"', html)
        assert len(dots) == len(panes)
        assert dots == [str(i) for i in range(len(panes))]
        assert len(re.findall(r'aria-label="Show featured listing', html)) == len(panes)
        assert 'class="hero-card__dot is-active"' in html

    def test_every_pane_links_to_its_detail_page(self):
        from apps.listings.models import Property
        html = Client().get("/").content.decode()
        first = Property.objects.published().order_by("-published_at").first()
        # each pane carries three links into the detail page (media,
        # title, View details) — never a dead card
        links = re.findall(r'class="hero-card__(?:media|title a?)?"? ?href="([^"]+)"', html)
        assert len(re.findall(r'class="hero-card__link" href="[^"]+"', html)) >= 2
        assert len(re.findall(r'class="hero-card__media" href="[^"]+"', html)) >= 2

    def test_no_javascript_still_shows_listing_one(self):
        """The first pane is active server-side — the served HTML alone
        (no JS execution) presents exactly one visible listing card."""
        html = Client().get("/").content.decode()
        # pane #1 carries the active class in the article tag itself
        assert 'class="hero-card__pane is-active" data-hero-card-pane' in html
        # every other pane is display:none in CSS terms — served inert
        assert html.count('class="hero-card__pane" data-hero-card-pane') >= 1
