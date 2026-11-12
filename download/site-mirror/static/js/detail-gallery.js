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

    // Single-image listings have no thumbnail strip — fall back to the
    // main frame's own background so the L4 zoom viewer still ships.
    if (images.length === 0 && main) {
      var m0 = /url\(["']?(.*?)["']?\)/.exec(main.style.backgroundImage || '');
      if (m0 && m0[1]) images = [m0[1]];
    }

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

      // Keyboard navigation (skipped while the L4 lightbox owns the keys).
      document.addEventListener('keydown', function (e) {
        if (lb && lb.classList.contains('is-open')) return;
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

      // --- L4: lightbox (click-to-zoom) with focus trap ---------------------
      // Extends the S10/v2 gallery in place (no rewrite). The DOM is built
      // by JS, so with scripts blocked there is no dead control and the
      // gallery itself remains the full content surface (Q3/D-MOTION-SAFE).
      // The G2 shared-element name stays on the gallery main; the overlay
      // never carries a view-transition-name (D-LOOP-32a).
      var lb = null;
      var lbMain = null;
      var lbCurrent = null;
      var lbClose = null;
      var lastFocus = null;

      var lbSync = function () {
        lbMain.style.backgroundImage = 'url("' + images[current] + '")';
        lbCurrent.textContent = current + 1;
      };
      var closeLightbox = function () {
        lb.classList.remove('is-open');
        document.documentElement.classList.remove('lb-open');
        if (window.__lenis && window.__lenis.start) window.__lenis.start();  // F5 public API
        document.removeEventListener('keydown', lbKeys, true);
        if (lastFocus && lastFocus.focus) lastFocus.focus();
      };
      var lbKeys = function (e) {
        if (e.key === 'Escape') { e.preventDefault(); closeLightbox(); return; }
        if (e.key === 'ArrowLeft') { show(current - 1); lbSync(); return; }
        if (e.key === 'ArrowRight') { show(current + 1); lbSync(); return; }
        if (e.key !== 'Tab') return;
        var focusables = lb.querySelectorAll('button');
        var first = focusables[0];
        var last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
        else if (!lb.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
      };
      var openLightbox = function () {
        if (!lb) buildLightbox();
        lastFocus = document.activeElement;
        lbSync();
        lb.classList.add('is-open');
        document.documentElement.classList.add('lb-open');  // CSS scroll lock
        if (window.__lenis && window.__lenis.stop) window.__lenis.stop();   // F5 public API
        document.addEventListener('keydown', lbKeys, true);
        lbClose.focus();
      };
      var buildLightbox = function () {
        lb = document.createElement('div');
        lb.className = 'lightbox';
        lb.setAttribute('role', 'dialog');
        lb.setAttribute('aria-modal', 'true');
        lb.setAttribute('aria-label', 'Photo viewer');
        lb.innerHTML =
          '<button class="lightbox__close" type="button" aria-label="Close photo viewer">' +
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><line x1="6" y1="6" x2="18" y2="18"></line><line x1="18" y1="6" x2="6" y2="18"></line></svg>' +
          '</button>' +
          '<button class="lightbox__nav lightbox__nav--prev" type="button" aria-label="Previous image">' +
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"></polyline></svg>' +
          '</button>' +
          '<div class="lightbox__main"></div>' +
          '<button class="lightbox__nav lightbox__nav--next" type="button" aria-label="Next image">' +
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"></polyline></svg>' +
          '</button>' +
          '<div class="lightbox__count"><span data-lb-current>1</span> / ' + images.length + '</div>';
        document.body.appendChild(lb);
        lbMain = lb.querySelector('.lightbox__main');
        lbCurrent = lb.querySelector('[data-lb-current]');
        lbClose = lb.querySelector('.lightbox__close');
        lb.querySelector('.lightbox__nav--prev').addEventListener('click', function () { show(current - 1); lbSync(); });
        lb.querySelector('.lightbox__nav--next').addEventListener('click', function () { show(current + 1); lbSync(); });
        lbClose.addEventListener('click', closeLightbox);
        lb.addEventListener('click', function (e) { if (e.target === lb) closeLightbox(); });
      };

      // Enlarge control: JS-injected so it never exists without JS.
      var expand = document.createElement('button');
      expand.type = 'button';
      expand.className = 'gallery__expand';
      expand.setAttribute('aria-label', 'Enlarge photo');
      expand.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>';
      expand.addEventListener('click', openLightbox);
      main.appendChild(expand);

      // Clicking the bare image (not the nav buttons) also opens the viewer.
      main.addEventListener('click', function (e) {
        if (e.target === main) openLightbox();
      });

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
