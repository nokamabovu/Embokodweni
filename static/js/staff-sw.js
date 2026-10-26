// Minimal service worker so staff can install the dashboard on their phone.
// It does not cache anything: the dashboard always shows live data.
self.addEventListener("install", function () { self.skipWaiting(); });
self.addEventListener("activate", function (e) { e.waitUntil(self.clients.claim()); });
self.addEventListener("fetch", function () {});
