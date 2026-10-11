/* Detail-page map init (S10 — external file so CSP `script-src 'self'` holds).
 * Reads lat/lng/label from the #detail-map element's data attributes.
 * Leaflet is self-hosted in /static/vendor/leaflet/ (see DECISIONS.md).
 *
 * v3 — Satellite-first, no OSM tile dependency (user request + 403 fix):
 *   - Default layer: Esri World Imagery (high-res satellite, free, no API key)
 *   - Alternate layer: CARTO Voyager streets (permissive usage policy —
 *     tile.openstreetmap.org 403-blocks datacenter/proxied browsers, which
 *     made the "Street map" toggle show "Access blocked" tiles)
 *   - Scroll-wheel zoom stays OFF until the map is clicked, so page scrolling
 *     is never hijacked; a hint chip explains it and fades once used.
 */
(function () {
  var mapEl = document.getElementById('detail-map');
  if (!mapEl || typeof L === 'undefined') return;

  var lat = parseFloat(mapEl.dataset.lat);
  var lng = parseFloat(mapEl.dataset.lng);
  var label = mapEl.dataset.label || '';
  if (isNaN(lat) || isNaN(lng)) return;

  var satellite = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    {
      attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics',
      maxZoom: 19,
    }
  );
  var streets = L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19,
    }
  );

  var map = L.map('detail-map', {
    layers: [satellite],
    scrollWheelZoom: false,
    zoomControl: true,
  }).setView([lat, lng], 15);

  L.control.layers({ 'Satellite': satellite, 'Street map': streets }, null, {
    position: 'topright',
    collapsed: false,
  }).addTo(map);

  // Enable wheel zoom once the visitor engages with the map.
  var hint = document.querySelector('.detail-map__hint');
  var enableWheel = function () {
    map.scrollWheelZoom.enable();
    if (hint) hint.classList.add('is-hidden');
  };
  map.on('click', enableWheel);
  map.on('dragstart', enableWheel);

  var marker = L.marker([lat, lng]).addTo(map);
  if (label) {
    marker.bindPopup(label).openPopup();
  }

  // Keep the popup visible on small screens (re-centre around it).
  setTimeout(function () {
    map.panTo([lat, lng]);
    map.invalidateSize();
  }, 250);
})();
