(function () {
  var mapEl = document.getElementById('search-map');
  var dataEl = document.getElementById('search-map-data');
  if (!mapEl || !dataEl) return;

  var listings = [];
  try { listings = JSON.parse(dataEl.textContent); } catch (error) { return; }

  // L1 — smooth scrolling only when the capability gate allows it
  // (D-LOOP-16a: motion-preference media queries live in fx-gate.js and
  // CSS only — never in this file).
  function smoothOk() {
    return document.documentElement.getAttribute('data-fx') !== 'none';
  }

  // L1 — two-way highlight, pin → row: scroll to + flash the row.
  // Focus is NOT moved: activating a pin opens its maplibre popup, which
  // takes focus itself (focusAfterOpen) — that is the keyboard path; the
  // flash orients everyone else.
  var flashTimer = null;
  function flashRow(id) {
    var row = document.getElementById('listing-row-' + id);
    if (!row) return;
    row.scrollIntoView({behavior: smoothOk() ? 'smooth' : 'auto', block: 'center'});
    row.classList.remove('is-flashed');
    void row.offsetWidth; /* restart the animation on re-trigger */
    row.classList.add('is-flashed');
    if (flashTimer) clearTimeout(flashTimer);
    flashTimer = setTimeout(function () {
      row.classList.remove('is-flashed');
    }, 1600);
  }

  // L1 — two-way highlight, row → pin: hovering a result row highlights
  // its pin (delegated, so HTMX row swaps keep working).
  var grid = document.getElementById('results-grid');
  if (grid) {
    var hotPin = null;
    grid.addEventListener('mouseover', function (event) {
      var row = event.target.closest('.listing-row');
      var pin = row && row.dataset.listingPk
        ? mapEl.querySelector('[data-listing-pin="' + row.dataset.listingPk + '"]')
        : null;
      if (hotPin && hotPin !== pin) hotPin.classList.remove('is-hot');
      if (pin) { pin.classList.add('is-hot'); hotPin = pin; }
    });
    grid.addEventListener('mouseleave', function () {
      if (hotPin) { hotPin.classList.remove('is-hot'); hotPin = null; }
    });
  }

  // L1 — floating "Map" pill: hidden until the map leaves the viewport;
  // with JS blocked it never appears (no dead control, Q3-safe).
  var pill = document.querySelector('[data-map-return]');
  if (pill && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      pill.hidden = entries[0].isIntersecting;
    }, {threshold: 0.15}).observe(mapEl);
    pill.addEventListener('click', function () {
      mapEl.scrollIntoView({behavior: smoothOk() ? 'smooth' : 'auto', block: 'start'});
      mapEl.focus({preventScroll: true});
      pill.hidden = true;
      pill.blur();
    });
  }

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>\'\"]/g, function (character) {
      return {'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '\"': '&quot;'}[character];
    });
  }

  import(mapEl.dataset.maplibreSrc).then(function (maplibregl) {
    mapEl.innerHTML = '';
    var map = new maplibregl.Map({
      container: mapEl,
      style: 'https://tiles.openfreemap.org/styles/positron',
      center: [39.6682, -4.0435],
      zoom: 12,
      minZoom: 10,
      maxZoom: 18,
      attributionControl: true,
      cooperativeGestures: true,
    });
    map.addControl(new maplibregl.NavigationControl({showCompass: false}), 'bottom-right');

    var bounds = new maplibregl.LngLatBounds();
    var validCount = 0;
    var coordinateCounts = Object.create(null);

    // "Show all homes" reset — re-fits the map to every pin after the
    // visitor has panned/zoomed into a cluster. Only shown when there is
    // more than one home to return to (a single-pin map starts framed).
    var resetBtn = document.createElement('button');
    resetBtn.type = 'button';
    resetBtn.className = 'search-map__reset';
    resetBtn.textContent = 'Show all homes';
    resetBtn.setAttribute('aria-label', 'Show all homes on the map again');
    resetBtn.hidden = true;
    resetBtn.addEventListener('click', function () {
      map.fitBounds(bounds, {padding: 48, maxZoom: 13});
      resetBtn.blur();
    });
    mapEl.parentElement.appendChild(resetBtn);

    map.on('load', function () {
      listings.forEach(function (listing) {
        var lat = Number(listing.lat);
        var lng = Number(listing.lng);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

        var market = ['sale', 'rent', 'bnb'].indexOf(listing.market) > -1 ? listing.market : 'sale';
        var coordinateKey = lat.toFixed(4) + ':' + lng.toFixed(4);
        var duplicateIndex = coordinateCounts[coordinateKey] || 0;
        coordinateCounts[coordinateKey] = duplicateIndex + 1;
        var angle = duplicateIndex * 2.39996;
        var ring = Math.floor(duplicateIndex / 6) + 1;
        var position = [
          lng + (duplicateIndex ? Math.cos(angle) * .003 * ring : 0),
          lat + (duplicateIndex ? Math.sin(angle) * .0025 * ring : 0),
        ];

        var pin = document.createElement('button');
        pin.type = 'button';
        pin.className = 'map-price-pin map-price-pin--' + market;
        pin.textContent = listing.price_short || listing.price || 'View';
        pin.setAttribute('aria-label', (listing.title || 'Property') + ', ' + pin.textContent);
        pin.dataset.listingPin = listing.id;  // L1: pairs with #listing-row-<id>
        pin.addEventListener('click', function () { flashRow(listing.id); });

        var popup = '<article class="map-property-popup">' +
          '<small>' + (market === 'bnb' ? 'SHORT STAY' : (market === 'rent' ? 'FOR RENT' : 'FOR SALE')) + '</small>' +
          '<strong>' + escapeHtml(listing.title) + '</strong>' +
          '<p>' + escapeHtml(listing.price) + ' · ' + escapeHtml(listing.location) + '</p>' +
          '<a href="' + escapeHtml(listing.url) + '">View home →</a></article>';
        new maplibregl.Marker({element: pin, anchor: 'center'})
          .setLngLat(position)
          .setPopup(new maplibregl.Popup({offset: 22, maxWidth: '290px'}).setHTML(popup))
          .addTo(map);
        bounds.extend(position);
        validCount += 1;
      });

      if (validCount > 1) {
        map.fitBounds(bounds, {padding: 48, maxZoom: 13});
        resetBtn.hidden = false;
      } else if (validCount === 1) {
        map.setCenter(bounds.getCenter()).setZoom(14);
      }
    });
  }).catch(function (error) {
    console.error('Property map failed to initialize:', error);
    mapEl.innerHTML = '<p role="status">The property map could not load. Please try again shortly.</p>';
  });
})();
