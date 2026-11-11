/* Photo-led property detail map using the site's self-hosted MapLibre and
 * OpenFreeMap's OpenStreetMap-based style. No paid map key is needed. */
(function () {
  var mapEl = document.getElementById('detail-map');
  if (!mapEl) return;

  var lat = Number(mapEl.dataset.lat);
  var lng = Number(mapEl.dataset.lng);
  var label = mapEl.dataset.label || 'Approximate property location';
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

  import(mapEl.dataset.maplibreSrc).then(function (maplibregl) {
    mapEl.innerHTML = '';
    var map = new maplibregl.Map({
      container: mapEl,
      style: 'https://tiles.openfreemap.org/styles/positron',
      center: [lng, lat],
      zoom: 14,
      minZoom: 10,
      maxZoom: 18,
      scrollZoom: false,
      cooperativeGestures: true,
      attributionControl: true,
    });
    map.addControl(new maplibregl.NavigationControl({showCompass: false}), 'bottom-right');
    new maplibregl.Marker({color: '#b64b1b'})
      .setLngLat([lng, lat])
      .setPopup(new maplibregl.Popup({offset: 22}).setText(label))
      .addTo(map);
  }).catch(function (error) {
    console.error('Property location map failed to initialize:', error);
    mapEl.innerHTML = '<p class="detail-map__error" role="status">The location map could not load. Please try again shortly.</p>';
  });
})();
