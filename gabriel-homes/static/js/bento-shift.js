/* =============================================================
   Gabriel Homes — homes bento "shape shift" (home page only)

   Ports the behaviour of the Framer "Spotlight Bento Grid" to the
   .bento-grid--shift mosaic on the home page.

   Hovering (or keyboard-focusing) a card promotes THAT card to a
   full-width, two-row spotlight and the other cards reflow around it.

   Why it is built this way (the "shuffling" bug):
     - The promoted card is placed on the row of the card you hovered,
       so its new box always contains the old one. The pointer can
       therefore never end up over a different card after the reflow,
       which is what used to chain into promote -> reflow -> promote.
     - Which card is hovered is decided from LAYOUT positions
       (offsetLeft/Top/Width/Height ignore transforms), not from the
       element under the cursor, so cards flying past mid-animation
       can't be mistaken for hover targets.
     - Gaps and corners keep the current state; switching cards waits a
       short hover-intent delay; leaving the grid has a grace delay.
     - Colour/zoom follow the .is-spot class, not CSS :hover, so a card
       sliding under a still cursor doesn't flash.

   Only on devices the capability gate marks rich + fine pointer (same
   pointer query the CSS uses, centralised in fx-gate.js). Touch screens
   keep plain tap-through cards; reduced-motion and lite devices never
   enter the effect at all. Below 1021px nothing applies.
   ============================================================= */
