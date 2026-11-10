/* Agent dashboard — image formset helper (S10 — moved inline script out of
 * the template so CSP `script-src 'self'` can hold).
 * Reveals hidden extra form slots when "Add image slot" is clicked.
 */
(function () {
  var btn = document.getElementById('add-image-btn');
  if (!btn) return;
  var hidden = document.querySelectorAll('.image-formset__item[style*="display: none"]');
  var idx = 0;
  btn.addEventListener('click', function () {
    if (idx < hidden.length) {
      hidden[idx].style.display = '';
      idx++;
      if (idx >= hidden.length) btn.style.display = 'none';
    }
  });
})();
