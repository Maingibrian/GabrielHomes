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
      target.scrollIntoView({ behavior: "smooth", block: "start" });
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

  function init() {
    setupCounters();
    setupQuoteReveal();
    setupReveal();
    setupHeaderScroll();
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
