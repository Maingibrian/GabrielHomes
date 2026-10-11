/* Detail-page gallery slider + share button (S10 — external files so CSP
 * `script-src 'self'` holds).
 *
 * v2 — Framer "Thumbnail Slider" effects, applied where appropriate:
 *   - crossfade + subtle scale-settle on the main image (no hard swap)
 *   - active thumbnail ring with smooth auto-centering inside the strip
 *   - counter micro-animation on change
 *   - touch swipe (left / right) for mobile
 *   - neighbour images preloaded so transitions never flash empty
 */
(function () {
  var gallery = document.querySelector('[data-gallery]');
  if (gallery) {
    var main = gallery.querySelector('[data-gallery-main]');
    var thumbs = Array.prototype.slice.call(gallery.querySelectorAll('[data-gallery-thumb]'));
    var prevBtn = gallery.querySelector('[data-gallery-prev]');
    var nextBtn = gallery.querySelector('[data-gallery-next]');
    var currentEl = gallery.querySelector('[data-gallery-current]');
    var strip = gallery.querySelector('.gallery__thumbs');

    // Image URLs come from the thumbnails' background-image.
    var images = thumbs.map(function (t) {
      var m = /url\(["']?(.*?)["']?\)/.exec(t.style.backgroundImage || '');
      return m ? m[1] : '';
    }).filter(Boolean);

    if (images.length > 0) {
      var current = 0;
      var animating = false;

      // Crossfade layer sits above the main background; it shows the incoming
      // image while the transition runs, then the main background is swapped.
      var fadeLayer = document.createElement('div');
      fadeLayer.className = 'gallery__fade';
      main.appendChild(fadeLayer);

      var show = function (i) {
        var next = (i + images.length) % images.length;
        if (next === current && fadeLayer.dataset.loaded === '1') return;
        current = next;

        var swap = function () {
          main.style.backgroundImage = 'url("' + images[current] + '")';
          fadeLayer.classList.remove('is-entering');
          fadeLayer.dataset.loaded = '1';
          animating = false;
        };

        if (animating) {
          // Fast clicking: settle immediately on the latest request.
          swap();
        } else {
          animating = true;
          fadeLayer.style.backgroundImage = 'url("' + images[current] + '")';
          // Force a reflow so the transition always plays.
          void fadeLayer.offsetWidth;
          fadeLayer.classList.add('is-entering');
          setTimeout(swap, 480);
        }

        if (currentEl) {
          currentEl.textContent = current + 1;
          currentEl.classList.remove('is-bumping');
          void currentEl.offsetWidth;
          currentEl.classList.add('is-bumping');
        }

        thumbs.forEach(function (t, j) {
          t.classList.toggle('is-active', j === current);
        });

        // Centre the active thumbnail inside the strip (no page scrolling).
        if (strip) {
          var active = thumbs[current];
          if (active && strip.scrollTo) {
            strip.scrollTo({
              left: active.offsetLeft - strip.clientWidth / 2 + active.clientWidth / 2,
              behavior: 'smooth',
            });
          }
        }

        // Preload neighbours so the next transition is instant.
        [current - 1, current + 1].forEach(function (n) {
          var url = images[(n + images.length) % images.length];
          if (url) { var img = new Image(); img.src = url; }
        });
      };

      if (prevBtn) prevBtn.addEventListener('click', function () { show(current - 1); });
      if (nextBtn) nextBtn.addEventListener('click', function () { show(current + 1); });
      thumbs.forEach(function (t, i) { t.addEventListener('click', function () { show(i); }); });

      // Keyboard navigation.
      document.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') show(current - 1);
        if (e.key === 'ArrowRight') show(current + 1);
      });

      // Touch swipe (mobile).
      var touchX = null;
      main.addEventListener('touchstart', function (e) {
        touchX = e.touches[0].clientX;
      }, { passive: true });
      main.addEventListener('touchend', function (e) {
        if (touchX === null) return;
        var dx = e.changedTouches[0].clientX - touchX;
        if (Math.abs(dx) > 42) show(dx < 0 ? current + 1 : current - 1);
        touchX = null;
      }, { passive: true });

      // Preload the first neighbour right away.
      if (images.length > 1) { var im = new Image(); im.src = images[1]; }
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
