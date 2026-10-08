/* Search page behaviour (S10 — moved inline script out of the template so
 * CSP `script-src 'self'` can hold; no inline handlers either).
 * 1. Mobile filter drawer toggle.
 * 2. Sort dropdown auto-submit (replaces the old inline onchange=).
 */
(function () {
  // --- Mobile filter drawer -------------------------------------------------
  var toggle = document.querySelector('[data-filter-toggle]');
  var drawer = document.querySelector('[data-filter-drawer]');
  if (toggle && drawer) {
    var open = function () {
      drawer.classList.add('is-open');
      drawer.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    };
    var close = function () {
      drawer.classList.remove('is-open');
      drawer.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    };
    toggle.addEventListener('click', open);
    drawer.querySelectorAll('[data-filter-close]').forEach(function (el) {
      el.addEventListener('click', close);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open')) close();
    });
  }

  // --- Sort dropdown: submit its form on change -----------------------------
  var sortSelect = document.querySelector('[data-sort-select]');
  if (sortSelect && sortSelect.form) {
    sortSelect.addEventListener('change', function () {
      sortSelect.form.submit();
    });
  }
})();
