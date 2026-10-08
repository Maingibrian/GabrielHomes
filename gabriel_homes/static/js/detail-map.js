/* Detail-page map init (S10 — moved inline script out of the template so
 * CSP `script-src 'self'` can hold).
 * Reads lat/lng/label from the #detail-map element's data attributes.
 * Leaflet itself is self-hosted in /static/vendor/leaflet/ (see DECISIONS.md).
 */
(function () {
  var mapEl = document.getElementById('detail-map');
  if (!mapEl || typeof L === 'undefined') return;
  var lat = parseFloat(mapEl.dataset.lat);
  var lng = parseFloat(mapEl.dataset.lng);
  var label = mapEl.dataset.label || '';
  var map = L.map('detail-map').setView([lat, lng], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map);
  L.marker([lat, lng]).addTo(map).bindPopup(label);
})();
