/* =============================================================
   Gabriel Homes — hero featured-card rotation (home page only)

   The owner asked for the hero's listing card to be "dynamic,
   changing from listing to listing": the card is now a carousel of
   up to five showcase panes. The ROTATION is content, not
   decoration — it runs in every fx tier and under reduced motion;
   only the crossfade is motion (home.css gates it behind
   html.motion-ready with the r48 triple kill switches). This file
   therefore never reads the fx gate.

   Pane #1 is active server-side, so no-JS shows the first listing
   and nothing here is load-bearing for content. The rotation starts
   only when there are 2+ panes AND the card is actually displayed
   (offsetParent — the whole feature is hidden below 1200px, where
   the bento below already carries the listings).

   Pause contract (WCAG 2.2.2 — pause, stop, hide):
     - hovering or focusing anything inside the card stops the timer;
       leaving resumes it (focus must truly leave — relatedTarget);
     - the dots give direct navigation and pause by focus;
     - a hidden tab stops it (visibilitychange) and it resumes on
       return only if the pointer is not parked on the card.
   ============================================================= */
(function () {
  "use strict";

  var track = document.querySelector("[data-hero-card-track]");
  if (!track) return;

  var root = track.closest(".hero-card");
  var panes = Array.prototype.slice.call(
    track.querySelectorAll("[data-hero-card-pane]"));
  var dots = Array.prototype.slice.call(
    document.querySelectorAll("[data-hero-card-dot]"));

  // A single listing is a static card — pane #1 is already active in
  // the served HTML; no timer, no dots (the template guards the dots
  // the same way).
  if (panes.length < 2) return;

  var INTERVAL = 6000;  // the hero slideshow beat
  var FADE_MS = 700;    // covers the .55s CSS transition with slack —
                        // and doubles as the no-motion cleanup path
                        // (transitionend never fires under
                        // transition: none, so the timeout is the only
                        // reliable sweeper in every tier)
  var index = 0;
  var timer = null;
  var hoverPaused = false;

  function syncDots() {
    dots.forEach(function (dot, i) {
      dot.classList.toggle("is-active", i === index);
      if (i === index) dot.setAttribute("aria-current", "true");
      else dot.removeAttribute("aria-current");
    });
  }

  function goTo(next) {
    if (next === index) return;
    var old = panes[index];
    var fresh = panes[next];
    index = next;
    // The outgoing pane fades ON TOP of the incoming one (CSS: is-leaving
    // is absolute, z-index 2, opacity 0). Both class changes land in one
    // tick so the transition engine sees a 1 -> 0 opacity run.
    old.classList.remove("is-active");
    old.classList.add("is-leaving");
    fresh.classList.add("is-active");
    setTimeout(function () { old.classList.remove("is-leaving"); }, FADE_MS);
    syncDots();
  }

  function stop() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  function restart() {
    stop();
    if (hoverPaused || document.hidden) return;
    timer = setInterval(function () {
      goTo((index + 1) % panes.length);
    }, INTERVAL);
  }

  // The card is display:none below 1200px — never start an invisible
  // timer for a feature the viewport cannot show.
  if (root && root.offsetParent === null) return;

  if (root) {
    root.addEventListener("mouseenter", function () {
      hoverPaused = true; stop();
    });
    root.addEventListener("mouseleave", function () {
      hoverPaused = false; restart();
    });
    root.addEventListener("focusin", function () {
      hoverPaused = true; stop();
    });
    root.addEventListener("focusout", function (e) {
      // resume only when focus actually leaves the whole card
      if (!root.contains(e.relatedTarget)) { hoverPaused = false; restart(); }
    });
  }

  dots.forEach(function (dot) {
    dot.addEventListener("click", function () {
      goTo(parseInt(dot.getAttribute("data-hero-card-dot"), 10) || 0);
    });
  });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) stop(); else restart();
  });

  syncDots();
  restart();
})();
