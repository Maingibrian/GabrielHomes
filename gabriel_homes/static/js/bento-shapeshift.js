/* =============================================================
   Gabriel Homes — bento shape-shift (r13)

   Vanilla re-implementation of the Framer "Spotlight Bento Grid"
   interaction (framer.com/m/Spotlight-Bento-Grid), decoded from
   its published component source:

     - The hovered card swaps its grid geometry (span 1 -> span 2);
       grid-auto-flow re-packs the siblings around it. That is the
       "shape shift".
     - Framer animates the geometry swap with a framer-motion layout
       animation (FLIP): measure each card's box before/after the
       class swap, then animate translate+scale back to identity
       with a spring {bounce: .12, duration: .45}. Children receive
       inverse-scale compensation so photos/text never distort.

   This file reproduces exactly that with zero deps:

     1. Grid-level pointer tracking (not per-card enter/leave): the
        card under the pointer is the single grown card. Chrome
        re-fires boundary events after layout shifts, so per-card
        hover toggles ping-pong forever once cards move under a
        still cursor — grid-level tracking + a post-settle check
        kills that loop (this is what Framer's variant engine does).
     2. Boxes are measured with offsetLeft/Top/Width/Height, which
        ignore transforms -> mid-flight re-hovers measure cleanly.
     3. WAAPI animates translate+scale -> none with origin top-left
        (origin is what makes the FLIP math land pixel-exact).
     4. Easing cubic-bezier(0.3, 1.4, 0.45, 1) ~= spring bounce .12
        at 450ms: slight overshoot, soft landing.
     5. Border radius is corrected per-axis during scale.

   SAFETY GATES (D-MOTION-SAFE, same philosophy as motion.js):
     - All growth CSS is gated behind html.bento-live-ready, set
       HERE only. No JS -> the mosaic is exactly as before.
     - Desktop only (min-width 1021px, 3-col layout), fine pointer
       with hover, and never under prefers-reduced-motion.
     - The spotlight card (already 3x2) never shape-shifts.
   ============================================================= */
