/* Detail-page gallery slider + share button (S10 — moved inline scripts and
 * inline onclick handler out of the template so CSP `script-src 'self'` holds).
 */
(function () {
  // --- Gallery slider (vanilla JS — no library) ------------------------------
  var gallery = document.querySelector('[data-gallery]');
  if (gallery) {
    var main = gallery.querySelector('[data-gallery-main]');
    var thumbs = gallery.querySelectorAll('[data-gallery-thumb]');
    var prevBtn = gallery.querySelector('[data-gallery-prev]');
    var nextBtn = gallery.querySelector('[data-gallery-next]');
    var currentEl = gallery.querySelector('[data-gallery-current]');
    // Image URLs come from the thumbnails' background-image.
    var images = Array.from(thumbs).map(function (t) {
      return t.style.backgroundImage.slice(5, -2);
    });
    if (images.length > 0) {
      var current = 0;

      var show = function (i) {
        current = (i + images.length) % images.length;
        main.style.backgroundImage = 'url("' + images[current] + '")';
        if (currentEl) currentEl.textContent = current + 1;
        thumbs.forEach(function (t, j) {
          t.classList.toggle('is-active', j === current);
        });
      };

      if (prevBtn) prevBtn.addEventListener('click', function () { show(current - 1); });
      if (nextBtn) nextBtn.addEventListener('click', function () { show(current + 1); });
      thumbs.forEach(function (t, i) { t.addEventListener('click', function () { show(i); }); });

      // Keyboard nav
      document.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') show(current - 1);
        if (e.key === 'ArrowRight') show(current + 1);
      });
    }
  }

  // --- Share button (Web Share API with clipboard fallback) ------------------
  var shareBtn = document.querySelector('[data-share-url]');
  if (shareBtn) {
    shareBtn.addEventListener('click', function () {
      var shareData = { title: document.title, url: shareBtn.dataset.shareUrl || window.location.href };
      if (navigator.share) {
        navigator.share(shareData);
      } else if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(shareData.url);
      }
    });
  }
})();
