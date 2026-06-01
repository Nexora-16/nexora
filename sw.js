const CACHE_SHELL = 'nexora-shell-v2';
const CACHE_API   = 'nexora-api-v1';

const SHELL_FILES = ['/', '/manifest.json', '/nexora-icon.svg'];

// Install: cache app shell
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_SHELL)
      .then(c => c.addAll(SHELL_FILES))
      .then(() => self.skipWaiting())
  );
});

// Activate: clean old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_SHELL && k !== CACHE_API).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = e.request.url;
  const isApi = url.includes('/api/');
  const isGet = e.request.method === 'GET';

  // Non-GET API (POST/PUT/DELETE): always network, never cache
  if (isApi && !isGet) return;

  if (isApi && isGet) {
    // API GETs: network first, fall back to stale cache
    e.respondWith(
      fetch(e.request)
        .then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE_API).then(c => c.put(e.request, clone));
          }
          return res;
        })
        .catch(() => caches.match(e.request, { cacheName: CACHE_API }))
    );
    return;
  }

  // App shell: network first, fall back to cache
  e.respondWith(
    fetch(e.request)
      .then(res => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE_SHELL).then(c => c.put(e.request, clone));
        }
        return res;
      })
      .catch(() => caches.match(e.request, { cacheName: CACHE_SHELL }))
  );
});
