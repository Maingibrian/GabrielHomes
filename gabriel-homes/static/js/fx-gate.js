/* =============================================================
   Gabriel Homes — capability gate (F2)

   One tiny deferred script decides, ONCE, what this device gets:

     html[data-fx]   = "rich" | "lite" | "none"
     html[data-fine] = present only on (hover: hover) and (pointer: fine)

       none — prefers-reduced-motion. Behaves exactly like the old
              reduced-motion path: no effects run, content is fully
              visible (motion.js renders everything instantly).
       lite — constrained device: Save-Data on, or <= 4 CPU cores,
              or <= 4 GB deviceMemory. Essential behaviour runs;
              decorative/pointer effects do not.
       rich — full effects. Pointer-driven DECORATIVE effects
              (bento shape-shift, cursor polish) additionally
              require [data-fine].

   D-FX-GATE contract: every effect keys off these attributes — no
   effect re-checks prefers-reduced-motion or pointer media queries
   itself (the CSS @media parity blocks in tokens/home/components
   remain; they make TRANSITIONS free, not decisions).

   D-MOTION-SAFE: without JavaScript this script never runs, so no
   attribute is set and no effect runs anywhere — content is always
   visible. A missing attribute also fails CLOSED: motion.js and
   bento-shift.js treat it as "none".

   The decision table is mirrored 1:1 in
   apps/core/tests/test_f2_capability_gate.py — keep both in sync.
   ============================================================= */
(function () {
  "use strict";

  // Pure decision function: (mq, nav) -> "rich" | "lite" | "none".
  function computeFx(mq, nav) {
    if (mq("(prefers-reduced-motion: reduce)")) return "none";
    var cap = "rich";
    if (nav.connection && nav.connection.saveData) cap = "lite";
    if (typeof nav.hardwareConcurrency === "number" &&
        nav.hardwareConcurrency <= 4) {
      cap = "lite";
    }
    if (typeof nav.deviceMemory === "number" &&
        nav.deviceMemory <= 4) {
      cap = "lite";
    }
    return cap;
  }

  function apply(doc, win, nav) {
    if (!doc.documentElement || typeof win.matchMedia !== "function") return;
    var mq = function (q) {
      try { return win.matchMedia(q).matches; } catch (err) { return false; }
    };
    var html = doc.documentElement;
    html.setAttribute("data-fx", computeFx(mq, nav));
    if (mq("(hover: hover) and (pointer: fine)")) {
      html.setAttribute("data-fine", "");
    }
  }

  apply(document, window, navigator);
})();
