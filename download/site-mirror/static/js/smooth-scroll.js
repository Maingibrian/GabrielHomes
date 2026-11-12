/* F5 — smooth scroll (Lenis), D-LOOP-29a.
 *
 * Contract (SCORECARD F5): fx=rich ONLY; off for touch (fine pointer +
 * hover required); anchors, find-in-page, focus and keyboard scrolling
 * stay native — this file adds no key/touch listeners, it only drives
 * wheel-based smoothing. Without JS nothing happens (D-MOTION-SAFE).
 *
 * window.ghScrollTo(el, block) is defined UNCONDITIONALLY so every call
 * site is safe on lite/none/touch devices: it drives Lenis when the
 * instance exists and falls back to native scrollIntoView otherwise —
 * the pre-F5 behaviour, reachable at every call site.
 */
(function () {
  "use strict";

  var root = document.documentElement;

  // Shared scroll helper — the scrollIntoView hack's replacement.
  // Honours scroll-margin-top (what native scrollIntoView uses) so the
  // fixed pill nav never covers the target.
  window.ghScrollTo = function (el, block) {
    if (!el) return;
    if (window.__lenis) {
      var m = parseFloat(getComputedStyle(el).scrollMarginTop) || 0;
      var opts = { offset: -m };
      if (block === "center") {
        opts.offset = -(window.innerHeight - el.getBoundingClientRect().height) / 2;
      }
      window.__lenis.scrollTo(el, opts);
      return;
    }
    var fxNone = root.getAttribute("data-fx") === "none";
    el.scrollIntoView({ behavior: fxNone ? "auto" : "smooth", block: block || "start" });
  };

  // ---- Lenis guards, in contract order, all before construction ----
  // D-LOOP-16a: the reduced-motion preference is NEVER re-checked in JS —
  // fx-gate.js maps it to data-fx="none" and the guard below refuses
  // anything but rich.
  if (root.getAttribute("data-fx") !== "rich") return;          // fx=rich only
  if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
  if (!window.Lenis) return;                                    // lib missing

  window.__lenis = new Lenis({ autoRaf: true, anchors: false });  // motion.js owns anchors
})();
