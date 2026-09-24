/* PORE service worker — offline app shell. Generated into /sw.js by tools/build.py. */
const VERSION = 'd007e94689';
const SHELL = 'pore-shell-' + VERSION;
const ICONS = 'pore-icons-v1';
const SHELL_FILES = ['./', './index.html', './manifest.webmanifest', './icons/sprite.svg', './icons/sprite-modern.svg', './icons/app/icon-192.png', './icons/app/icon-512.png', './icons/app/maskable-512.png'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(SHELL).then(cache => cache.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('pore-shell-') && k !== SHELL).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', event => {
  if (event.data === 'version') event.source.postMessage({ type: 'version', version: VERSION });
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // SVG icons: cache first, fill the cache on demand (they never change for a given id).
  if (url.pathname.includes('/icons/svg/')) {
    event.respondWith(caches.open(ICONS).then(cache => cache.match(req).then(hit => hit || fetch(req).then(res => { if (res.ok) cache.put(req, res.clone()); return res; }))));
    return;
  }

  // App shell: network first (so deploys show up), fall back to the cached copy when offline.
  event.respondWith(
    fetch(req).then(res => {
      if (res.ok && (url.pathname.endsWith('/') || url.pathname.endsWith('.html') || url.pathname.endsWith('.webmanifest') || /\/icons\/sprite(-modern)?\.svg$/.test(url.pathname) || url.pathname.includes('/icons/app/'))) {
        const copy = res.clone();
        caches.open(SHELL).then(cache => cache.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then(hit => hit || (url.pathname.endsWith('/') || url.pathname.endsWith('.html') ? caches.match('./index.html') : undefined)))
  );
});
