const CACHE = 'rist-pending-packet-v2';
const SHELL = ['./', './index.html', './pending-packet.js?v=3'];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key.startsWith('rist-pending-packet-') && key !== CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.mode !== 'navigate') return;
  event.respondWith(
    fetch(event.request)
      .catch(async () => {
        const cache = await caches.open(CACHE);
        return (await cache.match('./index.html')) || (await cache.match('./'));
      })
  );
});
