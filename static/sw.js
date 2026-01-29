const CACHE_NAME = "pc-vas-cache-v1";

// File da mettere in cache
const ASSETS = [
    "/",
    "/static/manifest.json",
    "/static/img/logo.png",
    "/static/img/logo.ico",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
];

// Installazione SW
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(ASSETS);
        })
    );
    self.skipWaiting();
});

// Attivazione SW
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

// Gestione richieste
self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(cached => {
            return (
                cached ||
                fetch(event.request).catch(() =>
                    caches.match("/static/img/logo.png")
                )
            );
        })
    );
});
