const CACHE = "birdfolio-v1";
const OFFLINE = ["/static/manifest.json"];

self.addEventListener("install", e =>
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(OFFLINE)))
);

self.addEventListener("fetch", e => {
  // Network first for API calls, cache first for static assets
  if (e.request.url.includes("/users/")) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
  } else {
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request))
    );
  }
});
