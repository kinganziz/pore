/* PORE service worker — offline app shell. Generated into /sw.js by tools/build.py. */
const VERSION = 'c6a1e8c62f';
const SHELL = 'pore-shell-' + VERSION;
const SHELL_FILES = ['./', './index.html', './manifest.webmanifest', './icons/sprite-pixel.svg', './icons/app/anz.png', './icons/app/icon-192.png', './icons/app/icon-512.png', './icons/app/maskable-512.png'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(SHELL).then(cache => cache.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => (k.startsWith('pore-shell-') && k !== SHELL) || k === 'pore-icons-v1').map(k => caches.delete(k))))
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

  // HD icons (one small file each): cache first within a deploy; each new version starts a fresh cache.
  if (url.pathname.includes('/icons/modern/')) {
    event.respondWith(caches.open(SHELL).then(cache => cache.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok) cache.put(req, res.clone());
      return res;
    }))));
    return;
  }

  // App shell: network first (so deploys show up), fall back to the cached copy when offline.
  // cache: 'no-cache' revalidates with the server (ETag) instead of trusting the 10-minute HTTP cache,
  // so a refresh always shows the latest deploy.
  event.respondWith(
    fetch(req, { cache: 'no-cache' }).then(res => {
      if (res.ok && (url.pathname.endsWith('/') || url.pathname.endsWith('.html') || url.pathname.endsWith('.webmanifest') || /\/icons\/sprite-pixel\.svg$/.test(url.pathname) || url.pathname.includes('/icons/app/'))) {
        const copy = res.clone();
        caches.open(SHELL).then(cache => cache.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then(hit => hit || (url.pathname.endsWith('/') || url.pathname.endsWith('.html') ? caches.match('./index.html') : undefined)))
  );
});
