/* =============================================================
   Gabriel Homes — motion layer (progressive enhancement)
   All effects disabled when the capability gate (fx-gate.js) sets
   html[data-fx="none"] — reduced-motion devices, and fail-closed when
   the gate script itself is missing.

   Implements (per WORK.md §10.6):
     1. Smooth scrolling (lightweight, no Lenis dependency)
     2. Animated number counters via IntersectionObserver
     3. Word-by-word reveal for the founder quote
     4. Appear-on-scroll fades for cards / sections
     5. Header background change on scroll
     6. Mobile menu open/close toggle
     7. Search-bar Buy/Rent segment toggle

   All text is readable without JS — these are enhancements only.
   ============================================================= */
(function () {
  "use strict";

  // Gate for CSS-hidden reveal targets. CSS hides [data-reveal] elements
  // ONLY under `html.motion-ready`, which is set HERE — the first statement
  // this script executes. If motion.js is stale, blocked by a network error,
  // or crashes later, the class is absent and every element stays visible.
  // (D-MOTION-SAFE: content can never be permanently blank.)
  document.documentElement.classList.add("motion-ready");

  // F2: the capability gate (static/js/fx-gate.js, always loaded first)
  // decides the tier ONCE for the whole site. data-fx="none" (reduced
  // motion) behaves exactly like the old in-file reduced-motion check;
  // a MISSING attribute fails CLOSED to "none" too — if fx-gate.js is
  // ever blocked or stale, every effect simply stays off (D-MOTION-SAFE:
  // content is rendered instantly, never blank).
  var fxNone =
    (document.documentElement.getAttribute("data-fx") || "none") === "none";

  // ---------- 1. Smooth scrolling (very small Lenis-style ease) ----------
  if (!fxNone && "addEventListener" in window) {
    document.addEventListener("click", function (e) {
      var a = e.target.closest('a[href^="#"]');
      if (!a) return;
      var hash = a.getAttribute("href");
      if (hash === "#" || hash.length < 2) return;
      var target = document.querySelector(hash);
      if (!target) return;
      e.preventDefault();
      /* F5 (D-LOOP-29a): Lenis under fx=rich; native fallback keeps lite/none intact. */
      if (window.ghScrollTo) { window.ghScrollTo(target, "start"); }
      else { target.scrollIntoView({ behavior: "smooth", block: "start" }); }
    });
  }

  // ---------- 2. Animated number counters ----------
  function animateCounter(el) {
    var target = parseFloat(el.dataset.count || "0");
    var suffix = el.dataset.suffix || "";
    var prefix = el.dataset.prefix || "";
    var decimals = parseInt(el.dataset.decimals || "0", 10);
    var duration = fxNone ? 0 : 1500;
    var start = performance.now();
    function fmt(v) {
      return prefix + v.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",") + suffix;
    }
    function step(now) {
      var t = Math.min(1, (now - start) / duration);
      // easeOutCubic
      var eased = 1 - Math.pow(1 - t, 3);
      el.textContent = fmt(target * eased);
      if (t < 1) requestAnimationFrame(step);
      else el.textContent = fmt(target);
    }
    requestAnimationFrame(step);
  }

  function setupCounters() {
    var counters = document.querySelectorAll("[data-count]");
    if (!counters.length) return;
    if (!("IntersectionObserver" in window) || fxNone) {
      counters.forEach(animateCounter);
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    counters.forEach(function (c) { io.observe(c); });
  }

  // ---------- 3. Word-by-word reveal for the founder quote ----------
  function setupQuoteReveal() {
    var quote = document.querySelector("[data-quote-reveal]");
    if (!quote) return;
    var text = quote.textContent.trim();
    var words = text.split(/\s+/);
    // S11 audit: build spans via DOM APIs instead of innerHTML so no
    // template-supplied text is ever re-parsed as markup.
    quote.textContent = "";
    var wordEls = words.map(function (w, i) {
      var span = document.createElement("span");
      span.className = "word";
      span.textContent = w;
      if (i > 0) quote.appendChild(document.createTextNode(" "));
      quote.appendChild(span);
      return span;
    });
    if (fxNone || !("IntersectionObserver" in window)) {
      wordEls.forEach(function (w) { w.classList.add("is-lit"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        // Reveal one word every ~120ms while the quote is in view.
        wordEls.forEach(function (w, i) {
          setTimeout(function () { w.classList.add("is-lit"); }, i * 120);
        });
        io.unobserve(entry.target);
      });
    }, { threshold: 0.3 });
    io.observe(quote);
  }

  // ---------- 4. Appear-on-scroll ----------
  function setupReveal() {
    var els = document.querySelectorAll("[data-reveal]");
    if (!els.length) return;
    if (fxNone || !("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -10% 0px" });
    els.forEach(function (el) { io.observe(el); });
  }

  // ---------- 5. Header scroll state ----------
  function setupHeaderScroll() {
    var header = document.querySelector(".site-header");
    if (!header) return;
    var onScroll = function () {
      if (window.scrollY > 24) header.classList.add("site-header--scrolled");
      else header.classList.remove("site-header--scrolled");
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // ---------- 5b. G1: floating pill nav — hides on scroll-down, returns
  // on scroll-up. Called ONLY under fx lite or rich (see init); with JS
  // blocked or fx=none the class is never added, so the header stays
  // visible (D-MOTION-SAFE: CSS never hides it on its own).
  function setupNavAutoHide() {
    var header = document.querySelector(".site-header");
    if (!header) return;
    var lastY = window.scrollY;
    var ticking = false;
    var onScroll = function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var y = window.scrollY;
        if (y > lastY + 4 && y > 160) {
          header.classList.add("nav--hidden");
        } else if (y < lastY - 4 || y <= 160) {
          header.classList.remove("nav--hidden");
        }
        lastY = y;
        ticking = false;
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    // Keyboard safety: focus entering the header always returns it.
    header.addEventListener("focusin", function () {
      header.classList.remove("nav--hidden");
    });
  }

  // ---------- 6. Mobile menu ----------
  function setupMobileMenu() {
    var openBtn = document.querySelector("[data-mobile-menu-open]");
    var menu = document.querySelector("[data-mobile-menu]");
    if (!openBtn || !menu) return;
    var closeBtn = menu.querySelector("[data-mobile-menu-close]");

    var open = function () {
      menu.classList.add("is-open");
      menu.setAttribute("aria-hidden", "false");
      openBtn.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";
    };
    var close = function () {
      menu.classList.remove("is-open");
      menu.setAttribute("aria-hidden", "true");
      openBtn.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    };
    openBtn.addEventListener("click", open);
    if (closeBtn) closeBtn.addEventListener("click", close);
    menu.addEventListener("click", function (e) {
      // Click on a nav link closes the menu.
      if (e.target.closest("a")) close();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.classList.contains("is-open")) close();
    });
  }

  // ---------- 7. Search bar Buy/Rent segment + URL builder + autocomplete ----------
  function setupSearchSegment() {
    var form = document.querySelector("[data-search-bar]");
    if (!form) return;
    var segBtns = form.querySelectorAll("[data-segment]");
    var hiddenType = form.querySelector("input[name='listing_type']");
    var typeSelect = form.querySelector("#hero-search-type");
    var locInput = form.querySelector("#hero-search-q");
    var locHidden = form.querySelector("#hero-search-location");

    // Build the SEO-friendly action URL from the current selections.
    // Pattern: /<type>-for-<sale|rent>/<location-slug>/  (or /property-for-<sale|rent>/<location-slug>/)
    function buildAction() {
      var listingType = hiddenType ? hiddenType.value : "sale";
      var typeSlug = typeSelect ? typeSelect.value : "";
      var locSlug = locHidden ? locHidden.value : "";
      var action = typeSlug
        ? "/" + typeSlug + "-for-" + listingType + "/"
        : "/property-for-" + listingType + "/";
      if (locSlug) action += locSlug + "/";
      form.setAttribute("action", action);
    }

    segBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        segBtns.forEach(function (b) { b.classList.remove("is-active"); });
        btn.classList.add("is-active");
        if (hiddenType) hiddenType.value = btn.dataset.segment;
        buildAction();
      });
    });
    if (typeSelect) typeSelect.addEventListener("change", buildAction);

    // If the user types a location but doesn't pick a suggestion,
    // fall back to a text search via the q param on the type-only URL.
    if (locInput) {
      locInput.addEventListener("input", function () {
        if (locHidden) locHidden.value = "";
        buildAction();
      });
    }

    // Autocomplete dropdown
    if (locInput && locHidden) {
      var dropdown = null;
      var debounceTimer = null;

      function clearDropdown() {
        if (dropdown) { dropdown.remove(); dropdown = null; }
      }

      function showResults(results) {
        clearDropdown();
        if (!results.length) return;
        dropdown = document.createElement("div");
        dropdown.setAttribute("role", "listbox");
        dropdown.style.cssText = [
          "position:absolute",
          "background:var(--white)",
          "border:1px solid var(--sand)",
          "border-radius:var(--radius-sm)",
          "box-shadow:var(--shadow-card)",
          "max-height:300px",
          "overflow-y:auto",
          "z-index:100",
          "width:100%",
          "margin-top:4px",
        ].join(";");
        // Position relative to the input's parent label.
        var parentLabel = locInput.closest("label");
        if (parentLabel) {
          parentLabel.style.position = "relative";
          parentLabel.appendChild(dropdown);
        } else {
          locInput.parentNode.appendChild(dropdown);
        }
        results.forEach(function (res) {
          var item = document.createElement("div");
          item.setAttribute("role", "option");
          item.style.cssText = [
            "padding:0.6rem 0.85rem",
            "cursor:pointer",
            "font-size:var(--text-sm)",
            "color:var(--ink)",
            "border-bottom:1px solid var(--sand)",
          ].join(";");
          // S11 audit: DOM APIs instead of innerHTML (input is DB-derived
          // location data; textContent can never re-parse it as markup).
          var strong = document.createElement("strong");
          strong.textContent = res.name;
          var pathSpan = document.createElement("span");
          pathSpan.style.cssText =
            "display:block;font-size:var(--text-xs);color:var(--taupe);font-family:var(--font-mono)";
          pathSpan.textContent = res.full_path;
          item.appendChild(strong);
          item.appendChild(pathSpan);
          item.addEventListener("mouseenter", function () {
            item.style.background = "var(--cream)";
          });
          item.addEventListener("mouseleave", function () {
            item.style.background = "";
          });
          item.addEventListener("click", function () {
            locInput.value = res.name;
            locHidden.value = res.slug;
            buildAction();
            clearDropdown();
          });
          dropdown.appendChild(item);
        });
      }

      locInput.addEventListener("input", function () {
        var q = locInput.value.trim();
        if (q.length < 2) { clearDropdown(); return; }
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () {
          fetch("/search/locations/?q=" + encodeURIComponent(q))
            .then(function (r) { return r.json(); })
            .then(function (data) { showResults(data.results || []); })
            .catch(function () { clearDropdown(); });
        }, 200);
      });

      locInput.addEventListener("blur", function () {
        // Delay so click on suggestion fires first
        setTimeout(clearDropdown, 200);
      });
    }
  }

  // ---------- H2.b: split-text mask headline ----------
  // Word-splits the hero headline in place (DOM APIs only — no innerHTML,
  // same rule as the quote reveal) so each word can rise out of its own
  // overflow-hidden mask. Ownership hand-over: once the words own the
  // entrance, the h1's own hv2-rise fade is removed (a one-shot transition
  // must never share the animated properties with the mask animation —
  // same sole-owner rule as G3/D-LOOP-31a). fxNone skips the split entirely:
  // the h1 stays plain and fully visible (D-MOTION-SAFE).
  function setupHeroHeadline() {
    var headline = document.querySelector("[data-hero-headline]");
    if (!headline) return;
    if (fxNone) return;
    var index = 0;
    // Split ONE text node inside its parent element: every run of
    // non-whitespace becomes a mask span, every whitespace run is kept
    // VERBATIM as plain text (leading/trailing/between — so the inter-part
    // spaces of the template survive and innerText matches the plain h1).
    function splitText(parent, textNode) {
      var raw = textNode.textContent;
      var frag = document.createDocumentFragment();
      var re = /\S+/g;
      var m;
      var last = 0;
      while ((m = re.exec(raw))) {
        if (m.index > last) {
          frag.appendChild(document.createTextNode(raw.slice(last, m.index)));
        }
        var mask = document.createElement("span");
        mask.className = "hero__w";
        var inner = document.createElement("span");
        inner.className = "hero__w-in";
        inner.style.setProperty("--d", index++);
        inner.textContent = m[0];
        mask.appendChild(inner);
        frag.appendChild(mask);
        last = m.index + m[0].length;
      }
      if (last < raw.length) {
        frag.appendChild(document.createTextNode(raw.slice(last)));
      }
      parent.replaceChild(frag, textNode);
    }
    Array.prototype.slice.call(headline.childNodes).forEach(function (n) {
      if (n.nodeType === 3 && n.textContent.trim()) {
        splitText(headline, n);
      } else if (n.nodeType === 1) {
        Array.prototype.slice.call(n.childNodes).forEach(function (m) {
          if (m.nodeType === 3 && m.textContent.trim()) splitText(n, m);
        });
      }
    });
    headline.classList.remove("hv2-rise");
    headline.style.removeProperty("--d");
  }

  // ---------- H2.b: hero video under fx=rich && !Save-Data (D-LOOP-21a) ----------
  // The 1.5MB loop is a rich-device upgrade of the slide stack: it loads
  // ONLY when the gate says rich and Save-Data is off; otherwise the
  // template's hidden attribute keeps it from loading at all (preload=
  // "none" as a second belt) and the slides stay the visual.
  function setupHeroVideo() {
    var video = document.querySelector("[data-hero-video]");
    if (!video) return;
    var rich = document.documentElement.getAttribute("data-fx") === "rich";
    var conn = navigator.connection || {};
    var saveData = !!(conn.saveData ||
        (conn.effectiveType && /(^2g$)/.test(conn.effectiveType)));
    if (!rich || saveData) return;
    video.hidden = false;
    var bg = video.closest(".hero__bg");
    if (bg) bg.classList.add("is-video");
    var playPromise = video.play();
    if (playPromise && playPromise.catch) playPromise.catch(function () {});
  }

  // ---------- G4: pointer polish (cursor-view bubble + magnetic CTAs) ----------
  // Rich devices with a fine, hover-capable pointer only (the fx gate alone
  // is not enough — a rich touch device must not grow a cursor bubble).
  // The bubble is JS-BUILT, aria-hidden decoration that duplicates an
  // existing link affordance ("View" — rows/cards are links), so keyboard
  // users lose nothing: only real pointer events drive it, and the bento
  // cards are excluded because M4 bento-shift owns the pointer there
  // (never two pointer effects on one element). Magnets are transform-only,
  // clamped to ±8px, and pointermove never fires on keyboard focus.
  function setupPointerPolish() {
    if (fxNone) return;
    if (document.documentElement.getAttribute("data-fx") !== "rich") return;
    if (!window.matchMedia("(pointer: fine)").matches) return;
    if (!window.matchMedia("(hover: hover)").matches) return;
    var PULL = 8;
    var bubbleTargets = document.querySelectorAll("[data-cursor-view]");
    if (bubbleTargets.length) {
      var bubble = document.createElement("div");
      bubble.className = "cursor-view";
      bubble.setAttribute("aria-hidden", "true");
      bubble.textContent = "View";
      document.body.appendChild(bubble);
      document.addEventListener("pointermove", function (e) {
        bubble.style.setProperty("--cx", e.clientX + "px");
        bubble.style.setProperty("--cy", e.clientY + "px");
      }, { passive: true });
      Array.prototype.forEach.call(bubbleTargets, function (t) {
        t.addEventListener("pointerenter", function () {
          document.body.classList.add("cursor-view-on");
        });
        t.addEventListener("pointerleave", function () {
          document.body.classList.remove("cursor-view-on");
        });
      });
    }
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-magnetic]"), function (el) {
        el.addEventListener("pointermove", function (e) {
          var r = el.getBoundingClientRect();
          var dx = (e.clientX - (r.left + r.width / 2)) * 0.18;
          var dy = (e.clientY - (r.top + r.height / 2)) * 0.18;
          el.style.setProperty("--mx",
            Math.max(-PULL, Math.min(PULL, dx)).toFixed(1) + "px");
          el.style.setProperty("--my",
            Math.max(-PULL, Math.min(PULL, dy)).toFixed(1) + "px");
        });
        el.addEventListener("pointerleave", function () {
          el.style.setProperty("--mx", "0px");
          el.style.setProperty("--my", "0px");
        });
      });
  }

  // ---------- r47: bubbly section-title reveal (data-bubble-title) ----------
  // Every topic title pops in letter-by-letter (the bt-pop bubble in
  // home.css: rise -> overshoot -> wobble -> settle) and REPLAYS when
  // it re-enters view, scrolling down or back up (owner request).
  // Hysteresis: pop at >=30% visible, re-arm only once the title has
  // FULLY left (ratio 0) — a title drifting past the edge never
  // flickers. Words wrap as units (.bt-w), letters animate (.bt-l);
  // per-letter delay = word stagger (capped) + letter stagger, both
  // set as CSS vars by the split.
  // D-MOTION-SAFE: fxNone / no-JS / no-IO -> the title never splits
  // and stays plain text. The .bt-armed class (the ONLY thing that
  // hides letters) is added per element AFTER io.observe succeeds —
  // a crash anywhere earlier leaves fully visible text behind.
  // Split is DOM-APIs-only (S11): template text is never re-parsed.
  function setupBubbleTitles() {
    var els = document.querySelectorAll("[data-bubble-title]");
    if (!els.length) return;
    if (fxNone || !("IntersectionObserver" in window)) return;

    function splitTitle(el) {
      var wordIndex = 0;
      Array.prototype.slice.call(el.childNodes).forEach(function (n) {
        if (n.nodeType !== 3 || !n.textContent.trim()) return;
        var raw = n.textContent;
        var frag = document.createDocumentFragment();
        var re = /\S+/g, m, last = 0;
        while ((m = re.exec(raw))) {
          if (m.index > last) {
            frag.appendChild(document.createTextNode(raw.slice(last, m.index)));
          }
          var word = document.createElement("span");
          word.className = "bt-w";
          // cap the word stagger so long titles still pop as one gesture
          var wd = Math.min(wordIndex * 70, 420);
          for (var li = 0; li < m[0].length; li++) {
            var letter = document.createElement("span");
            letter.className = "bt-l";
            letter.style.setProperty("--wd", wd + "ms");
            letter.style.setProperty("--ld", (li * 26) + "ms");
            letter.textContent = m[0].charAt(li);
            word.appendChild(letter);
          }
          frag.appendChild(word);
          last = m.index + m[0].length;
          wordIndex++;
        }
        if (last < raw.length) {
          frag.appendChild(document.createTextNode(raw.slice(last)));
        }
        el.replaceChild(frag, n);
      });
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.intersectionRatio >= 0.3) {
          entry.target.classList.add("is-bubbled");
        } else if (entry.intersectionRatio === 0) {
          // fully out of view: re-arm so the next entry pops again
          entry.target.classList.remove("is-bubbled");
        }
      });
    }, { threshold: [0, 0.3] });

    els.forEach(function (el) {
      splitTitle(el);
      io.observe(el);
      el.classList.add("bt-armed");   // after observe: hide letters
    });
  }

  function init() {
    setupCounters();
    setupQuoteReveal();
    setupHeroHeadline();
    setupHeroVideo();
    setupPointerPolish();
    setupReveal();
    setupBubbleTitles();
    setupHeaderScroll();
    if (!fxNone) setupNavAutoHide();  // G1: hide/return is lite/rich only
    setupMobileMenu();
    setupSearchSegment();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

// r11: flash-message dismiss (event delegation, works for dynamically added flashes)
document.addEventListener("click", function (e) {
  var btn = e.target.closest("[data-flash-close]");
  if (!btn) return;
  var flash = btn.closest(".flash");
  if (flash) flash.remove();
});
