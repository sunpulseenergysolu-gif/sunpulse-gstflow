// SunPulse GSTFlow Service Worker (Zero-Cache Dynamic Network Engine)
self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.map((k) => caches.delete(k)));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Never intercept API requests - let browser handle them directly
  if (e.request.url.includes('/api/')) {
    return;
  }
  // For static assets, fetch fresh from network
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});

