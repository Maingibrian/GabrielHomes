/* r74 (BACKEND-PLAN 2C) — the owner's map pin picker.
 * Self-hosted MapLibre (same stack as the public detail map: OpenFreeMap
 * positron style, no key, no new dependency). Tap the map or drag the
 * marker; the coordinates land in the two number inputs, so the form
 * works with or without this script (D-MOTION-SAFE: nothing here
 * animates; it is a positioning tool, not decoration).
 */
(function () {
  var mapEl = document.getElementById('pin-map');
  if (!mapEl) return;

  var latInput = document.getElementById(mapEl.dataset.latInput || 'id_lat');
  var lngInput = document.getElementById(mapEl.dataset.lngInput || 'id_lng');
  if (!latInput || !lngInput) return;

  var MOMBASA = [39.6682, -4.0500]; // [lng, lat] — MapLibre order, sane no-pin default
  // parseFloat("") is NaN — Number("") would be 0 and turn "no pin yet"
  // into a real pin at null island (caught live in r74).
  var lat = parseFloat(mapEl.dataset.lat);
  var lng = parseFloat(mapEl.dataset.lng);
  var hasPin = Number.isFinite(lat) && Number.isFinite(lng);
  var center = hasPin ? [lng, lat] : MOMBASA;

  import(mapEl.dataset.maplibreSrc).then(function (maplibregl) {
    mapEl.innerHTML = '';
    var map = new maplibregl.Map({
      container: mapEl,
      style: 'https://tiles.openfreemap.org/styles/positron',
      center: center,
      zoom: hasPin ? 15 : 12,
      minZoom: 9,
      maxZoom: 18,
      scrollZoom: false,
      cooperativeGestures: true,
      attributionControl: true
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');

    var marker = null;
    function setPin(lngLat, fromUser) {
      if (!marker) {
        marker = new maplibregl.Marker({ color: '#b64b1b', draggable: true })
          .setLngLat(lngLat)
          .addTo(map);
        marker.on('dragend', function () { setPin(marker.getLngLat(), true); });
      } else {
        marker.setLngLat(lngLat);
      }
      if (fromUser) {
        // 6 decimals matches the model's DecimalField(9,6).
        latInput.value = lngLat.lat.toFixed(6);
        lngInput.value = lngLat.lng.toFixed(6);
        latInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }

    if (hasPin) setPin([lng, lat], false);

    map.on('click', function (e) { setPin(e.lngLat, true); });

    // If the owner edits the numbers by hand, move the pin to match.
    function syncFromInputs() {
      var la = Number(latInput.value);
      var ln = Number(lngInput.value);
      if (Number.isFinite(la) && Number.isFinite(ln)) setPin([ln, la], false);
    }
    latInput.addEventListener('input', syncFromInputs);
    lngInput.addEventListener('input', syncFromInputs);
  }).catch(function (error) {
    console.error('Pin picker failed to initialize:', error);
    mapEl.innerHTML = '<p class="manage-pincard__error" role="status">The map could not load — the number fields below still work.</p>';
  });
})();
