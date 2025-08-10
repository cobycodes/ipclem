// Parse the location string passed from Flask template
const loc = MAP_GEOLOC.split(",");
const lat = parseFloat(loc[0]);
const lon = parseFloat(loc[1]);

const map = L.map("map").setView([lat, lon], 10);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

L.marker([lat, lon])
  .addTo(map)
  .bindPopup(MAP_POPUP_TEXT)
  .openPopup();
