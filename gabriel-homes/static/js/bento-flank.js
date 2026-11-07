/* =============================================================
   Gabriel Homes — r44 bento flank wordmarks ("gabriel" / "homes")

   The two giant words flanking the bento (static/css/home.css §3e)
   lag behind the scroll: they translate at ~0.14x of the section's
   travel, with heavy per-frame damping, so the mosaic streams past
   while the words barely move — the "stagnant parallax" the owner
   asked for. Same transform for both words; travel is clamped so a
   word can never leave its section.

   Fails closed like every effect on the site: no data-fx attribute
   (fx-gate blocked / JS off) or fx="none" (which the gate already
   assigns to reduced-motion users) → this script does nothing and
   the words simply sit at their anchors. CSS covers the rest: the
   motion-reduce block in home.css pins the words with
   transform:none !important, which beats this file's inline style.

   bento-shift.js is deliberately NOT touched — the H3 mobile rail
   stays pure CSS.
   ============================================================= */
(function () {
  "use strict";

  var section = document.querySelector(".showcase");
  if (!section) return;
  var words = section.querySelectorAll(".bento-flank__word");
  if (!words.length) return;

  var FX = document.documentElement.getAttribute("data-fx") || "none";
  if (FX === "none") return;  // fail closed: no gate, no motion
  // (reduced motion is handled centrally: fx-gate.js sets data-fx="none",
  //  and the reduce block in home.css pins the words regardless)

  var wide = window.matchMedia("(min-width: 1440px)");
  if (!wide || !wide.matches) return;  // words are display:none below 1440

  var FACTOR = 0.14;   // lag fraction — 0 glues words to the section, 1 to the viewport
  var MAX_PX = 110;    // travel clamp; with the 7.5rem anchors a word never leaves the section
  var DAMPING = 0.065; // per-frame ease — the heavy, "stagnant" glide

  var target = 0, current = 0, raf = 0;

  function frame() {
    raf = 0;
    var r = section.getBoundingClientRect();
    var vh = window.innerHeight || document.documentElement.clientHeight;
    // Skip the work while the section is well off-screen.
    if (r.bottom > -240 && r.top < vh + 240) {
      // + when the section centre sits below the viewport centre, - above it.
      var centre = r.top + r.height / 2 - vh / 2;
      target = Math.max(-MAX_PX, Math.min(MAX_PX, centre * FACTOR));
      current += (target - current) * DAMPING;
      if (Math.abs(target - current) < 0.05) current = target;
      var t = "translate3d(0," + (-current).toFixed(2) + "px,0)";
      for (var i = 0; i < words.length; i++) words[i].style.transform = t;
    }
    if (!raf) raf = requestAnimationFrame(frame);
  }
  raf = requestAnimationFrame(frame);

  // Pause the loop when the breakpoint flips (words hidden → no rAF).
  if (wide.addEventListener) {
    wide.addEventListener("change", function () {
      if (!wide.matches && raf) {
        cancelAnimationFrame(raf);
        raf = 0;
      } else if (wide.matches && !raf) {
        raf = requestAnimationFrame(frame);
      }
    });
  }
})();
