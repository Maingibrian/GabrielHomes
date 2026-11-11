/* ga-init.js — r73 (BACKEND-PLAN 1E)
 *
 * Loads Google Analytics 4 ONLY when the owner has set an Analytics ID
 * (manage > SEO). The ID travels on this script tag's data attribute, so
 * the site ships ZERO inline scripts and the strict CSP holds (the
 * test_csp pin bans executable inline <script> outright — a nonce would
 * be allowed by the browser but violates the project's own stricter
 * rule, so we don't ship one at all).
 *
 * When the data attribute is missing or malformed this file does
 * nothing — the site stays tracker-free by default.
 */
(function () {
  "use strict";

  var el = document.currentScript;
  var id = el && el.dataset ? el.dataset.gaId : "";
  if (!id || id.indexOf("G-") !== 0) {
    return;
  }

  // Standard gtag bootstrap, built dynamically from the allowed origin.
  var loader = document.createElement("script");
  loader.async = true;
  loader.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(id);
  document.head.appendChild(loader);

  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  gtag("js", new Date());
  gtag("config", id);
})();