(function () {
  "use strict";

  var mqDesktop = window.matchMedia("(min-width: 1021px)");
  var mqFine = window.matchMedia("(hover: hover) and (pointer: fine)");
  var mqReduced = window.matchMedia("(prefers-reduced-motion: reduce)");

  function eligible() {
    return mqDesktop.matches && mqFine.matches && !mqReduced.matches;
  }

  if (!eligible()) return;
  if (!document.querySelectorAll(".bento-grid").length) return;

  // First executable effect: arm the CSS gate. From here the
  // .is-grown span rule exists; everything else is enhancement.
  document.documentElement.classList.add("bento-live-ready");

  var DURATION = 450;
  var SETTLE = DURATION + 90; // spring tail before the re-check runs
  var EASING = "cubic-bezier(0.3, 1.4, 0.45, 1)";
  var RADIUS = 16; // keep in sync with .bento-card border-radius

  var anims = new WeakMap();

  function cancelAnims(el) {
    var list = anims.get(el);
    if (list) list.forEach(function (a) { try { a.cancel(); } catch (e) {} });
  }

  function trackAnims(el, list) { anims.set(el, list); }

  // Transform-immune geometry (layout box, not visual box).
  function boxOf(el) {
    return {
      x: el.offsetLeft, y: el.offsetTop,
      w: el.offsetWidth, h: el.offsetHeight
    };
  }

  function boxes(cards) {
    return cards.map(boxOf);
  }

  /* Animate every card whose slot changed from `first` to `last`.
     FLIP: start each card at its OLD box (translate + scale, origin
     top-left) and spring to identity. Children are counter-scaled
     (framer-motion's technique) so photos and text never distort. */
  function playFlip(grid, first, last) {
    var cards = cardList(grid);
    var running = [];
    cards.forEach(function (card, i) {
      var a = first[i];
      var b = last[i];
      if (a.x === b.x && a.y === b.y &&
          a.w === b.w && a.h === b.h) return;

      cancelAnims(card);

      var sx = a.w / b.w;
      var sy = a.h / b.h;
      var dx = a.x - b.x;
      var dy = a.y - b.y;

      running.push(card.animate([
        {
          transform: "translate(" + dx + "px, " + dy + "px) " +
                     "scale(" + sx + ", " + sy + ")",
          borderRadius: RADIUS / sx + "px / " + RADIUS / sy + "px"
        },
        { transform: "none", borderRadius: RADIUS + "px" }
      ], { duration: DURATION, easing: EASING }));

      card.querySelectorAll(
        ".bento-card__bg, .bento-card__scrim, .bento-card__body"
      ).forEach(function (kid) {
        kid.style.transformOrigin = "top left";
        running.push(kid.animate([
          { transform: "scale(" + (1 / sx) + ", " + (1 / sy) + ")" },
          { transform: "none" }
        ], { duration: DURATION, easing: EASING }));
      });

      trackAnims(card, running);
    });
    return running.length;
  }

  function cardList(grid) {
    return Array.prototype.slice.call(
      grid.querySelectorAll(".bento-card"));
  }

  function grownCard(grid) {
    return grid.querySelector(".bento-card.is-grown");
  }

  /* Make `card` the single grown tile of its grid (FLIP-animated). */
  function activate(grid, card) {
    if (card.classList.contains("bento-card--spotlight")) return;
    if (card === grownCard(grid)) return;

    var cards = cardList(grid);
    var first = boxes(cards);
    var prev = grownCard(grid);
    if (prev) prev.classList.remove("is-grown");
    card.classList.add("is-grown");
    grid.classList.add("bento-live");
    playFlip(grid, first, boxes(cards));
    scheduleSettle(grid);
  }

  /* Remove growth (FLIP back to the resting mosaic). */
  function deactivate(grid) {
    var prev = grownCard(grid);
    if (!prev) return;
    var cards = cardList(grid);
    var first = boxes(cards);
    prev.classList.remove("is-grown");
    grid.classList.remove("bento-live");
    playFlip(grid, first, boxes(cards));
  }

  /* ---- The settle loop: after each morph, the layout has changed
     under a possibly stationary cursor. Re-check which card is
     under the last pointer position and switch ONCE if the pack
     slid a different tile under it. Bounded (max 2 passes) so no
     oscillation is possible, unlike per-card enter/leave toggles. */
  function scheduleSettle(grid) {
    var state = gridState.get(grid);
    clearTimeout(state.settleTimer);
    state.settleTimer = setTimeout(function () {
      var x = state.px;
      var y = state.py;
      if (x == null || !grownCard(grid)) return;
      var el = document.elementFromPoint(x, y);
      var card = el && el.closest ? el.closest(".bento-card") : null;
      if (card && card.closest(".bento-grid") === grid &&
          card !== grownCard(grid) &&
          !card.classList.contains("bento-card--spotlight")) {
        activate(grid, card);
      }
    }, SETTLE);
  }

  var gridState = new WeakMap();

  function stateFor(grid) {
    var s = gridState.get(grid);
    if (!s) {
      s = { px: null, py: null, raf: 0, settleTimer: 0 };
      gridState.set(grid, s);
    }
    return s;
  }

  document.querySelectorAll(".bento-grid").forEach(function (grid) {
    var state = stateFor(grid);

    // Pointer tracking at grid level; rAF-throttled hit testing.
    grid.addEventListener("pointermove", function (e) {
      state.px = e.clientX;
      state.py = e.clientY;
      if (state.raf) return;
      state.raf = requestAnimationFrame(function () {
        state.raf = 0;
        if (!eligible()) return;
        var el = document.elementFromPoint(state.px, state.py);
        var card = el && el.closest ? el.closest(".bento-card") : null;
        if (card && card.closest(".bento-grid") === grid) {
          activate(grid, card);
        }
      });
    });

    // Leaving the whole mosaic relaxes it; gaps between cards do not.
    grid.addEventListener("pointerleave", function () {
      state.px = state.py = null;
      clearTimeout(state.settleTimer);
      deactivate(grid);
    });

    // Keyboard parity: focusing a tile shape-shifts it too.
    grid.addEventListener("focusin", function (e) {
      var card = e.target.closest(".bento-card");
      if (card && card.closest(".bento-grid") === grid) activate(grid, card);
    });
    grid.addEventListener("focusout", function (e) {
      var to = e.relatedTarget;
      if (!to || !grid.contains(to)) deactivate(grid);
    });
  });

  // Context changes (resize across the 1021px line, OS motion toggle):
  // disarm and drop any half-state immediately.
  function onContextChange() {
    if (!eligible()) {
      document.documentElement.classList.remove("bento-live-ready");
      document.querySelectorAll(".bento-grid").forEach(function (grid) {
        clearTimeout(stateFor(grid).settleTimer);
        var g = grownCard(grid);
        if (g) g.classList.remove("is-grown");
        grid.classList.remove("bento-live");
      });
    } else {
      document.documentElement.classList.add("bento-live-ready");
    }
  }
  [mqDesktop, mqFine, mqReduced].forEach(function (mq) {
    if (mq.addEventListener) mq.addEventListener("change", onContextChange);
  });
})();