(function () {
  "use strict";

  var grid = document.querySelector(".bento-grid--shift");
  if (!grid || !window.matchMedia) return;

  // F2: pointer-driven DECORATIVE effects are rich-tier and fine-pointer
  // only, decided once by fx-gate.js. [data-fine] exists only on
  // (hover: hover) and (pointer: fine); data-fx="none" (reduced motion)
  // and "lite" (Save-Data / <=4 cores / <=4 GB) skip this effect
  // entirely — the runbook's "no effect runs under none". A missing
  // attribute (fx-gate blocked) fails CLOSED to no-effect.
  // The viewport half of the old check (min-width 1021px) stays local:
  // it is layout, not capability (H3 builds the mobile alternative).
  var FX = document.documentElement.getAttribute("data-fx") || "none";
  if (!document.documentElement.hasAttribute("data-fine") || FX !== "rich") {
    return;
  }

  var canAnimate = typeof Element.prototype.animate === "function";
  var reduce = !canAnimate; // rich tier already excludes reduced-motion
  var wide = window.matchMedia("(min-width: 1021px)");

  grid.classList.add("is-live");          // CSS gates the shape-shift/zoom states on this
  // (r12: the desaturation pass is gone — cards rest in colour now)
  // offsetTop/Left are measured against the grid, so it must be positioned.
  if (getComputedStyle(grid).position === "static") grid.style.position = "relative";

  var DURATION = 520;
  // Same overshoot curve as the photo de-zoom, so the motion feels related.
  var EASE = "cubic-bezier(0.34, 1.2, 0.5, 1)";
  var INTENT_MS = 110;     // pointer must rest on a card this long before it is promoted
  var COOLDOWN_MS = 240;   // minimum gap between two promotions
  var LEAVE_MS = 140;      // grace before the grid resets after the pointer exits

  var cards = Array.prototype.slice.call(grid.querySelectorAll(".bento-card"));
  var active = null;       // card currently promoted, or null
  var running = [];        // animations THIS script started (never CSS transitions)
  var lastChange = 0;
  var target = null, intentTimer = 0, leaveTimer = 0;
  var lastX = 0, lastY = 0, hasPointer = false;

  // ---------- layout helpers (all transform-proof) ----------

  function metrics() {
    var cs = getComputedStyle(grid);
    var gap = parseFloat(cs.rowGap);
    if (!isFinite(gap)) gap = 0;
    var rowH = parseFloat(cs.gridAutoRows);
    if (!isFinite(rowH)) {
      rowH = Infinity;
      cards.forEach(function (c) { rowH = Math.min(rowH, c.offsetHeight); });
    }
    var step = rowH + gap, bottom = 0;
    cards.forEach(function (c) { bottom = Math.max(bottom, c.offsetTop + c.offsetHeight); });
    return { step: step, rows: Math.max(1, Math.round((bottom + gap) / step)) };
  }

  // Row (0-based) the promoted card should start on: the hovered card's
  // own row, pulled up only if a 2-row card wouldn't fit below it.
  function startRow(card) {
    var m = metrics();
    var r = Math.round(card.offsetTop / m.step);
    return Math.max(0, Math.min(r, m.rows - 2));
  }

  // Card whose LAYOUT box contains the pointer (null in the gaps).
  function cardAt(cx, cy) {
    var g = grid.getBoundingClientRect();
    var x = cx - g.left - grid.clientLeft;
    var y = cy - g.top - grid.clientTop;
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      if (x >= c.offsetLeft && x < c.offsetLeft + c.offsetWidth &&
          y >= c.offsetTop && y < c.offsetTop + c.offsetHeight) return c;
    }
    return null;
  }

  function cardFrom(el) {
    return el && el.closest ? el.closest(".bento-card") : null;
  }

  // ---------- animation (FLIP) ----------

  function run(el, frames) {
    var anim = el.animate(frames, { duration: DURATION, easing: EASE });
    running.push(anim);
    var done = function () {
      var i = running.indexOf(anim);
      if (i > -1) running.splice(i, 1);
    };
    anim.onfinish = done;
    anim.oncancel = done;
  }

  function cancelRunning() {
    var list = running;
    running = [];
    list.forEach(function (a) { a.cancel(); });
  }

  // `before` holds the old (visual) rects. Growing cards are revealed
  // through a clip that expands (no stretching); shrinking cards scale
  // down with their text faded out; the rest just slide.
  function flip(before) {
    cancelRunning();
    cards.forEach(function (card, i) {
      var a = before[i];
      var b = card.getBoundingClientRect();
      var dx = a.left - b.left;
      var dy = a.top - b.top;
      var grows = b.width > a.width + 1 || b.height > a.height + 1;
      var shrinks = !grows && (b.width < a.width - 1 || b.height < a.height - 1);
      if (!grows && !shrinks && Math.abs(dx) < 1 && Math.abs(dy) < 1) return;

      if (grows) {
        var gx = Math.max(0, b.width - a.width);
        var gy = Math.max(0, b.height - a.height);
        var endR = card.classList.contains("is-spot") ? 32 : 16;
        run(card, [
          { transform: "translate(" + dx + "px," + dy + "px)",
            clipPath: "inset(0px " + gx + "px " + gy + "px 0px round 16px)" },
          { transform: "translate(0px, 0px)",
            clipPath: "inset(0px 0px 0px 0px round " + endR + "px)" }
        ]);
      } else if (shrinks) {
        var sx = a.width / b.width;
        var sy = a.height / b.height;
        run(card, [
          { transformOrigin: "0 0",
            transform: "translate(" + dx + "px," + dy + "px) scale(" + sx + "," + sy + ")" },
          { transformOrigin: "0 0", transform: "translate(0px, 0px) scale(1, 1)" }
        ]);
        var body = card.querySelector(".bento-card__body");
        if (body) run(body, [{ opacity: 0 }, { opacity: 0, offset: 0.55 }, { opacity: 1 }]);
      } else {
        run(card, [
          { transform: "translate(" + dx + "px," + dy + "px)" },
          { transform: "translate(0px, 0px)" }
        ]);
      }
    });
  }

  // ---------- state ----------

  function clearAll() {
    clearTimeout(intentTimer);
    clearTimeout(leaveTimer);
    target = null;
    cancelRunning();
    if (active) {
      active.classList.remove("is-spot");
      active.style.removeProperty("--spot-row");
    }
    active = null;
    grid.classList.remove("has-spot");
  }

  function setSpot(card) {
    if (!wide.matches) { clearAll(); return; }
    if (card === active) return;

    var before = reduce ? null : cards.map(function (c) { return c.getBoundingClientRect(); });
    var row = card ? startRow(card) : 0;   // read layout BEFORE changing classes

    if (active) {
      active.classList.remove("is-spot");
      active.style.removeProperty("--spot-row");
    }
    active = card || null;
    if (active) {
      active.style.setProperty("--spot-row", String(row + 1));
      active.classList.add("is-spot");
      grid.classList.add("has-spot");
    } else {
      grid.classList.remove("has-spot");
    }

    lastChange = performance.now();
    if (before) flip(before);
  }

  // ---------- pointer ----------

  function commit() {
    intentTimer = 0;
    target = null;
    if (!hasPointer) return;
    var c = cardAt(lastX, lastY);
    if (c && c !== active) setSpot(c);
  }

  // Every promotion waits for dwell, including the first one. Without this,
  // a pointer sweeping across the grid promoted each card it passed over.
  function schedule(card) {
    if (card === target) return;
    target = card;
    clearTimeout(intentTimer);
    var wait = INTENT_MS;
    if (active) wait = Math.max(INTENT_MS, lastChange + COOLDOWN_MS - performance.now());
    intentTimer = setTimeout(commit, wait);
  }

  grid.addEventListener("pointermove", function (e) {
    if (e.pointerType !== "mouse" && e.pointerType !== "pen") return;
    hasPointer = true;
    lastX = e.clientX;
    lastY = e.clientY;
    clearTimeout(leaveTimer);
    var c = cardAt(lastX, lastY);
    if (!c) return;                        // in a gap: keep the current state
    if (c === active) {                    // back on the promoted card: cancel any switch
      clearTimeout(intentTimer);
      target = null;
      return;
    }
    schedule(c);
  });

  grid.addEventListener("pointerleave", function (e) {
    if (e.pointerType !== "mouse" && e.pointerType !== "pen") return;
    hasPointer = false;
    target = null;
    clearTimeout(intentTimer);
    clearTimeout(leaveTimer);
    leaveTimer = setTimeout(function () {
      if (hasPointer) return;
      var f = document.activeElement;     // keep a keyboard-focused card promoted
      if (f && grid.contains(f) && f.matches(":focus-visible")) setSpot(cardFrom(f));
      else setSpot(null);
    }, LEAVE_MS);
  });

  // ---------- keyboard ----------

  grid.addEventListener("focusin", function (e) {
    var card = cardFrom(e.target);
    if (card && card.matches(":focus-visible")) setSpot(card);
  });
  grid.addEventListener("focusout", function (e) {
    if (!hasPointer && !grid.contains(e.relatedTarget)) setSpot(null);
  });

  // Crossing the breakpoint resets the state so it never comes back stale.
  if (wide.addEventListener) {
    wide.addEventListener("change", function () { if (!wide.matches) clearAll(); });
  }
})();
